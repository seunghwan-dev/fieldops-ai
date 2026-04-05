"""
ML Prediction request/response models.

WHY: Typed schemas for ML-only prediction (Track B).
     Same prediction block reused in Phase 4 Fusion response.
INTERVIEW: "ML prediction schema is Phase 4's building block -- fusion adds layers on top."
"""

from typing import Optional
from pydantic import BaseModel


class MixerConditions(BaseModel):
    temperature_celsius: float   # = jacket_temp in CSV
    rpm: float
    input_rate_kg_h: float       # feed rate in kg/h (replaces fill_ratio)
    blade_type: str              # "A" ~ "G" (7 types)
    machine_prop_a: float
    machine_prop_b: float
    machine_prop_c: float


class GrinderConditions(BaseModel):
    feed_rate_kg_h: float
    grinding_pressure_mpa: float
    classifier_rpm: float
    air_flow: float
    bulk_density: float          # g/cm³ — affects grinding efficiency


class PredictRequest(BaseModel):
    material: str
    equipment_type: str          # "mixer" | "grinder"
    conditions: dict             # MixerConditions or GrinderConditions


class ShapFactor(BaseModel):
    feature: str
    value: float
    shap_value: float
    direction: str               # "increases" | "decreases"


class ShapExplanation(BaseModel):
    top_factors: list[ShapFactor]
    base_value: float
    explanation: str


class PredictionResult(BaseModel):
    discharge_temp_celsius: Optional[float] = None   # Equipment A
    d50_micron: Optional[float] = None               # Equipment B
    physics_only_d50: Optional[float] = None         # Equipment B physics baseline
    ml_correction: Optional[float] = None            # Equipment B ML error correction
    physics_formula: Optional[str] = None            # Equipment B formula description
    confidence: float
    model: str
    r2_score: float


class PredictMeta(BaseModel):
    track_b_time_ms: float
    equipment_type: str


class PredictResponse(BaseModel):
    prediction: PredictionResult
    shap: ShapExplanation
    requires_human_review: bool = True    # Always true -- "Zero-Input, Human-Final"
    meta: PredictMeta
