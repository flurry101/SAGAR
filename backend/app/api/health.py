import uuid
from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.common import APIResponse, Meta

router = APIRouter()

@router.get("/health", response_model=APIResponse[dict])
def health_check():
    return APIResponse(
        status="success",
        data={"status": "healthy"},
        meta=Meta(request_id=str(uuid.uuid4()), timestamp=datetime.now(timezone.utc).isoformat(), version="v1")
    )

@router.get("/ready", response_model=APIResponse[dict])
def ready_check():
    return APIResponse(
        status="success",
        data={"status": "ready"},
        meta=Meta(request_id=str(uuid.uuid4()), timestamp=datetime.now(timezone.utc).isoformat(), version="v1")
    )