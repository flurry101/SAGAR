# attr: m1
# [vessel profile management router]
from __future__ import annotations

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.core.auth import get_current_user_optional
from app.repositories.vessel_repo import get_vessel_by_id, upsert_vessel
from app.schemas.common import APIResponse, Meta
from app.schemas.vessel import VesselProfile, VesselCreate, VesselUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/vessel/{vessel_id}", response_model=APIResponse[VesselProfile])
def get_vessel_profile(vessel_id: str, request: Request):
    # [retrieve vessel profile by id]
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    record = get_vessel_by_id(vessel_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vessel with id '{vessel_id}' not found.",
        )

    profile = VesselProfile(
        vessel_id=record.get("id") or record.get("vessel_id"),
        vessel_type=record.get("vessel_type", "mechanized_trawler"),
        beam_width_m=float(record.get("beam_width_m", 4.0)),
        length_m=float(record.get("length_m")) if record.get("length_m") is not None else None,
        cruising_speed_kmh=float(record.get("cruising_speed_kmh", 15.0)),
        has_ais=bool(record.get("has_ais", False)),
    )

    return APIResponse(
        status="success",
        data=profile,
        meta=Meta(request_id=request_id),
    )


@router.post("/vessel", response_model=APIResponse[VesselProfile], status_code=status.HTTP_201_CREATED)
def create_vessel_profile(
    payload: VesselCreate,
    request: Request,
    user=Depends(get_current_user_optional),
):
    # [register a new vessel profile]
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    fisher_id = str(user.user_id) if user and hasattr(user, "user_id") else None

    vessel_id = str(uuid.uuid4())
    data_dict = payload.model_dump()
    data_dict["vessel_id"] = vessel_id

    saved = upsert_vessel(fisher_id=fisher_id, vessel_data=data_dict)

    profile = VesselProfile(
        vessel_id=saved.get("id") or saved.get("vessel_id", vessel_id),
        vessel_type=saved.get("vessel_type", payload.vessel_type),
        beam_width_m=float(saved.get("beam_width_m", payload.beam_width_m)),
        length_m=float(saved.get("length_m")) if saved.get("length_m") is not None else payload.length_m,
        cruising_speed_kmh=float(saved.get("cruising_speed_kmh", payload.cruising_speed_kmh)),
        has_ais=bool(saved.get("has_ais", payload.has_ais)),
    )

    return APIResponse(
        status="success",
        data=profile,
        meta=Meta(request_id=request_id),
    )


@router.put("/vessel/{vessel_id}", response_model=APIResponse[VesselProfile])
def update_vessel_profile(
    vessel_id: str,
    payload: VesselUpdate,
    request: Request,
    user=Depends(get_current_user_optional),
):
    # [update existing vessel profile]
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    fisher_id = str(user.user_id) if user and hasattr(user, "user_id") else None

    existing = get_vessel_by_id(vessel_id) or {}
    update_data = payload.model_dump(exclude_unset=True)
    merged = {**existing, **update_data, "vessel_id": vessel_id}

    saved = upsert_vessel(fisher_id=fisher_id, vessel_data=merged)

    profile = VesselProfile(
        vessel_id=saved.get("id") or saved.get("vessel_id", vessel_id),
        vessel_type=saved.get("vessel_type", "mechanized_trawler"),
        beam_width_m=float(saved.get("beam_width_m", 4.0)),
        length_m=float(saved.get("length_m")) if saved.get("length_m") is not None else None,
        cruising_speed_kmh=float(saved.get("cruising_speed_kmh", 15.0)),
        has_ais=bool(saved.get("has_ais", False)),
    )

    return APIResponse(
        status="success",
        data=profile,
        meta=Meta(request_id=request_id),
    )
# attr: m1

