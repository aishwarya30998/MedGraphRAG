"""
test_build_graph.py — Integration tests for graph/build_graph.py

Verifies the Neo4j graph was loaded correctly after running build_graph.py.

Requires: Neo4j running at localhost:7687
Mark:      @pytest.mark.integration

Run:
    pytest tests/test_build_graph.py -v
"""

import pytest


@pytest.mark.integration
class TestNodeCounts:
    """Verify the correct number of nodes were loaded."""

    def test_disease_node_count(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH (d:Disease) RETURN count(d) AS count").single()
        assert result["count"] == 10, f"Expected 10 Disease nodes, got {result['count']}"

    def test_drug_node_count(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH (d:Drug) RETURN count(d) AS count").single()
        assert result["count"] == 15, f"Expected 15 Drug nodes, got {result['count']}"

    def test_symptom_node_count(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH (s:Symptom) RETURN count(s) AS count").single()
        assert result["count"] == 24, f"Expected 24 Symptom nodes, got {result['count']}"

    def test_gene_node_count(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH (g:Gene) RETURN count(g) AS count").single()
        assert result["count"] == 6, f"Expected 6 Gene nodes, got {result['count']}"


@pytest.mark.integration
class TestRelationshipCounts:
    """Verify relationships were created."""

    def test_has_symptom_relationships_exist(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH ()-[r:HAS_SYMPTOM]->() RETURN count(r) AS count").single()
        assert result["count"] > 0, "No HAS_SYMPTOM relationships found"

    def test_treats_relationships_exist(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH ()-[r:TREATS]->() RETURN count(r) AS count").single()
        assert result["count"] > 0, "No TREATS relationships found"

    def test_interacts_with_relationships_exist(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) AS count").single()
        assert result["count"] > 0, "No INTERACTS_WITH relationships found"

    def test_comorbid_with_relationships_exist(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH ()-[r:COMORBID_WITH]->() RETURN count(r) AS count").single()
        assert result["count"] > 0, "No COMORBID_WITH relationships found"

    def test_associated_with_relationships_exist(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH ()-[r:ASSOCIATED_WITH]->() RETURN count(r) AS count").single()
        assert result["count"] > 0, "No ASSOCIATED_WITH relationships found"

    def test_interacts_with_is_bidirectional(self, neo4j_driver):
        """Warfarin <-> Aspirin should exist in both directions."""
        with neo4j_driver.session() as s:
            fwd = s.run(
                "MATCH (a:Drug {name:'Warfarin'})-[:INTERACTS_WITH]->(b:Drug {name:'Aspirin'}) RETURN count(*) AS c"
            ).single()["c"]
            rev = s.run(
                "MATCH (a:Drug {name:'Aspirin'})-[:INTERACTS_WITH]->(b:Drug {name:'Warfarin'}) RETURN count(*) AS c"
            ).single()["c"]
        assert fwd == 1, "Warfarin->Aspirin interaction missing"
        assert rev == 1, "Aspirin->Warfarin interaction missing (should be bidirectional)"


@pytest.mark.integration
class TestNodeProperties:
    """Verify specific node properties were stored correctly."""

    def test_diabetes_has_icd_code(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run(
                "MATCH (d:Disease {name: 'Type 2 Diabetes Mellitus'}) RETURN d.icd_code AS icd"
            ).single()
        assert result is not None, "Type 2 Diabetes Mellitus not found"
        assert result["icd"] == "E11"

    def test_metformin_has_drug_class(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run(
                "MATCH (d:Drug {name: 'Metformin'}) RETURN d.drug_class AS cls"
            ).single()
        assert result is not None, "Metformin not found"
        assert result["cls"] == "Biguanide"

    def test_warfarin_aspirin_interaction_severity(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run(
                """MATCH (a:Drug {name:'Warfarin'})-[r:INTERACTS_WITH]->(b:Drug {name:'Aspirin'})
                   RETURN r.severity AS severity"""
            ).single()
        assert result is not None
        assert result["severity"] == "Major"

    def test_metformin_treats_diabetes(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run(
                """MATCH (d:Drug {name:'Metformin'})-[r:TREATS]->(dis:Disease {name:'Type 2 Diabetes Mellitus'})
                   RETURN r.evidence AS evidence"""
            ).single()
        assert result is not None, "Metformin TREATS Type 2 Diabetes relationship missing"
        assert result["evidence"] == "Level A"

    def test_diabetes_hypertension_comorbidity(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run(
                """MATCH (a:Disease {name:'Type 2 Diabetes Mellitus'})-[:COMORBID_WITH]->
                          (b:Disease {name:'Hypertension'})
                   RETURN count(*) AS c"""
            ).single()
        assert result["c"] == 1, "Diabetes-Hypertension comorbidity missing"


@pytest.mark.integration
class TestEmbeddings:
    """Verify embeddings were added by enrich_graph.py."""

    def test_disease_nodes_have_embeddings(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run(
                "MATCH (d:Disease) WHERE d.embedding IS NOT NULL RETURN count(d) AS count"
            ).single()
        assert result["count"] == 10, (
            f"Expected 10 Disease nodes with embeddings, got {result['count']}. "
            "Did you run graph/enrich_graph.py?"
        )

    def test_drug_nodes_have_embeddings(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run(
                "MATCH (d:Drug) WHERE d.embedding IS NOT NULL RETURN count(d) AS count"
            ).single()
        assert result["count"] == 15, (
            f"Expected 15 Drug nodes with embeddings, got {result['count']}."
        )

    def test_embedding_is_correct_dimension(self, neo4j_driver):
        """all-MiniLM-L6-v2 produces 384-dimensional embeddings."""
        with neo4j_driver.session() as s:
            result = s.run(
                "MATCH (d:Disease) WHERE d.embedding IS NOT NULL RETURN d.embedding AS emb LIMIT 1"
            ).single()
        assert result is not None
        assert len(result["emb"]) == 384, f"Expected 384-dim embedding, got {len(result['emb'])}"
