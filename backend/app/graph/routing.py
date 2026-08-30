"""
LangGraph Routing — Conditional Edge Functions

These functions determine the graph's control flow at decision points.

Reference: 08_AI_ML_AGENTIC_ARCHITECTURE.md, Section 21 (LangGraph Control Flow)
"""

from __future__ import annotations

from app.graph.state import OrcaState


def should_clarify(state: OrcaState) -> str:
    """Determine whether the Planner needs to ask for more information.

    Returns:
        "clarify" — if critical trip parameters are missing
        "proceed" — if Trip Context is validated and ready for Geo
    """
    trip = state.get("trip_context", {})
    workflow = state.get("workflow_status", "")

    # If the planner explicitly flagged clarification needed
    if workflow == "CLARIFICATION_REQUIRED":
        return "clarify"

    # Check for minimum required fields
    required_fields = ["origin", "departure_time_iso"]
    for field in required_fields:
        if not trip.get(field):
            return "clarify"

    # Vessel profile must have beam_width_m for safety evaluation
    vessel = state.get("vessel_profile", {})
    if not vessel.get("beam_width_m"):
        return "clarify"

    return "proceed"


def route_after_risk(state: OrcaState) -> str:
    """Determine the next step after Risk Engine evaluation.

    Returns:
        "synthesize"    — if risk evidence is available (any category)
        "insufficient"  — if critical data was missing and risk could not complete

    Note: Both routes lead to planner_synthesize, but the Planner
    will generate different advisory text based on the category.
    """
    risk = state.get("risk_evidence", {})
    category = risk.get("advisory_category", "")

    if category == "INSUFFICIENT_INFORMATION":
        return "insufficient"

    return "synthesize"
