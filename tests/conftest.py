"""
conftest.py — Shared pytest fixtures and markers.

Test categories:
  - Unit tests        : No infrastructure needed. Always run.
  - Integration tests : Need Neo4j running.  Mark with @pytest.mark.integration
  - LLM tests         : Need Ollama running.  Mark with @pytest.mark.llm

Run only unit tests (fast):
    pytest tests/ -m "not integration and not llm"

Run all tests (requires Neo4j + Ollama):
    pytest tests/
"""

import os
import sys
import pytest

# Make sure project root is on path for all tests
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)



# Custom markers

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: requires Neo4j running on localhost:7687"
    )
    config.addinivalue_line(
        "markers", "llm: requires Ollama running on localhost:11434"
    )


# Helpers to check infrastructure availability

def _neo4j_available() -> bool:
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "medgraph123")
        )
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


def _ollama_available() -> bool:
    try:
        import httpx
        resp = httpx.get("http://localhost:11434", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False



# Fixtures

@pytest.fixture(scope="session")
def neo4j_driver():
    """Session-scoped Neo4j driver. Skips if Neo4j not available."""
    if not _neo4j_available():
        pytest.skip("Neo4j not available at localhost:7687 — start with: docker-compose up -d neo4j")
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "medgraph123"))
    yield driver
    driver.close()


@pytest.fixture(scope="session")
def neo4j_session(neo4j_driver):
    """Convenience fixture: open Neo4j session."""
    with neo4j_driver.session() as session:
        yield session


@pytest.fixture(scope="session")
def ollama_client():
    """Session-scoped Ollama client. Skips if Ollama not available."""
    if not _ollama_available():
        pytest.skip("Ollama not available at localhost:11434 — make sure Ollama app is running")
    import ollama
    return ollama.Client(host="http://localhost:11434")


@pytest.fixture(scope="session")
def synthetic_data():
    """Load or generate synthetic data dict."""
    from data.generate_synthetic import generate
    return generate()
