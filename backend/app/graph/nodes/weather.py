"""
weather.py
==========
Thin Weather graph node (M4-owned). Calls weather_tools only — no routing,
no risk math, no LangGraph state schema ownership.

Now includes alert generation from weather observations.
"""
from typing import Any, Dict, List, Optional

from app.tools.weather_tools import (
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


from datetime import datetime, timezone

# --- Alert Thresholds (deterministic constants, NOT LLM-generated) ---
ALERT_THRESHOLDS = {
    "HIGH_WAVE": {"field": "wave_height_m", "threshold": 2.0, "severity": "HIGH"},
    "STRONG_WIND": {"field": "wind_speed_kmh", "threshold": 40.0, "severity": "HIGH"},
    "EXTREME_WIND": {"field": "wind_speed_kmh", "threshold": 60.0, "severity": "SEVERE"},
    "LOW_VISIBILITY": {"field": "visibility_km", "threshold": 1.0, "severity": "WARNING", "below": True},
    "EXTREME_WAVE": {"field": "wave_height_m", "threshold": 4.0, "severity": "SEVERE"},
}


def _generate_alerts(weather_observations: List[Dict[str, Any]], hazard_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate structured Alert objects from weather observations.

    Uses deterministic thresholds. Never uses LLM for alert generation.
    """
    alerts = []

    for obs in weather_observations:
        w = obs.get("weather", {})
        lat = obs.get("lat")
        lon = obs.get("lon")
        time_iso = obs.get("time_iso")

        # Wave height alerts
        wave = w.get("wave_height_m")
        if wave is not None:
            if wave >= 4.0:
                alerts.append({
                    "alert_type": "EXTREME_WAVE",
                    "severity": "SEVERE",
                    "message": f"Extreme wave height detected: {wave:.1f}m. Do NOT venture into the sea.",
                    "source": "Open-Meteo",
                    "timestamp": time_iso,
                    "lat": lat,
                    "lon": lon,
                    "evidence_ids": [],
                })
            elif wave >= 2.0:
                alerts.append({
                    "alert_type": "HIGH_WAVE",
                    "severity": "HIGH",
                    "message": f"High wave conditions: {wave:.1f}m. Exercise extreme caution.",
                    "source": "Open-Meteo",
                    "timestamp": time_iso,
                    "lat": lat,
                    "lon": lon,
                    "evidence_ids": [],
                })

        # Wind speed alerts
        wind = w.get("wind_speed_kmh")
        if wind is not None:
            if wind >= 60.0:
                alerts.append({
                    "alert_type": "EXTREME_WIND",
                    "severity": "SEVERE",
                    "message": f"Extreme wind speed: {wind:.0f} km/h. Navigation is dangerous.",
                    "source": "Open-Meteo",
                    "timestamp": time_iso,
                    "lat": lat,
                    "lon": lon,
                    "evidence_ids": [],
                })
            elif wind >= 40.0:
                alerts.append({
                    "alert_type": "STRONG_WIND",
                    "severity": "HIGH",
                    "message": f"Strong wind detected: {wind:.0f} km/h.",
                    "source": "Open-Meteo",
                    "timestamp": time_iso,
                    "lat": lat,
                    "lon": lon,
                    "evidence_ids": [],
                })

        # Visibility alerts
        vis = w.get("visibility_km")
        if vis is not None and vis < 1.0:
            alerts.append({
                "alert_type": "LOW_VISIBILITY",
                "severity": "WARNING",
                "message": f"Low visibility: {vis:.1f} km. Navigation hazard.",
                "source": "Open-Meteo",
                "timestamp": time_iso,
                "lat": lat,
                "lon": lon,
                "evidence_ids": [],
            })

    # Cyclone alert from hazard data
    if isinstance(hazard_data, dict):
        if hazard_data.get("cyclone_active"):
            alerts.append({
                "alert_type": "CYCLONE",
                "severity": "SEVERE",
                "message": "Active cyclone detected in the area. Do NOT venture into the sea.",
                "source": "GDACS",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "lat": None,
                "lon": None,
                "evidence_ids": [],
            })

        # Individual hazard segments
        for hazard in hazard_data.get("hazards", []):
            if isinstance(hazard, dict):
                alerts.append({
                    "alert_type": hazard.get("type", "MARINE_HAZARD"),
                    "severity": hazard.get("severity", "WARNING"),
                    "message": hazard.get("description", "Marine hazard detected."),
                    "source": "GDACS",
                    "timestamp": hazard.get("timestamp"),
                    "lat": hazard.get("lat"),
                    "lon": hazard.get("lon"),
                    "evidence_ids": [],
                })

    # Deduplicate by alert_type (keep the highest severity)
    seen = {}
    for alert in alerts:
        key = alert["alert_type"]
        severity_rank = {"INFO": 0, "WARNING": 1, "HIGH": 2, "SEVERE": 3}
        if key not in seen or severity_rank.get(alert["severity"], 0) > severity_rank.get(seen[key]["severity"], 0):
            seen[key] = alert

    return list(seen.values())


def weather_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch weather (and optional hazards) for trajectory waypoints in `state`.
    Reads spatial_constraints for bbox.
    Now also generates structured alerts from weather conditions.
    """
    trajectory = state.get("trajectory") or {}
    waypoints: List[Dict[str, Any]] = state.get("waypoints") or trajectory.get("waypoints", [])
    
    updates: Dict[str, Any] = {}
    if waypoints:
        updates["weather_observations"] = fetch_weather_forecast_batch(waypoints)

    # Extract bbox from state directly or from spatial_constraints
    spatial_constraints = state.get("spatial_constraints", [])
    bbox = state.get("bbox")
    if not bbox:
        for constraint in spatial_constraints:
            if constraint.get("type") == "bbox" and constraint.get("purpose") == "hazard_alerts":
                bbox = constraint.get("coordinates")
                break

    hazard_data = state.get("hazard_alerts") or {}
    if bbox:
        # We can extract a time window from the trajectory
        time_window = None
        if waypoints:
            time_window = {
                "from": waypoints[0].get("eta_iso") or waypoints[0].get("timestamp"),
                "to": waypoints[-1].get("eta_iso") or waypoints[-1].get("timestamp"),
            }
        hazard_data = state.get("hazard_alerts") or fetch_hazard_alerts(bbox, time_window)
        updates["hazard_alerts"] = hazard_data

    # --- Generate structured alerts ---
    weather_obs = updates.get("weather_observations", [])
    alerts = _generate_alerts(weather_obs, hazard_data)
    if alerts:
        updates["alerts"] = alerts

    # --- Populate evidence registry ---
    evidence_items = []
    for obs in weather_obs:
        w = obs.get("weather", {})
        now_iso = datetime.now(timezone.utc).isoformat()
        if w.get("wave_height_m") is not None:
            evidence_items.append({
                "evidence_id": f"weather_wave_{obs.get('waypoint_index', 0)}",
                "category": "weather",
                "value": w["wave_height_m"],
                "unit": "m",
                "source": "Open-Meteo",
                "timestamp": obs.get("time_iso"),
                "lat": obs.get("lat"),
                "lon": obs.get("lon"),
                "confidence": 1.0,
                "agent": "weather",
            })
        if w.get("wind_speed_kmh") is not None:
            evidence_items.append({
                "evidence_id": f"weather_wind_{obs.get('waypoint_index', 0)}",
                "category": "weather",
                "value": w["wind_speed_kmh"],
                "unit": "km/h",
                "source": "Open-Meteo",
                "timestamp": obs.get("time_iso"),
                "lat": obs.get("lat"),
                "lon": obs.get("lon"),
                "confidence": 1.0,
                "agent": "weather",
            })
    if evidence_items:
        updates["evidence_registry"] = evidence_items

    # Log execution
    obs_count = len(updates.get("weather_observations", []))
    alert_count = len(alerts)
    hazard_count = len(hazard_data.get("hazards", [])) if isinstance(hazard_data, dict) else 0
    updates["agent_executions"] = [{
        "agent_name": "weather",
        "status": "completed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": ["open_meteo", "gdacs"],
        "output_summary": f"Fetched {obs_count} weather observations, {hazard_count} hazards, generated {alert_count} alerts.",
        "evidence_count": len(evidence_items),
    }]

    return updates

