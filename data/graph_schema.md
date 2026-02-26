# MedGraphRAG — Knowledge Graph Schema

## Node Types

| Label     | Key Properties                                      | Description                         |
|-----------|-----------------------------------------------------|-------------------------------------|
| Disease   | name (unique), icd_code, description, category, embedding | A medical condition or diagnosis |
| Symptom   | name (unique), description, embedding               | A clinical sign or patient symptom  |
| Drug      | name (unique), drug_class, mechanism, embedding     | A pharmaceutical agent              |
| Gene      | name (unique), full_name                            | A human gene associated with disease|

## Relationship Types

| Relationship       | From    | To      | Properties                          |
|--------------------|---------|---------|-------------------------------------|
| HAS_SYMPTOM        | Disease | Symptom | —                                   |
| TREATS             | Drug    | Disease | evidence ("Level A / B / C")        |
| INTERACTS_WITH     | Drug    | Drug    | severity, description (bidirectional)|
| COMORBID_WITH      | Disease | Disease | — (bidirectional)                   |
| ASSOCIATED_WITH    | Gene    | Disease | —                                   |

## Graph Diagram (ASCII)

```
(:Gene)
   |
   | ASSOCIATED_WITH
   v
(:Disease) ──HAS_SYMPTOM──> (:Symptom)
   ^
   | TREATS
(:Drug) ──INTERACTS_WITH──> (:Drug)

(:Disease) ──COMORBID_WITH──> (:Disease)
```

## Example Cypher Queries

### Find treatments for a disease
```cypher
MATCH (dr:Drug)-[t:TREATS]->(d:Disease {name: "Type 2 Diabetes Mellitus"})
RETURN dr.name, t.evidence
ORDER BY t.evidence;
```

### Find drug interactions
```cypher
MATCH (a:Drug {name: "Warfarin"})-[ix:INTERACTS_WITH]->(b:Drug)
RETURN b.name, ix.severity, ix.description
ORDER BY ix.severity;
```

### Find diseases by symptom
```cypher
MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom {name: "Chest Pain"})
RETURN d.name, d.category;
```

### Find comorbid diseases
```cypher
MATCH (d:Disease {name: "Type 2 Diabetes Mellitus"})-[:COMORBID_WITH]->(c:Disease)
RETURN c.name;
```

### Find genes associated with a disease
```cypher
MATCH (g:Gene)-[:ASSOCIATED_WITH]->(d:Disease {name: "Hypertension"})
RETURN g.name, g.full_name;
```
