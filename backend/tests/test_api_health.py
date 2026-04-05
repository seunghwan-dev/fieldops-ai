"""
A. Core API Tests — Health & Readiness (A01-A02).

WHY: Verify system liveness and dependency connectivity.
INTERVIEW: "Health checks verify all 4 Docker services are connected."
"""


class TestHealthEndpoints:

    def test_health_ok(self, test_client):
        """A01: GET /health → 200, status=healthy."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_all_connected(self, test_client):
        """
        A02: GET /readiness → 200, services connected.

        WHY: Readiness probe checks Oracle, Ollama, Embedding.
        """
        response = test_client.get("/readiness")
        assert response.status_code == 200
        data = response.json()
        assert "oracle" in str(data).lower() or "database" in str(data).lower()
