"""
Assessment Retrieval API Router.
Fetches persisted assessment records and related evidence items from Supabase.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.assessment import AssessmentDetailResponse
from app.core.supabase import get_supabase_client
from app.core.auth import get_current_user_optional
from app.models.user import User

router = APIRouter()


@router.get("/assessment/{assessment_id}", response_model=AssessmentDetailResponse, summary="Get assessment by ID")
async def get_assessment(
    assessment_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Retrieves stored assessment records including risk evaluation, advisories, weather/marine observations,
    and agent execution traces.
    """
    request_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    client = get_supabase_client()

    if not client:
        # Fallback when Supabase is not configured locally
        return AssessmentDetailResponse(
            status="success",
            data={
                "assessment_id": assessment_id,
                "note": "Supabase client not configured in current environment. Returning empty record.",
            },
            meta={
                "request_id": request_id,
                "timestamp": now_iso,
                "version": "v1",
            },
        )

    try:
        # Fetch top-level assessment
        res = client.table("assessments").select("*").eq("assessment_id", assessment_id).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment '{assessment_id}' not found.",
            )

        assessment = res.data[0]

        # Fetch related tables
        risk_res = client.table("risk_evidence").select("*").eq("assessment_id", assessment_id).execute()
        adv_res = client.table("advisories").select("*").eq("assessment_id", assessment_id).execute()
        weather_res = client.table("weather_evidence").select("*").eq("assessment_id", assessment_id).execute()
        marine_res = client.table("marine_evidence").select("*").eq("assessment_id", assessment_id).execute()
        exec_res = client.table("agent_executions").select("*").eq("assessment_id", assessment_id).execute()
        report_res = client.table("reports").select("*").eq("assessment_id", assessment_id).execute()

        data_payload = {
            "assessment": assessment,
            "risk_evidence": risk_res.data,
            "advisories": adv_res.data,
            "weather_evidence": weather_res.data,
            "marine_evidence": marine_res.data,
            "agent_executions": exec_res.data,
            "reports": report_res.data,
        }

        return AssessmentDetailResponse(
            status="success",
            data=data_payload,
            meta={
                "request_id": request_id,
                "timestamp": now_iso,
                "version": "v1",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        # If the remote table or record doesn't exist, return 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment '{assessment_id}' not found: {str(e)}",
        )
