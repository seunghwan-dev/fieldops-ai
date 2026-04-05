"""
Fusion Prediction Router.

WHY: Single endpoint for both ml_only and fusion modes.
     Demo Before/After toggle hits same endpoint with different mode.
INTERVIEW: "One API, two modes. Before shows ML blind spot. After shows AI correction."
"""

from fastapi import APIRouter
from schemas.fusion import FusionRequest
from services import fusion_service

router = APIRouter(tags=["Fusion Prediction"])


@router.post("/fusion/predict")
async def fusion_predict(request: FusionRequest):
    """
    POST /api/v1/fusion/predict -- Dual-track prediction with optional fusion.

    WHY: mode=ml_only returns raw ML prediction (Track B only).
         mode=fusion adds RAG domain knowledge + LLM fusion + safety rules.
    """
    return await fusion_service.predict(request)
