"""
B. Integration Tests — Full Pipeline E2E (B01-B10).

WHY: A tests mock LLM/VLM. B tests use ALL REAL services.
     Docker required: Oracle + Ollama + Embedding + FastAPI.
RISK: LLM non-determinism -> assert ranges, not exact values.
     VLM tests (B01-B03) are slow (~30s/page).
INTERVIEW: "Integration tests validate the actual AI pipeline end-to-end."

Run: docker exec fieldops-ai-backend-1 pytest tests/test_integration.py -v
"""
import pytest


pytestmark = pytest.mark.integration


class TestVLMToOracle:
    """B01-B03: VLM -> Embedding -> Oracle pipeline (real VLM)."""

    def test_vlm_to_oracle(self, test_client, sample_pdf_path):
        """
        B01: PDF -> VLM -> embedding -> Oracle. chunks_created > 0.

        WHY: E2E ingestion validation with real GPT-4o Vision.
        NOTE: Real Azure OpenAI call. Requires AZURE_OPENAI_ENDPOINT.
        """
        with open(sample_pdf_path, "rb") as f:
            response = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": ("paper_a.pdf", f, "application/pdf")}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["chunks_created"] > 0

    def test_vlm_chunk_types(self, test_client, sample_pdf_path):
        """
        B02: Paper-A has text and table chunk types.

        WHY: VLM should extract ALL content types, not just text.
        """
        with open(sample_pdf_path, "rb") as f:
            response = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": ("paper_a.pdf", f, "application/pdf")}
            )
        data = response.json()
        dist = data["chunk_distribution"]
        assert dist["text"] > 0
        assert dist["table_row"] > 0

    def test_vlm_then_search(self, test_client, sample_pdf_path):
        """
        B03: Ingest -> search "thermal runaway" -> results >= 1.

        WHY: VLM output must be searchable via hybrid RAG.
        """
        with open(sample_pdf_path, "rb") as f:
            test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": ("paper_a.pdf", f, "application/pdf")}
            )
        response = test_client.get(
            "/api/v1/knowledge/search",
            params={"q": "thermal runaway Material X"}
        )
        assert response.status_code == 200
        assert len(response.json()["results"]) >= 1


class TestFusionScenarios:
    """B04-B07: Three scenarios with real LLM (Qwen 7B)."""

    def test_scenario1_agree(self, test_client, scenario1_input):
        """
        B04: Safe conditions (150C, 60rpm) -> no safety overrides.

        WHY: When ML and domain agree on safe conditions,
             no CRITICAL or WARNING rules should trigger.
             SAFETY-001 needs discharge > 200 (won't reach at 150C).
             SAFETY-002 needs rpm > 90 (we have 60).
        """
        request = {**scenario1_input, "mode": "fusion"}
        response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code == 200
        data = response.json()
        assert len(data["safety_overrides"]) == 0

    def test_scenario2_conflict(self, test_client, scenario2_input):
        """
        B05: Killer scenario (210C, 100rpm) -> HIGH or CRITICAL.

        WHY: ML predicts ~223C, domain says max 180C.
             SAFETY-001 (discharge > 200 -> force 180) should trigger
             unless LLM already corrected below 200.
             Either way, risk must be HIGH or CRITICAL.
        INTERVIEW: "The Before/After killer demo."
        """
        request = {**scenario2_input, "mode": "fusion"}
        response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code == 200
        resp_str = str(response.json()).upper()
        assert "HIGH" in resp_str or "CRITICAL" in resp_str

    def test_scenario3_no_data(self, test_client, scenario3_input):
        """
        B06: Material G grinder (no domain data) -> prediction exists.

        WHY: No domain knowledge -> ML preserved.
             Bond's Law hybrid should still produce d50_micron prediction.
             SAFETY-003 needs grinding_pressure > 1.0 (we have 0.8).
        """
        request = {**scenario3_input, "mode": "fusion"}
        response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is not None
        assert data["prediction"]["d50_micron"] > 0

    def test_before_after_ml_unchanged(self, test_client, scenario2_input):
        """
        B07: ML prediction identical between ml_only and fusion modes.

        WHY: Fusion adds layers ON TOP of ML. ML itself must not change.
             prediction.discharge_temp_celsius must be identical.
        """
        resp_ml = test_client.post("/api/v1/fusion/predict",
                                   json={**scenario2_input, "mode": "ml_only"})
        resp_f = test_client.post("/api/v1/fusion/predict",
                                  json={**scenario2_input, "mode": "fusion"})
        assert resp_ml.status_code == 200
        assert resp_f.status_code == 200
        ml_pred = resp_ml.json()["prediction"]["discharge_temp_celsius"]
        fusion_pred = resp_f.json()["prediction"]["discharge_temp_celsius"]
        assert ml_pred == fusion_pred


class TestDemoPipeline:
    """B08-B10: Demo flow 1->2->3 validation."""

    def test_demo_1to2(self, test_client, sample_pdf_path):
        """
        B08: Ingest -> Search -> ingested doc in results.

        WHY: Knowledge -> Search pipeline connection.
        """
        with open(sample_pdf_path, "rb") as f:
            r1 = test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": ("paper_a.pdf", f, "application/pdf")}
            )
        assert r1.status_code == 200

        r2 = test_client.get(
            "/api/v1/knowledge/search",
            params={"q": "Material X temperature"}
        )
        assert r2.status_code == 200
        assert len(r2.json()["results"]) >= 1

    def test_demo_2to3(self, test_client, scenario2_input):
        """
        B09: Search -> Fusion -> both 200 OK.

        WHY: Search and Fusion share same domain evidence source.
        """
        r2 = test_client.get(
            "/api/v1/knowledge/search",
            params={"q": "Material X thermal runaway"}
        )
        assert r2.status_code == 200

        r3 = test_client.post("/api/v1/fusion/predict",
                              json={**scenario2_input, "mode": "fusion"})
        assert r3.status_code == 200

    def test_demo_full_pipeline(self, test_client, sample_pdf_path, scenario2_input):
        """
        B10: Ingest -> Search -> Fusion -> all 3 stages 200 OK.

        INTERVIEW: "This test runs the entire 5-min demo in one go."
        """
        # Stage 1: Ingest
        with open(sample_pdf_path, "rb") as f:
            assert test_client.post(
                "/api/v1/knowledge/ingest",
                files={"file": ("paper_a.pdf", f, "application/pdf")}
            ).status_code == 200

        # Stage 2: Search
        assert test_client.get(
            "/api/v1/knowledge/search",
            params={"q": "Material X safe temperature"}
        ).status_code == 200

        # Stage 3: Fusion
        assert test_client.post(
            "/api/v1/fusion/predict",
            json={**scenario2_input, "mode": "fusion"}
        ).status_code == 200
