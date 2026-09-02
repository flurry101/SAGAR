"""
gebco_adapter.py
================
Bathymetry (ocean depth) adapter for coastal and offshore waters.

LIVE DATA — Tier 1 makes a real HTTP request on every call.

Fallback chain (Step 06, Section 15):
    Tier 1 — OpenTopoData ETOPO1 API (global relief model, land + ocean)
             https://api.opentopodata.org/v1/etopo1?locations=LAT,LON
             Free public API, no key required.
             Returns negative elevation for ocean depth, positive for land.
             ETOPO1 (NOAA/NCEI, 1 arc-minute) is authoritative for global bathymetry.

    Tier 3 — Static bathymetry lookup table for Indian coastal waters
             Used when:
                - Live API request fails or times out
                - Closest API result is more than 3 hours of tolerance
             Provenance explicitly states this is NOT a live pull.

    Unresolvable — when the timestamp cannot be parsed or location is invalid.

Adapter chain:
    Risk Engine / Geo Node -> fetch_bathymetry tool -> GEBCOAdapter -> OpenTopoData ETOPO1 API

Output schema: Bathymetry observation (Step 07, Section 2.6):
    lat              – float
    lon              – float
    time_iso         – str (ISO 8601 UTC)
    depth_m          – float (positive for ocean depth, negative for land elevation)
    resolved         – bool
    status           – "ok" | "unresolvable"
    provenance       – Provenance (source, fallback_tier, confidence)
"""
import os
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .base_adapter import MarineDataAdapter

# ---------------------------------------------------------------------------
# Live API endpoint — OpenTopoData ETOPO1 (NOAA global relief model, no auth)
# ---------------------------------------------------------------------------
_OPENTOPODATA_URL = "https://api.opentopodata.org/v1/etopo1"
_TIMEOUT_S = 10.0
_MAX_DIFF_S = 10800  # 3 hours — maximum acceptable time offset (unused for depth, but kept for consistency)

# Path to the static fallback file (relative to this file)
_FALLBACK_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "data", "fallback", "bathymetry_sample.json"
    )
)


class GEBCOAdapter(MarineDataAdapter):
    """
    Retrieves bathymetry (ocean depth) at a location.

    Normal path (Tier 1): real httpx GET to OpenTopoData ETOPO1 API.
    Fallback  (Tier 3):   Static bathymetry table for Indian coastal waters.

    Note: Depth is location-static (does not vary with time). Timestamp is
    stored for consistency with the adapter interface, but is NOT used for
    lookup — depth at (lat, lon) is always the same regardless of time_iso.
    """

    # ------------------------------------------------------------------
    # Public interface (MarineDataAdapter contract)
    # ------------------------------------------------------------------

    def fetch_data(self, lat: float, lon: float, timestamp: str = None) -> Dict[str, Any]:
        """
        Fetch bathymetry (ocean depth) for (lat, lon).

        Note: Depth is location-dependent only. Timestamp is stored but
        does not affect the result.

        Parameters
        ----------
        lat, lon  : Query coordinate — sent verbatim to the OpenZenith API.
        timestamp : ISO 8601 UTC time (stored for consistency, not used for lookup).

        Returns
        -------
        Bathymetry dict with depth_m and provenance.
        """
        # Normalise and store the time and retrieval time
        time_iso = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Guard: reject physically impossible coordinates BEFORE any lookup
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return self._make_unresolvable(
                lat, lon, time_iso, retrieved_at,
                reason="Invalid coordinates (lat must be -90..90, lon must be -180..180)"
            )

        # --- Tier 1: Live OpenZenith Elevation API (GEBCO 2025) --------
        try:
            live = self._fetch_live(lat, lon, time_iso, retrieved_at)
            if live is not None:
                return live
        except Exception:
            pass

        # --- Tier 3: Static fallback bathymetry table -----------------
        return self._fetch_static_fallback(lat, lon, time_iso, retrieved_at)

    # ------------------------------------------------------------------
    # Tier 1: Real HTTP call to OpenTopoData ETOPO1 API
    # ------------------------------------------------------------------

    def _fetch_live(
        self,
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Query OpenTopoData ETOPO1 API for elevation/depth at (lat, lon).

        OpenTopoData ETOPO1 returns:
            - negative elevation for ocean (depth below sea level, e.g., -45 for 45m deep)
            - positive elevation for land (meters above sea level)
            - status "OK" and results[0].elevation on success

        Returns a normalized dict on success, or None to signal fallback.
        Raises exception only for network/parsing errors (not API-specific failures).
        """
        try:
            # OpenTopoData uses a single `locations` param: "lat,lon"
            params = {
                "locations": f"{lat},{lon}",
            }

            with httpx.Client(timeout=_TIMEOUT_S, trust_env=False) as client:
                response = client.get(_OPENTOPODATA_URL, params=params)
                response.raise_for_status()
                data = response.json()

            # Validate response structure
            if data.get("status") != "OK":
                return None

            results = data.get("results", [])
            if not results:
                return None

            elevation = results[0].get("elevation")
            if elevation is None:
                return None

            # If elevation is negative, it's ocean depth; if positive, it's land elevation.
            # For a Risk Engine use case (grounding prevention), we need to know the
            # absolute depth below sea level. Convert to positive depth_m for ocean.
            # For land, store elevation as-is (positive = above sea level).
            if elevation < 0:
                depth_m = abs(elevation)  # Convert negative depth to positive
                surface_type = "ocean"
            else:
                depth_m = elevation  # Land elevation (positive)
                surface_type = "land"

            return self._make_result(
                lat=lat,
                lon=lon,
                time_iso=time_iso,
                depth_m=float(depth_m),
                surface_type=surface_type,
                retrieved_at=retrieved_at,
                validity_time=time_iso,
                fallback_tier=1,
                source="OpenTopoData ETOPO1 (NOAA global relief model, 1 arc-minute)",
                confidence="HIGH",
            )

        except (httpx.RequestError, httpx.HTTPStatusError,
                KeyError, IndexError, ValueError, TypeError):
            # Network error, HTTP error, or parsing failure → fall through
            return None

    # ------------------------------------------------------------------
    # Tier 3: Static bathymetry table (always available)
    # ------------------------------------------------------------------

    def _fetch_static_fallback(
        self,
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
    ) -> Dict[str, Any]:
        """
        Load bathymetry_sample.json and find the record closest to (lat, lon).

        Returns a dict on success (Tier 3), or unresolvable if the file
        cannot be opened or if no record is within search distance.

        The static file is a hand-built bathymetry lookup table for
        Indian coastal waters (key fishing zones).
        """
        if not os.path.exists(_FALLBACK_PATH):
            return self._make_unresolvable(
                lat, lon, time_iso, retrieved_at,
                reason="Fallback bathymetry_sample.json not found"
            )

        try:
            with open(_FALLBACK_PATH, "r", encoding="utf-8") as fh:
                fallback_data = json.load(fh)
        except (IOError, json.JSONDecodeError):
            return self._make_unresolvable(
                lat, lon, time_iso, retrieved_at,
                reason="Cannot load fallback bathymetry_sample.json"
            )

        # Find the closest record in the fallback table
        best_record: Optional[Dict] = None
        min_distance_m: float = float("inf")

        MAX_DISTANCE_M = 5000.0  # Max 5 km search distance for coastal table

        for record in fallback_data.get("bathymetry_records", []):
            rec_lat = record.get("lat")
            rec_lon = record.get("lon")
            if rec_lat is None or rec_lon is None:
                continue

            try:
                # Simple Haversine-like distance (for small distances, ~dx² + ~dy² suffices)
                # More accurate: use proper Haversine, but for MVP this is fine
                dx_m = (rec_lon - lon) * 111000 * (180 - abs(lat)) / 180  # rough estimate
                dy_m = (rec_lat - lat) * 111000
                distance_m = (dx_m ** 2 + dy_m ** 2) ** 0.5

                if distance_m < min_distance_m:
                    min_distance_m = distance_m
                    best_record = record
            except (ValueError, TypeError):
                continue

        if best_record is None or min_distance_m > MAX_DISTANCE_M:
            return self._make_unresolvable(
                lat, lon, time_iso, retrieved_at,
                reason=f"No bathymetry record within {MAX_DISTANCE_M/1000:.0f} km"
            )

        return self._make_result(
            lat=lat,
            lon=lon,
            time_iso=time_iso,
            depth_m=best_record.get("depth_m"),
            surface_type=best_record.get("surface_type", "ocean"),
            retrieved_at=retrieved_at,
            validity_time=time_iso,
            fallback_tier=3,
            source="Static bathymetry table (Indian coastal waters)",
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
        depth_m: Optional[float],
        surface_type: str,
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
            # Bathymetry-specific field
            "depth_m": depth_m,
            "surface_type": surface_type,  # "ocean" or "land"
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
        reason: str = "Cannot fetch bathymetry data",
    ) -> Dict[str, Any]:
        return {
            "lat": lat,
            "lon": lon,
            "time_iso": time_iso,
            "depth_m": None,
            "surface_type": None,
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
