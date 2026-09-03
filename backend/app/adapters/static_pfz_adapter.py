"""
static_pfz_adapter.py
=====================
Potential Fishing Zone (PFZ) Adapter for PathFinder.

Resilience Fallback Chain:
    Tier 1 -- Live INCOIS PFZ WFS endpoint:
              Queries INCOIS Geoserver WFS for pfzlines (GeoJSON MultiLineStrings).
              Parses coordinate points, calculates centroids and distances,
              and filters against user query parameters.
    Tier 3 -- Local GeoJSON fallback file: backend/data/fallback/pfz.geojson
              Used if live INCOIS WFS is unreachable, times out, or fails.
    Unresolvable -- Standardized error object if both live and fallback fail.

Output Schema: FishingZone (Step 07, Section 2.5):
    pfz_id        -- str
    coordinates   -- {"lat": float, "lon": float} (centroid)
    geometry      -- GeoJSON Point, LineString, MultiLineString or Polygon
    valid_from    -- str (ISO 8601)
    valid_until   -- str (ISO 8601)
    source        -- str
    distance_km   -- float
    provenance    -- Provenance dictionary

"""
import json
import math
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .base_adapter import MarineDataAdapter
from .relative_time import resolve_validity_window

# ---------------------------------------------------------------------------
# ERDDAP Endpoints and Tunable Front Detection Constants
# ---------------------------------------------------------------------------
_ERDDAP_BASE = "https://oceanwatch.pifsc.noaa.gov/erddap/griddap"
# Daily High-Resolution SST (5km)
_SST_DAILY_DATASET = "goes-poes-1d-ghrsst-RAN"
_SST_VAR = "analysed_sst"
# Chlorophyll (4km)
_CHL_DATASET = "esa-cci-chla-monthly-v6-0"
_CHL_VAR = "chlor_a"
_TIMEOUT_S = 15.0

# Tunable thresholds (calibrated against Indian Ocean SST/Chl distributions)
SST_FRONT_THRESHOLD = 0.08         # SST gradient (°C per 5km step, ~90th percentile)
CHL_PRODUCTIVITY_THRESHOLD = 0.3   # Chlorophyll-a threshold (mg/m³)

# Debug flag for diagnostic logging
_DEBUG = False

# Path to the static fallback file (relative to this file)
_FALLBACK_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "data", "fallback", "pfz.geojson"
    )
)


# ---------------------------------------------------------------------------
# Spatial Helpers
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two WGS-84 points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def _polygon_centroid(coords: List[List[float]]) -> Dict[str, float]:
    """Compute centroid of a GeoJSON Polygon ring [[lon, lat], ...]."""
    ring = coords[:-1] if coords[0] == coords[-1] else coords
    lon_sum = sum(pt[0] for pt in ring)
    lat_sum = sum(pt[1] for pt in ring)
    n = len(ring) or 1
    return {"lat": round(lat_sum / n, 4), "lon": round(lon_sum / n, 4)}


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class StaticPFZAdapter(MarineDataAdapter):
    """
    Adapter for Potential Fishing Zones (PFZs).

    Attempts Tier 1 live gradient front detection from NOAA ERDDAP Daily SST + Chlorophyll.
    Falls back to Tier 3 pfz.geojson if ERDDAP is unavailable.
    """

    def fetch_data(
        self,
        lat: float,
        lon: float,
        timestamp: str = None,
        radius_km: float = 100.0,
        debug: bool = False,
    ) -> Dict[str, Any]:
        """
        Return all PFZs within `radius_km` kilometres of (lat, lon).
        """
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # --- Tier 1: Live Front Detection via NOAA ERDDAP -----------------
        try:
            live_result = self._fetch_live_fronts(lat, lon, radius_km, retrieved_at, debug=debug or _DEBUG)
            if live_result is not None:
                return live_result
        except Exception:
            pass

        # --- Tier 3: Static Fallback File ---------------------------------
        try:
            fallback_result = self._fetch_static_fallback(lat, lon, radius_km, retrieved_at)
            if fallback_result is not None:
                return fallback_result
        except Exception:
            pass

        # --- Fully Exhausted: Error ---------------------------------------
        return {
            "pfzs": [],
            "resolved": False,
            "status": "error",
            "reason": "NOAA ERDDAP live front query failed and local pfz.geojson could not be loaded.",
            "provenance": {
                "source": None,
                "retrieved_at": retrieved_at,
                "validity_time": None,
                "fallback_tier": 3,
                "confidence": "LOW",
            },
        }

    # ------------------------------------------------------------------
    # Tier 1: Live Front Detection with Regridding & Sobel Gradient
    # ------------------------------------------------------------------

    def _fetch_live_fronts(
        self, lat: float, lon: float, radius_km: float, retrieved_at: str, debug: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Query live INCOIS WFS endpoint for PFZ lines and filter by radius."""
        url = (
            "https://www.incois.gov.in/geoserver/PFZ_Automation/ows"
            "?service=WFS&version=1.1.0&request=GetFeature"
            "&typeName=PFZ_Automation:pfzlines&outputFormat=application/json"
        )

        try:
            with httpx.Client(timeout=_TIMEOUT_S, follow_redirects=True, trust_env=False) as client:
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()

            features = data.get("features", [])
            matched_pfzs: List[Dict[str, Any]] = []
            valid_until_dt = datetime.now(timezone.utc) + timedelta(days=3)

            provenance = {
                "source": "INCOIS PFZ",
                "retrieved_at": retrieved_at,
                "validity_time": retrieved_at,
                "fallback_tier": 1,
                "confidence": "HIGH",
            }

            for idx, feature in enumerate(features):
                geom = feature.get("geometry", {})
                props = feature.get("properties", {})
                gtype = geom.get("type", "")
                coords = geom.get("coordinates", [])

                # Parse coordinates to find centroid
                all_pts = []
                if gtype == "MultiLineString":
                    for line in coords:
                        all_pts.extend(line)
                elif gtype == "LineString":
                    all_pts = coords
                
                if not all_pts:
                    continue

                lons = [p[0] for p in all_pts]
                lats = [p[1] for p in all_pts]
                avg_lon = sum(lons) / len(lons)
                avg_lat = sum(lats) / len(lats)
                centroid = {"lat": round(avg_lat, 4), "lon": round(avg_lon, 4)}

                dist_km = _haversine_km(lat, lon, centroid["lat"], centroid["lon"])
                if dist_km <= radius_km:
                    matched_pfzs.append({
                        "pfz_id": f"PFZ-INCOIS-{props.get('UID') or props.get('Sno') or (idx+1)}",
                        "coordinates": centroid,
                        "geometry": geom,
                        "valid_from": retrieved_at,
                        "valid_until": valid_until_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "source": f"INCOIS Live PFZ Line (Category {props.get('Category', 'sst')}, Length {props.get('Length', 0.0):.2f}km)",
                        "distance_km": round(dist_km, 2),
                        "provenance": provenance,
                    })

            # Sort matched PFZs by distance (closest first)
            matched_pfzs.sort(key=lambda x: x["distance_km"])

            return {
                "pfzs": matched_pfzs,
                "resolved": True,
                "status": "ok" if matched_pfzs else "empty",
                "provenance": provenance,
            }

        except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError, ValueError, TypeError):
            return None


    # ------------------------------------------------------------------
    # Tier 3: Static Fallback File
    # ------------------------------------------------------------------

    def _fetch_static_fallback(
        self, lat: float, lon: float, radius_km: float, retrieved_at: str
    ) -> Optional[Dict[str, Any]]:
        """Load fallback GeoJSON file and filter by radius."""
        if not os.path.exists(_FALLBACK_PATH):
            return None

        with open(_FALLBACK_PATH, "r", encoding="utf-8") as fh:
            geojson = json.load(fh)

        provenance = {
            "source": "INCOIS PFZ Advisory (Static Fallback -- pfz.geojson)",
            "retrieved_at": retrieved_at,
            "validity_time": None,
            "fallback_tier": 3,
            "confidence": "MODERATE",
        }

        nearby: List[Dict[str, Any]] = []
        for feature in geojson.get("features", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})

            if geom.get("type") == "Polygon":
                centroid = _polygon_centroid(geom["coordinates"][0])
            elif geom.get("type") == "Point":
                centroid = {"lat": geom["coordinates"][1], "lon": geom["coordinates"][0]}
            else:
                continue

            dist_km = _haversine_km(lat, lon, centroid["lat"], centroid["lon"])
            if dist_km <= radius_km:
                validity = resolve_validity_window(props)
                nearby.append({
                    "pfz_id": props.get("pfz_id", "UNKNOWN"),
                    "coordinates": centroid,
                    "geometry": geom,
                    "valid_from": validity["valid_from"],
                    "valid_until": validity["valid_until"],
                    "source": props.get("source", "INCOIS (Static Fallback)"),
                    "distance_km": round(dist_km, 2),
                    "provenance": provenance,
                })

        return {
            "pfzs": nearby,
            "resolved": True,
            "status": "ok" if nearby else "empty",
            "provenance": provenance,
        }

    def fetch_chlorophyll_at_point(
        self, lat: float, lon: float, timestamp: str = None
    ) -> Dict[str, Any]:
        """
        Fetch chlorophyll concentration at a specific (lat, lon) point.

        This method queries the NOAA ERDDAP chlorophyll grid without computing
        front detection. It reuses the same ERDDAP pipeline as fetch_data() but
        returns the raw chlorophyll value at the query point instead of PFZs.

        Invoked by: Marine Agent (chlorophyll-as-a-proxy-for-productivity)
        Returns: MarineObservation-subset dict with chlorophyll_mg_m3 populated

        Parameters
        ----------
        lat, lon  : Query coordinate
        timestamp : ISO 8601 UTC time (unused; chlorophyll is location-dependent)

        Returns
        -------
        Dict with:
            lat, lon, time_iso,
            chlorophyll_mg_m3 (float | None),
            resolved (bool),
            status (str: "ok" | "unresolvable"),
            provenance (Provenance)
        """
        time_iso = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Guard: reject physically impossible coordinates
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return self._make_chlorophyll_unresolvable(
                lat, lon, time_iso, retrieved_at,
                reason="Invalid coordinates"
            )

        # --- Tier 1: Live NOAA ERDDAP chlorophyll grid ----------
        try:
            live = self._fetch_chlorophyll_live(lat, lon, time_iso, retrieved_at)
            if live is not None:
                return live
        except Exception:
            pass

        # --- Tier 3: Static fallback (no chlorophyll in pfz.geojson) --
        return self._make_chlorophyll_unresolvable(
            lat, lon, time_iso, retrieved_at,
            reason="Live ERDDAP chlorophyll unavailable; static PFZ file has no chlorophyll data"
        )

    def _fetch_chlorophyll_live(
        self,
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Query NOAA ERDDAP for chlorophyll-a concentration at (lat, lon).

        Minimal region query (0.5° × 0.5° box) to avoid large transfer for a single point.
        """
        d_deg = 0.25  # 0.5° box (±0.25°)
        lat_min, lat_max = max(-90.0, lat - d_deg), min(90.0, lat + d_deg)
        lon_min, lon_max = max(-180.0, lon - d_deg), min(180.0, lon + d_deg)

        chl_url = (
            f"{_ERDDAP_BASE}/{_CHL_DATASET}.json?"
            f"{_CHL_VAR}[(last)][({lat_min:.2f}):({lat_max:.2f})][({lon_min:.2f}):({lon_max:.2f})]"
        )

        try:
            with httpx.Client(timeout=_TIMEOUT_S, follow_redirects=True, trust_env=False) as client:
                chl_resp = client.get(chl_url)
                if chl_resp.status_code != 200:
                    return None

                chl_data = chl_resp.json()
                rows = chl_data.get("table", {}).get("rows", [])

                if not rows:
                    return None

                # Find the row closest to the query point
                closest_row = None
                min_distance = float("inf")

                for row in rows:
                    r_lat, r_lon, r_val = row[1], row[2], row[3]
                    if r_val is None:
                        continue

                    # Haversine distance to this grid cell
                    distance = _haversine_km(lat, lon, r_lat, r_lon)
                    if distance < min_distance:
                        min_distance = distance
                        closest_row = (r_lat, r_lon, r_val)

                if closest_row is None:
                    return None

                chl_val = float(closest_row[2])

                return self._make_chlorophyll_result(
                    lat=lat,
                    lon=lon,
                    time_iso=time_iso,
                    chlorophyll_mg_m3=chl_val,
                    retrieved_at=retrieved_at,
                    validity_time=time_iso,
                    fallback_tier=1,
                    source="NOAA CoastWatch ERDDAP Chlorophyll-a (ESA-CCI/VIIRS 4km)",
                    confidence="HIGH",
                )

        except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError, ValueError, TypeError):
            return None

    @staticmethod
    def _make_chlorophyll_result(
        lat: float,
        lon: float,
        time_iso: str,
        chlorophyll_mg_m3: Optional[float],
        retrieved_at: str,
        validity_time: str,
        fallback_tier: int,
        source: str,
        confidence: str,
    ) -> Dict[str, Any]:
        """Assemble a chlorophyll observation dict."""
        return {
            "lat": lat,
            "lon": lon,
            "time_iso": time_iso,
            "chlorophyll_mg_m3": chlorophyll_mg_m3,
            # Schema completeness — all other marine fields are None
            "sst_celsius": None,
            "current_speed_kmh": None,
            "current_direction_deg": None,
            "hab_detected": None,
            "resolved": True,
            "status": "ok",
            "provenance": {
                "source": source,
                "retrieved_at": retrieved_at,
                "validity_time": validity_time,
                "fallback_tier": fallback_tier,
                "confidence": confidence,
            },
        }

    @staticmethod
    def _make_chlorophyll_unresolvable(
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
        reason: str = "Cannot fetch chlorophyll",
    ) -> Dict[str, Any]:
        return {
            "lat": lat,
            "lon": lon,
            "time_iso": time_iso,
            "chlorophyll_mg_m3": None,
            "sst_celsius": None,
            "current_speed_kmh": None,
            "current_direction_deg": None,
            "hab_detected": None,
            "resolved": False,
            "status": "unresolvable",
            "reason": reason,
            "provenance": {
                "source": None,
                "retrieved_at": retrieved_at,
                "validity_time": time_iso,
                "fallback_tier": 3,
                "confidence": "LOW",
            },
        }


# Alias for backward compatibility
PFZAdapter = StaticPFZAdapter
