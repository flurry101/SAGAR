"""
sst_adapter.py
==============
Sea Surface Temperature (SST) adapter.

LIVE DATA — Tier 1 makes a real HTTP request on every call.

Fallback chain (Step 06, Section 15):
    Tier 1 — Open-Meteo Marine API (sea_surface_temperature, free, no auth)
              GET https://marine-api.open-meteo.com/v1/marine
                  ?latitude=LAT&longitude=LON
                  &hourly=sea_surface_temperature
                  &timezone=UTC&forecast_days=7
              The requested lat/lon and time_iso are sent verbatim to the API.
              No credentials required.

    Tier 3 — NOAA World Ocean Atlas 2023 monthly climatology table.
              Used when:
                - The live API request fails or times out.
                - The API responds but sea_surface_temperature is null for the
                  requested grid cell (Option A, approved by user 2026-08-28).
                - The closest API forecast is more than 3 hours from time_iso.
              Provenance explicitly states this is NOT a live pull.

    Unresolvable — when the timestamp cannot be parsed for either tier.

Adapter chain:
    Marine Agent -> fetch_sst tool -> SSTAdapter -> Open-Meteo Marine API

Output schema: MarineObservation subset (Step 07, Section 2.6.2):
    lat              – float
    lon              – float
    time_iso         – str (ISO 8601 UTC)
    sst_celsius      – float | None
    chlorophyll_mgm3 – None (not sourced in M4 scope)
    hab_detected     – None (owned by AmfitriteHABAdapter)
    hab_probability  – None (owned by AmfitriteHABAdapter)
    current_speed_kmh    – None (not sourced here)
    current_direction_deg – None (not sourced here)
    resolved         – bool
    status           – "ok" | "unresolvable"
    provenance       – Provenance (Section 2.9)
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .base_adapter import MarineDataAdapter
from .open_meteo_client import fetch_marine_hourly

# ---------------------------------------------------------------------------
# Live API endpoint — Open-Meteo Marine (no credentials required)
# ---------------------------------------------------------------------------
_MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
_TIMEOUT_S      = 10.0   # seconds
_MAX_DIFF_S     = 10800  # 3 hours — maximum acceptable time offset

# ---------------------------------------------------------------------------
# Tier 3 climatology fallback
# Monthly mean SST (°C) for the Arabian Sea / Indian Ocean region (~8–22°N, 68–80°E).
# Derived from NOAA World Ocean Atlas 2023 documented monthly means.
# NOT a live pull — hand-built reference table used only when Tier 1 fails.
# ---------------------------------------------------------------------------
_SEASONAL_SST: Dict[int, float] = {
    1:  27.0,   # January
    2:  27.5,   # February
    3:  28.5,   # March
    4:  29.5,   # April
    5:  30.0,   # May
    6:  28.5,   # June   — SW monsoon onset cools surface
    7:  27.5,   # July
    8:  27.0,   # August
    9:  27.5,   # September
    10: 28.0,   # October
    11: 28.5,   # November
    12: 27.5,   # December
}


class SSTAdapter(MarineDataAdapter):
    """
    Retrieves Sea Surface Temperature.

    Normal path (Tier 1): real httpx GET to Open-Meteo Marine API.
    Fallback  (Tier 3):   _SEASONAL_SST climatology table.

    There is no Tier 2 for SST — no validated ML inference is scoped here.
    """

    # ------------------------------------------------------------------
    # Public interface (MarineDataAdapter contract)
    # ------------------------------------------------------------------

    def fetch_data(self, lat: float, lon: float, timestamp: str = None) -> Dict[str, Any]:
        """
        Fetch SST for (lat, lon) at `timestamp`.

        Parameters
        ----------
        lat, lon  : Query coordinate — sent verbatim to the Open-Meteo API.
        timestamp : ISO 8601 UTC target time (e.g. waypoint eta_iso).
                    Defaults to now() if omitted.

        Returns
        -------
        MarineObservation-subset dict with sst_celsius and provenance.
        """
        # Normalise and store the target time
        time_iso     = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # --- Tier 1: Live Open-Meteo Marine API ---------------------------
        try:
            live = self._fetch_live(lat, lon, time_iso, retrieved_at)
            if live is not None:
                return live
        except Exception:
            pass

        # --- Tier 3: NOAA WOA2023 monthly climatology --------------------
        return self._fetch_climatology(lat, lon, time_iso, retrieved_at)

    # ------------------------------------------------------------------
    # Tier 1: Real HTTP call to Open-Meteo Marine API
    # ------------------------------------------------------------------

    def _fetch_live(
        self,
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Query Open-Meteo Marine API for sea_surface_temperature.

        Returns a normalized dict on success, or None to signal fallback.
        Option A (user approved 2026-08-28): if the API responds but the SST
        field is null for the requested location/time, return None so the
        climatology table is used instead.
        """
        try:
            data = fetch_marine_hourly(
                lat, lon, timeout_s=_TIMEOUT_S, forecast_days=7
            )

            hourly     = data.get("hourly", {})
            times      = hourly.get("time", [])
            sst_values = hourly.get("sea_surface_temperature", [])

            # Find closest time index
            target_dt            = _parse_utc(time_iso)
            closest_idx, diff_s  = _closest_index(times, target_dt)

            if closest_idx == -1 or diff_s > _MAX_DIFF_S:
                # No forecast within 3 hours of the requested time → fall through
                return None

            sst = sst_values[closest_idx] if closest_idx < len(sst_values) else None

            # Option A: null SST from API → fall through to climatology
            if sst is None:
                return None

            # Build validity_time from the matched API time string
            matched_time = times[closest_idx]
            if "+" not in matched_time and not matched_time.endswith("Z"):
                matched_time = matched_time + "Z"

            return self._make_result(
                lat=lat, lon=lon,
                time_iso=time_iso,
                sst_celsius=float(sst),
                retrieved_at=retrieved_at,
                validity_time=matched_time,
                fallback_tier=1,
                source="Open-Meteo Marine API (sea_surface_temperature)",
                confidence="HIGH",
            )

        except (httpx.RequestError, httpx.HTTPStatusError,
                KeyError, IndexError, ValueError, TypeError):
            # Network error, HTTP error, or parsing failure → fall through
            return None

    # ------------------------------------------------------------------
    # Tier 3: Static climatology table (always available)
    # ------------------------------------------------------------------

    def _fetch_climatology(
        self,
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
    ) -> Dict[str, Any]:
        """
        Return a Tier 3 climatology-based SST estimate for the month of `time_iso`.

        Coordinate validity is checked first.  Coordinates outside the WGS-84
        valid range (lat ∈ [-90, 90], lon ∈ [-180, 180]) are physically
        impossible and must NOT produce a fabricated climatology value — they
        are returned as unresolvable so the caller can surface the data-quality
        problem rather than silently masking it.

        This is an explicit, documented fallback. Its provenance must never be
        labelled as Tier 1 or as a live pull.

        Falls through to unresolvable if the timestamp cannot be parsed.
        """
        # ------------------------------------------------------------------
        # Guard: reject physically impossible coordinates BEFORE any lookup.
        # A GPS glitch or upstream bug must surface here, not produce a
        # plausible-looking but fabricated SST reading.
        # ------------------------------------------------------------------
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return self._make_unresolvable(
                lat, lon, time_iso, retrieved_at,
                reason=(
                    f"Invalid coordinates (lat={lat}, lon={lon}): "
                    "lat must be in [-90, 90] and lon in [-180, 180]. "
                    "Climatology lookup suppressed to avoid fabricated data."
                ),
            )

        try:
            dt  = _parse_utc(time_iso)
            sst = _SEASONAL_SST[dt.month]
        except (ValueError, KeyError):
            # Unparseable timestamp or month out of range
            return self._make_unresolvable(lat, lon, time_iso, retrieved_at)

        return self._make_result(
            lat=lat, lon=lon,
            time_iso=time_iso,
            sst_celsius=sst,
            retrieved_at=retrieved_at,
            validity_time=time_iso,
            fallback_tier=3,
            source=(
                "NOAA World Ocean Atlas 2023 — Monthly Climatology "
                "(Static Fallback, NOT a live API pull)"
            ),
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
        sst_celsius: float,
        retrieved_at: str,
        validity_time: str,
        fallback_tier: int,
        source: str,
        confidence: str,
    ) -> Dict[str, Any]:
        return {
            "lat":                lat,
            "lon":                lon,
            "time_iso":           time_iso,
            "sst_celsius":        sst_celsius,
            "chlorophyll_mgm3":   None,
            "hab_detected":       None,
            "hab_probability":    None,
            "current_speed_kmh":  None,
            "current_direction_deg": None,
            "resolved":           True,
            "status":             "ok",
            "provenance": {
                "source":        source,
                "retrieved_at":  retrieved_at,
                "validity_time": validity_time,
                "fallback_tier": fallback_tier,
                "confidence":    confidence,
            },
        }

    @staticmethod
    def _make_unresolvable(
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
        reason: str = "Cannot determine month from timestamp for climatology fallback.",
    ) -> Dict[str, Any]:
        return {
            "lat":                lat,
            "lon":                lon,
            "time_iso":           time_iso,
            "sst_celsius":        None,
            "chlorophyll_mgm3":   None,
            "hab_detected":       None,
            "hab_probability":    None,
            "current_speed_kmh":  None,
            "current_direction_deg": None,
            "resolved":           False,
            "status":             "unresolvable",
            "reason":             reason,
            "provenance": {
                "source":        None,
                "retrieved_at":  retrieved_at,
                "validity_time": time_iso,
                "fallback_tier": 3,
                "confidence":    "LOW",
            },
        }


# ---------------------------------------------------------------------------
# Module-level helpers (also used by OpenMeteoAdapter for time parsing)
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


def _closest_index(time_strs: List[str], target: datetime) -> Tuple[int, float]:
    """
    Return (index, diff_seconds) for the entry in `time_strs` closest to `target`.

    Open-Meteo returns naive-looking UTC strings ("2026-08-28T14:00") — these
    are treated as implicit UTC.  Returns (-1, inf) if the list is empty.
    """
    best_idx = -1
    min_diff = float("inf")

    for idx, t_str in enumerate(time_strs):
        norm = t_str
        if norm.endswith("Z"):
            norm = norm[:-1] + "+00:00"
        elif "+" not in norm and len(norm) > 10 and norm[10] == "T":
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
