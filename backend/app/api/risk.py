"""
Deterministic Risk Engine API Router.
Direct evaluation endpoint for mathematical safety verification.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from app.risk_engine.schemas import RiskInput
from app.schemas.risk import RiskEvaluateApiResponse
from app.risk_engine.engine import RiskEngine

router = APIRouter()


@router.post("/risk/evaluate", response_model=RiskEvaluateApiResponse, summary="Evaluate voyage safety deterministically")
async def evaluate_risk(request: RiskInput):
    """
    Evaluates a voyage plan through the deterministic Risk Engine.
    Executes SVAS capsize checks, geofence violations, cyclone overrides, wind speed limits,
    bathymetry grounding, and tidal clearance rules.
    """
    request_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        engine = RiskEngine()
        evidence = engine.evaluate(request)
        return RiskEvaluateApiResponse(
            status="success",
            data=evidence.model_dump(),
            meta={
                "request_id": request_id,
                "timestamp": now_iso,
                "version": "v1",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk evaluation failed: {str(e)}",
        )
