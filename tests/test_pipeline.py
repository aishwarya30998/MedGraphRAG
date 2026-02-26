"""
test_pipeline.py — Integration tests for rag/pipeline.py

Tests the full end-to-end RAG pipeline: Neo4j retrieval + Ollama generation.

Requires: Neo4j running + Ollama running
Mark:      @pytest.mark.integration + @pytest.mark.llm

Run:
    pytest tests/test_pipeline.py -v
"""

import pytest
from rag.pipeline import graph_rag_pipeline


@pytest.mark.integration
@pytest.mark.llm
class TestPipelineOutputStructure:
    """Verify the pipeline returns the correct types and structure."""

    def test_returns_tuple(self, neo4j_driver, ollama_client):
        result = graph_rag_pipeline("What drugs treat Type 2 Diabetes?")
        assert isinstance(result, tuple), "pipeline should return a tuple"

    def test_returns_two_items(self, neo4j_driver, ollama_client):
        result = graph_rag_pipeline("What drugs treat Type 2 Diabetes?")
        assert len(result) == 2, "pipeline should return (answer, subgraph)"

    def test_answer_is_string(self, neo4j_driver, ollama_client):
        answer, _ = graph_rag_pipeline("What drugs treat Type 2 Diabetes?")
        assert isinstance(answer, str)

    def test_answer_is_not_empty(self, neo4j_driver, ollama_client):
        answer, _ = graph_rag_pipeline("What drugs treat Type 2 Diabetes?")
        assert len(answer.strip()) > 0

    def test_subgraph_is_dict(self, neo4j_driver, ollama_client):
        _, subgraph = graph_rag_pipeline("What drugs treat Type 2 Diabetes?")
        assert isinstance(subgraph, dict)

    def test_subgraph_has_required_keys(self, neo4j_driver, ollama_client):
        _, subgraph = graph_rag_pipeline("What drugs treat Type 2 Diabetes?")
        assert "query" in subgraph
        assert "seed_nodes" in subgraph
        assert "disease_contexts" in subgraph
        assert "drug_contexts" in subgraph


@pytest.mark.integration
@pytest.mark.llm
class TestPipelineQueryResults:
    """Verify the pipeline returns relevant results for known queries."""

    def test_diabetes_query_returns_metformin(self, neo4j_driver, ollama_client):
        answer, subgraph = graph_rag_pipeline("What is the treatment for Type 2 Diabetes?")
        assert "metformin" in answer.lower(), (
            f"Expected Metformin mentioned in diabetes answer. Got:\n{answer[:400]}"
        )

    def test_warfarin_query_returns_interaction_info(self, neo4j_driver, ollama_client):
        answer, subgraph = graph_rag_pipeline(
            "What are the drug interactions between warfarin and aspirin?"
        )
        assert "warfarin" in answer.lower() or "aspirin" in answer.lower(), (
            f"Expected warfarin/aspirin mentioned in answer. Got:\n{answer[:400]}"
        )

    def test_chest_pain_query_seeds_cardiovascular(self, neo4j_driver, ollama_client):
        answer, subgraph = graph_rag_pipeline(
            "What diseases are associated with chest pain and shortness of breath?"
        )
        seeds = subgraph["seed_nodes"]["diseases"]
        cardiovascular = {
            "Coronary Artery Disease", "Asthma",
            "Chronic Obstructive Pulmonary Disease", "Atrial Fibrillation"
        }
        assert any(d in cardiovascular for d in seeds), (
            f"Expected cardiovascular disease in seeds for chest pain query. Got: {seeds}"
        )

    def test_answer_contains_disclaimer(self, neo4j_driver, ollama_client):
        answer, _ = graph_rag_pipeline("What treats hypertension?")
        assert "educational" in answer.lower() or "clinician" in answer.lower(), (
            "Answer should contain the safety disclaimer"
        )


@pytest.mark.integration
@pytest.mark.llm
class TestPipelineTopK:
    """Verify top_k parameter affects seed node count."""

    def test_top_k_1_returns_one_seed(self, neo4j_driver, ollama_client):
        _, subgraph = graph_rag_pipeline("diabetes treatment", top_k=1)
        total = (
            len(subgraph["seed_nodes"]["diseases"]) +
            len(subgraph["seed_nodes"]["drugs"])
        )
        assert total <= 1, f"top_k=1 should return at most 1 seed, got {total}"

    def test_top_k_5_returns_up_to_five_seeds(self, neo4j_driver, ollama_client):
        _, subgraph = graph_rag_pipeline("medicine disease treatment drug", top_k=5)
        total = (
            len(subgraph["seed_nodes"]["diseases"]) +
            len(subgraph["seed_nodes"]["drugs"])
        )
        assert total <= 5, f"top_k=5 should return at most 5 seeds, got {total}"
