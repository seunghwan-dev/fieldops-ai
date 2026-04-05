"""
A. Core API Tests — Fusion Predict (A14-A20).

WHY: Fusion Engine = killer feature. LLM + Rule dual-layer.
     ML-only = "Before", Fusion = "After" in demo.
INTERVIEW: "ML says >200°C no warning. Fusion says 180°C with evidence and CRITICAL risk."
"""
import pytest
from unittest.mock import patch, AsyncMock
import time
import json


class TestFusionPredict:
    """A14-A20: Fusion prediction (LLM mocked, ML+Oracle real)."""

    def _build_request(self, mode="ml_only"):
        """
        Helper: Equipment A prediction request (210°C, 100rpm).

        WHY: FusionRequest schema takes material + conditions + mode.
             equipment_type is inferred internally by fusion_service._equipment_type().
        """
        return {
            "material": "Material A",
            "conditions": {
                "temperature_celsius": 210,
                "rpm": 100,
                "input_rate_kg_h": 25,
                "blade_type": "A",
                "machine_prop_a": 50,
                "machine_prop_b": 50,
                "machine_prop_c": 50
            },
            "mode": mode
        }

    def test_predict_ml_only(self, test_client):
        """
        A14: mode=ml_only -> prediction exists, fusion=null.

        WHY: ML-only is the "Before" in Before/After demo.
        """
        request = self._build_request("ml_only")
        response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is not None
        assert data["fusion"] is None

    def test_predict_ml_has_shap(self, test_client):
        """
        A15: ML-only includes SHAP with >= 3 top factors.

        INTERVIEW: "SHAP TreeExplainer decomposes 'why this temperature'."
        """
        request = self._build_request("ml_only")
        response = test_client.post("/api/v1/fusion/predict", json=request)
        data = response.json()
        assert "top_factors" in data["shap"]
        assert len(data["shap"]["top_factors"]) >= 3

    def test_predict_fusion_mode(self, test_client, mock_llm_success):
        """
        A16: mode=fusion -> fused_prediction exists.

        WHY: Full pipeline — Track A + B + LLM + Rule.
        PATCH TARGET: services.fusion_service.generate_raw (called at fusion_service.py:193).
        """
        request = self._build_request("fusion")
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_llm_success)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code == 200
        data = response.json()
        assert data["fusion"] is not None
        assert "fused_prediction" in data["fusion"]

    def test_predict_fusion_correction(self, test_client, mock_llm_success):
        """
        A17: Dangerous conditions -> correction_applied.

        WHY: LLM detects conflict between ML (>200°C) and domain knowledge.
        """
        request = self._build_request("fusion")
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_llm_success)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        data = response.json()
        assert data["fusion"]["correction_applied"] is True

    def test_predict_fusion_evidence(self, test_client, mock_llm_success):
        """
        A18: Fusion response has domain_evidence >= 1.

        WHY: Every correction must cite evidence. No evidence = no trust.
        """
        request = self._build_request("fusion")
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_llm_success)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        data = response.json()
        assert len(data["fusion"]["domain_evidence"]) >= 1

    def test_predict_human_review(self, test_client, mock_llm_success):
        """
        A19: Both modes return requires_human_review=true.

        WHY: "Zero-Input, Human-Final" — AI assists, never decides.
        INTERVIEW: "Every output carries requires_human_review: true."
        """
        resp_ml = test_client.post("/api/v1/fusion/predict",
                                   json=self._build_request("ml_only"))
        assert resp_ml.json()["requires_human_review"] is True

        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_llm_success)):
            resp_f = test_client.post("/api/v1/fusion/predict",
                                     json=self._build_request("fusion"))
        assert resp_f.json()["requires_human_review"] is True

    def test_predict_response_time(self, test_client, mock_llm_success):
        """
        A20: Fusion completes < 15 seconds.

        WHY: Phase 4 showed max 7,039ms. 15s is generous safety margin.
        """
        request = self._build_request("fusion")
        start = time.time()
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_llm_success)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        elapsed_ms = (time.time() - start) * 1000
        assert response.status_code == 200
        assert elapsed_ms < 15000, f"Took {elapsed_ms:.0f}ms"
