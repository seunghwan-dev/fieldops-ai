"""
VLM Service — Azure OpenAI GPT-4o Vision.

WHY: Extracts text, tables, and figure semantics from PDF page images.
     Cloud VLM chosen for accuracy over local VRAM constraints.
RISK: API rate limits (GPT-4o: 30 RPM free tier). Retry with exponential backoff.
INTERVIEW: "Cloud VLM for knowledge ingestion accuracy; local LLM for runtime prediction."
"""

import os
import json
import time
import base64
import asyncio
import logging
from pathlib import Path

from openai import AsyncAzureOpenAI
from pdf2image import convert_from_path

from schemas.knowledge import VLMPageResult

logger = logging.getLogger(__name__)

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

VLM_PROMPT = """You are a technical document analyzer. Analyze this page image
and extract ALL content.

RESPOND ONLY IN JSON. No markdown, no preamble.

{
  "page_number": <int>,
  "content_type": "text" | "table" | "figure" | "mixed",
  "text_content": "<all readable text>",
  "tables": [{
    "table_id": "table_1",
    "caption": "...",
    "headers": [...],
    "rows": [[...], ...],
    "semantic_summary": "<one sentence>"
  }],
  "figures": [{
    "figure_id": "fig_1",
    "caption": "...",
    "type": "line_chart" | "bar_chart" | "diagram",
    "semantic_summary": "<trends, key values, conclusions>",
    "key_data_points": ["onset ~180°C", "rapid at 200°C"]
  }]
}"""


def _get_client() -> AsyncAzureOpenAI:
    """
    Create Azure OpenAI client.

    WHY: Lazy initialization to avoid import-time errors when env vars missing.
    """
    return AsyncAzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=AZURE_API_KEY,
        api_version=AZURE_API_VERSION,
    )


def _image_to_base64(pil_image) -> str:
    """Convert PIL image to base64-encoded PNG string."""
    import io
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


async def _call_vlm_for_page(
    client: AsyncAzureOpenAI, image_b64: str, page_num: int
) -> VLMPageResult:
    """
    Call GPT-4o Vision for a single page image.

    WHY: Per-page API call with retry for robustness.
    RISK: JSON parse failure on VLM output. 3 retries with exponential backoff.
    """
    delays = [1, 2, 4]

    for attempt in range(3):
        try:
            start = time.time()
            response = await client.chat.completions.create(
                model=AZURE_DEPLOYMENT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": VLM_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=4096,
                temperature=0.0,
            )
            elapsed = time.time() - start
            raw = response.choices[0].message.content.strip()

            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()

            data = json.loads(raw)
            data["page_number"] = page_num
            logger.info(f"Page {page_num} processed in {elapsed:.1f}s (attempt {attempt + 1})")
            return VLMPageResult(**data)

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Page {page_num} JSON parse failed (attempt {attempt + 1}): {e}")
            if attempt < 2:
                await asyncio.sleep(delays[attempt])
        except Exception as e:
            logger.error(f"Page {page_num} VLM API error (attempt {attempt + 1}): {e}")
            if attempt < 2:
                await asyncio.sleep(delays[attempt])

    # Fallback: return text_content only
    logger.error(f"Page {page_num} all retries failed. Returning fallback.")
    return VLMPageResult(
        page_number=page_num,
        content_type="text",
        text_content=f"[VLM extraction failed for page {page_num}]",
    )


async def extract_from_pdf(pdf_path: str) -> list[VLMPageResult]:
    """
    Extract content from all pages of a PDF via GPT-4o Vision.

    WHY: Full PDF -> per-page VLM extraction pipeline.
    RISK: ~30s per page. 6-page PDF = ~3 min. Timeout accordingly.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(f"Converting PDF to images: {path.name}")
    images = convert_from_path(str(path), dpi=300)
    logger.info(f"PDF has {len(images)} pages")

    client = _get_client()
    results = []

    for idx, image in enumerate(images):
        page_num = idx + 1
        image_b64 = _image_to_base64(image)
        result = await _call_vlm_for_page(client, image_b64, page_num)
        results.append(result)

    return results
