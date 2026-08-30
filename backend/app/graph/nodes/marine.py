"""
marine.py
=========
Thin Marine graph node (M4-owned). Calls marine_tools only — no routing,
no risk math, no LangGraph state schema ownership.
"""
from typing import Any, Dict, List

from app.tools.marine_tools import (
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


from datetime import datetime, timezone

def marine_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch PFZ + per-waypoint marine observations for `state`.
    Reads from trip_context and trajectory.
    """
    trajectory = state.get("trajectory") or {}
    waypoints: List[Dict[str, Any]] = trajectory.get("waypoints", [])
    
    trip_context = state.get("trip_context", {})
    origin_lat = trip_context.get("origin_lat")
    origin_lon = trip_context.get("origin_lon")
    
    updates: Dict[str, Any] = {}

    if origin_lat is not None and origin_lon is not None:
        origin = {"lat": origin_lat, "lon": origin_lon}
        radius = float(state.get("pfz_radius_km") or 100.0)
        updates["pfz_data"] = fetch_pfz(origin, radius_km=radius)

    if waypoints:
        updates["marine_observations"] = fetch_marine_forecast_batch(waypoints)
        
    # Log execution
    obs_count = len(updates.get("marine_observations", []))
    pfz_count = len(updates.get("pfz_data", {}).get("pfzs", []))
    updates.setdefault("agent_executions", []).append({
        "agent_name": "marine",
        "status": "completed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": ["sst_adapter", "hab_adapter", "pfz_adapter"],
        "output_summary": f"Fetched {obs_count} marine observations and {pfz_count} PFZs."
    })
    
    return updates
