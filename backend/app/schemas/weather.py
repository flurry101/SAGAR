# attr: m1
# [weather observation and alert schemas]
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.provenance import Provenance


class WeatherObservation(BaseModel):
    # [waypoint weather forecast data]
    waypoint_index: Optional[int] = Field(default=None, description="index of waypoint")
    lat: float = Field(..., description="latitude")
    lon: float = Field(..., description="longitude")
    time_iso: str = Field(..., description="forecast valid timestamp")
    wave_height_m: Optional[float] = Field(default=None, description="significant wave height in meters")
    wind_speed_kmh: Optional[float] = Field(default=None, description="wind speed in km/h")
    wind_direction_deg: Optional[float] = Field(default=None, description="wind direction in degrees")
    swell_height_m: Optional[float] = Field(default=None, description="swell height in meters")
    swell_direction_deg: Optional[float] = Field(default=None, description="swell direction in degrees")
    visibility_km: Optional[float] = Field(default=None, description="visibility in kilometers")
    precipitation_mm: Optional[float] = Field(default=None, description="precipitation in mm")
    provenance: Optional[Provenance] = Field(default=None, description="data source provenance")


class Alert(BaseModel):
    # [environmental or safety alert]
    alert_type: str = Field(..., description="type e.g. HIGH_WAVE, EXTREME_WAVE, CYCLONE")
    severity: str = Field(default="WARNING", description="severity level: INFO, WARNING, SEVERE")
    message: str = Field(..., description="human readable alert description")
    source: str = Field(default="Open-Meteo", description="alert data source")
    timestamp: Optional[str] = Field(default=None, description="alert trigger timestamp")
    lat: Optional[float] = Field(default=None, description="latitude")
    lon: Optional[float] = Field(default=None, description="longitude")
    evidence_ids: List[str] = Field(default_factory=list, description="associated evidence identifiers")
# attr: m1

