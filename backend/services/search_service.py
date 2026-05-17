"""
Hybrid Search Service -- Vector + BM25 + RRF.

WHY: Pure vector search confuses similar material names (e.g., Material X vs Y).
     BM25 ensures exact keyword matching for material names and equipment IDs.
     RRF (k=60) combines both rankings without tuning weights.
RISK: BM25 index (Oracle Text CONTAINS) requires CTX_DDL sync.
      May need CTX_DDL.SYNC_INDEX after data changes.
INTERVIEW: "Designed threshold at 0.75, empirically adjusted to 0.91 in P1.
            Starting at 0.75 here -- will tune based on actual e5-large scores."
"""

import asyncio
import time
import logging

from services.embedding_service import embed_query
from services.oracle_service import vector_search, bm25_search
from services.llm_service import generate_search_answer
from schemas.search import SearchResult, SearchResponse, SearchMeta

logger = logging.getLogger(__name__)

# WHY: P1 empirical threshold was 0.91. Initial 0.75 let through false positives
#      (e.g., "quantum physics" scored 0.77). Tuned to 0.80 after Phase 2 testing.
SIMILARITY_THRESHOLD = 0.80


def reciprocal_rank_fusion(
    vector_results: list[SearchResult],
    bm25_results: list[SearchResult],
    k: int = 60,
) -> list[SearchResult]:
    """
    Reciprocal Rank Fusion -- combines two ranked lists without weight tuning.

    WHY: k=60 is the standard default (Cormack et al., 2009).
         Reused from P1 where this value proved effective.
    INTERVIEW: "RRF eliminates the need to manually tune vector vs keyword weights."
    """
    scores: dict[str, float] = {}
    result_map: dict[str, SearchResult] = {}

    for rank, result in enumerate(vector_results):
        scores[result.chunk_id] = scores.get(result.chunk_id, 0) + 1 / (k + rank + 1)
        result_map[result.chunk_id] = result  # vector result has real similarity

    for rank, result in enumerate(bm25_results):
        scores[result.chunk_id] = scores.get(result.chunk_id, 0) + 1 / (k + rank + 1)
        if result.chunk_id not in result_map:
            result_map[result.chunk_id] = result

    sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    combined = []
    for chunk_id, rrf_score in sorted_ids:
        r = result_map[chunk_id]
        # WHY: Override search_method to "hybrid" since RRF combined both sources
        combined.append(r.model_copy(update={"search_method": "hybrid"}))

    return combined


async def hybrid_search(
    query: str,
    max_results: int = 5,
    threshold: float = SIMILARITY_THRESHOLD,
) -> SearchResponse:
    """
    Main search entry point. Used by:
      - GET /api/v1/knowledge/search (this phase)
      - Phase 4 Fusion Engine Track A input

    WHY: asyncio.gather runs vector and BM25 in parallel for latency reduction.
    RISK: Each search needs its own DB connection from pool.
    """
    start_ms = time.time()

    query_vector = await embed_query(query)

    vec_results, bm25_results = await asyncio.gather(
        vector_search(query_vector, max_results * 2),
        bm25_search(query, max_results * 2),
    )

    combined = reciprocal_rank_fusion(vec_results, bm25_results, k=60)

    # 4. Threshold filter
    filtered = [r for r in combined if r.similarity >= threshold]

    top_results = filtered[:max_results]

    answer = ""
    sources: list[str] = []
    if top_results:
        answer = await generate_search_answer(query, top_results)
        sources = list({
            f"{r.doc_title}, p.{r.page_number}" if r.page_number
            else r.doc_title
            for r in top_results
        })

    elapsed_ms = int((time.time() - start_ms) * 1000)

    return SearchResponse(
        query=query,
        results=top_results,
        answer=answer,
        sources=sources,
        total_results=len(top_results),
        search_meta=SearchMeta(
            vector_hits=len(vec_results),
            bm25_hits=len(bm25_results),
            rrf_combined=len(combined),
            threshold_applied=threshold,
            search_time_ms=elapsed_ms,
        ),
    )
