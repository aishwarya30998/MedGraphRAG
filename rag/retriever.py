"""
retriever.py — Graph RAG retrieval step.

Two-phase retrieval:
  1. Vector similarity search → find seed nodes (Diseases or Drugs)
     that are most similar to the query.
  2. Graph traversal from seed nodes → collect connected context
     (symptoms, treatments, interactions, comorbidities, genes).
"""

import os
from typing import Any

import numpy as np
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "medgraph123")
MODEL_NAME = "all-MiniLM-L6-v2"

# Singleton model (loaded once per process)
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def get_driver():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    return driver


# Cosine similarity (computed in Python since Neo4j Community Edition
# does not include the vector index plugin)

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)



# Phase 1: Vector seed search across Disease and Drug nodes
def _find_seed_nodes(
    session, query_embedding: list[float], top_k: int = 3
) -> dict[str, list[str]]:
    """
    Returns {"diseases": [...names...], "drugs": [...names...]}
    for the top-k most similar nodes across both types.
    """
    all_candidates = []

    # --- Diseases ---
    disease_records = session.run(
        "MATCH (d:Disease) WHERE d.embedding IS NOT NULL "
        "RETURN d.name AS name, d.embedding AS embedding"
    ).data()

    for rec in disease_records:
        sim = _cosine_similarity(query_embedding, rec["embedding"])
        all_candidates.append({"type": "disease", "name": rec["name"], "sim": sim})

    # --- Drugs ---
    drug_records = session.run(
        "MATCH (dr:Drug) WHERE dr.embedding IS NOT NULL "
        "RETURN dr.name AS name, dr.embedding AS embedding"
    ).data()

    for rec in drug_records:
        sim = _cosine_similarity(query_embedding, rec["embedding"])
        all_candidates.append({"type": "drug", "name": rec["name"], "sim": sim})

    # Sort and take top_k
    top = sorted(all_candidates, key=lambda x: x["sim"], reverse=True)[:top_k]

    seed_diseases = [c["name"] for c in top if c["type"] == "disease"]
    seed_drugs = [c["name"] for c in top if c["type"] == "drug"]

    return {"diseases": seed_diseases, "drugs": seed_drugs}



# Phase 2: Graph traversal from seed nodes

def _traverse_from_diseases(session, disease_names: list[str]) -> list[dict]:
    if not disease_names:
        return []

    records = session.run(
        """
        MATCH (d:Disease)
        WHERE d.name IN $names
        OPTIONAL MATCH (d)-[:HAS_SYMPTOM]->(s:Symptom)
        OPTIONAL MATCH (drug:Drug)-[t:TREATS]->(d)
        OPTIONAL MATCH (drug)-[ix:INTERACTS_WITH]->(other_drug:Drug)
        OPTIONAL MATCH (d)-[:COMORBID_WITH]->(comorbid:Disease)
        OPTIONAL MATCH (gene:Gene)-[:ASSOCIATED_WITH]->(d)
        RETURN
            d.name          AS disease,
            d.description   AS description,
            d.icd_code      AS icd_code,
            d.category      AS category,
            collect(DISTINCT s.name)              AS symptoms,
            collect(DISTINCT {
                drug: drug.name,
                evidence: t.evidence
            })                                    AS treatments,
            collect(DISTINCT {
                drug_a: drug.name,
                drug_b: other_drug.name,
                severity: ix.severity,
                description: ix.description
            })                                    AS drug_interactions,
            collect(DISTINCT comorbid.name)       AS comorbidities,
            collect(DISTINCT gene.name)           AS genes
        """,
        names=disease_names,
    ).data()

    # Clean up null entries produced by OPTIONAL MATCH
    cleaned = []
    for r in records:
        r["treatments"] = [t for t in r["treatments"] if t.get("drug")]
        r["drug_interactions"] = [
            ix for ix in r["drug_interactions"]
            if ix.get("drug_a") and ix.get("drug_b")
        ]
        cleaned.append(r)

    return cleaned


def _traverse_from_drugs(session, drug_names: list[str]) -> list[dict]:
    if not drug_names:
        return []

    records = session.run(
        """
        MATCH (dr:Drug)
        WHERE dr.name IN $names
        OPTIONAL MATCH (dr)-[t:TREATS]->(d:Disease)
        OPTIONAL MATCH (dr)-[ix:INTERACTS_WITH]->(other:Drug)
        RETURN
            dr.name         AS drug,
            dr.drug_class   AS drug_class,
            dr.mechanism    AS mechanism,
            collect(DISTINCT {
                disease: d.name,
                evidence: t.evidence
            })              AS treats,
            collect(DISTINCT {
                drug: other.name,
                severity: ix.severity,
                description: ix.description
            })              AS interactions
        """,
        names=drug_names,
    ).data()

    cleaned = []
    for r in records:
        r["treats"] = [t for t in r["treats"] if t.get("disease")]
        r["interactions"] = [ix for ix in r["interactions"] if ix.get("drug")]
        cleaned.append(r)

    return cleaned


# Public API

def retrieve_subgraph(
    query: str,
    driver=None,
    top_k: int = 3,
) -> dict[str, Any]:
    """
    Main retrieval function.

    Returns:
        {
            "query": str,
            "seed_nodes": {"diseases": [...], "drugs": [...]},
            "disease_contexts": [...],
            "drug_contexts": [...],
        }
    """
    model = _get_model()
    query_embedding = model.encode(query).tolist()

    owns_driver = driver is None
    if owns_driver:
        driver = get_driver()

    try:
        with driver.session() as session:
            seeds = _find_seed_nodes(session, query_embedding, top_k=top_k)
            disease_ctx = _traverse_from_diseases(session, seeds["diseases"])
            drug_ctx = _traverse_from_drugs(session, seeds["drugs"])
    finally:
        if owns_driver:
            driver.close()

    return {
        "query": query,
        "seed_nodes": seeds,
        "disease_contexts": disease_ctx,
        "drug_contexts": drug_ctx,
    }


if __name__ == "__main__":
    # Quick smoke test
    import json
    result = retrieve_subgraph("What drugs treat Type 2 Diabetes?")
    print(json.dumps(result, indent=2))
