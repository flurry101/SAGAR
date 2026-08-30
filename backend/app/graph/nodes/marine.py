"""
marine.py
=========
Thin Marine graph node (M4-owned). Calls marine_tools only — no routing,
no risk math, no LangGraph state schema ownership.
"""
from typing import Any, Dict, List

from backend.app.tools.marine_tools import (
    detect_hab,
    fetch_marine_forecast_batch,
    fetch_pfz,
    fetch_sst,
)

__all__ = [
    "marine_node",
    "fetch_pfz",
    "fetch_sst",
    "detect_hab",
    "fetch_marine_forecast_batch",
]


def marine_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch PFZ + per-waypoint marine observations for `state`.

    Expected keys (any may be omitted):
        origin: {lat, lon}
        pfz_radius_km
        trajectory.waypoints | waypoints
    """
    trajectory = state.get("trajectory") or {}
    waypoints: List[Dict[str, Any]] = (
        trajectory.get("waypoints") or state.get("waypoints") or []
    )
    updates: Dict[str, Any] = {}

    origin = state.get("origin")
    if origin and "lat" in origin and "lon" in origin:
        radius = float(state.get("pfz_radius_km") or 100.0)
        updates["pfz_data"] = fetch_pfz(origin, radius_km=radius)

    if waypoints:
        updates["marine_observations"] = fetch_marine_forecast_batch(waypoints)
    return updates
