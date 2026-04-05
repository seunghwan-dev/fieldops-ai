"""
ML Prediction Router.

WHY: Standalone ML prediction endpoint (Track B only).
     Used for:
     - Demo "Before" mode (ml_only)
     - Phase 4 Fusion Engine (Track B input via asyncio.gather)
     - Phase 6 test cases
INTERVIEW: "Same endpoint serves both standalone demo and Fusion pipeline input."
"""

from fastapi import APIRouter, HTTPException
from schemas.predict import PredictRequest, PredictResponse
from services.ml_service import predict_mixer, predict_grinder

router = APIRouter(tags=["ML Prediction"])


@router.post("/ml/predict", response_model=PredictResponse)
async def ml_predict(request: PredictRequest):
    """
    POST /api/v1/ml/predict -- ML-only prediction (Track B).

    WHY: Returns numerical prediction + SHAP explanation.
         No safety checks -- that is Phase 4 Fusion Engine's responsibility.
    """
    if request.equipment_type == "mixer":
        return await predict_mixer(request.conditions)
    elif request.equipment_type == "grinder":
        return await predict_grinder(request.conditions)
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported equipment_type. Use 'mixer' or 'grinder'.",
        )
