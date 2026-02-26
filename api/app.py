"""
app.py — FastAPI REST API for MedGraphRAG. 
Not used in local Streamlit UI but might be useful when used in other frontend applications or for direct API access.

Endpoints:
  GET  /              → Health check
  POST /query         → Run Graph RAG pipeline
  GET  /graph/stats   → Neo4j graph statistics
  GET  /graph/diseases → List all diseases
  GET  /graph/drugs    → List all drugs
"""

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "medgraph123")

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver



# App lifecycle

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify Neo4j connection
    try:
        get_driver().verify_connectivity()
    except Exception as exc:
        print(f"[WARN] Neo4j not reachable on startup: {exc}")
    yield
    # Shutdown: close driver
    global _driver
    if _driver:
        _driver.close()
        _driver = None


app = FastAPI(
    title="MedGraphRAG API",
    description="Graph-powered medical Q&A using Neo4j + Ollama",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



# Request / Response schemas

class QueryRequest(BaseModel):
    question: str
    top_k: int = 3


class QueryResponse(BaseModel):
    question: str
    answer: str
    seed_nodes: dict[str, list[str]]
    disease_contexts: list[dict[str, Any]]
    drug_contexts: list[dict[str, Any]]



# Routes

@app.get("/")
def health_check():
    return {"status": "ok", "service": "MedGraphRAG API", "version": "0.4.0"}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # Import here to avoid circular import issues at module load time
        from rag.pipeline import graph_rag_pipeline
        answer, subgraph = graph_rag_pipeline(req.question, top_k=req.top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return QueryResponse(
        question=req.question,
        answer=answer,
        seed_nodes=subgraph["seed_nodes"],
        disease_contexts=subgraph["disease_contexts"],
        drug_contexts=subgraph["drug_contexts"],
    )


@app.get("/graph/stats")
def graph_stats():
    try:
        with get_driver().session() as session:
            result = session.run(
                """
                MATCH (n)
                RETURN labels(n)[0] AS label, count(n) AS count
                ORDER BY count DESC
                """
            ).data()
            rel_result = session.run(
                "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY count DESC"
            ).data()
        return {"nodes": result, "relationships": rel_result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/graph/diseases")
def list_diseases():
    try:
        with get_driver().session() as session:
            records = session.run(
                "MATCH (d:Disease) RETURN d.name AS name, d.icd_code AS icd_code, d.category AS category ORDER BY d.name"
            ).data()
        return {"diseases": records}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/graph/drugs")
def list_drugs():
    try:
        with get_driver().session() as session:
            records = session.run(
                "MATCH (dr:Drug) RETURN dr.name AS name, dr.drug_class AS drug_class ORDER BY dr.name"
            ).data()
        return {"drugs": records}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
