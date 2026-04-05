"""
LLM Service -- Qwen 2.5 7B via Ollama.

WHY: Generates natural language answers from search results.
     3-line summary format with source citations.
RISK: Qwen may respond in Chinese when processing Japanese/multilingual input.
      (P1 lesson) Force English in system prompt.
INTERVIEW: "Explicit language instruction prevents Qwen's Chinese fallback."
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")

# WHY: Temperature 0.3 for factual accuracy; higher values cause hallucination.
#      num_predict 300 tokens is enough for 2-3 sentence answer with citations.
SEARCH_ANSWER_SYSTEM = """You are a technical assistant for manufacturing engineers.
Based on the provided search results, answer the question concisely in 2-3 sentences.

RULES:
1. Only use information from the provided search results. Never invent data.
2. Always cite sources in format: (Source: document_name, page/table).
3. If search results are insufficient, say "Insufficient data found."
4. Answer in English only.
"""


async def generate_search_answer(query: str, results: list) -> str:
    """
    Generate a natural language answer from search results using Qwen 7B.

    WHY: Raw search results are hard for engineers to parse quickly.
         LLM synthesizes them into actionable 2-3 sentence answers.
    RISK: Ollama timeout if model not loaded. 30s timeout with graceful fallback.
    """
    context = "\n\n".join([
        f"[Source: {r.doc_title}, p.{r.page_number}]\n{r.chunk_text}"
        for r in results
    ])

    prompt = f"Question: {query}\n\nSearch Results:\n{context}\n\nAnswer:"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": "qwen2.5:7b-instruct-q4_K_M",
                    "system": SEARCH_ANSWER_SYSTEM,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 300,
                    },
                },
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
    except Exception as e:
        # WHY: Graceful degradation -- search results still useful without LLM answer
        logger.warning(f"LLM answer generation failed: {e}")
        return f"[LLM unavailable: {str(e)[:100]}] Please review search results directly."


async def generate_raw(
    system: str, prompt: str, temperature: float = 0.3, max_tokens: int = 500
) -> str:
    """
    Raw LLM generation without post-processing.

    WHY: Fusion prompt requires JSON-only output.
         Different from search_answer which returns natural text.
    RISK: Ollama timeout if model not loaded. 30s timeout.
    INTERVIEW: "Fusion Engine needs raw JSON output for structured parsing."
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": "qwen2.5:7b-instruct-q4_K_M",
                "system": system,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        return response.json().get("response", "")
