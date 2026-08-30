"""
ORCA Context Tools — Read-Only Supabase Access (Layer 2)

These tools allow the Copilot to read completed, persisted agent evidence
from Supabase to explain ORCA's trip decisions.

CRITICAL: All tools are READ-ONLY. No tool writes to any evidence table.
CRITICAL: No tool accesses LangGraph in-memory state or checkpoints.

Reference: 08_AI_ML_AGENTIC_ARCHITECTURE.md, Section 28
"""

from __future__ import annotations

import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _get_client():
    """Get the Supabase client, or None if not configured."""
    try:
        from app.core.supabase import get_supabase_client
        return get_supabase_client()
    except Exception as e:
        logger.warning(f"Could not get Supabase client: {e}")
        return None


def _supabase_unavailable_response(resource: str, identifier: str) -> dict:
    """Consistent response when Supabase is not configured."""
    return {
        "status": "supabase_not_configured",
        "resource": resource,
        "identifier": identifier,
        "message": (
            "Supabase is not configured. To enable evidence retrieval, "
            "set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the .env file."
        ),
    }


@tool
def get_trip_advisory(trip_id: str) -> dict:
    """Retrieve the final advisory for a completed trip.

    Use this when the fisherman asks about a trip decision, e.g.:
    - "Why did ORCA say my trip is risky?"
    - "What was the recommendation for my last trip?"

    Args:
        trip_id: The UUID of the completed trip.

    Returns:
        The advisory dict with recommendation_text, advisory_category,
        reason, affected_phase, and evidence_summary.
    """
    client = _get_client()
    if not client:
        return _supabase_unavailable_response("advisory", trip_id)

    try:
        result = (
            client.table("advisories")
            .select("*")
            .eq("trip_id", trip_id)
            .maybe_single()
            .execute()
        )
        if result.data:
            return {"status": "found", "data": result.data}
        return {"status": "not_found", "trip_id": trip_id}
    except Exception as e:
        logger.warning(f"Advisory query failed: {e}")
        return {"status": "error", "trip_id": trip_id, "error": str(e)}


@tool
def get_risk_evidence(trip_id: str) -> dict:
    """Retrieve the structured Risk Evidence for a completed trip.

    Use this when the fisherman asks WHY a decision was made, e.g.:
    - "Why is my return dangerous?"
    - "What hazards were found?"

    Args:
        trip_id: The UUID of the completed trip.

    Returns:
        RiskEvidence dict with advisory_category, risk_level, hazard_flags,
        and the specific thresholds that were exceeded.
    """
    client = _get_client()
    if not client:
        return _supabase_unavailable_response("risk_evidence", trip_id)

    try:
        result = (
            client.table("risk_evidence")
            .select("*")
            .eq("trip_id", trip_id)
            .maybe_single()
            .execute()
        )
        if result.data:
            return {"status": "found", "data": result.data}
        return {"status": "not_found", "trip_id": trip_id}
    except Exception as e:
        logger.warning(f"Risk evidence query failed: {e}")
        return {"status": "error", "trip_id": trip_id, "error": str(e)}


@tool
def get_weather_evidence(trip_id: str) -> dict:
    """Retrieve the weather observations that agents collected for a trip.

    Use this when the fisherman asks about weather conditions, e.g.:
    - "What was the wave height during my trip?"
    - "What weather data did ORCA use?"

    Args:
        trip_id: The UUID of the completed trip.

    Returns:
        List of WeatherObservation dicts matched to trajectory waypoints.
    """
    client = _get_client()
    if not client:
        return _supabase_unavailable_response("weather_evidence", trip_id)

    try:
        result = (
            client.table("weather_evidence")
            .select("*")
            .eq("trip_id", trip_id)
            .execute()
        )
        return {
            "status": "found" if result.data else "not_found",
            "trip_id": trip_id,
            "count": len(result.data) if result.data else 0,
            "data": result.data or [],
        }
    except Exception as e:
        logger.warning(f"Weather evidence query failed: {e}")
        return {"status": "error", "trip_id": trip_id, "error": str(e)}


@tool
def get_marine_evidence(trip_id: str) -> dict:
    """Retrieve the marine observations that agents collected for a trip.

    Use this when the fisherman asks about marine/fishing data, e.g.:
    - "What PFZ data was used?"
    - "Was there any HAB detected?"

    Args:
        trip_id: The UUID of the completed trip.

    Returns:
        List of MarineObservation dicts plus PFZ data.
    """
    client = _get_client()
    if not client:
        return _supabase_unavailable_response("marine_evidence", trip_id)

    try:
        result = (
            client.table("marine_evidence")
            .select("*")
            .eq("trip_id", trip_id)
            .execute()
        )
        return {
            "status": "found" if result.data else "not_found",
            "trip_id": trip_id,
            "count": len(result.data) if result.data else 0,
            "data": result.data or [],
        }
    except Exception as e:
        logger.warning(f"Marine evidence query failed: {e}")
        return {"status": "error", "trip_id": trip_id, "error": str(e)}


@tool
def get_agent_execution_history(trip_id: str) -> list[dict]:
    """Retrieve what each agent did during a trip assessment.

    Use this when the fisherman asks about agent behavior, e.g.:
    - "What did the weather agent do?"
    - "Did any agent fail?"
    - "What data sources were used?"

    Args:
        trip_id: The UUID of the completed trip.

    Returns:
        List of AgentExecution dicts with agent_name, status, data_sources,
        input_summary, output_data, and timestamps.
    """
    client = _get_client()
    if not client:
        return [_supabase_unavailable_response("agent_executions", trip_id)]

    try:
        result = (
            client.table("agent_executions")
            .select("*")
            .eq("trip_id", trip_id)
            .order("started_at")
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.warning(f"Agent execution query failed: {e}")
        return [{"status": "error", "trip_id": trip_id, "error": str(e)}]


# Convenience list for registration
ORCA_CONTEXT_TOOLS = [
    get_trip_advisory,
    get_risk_evidence,
    get_weather_evidence,
    get_marine_evidence,
    get_agent_execution_history,
]
