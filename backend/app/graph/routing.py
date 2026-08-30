"""
LangGraph Routing — Conditional Edge Functions for Supervisor Architecture

These functions determine the graph's control flow at decision points.
The Supervisor produces a TaskPlan, and these routers use it to
dynamically select which capabilities execute.

Reference: SIH26176 — Autonomous planning, task decomposition
"""

from __future__ import annotations

from app.graph.state import OrcaState, APPROVED_CAPABILITIES


# ---------------------------------------------------------------------------
# Deterministic Dependency Map
# ---------------------------------------------------------------------------

DEPENDENCY_MAP = {
    "route": ["geo", "weather", "marine", "risk"],
    "ocean_analytics": ["marine", "weather"],
    "visualization": ["geo"],
    "reporting": ["risk"],
    "risk": ["geo", "weather", "marine"],
}


def resolve_dependencies(task_plan: dict) -> dict:
    """Deterministic dependency resolver.

    If the Supervisor requests a capability that has prerequisites,
    the resolver automatically adds the required capabilities.

    Example:
        Supervisor requests: ["route"]
        Resolver resolves to: ["geo", "weather", "marine", "risk", "route"]

    This ensures the graph has all the data it needs before executing
    a downstream component, regardless of what the LLM selected.
    """
    caps = set(task_plan.get("required_capabilities", []))
    resolved = set(caps)

    # Iteratively resolve until stable
    changed = True
    while changed:
        changed = False
        for cap in list(resolved):
            deps = DEPENDENCY_MAP.get(cap, [])
            for dep in deps:
                if dep not in resolved and dep in APPROVED_CAPABILITIES:
                    resolved.add(dep)
                    changed = True

    task_plan["required_capabilities"] = [
        c for c in task_plan["required_capabilities"] if c in resolved
    ] + [c for c in resolved if c not in task_plan.get("required_capabilities", [])]

    return task_plan


def supervisor_router(state: OrcaState) -> str:
    """Route after Supervisor based on TaskPlan.

    Returns:
        "clarify"  — if critical parameters are missing
        "knowledge" — if only knowledge/RAG is needed (skip entire pipeline)
        "proceed"  — if trip/operational capabilities are needed
    """
    task_plan = state.get("task_plan", {})
    workflow = state.get("workflow_status", "")

    # If clarification is needed
    if workflow == "CLARIFICATION_REQUIRED" or task_plan.get("clarification_required"):
        return "clarify"

    # If only knowledge/copilot is needed — skip the data pipeline entirely
    caps = set(task_plan.get("required_capabilities", []))
    knowledge_only = caps.issubset({"knowledge", "copilot"})
    if knowledge_only and caps:
        return "knowledge"

    return "proceed"


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


def post_risk_router(state: OrcaState) -> str:
    """Route after risk node based on TaskPlan capabilities.

    Determines whether to run optional post-risk nodes
    (ocean_analytics, route, visualization, reporting) or go straight
    to synthesis.
    """
    task_plan = state.get("task_plan", {})
    caps = set(task_plan.get("required_capabilities", []))

    # If any post-risk capability is requested, go to post-processing
    post_risk_caps = {"ocean_analytics", "route", "visualization", "reporting"}
    if caps & post_risk_caps:
        return "post_process"

    return "synthesize"
