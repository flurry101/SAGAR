"""
Trip Planning and Assessment API Router.
Wires FastAPI HTTP requests directly to the compiled LangGraph supervisor pipeline.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.schemas.trip import TripAssessRequest, TripAssessResponse, TripContinueRequest, ChatRequest
from app.graph.builder import get_compiled_graph
from app.core.auth import get_current_user_optional
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


def get_graph():
    return get_compiled_graph()


@router.post("/trip/assess", response_model=TripAssessResponse, summary="Assess fishing trip safety and route")
@router.post("/chat", response_model=TripAssessResponse, summary="Chat interface with LangGraph Trip Planner")
async def assess_trip(
    request_data: TripAssessRequest,
    req: Request = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    graph=Depends(get_graph),
):
    """
    Submits a natural-language or structured trip planning query to the ORCA LangGraph pipeline.
    Runs Supervisor -> Geo -> Marine/Weather -> Risk -> Post-Process -> Advisory Synthesis -> Persistence.
    """
    session_id = request_data.session_id or str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    # Build initial conversation
    initial_conversation = list(request_data.conversation_history or [])
    initial_conversation.append({"role": "user", "content": request_data.message})

    language = request_data.language or (current_user.preferred_language if current_user and hasattr(current_user, "preferred_language") else "en")
    fisher_id = request_data.fisher_id or (str(current_user.id) if current_user and hasattr(current_user, "id") else None)

    trip_ctx = {
        "trip_id": session_id,
        "fisher_id": fisher_id or "anonymous",
        "language": language,
    }
    if request_data.origin:
        trip_ctx["origin"] = request_data.origin
    if request_data.departure_time:
        trip_ctx["departure_time_iso"] = request_data.departure_time

    vessel_profile = {}
    v_input = request_data.vessel or request_data.vessel_profile
    if v_input:
        if hasattr(v_input, "model_dump"):
            vessel_profile = v_input.model_dump(exclude_none=True)
        elif isinstance(v_input, dict):
            vessel_profile = v_input
    elif current_user and getattr(current_user, "vessel_id", None):
        vessel_profile = {"vessel_id": current_user.vessel_id, "beam_width_m": 4.5}

    state_input = {
        "conversation_history": initial_conversation,
        "trip_context": trip_ctx,
        "vessel_profile": vessel_profile,
        "workflow_status": "RECEIVED",
        "language": language,
    }

    try:
        config = {"configurable": {"thread_id": session_id}}
        result = await graph.ainvoke(state_input, config=config)

        status_type = "success"
        workflow_status = result.get("workflow_status", "COMPLETED")
        if workflow_status == "CLARIFICATION_REQUIRED":
            status_type = "needs_clarification"
        elif workflow_status == "INSUFFICIENT_INFORMATION":
            status_type = "insufficient_information"

        data_payload = {
            "session_id": session_id,
            "trip_id": result.get("trip_context", {}).get("trip_id") or session_id,
            "workflow_status": workflow_status,
            "overall_risk_level": result.get("overall_risk_level", "UNKNOWN"),
            "task_plan": result.get("task_plan"),
            "trip_context": result.get("trip_context"),
            "vessel_profile": result.get("vessel_profile"),
            "trajectory": result.get("trajectory"),
            "weather_observations": result.get("weather_observations", []),
            "marine_observations": result.get("marine_observations", []),
            "pfz_data": result.get("pfz_data"),
            "risk_evidence": result.get("risk_evidence"),
            "advisory": result.get("advisory"),
            "alerts": result.get("alerts", []),
            "route_candidates": result.get("route_candidates", []),
            "ocean_analysis": result.get("ocean_analysis"),
            "visualization_spec": result.get("visualization_spec"),
            "report": result.get("report"),
            "evidence_registry": result.get("evidence_registry", []),
            "persistence_status": result.get("persistence_status", "skipped"),
            "agent_executions": result.get("agent_executions", []),
            "errors": result.get("errors", []),
        }

        return TripAssessResponse(
            status=status_type,
            data=data_payload,
            meta={
                "request_id": request_id,
                "timestamp": now_iso,
                "version": "v1",
            },
        )

    except Exception as e:
        logger.error(f"Trip assessment failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangGraph execution error: {str(e)}",
        )


@router.post("/trip/continue", response_model=TripAssessResponse, summary="Continue conversational clarification loop")
async def continue_trip(
    payload: TripContinueRequest,
    graph=Depends(get_graph),
):
    """
    Continues a multi-turn trip assessment conversation for clarification.
    """
    request_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    update_state: Dict[str, Any] = {
        "conversation_history": [{"role": "user", "content": payload.message}],
        "language": payload.language or "en",
    }

    try:
        config = {"configurable": {"thread_id": payload.session_id}}
        result_state = await graph.ainvoke(update_state, config=config)

        workflow_status = result_state.get("workflow_status", "COMPLETED")
        status_type = "needs_clarification" if workflow_status == "CLARIFICATION_REQUIRED" else "success"

        data_payload = {
            "session_id": payload.session_id,
            "trip_id": result_state.get("trip_context", {}).get("trip_id") or payload.session_id,
            "workflow_status": workflow_status,
            "overall_risk_level": result_state.get("overall_risk_level", "UNKNOWN"),
            "task_plan": result_state.get("task_plan"),
            "trip_context": result_state.get("trip_context"),
            "vessel_profile": result_state.get("vessel_profile"),
            "trajectory": result_state.get("trajectory"),
            "risk_evidence": result_state.get("risk_evidence"),
            "advisory": result_state.get("advisory"),
            "alerts": result_state.get("alerts", []),
            "visualization_spec": result_state.get("visualization_spec"),
            "report": result_state.get("report"),
            "persistence_status": result_state.get("persistence_status", "skipped"),
            "errors": result_state.get("errors", []),
        }

        return TripAssessResponse(
            status=status_type,
            data=data_payload,
            meta={
                "request_id": request_id,
                "timestamp": now_iso,
                "version": "v1",
            },
        )
    except Exception as e:
        logger.error(f"Trip continue failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangGraph execution error: {str(e)}",
        )
