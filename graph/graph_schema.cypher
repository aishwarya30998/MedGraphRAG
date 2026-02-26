// ============================================================
// MedGraphRAG — Neo4j Schema Setup
// Run once to create indexes and constraints before loading data
// ============================================================

// --- Constraints (unique IDs) ---
CREATE CONSTRAINT disease_name IF NOT EXISTS
  FOR (d:Disease) REQUIRE d.name IS UNIQUE;

CREATE CONSTRAINT symptom_name IF NOT EXISTS
  FOR (s:Symptom) REQUIRE s.name IS UNIQUE;

CREATE CONSTRAINT drug_name IF NOT EXISTS
  FOR (dr:Drug) REQUIRE dr.name IS UNIQUE;

CREATE CONSTRAINT gene_name IF NOT EXISTS
  FOR (g:Gene) REQUIRE g.name IS UNIQUE;

// --- Indexes for fast lookup ---
CREATE INDEX disease_category IF NOT EXISTS
  FOR (d:Disease) ON (d.category);

CREATE INDEX drug_class IF NOT EXISTS
  FOR (dr:Drug) ON (dr.drug_class);

CREATE INDEX disease_icd IF NOT EXISTS
  FOR (d:Disease) ON (d.icd_code);

// ============================================================
// Relationship types used in this graph:
//
//   (:Disease)-[:HAS_SYMPTOM]->(:Symptom)
//   (:Drug)-[:TREATS {evidence: "Level A/B/C"}]->(:Disease)
//   (:Drug)-[:INTERACTS_WITH {severity: "Major/Moderate/Mild", description: "..."}]->(:Drug)
//   (:Disease)-[:COMORBID_WITH]->(:Disease)
//   (:Gene)-[:ASSOCIATED_WITH]->(:Disease)
// ============================================================
