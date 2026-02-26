# MedGraphRAG 🏥

A fully local, open-source **Graph RAG** system for medical Q&A.
Answer clinical questions by traversing a medical knowledge graph of diseases, symptoms, drugs, interactions, and genes — powered by **Neo4j + Ollama + sentence-transformers**. Zero cloud, zero cost.

> ⚠️ **Disclaimer:** This project is for educational and research purposes only.
> It is NOT intended for real clinical decision-making. Always consult a licensed clinician.

---

## Example Queries

- *"What are the drug interactions between warfarin and aspirin?"*
- *"What diseases are associated with chest pain and shortness of breath?"*
- *"What is the treatment protocol for Type 2 Diabetes?"*
- *"What genes are associated with hypertension?"*
- *"What diseases commonly co-occur with Type 2 Diabetes?"*

---

## Architecture

```
User query
    │
    ▼
[Sentence Transformer]       ← embeds query (all-MiniLM-L6-v2)
    │  cosine similarity
    ▼
[Neo4j – vector seed search] ← finds top-k most similar Disease/Drug nodes
    │  graph traversal
    ▼
[Subgraph context]           ← symptoms, treatments, interactions, comorbidities, genes
    │
    ▼
[Ollama – llama3.2:3b]       ← grounded answer generation (runs locally)
    │
    ▼
Answer + structured context
```

---

## Tech Stack

| Component   | Tool                                      | Cost  |
|-------------|-------------------------------------------|-------|
| LLM         | Ollama — llama3.2:3b (runs locally)       | Free  |
| Graph DB    | Neo4j 5 Community Edition (Docker)        | Free  |
| Embeddings  | sentence-transformers all-MiniLM-L6-v2    | Free  |
| Backend API | FastAPI                                   | Free  |
| Frontend UI | Streamlit                                 | Free  |

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.10 – 3.13 | [python.org](https://python.org) |
| Docker Desktop | Latest | [docker.com](https://www.docker.com/products/docker-desktop/) |
| Ollama | Latest | [ollama.ai](https://ollama.ai) |

---

## Quick Start (Local Development)

### 1. Clone the repo

```bash
git clone https://github.com/aishwarya30998/MedGraphRAG.git
cd MedGraphRAG
```

### 2. Pull the LLM model

```bash
ollama pull llama3.2:3b
```

> Downloads ~2GB. Only needed once.

### 3. Create a virtual environment

```bash
python -m venv venv

# Mac / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Create your `.env` file

Create a file named `.env` in the project root with this content:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=medgraph123
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
APP_PORT=8501
```

### 6. Start Neo4j

```bash
docker-compose up -d neo4j
```

Wait ~15 seconds, then verify at **http://localhost:7474**
(login: `neo4j` / `medgraph123`)

### 7. Load the knowledge graph (run once)

```bash
python data/generate_synthetic.py   # creates the dataset
python graph/build_graph.py         # loads it into Neo4j
python graph/enrich_graph.py        # adds embeddings to nodes
```

> ✅ Run these only once. Data persists in the Docker volume across restarts.

### 8. Launch the Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

Open **http://localhost:8501** and start asking questions!

---

## Docker Setup (Auto-start, No Terminal Needed)

Run the full stack from Docker — Neo4j + Streamlit app start together:

```bash
# First time: build and start
docker-compose up --build -d

# First time only: init the graph inside the container
docker exec medgraph-app python data/generate_synthetic.py
docker exec medgraph-app python graph/build_graph.py
docker exec medgraph-app python graph/enrich_graph.py
```

Open **http://localhost:8501** — done.

Every subsequent start:
```bash
docker-compose up -d
```

> **Note:** Ollama must be running natively on your Mac/Linux machine. It connects from Docker via `host.docker.internal`.

---

## Optional: REST API

```bash
uvicorn api.app:app --reload --port 8000
```

Interactive docs at **http://localhost:8000/docs**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Run a Graph RAG query |
| `/graph/stats` | GET | Node and relationship counts |
| `/graph/diseases` | GET | List all diseases |
| `/graph/drugs` | GET | List all drugs |

---

## Testing

The project includes a full **pytest** test suite covering all modules. Tests are organized into three categories based on infrastructure requirements.

### Test Categories

| Category | Marker | Infrastructure Needed | Speed |
|----------|--------|----------------------|-------|
| Unit | *(no marker)* | None — pure Python | ⚡ ~0.1s |
| Integration | `@pytest.mark.integration` | Neo4j running + graph loaded | 🐢 seconds |
| LLM | `@pytest.mark.llm` | Ollama running with llama3.2:3b | 🐢 seconds |

> Integration and LLM tests **auto-skip** gracefully if Neo4j or Ollama is not available — they will never fail your CI pipeline just because infra is down.

### Run the Tests

**Unit tests only** (no infrastructure needed — runs anywhere):
```bash
pytest tests/test_synthetic_data.py -v
```

**Integration tests** (requires Neo4j with graph loaded):
```bash
pytest -m integration -v
```

**LLM tests** (requires Ollama):
```bash
pytest -m llm -v
```

**All tests** (requires Neo4j + Ollama):
```bash
pytest -v
```

**Skip slow LLM tests, run everything else:**
```bash
pytest -m "not llm" -v
```

### Test Files

| File | Marker | What It Tests |
|------|--------|---------------|
| `tests/test_synthetic_data.py` | *(unit)* | Dataset integrity — node counts, required fields, relationship consistency |
| `tests/test_build_graph.py` | `integration` | Neo4j node/relationship counts, property values, embedding dimensions |
| `tests/test_retriever.py` | `integration` | Vector seed search accuracy, graph traversal, top_k limiting |
| `tests/test_generator.py` | `llm` | LLM output format, grounding on context, edge cases (empty subgraph) |
| `tests/test_pipeline.py` | `integration` + `llm` | Full end-to-end pipeline: correct answer content, top_k behavior |
| `tests/test_api.py` | `integration` + `llm` | FastAPI endpoints — status codes, response structure, validation |

### Example Output

```
tests/test_synthetic_data.py ..................................................  [ 32%]
tests/test_build_graph.py ....................                                  [ 65%]
tests/test_retriever.py ................                                        [ 75%]
...
157 passed in 0.06s
```

---

## Project Structure

```
MedGraphRAG/
├── data/
│   ├── generate_synthetic.py   # Defines diseases, drugs, symptoms, interactions
│   ├── processed/              # Generated JSON (auto-created, git-ignored)
│   └── graph_schema.md         # Graph node/edge documentation
├── graph/
│   ├── build_graph.py          # Loads data into Neo4j
│   ├── graph_schema.cypher     # Neo4j constraints and indexes
│   └── enrich_graph.py         # Adds sentence-transformer embeddings to nodes
├── rag/
│   ├── retriever.py            # Vector seed search + graph traversal
│   ├── generator.py            # Ollama LLM prompt builder + answer generation
│   └── pipeline.py             # Full RAG pipeline (retriever + generator)
├── api/
│   └── app.py                  # FastAPI REST endpoints
├── ui/
│   └── streamlit_app.py        # Streamlit chat UI
├── tests/
│   ├── conftest.py             # Shared fixtures: neo4j_driver, ollama_client, synthetic_data
│   ├── test_synthetic_data.py  # Unit tests — no infrastructure needed
│   ├── test_build_graph.py     # Integration — verifies Neo4j graph contents
│   ├── test_retriever.py       # Integration — vector search + graph traversal
│   ├── test_generator.py       # LLM — Ollama answer generation
│   ├── test_pipeline.py        # Integration + LLM — full end-to-end pipeline
│   └── test_api.py             # Integration + LLM — FastAPI endpoint tests
├── Dockerfile                  # Packages Streamlit app into Docker image
├── docker-compose.yml          # Runs Neo4j + app together
├── requirements.txt            # Python dependencies
└── .env                        # Local config (git-ignored — create manually)
```

---

## Knowledge Graph Contents

| Type | Count | Examples |
|------|-------|---------|
| Diseases | 10 | Type 2 Diabetes, Hypertension, COPD, Atrial Fibrillation |
| Drugs | 15 | Metformin, Warfarin, Aspirin, Lisinopril, Atorvastatin |
| Symptoms | 24 | Chest Pain, Shortness of Breath, Fatigue, Polyuria |
| Drug Interactions | 11 | Warfarin+Aspirin (Major), Metformin+Aspirin (Mild) |
| Comorbidities | 9 | Diabetes↔Hypertension, COPD↔Asthma |
| Genes | 6 | TCF7L2, ACE, APOE, NPPA |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `pip install` fails with Rust/pydantic error | Check `python --version` — needs 3.10–3.13 |
| Neo4j connection refused | Run `docker-compose up -d neo4j` and wait 15s |
| Ollama not reachable | Make sure Ollama is running: `ollama list` |
| No answer shown in UI | Run `python graph/enrich_graph.py` — embeddings are required |
| `ModuleNotFoundError: rag` | Run from project root: `python -m rag.pipeline` |
| Docker app can't reach Neo4j | App uses `bolt://neo4j:7687` (service name) not `localhost` |
| Tests say "skipped" instead of failing | Expected — integration/llm tests auto-skip when Neo4j/Ollama is not running |
| `pytest: command not found` | Activate your venv first: `source venv/bin/activate` |

---

## Milestones

| Version | Status | Features |
|---------|--------|----------|
| v0.1 | ✅ Done | Synthetic data + Neo4j graph + Cypher retrieval |
| v0.2 | ✅ Done | Sentence-transformer embeddings on nodes |
| v0.3 | ✅ Done | Ollama LLM integration + full RAG pipeline |
| v0.4 | ✅ Done | Streamlit UI + FastAPI + Docker Compose |
| v0.5 | ✅ Done | Full pytest suite — unit, integration, and LLM tests |
| v1.0 | 🔜 Planned | Real medical datasets + evaluation benchmarks |

---

## Real Dataset Sources (v1.0)

- [DrugBank Open Data](https://go.drugbank.com/releases/latest#open-data) — 11,000+ drugs, 1.5M interactions
- [SNAP Biomedical Datasets](https://snap.stanford.edu/biodata) — disease-gene, drug-disease graphs
- [PubMed via NCBI API](https://www.ncbi.nlm.nih.gov/home/develop/api/) — free, no key needed for low volume
- [MIMIC-III Demo](https://physionet.org/content/mimiciii-demo/) — clinical notes (free with PhysioNet account)

---

## Contributing

Pull requests welcome! Please open an issue first to discuss what you'd like to change.
