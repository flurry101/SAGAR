"""GIS schemas for Trajectory and Waypoint models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class LegLabel(str, Enum):
    OUTBOUND = "outbound"
    FISHING = "fishing"
    RETURN = "return"


class Waypoint(BaseModel):
    """Represents a single spatio-temporal point along a vessel trajectory."""

    lat: float = Field(..., description="Latitude in decimal degrees (-90.0 to 90.0)", ge=-90.0, le=90.0)
    lon: float = Field(..., description="Longitude in decimal degrees (-180.0 to 180.0)", ge=-180.0, le=180.0)
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp string (e.g. '2026-08-29T10:00:00Z')")
    leg_label: LegLabel = Field(..., description="Leg segment label: outbound, fishing, or return")


class Trajectory(BaseModel):
    """Complete vessel voyage trajectory composed of ordered waypoints across legs."""

    waypoints: List[Waypoint] = Field(default_factory=list, description="Ordered list of waypoints")
    total_distance_nm: float = Field(..., description="Total trajectory distance in nautical miles (nm)", ge=0.0)
    total_duration_hours: float = Field(..., description="Total voyage duration in hours", ge=0.0)
    origin_name: Optional[str] = Field(None, description="Origin port or location name")
    destination_name: Optional[str] = Field(None, description="Destination port or location name")
    departure_time: str = Field(..., description="Departure ISO 8601 UTC timestamp string")
