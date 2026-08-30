"""
Supervisor Agent — Autonomous Intent Understanding & Task Decomposition

The Supervisor is the brain of ORCA's bounded-autonomous architecture.
It uses Gemini structured output to produce a TaskPlan that determines
which specialized capabilities are needed for a given user request.

CRITICAL SAFETY RULE:
    The Supervisor may choose WHICH capabilities are needed.
    The Supervisor must NEVER choose the final safety outcome.
    The Safety Guard enforces mandatory risk assessment for trip/navigation queries.

Reference: SIH26176 — Autonomous planning, task decomposition, agent coordination
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from app.graph.state import OrcaState, APPROVED_CAPABILITIES


# ---------------------------------------------------------------------------
# Safety Guard — deterministic policy layer
# ---------------------------------------------------------------------------

# Keywords that indicate a trip/navigation/safety request
TRIP_KEYWORDS = [
    "safe", "safety", "trip", "fishing", "go", "leave", "venture", "sail",
    "navigate", "route", "journey", "travel", "depart", "return",
    "tomorrow", "morning", "evening", "tonight", "today",
    "boat", "vessel", "sea", "ocean", "harbor", "port",
    "risk", "danger", "hazard", "cyclone", "storm", "wave",
]

KNOWLEDGE_KEYWORDS = [
    "what is", "what are", "explain", "define", "meaning", "means",
    "tell me about", "how does", "why", "difference between",
]


def enforce_safety_requirements(task_plan: dict, user_message: str) -> dict:
    """Safety Guard: enforce mandatory capabilities for trip/navigation requests.

    Even if the Supervisor forgets to include 'risk', this guard adds it.
    The Supervisor is allowed to UNDER-REQUEST capabilities.
    The Safety Guard can ADD but never REMOVE mandatory safety evaluation.
    """
    caps = set(task_plan.get("required_capabilities", []))
    msg_lower = user_message.lower()

    # If it looks like a trip/navigation request, force safety capabilities
    is_trip = task_plan.get("requires_safety_assessment", False)
    if not is_trip:
        trip_score = sum(1 for kw in TRIP_KEYWORDS if kw in msg_lower)
        if trip_score >= 2:
            is_trip = True

    if is_trip:
        # Mandatory for any trip assessment
        for mandatory in ["geo", "weather", "marine", "risk"]:
            caps.add(mandatory)
        task_plan["requires_safety_assessment"] = True

    # If route is requested, geo and risk are mandatory
    if "route" in caps:
        caps.update(["geo", "weather", "risk"])
        task_plan["requires_safety_assessment"] = True

    # Filter to only approved capabilities
    caps = [c for c in caps if c in APPROVED_CAPABILITIES]

    task_plan["required_capabilities"] = caps
    return task_plan


# ---------------------------------------------------------------------------
# Supervisor Node
# ---------------------------------------------------------------------------

def supervisor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Supervisor: understand intent, decompose task, select capabilities.

    Uses Gemini structured output to produce a TaskPlan.
    Then applies the Safety Guard to enforce mandatory capabilities.

    This node replaces the old planner_intake as the graph entry point.
    It still extracts trip_context (origin, time, language) from the message,
    but ALSO produces a structured task plan for dynamic routing.
    """
    execution = {
        "agent_name": "supervisor",
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": [],
        "input_summary": {"phase": "task_decomposition"},
        "output_data": {},
        "error": None,
    }

    history = state.get("conversation_history", [])
    trip = state.get("trip_context", {})
    vessel = state.get("vessel_profile", {})
    user_message = ""

    if history:
        user_message = history[-1].get("content", "")

    # --- LLM-based intent understanding & task decomposition ---
    api_key = os.environ.get("GOOGLE_API_KEY")
    task_plan = _default_task_plan(user_message)

    if api_key and user_message:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=api_key,
                temperature=0.1,
            )

            prompt = f"""You are the ORCA Supervisor Agent for a marine intelligence platform.

Analyze the user's message and produce a structured task plan.

APPROVED CAPABILITIES (you may ONLY select from these):
- geo: geospatial calculations, trajectory, bounding box, geofencing
- marine: PFZ, SST, chlorophyll, marine observations
- weather: wind, waves, forecast, hazard alerts, cyclone, lightning
- ocean_analytics: correlate SST + chlorophyll + PFZ for fishing opportunity
- route: route optimization considering weather and geofences
- risk: deterministic safety assessment (REQUIRED for any trip/navigation)
- visualization: generate map layer specifications
- reporting: generate structured evidence-backed report
- knowledge: search marine knowledge base (RAG) for general questions
- copilot: general conversational response

RULES:
1. For trip/navigation/safety questions → MUST include geo, weather, marine, risk
2. For general knowledge questions (e.g. "What is SST?") → use knowledge only
3. For PFZ queries → include marine, geo, visualization
4. For weather queries → include weather, geo
5. For route queries → include geo, marine, weather, route, risk, visualization

Also extract trip details from the message if present:
- origin: string (port/city name)
- departure_time_iso: ISO 8601 string or null
- language: ISO 639-1 code (en, hi, ta, te, kn, ml, mr, bn, gu, or)

Return ONLY a JSON object with these keys:
- intent: string describing what user wants
- required_capabilities: list of capability strings
- priority: "safety" | "information" | "planning"
- requires_safety_assessment: boolean
- requires_route: boolean
- requires_visualization: boolean
- requires_report: boolean
- clarification_required: boolean
- clarification_question: string or null
- reasoning_summary: brief rationale
- extracted_origin: string or null
- extracted_departure_time: string or null
- extracted_language: string (default "en")

User message: {user_message}
"""
            resp = llm.invoke([
                SystemMessage(content="You are an intent classification and task decomposition assistant."),
                HumanMessage(content=prompt),
            ])

            raw = resp.content.strip().strip("```json").strip("```").strip()
            parsed = json.loads(raw)

            task_plan = {
                "intent": parsed.get("intent", "unknown"),
                "required_capabilities": [
                    c for c in parsed.get("required_capabilities", [])
                    if c in APPROVED_CAPABILITIES
                ],
                "priority": parsed.get("priority", "information"),
                "requires_safety_assessment": parsed.get("requires_safety_assessment", False),
                "requires_route": parsed.get("requires_route", False),
                "requires_visualization": parsed.get("requires_visualization", False),
                "requires_report": parsed.get("requires_report", False),
                "clarification_required": parsed.get("clarification_required", False),
                "clarification_question": parsed.get("clarification_question"),
                "reasoning_summary": parsed.get("reasoning_summary", ""),
            }

            # Extract trip context from Supervisor response
            if parsed.get("extracted_origin"):
                trip["origin"] = parsed["extracted_origin"]
            if parsed.get("extracted_departure_time"):
                trip["departure_time_iso"] = parsed["extracted_departure_time"]
            if parsed.get("extracted_language"):
                trip["language"] = parsed["extracted_language"]

        except Exception as e:
            execution["error"] = f"Supervisor LLM failed: {e}"
            # Fall back to default task plan

    # --- Apply Safety Guard ---
    task_plan = enforce_safety_requirements(task_plan, user_message)

    # --- Apply Dependency Resolver ---
    from app.graph.routing import resolve_dependencies
    task_plan = resolve_dependencies(task_plan)

    # --- Check for clarification needs ---
    if task_plan.get("requires_safety_assessment"):
        required_trip = ["origin", "departure_time_iso"]
        missing = [f for f in required_trip if not trip.get(f)]
        if not vessel.get("beam_width_m"):
            missing.append("beam_width_m")

        if missing:
            task_plan["clarification_required"] = True
            task_plan["clarification_question"] = (
                f"I need more information to assess safety. "
                f"Please provide: {', '.join(missing)}"
            )

    # --- Update state ---
    state["task_plan"] = task_plan
    state["trip_context"] = trip
    state["workflow_status"] = (
        "CLARIFICATION_REQUIRED" if task_plan.get("clarification_required")
        else "TASK_PLANNED"
    )

    execution["status"] = "completed"
    execution["completed_at"] = datetime.now(timezone.utc).isoformat()
    execution["output_data"] = {
        "intent": task_plan.get("intent"),
        "capabilities": task_plan.get("required_capabilities"),
        "safety_required": task_plan.get("requires_safety_assessment"),
    }
    state.setdefault("agent_executions", []).append(execution)

    return state


def _default_task_plan(user_message: str) -> dict:
    """Fallback task plan when LLM is unavailable.

    Uses keyword-based intent classification to produce a reasonable
    TaskPlan even without Gemini. This ensures the system remains
    operational when the LLM is temporarily down.
    """
    msg_lower = user_message.lower()

    # --- Keyword-based fallback classification ---
    is_knowledge = any(kw in msg_lower for kw in KNOWLEDGE_KEYWORDS)

    # PFZ / marine query
    pfz_keywords = ["pfz", "fishing zone", "potential fishing", "fish zone"]
    is_pfz = any(kw in msg_lower for kw in pfz_keywords)

    # Weather-only query
    weather_keywords = ["weather", "forecast", "rain", "wind speed", "wave height"]
    is_weather = any(kw in msg_lower for kw in weather_keywords) and not any(
        kw in msg_lower for kw in ["safe", "trip", "route", "go"]
    )

    # Route query
    route_keywords = ["route", "path", "navigate to", "safest route", "shortest"]
    is_route = any(kw in msg_lower for kw in route_keywords)

    # SST / chlorophyll / marine science
    marine_science = ["sst", "sea surface temperature", "chlorophyll", "ocean temperature"]
    is_marine_science = any(kw in msg_lower for kw in marine_science)

    # Alert query
    alert_keywords = ["alert", "warning", "cyclone", "storm", "hazard"]
    is_alert = any(kw in msg_lower for kw in alert_keywords) and not any(
        kw in msg_lower for kw in ["safe", "trip", "route"]
    )

    # Trip/safety (broadest — caught last)
    is_trip = any(kw in msg_lower for kw in TRIP_KEYWORDS[:12])

    # --- Build plan by priority (specific intents FIRST) ---

    # Marine science knowledge (specific knowledge, before generic)
    if is_marine_science and not is_trip:
        return {
            "intent": "marine_science_query",
            "required_capabilities": ["knowledge"],
            "priority": "information",
            "requires_safety_assessment": False,
            "requires_route": False,
            "requires_visualization": False,
            "requires_report": False,
            "clarification_required": False,
            "clarification_question": None,
            "reasoning_summary": "Marine science question detected via keyword fallback.",
        }

    # PFZ query
    if is_pfz and not is_trip:
        return {
            "intent": "pfz_query",
            "required_capabilities": ["marine", "geo", "visualization"],
            "priority": "information",
            "requires_safety_assessment": False,
            "requires_route": False,
            "requires_visualization": True,
            "requires_report": False,
            "clarification_required": False,
            "clarification_question": None,
            "reasoning_summary": "PFZ query detected via keyword fallback.",
        }

    # Weather-only query
    if is_weather and not is_trip:
        return {
            "intent": "weather_query",
            "required_capabilities": ["geo", "weather", "visualization"],
            "priority": "information",
            "requires_safety_assessment": False,
            "requires_route": False,
            "requires_visualization": True,
            "requires_report": False,
            "clarification_required": False,
            "clarification_question": None,
            "reasoning_summary": "Weather query detected via keyword fallback.",
        }

    # Alert/hazard query
    if is_alert and not is_trip:
        return {
            "intent": "alert_query",
            "required_capabilities": ["geo", "weather", "visualization"],
            "priority": "safety",
            "requires_safety_assessment": False,
            "requires_route": False,
            "requires_visualization": True,
            "requires_report": False,
            "clarification_required": False,
            "clarification_question": None,
            "reasoning_summary": "Alert/hazard query detected via keyword fallback.",
        }

    # Route optimization
    if is_route:
        return {
            "intent": "route_optimization",
            "required_capabilities": [
                "geo", "weather", "marine", "ocean_analytics",
                "route", "risk", "visualization", "reporting",
            ],
            "priority": "safety",
            "requires_safety_assessment": True,
            "requires_route": True,
            "requires_visualization": True,
            "requires_report": True,
            "clarification_required": False,
            "clarification_question": None,
            "reasoning_summary": "Route optimization detected via keyword fallback.",
        }

    # Generic knowledge (catch-all for "what is", "explain", etc.)
    if is_knowledge and not is_trip:
        return {
            "intent": "knowledge_question",
            "required_capabilities": ["knowledge"],
            "priority": "information",
            "requires_safety_assessment": False,
            "requires_route": False,
            "requires_visualization": False,
            "requires_report": False,
            "clarification_required": False,
            "clarification_question": None,
            "reasoning_summary": "Knowledge question detected via keyword fallback.",
        }

    # Default: trip assessment (safety-first)
    return {
        "intent": "trip_assessment",
        "required_capabilities": [
            "geo", "weather", "marine", "risk",
            "visualization", "reporting",
        ],
        "priority": "safety",
        "requires_safety_assessment": True,
        "requires_route": False,
        "requires_visualization": True,
        "requires_report": True,
        "clarification_required": False,
        "clarification_question": None,
        "reasoning_summary": "Default trip assessment plan (LLM unavailable).",
    }

