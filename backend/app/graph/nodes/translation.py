"""
Translation Node — Bhashini Regional Language Translation

Placed after planner_synthesize, before persistence.
Translates the English advisory into the user's regional language.

Architecture:
    planner_synthesize
        ↓
    English advisory
        ↓
    translation_node
        ↓
    Regional language advisory (via Bhashini)
        ↓
    persist_results

Translation priority:
    1. Bhashini (preferred for Indian regional languages)
    2. Gemini fallback (if Bhashini is unavailable)
    3. Original English (if both fail)

Reference: SIH26176 — Indian regional language support
"""

from __future__ import annotations

import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.adapters.bhashini_adapter import BhashiniAdapter, BHASHINI_SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

# Module-level singleton
_bhashini_adapter = BhashiniAdapter()


def translation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Translate the advisory into the user's regional language.

    Reads:
        state["advisory"]["recommendation_text"]
        state["advisory"]["reason"]
        state["advisory"]["language"] or state["trip_context"]["language"]

    Writes:
        state["advisory"]["recommendation_text"] (translated)
        state["advisory"]["reason"] (translated)
        state["advisory"]["translation_provider"]
        state["advisory"]["original_text_en"]
    """
    advisory = state.get("advisory", {})
    trip_ctx = state.get("trip_context", {})

    target_lang = advisory.get("language") or trip_ctx.get("language", "en")
    recommendation = advisory.get("recommendation_text", "")
    reason = advisory.get("reason", "")

    execution = {
        "agent_name": "translation",
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": [],
        "output_summary": "",
        "error": None,
    }

    # --- Skip if English ---
    if target_lang == "en" or not target_lang:
        advisory["translation_provider"] = "none_required"
        execution["status"] = "completed"
        execution["completed_at"] = datetime.now(timezone.utc).isoformat()
        execution["output_summary"] = "No translation needed (English)."
        state["agent_executions"] = [execution]
        return state

    # --- Store original English text ---
    advisory["original_text_en"] = recommendation

    # --- Attempt 1: Bhashini ---
    if target_lang in BHASHINI_SUPPORTED_LANGUAGES and _bhashini_adapter.is_configured:
        rec_result = _bhashini_adapter.translate(
            text=recommendation,
            source_lang="en",
            target_lang=target_lang,
        )

        if rec_result["success"]:
            advisory["recommendation_text"] = rec_result["translated_text"]
            advisory["translation_provider"] = "bhashini"

            # Translate reason too
            reason_result = _bhashini_adapter.translate(
                text=reason,
                source_lang="en",
                target_lang=target_lang,
            )
            if reason_result["success"]:
                advisory["reason"] = reason_result["translated_text"]

            execution["status"] = "completed"
            execution["completed_at"] = datetime.now(timezone.utc).isoformat()
            execution["data_sources"] = ["bhashini"]
            execution["output_summary"] = (
                f"Translated to {target_lang} via Bhashini."
            )
            state["advisory"] = advisory
            state["agent_executions"] = [execution]
            return state
        else:
            logger.warning(
                f"Bhashini translation failed: {rec_result.get('error')}. "
                "Falling back to Gemini."
            )

    # --- Attempt 2: LLM Fallback (Gemini -> Qwen) ---
    try:
        from app.core.llm import get_llm
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = get_llm(temperature=0.1)

        prompt = f"""Translate the following text to language code '{target_lang}'.
Preserve:
- All numerical values exactly as they are
- Risk levels (SAFE, MODERATE, HIGH, SEVERE)
- Source names (Open-Meteo, INCOIS, GDACS)
- Units (m, km/h, °C, mg/m³)
- Warning labels

Return ONLY a JSON object with keys: "recommendation", "reason"

Text to translate:
Recommendation: {recommendation}
Reason: {reason}
"""

        resp = llm.invoke([
            SystemMessage(content="You are a precise translator. Preserve all technical terms."),
            HumanMessage(content=prompt),
        ])

        raw = resp.content.strip().strip("```json").strip("```").strip()
        parsed = json.loads(raw)

        advisory["recommendation_text"] = parsed.get("recommendation", recommendation)
        advisory["reason"] = parsed.get("reason", reason)
        # Keep the public fallback contract stable even when the runtime model stack
        # internally falls back from Gemini to Qwen.
        advisory["translation_provider"] = "gemini_fallback"

        execution["status"] = "completed"
        execution["completed_at"] = datetime.now(timezone.utc).isoformat()
        execution["data_sources"] = ["gemini"]
        execution["output_summary"] = (
            f"Translated to {target_lang} via Gemini (Bhashini unavailable)."
        )
        state["advisory"] = advisory
        state["agent_executions"] = [execution]
        return state

    except Exception as e:
        logger.warning(f"Gemini translation also failed: {e}")
        execution["error"] = f"Both Bhashini and Gemini failed: {e}"

    # --- Attempt 3: Return original English ---
    advisory["translation_provider"] = "unavailable"
    execution["status"] = "completed"
    execution["completed_at"] = datetime.now(timezone.utc).isoformat()
    execution["output_summary"] = (
        f"Translation to {target_lang} unavailable. Returning English."
    )
    state["advisory"] = advisory
    state["agent_executions"] = [execution]
    return state
