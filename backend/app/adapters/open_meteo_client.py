"""
open_meteo_client.py
====================
Shared Open-Meteo HTTP client with a short-lived in-process cache.

OpenMeteoAdapter (waves/wind/swell) and SSTAdapter both need the Marine
API. One marine GET is reused for both so a waypoint does not issue two
identical marine requests.
"""
from typing import Any, Dict, Tuple

import httpx

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

MARINE_HOURLY = (
    "wave_height,wave_direction,"
    "swell_wave_height,swell_wave_direction,"
    "sea_surface_temperature,"
    "ocean_current_velocity,ocean_current_direction"
)
WEATHER_HOURLY = "wind_speed_10m,wind_direction_10m,visibility"

# (rounded_lat, rounded_lon, forecast_days) -> JSON
_marine_cache: Dict[Tuple[float, float, int], Dict[str, Any]] = {}
_weather_cache: Dict[Tuple[float, float, int], Dict[str, Any]] = {}


def clear_open_meteo_cache() -> None:
    """Drop cached marine/weather payloads (tests and long-running processes)."""
    _marine_cache.clear()
    _weather_cache.clear()


def _coord_key(lat: float, lon: float, forecast_days: int) -> Tuple[float, float, int]:
    return (round(float(lat), 4), round(float(lon), 4), int(forecast_days))


def fetch_marine_hourly(
    lat: float,
    lon: float,
    timeout_s: float,
    forecast_days: int = 7,
) -> Dict[str, Any]:
    key = _coord_key(lat, lon, forecast_days)
    cached = _marine_cache.get(key)
    if cached is not None:
        return cached

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": MARINE_HOURLY,
        "timezone": "UTC",
        "forecast_days": forecast_days,
    }
    # Public data adapters must not inherit a workstation's proxy settings.
    # A stale proxy should not turn a directly reachable public API into Tier 3.
    with httpx.Client(timeout=timeout_s, trust_env=False) as client:
        resp = client.get(MARINE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    _marine_cache[key] = data
    return data


def fetch_weather_hourly(
    lat: float,
    lon: float,
    timeout_s: float,
    forecast_days: int = 7,
) -> Dict[str, Any]:
    key = _coord_key(lat, lon, forecast_days)
    cached = _weather_cache.get(key)
    if cached is not None:
        return cached

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": WEATHER_HOURLY,
        "wind_speed_unit": "kmh",
        "timezone": "UTC",
        "forecast_days": forecast_days,
    }
    with httpx.Client(timeout=timeout_s, trust_env=False) as client:
        resp = client.get(WEATHER_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    _weather_cache[key] = data
    return data
