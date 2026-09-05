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
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.graph.state import OrcaState, APPROVED_CAPABILITIES
from app.adapters.bhashini_adapter import BhashiniAdapter

logger = logging.getLogger(__name__)

_bhashini_adapter = BhashiniAdapter()


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
    intent = task_plan.get("intent", "")

    # If the intent is explicitly conversational or informational, bypass the keyword heuristic
    if intent in ["conversational", "informational", "knowledge_question", "marine_science_query"]:
        # Do not force a trip assessment on purely conversational/informational queries
        task_plan["requires_safety_assessment"] = False
        task_plan["requires_route"] = False
        task_plan["required_capabilities"] = list(caps)
        return task_plan

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

    trip = state.get("trip_context", {})
    vessel = state.get("vessel_profile", {})
    
    # Use the context-resolved query, falling back to original history if missing
    user_message = state.get("resolved_query", "").strip()
    if not user_message:
        history = state.get("conversation_history", [])
        if history:
            user_message = history[-1].get("content", "")

    input_lang = state.get("language", "en")
    if input_lang and input_lang != "en":
        try:
            from app.core.llm import get_llm
            from langchain_core.messages import SystemMessage, HumanMessage
            logger.info(f"Translating user message from {input_lang} to English using LLM")
            llm_translator = get_llm(temperature=0.1)
            prompt = f"Translate the following text to English. Return ONLY the translated English text, nothing else.\n\nText: {user_message}"
            resp = llm_translator.invoke([
                SystemMessage(content="You are a precise translator. Return ONLY the translated English text without quotes."),
                HumanMessage(content=prompt)
            ])
            user_message = resp.content.strip()
            logger.info(f"Translated user message: {user_message}")
        except Exception as e:
            logger.warning(f"Incoming translation failed: {e}")

    # Check for simple conversational greetings (fast path)
    greetings = ["hello", "hi", "hey", "thanks", "thank you", "good morning", "good evening", "what can you do"]
    msg_clean = user_message.lower().strip()
    if msg_clean in greetings or (len(msg_clean.split()) <= 4 and any(g == msg_clean for g in greetings)):
        task_plan = {
            "intent": "conversational",
            "required_capabilities": [],
            "priority": "information",
            "requires_safety_assessment": False,
            "requires_route": False,
            "requires_visualization": False,
            "requires_report": False,
            "clarification_required": False,
            "reasoning_summary": "Trivial greeting detected.",
        }
        state["task_plan"] = task_plan
        state["workflow_status"] = "TASK_PLANNED"
        
        execution["status"] = "completed"
        execution["completed_at"] = datetime.now(timezone.utc).isoformat()
        if "agent_executions" not in state:
            state["agent_executions"] = []
        state["agent_executions"].append(execution)
        return state

    from app.core.llm import get_llm
    from app.core.llm_utils import normalize_content, extract_json, parse_natural_time
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = get_llm()
    task_plan = None

    if llm:
        system_prompt = f"""You are the ORCA Supervisor Agent.
Your job is to analyze the user's natural language request and output a structured task plan.

AVAILABLE CAPABILITIES:
{json.dumps(APPROVED_CAPABILITIES)}

INTENT TIERS:
1. "conversational": Simple chat, greeting, thanks. (Capabilities: [])
2. "informational": General questions, or follow-up questions asking for reasons/explanations (e.g. "What is SST?", "Why is it dangerous?", "What is the reason I can't go to sea?"). (Capabilities: ["knowledge"])
3. "operational": Search or planning (e.g. "Find PFZ near Malpe"). (Capabilities: ["marine", "geo", "visualization"])
4. "safety_critical": Any new voyage, route, or safety assessment (e.g. "Is it safe to go fishing tomorrow?", "Plan a trip to X"). (Capabilities: ["geo", "weather", "marine", "risk", "visualization", "reporting"])

Respond ONLY with valid JSON in this exact schema:
```json
{{
  "intent": "conversational" | "informational" | "operational" | "safety_critical",
  "required_capabilities": ["list", "of", "capabilities"],
  "priority": "safety" | "information",
  "requires_safety_assessment": boolean,
  "requires_route": boolean,
  "requires_visualization": boolean,
  "requires_report": boolean,
  "clarification_required": boolean,
  "clarification_question": "string or null",
  "reasoning_summary": "string explaining capability selection",
  "extracted_origin": "string or null",
  "extracted_destination_name": "string (e.g. 'Gulf of Mannar', 'Malpe') or null",
  "extracted_departure_time": "string (e.g. '5 AM', 'tomorrow'). Assume IST timezone. or null",
  "extracted_return_time": "string (e.g. '1 PM', 'tomorrow 5pm'). Assume IST timezone. or null",
  "extracted_beam_width": number or null,
  "extracted_cruising_speed_kmh": number or null,
  "extracted_language": "en" | "hi" | "kn" | "ta" | "ml" | "or" | "gu" | "mr" | "te" | "bn"
}}
```"""
        try:
            resp = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ])
            raw_text = normalize_content(resp.content)
            parsed = extract_json(raw_text)

            task_plan = {
                "intent": parsed.get("intent", "safety_critical"),
                "required_capabilities": parsed.get("required_capabilities", []),
                "priority": parsed.get("priority", "safety"),
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
            if parsed.get("extracted_destination_name"):
                trip["destination_name"] = parsed["extracted_destination_name"]
            if parsed.get("extracted_departure_time"):
                trip["departure_time_iso"] = parse_natural_time(parsed["extracted_departure_time"])
            if parsed.get("extracted_return_time"):
                trip["return_time_iso"] = parse_natural_time(parsed["extracted_return_time"])
            if parsed.get("extracted_language"):
                trip["language"] = parsed["extracted_language"]
            if parsed.get("extracted_beam_width"):
                try:
                    vessel["beam_width_m"] = float(parsed["extracted_beam_width"])
                except (ValueError, TypeError):
                    pass
            if parsed.get("extracted_cruising_speed_kmh"):
                try:
                    vessel["cruising_speed_kmh"] = float(parsed["extracted_cruising_speed_kmh"])
                except (ValueError, TypeError):
                    pass
            
            logger.info(f"[LLM_EXTRACTION]\n{json.dumps(trip, indent=2)}")

        except Exception as e:
            execution["error"] = f"LLM parsing failed: {e}. Falling back to default plan."

    # If LLM failed, fallback to keyword extraction
    if not task_plan:
        task_plan = _default_task_plan(user_message)

    # --- Knowledge Guard ---
    # Force knowledge intent for explicit questions to prevent them from triggering the trip pipeline
    msg_clean_lower = user_message.lower().strip()
    knowledge_starters = ["what is", "what are", "what does", "explain", "why", "how", "tell me", "can you explain", "whta"]
    
    is_question = any(msg_clean_lower.startswith(kw) for kw in knowledge_starters)
    if "reason" in msg_clean_lower or "why" in msg_clean_lower or "explain" in msg_clean_lower:
        is_question = True

    if is_question:
        task_plan["intent"] = "informational"
        task_plan["required_capabilities"] = ["knowledge"]
        task_plan["requires_safety_assessment"] = False
        task_plan["requires_route"] = False
        task_plan["requires_visualization"] = False
        task_plan["requires_report"] = False

    # --- Enforce Safety Guard ---
    task_plan = enforce_safety_requirements(task_plan, user_message)

    # --- Resolve Dependencies ---
    from app.graph.routing import resolve_dependencies
    task_plan = resolve_dependencies(task_plan)

    # --- Check for clarification needs ---
    task_plan["clarification_required"] = False
    task_plan["clarification_question"] = None
    task_plan["missing_fields"] = []

    if task_plan.get("requires_safety_assessment"):
        required_trip = ["origin", "departure_time_iso"]
        missing = [f for f in required_trip if not trip.get(f)]

        # Apply sensible defaults for vessel params instead of blocking
        if not vessel.get("beam_width_m"):
            vessel["beam_width_m"] = 4.5  # Typical small fishing vessel
            logger.info("[SUPERVISOR] Applied default beam_width_m=4.5m")
        if not vessel.get("cruising_speed_kmh"):
            vessel["cruising_speed_kmh"] = 15.0  # ~8 knots
            logger.info("[SUPERVISOR] Applied default cruising_speed_kmh=15.0 km/h")

        if missing:
            friendly_names = {
                "origin": "origin port",
                "departure_time_iso": "departure time",
                "beam_width_m": "vessel beam width (meters)",
                "cruising_speed_kmh": "vessel cruising speed (km/h)"
            }
            friendly_missing = [friendly_names.get(m, m) for m in missing]
            
            task_plan["clarification_required"] = True
            question = (
                f"I need more information to assess safety. "
                f"Please provide: {', '.join(friendly_missing)}"
            )
            
            # Translate if needed
            lang = state.get("language", "en")
            if lang and lang != "en":
                translated = False
                if _bhashini_adapter.supports_language(lang) and _bhashini_adapter.is_configured:
                    res = _bhashini_adapter.translate(question, target_lang=lang)
                    if res.get("success"):
                        question = res.get("translated_text", question)
                        translated = True
                
                if not translated:
                    # Fallback to Gemini
                    try:
                        from app.core.llm import get_llm
                        from langchain_core.messages import SystemMessage, HumanMessage
                        llm = get_llm(temperature=0.1)
                        prompt = f"Translate the following text to language code '{lang}'. Return ONLY the translated text, no other formatting or explanations.\n\nText: {question}"
                        resp = llm.invoke([
                            SystemMessage(content="You are a precise translator."),
                            HumanMessage(content=prompt)
                        ])
                        question = resp.content.strip()
                    except Exception as e:
                        logger.warning(f"Fallback translation failed: {e}")
                        
            task_plan["clarification_question"] = question
            task_plan["missing_fields"] = [{"field": m, "reason": "Required for safety calculation"} for m in missing]

    # --- Update state ---
    state["task_plan"] = task_plan
    state["trip_context"] = trip
    state["vessel_profile"] = vessel
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
    # Ensure agent_executions list exists
    if "agent_executions" not in state:
        state["agent_executions"] = []
    state["agent_executions"].append(execution)

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

