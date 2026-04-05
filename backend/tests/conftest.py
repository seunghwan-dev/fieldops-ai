"""
Test fixtures for FieldOps-AI.

WHY: Shared fixtures across all test files.
     Mock strategy: A tests use mocks for speed/determinism.
     B tests use real services for E2E validation.
     C tests use mock failure injection.
INTERVIEW: "50 tests: 20 API + 10 integration + 10 edge cases."
"""
import pytest
from fastapi.testclient import TestClient
import json
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(scope="module")
def test_client():
    """
    FastAPI TestClient — module-scoped to share event loop.

    WHY: oracledb async pool binds to one event loop.
         Function-scoped TestClient creates a new loop per test,
         causing 'Future attached to a different loop' errors.
    """
    import services.oracle_service as _ora
    _ora._pool = None
    from main import app
    with TestClient(app) as client:
        yield client
    _ora._pool = None


@pytest.fixture
def sample_pdf_path():
    """Path to test PDF (Paper-A)."""
    return os.path.join(FIXTURES_DIR, "paper_a_sample.pdf")


@pytest.fixture
def mock_vlm_response():
    """Mock GPT-4o Vision response for Paper-A."""
    with open(os.path.join(FIXTURES_DIR, "mock_vlm_response.json")) as f:
        return json.load(f)


@pytest.fixture
def mock_llm_responses():
    """All mock LLM responses."""
    with open(os.path.join(FIXTURES_DIR, "mock_llm_responses.json")) as f:
        return json.load(f)


@pytest.fixture
def mock_llm_success(mock_llm_responses):
    return mock_llm_responses["success"]


@pytest.fixture
def mock_llm_invalid_json(mock_llm_responses):
    return mock_llm_responses["invalid_json"]


@pytest.fixture
def mock_llm_chinese(mock_llm_responses):
    return mock_llm_responses["chinese"]


@pytest.fixture
def mock_llm_high_fused(mock_llm_responses):
    """Mock LLM fused=215 to trigger Rule override."""
    return mock_llm_responses["high_fused"]


@pytest.fixture
def expected_scenarios():
    with open(os.path.join(FIXTURES_DIR, "expected_scenarios.json")) as f:
        return json.load(f)


@pytest.fixture
def scenario1_input(expected_scenarios):
    return expected_scenarios["scenario1"]["input"]


@pytest.fixture
def scenario2_input(expected_scenarios):
    return expected_scenarios["scenario2"]["input"]


@pytest.fixture
def scenario3_input(expected_scenarios):
    return expected_scenarios["scenario3"]["input"]
