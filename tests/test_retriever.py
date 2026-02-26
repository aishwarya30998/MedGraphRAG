"""
test_retriever.py — Integration tests for rag/retriever.py

Verifies that vector seed search + graph traversal works correctly.

Requires: Neo4j running with embeddings loaded
Mark:      @pytest.mark.integration

Run:
    pytest tests/test_retriever.py -v
"""

import pytest
from rag.retriever import retrieve_subgraph


@pytest.mark.integration
class TestRetrieverOutputStructure:
    """Verify the return structure of retrieve_subgraph()."""

    def test_returns_dict(self, neo4j_driver):
        result = retrieve_subgraph("What drugs treat diabetes?", driver=neo4j_driver)
        assert isinstance(result, dict)

    def test_has_required_keys(self, neo4j_driver):
        result = retrieve_subgraph("What drugs treat diabetes?", driver=neo4j_driver)
        assert "query" in result
        assert "seed_nodes" in result
        assert "disease_contexts" in result
        assert "drug_contexts" in result

    def test_seed_nodes_has_diseases_and_drugs_keys(self, neo4j_driver):
        result = retrieve_subgraph("What drugs treat diabetes?", driver=neo4j_driver)
        assert "diseases" in result["seed_nodes"]
        assert "drugs" in result["seed_nodes"]

    def test_query_preserved_in_result(self, neo4j_driver):
        q = "What drugs treat diabetes?"
        result = retrieve_subgraph(q, driver=neo4j_driver)
        assert result["query"] == q


@pytest.mark.integration
class TestVectorSeedSearch:
    """Verify the right seed nodes are returned for specific queries."""

    def test_diabetes_query_returns_diabetes_seed(self, neo4j_driver):
        result = retrieve_subgraph("Type 2 Diabetes treatment", driver=neo4j_driver)
        all_seeds = result["seed_nodes"]["diseases"] + result["seed_nodes"]["drugs"]
        assert len(all_seeds) > 0, "No seed nodes returned"
        assert "Type 2 Diabetes Mellitus" in result["seed_nodes"]["diseases"], (
            f"Expected Type 2 Diabetes Mellitus in seeds, got: {result['seed_nodes']}"
        )

    def test_chest_pain_query_returns_cardiovascular_disease(self, neo4j_driver):
        result = retrieve_subgraph(
            "What diseases cause chest pain and shortness of breath?",
            driver=neo4j_driver
        )
        diseases = result["seed_nodes"]["diseases"]
        cardiovascular = {"Coronary Artery Disease", "Asthma", "Atrial Fibrillation"}
        assert any(d in cardiovascular for d in diseases), (
            f"Expected a cardiovascular disease in seeds, got: {diseases}"
        )

    def test_warfarin_query_returns_warfarin_seed(self, neo4j_driver):
        result = retrieve_subgraph(
            "What are the interactions of warfarin?",
            driver=neo4j_driver
        )
        assert "Warfarin" in result["seed_nodes"]["drugs"], (
            f"Expected Warfarin in drug seeds, got: {result['seed_nodes']['drugs']}"
        )

    def test_top_k_limits_total_seeds(self, neo4j_driver):
        result = retrieve_subgraph("diabetes", driver=neo4j_driver, top_k=2)
        total_seeds = (
            len(result["seed_nodes"]["diseases"]) +
            len(result["seed_nodes"]["drugs"])
        )
        assert total_seeds <= 2, f"top_k=2 should return at most 2 seeds, got {total_seeds}"


@pytest.mark.integration
class TestGraphTraversal:
    """Verify that graph traversal returns proper context from seed nodes."""

    def test_diabetes_context_has_symptoms(self, neo4j_driver):
        result = retrieve_subgraph("Type 2 Diabetes symptoms", driver=neo4j_driver)
        contexts = result["disease_contexts"]
        assert len(contexts) > 0, "No disease contexts returned"
        # Find diabetes context
        diabetes_ctx = next(
            (c for c in contexts if "Diabetes" in c.get("disease", "")), None
        )
        assert diabetes_ctx is not None, "No Diabetes context found"
        assert len(diabetes_ctx["symptoms"]) > 0, "Diabetes context has no symptoms"

    def test_diabetes_context_has_treatments(self, neo4j_driver):
        result = retrieve_subgraph("Type 2 Diabetes treatment", driver=neo4j_driver)
        contexts = result["disease_contexts"]
        diabetes_ctx = next(
            (c for c in contexts if "Diabetes" in c.get("disease", "")), None
        )
        assert diabetes_ctx is not None
        assert len(diabetes_ctx["treatments"]) > 0, "Diabetes context has no treatments"
        drug_names = [t["drug"] for t in diabetes_ctx["treatments"]]
        assert "Metformin" in drug_names, f"Metformin not in treatments: {drug_names}"

    def test_drug_context_has_interactions(self, neo4j_driver):
        result = retrieve_subgraph("warfarin drug interactions", driver=neo4j_driver)
        drug_contexts = result["drug_contexts"]
        warfarin_ctx = next(
            (c for c in drug_contexts if c.get("drug") == "Warfarin"), None
        )
        assert warfarin_ctx is not None, "No Warfarin context found in drug_contexts"
        assert len(warfarin_ctx["interactions"]) > 0, "Warfarin has no interactions in context"

    def test_disease_context_has_comorbidities(self, neo4j_driver):
        result = retrieve_subgraph("Type 2 Diabetes comorbidities", driver=neo4j_driver)
        contexts = result["disease_contexts"]
        diabetes_ctx = next(
            (c for c in contexts if "Diabetes" in c.get("disease", "")), None
        )
        assert diabetes_ctx is not None
        assert len(diabetes_ctx["comorbidities"]) > 0, "Diabetes has no comorbidities in context"
