"""
D. Equipment Physics & Additional Validation (D01-D10).

WHY: D01-D05 validate Bond's Law hybrid prediction for Equipment B (grinder).
     D06-D10 cover SHAP, timing, concurrency, and safety structure.
     All ML/physics tests are deterministic — no LLM mock needed.
INTERVIEW: "Bond's Law is accurate at high RPM. ML corrects low-RPM turbulence."
"""
import json
from unittest.mock import patch, AsyncMock


def _grinder_request(classifier_rpm=8000, pressure=0.8, feed_rate=10, air_flow=50, bulk_density=0.8):
    """Helper: Material G grinder request with configurable RPM."""
    return {
        "material": "Material G",
        "conditions": {
            "feed_rate_kg_h": feed_rate,
            "grinding_pressure_mpa": pressure,
            "classifier_rpm": classifier_rpm,
            "air_flow": air_flow,
            "bulk_density": bulk_density,
        },
        "mode": "ml_only",
    }


def _mixer_request(temp=150, rpm=60):
    """Helper: Material A mixer request."""
    return {
        "material": "Material A",
        "conditions": {
            "temperature_celsius": temp,
            "rpm": rpm,
            "input_rate_kg_h": 25,
            "blade_type": "A",
            "machine_prop_a": 50,
            "machine_prop_b": 50,
            "machine_prop_c": 50,
        },
        "mode": "ml_only",
    }


class TestEquipmentBPhysics:
    """D01-D05: Bond's Law hybrid prediction for grinder."""

    def test_physics_only_positive(self, test_client):
        """
        D01: physics_only_d50 > 0 for standard grinder conditions.

        WHY: Bond's Law d_cut formula must produce positive particle size.
        """
        response = test_client.post("/api/v1/fusion/predict",
                                    json=_grinder_request())
        assert response.status_code == 200
        pred = response.json()["prediction"]
        assert pred["physics_only_d50"] > 0

    def test_physics_plus_correction(self, test_client):
        """
        D02: physics_only_d50 + ml_correction ≈ d50_micron (within 0.01).

        WHY: Hybrid = physics baseline + ML error correction.
             d50_final = max(physics + correction, 0.01), rounded to 2 decimals.
        """
        response = test_client.post("/api/v1/fusion/predict",
                                    json=_grinder_request())
        pred = response.json()["prediction"]
        expected = round(max(pred["physics_only_d50"] + pred["ml_correction"], 0.01), 2)
        assert abs(pred["d50_micron"] - expected) < 0.01

    def test_high_rpm_low_correction(self, test_client):
        """
        D03: classifier_rpm=8000 -> abs(ml_correction) < 0.5.

        WHY: At high RPM (>6000), Bond's Law is accurate.
             ML correction should be minimal.
        INTERVIEW: "High RPM = laminar flow. Physics model handles it."
        """
        response = test_client.post("/api/v1/fusion/predict",
                                    json=_grinder_request(classifier_rpm=8000))
        pred = response.json()["prediction"]
        self._high_rpm_correction = abs(pred["ml_correction"])
        assert abs(pred["ml_correction"]) < 0.5

    def test_low_rpm_high_correction(self, test_client):
        """
        D04: classifier_rpm=3000 -> abs(ml_correction) > high-RPM correction.

        WHY: At low RPM (<4000), turbulence causes deviation.
             ML correction should be larger than at high RPM.
        INTERVIEW: "The veteran's intuition at low RPM — that's what ML learned."
        """
        resp_high = test_client.post("/api/v1/fusion/predict",
                                     json=_grinder_request(classifier_rpm=8000))
        resp_low = test_client.post("/api/v1/fusion/predict",
                                    json=_grinder_request(classifier_rpm=3000))
        corr_high = abs(resp_high.json()["prediction"]["ml_correction"])
        corr_low = abs(resp_low.json()["prediction"]["ml_correction"])
        assert corr_low > corr_high

    def test_physics_formula_field(self, test_client):
        """
        D05: physics_formula field contains "Bond".

        WHY: Transparency — response must declare the physics model used.
        """
        response = test_client.post("/api/v1/fusion/predict",
                                    json=_grinder_request())
        pred = response.json()["prediction"]
        assert "Bond" in pred["physics_formula"]


class TestAdditionalValidation:
    """D06-D10: SHAP, timing, concurrency, safety structure."""

    def test_mixer_shap_top_factor(self, test_client):
        """
        D06: Mixer SHAP top_factors[0] feature is a known feature.

        WHY: For mixer, jacket temperature and RPM are the dominant
             process variables driving discharge temperature.
        """
        response = test_client.post("/api/v1/fusion/predict",
                                    json=_mixer_request())
        top = response.json()["shap"]["top_factors"][0]
        assert top["feature"] in ("jacket_temp", "rpm", "input_rate",
                                   "blade_type", "machine_prop_a",
                                   "machine_prop_b", "machine_prop_c")

    def test_grinder_shap_exists(self, test_client):
        """
        D07: Jet mill SHAP has >= 2 top_factors.

        WHY: Equipment B has 4 features; SHAP should report at least 2.
        """
        response = test_client.post("/api/v1/fusion/predict",
                                    json=_grinder_request())
        factors = response.json()["shap"]["top_factors"]
        assert len(factors) >= 2

    def test_fusion_meta_timing(self, test_client, mock_llm_success):
        """
        D08: Fusion response meta.total_time_ms > 0.

        WHY: Timing metadata is essential for performance monitoring.
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
                "machine_prop_c": 50,
            },
            "mode": "fusion",
        }
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_llm_success)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        meta = response.json()["meta"]
        assert meta["total_time_ms"] > 0
        assert meta["track_b_time_ms"] > 0

    def test_concurrent_ml_predictions(self, test_client):
        """
        D09: Mixer + grinder sequential calls both return 200 OK.

        WHY: Both ML models must coexist without interference.
        """
        r1 = test_client.post("/api/v1/fusion/predict",
                              json=_mixer_request())
        r2 = test_client.post("/api/v1/fusion/predict",
                              json=_grinder_request())
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert "discharge_temp_celsius" in r1.json()["prediction"]
        assert "d50_micron" in r2.json()["prediction"]

    def test_safety_rules_loaded(self, test_client, mock_llm_success):
        """
        D10: safety_overrides in response is always a list.

        WHY: Downstream consumers (React UI) expect consistent array type.
        """
        request = {
            "material": "Material A",
            "conditions": {
                "temperature_celsius": 150,
                "rpm": 60,
                "input_rate_kg_h": 25,
                "blade_type": "A",
                "machine_prop_a": 50,
                "machine_prop_b": 50,
                "machine_prop_c": 50,
            },
            "mode": "fusion",
        }
        with patch("services.fusion_service.generate_raw",
                   new_callable=AsyncMock,
                   return_value=json.dumps(mock_llm_success)):
            response = test_client.post("/api/v1/fusion/predict", json=request)
        assert isinstance(response.json()["safety_overrides"], list)
