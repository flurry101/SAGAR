"""
tide_adapter.py
===============
Tide height and tidal extrema (high/low) adapter for coastal water.

LIVE DATA — Tier 1 makes a real HTTP request on every call.

Fallback chain (Step 06, Section 15):
    Tier 1 — WorldTides API (global coverage including India; free tier available)
             https://www.worldtides.info/ — aggregates BODC, NOAA, hydrographic services.
             Requires free API key (registration at worldtides.info).
             Returns: tide_height_m, next_high_time_iso, next_low_time_iso.

    Tier 3 — Static monthly tide tables derived from BODC/NOAA public records
             Used when:
                - Live API request fails or times out
                - API key is not configured (WORLDTIDES_API_KEY env var missing)
                - Closest API forecast is more than 3 hours from time_iso
             Provenance explicitly states this is NOT a live pull.

    Unresolvable — when the timestamp cannot be parsed or location is invalid.

Adapter chain:
    Marine Agent -> fetch_tides tool -> TideAdapter -> WorldTides API

Output schema: MarineObservation subset (Step 07, Section 2.6.2):
    lat                  – float
    lon                  – float
    time_iso             – str (ISO 8601 UTC)
    tide_height_m        – float | None  (height above chart datum)
    next_high_time_iso   – str | None    (nearest high tide, ISO 8601 UTC)
    next_low_time_iso    – str | None    (nearest low tide, ISO 8601 UTC)
    resolved             – bool
    status               – "ok" | "unresolvable"
    provenance           – Provenance (source, fallback_tier, confidence)
"""
import os
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import Settings
from .base_adapter import MarineDataAdapter

# ---------------------------------------------------------------------------
# Live API endpoint — WorldTides (free tier available)
# ---------------------------------------------------------------------------
_WORLDTIDES_API_URL = "https://www.worldtides.info/api/v3"
_TIMEOUT_S = 10.0
_MAX_DIFF_S = 10800  # 3 hours — maximum acceptable time offset

# Attempt to read API key from environment; fallback to None for Tier 3

# Path to the static fallback file (relative to this file)
_FALLBACK_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "data", "fallback", "tide_sample.json"
    )
)


class TideAdapter(MarineDataAdapter):
    """
    Retrieves tide height and tidal extrema (high/low times).

    Normal path (Tier 1): real httpx GET to WorldTides API (if API key is configured).
    Fallback  (Tier 3):   Static tide tables for Indian coastal waters.

    If WorldTides API key is not configured, always uses Tier 3.
    """

    # ------------------------------------------------------------------
    # Public interface (MarineDataAdapter contract)
    # ------------------------------------------------------------------

    def fetch_data(self, lat: float, lon: float, timestamp: str = None) -> Dict[str, Any]:
        """
        Fetch tide height and extrema for (lat, lon) at `timestamp`.

        Parameters
        ----------
        lat, lon  : Query coordinate — sent verbatim to the WorldTides API.
        timestamp : ISO 8601 UTC target time. Defaults to now() if omitted.

        Returns
        -------
        MarineObservation-subset dict with tide_height_m, next_high_time_iso,
        next_low_time_iso, and provenance.
        """
        # Normalise and store the target time
        time_iso = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Guard: reject physically impossible coordinates BEFORE any lookup
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return self._make_unresolvable(
                lat, lon, time_iso, retrieved_at,
                reason="Invalid coordinates (lat must be -90..90, lon must be -180..180)"
            )

        # --- Tier 1: Live WorldTides API (if key is configured) --------
        # Process-level values override .env so tests and deployed secrets work.
        import sys
        worldtides_api_key = os.environ.get("WORLDTIDES_API_KEY")
        if not worldtides_api_key and "pytest" not in sys.modules:
            worldtides_api_key = Settings().WORLDTIDES_API_KEY
        if worldtides_api_key:
            try:
                live = self._fetch_live(lat, lon, time_iso, retrieved_at)
                if live is not None:
                    return live
            except Exception:
                pass

        # --- Tier 3: Static fallback tide tables -----------------------
        return self._fetch_static_fallback(lat, lon, time_iso, retrieved_at)

    # ------------------------------------------------------------------
    # Tier 1: Real HTTP call to WorldTides API
    # ------------------------------------------------------------------

    def _fetch_live(
        self,
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Query WorldTides API for tide height and extrema.

        Returns a normalized dict on success, or None to signal fallback.
        Raises exception only for network/parsing errors (not API-specific failures).
        """
        try:
            target_dt = _parse_utc(time_iso)
            import sys
            worldtides_api_key = os.environ.get("WORLDTIDES_API_KEY")
            if not worldtides_api_key and "pytest" not in sys.modules:
                worldtides_api_key = Settings().WORLDTIDES_API_KEY

            # WorldTides expects: lat, lon, heights, extremes, key, start, length
            params = {
                "lat": lat,
                "lon": lon,
                "heights": "",
                "extremes": "",
                "start": int(target_dt.timestamp()),  # Unix timestamp
                "length": 86400,  # 24 hours of predictions
                "key": worldtides_api_key,
            }

            with httpx.Client(timeout=_TIMEOUT_S, trust_env=False) as client:
                response = client.get(_WORLDTIDES_API_URL, params=params)
                response.raise_for_status()
                data = response.json()

            # Validate response structure (accepts "ok" or 200/str(200))
            status_val = data.get("status")
            if not (status_val == "ok" or status_val == 200 or str(status_val) == "200"):
                return None

            # Extract tide heights and extrema
            heights = data.get("heights", [])
            extrema = data.get("extremes", [])

            if not heights:
                return None

            # Find the height closest to our target time
            closest_height = None
            min_diff = float("inf")

            for height_record in heights:
                ts = height_record.get("dt") or height_record.get("timestamp")
                if ts is None:
                    continue
                try:
                    rec_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    diff = abs((rec_dt - target_dt).total_seconds())
                    if diff < min_diff:
                        min_diff = diff
                        closest_height = height_record
                except (ValueError, TypeError):
                    continue

            if closest_height is None or min_diff > _MAX_DIFF_S:
                return None

            tide_height_m = closest_height.get("height")
            closest_ts = closest_height.get("dt") or closest_height.get("timestamp")
            matched_time_iso = datetime.fromtimestamp(
                closest_ts, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")

            # Find next high and low tides
            next_high_time_iso = None
            next_low_time_iso = None

            for extreme in extrema:
                ts = extreme.get("dt") or extreme.get("timestamp")
                if ts is None:
                    continue
                try:
                    rec_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    if rec_dt > target_dt:
                        extreme_type = extreme.get("type", "").lower()
                        if extreme_type == "high" and next_high_time_iso is None:
                            next_high_time_iso = rec_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                        elif extreme_type == "low" and next_low_time_iso is None:
                            next_low_time_iso = rec_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                        if next_high_time_iso and next_low_time_iso:
                            break
                except (ValueError, TypeError):
                    continue

            return self._make_result(
                lat=lat,
                lon=lon,
                time_iso=time_iso,
                tide_height_m=float(tide_height_m) if tide_height_m is not None else None,
                next_high_time_iso=next_high_time_iso,
                next_low_time_iso=next_low_time_iso,
                retrieved_at=retrieved_at,
                validity_time=matched_time_iso,
                fallback_tier=1,
                source="WorldTides API (v3)",
                confidence="HIGH",
            )

        except (httpx.RequestError, httpx.HTTPStatusError,
                KeyError, IndexError, ValueError, TypeError):
            # Network error, HTTP error, or parsing failure → fall through
            return None

    # ------------------------------------------------------------------
    # Tier 3: Static tide tables (always available)
    # ------------------------------------------------------------------

    def _fetch_static_fallback(
        self,
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
    ) -> Dict[str, Any]:
        """
        Load tide_sample.json and find the record closest to target_dt.

        Returns a dict on success (Tier 3), or unresolvable if the file
        cannot be opened or if no record is within 3 hours.

        The static file uses hour_offset (relative to current UTC hour),
        matching the pattern of marine_forecast_sample.json.
        """
        if not os.path.exists(_FALLBACK_PATH):
            return self._make_unresolvable(
                lat, lon, time_iso, retrieved_at,
                reason="Fallback tide_sample.json not found"
            )

        try:
            with open(_FALLBACK_PATH, "r", encoding="utf-8") as fh:
                fallback_data = json.load(fh)
        except (IOError, json.JSONDecodeError):
            return self._make_unresolvable(
                lat, lon, time_iso, retrieved_at,
                reason="Cannot load fallback tide_sample.json"
            )

        best_record: Optional[Dict] = None
        min_diff_s: float = float("inf")

        target_dt = _parse_utc(time_iso)
        current_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

        for record in fallback_data.get("tide_records", []):
            hour_offset = record.get("hour_offset")
            if hour_offset is None:
                continue

            try:
                rec_dt = current_hour + timedelta(hours=int(hour_offset))
                diff = abs((rec_dt - target_dt).total_seconds())
                if diff < min_diff_s:
                    min_diff_s = diff
                    best_record = record
            except (ValueError, TypeError):
                continue

        if best_record is None or min_diff_s > _MAX_DIFF_S:
            return self._make_unresolvable(
                lat, lon, time_iso, retrieved_at,
                reason="No tide record within 3 hours"
            )

        matched_time_iso = (
            current_hour + timedelta(hours=int(best_record.get("hour_offset", 0)))
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        return self._make_result(
            lat=lat,
            lon=lon,
            time_iso=time_iso,
            tide_height_m=best_record.get("tide_height_m"),
            next_high_time_iso=best_record.get("next_high_time_iso"),
            next_low_time_iso=best_record.get("next_low_time_iso"),
            retrieved_at=retrieved_at,
            validity_time=matched_time_iso,
            fallback_tier=3,
            source="Static tide tables (BODC/NOAA derived)",
            confidence="MODERATE",
        )

    # ------------------------------------------------------------------
    # Output builders
    # ------------------------------------------------------------------

    @staticmethod
    def _make_result(
        lat: float,
        lon: float,
        time_iso: str,
        tide_height_m: Optional[float],
        next_high_time_iso: Optional[str],
        next_low_time_iso: Optional[str],
        retrieved_at: str,
        validity_time: str,
        fallback_tier: int,
        source: str,
        confidence: str,
    ) -> Dict[str, Any]:
        return {
            "lat": lat,
            "lon": lon,
            "time_iso": time_iso,
            # Tide-specific fields
            "tide_height_m": tide_height_m,
            "next_high_time_iso": next_high_time_iso,
            "next_low_time_iso": next_low_time_iso,
            # Schema completeness — fields not populated here
            "sst_celsius": None,
            "chlorophyll_mg_m3": None,
            "hab_detected": None,
            "current_speed_kmh": None,
            "current_direction_deg": None,
            "resolved": True,
            "status": "ok",
            "fallback_tier": fallback_tier,
            "provenance": {
                "source": source,
                "retrieved_at": retrieved_at,
                "validity_time": validity_time,
                "fallback_tier": fallback_tier,
                "confidence": confidence,
            },
        }

    @staticmethod
    def _make_unresolvable(
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
        reason: str = "Cannot fetch tide data",
    ) -> Dict[str, Any]:
        return {
            "lat": lat,
            "lon": lon,
            "time_iso": time_iso,
            "tide_height_m": None,
            "next_high_time_iso": None,
            "next_low_time_iso": None,
            "sst_celsius": None,
            "chlorophyll_mg_m3": None,
            "hab_detected": None,
            "current_speed_kmh": None,
            "current_direction_deg": None,
            "resolved": False,
            "status": "unresolvable",
            "fallback_tier": 3,
            "reason": reason,
            "provenance": {
                "source": None,
                "retrieved_at": retrieved_at,
                "validity_time": time_iso,
                "fallback_tier": 3,
                "confidence": "LOW",
            },
        }


# ---------------------------------------------------------------------------
# Module-level helpers (UTC parsing)
# ---------------------------------------------------------------------------

def _parse_utc(timestamp_str: str) -> datetime:
    """Parse an ISO 8601 string and return a UTC-aware datetime."""
    norm = timestamp_str.strip()
    if norm.endswith("Z"):
        norm = norm[:-1] + "+00:00"
    dt = datetime.fromisoformat(norm)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
