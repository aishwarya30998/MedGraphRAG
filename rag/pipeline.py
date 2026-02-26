"""
pipeline.py — Full Graph RAG pipeline.

Combines retriever + generator into a single callable:

    answer, subgraph = graph_rag_pipeline("What drugs treat Type 2 Diabetes?")
"""

import os
from typing import Any

from neo4j import GraphDatabase
from dotenv import load_dotenv

from rag.retriever import retrieve_subgraph
from rag.generator import generate_answer

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "medgraph123")

# Shared driver (kept open across requests for efficiency)
_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        _driver.verify_connectivity()
    return _driver


def graph_rag_pipeline(
    query: str,
    top_k: int = 3,
) -> tuple[str, dict[str, Any]]:
    """
    Full Graph RAG pipeline.

    Args:
        query:  Natural language clinical question.
        top_k:  Number of seed nodes to retrieve via vector similarity.

    Returns:
        (answer: str, subgraph: dict)
        - answer:   LLM-generated answer grounded in the graph context.
        - subgraph: The raw structured context dict for display/debugging.
    """
    driver = _get_driver()

    # Step 1: Retrieve relevant subgraph
    subgraph = retrieve_subgraph(query, driver=driver, top_k=top_k)

    # Step 2: Generate answer from subgraph context
    answer = generate_answer(query, subgraph)

    return answer, subgraph


def close():
    """Call this on application shutdown."""
    global _driver
    if _driver:
        _driver.close()
        _driver = None


if __name__ == "__main__":
    import json

    test_queries = [
        "What are the drug interactions between metformin and aspirin?",
        "What diseases are associated with chest pain and shortness of breath?",
        "What is the treatment protocol for Type 2 Diabetes?",
        "What are the side effects and interactions of warfarin?",
    ]

    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {q}")
        print("=" * 60)
        answer, subgraph = graph_rag_pipeline(q)
        print(f"SEEDS: {subgraph['seed_nodes']}")
        print(f"\nANSWER:\n{answer}")

    close()
