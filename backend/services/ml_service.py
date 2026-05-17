"""
ML Prediction Service -- RandomForest + SHAP.

WHY: Track B of Dual-Track Prediction.
     Loads pre-trained models from Phase 1 (data/ml/*.joblib).
     Returns numerical prediction + SHAP explainability.
RISK: Model trained on 100 rows (Equipment A), 50 rows (Equipment B). PoC-grade, not production.
     Intentionally lacks safety awareness -- Fusion Engine's job (Phase 4).
INTERVIEW: "ML intentionally predicts numbers without safety judgment.
            The Fusion Engine adds the domain knowledge layer."
"""

import time
import warnings
import logging

import joblib
import numpy as np
import shap

logger = logging.getLogger(__name__)

# WHY: Suppress SHAP feature perturbation warnings (noisy, expected behavior).
warnings.filterwarnings("ignore", module="shap")

# WHY: Load once at import time, not per-request.
# RISK: If model files missing, service fails at startup -- intentional fail-fast.
MODEL_A = joblib.load("data/ml/model_a.joblib")
MODEL_B = joblib.load("data/ml/model_b.joblib")
LABEL_ENCODER_A = joblib.load("data/ml/label_encoder_a.joblib")

# WHY: Pre-initialize SHAP explainers to avoid 1-2s delay on first request.
EXPLAINER_A = shap.TreeExplainer(MODEL_A)
EXPLAINER_B = shap.TreeExplainer(MODEL_B)

logger.info("ML models and SHAP explainers loaded successfully.")


def build_shap_factors(
    feature_names: list, feature_values: list, shap_vals, top_n: int = 5
) -> list[dict]:
    """
    Build sorted SHAP factor list.

    WHY: SHAP provides per-feature contribution to prediction.
         Sorted by absolute value -- most impactful first for UI display.
    INTERVIEW: "SHAP makes ML predictions explainable --
               engineers see which input matters most."
    """
    factors = []
    for name, value, sv in zip(feature_names, feature_values, shap_vals):
        factors.append({
            "feature": name,
            "value": round(float(value), 2),
            "shap_value": round(float(sv), 2),
            "direction": "increases" if sv > 0 else "decreases",
        })
    factors.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
    return factors[:top_n]


def _generate_explanation(top_factors: list[dict]) -> str:
    """Generate human-readable SHAP explanation from top factor."""
    if not top_factors:
        return "No dominant factors identified."
    top = top_factors[0]
    direction = "+" if top["direction"] == "increases" else "-"
    return (
        f"{top['feature']} contributes most "
        f"({direction}{abs(top['shap_value'])}) to the prediction."
    )


async def predict_mixer(conditions: dict) -> dict:
    """
    Predict discharge temperature for Equipment A (continuous mixer).

    WHY: Feature order MUST match train_models.py training order:
         [rpm, input_rate_kg_h, blade_type(encoded), jacket_temp,
          machine_prop_a, machine_prop_b, machine_prop_c]
         input_rate_kg_h replaces fill_ratio -- actual feed rate.
    RISK: No safety threshold check. ML predicts numbers only -- by design.
    INTERVIEW: "210C jacket -> ML predicts >200C with zero warning.
               That's the Fusion scenario."
    """
    start = time.time()

    features = [
        conditions["rpm"],
        conditions["input_rate_kg_h"],
        LABEL_ENCODER_A.transform([conditions["blade_type"]])[0],
        conditions["temperature_celsius"],  # = jacket_temp in CSV
        conditions["machine_prop_a"],
        conditions["machine_prop_b"],
        conditions["machine_prop_c"],
    ]

    feature_array = np.array([features])
    prediction = MODEL_A.predict(feature_array)[0]

    shap_values = EXPLAINER_A.shap_values(feature_array)

    feature_names = ["rpm", "input_rate", "blade_type", "jacket_temp",
                     "machine_prop_a", "machine_prop_b", "machine_prop_c"]
    top_factors = build_shap_factors(feature_names, features, shap_values[0])

    elapsed_ms = (time.time() - start) * 1000

    return {
        "prediction": {
            "discharge_temp_celsius": round(float(prediction), 1),
            "confidence": 0.949,
            "model": "RandomForest-EquipmentA-v1",
            "r2_score": 0.949,
        },
        "shap": {
            "top_factors": top_factors,
            "base_value": round(float(np.mean(EXPLAINER_A.expected_value)), 1),
            "explanation": _generate_explanation(top_factors),
        },
        "requires_human_review": True,
        "meta": {
            "track_b_time_ms": round(elapsed_ms, 1),
            "equipment_type": "mixer",
        },
    }


def _bonds_law_prediction(conditions: dict) -> float:
    """
    Simplified Bond's Law for grinder particle size prediction.

    WHY: Well-established grinding energy equation. Accurate at high RPM (>6000).
         At low RPM (<4000), turbulence causes 15-30% deviation -- ML corrects this.
    RISK: Simplified constants for PoC. Production would use material-specific Wi values.
    INTERVIEW: "Production uses material-specific Work Index DB. K=500 is PoC shortcut."
    """
    pressure = conditions["grinding_pressure_mpa"]
    classifier_rpm = conditions["classifier_rpm"]
    feed_rate = conditions["feed_rate_kg_h"]
    air_flow = conditions["air_flow"]
    bulk_density = conditions.get("bulk_density", 1.0)

    # K = 2.84: Calibrated from median of 50 training samples (original design K=500).
    # INTERVIEW: "K was empirically calibrated -- not assumed. Design 500 -> Actual 2.84."
    K = 2.84
    d_cut = K / (classifier_rpm * (pressure ** 0.5))
    feed_factor = 1.0 + 0.02 * (feed_rate - 10)
    air_factor = 1.0 - 0.005 * (air_flow - 50)
    # WHY: High bulk density reduces grinding efficiency -> larger particle size.
    density_factor = 1.0 + 0.3 * (bulk_density - 1.0)
    return d_cut * feed_factor * air_factor * density_factor * 1000


# WHY: R2 on error residuals (not absolute). Lower than Equipment A is expected.
R2_B = 0.580


async def predict_grinder(conditions: dict) -> dict:
    """
    Equipment B: Physics + ML Error Correction Hybrid.

    WHY: Bond's Law provides theoretical baseline. ML corrects residual error.
         At high RPM (>6000), physics is accurate -- ML correction ~ 0.
         At low RPM (<4000), turbulence causes deviation -- ML correction is significant.
    RISK: Simplified Bond's Law constants for PoC. Production needs material-specific calibration.
    INTERVIEW: "The veteran engineer's intuition at low RPM -- that's what the ML model learned."
    """
    start = time.time()

    # Step 1: Physics prediction (Bond's Law)
    d50_physics = _bonds_law_prediction(conditions)

    features = [
        conditions["feed_rate_kg_h"],
        conditions["grinding_pressure_mpa"],
        conditions["classifier_rpm"],
        conditions["air_flow"],
        conditions.get("bulk_density", 1.0),
    ]
    feature_array = np.array([features])
    error_prediction = MODEL_B.predict(feature_array)[0]

    # Step 3: Hybrid combination
    # WHY: Particle size cannot be negative. Physical lower bound.
    # RISK: Clamp should rarely trigger with calibrated K. If it does, data quality issue.
    d50_final = max(d50_physics + error_prediction, 0.01)

    shap_values = EXPLAINER_B.shap_values(feature_array)
    feature_names = ["feed_rate", "grinding_pressure", "classifier_rpm", "air_flow", "bulk_density"]
    top_factors = build_shap_factors(feature_names, features, shap_values[0])

    elapsed_ms = (time.time() - start) * 1000

    # WHY: SHAP explanation describes error correction contribution, not absolute prediction.
    if top_factors:
        top = top_factors[0]
        shap_explanation = (
            f"ML error correction: {top['feature']} contributes most "
            f"({top['shap_value']:+.2f}\u03bcm) to the correction."
        )
    else:
        shap_explanation = "No dominant correction factors identified."

    return {
        "prediction": {
            "d50_micron": round(float(d50_final), 2),
            "physics_only_d50": round(float(d50_physics), 2),
            "ml_correction": round(float(error_prediction), 2),
            "confidence": R2_B,
            "model": "BondsLaw+RandomForest-EquipmentB-v1",
            "r2_score": R2_B,
            "physics_formula": "Bond's Law + classifier cut-point equation",
        },
        "shap": {
            "top_factors": top_factors,
            "base_value": round(float(np.mean(EXPLAINER_B.expected_value)), 2),
            "explanation": shap_explanation,
        },
        "requires_human_review": True,
        "meta": {
            "track_b_time_ms": round(elapsed_ms, 1),
            "equipment_type": "grinder",
            "prediction_method": "physics_hybrid",
        },
    }
