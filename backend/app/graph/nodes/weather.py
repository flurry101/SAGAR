"""
weather.py
==========
Thin Weather graph node (M4-owned). Calls weather_tools only — no routing,
no risk math, no LangGraph state schema ownership.
"""
from typing import Any, Dict, List, Optional

from backend.app.tools.weather_tools import (
    fetch_hazard_alerts,
    fetch_swell_forecast,
    fetch_wave_forecast,
    fetch_weather_forecast_batch,
    fetch_wind_forecast,
)

# Re-export tool callables so Member 2 can bind them from this module if needed.
__all__ = [
    "weather_node",
    "fetch_wave_forecast",
    "fetch_wind_forecast",
    "fetch_swell_forecast",
    "fetch_hazard_alerts",
    "fetch_weather_forecast_batch",
]


def weather_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch weather (and optional hazards) for trajectory waypoints in `state`.

    Expected keys (any may be omitted):
        trajectory.waypoints | waypoints
        bbox, time_window  — for fetch_hazard_alerts
    """
    trajectory = state.get("trajectory") or {}
    waypoints: List[Dict[str, Any]] = (
        trajectory.get("waypoints") or state.get("waypoints") or []
    )
    updates: Dict[str, Any] = {}
    if waypoints:
        updates["weather_observations"] = fetch_weather_forecast_batch(waypoints)

    bbox = state.get("bbox")
    if bbox:
        time_window: Optional[Dict[str, Optional[str]]] = state.get("time_window")
        updates["hazard_alerts"] = fetch_hazard_alerts(bbox, time_window)
    return updates
