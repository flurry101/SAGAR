"""
Assessment Repository — Supabase Persistence Layer

Persists completed ORCA assessment results to Supabase.

CRITICAL: Persistence failure MUST NOT corrupt the safety decision.
The graph must report risk_decision = completed, persistence_status = failed
rather than pretending persistence succeeded.

Reference: SIH26176 — Evidence persistence, provenance tracking
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_client():
    """Get the Supabase client, or None if not configured."""
    try:
        from app.core.supabase import get_supabase_client
        return get_supabase_client()
    except Exception as e:
        logger.warning(f"Could not get Supabase client: {e}")
        return None


def _safe_json(obj: Any) -> Any:
    """Convert an object to JSON-safe format for Supabase insertion."""
    if obj is None:
        return None
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def persist_assessment(state: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a complete ORCA assessment to Supabase.

    Persists to tables:
        - assessments (top-level record)
        - risk_evidence
        - weather_evidence
        - marine_evidence
        - advisories
        - agent_executions

    Returns:
        {
            "persistence_status": "success" | "partial" | "failed" | "supabase_not_configured",
            "tables_written": [...],
            "errors": [...]
        }
    """
    client = _get_client()
    if not client:
        return {
            "persistence_status": "supabase_not_configured",
            "tables_written": [],
            "errors": ["Supabase client is not configured."],
        }

    assessment_id = str(uuid.uuid4())
    trip_ctx = state.get("trip_context", {})
    trip_id = trip_ctx.get("trip_id", assessment_id)
    now_iso = datetime.now(timezone.utc).isoformat()

    tables_written = []
    errors = []

    # --- 1. Assessment (top-level record) ---
    try:
        client.table("assessments").insert({
            "assessment_id": assessment_id,
            "trip_id": trip_id,
            "origin": trip_ctx.get("origin"),
            "departure_time": trip_ctx.get("departure_time_iso"),
            "language": trip_ctx.get("language", "en"),
            "overall_risk_level": state.get("overall_risk_level", "UNKNOWN"),
            "workflow_status": state.get("workflow_status", "UNKNOWN"),
            "created_at": now_iso,
            "task_plan": _safe_json(state.get("task_plan")),
        }).execute()
        tables_written.append("assessments")
    except Exception as e:
        errors.append(f"assessments: {e}")

    # --- 2. Risk Evidence ---
    risk = state.get("risk_evidence")
    if risk:
        try:
            client.table("risk_evidence").insert({
                "assessment_id": assessment_id,
                "trip_id": trip_id,
                "advisory_category": risk.get("advisory_category"),
                "risk_level": state.get("overall_risk_level"),
                "summary": risk.get("summary"),
                "evidence_json": _safe_json(risk),
                "created_at": now_iso,
            }).execute()
            tables_written.append("risk_evidence")
        except Exception as e:
            errors.append(f"risk_evidence: {e}")

    # --- 3. Weather Evidence ---
    weather_obs = state.get("weather_observations", [])
    if weather_obs:
        try:
            rows = []
            for obs in weather_obs:
                rows.append({
                    "assessment_id": assessment_id,
                    "trip_id": trip_id,
                    "waypoint_index": obs.get("waypoint_index"),
                    "lat": obs.get("lat"),
                    "lon": obs.get("lon"),
                    "time_iso": obs.get("time_iso"),
                    "weather_json": _safe_json(obs.get("weather")),
                    "created_at": now_iso,
                })
            client.table("weather_evidence").insert(rows).execute()
            tables_written.append("weather_evidence")
        except Exception as e:
            errors.append(f"weather_evidence: {e}")

    # --- 4. Marine Evidence ---
    marine_obs = state.get("marine_observations", [])
    if marine_obs:
        try:
            rows = []
            for obs in marine_obs:
                rows.append({
                    "assessment_id": assessment_id,
                    "trip_id": trip_id,
                    "lat": obs.get("lat"),
                    "lon": obs.get("lon"),
                    "marine_json": _safe_json(obs.get("marine")),
                    "created_at": now_iso,
                })
            client.table("marine_evidence").insert(rows).execute()
            tables_written.append("marine_evidence")
        except Exception as e:
            errors.append(f"marine_evidence: {e}")

    # --- 5. Advisory ---
    advisory = state.get("advisory")
    if advisory:
        try:
            client.table("advisories").insert({
                "assessment_id": assessment_id,
                "trip_id": trip_id,
                "advisory_category": advisory.get("advisory_category"),
                "recommendation_text": advisory.get("recommendation_text"),
                "reason": advisory.get("reason"),
                "language": advisory.get("language", "en"),
                "translation_provider": advisory.get("translation_provider"),
                "evidence_summary": advisory.get("evidence_summary"),
                "disclaimer": advisory.get("disclaimer"),
                "created_at": now_iso,
            }).execute()
            tables_written.append("advisories")
        except Exception as e:
            errors.append(f"advisories: {e}")

    # --- 6. Agent Executions ---
    executions = state.get("agent_executions", [])
    if executions:
        try:
            rows = []
            for ex in executions:
                rows.append({
                    "assessment_id": assessment_id,
                    "trip_id": trip_id,
                    "agent_name": ex.get("agent_name"),
                    "status": ex.get("status"),
                    "started_at": ex.get("started_at"),
                    "completed_at": ex.get("completed_at"),
                    "data_sources": _safe_json(ex.get("data_sources")),
                    "output_summary": ex.get("output_summary"),
                    "error": ex.get("error"),
                })
            client.table("agent_executions").insert(rows).execute()
            tables_written.append("agent_executions")
        except Exception as e:
            errors.append(f"agent_executions: {e}")

    # --- 7. Report (if generated) ---
    report = state.get("report")
    if report:
        try:
            client.table("reports").insert({
                "assessment_id": assessment_id,
                "trip_id": trip_id,
                "summary": report.get("summary"),
                "recommendation": report.get("recommendation"),
                "report_json": _safe_json(report),
                "created_at": now_iso,
            }).execute()
            tables_written.append("reports")
        except Exception as e:
            errors.append(f"reports: {e}")

    # --- Determine overall status ---
    if not errors:
        status = "success"
    elif tables_written:
        status = "partial"
    else:
        status = "failed"

    return {
        "persistence_status": status,
        "assessment_id": assessment_id,
        "tables_written": tables_written,
        "errors": errors,
    }
