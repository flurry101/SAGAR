"""
Marine Observation and PFZ Schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.provenance import Provenance


class MarineObservation(BaseModel):
    waypoint_index: Optional[int] = Field(default=None, description="index of waypoint")
    lat: float = Field(..., description="latitude")
    lon: float = Field(..., description="longitude")
    time_iso: str = Field(..., description="observation timestamp")
    sst_celsius: Optional[float] = Field(default=None, description="sea surface temperature in celsius")
    chlorophyll_mg_m3: Optional[float] = Field(default=None, description="chlorophyll concentration")
    current_speed_ms: Optional[float] = Field(default=None, description="ocean current speed in m/s")
    current_direction_deg: Optional[float] = Field(default=None, description="ocean current direction in deg")
    hab_detected: Optional[bool] = Field(default=None, description="harmful algal bloom detection flag")
    provenance: Optional[Provenance] = Field(default=None, description="data source provenance")


class PFZData(BaseModel):
    pfz_id: Optional[str] = Field(default=None, description="pfz identifier")
    lat: float = Field(..., description="zone center latitude")
    lon: float = Field(..., description="zone center longitude")
    validity_start: str = Field(..., description="validity start timestamp")
    validity_end: str = Field(..., description="validity end timestamp")
    species_advisory: Optional[str] = Field(default=None, description="recommended target species")
    source: str = Field(default="NOAA ERDDAP / Static", description="source identifier")
    provenance: Optional[Provenance] = Field(default=None, description="data source provenance")


class PFZQueryRequest(BaseModel):
    origin: Dict[str, float] = Field(..., description="Origin coordinate with lat and lon")
    radius_km: Optional[float] = Field(100.0, ge=1.0, le=500.0, description="Search radius in km")


class MarineBatchRequest(BaseModel):
    waypoints: List[Dict[str, Any]] = Field(..., description="List of waypoints with lat, lon, and eta_iso")


class MarineApiResponse(BaseModel):
    status: str = Field("success", description="Status")
    data: Dict[str, Any] = Field(default_factory=dict, description="PFZ or marine observations")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
