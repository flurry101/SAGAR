"""
open_meteo_adapter.py
=====================
Adapter for querying marine and weather forecasts from the Open-Meteo APIs.

LIVE DATA — this adapter makes real HTTP requests on every call.
No hardcoded environmental values exist in the live path.

Fallback chain (Step 06, Section 15):
    Tier 1  — Live Open-Meteo Marine API  (wave, swell, SST, ocean current)
              + Live Open-Meteo Weather API (wind, visibility)
              Both queried simultaneously per request.
    Tier 3  — Static JSON file: backend/data/fallback/marine_forecast_sample.json
              Used ONLY after the live API call fails or returns an out-of-range
              timestamp. SST and ocean current are NOT available from the static
              file — they are returned as None in Tier 3.
    Unresolvable — All fields None when both tiers are exhausted.

Adapter chain:
    Weather Agent -> tool -> OpenMeteoAdapter -> Open-Meteo Marine/Weather APIs

External API documentation:
    Marine:  https://open-meteo.com/en/docs/marine-weather-api
    Weather: https://open-meteo.com/en/docs

Unit conversion notes:
    - visibility: API returns meters -> divided by 1000.0 to produce visibility_km
    - ocean_current_velocity: API returns km/h (no conversion required)
    - sea_surface_temperature: API returns degrees Celsius (no conversion required)
    - wind_speed: requested with &wind_speed_unit=kmh -> already in km/h
"""
import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .base_adapter import MarineDataAdapter
from .open_meteo_client import fetch_marine_hourly, fetch_weather_hourly
from .relative_time import resolve_record_time


class OpenMeteoAdapter(MarineDataAdapter):
    """
    Fetches marine + atmospheric forecasts from Open-Meteo (no API key required).

    Marine API variables requested (hourly):
        wave_height, wave_direction,
        swell_wave_height, swell_wave_direction,
        sea_surface_temperature,
        ocean_current_velocity, ocean_current_direction

    Weather API variables requested (hourly):
        wind_speed_10m, wind_direction_10m, visibility

    Output fields (WeatherObservation schema + extra marine fields):
        lat, lon, time_iso
        wave_height_m, wave_direction_deg
        swell_height_m, swell_direction_deg
        wind_speed_kmh, wind_direction_deg
        visibility_km
        cyclone_alert          (always None — owned by StaticHazardAdapter)
        sst_celsius            (from Marine API; None if API null or Tier 3)
        current_speed_kmh      (from Marine API; None if API null or Tier 3)
        current_direction_deg  (from Marine API; None if API null or Tier 3)
        resolved, provenance
    """

    MARINE_URL  = "https://marine-api.open-meteo.com/v1/marine"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    TIMEOUT_S   = 10.0   # seconds before falling back to Tier 3
    MAX_TIME_DIFF_S = 10800  # 3 hours — max deviation before fallback

    # -----------------------------------------------------------------------
    # Fallback file path (resolved relative to this file, independent of cwd)
    # -----------------------------------------------------------------------
    _FALLBACK_PATH = os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "data", "fallback", "marine_forecast_sample.json",
        )
    )

    # -----------------------------------------------------------------------
    # Public interface — MarineDataAdapter contract
    # -----------------------------------------------------------------------

    def fetch_data(self, lat: float, lon: float, timestamp: str = None) -> Dict[str, Any]:
        """
        Return a normalized weather + marine observation for (lat, lon) at `timestamp`.

        The returned dict always contains all schema fields.
        The live Tier 1 path includes SST and ocean current.
        The Tier 3 fallback file only covers wave/swell/wind/visibility —
        sst_celsius, current_speed_kmh, current_direction_deg will be None.

        Parameters
        ----------
        lat, lon  : Waypoint coordinates sent verbatim to the Open-Meteo API.
        timestamp : ISO 8601 UTC target time (e.g. waypoint eta_iso).
                    If omitted, defaults to now().

        Returns
        -------
        WeatherObservation-shaped dict (Step 07, Section 2.6.1) with extra
        marine fields appended.
        """
        target_dt       = self._parse_utc(timestamp)
        validity_str    = target_dt.strftime("%Y-%m-%dT%H:00:00Z")
        retrieved_at    = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # ------------------------------------------------------------------
        # Tier 1: Live Open-Meteo Marine + Weather APIs
        # ------------------------------------------------------------------
        try:
            live = self._query_live_apis(lat, lon, target_dt)
            if live is not None:
                return self._build_observation(
                    lat=lat, lon=lon,
                    time_iso=validity_str,
                    retrieved_at=retrieved_at,
                    data=live,
                    source="Open-Meteo Marine & Weather API",
                    fallback_tier=1,
                    confidence="HIGH",
                )
        except Exception:
            # Any unhandled exception in the live path silently falls through.
            pass

        # ------------------------------------------------------------------
        # Tier 3: Static fallback JSON file
        # ------------------------------------------------------------------
        try:
            static = self._query_static_fallback(target_dt)
            if static is not None:
                return self._build_observation(
                    lat=lat, lon=lon,
                    time_iso=validity_str,
                    retrieved_at=retrieved_at,
                    data=static,
                    source="Hand-built static fallback (marine_forecast_sample.json — curated sample matching Step 07 schema)",
                    fallback_tier=3,
                    confidence="MODERATE",
                )
        except Exception:
            pass

        # ------------------------------------------------------------------
        # Fully exhausted — return standardized unresolvable observation
        # ------------------------------------------------------------------
        return self._build_unresolvable(lat, lon, validity_str, retrieved_at)

    # -----------------------------------------------------------------------
    # Tier 1: Live query
    # -----------------------------------------------------------------------

    def _query_live_apis(
        self, lat: float, lon: float, target_dt: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Query the Open-Meteo Marine and Weather APIs.

        Returns a raw dict of extracted values on success, or raises an
        exception if the request fails or the closest time exceeds 3 hours.
        Returns None if the closest time would exceed 3 hours (signals fallback
        rather than raising, so the exception path is reserved for real errors).
        """
        marine_json = fetch_marine_hourly(
            lat, lon, timeout_s=self.TIMEOUT_S, forecast_days=7
        )
        weather_json = fetch_weather_hourly(
            lat, lon, timeout_s=self.TIMEOUT_S, forecast_days=7
        )

        marine_hourly  = marine_json.get("hourly", {})
        weather_hourly = weather_json.get("hourly", {})

        marine_times  = marine_hourly.get("time", [])
        weather_times = weather_hourly.get("time", [])

        marine_idx,  marine_diff  = self._closest_index(marine_times,  target_dt)
        weather_idx, weather_diff = self._closest_index(weather_times, target_dt)

        # Reject if either series has no close-enough match
        if (marine_idx  == -1 or marine_diff  > self.MAX_TIME_DIFF_S or
                weather_idx == -1 or weather_diff > self.MAX_TIME_DIFF_S):
            return None  # trigger Tier 3 fallback

        def _get(lst: list, idx: int):
            """Safe list access — returns None instead of raising IndexError."""
            return lst[idx] if lst and idx < len(lst) else None

        vis_m = _get(weather_hourly.get("visibility", []), weather_idx)

        return {
            # Wave / swell — safety-critical
            "wave_height_m":      _get(marine_hourly.get("wave_height", []),            marine_idx),
            "wave_direction_deg": _get(marine_hourly.get("wave_direction", []),          marine_idx),
            "swell_height_m":     _get(marine_hourly.get("swell_wave_height", []),       marine_idx),
            "swell_direction_deg":_get(marine_hourly.get("swell_wave_direction", []),    marine_idx),
            # Atmospheric
            "wind_speed_kmh":     _get(weather_hourly.get("wind_speed_10m", []),         weather_idx),
            "wind_direction_deg": _get(weather_hourly.get("wind_direction_10m", []),     weather_idx),
            # visibility: API returns metres — convert to km
            "visibility_km":      (vis_m / 1000.0) if vis_m is not None else None,
            # Marine — not in WeatherObservation schema; carried as extra fields
            # SST: API returns °C; no conversion needed
            "sst_celsius":        _get(marine_hourly.get("sea_surface_temperature", []), marine_idx),
            # ocean_current_velocity: Open-Meteo Marine API returns km/h by default
            "current_speed_kmh":  _get(marine_hourly.get("ocean_current_velocity", []), marine_idx),
            "current_direction_deg": _get(marine_hourly.get("ocean_current_direction", []), marine_idx),
        }

    # -----------------------------------------------------------------------
    # Tier 3: Static fallback
    # -----------------------------------------------------------------------

    def _query_static_fallback(
        self, target_dt: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Load marine_forecast_sample.json and find the record closest to target_dt.

        Returns a dict on success, or None if the file cannot be opened or if
        no record is within 3 hours of the target.

        Note: The static file DOES NOT contain SST or ocean current data.
        Those fields will be None in Tier 3 observations.
        """
        if not os.path.exists(self._FALLBACK_PATH):
            return None

        with open(self._FALLBACK_PATH, "r", encoding="utf-8") as fh:
            fallback_data = json.load(fh)

        best_record: Optional[Dict]  = None
        min_diff_s: float            = float("inf")

        for record in fallback_data.get("forecasts", []):
            t_str = resolve_record_time(record)
            if not t_str:
                continue
            try:
                rec_dt = self._parse_utc(t_str)
                diff   = abs((rec_dt - target_dt).total_seconds())
                if diff < min_diff_s:
                    min_diff_s  = diff
                    best_record = record
            except (ValueError, TypeError):
                continue

        if best_record is None or min_diff_s > self.MAX_TIME_DIFF_S:
            return None

        return {
            "wave_height_m":       best_record.get("wave_height_m"),
            "wave_direction_deg":  best_record.get("wave_direction_deg"),
            "swell_height_m":      best_record.get("swell_height_m"),
            "swell_direction_deg": best_record.get("swell_direction_deg"),
            "wind_speed_kmh":      best_record.get("wind_speed_kmh"),
            "wind_direction_deg":  best_record.get("wind_direction_deg"),
            "visibility_km":       best_record.get("visibility_km"),
            # SST and ocean current are NOT in the static file
            "sst_celsius":         None,
            "current_speed_kmh":   None,
            "current_direction_deg": None,
        }

    # -----------------------------------------------------------------------
    # Output builders
    # -----------------------------------------------------------------------

    def _build_observation(
        self,
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
        data: Dict[str, Any],
        source: str,
        fallback_tier: int,
        confidence: str,
    ) -> Dict[str, Any]:
        """Assemble the full normalized observation dict from extracted raw values."""
        return {
            "lat":                  lat,
            "lon":                  lon,
            "time_iso":             time_iso,
            # WeatherObservation schema fields (Step 07, Section 2.6.1)
            "wave_height_m":        data.get("wave_height_m"),
            "wind_speed_kmh":       data.get("wind_speed_kmh"),
            "wind_direction_deg":   data.get("wind_direction_deg"),
            "swell_height_m":       data.get("swell_height_m"),
            "swell_direction_deg":  data.get("swell_direction_deg"),
            # cyclone_alert is explicitly None here — M4 rule (see Step 07 Section 2.6.1):
            # Cyclone data belongs to StaticHazardAdapter. Never substitute False.
            "cyclone_alert":        None,
            "visibility_km":        data.get("visibility_km"),
            # Extra marine fields (from Marine API — None in Tier 3 fallback)
            "sst_celsius":          data.get("sst_celsius"),
            "current_speed_kmh":    data.get("current_speed_kmh"),
            "current_direction_deg": data.get("current_direction_deg"),
            "resolved":             True,
            "provenance": {
                "source":       source,
                "retrieved_at": retrieved_at,
                "validity_time": time_iso,
                "fallback_tier": fallback_tier,
                "confidence":    confidence,
            },
        }

    def _build_unresolvable(
        self,
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
    ) -> Dict[str, Any]:
        """
        Return a symmetrically shaped unresolvable observation.

        All environmental values are None — never 0.0, never a guessed value.
        The Risk Engine treats this as INSUFFICIENT_INFORMATION.
        Provenance is present with source=None and confidence=LOW so downstream
        code always finds a provenance key in the same shape.
        """
        return {
            "lat":                  lat,
            "lon":                  lon,
            "time_iso":             time_iso,
            "wave_height_m":        None,
            "wind_speed_kmh":       None,
            "wind_direction_deg":   None,
            "swell_height_m":        None,
            "swell_direction_deg":  None,
            "cyclone_alert":        None,
            "visibility_km":        None,
            "sst_celsius":          None,
            "current_speed_kmh":    None,
            "current_direction_deg": None,
            "resolved":             False,
            "status":               "unresolvable",
            "reason": (
                "Live Open-Meteo API failed or timed out AND the static fallback "
                "file had no record within 3 hours of the requested time."
            ),
            "provenance": {
                "source":        None,
                "retrieved_at":  retrieved_at,
                "validity_time": time_iso,
                "fallback_tier": 3,
                "confidence":    "LOW",
            },
        }

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _parse_utc(timestamp_str: Optional[str]) -> datetime:
        """Parse any ISO 8601 string and return a UTC-aware datetime."""
        if not timestamp_str:
            return datetime.now(timezone.utc)
        norm = timestamp_str.strip()
        if norm.endswith("Z"):
            norm = norm[:-1] + "+00:00"
        dt = datetime.fromisoformat(norm)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _closest_index(
        time_strs: List[str], target: datetime
    ) -> Tuple[int, float]:
        """
        Find the index in `time_strs` whose parsed datetime is closest to `target`.

        Returns (index, diff_seconds). Returns (-1, inf) if the list is empty.

        Open-Meteo time strings are naive-looking UTC (e.g. "2026-08-28T14:00").
        They are treated as UTC implicitly.
        """
        best_idx  = -1
        min_diff  = float("inf")

        for idx, t_str in enumerate(time_strs):
            # Open-Meteo returns times without timezone offset — treat as UTC
            norm = t_str
            if norm.endswith("Z"):
                norm = norm[:-1] + "+00:00"
            elif "+" not in norm and len(norm) > 10 and norm[10] == "T":
                # Naive datetime string — append UTC offset
                norm += "+00:00"
            try:
                f_dt = datetime.fromisoformat(norm)
                if f_dt.tzinfo is None:
                    f_dt = f_dt.replace(tzinfo=timezone.utc)
                diff = abs((f_dt.astimezone(timezone.utc) - target).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    best_idx = idx
            except ValueError:
                continue

        return best_idx, min_diff
