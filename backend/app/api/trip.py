# attr: m1
# [trip planning operations router]
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, Request
from app.api.chat import get_graph
from app.core.auth import get_current_user_optional
from app.schemas.common import APIResponse, Meta
from app.schemas.trip import TripAssessRequest, TripContinueRequest, TripResponseData

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/trip/assess", response_model=APIResponse[TripResponseData])
async def assess_trip(
    payload: TripAssessRequest,
    request: Request,
    user=Depends(get_current_user_optional),
    graph=Depends(get_graph),
):
    # [submit trip assessment request initiating full workflow]
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    session_id = payload.session_id or str(uuid.uuid4())
    fisher_id = payload.fisher_id or (str(user.user_id) if user and hasattr(user, "user_id") else None)
    language = payload.language or (user.preferred_language if user and hasattr(user, "preferred_language") else "en")

    initial_state: Dict[str, Any] = {
        "conversation_history": [{"role": "user", "content": payload.message}],
        "trip_context": {
            "fisher_id": fisher_id or "anonymous",
            "language": language,
        },
        "language": language,
    }

    if payload.vessel_profile:
        initial_state["vessel_profile"] = payload.vessel_profile.model_dump()

    config = {"configurable": {"thread_id": session_id}}
    result_state = await graph.ainvoke(initial_state, config=config)

    workflow_status = result_state.get("workflow_status", "COMPLETED")
    status = "needs_clarification" if workflow_status == "CLARIFICATION_REQUIRED" else "success"

    response_data = TripResponseData(
        session_id=session_id,
        trip_id=result_state.get("trip_context", {}).get("trip_id"),
        workflow_status=workflow_status,
        task_plan=result_state.get("task_plan"),
        trip_context=result_state.get("trip_context"),
        vessel_profile=result_state.get("vessel_profile"),
        trajectory=result_state.get("trajectory") if isinstance(result_state.get("trajectory"), dict) else None,
        weather_observations=result_state.get("weather_observations"),
        marine_observations=result_state.get("marine_observations"),
        pfz_data=result_state.get("pfz_data"),
        alerts=result_state.get("alerts"),
        risk_evidence=result_state.get("risk_evidence"),
        overall_risk_level=result_state.get("overall_risk_level"),
        advisory=result_state.get("advisory"),
        visualization_spec=result_state.get("visualization_spec"),
        report=result_state.get("report"),
        persistence_status=result_state.get("persistence_status"),
        errors=result_state.get("errors"),
    )

    return APIResponse(
        status=status,
        data=response_data,
        meta=Meta(request_id=request_id),
    )


@router.post("/trip/continue", response_model=APIResponse[TripResponseData])
async def continue_trip(
    payload: TripContinueRequest,
    request: Request,
    graph=Depends(get_graph),
):
    # [continue conversational clarification loop]
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    update_state: Dict[str, Any] = {
        "conversation_history": [{"role": "user", "content": payload.message}],
        "language": payload.language or "en",
    }

    config = {"configurable": {"thread_id": payload.session_id}}
    result_state = await graph.ainvoke(update_state, config=config)

    workflow_status = result_state.get("workflow_status", "COMPLETED")
    status = "needs_clarification" if workflow_status == "CLARIFICATION_REQUIRED" else "success"

    response_data = TripResponseData(
        session_id=payload.session_id,
        trip_id=result_state.get("trip_context", {}).get("trip_id"),
        workflow_status=workflow_status,
        task_plan=result_state.get("task_plan"),
        trip_context=result_state.get("trip_context"),
        vessel_profile=result_state.get("vessel_profile"),
        trajectory=result_state.get("trajectory") if isinstance(result_state.get("trajectory"), dict) else None,
        weather_observations=result_state.get("weather_observations"),
        marine_observations=result_state.get("marine_observations"),
        pfz_data=result_state.get("pfz_data"),
        alerts=result_state.get("alerts"),
        risk_evidence=result_state.get("risk_evidence"),
        overall_risk_level=result_state.get("overall_risk_level"),
        advisory=result_state.get("advisory"),
        visualization_spec=result_state.get("visualization_spec"),
        report=result_state.get("report"),
        persistence_status=result_state.get("persistence_status"),
        errors=result_state.get("errors"),
    )

    return APIResponse(
        status=status,
        data=response_data,
        meta=Meta(request_id=request_id),
    )
# attr: m1

