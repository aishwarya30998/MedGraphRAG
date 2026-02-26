"""
test_api.py — Integration tests for api/app.py (FastAPI endpoints)

Uses FastAPI's TestClient (no real server needed).
Graph endpoints require Neo4j. /query endpoint also requires Ollama.

Requires: Neo4j running
Mark:      @pytest.mark.integration (graph endpoints)
           @pytest.mark.llm (query endpoint)

Run:
    pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


# Health check — no infrastructure needed

class TestHealthCheck:

    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_ok_status(self):
        response = client.get("/")
        data = response.json()
        assert data["status"] == "ok"

    def test_root_returns_service_name(self):
        response = client.get("/")
        data = response.json()
        assert "MedGraphRAG" in data["service"]

    def test_root_returns_version(self):
        response = client.get("/")
        data = response.json()
        assert "version" in data


# Graph endpoints — require Neo4j

@pytest.mark.integration
class TestGraphEndpoints:

    def test_stats_returns_200(self, neo4j_driver):
        response = client.get("/graph/stats")
        assert response.status_code == 200

    def test_stats_has_nodes_key(self, neo4j_driver):
        response = client.get("/graph/stats")
        data = response.json()
        assert "nodes" in data

    def test_stats_has_relationships_key(self, neo4j_driver):
        response = client.get("/graph/stats")
        data = response.json()
        assert "relationships" in data

    def test_stats_node_counts_nonzero(self, neo4j_driver):
        response = client.get("/graph/stats")
        data = response.json()
        total_nodes = sum(item["count"] for item in data["nodes"])
        assert total_nodes > 0, "Graph appears empty — run build_graph.py"

    def test_diseases_returns_200(self, neo4j_driver):
        response = client.get("/graph/diseases")
        assert response.status_code == 200

    def test_diseases_returns_list(self, neo4j_driver):
        response = client.get("/graph/diseases")
        data = response.json()
        assert "diseases" in data
        assert isinstance(data["diseases"], list)

    def test_diseases_count_correct(self, neo4j_driver):
        response = client.get("/graph/diseases")
        data = response.json()
        assert len(data["diseases"]) == 10, (
            f"Expected 10 diseases, got {len(data['diseases'])}"
        )

    def test_diseases_have_name_and_icd(self, neo4j_driver):
        response = client.get("/graph/diseases")
        diseases = response.json()["diseases"]
        for d in diseases:
            assert "name" in d
            assert "icd_code" in d

    def test_drugs_returns_200(self, neo4j_driver):
        response = client.get("/graph/drugs")
        assert response.status_code == 200

    def test_drugs_returns_list(self, neo4j_driver):
        response = client.get("/graph/drugs")
        data = response.json()
        assert "drugs" in data
        assert isinstance(data["drugs"], list)

    def test_drugs_count_correct(self, neo4j_driver):
        response = client.get("/graph/drugs")
        data = response.json()
        assert len(data["drugs"]) == 15, (
            f"Expected 15 drugs, got {len(data['drugs'])}"
        )


# Query endpoint — requires Neo4j + Ollama

@pytest.mark.integration
@pytest.mark.llm
class TestQueryEndpoint:

    def test_query_returns_200(self, neo4j_driver, ollama_client):
        response = client.post(
            "/query",
            json={"question": "What drugs treat Type 2 Diabetes?", "top_k": 3}
        )
        assert response.status_code == 200, f"Response: {response.text}"

    def test_query_response_has_answer(self, neo4j_driver, ollama_client):
        response = client.post(
            "/query",
            json={"question": "What drugs treat Type 2 Diabetes?"}
        )
        data = response.json()
        assert "answer" in data
        assert len(data["answer"].strip()) > 0

    def test_query_response_has_seed_nodes(self, neo4j_driver, ollama_client):
        response = client.post(
            "/query",
            json={"question": "What drugs treat Type 2 Diabetes?"}
        )
        data = response.json()
        assert "seed_nodes" in data
        assert "diseases" in data["seed_nodes"]
        assert "drugs" in data["seed_nodes"]

    def test_query_response_has_contexts(self, neo4j_driver, ollama_client):
        response = client.post(
            "/query",
            json={"question": "What drugs treat Type 2 Diabetes?"}
        )
        data = response.json()
        assert "disease_contexts" in data
        assert "drug_contexts" in data

    def test_query_response_echoes_question(self, neo4j_driver, ollama_client):
        q = "What drugs treat Type 2 Diabetes?"
        response = client.post("/query", json={"question": q})
        data = response.json()
        assert data["question"] == q


@pytest.mark.integration
class TestQueryValidation:
    """Validation tests that only need the API layer — no Ollama required."""

    def test_empty_question_returns_400(self, neo4j_driver):
        response = client.post("/query", json={"question": ""})
        assert response.status_code == 400

    def test_whitespace_question_returns_400(self, neo4j_driver):
        response = client.post("/query", json={"question": "   "})
        assert response.status_code == 400

    def test_missing_question_field_returns_422(self):
        response = client.post("/query", json={})
        assert response.status_code == 422
