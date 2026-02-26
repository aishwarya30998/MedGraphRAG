"""
test_generator.py — Integration tests for rag/generator.py

Verifies that the Ollama LLM generates valid answers from subgraph context.

Requires: Ollama running at localhost:11434 with llama3.2:3b pulled
Mark:      @pytest.mark.llm

Run:
    pytest tests/test_generator.py -v
"""

import pytest
from rag.generator import generate_answer

# Shared test subgraph (no Neo4j needed — passed directly)


DIABETES_SUBGRAPH = {
    "disease_contexts": [
        {
            "disease": "Type 2 Diabetes Mellitus",
            "icd_code": "E11",
            "category": "Endocrine",
            "description": "A chronic metabolic disorder characterized by high blood glucose.",
            "symptoms": ["Polyuria", "Polydipsia", "Fatigue", "Blurred Vision"],
            "treatments": [
                {"drug": "Metformin", "evidence": "Level A"},
                {"drug": "Atorvastatin", "evidence": "Level B"},
            ],
            "comorbidities": ["Hypertension", "Coronary Artery Disease"],
            "genes": ["TCF7L2"],
            "drug_interactions": [],
        }
    ],
    "drug_contexts": [],
}

WARFARIN_SUBGRAPH = {
    "disease_contexts": [],
    "drug_contexts": [
        {
            "drug": "Warfarin",
            "drug_class": "Anticoagulant",
            "mechanism": "Inhibits vitamin K epoxide reductase.",
            "treats": [{"disease": "Atrial Fibrillation", "evidence": "Level A"}],
            "interactions": [
                {
                    "drug": "Aspirin",
                    "severity": "Major",
                    "description": "Concurrent use significantly increases bleeding risk.",
                },
                {
                    "drug": "Ibuprofen",
                    "severity": "Major",
                    "description": "NSAIDs increase bleeding risk with warfarin.",
                },
            ],
        }
    ],
}

EMPTY_SUBGRAPH = {
    "disease_contexts": [],
    "drug_contexts": [],
}


@pytest.mark.llm
class TestGeneratorOutput:
    """Verify generate_answer() returns valid strings."""

    def test_returns_string(self, ollama_client):
        answer = generate_answer("What treats Type 2 Diabetes?", DIABETES_SUBGRAPH)
        assert isinstance(answer, str)

    def test_answer_is_not_empty(self, ollama_client):
        answer = generate_answer("What treats Type 2 Diabetes?", DIABETES_SUBGRAPH)
        assert len(answer.strip()) > 0

    def test_answer_is_not_error_message(self, ollama_client):
        answer = generate_answer("What treats Type 2 Diabetes?", DIABETES_SUBGRAPH)
        assert not answer.startswith("[ERROR]"), f"Generator returned error: {answer}"

    def test_answer_contains_disclaimer(self, ollama_client):
        answer = generate_answer("What treats Type 2 Diabetes?", DIABETES_SUBGRAPH)
        assert "educational" in answer.lower() or "clinician" in answer.lower(), (
            "Answer should contain the safety disclaimer"
        )


@pytest.mark.llm
class TestGeneratorGrounding:
    """Verify the LLM uses the provided context correctly."""

    def test_diabetes_answer_mentions_metformin(self, ollama_client):
        answer = generate_answer(
            "What is the first-line treatment for Type 2 Diabetes?",
            DIABETES_SUBGRAPH
        )
        assert "metformin" in answer.lower(), (
            f"Expected Metformin in answer about diabetes treatment. Got: {answer[:300]}"
        )

    def test_warfarin_answer_mentions_aspirin_interaction(self, ollama_client):
        answer = generate_answer(
            "What are the drug interactions of warfarin?",
            WARFARIN_SUBGRAPH
        )
        assert "aspirin" in answer.lower(), (
            f"Expected Aspirin interaction in warfarin answer. Got: {answer[:300]}"
        )

    def test_warfarin_answer_mentions_bleeding_risk(self, ollama_client):
        answer = generate_answer(
            "What are the drug interactions of warfarin?",
            WARFARIN_SUBGRAPH
        )
        assert "bleeding" in answer.lower(), (
            f"Expected bleeding risk mentioned in warfarin answer. Got: {answer[:300]}"
        )


@pytest.mark.llm
class TestGeneratorEdgeCases:
    """Verify generator handles edge cases gracefully."""

    def test_empty_context_returns_string(self, ollama_client):
        """With no context, LLM should still return a string (saying context not found)."""
        answer = generate_answer("What is aspirin?", EMPTY_SUBGRAPH)
        assert isinstance(answer, str)
        assert len(answer.strip()) > 0

    def test_answer_reasonable_length(self, ollama_client):
        """Answer should be more than a few words."""
        answer = generate_answer("What treats Type 2 Diabetes?", DIABETES_SUBGRAPH)
        word_count = len(answer.split())
        assert word_count >= 10, f"Answer too short ({word_count} words): {answer}"
