"""
Weather and Hazard Micro-Endpoint Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WeatherBatchRequest(BaseModel):
    waypoints: List[Dict[str, Any]] = Field(..., description="List of waypoints with lat, lon, and eta_iso")


class HazardQueryRequest(BaseModel):
    bbox: Optional[Dict[str, float]] = Field(None, description="Bounding box with lat_min, lat_max, lon_min, lon_max")
    time_window_start: Optional[str] = Field(None, description="Start timestamp in ISO format")
    time_window_end: Optional[str] = Field(None, description="End timestamp in ISO format")


class WeatherApiResponse(BaseModel):
    status: str = Field("success", description="Status")
    data: Dict[str, Any] = Field(default_factory=dict, description="Observations or hazards")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
