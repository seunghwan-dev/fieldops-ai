"""
Knowledge Search Router.

WHY: GET endpoint for hybrid RAG search. Used by:
     - Demo 2 (RAG instant answer)
     - Phase 4 Fusion Engine (Track A input)
     - React SearchPage (Phase 5)
INTERVIEW: "Single search endpoint serves both standalone demo and Fusion pipeline."
"""

from fastapi import APIRouter, Query
from services.search_service import hybrid_search

router = APIRouter(tags=["Knowledge Search"])


@router.get(
    "/knowledge/search",
    summary="Hybrid RAG search (Vector + BM25 + RRF)",
    description=(
        "Searches knowledge base using hybrid Vector + BM25 + RRF(k=60) strategy. "
        "Returns ranked results with AI-generated summary answer from Qwen 7B."
    ),
)
async def search_knowledge(
    q: str = Query(..., min_length=1, description="Search query text"),
    max_results: int = Query(5, ge=1, le=20, description="Maximum number of results"),
    threshold: float = Query(0.80, ge=0.0, le=1.0, description="Minimum similarity threshold"),
):
    """
    GET /api/v1/knowledge/search?q=Material+X+safe+temperature

    WHY: GET (not POST) because search is idempotent and cacheable.
    RISK: Very short queries (<3 chars) may produce noisy results.
    """
    return await hybrid_search(
        query=q,
        max_results=max_results,
        threshold=threshold,
    )
