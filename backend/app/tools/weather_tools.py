"""
weather_tools.py
================
LangGraph-compatible tool wrappers for the Weather Agent.

These tools sit between the LangGraph orchestrator (owned by a teammate) and
the M4 adapters. They enforce the locked tool signatures defined in Step 09,
Section 16.2 and must NOT call external APIs directly -- all I/O goes through
an adapter.

Strict chain:
    Weather Agent (LangGraph) -> tool -> Adapter -> Source

Tools implemented here:
    fetch_wave_forecast      -- single waypoint wave height + provenance
    fetch_wind_forecast      -- single waypoint wind speed/direction + provenance
    fetch_swell_forecast     -- single waypoint swell height/direction + provenance
    fetch_hazard_alerts      -- bounding-box + time-window hazard scan
    fetch_weather_forecast_batch -- batch: one weather observation per trajectory waypoint

Each function is a plain Python callable. If your teammate wraps them with
@tool from langgraph/langchain, the signatures are already compatible.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.adapters.open_meteo_adapter import OpenMeteoAdapter
from app.adapters.static_hazard_adapter import StaticHazardAdapter

# ---------------------------------------------------------------------------
# Module-level adapter singletons (instantiated once per process)
# ---------------------------------------------------------------------------
_weather_adapter = OpenMeteoAdapter()
_hazard_adapter  = StaticHazardAdapter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Single-point tools (Step 09, Section 16.2)
# ---------------------------------------------------------------------------

def fetch_wave_forecast(lat: float, lon: float, time_iso: str) -> Dict[str, Any]:
    """
    Return significant wave height for a single waypoint / time.

    Invoked by: Weather Agent
    Deterministic: Data retrieval (non-deterministic only if source changes)
    Adapter: OpenMeteoAdapter (Tier 1 live -> Tier 3 static fallback)

    Parameters
    ----------
    lat, lon : Waypoint coordinates.
    time_iso : ISO 8601 UTC target time (e.g. waypoint eta_iso).

    Returns
    -------
    {
        "wave_height_m" : float | None,
        "provenance"    : Provenance
    }
    """
    obs = _weather_adapter.fetch_data(lat, lon, time_iso)
    return {
        "wave_height_m": obs.get("wave_height_m"),
        "provenance":    obs.get("provenance"),
    }


def fetch_wind_forecast(lat: float, lon: float, time_iso: str) -> Dict[str, Any]:
    """
    Return wind speed and direction for a single waypoint / time.

    Invoked by: Weather Agent
    Adapter: OpenMeteoAdapter (Tier 1 live -> Tier 3 static fallback)

    Returns
    -------
    {
        "wind_speed_kmh"   : float | None,
        "wind_direction_deg": float | None,
        "provenance"       : Provenance
    }
    """
    obs = _weather_adapter.fetch_data(lat, lon, time_iso)
    return {
        "wind_speed_kmh":    obs.get("wind_speed_kmh"),
        "wind_direction_deg": obs.get("wind_direction_deg"),
        "provenance":        obs.get("provenance"),
    }


def fetch_swell_forecast(lat: float, lon: float, time_iso: str) -> Dict[str, Any]:
    """
    Return swell height and direction for a single waypoint / time.

    Invoked by: Weather Agent
    Adapter: OpenMeteoAdapter (Tier 1 live -> Tier 3 static fallback)

    Returns
    -------
    {
        "swell_height_m"    : float | None,
        "swell_direction_deg": float | None,
        "provenance"        : Provenance
    }
    """
    obs = _weather_adapter.fetch_data(lat, lon, time_iso)
    return {
        "swell_height_m":     obs.get("swell_height_m"),
        "swell_direction_deg": obs.get("swell_direction_deg"),
        "provenance":         obs.get("provenance"),
    }


def fetch_hazard_alerts(
    bbox: Dict[str, float],
    time_window: Optional[Dict[str, Optional[str]]] = None,
) -> Dict[str, Any]:
    """
    Scan for cyclone and extreme-weather alerts intersecting a bounding box
    and time window.

    Invoked by: Weather Agent
Adapter: StaticHazardAdapter (Tier 1 GDACS -> Tier 3 static fallback)
    Parameters
    ----------
    bbox        : {"lat_min", "lat_max", "lon_min", "lon_max"}
    time_window : {"from": str|None, "to": str|None}  (ISO 8601)

    Returns
    -------
    {
        "hazards"       : [HazardSegment, ...],
        "cyclone_active": bool,
        "provenance"    : Provenance
    }
    """
    result = _hazard_adapter.fetch_hazards_for_bbox(bbox=bbox, time_window=time_window)
    return {
        "hazards":        result.get("hazards", []),
        "cyclone_active": result.get("cyclone_active", False),
        "provenance":     result.get("provenance"),
    }


# ---------------------------------------------------------------------------
# Batch tool -- one full WeatherObservation per trajectory waypoint
# ---------------------------------------------------------------------------

def _normalize_waypoint_contract(waypoint: Dict[str, Any]) -> Dict[str, Any]:
    """Accept legacy and current waypoint field names without breaking downstream logic."""
    eta_iso = waypoint.get("eta_iso") or waypoint.get("time_iso") or waypoint.get("timestamp") or _now_iso()
    phase = waypoint.get("phase") or waypoint.get("leg_label") or "UNKNOWN"
    normalized = dict(waypoint)
    normalized["eta_iso"] = eta_iso
    normalized["time_iso"] = eta_iso
    normalized["phase"] = str(phase).upper()
    normalized["leg_label"] = str(phase).lower()
    return normalized


def fetch_weather_forecast_batch(
    waypoints: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Fetch a complete WeatherObservation for every waypoint in a trajectory.

    For each waypoint the closest hourly forecast to `eta_iso` is selected
    (no interpolation -- see team decision in user messages).  The selection
    window is governed by the OpenMeteoAdapter's internal 3-hour deviation
    limit; if no match is found within that window, the adapter falls back to
    Tier 3 or returns an unresolvable observation.

    Invoked by: Weather Agent (batch collection for the Environmental Cube)

    Parameters
    ----------
    waypoints : List of waypoint dicts, each containing at minimum:
        {
            "waypoint_index": int,
            "phase"         : str,   # "OUTBOUND" | "FISHING" | "RETURN"
            "lat"           : float,
            "lon"           : float,
            "eta_iso"       : str    # ISO 8601 UTC ETA
        }

    Returns
    -------
    List of WaypointForecast dicts (Step 07, Section 2.7):
        {
            "waypoint_index": int,
            "phase"         : str,
            "lat"           : float,
            "lon"           : float,
            "time_iso"      : str,
            "weather"       : WeatherObservation  -- full observation dict
        }

    Errors at individual waypoints are silently handled: the observation for
    that waypoint will have resolved=False and status="unresolvable" rather
    than raising an exception that aborts the entire batch.
    """
    results: List[Dict[str, Any]] = []

    for wp in waypoints:
        wp = _normalize_waypoint_contract(wp)
        lat       = wp["lat"]
        lon       = wp["lon"]
        eta_iso   = wp.get("eta_iso") or _now_iso()
        idx       = wp.get("waypoint_index", 0)
        phase     = wp.get("phase", "UNKNOWN")

        try:
            obs = _weather_adapter.fetch_data(lat, lon, eta_iso)
        except Exception as exc:  # pragma: no cover -- adapter must never raise
            obs = {
                "lat": lat, "lon": lon, "time_iso": eta_iso,
                "wave_height_m": None, "wind_speed_kmh": None,
                "wind_direction_deg": None, "swell_height_m": None,
                "swell_direction_deg": None, "cyclone_alert": None,
                "visibility_km": None,
                "resolved": False, "status": "unresolvable",
                "reason": f"Adapter raised unexpected exception: {exc}",
                "provenance": {
                    "source": None,
                    "retrieved_at": _now_iso(),
                    "validity_time": eta_iso,
                    "fallback_tier": 3,
                    "confidence": "LOW",
                },
            }

        results.append({
            "waypoint_index": idx,
            "phase":          phase,
            "lat":            lat,
            "lon":            lon,
            "time_iso":       eta_iso,
            "weather":        obs,
        })

    return results
