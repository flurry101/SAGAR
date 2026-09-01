"""
Marine & PFZ Micro-Endpoint API Router.
Direct access to Potential Fishing Zones (PFZ) and SST / HAB conditions.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Response, status
from app.schemas.marine import PFZQueryRequest, MarineBatchRequest, MarineApiResponse
from app.tools.marine_tools import fetch_pfz, fetch_marine_forecast_batch
from app.tools.ais_tools import get_nearby_vessels

router = APIRouter()


@router.get("/marine/traffic", summary="Get nearby AIS vessel traffic as GeoJSON")
async def get_marine_traffic(
    response: Response,
    lat: float,
    lon: float,
    radius_nm: float = 50.0,
):
    """Return Tier 1 AIS traffic when available, otherwise the local sample dataset."""
    if not -90.0 <= lat <= 90.0 or not -180.0 <= lon <= 180.0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid coordinates")
    if radius_nm <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="radius_nm must be positive")

    result = get_nearby_vessels(lat, lon, radius_nm)
    provenance = result["provenance"]
    response.headers["X-AIS-Source"] = provenance["source"]
    response.headers["X-AIS-Tier"] = str(provenance["tier"])
    return result["geojson"]


@router.post("/marine/pfz", response_model=MarineApiResponse, summary="Fetch Potential Fishing Zones near coordinate")
async def get_potential_fishing_zones(request: PFZQueryRequest):
    """
    Queries Potential Fishing Zones (PFZ) within a given radius using NOAA ERDDAP front detection
    with static GeoJSON fallback.
    """
    request_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        results = fetch_pfz(request.origin, radius_km=request.radius_km or 100.0)
        return MarineApiResponse(
            status="success",
            data=results,
            meta={
                "request_id": request_id,
                "timestamp": now_iso,
                "version": "v1",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PFZ query failed: {str(e)}",
        )


@router.post("/marine/observations", response_model=MarineApiResponse, summary="Fetch batch marine observations (SST, HAB)")
async def get_marine_observations(request: MarineBatchRequest):
    """
    Retrieves SST, chlorophyll, and HAB observations along a list of waypoints.
    """
    request_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        results = fetch_marine_forecast_batch(request.waypoints)
        return MarineApiResponse(
            status="success",
            data={"observations": results},
            meta={
                "request_id": request_id,
                "timestamp": now_iso,
                "version": "v1",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Marine observations query failed: {str(e)}",
        )
