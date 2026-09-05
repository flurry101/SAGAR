import json
import logging
from app.graph.state import OrcaState

logger = logging.getLogger(__name__)

# Keywords that suggest the user is referencing previous context
_CONTEXT_DEPENDENT_PATTERNS = [
    "what about", "how about", "and tomorrow", "instead", "compare",
    "the other", "safer", "why", "show me", "what if", "yesterday",
    "the same", "that route", "this area", "last time", "again",
    "more detail", "explain", "elaborate",
]


def _needs_llm_resolution(query: str, history: list, trip: dict) -> bool:
    """
    Determine if we actually need to call the LLM to resolve context.
    Returns False (skip LLM) for:
      - First message in a session (only 1 entry in history)
      - Messages that are clearly self-contained (contain location names, full sentences)
    Returns True (call LLM) for:
      - Follow-up questions that reference previous context
      - Short ambiguous messages with prior history
    """
    # If there's only the current message (or none), no prior context to resolve
    if len(history) <= 1:
        return False

    query_lower = query.lower().strip()

    # Very short messages with history almost certainly need resolution
    if len(query_lower.split()) <= 4 and len(history) > 1:
        return True

    # Check for context-dependent phrases
    for pattern in _CONTEXT_DEPENDENT_PATTERNS:
        if pattern in query_lower:
            return True

    return False


def resolve_context(state: OrcaState) -> dict:
    """
    Fast context resolver. Only calls the LLM when the user's message
    genuinely depends on prior conversation context.
    For first messages and self-contained queries, it passes through instantly.
    """
    history = state.get("conversation_history", [])
    original_query = history[-1].get("content", "").strip() if history else ""

    trip = state.get("trip_context", {})

    # FAST PATH: Skip LLM if not needed
    if not _needs_llm_resolution(original_query, history, trip):
        logger.info("Context Resolver: FAST PATH — no prior context to resolve.")
        return {
            "original_query": original_query,
            "resolved_query": original_query,
        }

    # SLOW PATH: Only for genuine follow-ups that need context resolution
    logger.info("Context Resolver: SLOW PATH — resolving follow-up context via LLM.")
    try:
        from app.core.llm import get_llm
        from app.core.llm_utils import normalize_content, extract_json, parse_natural_time
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = get_llm(temperature=0.1)
        if not llm:
            return {"original_query": original_query, "resolved_query": original_query}

        # Only send last 6 messages to save tokens
        recent_history = history[-6:] if len(history) > 6 else history

        prompt = f"""Rewrite the user's latest message into a structured query using prior context.

ACTIVE TRIP: {json.dumps(trip)}
RECENT CONVERSATION: {json.dumps(recent_history)}
CURRENT MESSAGE: {original_query}

RULES:
1. If it references prior context ("What about tomorrow?", "Why?", "Is the other route safer?"), rewrite it explicitly.
2. Maintain the active trip context where applicable.
3. DO NOT invent data. If required context is genuinely missing and the query is ambiguous, output needs_clarification=true.
4. If the message is self-contained (e.g. "Hello" or "What is SST?"), pass it through as the resolved_query.

Respond ONLY with a JSON object in the following format:
```json
{{
  "needs_clarification": boolean,
  "resolved_query": "The rewritten explicit query string",
  "updated_trip_context": {{
    "origin": "string or null",
    "destination_name": "string or null",
    "departure_time": "string (e.g. 5 AM, tomorrow) or null",
    "return_time": "string (e.g. 1 PM, tomorrow) or null"
  }}
}}
```"""

        resp = llm.invoke([
            SystemMessage(content="You are a conversational context resolver. Output only valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        raw_text = normalize_content(resp.content)
        parsed = extract_json(raw_text)

        if parsed.get("needs_clarification"):
            return {
                "original_query": original_query,
                "resolved_query": original_query,
                "workflow_status": "CLARIFICATION_REQUIRED",
            }
        
        # Merge updated trip context
        updated_trip = dict(trip)
        if parsed.get("updated_trip_context"):
            ctx = parsed["updated_trip_context"]
            if ctx.get("origin"):
                updated_trip["origin"] = ctx["origin"]
            if ctx.get("destination_name"):
                updated_trip["destination_name"] = ctx["destination_name"]
            if ctx.get("departure_time"):
                updated_trip["departure_time_iso"] = parse_natural_time(ctx["departure_time"])
            if ctx.get("return_time"):
                updated_trip["return_time_iso"] = parse_natural_time(ctx["return_time"])
        
        logger.info(f"[CONTEXT_RESOLUTION] Trip Context Updated:\n{json.dumps(updated_trip, indent=2)}")

        return {
            "original_query": original_query,
            "resolved_query": parsed.get("resolved_query", original_query),
            "trip_context": updated_trip,
        }

    except Exception as e:
        logger.warning(f"Context resolution failed: {e}. Passing through original.")
        return {
            "original_query": original_query,
            "resolved_query": original_query,
        }
