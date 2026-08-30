"""
Planner Node — Intent Extraction & Advisory Synthesis

The Planner is the entry point and exit point of the ORCA workflow.
It is the ONLY component that communicates directly with the fisher.

Phase 1 (planner_intake):
    - Parse natural language into structured Trip Context
    - Check for required fields
    - Ask for missing critical information — never guess

Phase 2 (planner_synthesize):
    - Read Risk Evidence JSON
    - Generate human-readable advisory explanation
    - Translate to fisher's language if needed (via Bhashini)

Reference: 08_AI_ML_AGENTIC_ARCHITECTURE.md, Section 4
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.graph.state import OrcaState, AgentExecution


import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

def get_llm():
    """Helper to initialize the Gemini LLM."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=api_key, temperature=0.1)

def planner_intake(state: OrcaState) -> OrcaState:
    """Phase 1: Extract intent from the fisher's message and validate trip context."""
    execution = AgentExecution(
        id="",
        trip_id=state.get("trip_context", {}).get("trip_id", ""),
        agent_name="planner",
        status="running",
        started_at=datetime.now(timezone.utc).isoformat(),
        input_summary={"phase": "intake"},
        output_data={},
        data_sources=[],
        confidence=None,
        error=None,
    )

    history = state.get("conversation_history", [])
    trip = state.get("trip_context", {})
    vessel = state.get("vessel_profile", {})

    llm = get_llm()
    if llm and history:
        last_msg = history[-1].get("content", "")
        # Extract trip context via LLM
        prompt = f"""
        Extract the following trip details from the user's message.
        Return ONLY a JSON object with keys:
        - origin: str
        - destination_lat: float or null
        - destination_lon: float or null
        - departure_time_iso: str (ISO 8601 format) or null
        - language: str (ISO 639-1 code of the user's language, e.g., 'en', 'hi', 'kn', 'ta', 'mr', 'te', 'ml', 'gu', 'bn', 'or')
        
        Message: {last_msg}
        """
        try:
            resp = llm.invoke([SystemMessage(content="You are an extraction assistant."), HumanMessage(content=prompt)])
            extracted = json.loads(resp.content.strip().strip('```json').strip('```'))
            if extracted.get("origin"): trip["origin"] = extracted["origin"]
            if extracted.get("destination_lat"): trip["destination_lat"] = extracted["destination_lat"]
            if extracted.get("destination_lon"): trip["destination_lon"] = extracted["destination_lon"]
            if extracted.get("departure_time_iso"): trip["departure_time_iso"] = extracted["departure_time_iso"]
            if extracted.get("language"): trip["language"] = extracted["language"]
            state["trip_context"] = trip
        except Exception as e:
            execution["error"] = f"LLM extraction failed: {e}"

    required_trip = ["origin", "departure_time_iso"]
    missing = [f for f in required_trip if not trip.get(f)]
    if not vessel.get("beam_width_m"):
        missing.append("beam_width_m")

    if missing:
        state["workflow_status"] = "CLARIFICATION_REQUIRED"
        execution["status"] = "completed"
        execution["output_data"] = {"missing_fields": missing}
    else:
        state["workflow_status"] = "VALIDATED"
        execution["status"] = "completed"
        execution["output_data"] = {"validated": True}

    execution["completed_at"] = datetime.now(timezone.utc).isoformat()
    state.setdefault("agent_executions", []).append(execution)
    return state


def planner_synthesize(state: OrcaState) -> OrcaState:
    """Phase 2: Synthesize Risk Evidence into a human-readable advisory."""
    execution = AgentExecution(
        id="",
        trip_id=state.get("trip_context", {}).get("trip_id", ""),
        agent_name="planner",
        status="running",
        started_at=datetime.now(timezone.utc).isoformat(),
        input_summary={"phase": "synthesis"},
        output_data={},
        data_sources=[],
        confidence=None,
        error=None,
    )

    risk = state.get("risk_evidence", {})
    category = risk.get("advisory_category", "INSUFFICIENT_INFORMATION")
    overall_risk = state.get("overall_risk_level", "UNKNOWN")
    user_lang = state.get("trip_context", {}).get("language", "en")

    llm = get_llm()
    recommendation = f"Advisory based on {category}. Overall Risk: {overall_risk}."
    reason = "Deterministic safety rules fired."

    if llm:
        prompt = f"""
        Synthesize a safety advisory for fishermen based on this evidence.
        Category: {category}
        Risk Level: {overall_risk}
        Evidence summary: {risk.get('summary', '')}
        
        Provide a short recommendation text (max 2 sentences) and a reason (1 sentence).
        Output BOTH the recommendation and reason in this language code: '{user_lang}'.
        Return JSON with keys: 'recommendation_text', 'reason'.
        """
        try:
            resp = llm.invoke([SystemMessage(content="You are a marine safety synthesis assistant."), HumanMessage(content=prompt)])
            extracted = json.loads(resp.content.strip().strip('```json').strip('```'))
            recommendation = extracted.get("recommendation_text", recommendation)
            reason = extracted.get("reason", reason)
        except Exception as e:
            execution["error"] = f"LLM synthesis failed: {e}"

    state["advisory"] = {
        "advisory_category": category,
        "recommendation_text": recommendation,
        "reason": reason,
        "affected_phase": "",
        "affected_time": "",
        "affected_location": "",
        "vessel_context": "",
        "evidence_summary": risk.get('summary', ''),
        "uncertainty_notes": "",
        "disclaimer": "PathFinder provides decision support only. Follow official alerts.",
        "language": user_lang,
    }
    state["workflow_status"] = "ADVISORY_READY"

    execution["status"] = "completed"
    execution["completed_at"] = datetime.now(timezone.utc).isoformat()
    execution["output_data"] = {"advisory_category": category}

    state.setdefault("agent_executions", []).append(execution)
    return state
