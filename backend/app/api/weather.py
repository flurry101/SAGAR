"""
Weather & Hazard Micro-Endpoint API Router.
Direct access to Open-Meteo weather forecasts and GDACS hazard alerts.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from app.schemas.weather import WeatherBatchRequest, HazardQueryRequest, WeatherApiResponse
from app.tools.weather_tools import fetch_weather_forecast_batch, fetch_hazard_alerts

router = APIRouter()


@router.post("/weather/forecast", response_model=WeatherApiResponse, summary="Fetch weather forecast batch along waypoints")
async def get_weather_forecast(request: WeatherBatchRequest):
    """
    Retrieves hourly marine and atmospheric forecasts (wave, swell, wind, visibility)
    for a list of waypoints from Open-Meteo with static resilience fallback.
    """
    request_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        results = fetch_weather_forecast_batch(request.waypoints)
        return WeatherApiResponse(
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
            detail=f"Weather forecast query failed: {str(e)}",
        )


@router.post("/weather/hazards", response_model=WeatherApiResponse, summary="Fetch active cyclone and hazard alerts")
async def get_hazards(request: HazardQueryRequest):
    """
    Retrieves active tropical cyclone and extreme weather hazards from GDACS with static fallback.
    """
    request_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    time_window = None
    if request.time_window_start or request.time_window_end:
        time_window = (request.time_window_start, request.time_window_end)

    try:
        results = fetch_hazard_alerts(bbox=request.bbox, time_window=time_window)
        return WeatherApiResponse(
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
            detail=f"Hazard alerts query failed: {str(e)}",
        )
