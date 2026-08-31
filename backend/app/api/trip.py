"""
Trip Planning and Assessment API Router.
Wires FastAPI HTTP requests directly to the compiled LangGraph supervisor pipeline.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.trip import TripAssessRequest, TripAssessResponse
from app.graph.builder import get_compiled_graph
from app.core.auth import get_current_user_optional
from app.models.user import User

router = APIRouter()


@router.post("/trip/assess", response_model=TripAssessResponse, summary="Assess fishing trip safety and route")
@router.post("/chat", response_model=TripAssessResponse, summary="Chat interface with LangGraph Trip Planner")
async def assess_trip(
    request: TripAssessRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Submits a natural-language or structured trip planning query to the ORCA LangGraph pipeline.
    Runs Supervisor -> Geo -> Marine/Weather -> Risk -> Post-Process -> Advisory Synthesis -> Persistence.
    """
    session_id = request.session_id or str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    # Build initial OrcaState from request
    initial_conversation = list(request.conversation_history or [])
    initial_conversation.append({"role": "user", "content": request.message})

    trip_ctx = {
        "trip_id": session_id,
        "language": request.language or (current_user.preferred_language if current_user else "en"),
    }
    if request.origin:
        trip_ctx["origin"] = request.origin
    if request.departure_time:
        trip_ctx["departure_time_iso"] = request.departure_time

    vessel_profile = {}
    if request.vessel:
        vessel_profile = request.vessel.model_dump(exclude_none=True)
    elif current_user and current_user.vessel_id:
        vessel_profile = {"vessel_id": current_user.vessel_id, "beam_width_m": 4.5}

    state_input = {
        "conversation_history": initial_conversation,
        "trip_context": trip_ctx,
        "vessel_profile": vessel_profile,
        "workflow_status": "RECEIVED",
    }

    try:
        graph = get_compiled_graph()
        result = await graph.ainvoke(
            state_input,
            config={"configurable": {"thread_id": session_id}},
        )

        status_type = "success"
        workflow_status = result.get("workflow_status", "COMPLETED")
        if workflow_status == "CLARIFICATION_REQUIRED":
            status_type = "needs_clarification"
        elif workflow_status == "INSUFFICIENT_INFORMATION":
            status_type = "insufficient_information"

        data_payload = {
            "session_id": session_id,
            "workflow_status": workflow_status,
            "overall_risk_level": result.get("overall_risk_level", "UNKNOWN"),
            "task_plan": result.get("task_plan"),
            "trip_context": result.get("trip_context"),
            "trajectory": result.get("trajectory"),
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangGraph execution error: {str(e)}",
        )
