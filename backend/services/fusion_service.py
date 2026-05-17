"""
Fusion Service -- Dual-Track Prediction + LLM Fusion + Rule Safety.

WHY: Orchestrates Track A (RAG) + Track B (ML) in parallel,
     then applies LLM-based fusion judgment + deterministic safety rules.
     This is the core differentiator from ML-only prediction.
RISK: Qwen 7B may output invalid JSON or Chinese text.
     3-retry + markdown strip + fallback to Rule-only.
INTERVIEW: "Layer 1 (LLM) provides flexible judgment with citations.
            Layer 2 (Rules) provides non-negotiable safety guarantees.
            Even if LLM fails completely, the system never outputs unsafe values."
"""

import json
import time
import asyncio
import logging

from services.search_service import hybrid_search
from services.ml_service import predict_mixer, predict_grinder
from services.llm_service import generate_raw
from services.safety_service import safety_service

logger = logging.getLogger(__name__)

FUSION_SYSTEM_PROMPT = """You are a Domain-ML Fusion Engine for manufacturing process optimization.

RULES:
1. If domain knowledge contradicts ML on SAFETY, domain wins.
2. If no relevant domain data, rely on ML with explicit caveat.
3. Always cite sources (paper name, page, table number).
4. Never invent data. If uncertain, say "insufficient domain data".
5. Output confidence_score 0.0-1.0 for the FUSED result.

RESPOND ONLY IN JSON. English only.
No markdown fences, no preamble, no explanation outside JSON.

Required JSON structure:
{
  "fused_prediction": <number>,
  "correction_applied": <true/false>,
  "correction_delta": <number or 0>,
  "correction_reason": "<string>",
  "domain_evidence": ["<source1>", "<source2>"],
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "recommendation": "<string>",
  "confidence_score": <0.0-1.0>
}"""


_GRINDER_MATERIALS = {"Material G", "Material H", "Material I", "Material J",
                       "Material K", "Material L", "Material M", "Material N"}


def _equipment_type(material: str) -> str:
    """
    Map material name to equipment type.

    WHY: Materials G~N -> grinder (Equipment B), all others -> mixer (Equipment A).
    """
    if material in _GRINDER_MATERIALS:
        return "grinder"
    return "mixer"


def _prediction_value(track_b: dict) -> float:
    """Extract the primary prediction value from Track B result."""
    pred = track_b["prediction"]
    if pred.get("discharge_temp_celsius") is not None:
        return pred["discharge_temp_celsius"]
    if pred.get("d50_micron") is not None:
        return pred["d50_micron"]
    return 0.0


def _prediction_unit(material: str) -> str:
    return "°C" if _equipment_type(material) == "mixer" else "μm"


async def _run_track_a(material: str, conditions: dict) -> dict:
    """
    Track A: Domain RAG search.

    WHY: Retrieves relevant domain knowledge for fusion context.
    RISK: Track A failure is non-fatal -- fusion continues with ML + Rules.
    """
    start = time.time()
    try:
        # WHY: Build search query from material + key conditions for relevance.
        parts = [material]
        if "temperature_celsius" in conditions:
            parts.append(f"temperature {conditions['temperature_celsius']}°C")
        if "rpm" in conditions:
            parts.append(f"rpm {int(conditions['rpm'])}")
        if "grinding_pressure_mpa" in conditions:
            parts.append(f"grinding pressure {conditions['grinding_pressure_mpa']} MPa")
        query = " ".join(parts)

        search_resp = await hybrid_search(query=query, max_results=5)
        elapsed = (time.time() - start) * 1000

        top_results = []
        for r in search_resp.results:
            top_results.append({
                "source": r.doc_title,
                "page": r.page_number,
                "similarity": r.similarity,
                "text": r.chunk_text[:300],
            })

        return {
            "rag_hits": search_resp.total_results,
            "top_results": top_results,
            "time_ms": round(elapsed, 1),
        }
    except Exception as e:
        logger.warning(f"Track A failed: {e}")
        elapsed = (time.time() - start) * 1000
        return {"rag_hits": 0, "top_results": [], "time_ms": round(elapsed, 1)}


async def _run_track_b(material: str, conditions: dict) -> dict:
    """
    Track B: ML prediction.

    WHY: Numerical prediction is mandatory -- Track B failure is fatal.
    """
    if _equipment_type(material) == "mixer":
        return await predict_mixer(conditions)
    else:
        return await predict_grinder(conditions)


def _build_user_prompt(material: str, conditions: dict, track_a: dict, track_b: dict) -> str:
    """
    Build dynamic user prompt for LLM fusion.

    WHY: Provides both tracks' outputs for LLM to synthesize.
    """
    pred_value = _prediction_value(track_b)
    unit = _prediction_unit(material)
    confidence = track_b["prediction"]["confidence"]

    top_shap = track_b["shap"]["top_factors"][:3]
    shap_str = json.dumps(top_shap, indent=2)

    rag_formatted = ""
    for r in track_a.get("top_results", []):
        rag_formatted += f"\n[Source: {r['source']}, p.{r['page']}]\n{r['text']}\n"

    if not rag_formatted.strip():
        rag_formatted = "\nNo relevant domain knowledge found.\n"

    return f"""PREDICTION INPUT:
Material: {material}
Conditions: {json.dumps(conditions)}

TRACK B — ML PREDICTION:
Predicted value: {pred_value}{unit}
Confidence: {confidence}
Top SHAP factors:
{shap_str}

TRACK A — DOMAIN KNOWLEDGE ({track_a.get('rag_hits', 0)} hits):
{rag_formatted}

TASK: Analyze both tracks. If domain knowledge indicates safety concerns
that ML does not capture, recommend a corrected value with evidence.
Output JSON only."""


def _strip_markdown_fences(text: str) -> str:
    """
    Strip markdown code fences from LLM output.

    WHY: Qwen frequently wraps JSON in ```json ... ```.
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n", 1)
        text = lines[1] if len(lines) > 1 else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def _llm_fusion(track_a: dict, track_b: dict, material: str, conditions: dict) -> dict:
    """
    Layer 1: LLM Fusion via Qwen 7B.

    WHY: Flexible judgment that synthesizes RAG + ML with domain reasoning.
    RISK: JSON parse failure. 3 retries, then fallback to rule-only mode.
    INTERVIEW: "Layer 1 is best-effort. Layer 2 (Rules) is the safety net."
    """
    user_prompt = _build_user_prompt(material, conditions, track_a, track_b)
    pred_value = _prediction_value(track_b)
    ml_confidence = track_b["prediction"]["confidence"]

    for attempt in range(3):
        try:
            raw = await generate_raw(
                system=FUSION_SYSTEM_PROMPT,
                prompt=user_prompt,
                temperature=0.3,
                max_tokens=500,
            )
            cleaned = _strip_markdown_fences(raw)
            result = json.loads(cleaned)

            _ = result["fused_prediction"]
            result["fusion_method"] = "llm_fusion"
            logger.info(f"LLM fusion succeeded (attempt {attempt + 1})")
            return result

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"LLM fusion JSON parse failed (attempt {attempt + 1}): {e}")
        except Exception as e:
            logger.warning(f"LLM fusion error (attempt {attempt + 1}): {e}")

    # WHY: Fallback preserves ML prediction. Layer 2 Rules will still catch safety issues.
    logger.error("LLM fusion failed after 3 retries. Using rule_only_fallback.")
    return {
        "fused_prediction": pred_value,
        "correction_applied": False,
        "correction_delta": 0,
        "correction_reason": "LLM fusion unavailable. ML prediction used as-is.",
        "domain_evidence": [],
        "risk_level": "MEDIUM",
        "recommendation": "LLM analysis failed. Manual review strongly recommended.",
        "confidence_score": ml_confidence * 0.5,
        "fusion_method": "rule_only_fallback",
    }


async def predict(request) -> dict:
    """
    Main fusion predict entry point.

    WHY: Single function handles both ml_only and fusion modes.
    INTERVIEW: "One API, two modes. Before shows ML blind spot. After shows AI correction."
    """
    total_start = time.time()
    material = request.material
    conditions = request.conditions
    eq_type = _equipment_type(material)

    if request.mode == "ml_only":
        track_b = await _run_track_b(material, conditions)
        elapsed = (time.time() - total_start) * 1000
        return {
            "mode": "ml_only",
            "prediction": track_b["prediction"],
            "shap": track_b["shap"],
            "domain_knowledge": None,
            "fusion": None,
            "safety_overrides": [],
            "requires_human_review": True,
            "meta": {
                "track_a_time_ms": 0,
                "track_b_time_ms": track_b["meta"]["track_b_time_ms"],
                "fusion_time_ms": 0,
                "total_time_ms": round(elapsed, 1),
            },
        }

    track_a, track_b = await asyncio.gather(
        _run_track_a(material, conditions),
        _run_track_b(material, conditions),
    )

    fusion_start = time.time()
    fusion_result = await _llm_fusion(track_a, track_b, material, conditions)
    fusion_time = (time.time() - fusion_start) * 1000

    # Step 3: Layer 2 — Rule Safety (always executes)
    safety_overrides = safety_service.apply_rules(
        fusion_result=fusion_result,
        ml_prediction=track_b["prediction"],
        material=material,
        conditions=conditions,
    )

    total_time = (time.time() - total_start) * 1000

    return {
        "mode": "fusion",
        "prediction": track_b["prediction"],
        "shap": track_b["shap"],
        "domain_knowledge": track_a,
        "fusion": fusion_result,
        "safety_overrides": safety_overrides,
        "requires_human_review": True,
        "meta": {
            "track_a_time_ms": track_a.get("time_ms", 0),
            "track_b_time_ms": track_b["meta"]["track_b_time_ms"],
            "fusion_time_ms": round(fusion_time, 1),
            "total_time_ms": round(total_time, 1),
        },
    }
