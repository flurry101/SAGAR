"""
Live Data Tools — Real-Time API Access (Layer 3)

These tools allow the Copilot to fetch current weather and marine conditions
when the fisherman asks about the present, or when persisted evidence is stale.

CRITICAL: These tools provide information only. They do NOT perform safety
calculations or override ORCA's risk assessment.

Reference: 08_AI_ML_AGENTIC_ARCHITECTURE.md, Section 28 — Layer 3
"""

from __future__ import annotations

import inspect
import logging
from datetime import datetime, timezone

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_live_weather(lat: float, lon: float) -> dict:
    """Get current weather and marine forecast for a location.

    Use this when the fisherman asks about current conditions, e.g.:
    - "What's the weather like near my fishing spot?"
    - "How are the waves right now at Mangalore?"
    - "Is it windy near the PFZ?"

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.

    Returns:
        Current weather data including wave height, wind speed, visibility.
    """
    try:
        from app.adapters.open_meteo_adapter import OpenMeteoAdapter

        adapter = OpenMeteoAdapter()
        time_iso = _now_iso()
        obs = adapter.fetch_data(lat, lon, time_iso)

        return {
            "data_available": True,
            "lat": lat,
            "lon": lon,
            "timestamp": time_iso,
            "source": "Open-Meteo",
            "wave_height_m": obs.get("wave_height_m"),
            "wind_speed_kmh": obs.get("wind_speed_kmh"),
            "wind_direction_deg": obs.get("wind_direction_deg"),
            "swell_height_m": obs.get("swell_height_m"),
            "visibility_km": obs.get("visibility_km"),
            "resolved": obs.get("resolved", False),
            "status": obs.get("status", "unknown"),
            "provenance": obs.get("provenance"),
        }

    except Exception as exc:  # pragma: no cover - external dependency path
        logger.warning("Live weather fetch failed: %s", exc)
        return {
            "data_available": False,
            "lat": lat,
            "lon": lon,
            "timestamp": _now_iso(),
            "source": "Open-Meteo",
            "reason": f"Weather API error: {exc}",
        }


def get_live_marine_conditions(lat: float, lon: float) -> dict:
    """Get current marine/ocean conditions for a location.

    Use this when the fisherman asks about ocean state, e.g.:
    - "What is the SST near my area?"
    - "Are there any active PFZ advisories?"
    - "Any harmful algal blooms nearby?"

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.

    Returns:
        Current marine data including SST, PFZ, and chlorophyll information.
    """
    result = {
        "data_available": False,
        "lat": lat,
        "lon": lon,
        "timestamp": _now_iso(),
        "sst": None,
        "pfz": None,
        "sources": [],
    }

    # --- SST from SST Adapter ---
    try:
        from app.adapters.sst_adapter import SSTAdapter

        sst_adapter = SSTAdapter()
        sst_data = sst_adapter.fetch_data(lat, lon, _now_iso())

        if sst_data:
            result["sst"] = {
                "sst_celsius": sst_data.get("sst_celsius"),
                "chlorophyll_mg_m3": sst_data.get("chlorophyll_mg_m3"),
                "source": sst_data.get("provenance", {}).get("source", "SST Adapter"),
                "resolved": sst_data.get("resolved", False),
            }
            result["sources"].append("SST Adapter")
            result["data_available"] = True

    except Exception as exc:
        logger.warning("SST fetch failed: %s", exc)
        result["sst"] = {"error": str(exc)}

    # --- PFZ from Static PFZ Adapter ---
    try:
        from app.adapters.static_pfz_adapter import StaticPFZAdapter

        pfz_adapter = StaticPFZAdapter()
        method_sig = inspect.signature(StaticPFZAdapter.fetch_data)
        first_param = next(iter(method_sig.parameters.values()), None)
        if first_param and first_param.name in {"self", "cls"}:
            pfz_data = pfz_adapter.fetch_data(
                lat=lat,
                lon=lon,
                timestamp=_now_iso(),
                radius_km=100.0,
            )
        else:
            pfz_data = StaticPFZAdapter.fetch_data(
                lat,
                lon,
                timestamp=_now_iso(),
                radius_km=100.0,
            )

        if pfz_data and pfz_data.get("pfzs"):
            result["pfz"] = {
                "count": len(pfz_data["pfzs"]),
                "zones": pfz_data["pfzs"][:5],  # Limit to 5 nearest
                "source": "INCOIS PFZ Advisory",
            }
            result["sources"].append("INCOIS PFZ")
            result["data_available"] = True

    except Exception as exc:
        logger.warning("PFZ fetch failed: %s", exc)
        result["pfz"] = {"error": str(exc)}

    return result


get_live_weather_tool = tool("get_live_weather")(get_live_weather)
get_live_marine_conditions_tool = tool("get_live_marine_conditions")(get_live_marine_conditions)

# Convenience list for registration
LIVE_DATA_TOOLS = [
    get_live_weather_tool,
    get_live_marine_conditions_tool,
]
