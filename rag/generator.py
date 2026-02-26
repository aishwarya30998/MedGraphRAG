"""
generator.py — LLM answer generation via Ollama (llama3.2:3b).

Takes the structured subgraph context from the retriever and asks
the local LLM to produce a grounded clinical answer.
"""

import os
from typing import Any

import ollama
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Configure the ollama client to point at the right host
_client = ollama.Client(host=OLLAMA_HOST)


# Context formatting helpers

def _format_disease_context(disease_ctx: list[dict]) -> str:
    if not disease_ctx:
        return ""
    lines = []
    for d in disease_ctx:
        lines.append(f"DISEASE: {d.get('disease', 'Unknown')}")
        lines.append(f"  ICD Code: {d.get('icd_code', 'N/A')}")
        lines.append(f"  Category: {d.get('category', 'N/A')}")
        lines.append(f"  Description: {d.get('description', 'N/A')}")

        symptoms = d.get("symptoms", [])
        if symptoms:
            lines.append(f"  Symptoms: {', '.join(symptoms)}")

        treatments = d.get("treatments", [])
        if treatments:
            tx_strs = [
                f"{t['drug']} (evidence: {t.get('evidence', 'N/A')})"
                for t in treatments
            ]
            lines.append(f"  Treatments: {', '.join(tx_strs)}")

        comorbidities = d.get("comorbidities", [])
        if comorbidities:
            lines.append(f"  Comorbidities: {', '.join(comorbidities)}")

        genes = d.get("genes", [])
        if genes:
            lines.append(f"  Associated Genes: {', '.join(genes)}")

        interactions = d.get("drug_interactions", [])
        if interactions:
            ix_strs = [
                f"{ix['drug_a']} ↔ {ix['drug_b']} [{ix.get('severity', '?')}]: {ix.get('description', '')}"
                for ix in interactions
            ]
            lines.append("  Drug Interactions:")
            for ix in ix_strs:
                lines.append(f"    - {ix}")

        lines.append("")
    return "\n".join(lines)


def _format_drug_context(drug_ctx: list[dict]) -> str:
    if not drug_ctx:
        return ""
    lines = []
    for d in drug_ctx:
        lines.append(f"DRUG: {d.get('drug', 'Unknown')}")
        lines.append(f"  Class: {d.get('drug_class', 'N/A')}")
        lines.append(f"  Mechanism: {d.get('mechanism', 'N/A')}")

        treats = d.get("treats", [])
        if treats:
            tx_strs = [
                f"{t['disease']} (evidence: {t.get('evidence', 'N/A')})"
                for t in treats
            ]
            lines.append(f"  Treats: {', '.join(tx_strs)}")

        interactions = d.get("interactions", [])
        if interactions:
            lines.append("  Interactions:")
            for ix in interactions:
                lines.append(
                    f"    - {ix['drug']} [{ix.get('severity', '?')}]: {ix.get('description', '')}"
                )
        lines.append("")
    return "\n".join(lines)


def _build_prompt(query: str, subgraph: dict[str, Any]) -> str:
    disease_section = _format_disease_context(subgraph.get("disease_contexts", []))
    drug_section = _format_drug_context(subgraph.get("drug_contexts", []))

    context_parts = []
    if disease_section.strip():
        context_parts.append(disease_section)
    if drug_section.strip():
        context_parts.append(drug_section)

    context_text = "\n".join(context_parts) if context_parts else "No relevant context found."

    prompt = f"""You are a clinical knowledge assistant powered by a medical knowledge graph.
Your role is to answer medical questions accurately using ONLY the structured context provided below.

IMPORTANT RULES:
- Base your answer strictly on the provided context.
- Do NOT hallucinate drug names, diseases, or treatments not in the context.
- Always mention if drug interactions are relevant to the question.
- End with: "⚠️ This is for educational purposes only. Always consult a licensed clinician."

=== KNOWLEDGE GRAPH CONTEXT ===
{context_text}
=== END OF CONTEXT ===

QUESTION: {query}

ANSWER:"""
    return prompt


# Public API

def generate_answer(query: str, subgraph: dict[str, Any]) -> str:
    """
    Generate a grounded answer using the local Ollama LLM.

    Args:
        query:    The user's clinical question.
        subgraph: The structured context dict from retriever.retrieve_subgraph().

    Returns:
        The LLM's answer as a string.
    """
    prompt = _build_prompt(query, subgraph)

    try:
        response = _client.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1},  # Low temperature for factual answers
        )
        # ollama >= 0.4.x returns a structured object, not a plain dict
        if hasattr(response, "message"):
            return response.message.content
        else:
            return response["message"]["content"]
    except Exception as exc:
        return (
            f"[ERROR] Could not reach Ollama. Make sure it is running at {OLLAMA_HOST} "
            f"and model '{OLLAMA_MODEL}' is pulled.\n\nDetails: {exc}"
        )


if __name__ == "__main__":
    # Quick test with dummy context
    dummy_subgraph = {
        "disease_contexts": [
            {
                "disease": "Type 2 Diabetes Mellitus",
                "icd_code": "E11",
                "category": "Endocrine",
                "description": "A chronic metabolic disorder.",
                "symptoms": ["Polyuria", "Polydipsia", "Fatigue"],
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
    answer = generate_answer("What is the first-line treatment for Type 2 Diabetes?", dummy_subgraph)
    print(answer)
