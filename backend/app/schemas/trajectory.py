# attr: m1
# [trajectory and waypoint schemas]
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class Waypoint(BaseModel):
    # [single trajectory coordinate and eta]
    lat: float = Field(..., description="latitude in decimal degrees")
    lon: float = Field(..., description="longitude in decimal degrees")
    eta_iso: str = Field(..., description="estimated arrival timestamp in iso 8601 utc")
    phase: str = Field(
        default="outbound",
        description="trip phase: outbound, fishing, return",
    )


class GeofenceResult(BaseModel):
    # [restricted maritime zone intersection check]
    zone_name: str = Field(..., description="restricted zone identifier")
    zone_type: str = Field(default="MPA", description="zone classification e.g. MPA, naval")
    intersects: bool = Field(default=False, description="whether route intersects this zone")
    waypoint_indices: List[int] = Field(default_factory=list, description="indices of affected waypoints")
    is_critical: bool = Field(default=False, description="critical navigation hazard flag")


class Trajectory(BaseModel):
    # [full voyage route trajectory]
    route_id: Optional[str] = Field(default=None, description="unique route identifier")
    total_distance_km: Optional[float] = Field(default=None, description="total route distance in kilometers")
    waypoints: List[Waypoint] = Field(default_factory=list, description="ordered waypoints")
    geofence_intersections: List[GeofenceResult] = Field(
        default_factory=list,
        description="restricted zones intersected",
    )
# attr: m1

