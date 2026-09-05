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


from app.core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import json

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
        - destination_name: str or null (name of destination harbor or area)
        - destination_lat: float or null
        - destination_lon: float or null
        - departure_time_iso: str (ISO 8601 format) or null
        - language: str (ISO 639-1 code of the user's language)
        
        Message: {last_msg}
        """
        try:
            from app.core.llm_utils import extract_json
            resp = llm.invoke([SystemMessage(content="You are an extraction assistant."), HumanMessage(content=prompt)])
            extracted_text = resp.content.strip()
            if "```json" in extracted_text:
                extracted = json.loads(extracted_text.split("```json")[1].split("```")[0].strip())
            else:
                extracted = json.loads(extracted_text)
            
            if extracted.get("origin"): trip["origin"] = extracted["origin"]
            if extracted.get("destination_name"): trip["destination_name"] = extracted["destination_name"]
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
    state["agent_executions"] = [execution]
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
    trip = state.get("trip_context", {})
    
    # We want to respond conversationally to the original query
    resolved_query = state.get("resolved_query", "")

    recommendation = f"Advisory based on {category}. Overall Risk: {overall_risk}."
    reason = "Deterministic safety rules fired."

    try:
        from app.core.llm import get_llm
        from app.core.llm_utils import normalize_content, extract_json
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = get_llm()
        if llm:
            prompt = f"""You are ORCA, an intelligent conversational marine assistant.
The deterministic agents have finished their execution. Your job is to generate the final natural-language response to the user.

USER REQUEST: {resolved_query}
TRIP CONTEXT: {json.dumps(trip)}

DETERMINISTIC RESULTS (DO NOT INVENT OR CONTRADICT THESE):
- Risk Level: {overall_risk}
- Risk Category: {category}
- Evidence Summary: {risk.get('summary', '')}
- Weather: {len(state.get('weather_observations', []))} observations
- Marine: {len(state.get('marine_observations', []))} observations
- PFZ: {len(state.get('pfz_data', []))} zones

RULES:
1. Write a natural, ChatGPT-style response directly to the user addressing their request.
2. ALWAYS cite the Risk Level and Evidence Summary if safety was assessed. Do NOT calculate safety yourself; explain the deterministic results.
3. Be concise and professional.
4. Output BOTH the recommendation text and a brief reason.
5. Translate your response to the user's preferred language code: '{user_lang}'.

Return ONLY valid JSON with keys:
```json
{{
  "recommendation_text": "Your natural language response...",
  "reason": "Brief summary of the deterministic reason"
}}
```"""
            resp = llm.invoke([
                SystemMessage(content="You are the ORCA Marine Synthesis Assistant. Output only valid JSON."), 
                HumanMessage(content=prompt)
            ])
            raw_text = normalize_content(resp.content)
            extracted = extract_json(raw_text)
            
            recommendation = extracted.get("recommendation_text", recommendation)
            reason = extracted.get("reason", reason)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"LLM synthesis failed: {e}")
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

    if "agent_executions" not in state:
        state["agent_executions"] = []
    state["agent_executions"].append(execution)
    return state
