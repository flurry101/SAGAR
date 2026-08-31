# attr: m1
# [marine observation and pfz schemas]
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.provenance import Provenance


class MarineObservation(BaseModel):
    # [oceanographic observations at waypoint]
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
    # [potential fishing zone advisory data]
    pfz_id: Optional[str] = Field(default=None, description="pfz identifier")
    lat: float = Field(..., description="zone center latitude")
    lon: float = Field(..., description="zone center longitude")
    validity_start: str = Field(..., description="validity start timestamp")
    validity_end: str = Field(..., description="validity end timestamp")
    species_advisory: Optional[str] = Field(default=None, description="recommended target species")
    source: str = Field(default="NOAA ERDDAP / Static", description="source identifier")
    provenance: Optional[Provenance] = Field(default=None, description="data source provenance")
# attr: m1

