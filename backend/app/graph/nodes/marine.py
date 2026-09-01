"""
marine.py
=========
Thin Marine graph node (M4-owned). Calls marine_tools only — no routing,
no risk math, no LangGraph state schema ownership.
"""
from typing import Any, Dict, List

from app.tools.bathymetry_tools import fetch_bathymetry
from app.tools.marine_tools import (
    detect_hab,
    fetch_marine_forecast_batch,
    fetch_pfz,
    fetch_sst,
)
from app.tools.tide_tools import fetch_tides

__all__ = [
    "marine_node",
    "fetch_pfz",
    "fetch_sst",
    "detect_hab",
    "fetch_marine_forecast_batch",
]


from datetime import datetime, timezone

def marine_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch PFZ + per-waypoint marine observations for `state`.
    Reads from trip_context and trajectory.
    """
    trajectory = state.get("trajectory") or {}
    waypoints: List[Dict[str, Any]] = state.get("waypoints") or trajectory.get("waypoints", [])
    
    trip_context = state.get("trip_context", {})
    origin = state.get("origin") or {}
    origin_lat = origin.get("lat") if origin.get("lat") is not None else trip_context.get("origin_lat")
    origin_lon = origin.get("lon") if origin.get("lon") is not None else trip_context.get("origin_lon")
    
    updates: Dict[str, Any] = {}

    if origin_lat is not None and origin_lon is not None:
        origin_coord = {"lat": origin_lat, "lon": origin_lon}
        radius = float(state.get("pfz_radius_km") or 100.0)
        updates["pfz_data"] = fetch_pfz(origin_coord, radius_km=radius)

    if waypoints:
        observations = fetch_marine_forecast_batch(waypoints)
        for item in observations:
            marine = item.get("marine", {})
            if marine.get("depth_m") is None:
                bathy = fetch_bathymetry(item["lat"], item["lon"])
                marine["depth_m"] = bathy.get("depth_m")
            if marine.get("tide_height_m") is None:
                tide = fetch_tides(item["lat"], item["lon"], item.get("time_iso"))
                marine["tide_height_m"] = tide.get("tide_height_m")
            item["marine"] = marine
        updates["marine_observations"] = observations

    # Log execution
    obs_count = len(updates.get("marine_observations", []))
    pfz_count = len(updates.get("pfz_data", {}).get("pfzs", []))
    updates["agent_executions"] = [{
        "agent_name": "marine",
        "status": "completed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": ["sst_adapter", "hab_adapter", "pfz_adapter"],
        "output_summary": f"Fetched {obs_count} marine observations and {pfz_count} PFZs."
    }]
    
    return updates
