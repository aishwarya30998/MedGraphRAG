"""
build_graph.py — Load synthetic medical data into Neo4j.

Usage:
    python graph/build_graph.py

Prerequisites:
    1. Neo4j running (via docker-compose up -d)
    2. Synthetic data generated (python data/generate_synthetic.py)
    3. pip install -r requirements.txt
"""

import json
import os
import sys
import time

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "medgraph123")

DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed", "synthetic_medical_data.json"
)


# Connection helper

def get_driver(retries: int = 10, delay: int = 3):
    """Retry connecting to Neo4j — useful when container is still booting."""
    for attempt in range(1, retries + 1):
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            driver.verify_connectivity()
            print(f"[OK] Connected to Neo4j at {NEO4J_URI}")
            return driver
        except Exception as exc:
            print(f"[{attempt}/{retries}] Neo4j not ready yet: {exc}. Retrying in {delay}s...")
            time.sleep(delay)
    print("[ERROR] Could not connect to Neo4j after multiple attempts. Is it running?")
    sys.exit(1)


# Schema / constraints

def apply_schema(session):
    schema_path = os.path.join(os.path.dirname(__file__), "graph_schema.cypher")
    with open(schema_path) as f:
        raw = f.read()

    # Split on semicolons and run each non-empty statement
    statements = [s.strip() for s in raw.split(";") if s.strip() and not s.strip().startswith("//")]
    for stmt in statements:
        try:
            session.run(stmt)
        except Exception as exc:
            # Constraint/index already exists — safe to ignore
            if "already exists" not in str(exc).lower():
                print(f"[WARN] Schema statement failed: {exc}")
    print("[OK] Schema constraints and indexes applied.")



# Node creation

def load_diseases(session, diseases):
    for d in diseases:
        session.run(
            """
            MERGE (n:Disease {name: $name})
            SET n.icd_code = $icd_code,
                n.description = $description,
                n.category = $category
            """,
            name=d["name"],
            icd_code=d["icd_code"],
            description=d["description"],
            category=d["category"],
        )
    print(f"[OK] Loaded {len(diseases)} Disease nodes.")


def load_symptoms(session, symptoms):
    for s in symptoms:
        session.run(
            """
            MERGE (n:Symptom {name: $name})
            SET n.description = $description
            """,
            name=s["name"],
            description=s["description"],
        )
    print(f"[OK] Loaded {len(symptoms)} Symptom nodes.")


def load_drugs(session, drugs):
    for d in drugs:
        session.run(
            """
            MERGE (n:Drug {name: $name})
            SET n.drug_class = $drug_class,
                n.mechanism = $mechanism
            """,
            name=d["name"],
            drug_class=d["drug_class"],
            mechanism=d["mechanism"],
        )
    print(f"[OK] Loaded {len(drugs)} Drug nodes.")


def load_genes(session, genes):
    for g in genes:
        session.run(
            """
            MERGE (n:Gene {name: $name})
            SET n.full_name = $full_name
            """,
            name=g["name"],
            full_name=g["full_name"],
        )
    print(f"[OK] Loaded {len(genes)} Gene nodes.")



# Relationship creation

def load_disease_symptoms(session, edges):
    for disease, symptom in edges:
        session.run(
            """
            MATCH (d:Disease {name: $disease})
            MATCH (s:Symptom {name: $symptom})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
            """,
            disease=disease,
            symptom=symptom,
        )
    print(f"[OK] Loaded {len(edges)} HAS_SYMPTOM relationships.")


def load_drug_treats(session, edges):
    for drug, disease, evidence in edges:
        session.run(
            """
            MATCH (dr:Drug {name: $drug})
            MATCH (d:Disease {name: $disease})
            MERGE (dr)-[r:TREATS]->(d)
            SET r.evidence = $evidence
            """,
            drug=drug,
            disease=disease,
            evidence=evidence,
        )
    print(f"[OK] Loaded {len(edges)} TREATS relationships.")


def load_drug_interactions(session, interactions):
    for item in interactions:
        session.run(
            """
            MATCH (a:Drug {name: $drug_a})
            MATCH (b:Drug {name: $drug_b})
            MERGE (a)-[r:INTERACTS_WITH]->(b)
            SET r.severity = $severity,
                r.description = $description
            MERGE (b)-[r2:INTERACTS_WITH]->(a)
            SET r2.severity = $severity,
                r2.description = $description
            """,
            drug_a=item["drug_a"],
            drug_b=item["drug_b"],
            severity=item["severity"],
            description=item["description"],
        )
    print(f"[OK] Loaded {len(interactions)} INTERACTS_WITH relationships (bidirectional).")


def load_comorbidities(session, pairs):
    for d1, d2 in pairs:
        session.run(
            """
            MATCH (a:Disease {name: $d1})
            MATCH (b:Disease {name: $d2})
            MERGE (a)-[:COMORBID_WITH]->(b)
            MERGE (b)-[:COMORBID_WITH]->(a)
            """,
            d1=d1,
            d2=d2,
        )
    print(f"[OK] Loaded {len(pairs)} COMORBID_WITH relationships (bidirectional).")


def load_gene_associations(session, genes):
    for g in genes:
        for disease in g["diseases"]:
            session.run(
                """
                MATCH (gene:Gene {name: $gene})
                MATCH (d:Disease {name: $disease})
                MERGE (gene)-[:ASSOCIATED_WITH]->(d)
                """,
                gene=g["name"],
                disease=disease,
            )
    total = sum(len(g["diseases"]) for g in genes)
    print(f"[OK] Loaded {total} ASSOCIATED_WITH relationships.")



# Main

def main():
    # 1. Load data file
    if not os.path.exists(DATA_PATH):
        print(f"[INFO] Data file not found at {DATA_PATH}. Generating now...")
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from data.generate_synthetic import generate
        generate()

    with open(DATA_PATH) as f:
        data = json.load(f)

    # 2. Connect
    driver = get_driver()

    with driver.session() as session:
        # 3. Schema
        apply_schema(session)

        # 4. Nodes
        load_diseases(session, data["diseases"])
        load_symptoms(session, data["symptoms"])
        load_drugs(session, data["drugs"])
        load_genes(session, data["genes"])

        # 5. Relationships
        load_disease_symptoms(session, data["disease_symptoms"])
        load_drug_treats(session, data["drug_treats"])
        load_drug_interactions(session, data["drug_interactions"])
        load_comorbidities(session, data["comorbidities"])
        load_gene_associations(session, data["genes"])

    driver.close()
    print("\n[DONE] Knowledge graph loaded successfully!")
    print("       Open http://localhost:7474 in your browser to explore it.")


if __name__ == "__main__":
    main()
