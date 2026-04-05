"""
Embedding Service Client.

WHY: HTTP client for the standalone embedding server (port 8001).
     Adds "passage: " prefix for document chunks, "query: " for search queries.
RISK: Embedding server down -> ingestion fails. Retry 3x.
INTERVIEW: "e5-large requires prefix differentiation -- query vs passage."
"""

import os
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

EMBEDDING_HOST = os.getenv("EMBEDDING_HOST", "http://embedding:8001")
BATCH_SIZE = 16


async def embed_passages(texts: list[str]) -> list[list[float]]:
    """
    Embed document chunks with "passage: " prefix.

    WHY: e5-large uses "passage: " prefix for documents, "query: " for queries.
         Missing prefix degrades similarity by ~0.15 (P1 empirical finding).
    RISK: Embedding server OOM if batch too large. Batch size capped at 16.
    """
    prefixed = [f"passage: {t}" for t in texts]
    return await _embed_batch(prefixed)


async def embed_query(text: str) -> list[float]:
    """
    Embed a search query with "query: " prefix.

    WHY: Query prefix tells e5-large to encode for retrieval matching.
         Used in Phase 2 RAG search pipeline.
    """
    result = await _embed_batch([f"query: {text}"])
    return result[0]


async def _embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Send texts to embedding server in batches with retry logic.

    WHY: Batching reduces HTTP overhead. Retry handles transient failures.
    RISK: 3 retries × 2s delay = 6s max wait per batch on failure.
    """
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        embeddings = await _call_embed_api(batch)
        all_embeddings.extend(embeddings)

    return all_embeddings


async def _call_embed_api(texts: list[str]) -> list[list[float]]:
    """Call the embedding server /embed endpoint with retry."""
    url = f"{EMBEDDING_HOST}/embed"

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json={"texts": texts})
                resp.raise_for_status()
                data = resp.json()
                return data["embeddings"]
        except Exception as e:
            logger.warning(f"Embedding API call failed (attempt {attempt + 1}): {e}")
            if attempt < 2:
                await asyncio.sleep(2)

    raise RuntimeError(f"Embedding API failed after 3 retries for {len(texts)} texts")
