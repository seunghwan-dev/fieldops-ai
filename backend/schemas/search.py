"""
Search API request/response models.

WHY: Typed schemas for hybrid search endpoint.
     Includes similarity scores and source citations for transparency.
INTERVIEW: "Every search result carries similarity score and source -- no black box."
"""

from typing import Optional
from pydantic import BaseModel


class SearchResult(BaseModel):
    """Single search result with provenance."""
    chunk_id: str
    chunk_type: str          # "text" | "table_row" | "figure"
    chunk_text: str
    doc_id: str
    doc_title: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    similarity: float        # 1 - cosine_distance
    search_method: str       # "vector" | "bm25" | "hybrid"


class SearchMeta(BaseModel):
    """Search execution metadata for debugging and tuning."""
    vector_hits: int
    bm25_hits: int
    rrf_combined: int
    threshold_applied: float
    search_time_ms: int


class SearchResponse(BaseModel):
    """
    Full search response with AI-generated answer.

    WHY: Phase 4 Fusion Engine reuses SearchResult list as Track A input.
         Schema defined independently for cross-phase compatibility.
    """
    query: str
    results: list[SearchResult]
    answer: str              # Qwen 7B generated (50+ chars)
    sources: list[str]       # ["Paper-A, Table 2", "Paper-A, Section 4"]
    total_results: int
    search_meta: SearchMeta
