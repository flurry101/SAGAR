"""
marine.py
=========
Thin Marine graph node (M4-owned). Calls marine_tools only — no routing,
no risk math, no LangGraph state schema ownership.
"""
import logging
from typing import Any, Dict, List

from app.tools.bathymetry_tools import fetch_bathymetry
from app.tools.marine_tools import (
    detect_hab,
    fetch_marine_forecast_batch,
    fetch_pfz,
    fetch_sst,
)
from app.tools.tide_tools import fetch_tides

logger = logging.getLogger(__name__)

__all__ = [
    "marine_node",
    "fetch_pfz",
    "fetch_sst",
    "detect_hab",
    "fetch_marine_forecast_batch",
]


from datetime import datetime, timezone
import time

def marine_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch PFZ + per-waypoint marine observations for `state`.
    Reads from trip_context and trajectory.
    """
    t0 = time.monotonic()
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

    t1 = time.monotonic()
    logger.info(f"[MARINE] PFZ fetch took {t1-t0:.2f}s")

    if waypoints:
        observations = fetch_marine_forecast_batch(waypoints)
        t2 = time.monotonic()
        logger.info(f"[MARINE] Batch SST/HAB fetch took {t2-t1:.2f}s for {len(waypoints)} waypoints")

        # Enrich with bathymetry + tides concurrently
        import concurrent.futures

        def enrich_observation(item):
            marine = item.get("marine", {})
            if marine.get("depth_m") is None:
                bathy = fetch_bathymetry(item["lat"], item["lon"])
                marine["depth_m"] = bathy.get("depth_m")
            if marine.get("tide_height_m") is None:
                tide = fetch_tides(item["lat"], item["lon"], item.get("time_iso"))
                marine["tide_height_m"] = tide.get("tide_height_m")
            item["marine"] = marine
            return item

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            observations = list(executor.map(enrich_observation, observations))

        t3 = time.monotonic()
        logger.info(f"[MARINE] Bathymetry+Tide enrichment took {t3-t2:.2f}s")

        updates["marine_observations"] = observations

    # Log execution
    obs_count = len(updates.get("marine_observations", []))
    pfz_count = len(updates.get("pfz_data", {}).get("pfzs", []))
    total = time.monotonic() - t0
    logger.info(f"[MARINE] Total marine_node took {total:.2f}s ({obs_count} obs, {pfz_count} PFZs)")
    updates["agent_executions"] = [{
        "agent_name": "marine",
        "status": "completed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": ["sst_adapter", "hab_adapter", "pfz_adapter"],
        "output_summary": f"Fetched {obs_count} marine observations and {pfz_count} PFZs in {total:.1f}s."
    }]
    
    return updates

