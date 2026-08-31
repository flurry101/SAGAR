# attr: m1
# [assessment retrieval router]
from __future__ import annotations

import logging
import uuid
from fastapi import APIRouter, HTTPException, Request, status
from app.repositories.assessment_repo import get_assessment_by_id
from app.schemas.common import APIResponse, Meta
from app.schemas.assessment import AssessmentDetailResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/assessment/{assessment_id}", response_model=APIResponse[AssessmentDetailResponse])
def get_assessment(assessment_id: str, request: Request):
    # [retrieve persisted assessment by id]
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    record = get_assessment_by_id(assessment_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment with id '{assessment_id}' not found.",
        )

    response_data = AssessmentDetailResponse(**record)

    return APIResponse(
        status="success",
        data=response_data,
        meta=Meta(request_id=request_id),
    )
# attr: m1

