"""
ORCA Context Tools — Read-Only Supabase Access (Layer 2)

These tools allow the Copilot to read completed, persisted agent evidence
from Supabase to explain ORCA's trip decisions.

CRITICAL: All tools are READ-ONLY. No tool writes to any evidence table.
CRITICAL: No tool accesses LangGraph in-memory state or checkpoints.

Reference: 08_AI_ML_AGENTIC_ARCHITECTURE.md, Section 28
"""

from __future__ import annotations

from langchain_core.tools import tool

# TODO: Replace with actual Supabase client
# from app.core.supabase_client import get_supabase


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
    # TODO: Implement Supabase query
    # supabase = get_supabase()
    # result = supabase.table("advisories").select("*").eq("trip_id", trip_id).single().execute()
    # return result.data

    return {
        "status": "stub",
        "message": f"Advisory for trip {trip_id} would be fetched from Supabase.",
        "note": "Implement Supabase query in production.",
    }


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
    # TODO: Implement Supabase query
    # supabase = get_supabase()
    # result = supabase.table("risk_evidence").select("*").eq("trip_id", trip_id).single().execute()
    # return result.data

    return {
        "status": "stub",
        "message": f"Risk evidence for trip {trip_id} would be fetched from Supabase.",
    }


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
    # TODO: Implement Supabase query
    # supabase = get_supabase()
    # result = supabase.table("weather_evidence").select("*").eq("trip_id", trip_id).execute()
    # return result.data

    return {
        "status": "stub",
        "message": f"Weather evidence for trip {trip_id} would be fetched from Supabase.",
    }


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
    # TODO: Implement Supabase query
    return {
        "status": "stub",
        "message": f"Marine evidence for trip {trip_id} would be fetched from Supabase.",
    }


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
    # TODO: Implement Supabase query
    # supabase = get_supabase()
    # result = supabase.table("agent_executions").select("*").eq("trip_id", trip_id).order("started_at").execute()
    # return result.data

    return [
        {
            "status": "stub",
            "message": f"Agent execution history for trip {trip_id} would be fetched from Supabase.",
        }
    ]


# Convenience list for registration
ORCA_CONTEXT_TOOLS = [
    get_trip_advisory,
    get_risk_evidence,
    get_weather_evidence,
    get_marine_evidence,
    get_agent_execution_history,
]
