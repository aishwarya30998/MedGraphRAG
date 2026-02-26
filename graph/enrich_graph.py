"""
enrich_graph.py — Add sentence-transformer embeddings to Neo4j nodes.

Embeds Disease and Drug nodes so that vector similarity search can be used
as the seed step in the Graph RAG retriever.

Usage:
    python graph/enrich_graph.py

Prerequisites:
    1. build_graph.py has already been run (graph is populated)
    2. pip install sentence-transformers
"""

import os
import sys

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "medgraph123")

# Small, fast, free model — ~80MB, no GPU needed
MODEL_NAME = "all-MiniLM-L6-v2"


def get_driver():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    return driver


def embed_disease_nodes(session, model: SentenceTransformer):
    """Embed Disease nodes using name + description."""
    records = session.run(
        "MATCH (d:Disease) RETURN d.name AS name, d.description AS description"
    ).data()

    if not records:
        print("[WARN] No Disease nodes found. Run build_graph.py first.")
        return

    texts = [f"{r['name']}: {r['description']}" for r in records]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=16)

    for record, embedding in zip(records, embeddings):
        session.run(
            """
            MATCH (d:Disease {name: $name})
            SET d.embedding = $embedding
            """,
            name=record["name"],
            embedding=embedding.tolist(),
        )
    print(f"[OK] Embedded {len(records)} Disease nodes.")


def embed_drug_nodes(session, model: SentenceTransformer):
    """Embed Drug nodes using name + mechanism."""
    records = session.run(
        "MATCH (dr:Drug) RETURN dr.name AS name, dr.mechanism AS mechanism, dr.drug_class AS drug_class"
    ).data()

    if not records:
        print("[WARN] No Drug nodes found. Run build_graph.py first.")
        return

    texts = [
        f"{r['name']} ({r['drug_class']}): {r['mechanism']}"
        for r in records
    ]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=16)

    for record, embedding in zip(records, embeddings):
        session.run(
            """
            MATCH (dr:Drug {name: $name})
            SET dr.embedding = $embedding
            """,
            name=record["name"],
            embedding=embedding.tolist(),
        )
    print(f"[OK] Embedded {len(records)} Drug nodes.")


def embed_symptom_nodes(session, model: SentenceTransformer):
    """Embed Symptom nodes using name + description."""
    records = session.run(
        "MATCH (s:Symptom) RETURN s.name AS name, s.description AS description"
    ).data()

    if not records:
        return

    texts = [f"{r['name']}: {r['description']}" for r in records]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    for record, embedding in zip(records, embeddings):
        session.run(
            """
            MATCH (s:Symptom {name: $name})
            SET s.embedding = $embedding
            """,
            name=record["name"],
            embedding=embedding.tolist(),
        )
    print(f"[OK] Embedded {len(records)} Symptom nodes.")


def verify_embeddings(session):
    result = session.run(
        """
        MATCH (n)
        WHERE n.embedding IS NOT NULL
        RETURN labels(n)[0] AS label, count(n) AS count
        """
    ).data()
    print("\n[Embedding Summary]")
    for row in result:
        print(f"  {row['label']}: {row['count']} nodes embedded")


def main():
    print(f"[INFO] Loading embedding model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)
    print("[OK] Model loaded.")

    driver = get_driver()
    print(f"[OK] Connected to Neo4j.")

    with driver.session() as session:
        embed_disease_nodes(session, model)
        embed_drug_nodes(session, model)
        embed_symptom_nodes(session, model)
        verify_embeddings(session)

    driver.close()
    print("\n[DONE] All node embeddings stored in Neo4j.")


if __name__ == "__main__":
    main()
