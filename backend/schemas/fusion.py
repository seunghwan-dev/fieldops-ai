"""
Fusion API request/response models.

WHY: Unified schema for ml_only and fusion modes.
     ml_only returns prediction+shap only.
     fusion adds domain_knowledge + fusion + safety_overrides.
INTERVIEW: "Before/After toggle -- same prediction block, fusion adds layers on top."
"""

from typing import Literal, Optional
from pydantic import BaseModel, field_validator


class FusionRequest(BaseModel):
    material: str                              # "Material A" ~ "Material G"
    conditions: dict                           # Same structure as PredictRequest.conditions
    mode: Literal["ml_only", "fusion"] = "fusion"

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v):
        """Reject negative numeric values in conditions (physical impossibility)."""
        for key, val in v.items():
            if isinstance(val, (int, float)) and val < 0:
                raise ValueError(f"{key} must be non-negative, got {val}")
        return v


class FusionResponse(BaseModel):
    mode: str
    prediction: dict
    shap: dict                                 # SHAP original -- immutable
    domain_knowledge: Optional[dict] = None
    fusion: Optional[dict] = None
    safety_overrides: list = []                # empty for ml_only
    requires_human_review: bool = True         # always True
    meta: dict = {}
