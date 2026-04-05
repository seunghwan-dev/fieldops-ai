"""
C. Edge Case Tests — Failure Injection & Safety (C01-C10).

WHY: LLM fails in predictable ways: invalid JSON, Chinese, timeout.
     Rule-based safety must catch what LLM misses.
INTERVIEW: "C tests inject LLM failures to verify the Rule-based safety net."
"""
import pytest
from unittest.mock import patch, AsyncMock
import json
import asyncio


class TestLLMFailures:
    """C01-C03: LLM failure injection."""

    def _fusion_request(self, temp=210, rpm=100):
        """
        Helper: mixer request for LLM failure injection.

        WHY: FusionRequest has no equipment_type field;
             fusion_service._equipment_type() infers from material name.
        """
        return {
            "material": "Material A",
            "conditions": {
                "temperature_celsius": temp,
                "rpm": rpm,
                "input_rate_kg_h": 25,
                "blade_type": "A",
                "machine_prop_a": 50,
                "machine_prop_b": 50,
                "machine_prop_c": 50
            },
            "mode": "fusion"
        }

    def test_llm_invalid_json(self, test_client, mock_llm_invalid_json):
        """
        C01: LLM returns markdown-fenced JSON -> strip fences or fallback.

        WHY: Qwen sometimes wraps JSON in ```json fences.
             _strip_markdown_fences() in fusion_service.py handles this.
        """
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=mock_llm_invalid_json):
            response = test_client.post("/api/v1/fusion/predict",
                                       json=self._fusion_request())
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is not None

    def test_llm_timeout(self, test_client):
        """
        C02: LLM timeout -> fallback to rule_only_fallback, not 500.

        WHY: Network issues or model overload.
             _llm_fusion() retries 3x then returns ML + Rule fallback.
        """
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   side_effect=asyncio.TimeoutError):
            response = test_client.post("/api/v1/fusion/predict",
                                       json=self._fusion_request())
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is not None
        # WHY: safety_service.apply_rules() may append " + rule_override"
        #      to fusion_method when SAFETY-001 triggers on the fallback value.
        assert data["fusion"]["fusion_method"].startswith("rule_only_fallback")

    def test_llm_chinese(self, test_client, mock_llm_chinese):
        """
        C03: LLM responds in Chinese -> still valid JSON, prediction OK.

        WHY: Qwen (Chinese-origin) sometimes outputs Chinese.
             Chinese in JSON values is valid JSON — json.loads handles it.
        INTERVIEW: "P1 lesson: Qwen needs explicit language instructions."
        """
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=mock_llm_chinese):
            response = test_client.post("/api/v1/fusion/predict",
                                       json=self._fusion_request())
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is not None
        assert data["fusion"]["fused_prediction"] == 180


class TestInputValidation:
    """C04-C07: Input validation edge cases."""

    def test_search_empty_query(self, test_client):
        """
        C04: Empty query -> 422 (min_length=1 in search router).

        WHY: FastAPI Query(min_length=1) rejects empty strings.
        """
        response = test_client.get(
            "/api/v1/knowledge/search",
            params={"q": ""}
        )
        assert response.status_code == 422

    def test_predict_extreme_temp(self, test_client, mock_llm_success):
        """
        C05: 999C -> response includes CRITICAL or HIGH risk.

        WHY: mock_llm_success has fused=180, risk_level="CRITICAL".
             Even with extreme input, LLM mock produces safe fused value.
             Rule SAFETY-001 (discharge > 200) does NOT trigger since fused=180.
             But the LLM-assigned risk_level "CRITICAL" is preserved.
        """
        request = {
            "material": "Material A",
            "conditions": {
                "temperature_celsius": 999,
                "rpm": 100,
                "input_rate_kg_h": 25,
                "blade_type": "A",
                "machine_prop_a": 50,
                "machine_prop_b": 50,
                "machine_prop_c": 50
            },
            "mode": "fusion"
        }
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_llm_success)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code == 200
        resp_upper = str(response.json()).upper()
        assert "CRITICAL" in resp_upper or "HIGH" in resp_upper

    def test_predict_negative_rpm(self, test_client):
        """
        C06: rpm=-100 -> 422 validation error.

        WHY: Physical impossibility. Pydantic validator in FusionRequest
             rejects negative values in conditions before reaching ML.
        """
        request = {
            "material": "Material A",
            "conditions": {
                "temperature_celsius": 150,
                "rpm": -100,
                "input_rate_kg_h": 25,
                "blade_type": "A",
                "machine_prop_a": 50,
                "machine_prop_b": 50,
                "machine_prop_c": 50
            },
            "mode": "ml_only"
        }
        response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code in [400, 422]

    def test_predict_unknown_material(self, test_client, mock_llm_success):
        """
        C07: "Material Z" -> 200 OK, prediction exists.

        WHY: Unknown material falls through to mixer (not "Material G").
             LLM mocked to avoid non-determinism.
             No safety rules match "Material Z", so overrides empty.
        """
        request = {
            "material": "Material Z",
            "conditions": {
                "temperature_celsius": 150,
                "rpm": 60,
                "input_rate_kg_h": 25,
                "blade_type": "A",
                "machine_prop_a": 50,
                "machine_prop_b": 50,
                "machine_prop_c": 50
            },
            "mode": "fusion"
        }
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_llm_success)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] is not None
        assert len(data["safety_overrides"]) == 0


class TestRuleOverrides:
    """C08-C10: Rule-based safety layer validation."""

    def test_rule_critical_override(self, test_client, mock_llm_high_fused):
        """
        C08: LLM outputs fused=215 -> SAFETY-001 overrides to 180C.

        WHY: Layer 1 (LLM) flexible, Layer 2 (Rule) non-negotiable.
             SAFETY-001: Material A, discharge_temp > 200 -> force 180.
             safety_service.apply_rules() mutates fusion_result in-place.
        INTERVIEW: "Phase 4 LLM always got it right, so Rule never triggered.
                   C08 injects wrong LLM output to verify the safety net."
        """
        request = {
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
            "mode": "fusion"
        }
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_llm_high_fused)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code == 200
        data = response.json()
        # SAFETY-001 should have fired
        assert len(data["safety_overrides"]) >= 1
        override = data["safety_overrides"][0]
        assert override["rule_id"] == "SAFETY-001"
        assert override["corrected_value"] == 180
        # Fusion result mutated by rule
        assert data["fusion"]["fused_prediction"] == 180
        assert data["fusion"]["risk_level"] == "CRITICAL"

    def test_rule_warning_only(self, test_client):
        """
        C09: fused=185, rpm=95 -> SAFETY-002 WARNING, value preserved at 185.

        WHY: WARNING rules escalate risk_level but do NOT override prediction.
             SAFETY-002: discharge > 180 AND rpm > 90 -> recommend_review.
        """
        mock_warning = {
            "fused_prediction": 185,
            "correction_applied": True,
            "correction_delta": -38,
            "correction_reason": "Caution near 200C.",
            "domain_evidence": ["Paper-A, Table 2"],
            "risk_level": "MEDIUM",
            "recommendation": "Monitor temperature.",
            "confidence_score": 0.82
        }
        request = {
            "material": "Material A",
            "conditions": {
                "temperature_celsius": 195,
                "rpm": 95,
                "input_rate_kg_h": 25,
                "blade_type": "A",
                "machine_prop_a": 50,
                "machine_prop_b": 50,
                "machine_prop_c": 50
            },
            "mode": "fusion"
        }
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_warning)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code == 200
        data = response.json()
        # SAFETY-002 WARNING triggered
        assert len(data["safety_overrides"]) >= 1
        assert data["safety_overrides"][0]["severity"] == "WARNING"
        # WARNING does NOT change fused_prediction
        assert data["fusion"]["fused_prediction"] == 185
        # Risk escalated to at least HIGH
        assert data["fusion"]["risk_level"] in ["HIGH", "CRITICAL"]

    def test_rule_no_match(self, test_client):
        """
        C10: Material G, grinding_pressure=0.8 -> no rules trigger.

        WHY: SAFETY-003 needs grinding_pressure > 1.0 (we have 0.8).
             safety_overrides must be empty.
        """
        mock_normal = {
            "fused_prediction": 4.1,
            "correction_applied": False,
            "correction_delta": 0,
            "correction_reason": "No domain data for Material G.",
            "domain_evidence": [],
            "risk_level": "LOW",
            "recommendation": "ML prediction used as-is.",
            "confidence_score": 0.80
        }
        request = {
            "material": "Material G",
            "conditions": {
                "feed_rate_kg_h": 10,
                "grinding_pressure_mpa": 0.8,
                "classifier_rpm": 8000,
                "air_flow": 50,
                "bulk_density": 0.8
            },
            "mode": "fusion"
        }
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_normal)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        assert response.status_code == 200
        data = response.json()
        assert len(data["safety_overrides"]) == 0
