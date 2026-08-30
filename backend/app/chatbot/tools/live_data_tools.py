"""
Live Data Tools — Real-Time API Access (Layer 3)

These tools allow the Copilot to fetch current weather and marine conditions
when the fisherman asks about the present, or when persisted evidence is stale.

CRITICAL: These tools provide information only. They do NOT perform safety
calculations or override ORCA's risk assessment.

Reference: 08_AI_ML_AGENTIC_ARCHITECTURE.md, Section 28 — Layer 3
"""

from __future__ import annotations

from langchain_core.tools import tool


@tool
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
    # TODO: Implement Open-Meteo Marine API call
    # from app.adapters.weather_adapter import OpenMeteoAdapter
    # adapter = OpenMeteoAdapter()
    # return await adapter.get_marine_forecast(lat, lon)

    return {
        "status": "stub",
        "lat": lat,
        "lon": lon,
        "message": f"Live weather for ({lat}, {lon}) would be fetched from Open-Meteo Marine API.",
        "note": "Implement Open-Meteo adapter in production.",
    }


@tool
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
        Current marine data including SST, currents, and any active PFZ.
    """
    # TODO: Implement MOSDAC / INCOIS API call
    # from app.adapters.marine_adapter import MOSDACAdapter
    # adapter = MOSDACAdapter()
    # return await adapter.get_marine_conditions(lat, lon)

    return {
        "status": "stub",
        "lat": lat,
        "lon": lon,
        "message": f"Live marine conditions for ({lat}, {lon}) would be fetched from MOSDAC/INCOIS.",
    }


# Convenience list for registration
LIVE_DATA_TOOLS = [
    get_live_weather,
    get_live_marine_conditions,
]
