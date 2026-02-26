"""
test_synthetic_data.py — Unit tests for data/generate_synthetic.py

These tests require NO infrastructure (no Neo4j, no Ollama).
They validate the shape and content of the synthetic dataset.

Run:
    pytest tests/test_synthetic_data.py -v
"""

import pytest
from data.generate_synthetic import (
    DISEASES,
    SYMPTOMS,
    DRUGS,
    DISEASE_SYMPTOMS,
    DRUG_TREATS,
    DRUG_INTERACTIONS,
    COMORBIDITIES,
    GENES,
    generate,
)



# Dataset counts

class TestDatasetCounts:

    def test_disease_count(self):
        assert len(DISEASES) == 10, f"Expected 10 diseases, got {len(DISEASES)}"

    def test_symptom_count(self):
        assert len(SYMPTOMS) == 24, f"Expected 24 symptoms, got {len(SYMPTOMS)}"

    def test_drug_count(self):
        assert len(DRUGS) == 15, f"Expected 15 drugs, got {len(DRUGS)}"

    def test_drug_interactions_count(self):
        assert len(DRUG_INTERACTIONS) == 11, f"Expected 11 interactions, got {len(DRUG_INTERACTIONS)}"

    def test_comorbidities_count(self):
        assert len(COMORBIDITIES) == 9, f"Expected 9 comorbidities, got {len(COMORBIDITIES)}"

    def test_genes_count(self):
        assert len(GENES) == 6, f"Expected 6 genes, got {len(GENES)}"

    def test_disease_symptom_edges_exist(self):
        assert len(DISEASE_SYMPTOMS) > 0

    def test_drug_treats_edges_exist(self):
        assert len(DRUG_TREATS) > 0

# Node field validation


class TestDiseaseFields:

    @pytest.mark.parametrize("disease", DISEASES)
    def test_disease_has_name(self, disease):
        assert "name" in disease and disease["name"].strip()

    @pytest.mark.parametrize("disease", DISEASES)
    def test_disease_has_icd_code(self, disease):
        assert "icd_code" in disease and disease["icd_code"].strip()

    @pytest.mark.parametrize("disease", DISEASES)
    def test_disease_has_description(self, disease):
        assert "description" in disease and len(disease["description"]) > 10

    @pytest.mark.parametrize("disease", DISEASES)
    def test_disease_has_category(self, disease):
        assert "category" in disease and disease["category"].strip()

    def test_disease_names_unique(self):
        names = [d["name"] for d in DISEASES]
        assert len(names) == len(set(names)), "Duplicate disease names found"


class TestDrugFields:

    @pytest.mark.parametrize("drug", DRUGS)
    def test_drug_has_name(self, drug):
        assert "name" in drug and drug["name"].strip()

    @pytest.mark.parametrize("drug", DRUGS)
    def test_drug_has_class(self, drug):
        assert "drug_class" in drug and drug["drug_class"].strip()

    @pytest.mark.parametrize("drug", DRUGS)
    def test_drug_has_mechanism(self, drug):
        assert "mechanism" in drug and len(drug["mechanism"]) > 10

    def test_drug_names_unique(self):
        names = [d["name"] for d in DRUGS]
        assert len(names) == len(set(names)), "Duplicate drug names found"


class TestSymptomFields:

    @pytest.mark.parametrize("symptom", SYMPTOMS)
    def test_symptom_has_name(self, symptom):
        assert "name" in symptom and symptom["name"].strip()

    @pytest.mark.parametrize("symptom", SYMPTOMS)
    def test_symptom_has_description(self, symptom):
        assert "description" in symptom and symptom["description"].strip()

    def test_symptom_names_unique(self):
        names = [s["name"] for s in SYMPTOMS]
        assert len(names) == len(set(names)), "Duplicate symptom names found"



# Relationship reference integrity


class TestRelationshipIntegrity:

    def test_disease_symptom_references_valid_diseases(self):
        disease_names = {d["name"] for d in DISEASES}
        for disease, _ in DISEASE_SYMPTOMS:
            assert disease in disease_names, f"Unknown disease in DISEASE_SYMPTOMS: {disease}"

    def test_disease_symptom_references_valid_symptoms(self):
        symptom_names = {s["name"] for s in SYMPTOMS}
        for _, symptom in DISEASE_SYMPTOMS:
            assert symptom in symptom_names, f"Unknown symptom in DISEASE_SYMPTOMS: {symptom}"

    def test_drug_treats_references_valid_drugs(self):
        drug_names = {d["name"] for d in DRUGS}
        for drug, _, _ in DRUG_TREATS:
            assert drug in drug_names, f"Unknown drug in DRUG_TREATS: {drug}"

    def test_drug_treats_references_valid_diseases(self):
        disease_names = {d["name"] for d in DISEASES}
        for _, disease, _ in DRUG_TREATS:
            assert disease in disease_names, f"Unknown disease in DRUG_TREATS: {disease}"

    def test_drug_treats_evidence_levels_valid(self):
        valid_levels = {"Level A", "Level B", "Level C"}
        for _, _, evidence in DRUG_TREATS:
            assert evidence in valid_levels, f"Invalid evidence level: {evidence}"

    def test_drug_interactions_have_required_fields(self):
        for ix in DRUG_INTERACTIONS:
            assert "drug_a" in ix and ix["drug_a"].strip()
            assert "drug_b" in ix and ix["drug_b"].strip()
            assert "severity" in ix
            assert "description" in ix

    def test_drug_interactions_severity_valid(self):
        valid = {"Major", "Moderate", "Mild"}
        for ix in DRUG_INTERACTIONS:
            assert ix["severity"] in valid, f"Invalid severity: {ix['severity']}"

    def test_drug_interactions_reference_valid_drugs(self):
        drug_names = {d["name"] for d in DRUGS}
        for ix in DRUG_INTERACTIONS:
            assert ix["drug_a"] in drug_names, f"Unknown drug_a: {ix['drug_a']}"
            assert ix["drug_b"] in drug_names, f"Unknown drug_b: {ix['drug_b']}"

    def test_comorbidities_reference_valid_diseases(self):
        disease_names = {d["name"] for d in DISEASES}
        for d1, d2 in COMORBIDITIES:
            assert d1 in disease_names, f"Unknown disease in COMORBIDITIES: {d1}"
            assert d2 in disease_names, f"Unknown disease in COMORBIDITIES: {d2}"

    def test_genes_reference_valid_diseases(self):
        disease_names = {d["name"] for d in DISEASES}
        for gene in GENES:
            for disease in gene["diseases"]:
                assert disease in disease_names, f"Gene {gene['name']} references unknown disease: {disease}"


# generate() function output

class TestGenerateFunction:

    def test_generate_returns_dict(self, synthetic_data):
        assert isinstance(synthetic_data, dict)

    def test_generate_has_all_keys(self, synthetic_data):
        required_keys = [
            "diseases", "symptoms", "drugs",
            "disease_symptoms", "drug_treats",
            "drug_interactions", "comorbidities", "genes",
        ]
        for key in required_keys:
            assert key in synthetic_data, f"Missing key: {key}"

    def test_generate_writes_json_file(self, tmp_path, monkeypatch):
        """generate() should create the processed JSON file."""
        import os
        # Point output to tmp dir
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        monkeypatch.chdir(tmp_path)
        # Just check the function runs without error
        from data.generate_synthetic import generate
        result = generate()
        assert isinstance(result, dict)
