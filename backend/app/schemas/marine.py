"""
Marine and PFZ Micro-Endpoint Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PFZQueryRequest(BaseModel):
    origin: Dict[str, float] = Field(..., description="Origin coordinate with lat and lon")
    radius_km: Optional[float] = Field(100.0, ge=1.0, le=500.0, description="Search radius in km")


class MarineBatchRequest(BaseModel):
    waypoints: List[Dict[str, Any]] = Field(..., description="List of waypoints with lat, lon, and eta_iso")


class MarineApiResponse(BaseModel):
    status: str = Field("success", description="Status")
    data: Dict[str, Any] = Field(default_factory=dict, description="PFZ or marine observations")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
