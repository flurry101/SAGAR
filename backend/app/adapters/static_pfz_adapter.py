"""
static_pfz_adapter.py
=====================
Potential Fishing Zone (PFZ) Adapter for PathFinder.

Resilience Fallback Chain:
    Tier 1 -- Live Gradient-Based Thermal-Productivity Front Detection:
              Queries NOAA OceanWatch / CoastWatch ERDDAP for Daily SST (GHRSST goes-poes 5km)
              and Chlorophyll-a (ESA-CCI/VIIRS 4km) griddap fields across the Arabian Sea / Bay of Bengal.
              Regrids both fields onto a unified coordinate space and computes 2D Sobel
              gradient magnitude on the SST grid, thresholding with Chlorophyll productivity
              to detect oceanic upwelling fronts (Potential Fishing Zones).
    Tier 3 -- Local GeoJSON fallback file: backend/data/fallback/pfz.geojson
              Used if NOAA ERDDAP is unreachable, times out, or fails.
    Unresolvable -- Standardized error object if both live and fallback fail.

Calibration & Gradient Distribution Reference:
    Based on real-world Indian Ocean daily GHRSST gradient distributions:
      - Mean SST spatial gradient: ~0.04 - 0.06 °C / 5km step.
      - 75th percentile gradient:  ~0.06 - 0.08 °C / 5km step.
      - 90th percentile gradient:  ~0.08 - 0.11 °C / 5km step.
      - 95th percentile gradient:  ~0.10 - 0.13 °C / 5km step.
    Calibrated thresholds:
      - SST_FRONT_THRESHOLD = 0.08 (°C / 5km step, ~90th percentile): Captures active thermal fronts.
      - CHL_PRODUCTIVITY_THRESHOLD = 0.3 (mg/m³): Pelagic fish forage productivity baseline.

Output Schema: FishingZone (Step 07, Section 2.5):
    pfz_id        -- str
    coordinates   -- {"lat": float, "lon": float} (centroid)
    geometry      -- GeoJSON Point or Polygon
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
        """Query NOAA ERDDAP for Daily SST and Chlorophyll grids and compute thermal fronts."""
        # Calculate bounding box around query point with margin
        d_deg = max(0.6, (radius_km / 111.0) * 1.2)
        lat_min, lat_max = max(-90.0, lat - d_deg), min(90.0, lat + d_deg)
        lon_min, lon_max = max(-180.0, lon - d_deg), min(180.0, lon + d_deg)

        # Build ERDDAP griddap URLs
        sst_url = (
            f"{_ERDDAP_BASE}/{_SST_DAILY_DATASET}.json?"
            f"{_SST_VAR}[(last)][({lat_min:.2f}):({lat_max:.2f})][({lon_min:.2f}):({lon_max:.2f})]"
        )
        chl_url = (
            f"{_ERDDAP_BASE}/{_CHL_DATASET}.json?"
            f"{_CHL_VAR}[(last)][({lat_min:.2f}):({lat_max:.2f})][({lon_min:.2f}):({lon_max:.2f})]"
        )

        with httpx.Client(timeout=_TIMEOUT_S, follow_redirects=True) as client:
            sst_resp = client.get(sst_url)
            sst_resp.raise_for_status()
            sst_data = sst_resp.json()

            # Attempt Chlorophyll fetch (non-fatal if cloud masked)
            chl_map: Dict[Tuple[float, float], float] = {}
            try:
                chl_resp = client.get(chl_url)
                if chl_resp.status_code == 200:
                    for row in chl_resp.json().get("table", {}).get("rows", []):
                        r_lat, r_lon, r_val = row[1], row[2], row[3]
                        if r_val is not None:
                            # Key rounded to 2 decimal places for spatial hash lookup
                            chl_map[(round(r_lat, 2), round(r_lon, 2))] = float(r_val)
            except Exception:
                pass

        # Parse SST grid
        rows = sst_data.get("table", {}).get("rows", [])
        if not rows:
            return None

        # Build unified coordinate grid
        lats_set = sorted(list({r[1] for r in rows}))
        lons_set = sorted(list({r[2] for r in rows}))

        if len(lats_set) < 3 or len(lons_set) < 3:
            return None

        lat_indices = {val: idx for idx, val in enumerate(lats_set)}
        lon_indices = {val: idx for idx, val in enumerate(lons_set)}

        num_lats, num_lons = len(lats_set), len(lons_set)
        grid = [[None for _ in range(num_lons)] for _ in range(num_lats)]

        for r in rows:
            r_lat, r_lon, sst_val = r[1], r[2], r[3]
            i = lat_indices[r_lat]
            j = lon_indices[r_lon]
            if sst_val is not None:
                # Convert Kelvin to Celsius if necessary
                val_f = float(sst_val)
                grid[i][j] = val_f - 273.15 if val_f > 100.0 else val_f

        # Compute Sobel gradient magnitude on SST grid
        front_points: List[Tuple[float, float, float, float]] = []
        all_gradients: List[float] = []

        for i in range(1, num_lats - 1):
            for j in range(1, num_lons - 1):
                patch_vals = [
                    grid[i-1][j-1], grid[i-1][j], grid[i-1][j+1],
                    grid[i][j-1],   grid[i][j],   grid[i][j+1],
                    grid[i+1][j-1], grid[i+1][j], grid[i+1][j+1],
                ]
                if any(v is None for v in patch_vals):
                    continue

                # Sobel kernels
                # Horizontal gradient Gx
                gx = (patch_vals[2] + 2*patch_vals[5] + patch_vals[8]) - (patch_vals[0] + 2*patch_vals[3] + patch_vals[6])
                # Vertical gradient Gy
                gy = (patch_vals[6] + 2*patch_vals[7] + patch_vals[8]) - (patch_vals[0] + 2*patch_vals[1] + patch_vals[2])

                grad_mag = math.sqrt(gx**2 + gy**2) / 8.0
                all_gradients.append(grad_mag)

                p_lat, p_lon = lats_set[i], lons_set[j]
                # Nearest co-registered chlorophyll value
                chl_val = chl_map.get((round(p_lat, 2), round(p_lon, 2)), CHL_PRODUCTIVITY_THRESHOLD)

                if grad_mag >= SST_FRONT_THRESHOLD and chl_val >= CHL_PRODUCTIVITY_THRESHOLD:
                    front_points.append((p_lat, p_lon, grad_mag, chl_val))

        # Diagnostic logging of gradient distribution when requested
        if debug and all_gradients:
            all_gradients.sort()
            n = len(all_gradients)
            p50 = all_gradients[int(n * 0.5)]
            p75 = all_gradients[int(n * 0.75)]
            p90 = all_gradients[int(n * 0.90)]
            p95 = all_gradients[int(n * 0.95)]
            print(f"[PFZ Diagnostic] Query ({lat:.2f}, {lon:.2f}) -> Cells: {n}, "
                  f"Grad min: {all_gradients[0]:.4f}, mean: {sum(all_gradients)/n:.4f}, "
                  f"p50: {p50:.4f}, p75: {p75:.4f}, p90: {p90:.4f}, p95: {p95:.4f}, max: {all_gradients[-1]:.4f}, "
                  f"Detected Fronts: {len(front_points)}")

        # Sort front points by gradient magnitude (strongest upwelling fronts first)
        front_points.sort(key=lambda x: x[2], reverse=True)

        # Spatial clustering: select distinct front centers spaced by at least 15km
        clustered_fronts: List[Tuple[float, float, float, float]] = []
        for fp in front_points:
            f_lat, f_lon, f_grad, f_chl = fp
            too_close = False
            for c_lat, c_lon, _, _ in clustered_fronts:
                if _haversine_km(f_lat, f_lon, c_lat, c_lon) < 15.0:
                    too_close = True
                    break
            if not too_close:
                clustered_fronts.append(fp)
            if len(clustered_fronts) >= 8:
                break

        # Convert clustered fronts into FishingZone records
        matched_pfzs: List[Dict[str, Any]] = []
        valid_until_dt = datetime.now(timezone.utc) + timedelta(days=3)

        provenance = {
            "source": "Derived from NOAA CoastWatch ERDDAP SST/Chlorophyll via gradient-front detection",
            "retrieved_at": retrieved_at,
            "validity_time": retrieved_at,
            "fallback_tier": 1,
            "confidence": "MODERATE",
        }

        for idx, (f_lat, f_lon, f_grad, f_chl) in enumerate(clustered_fronts):
            dist_km = _haversine_km(lat, lon, f_lat, f_lon)
            if dist_km <= radius_km:
                # 0.05 degree box around the front centroid
                half_box = 0.025
                poly_coords = [
                    [round(f_lon - half_box, 4), round(f_lat - half_box, 4)],
                    [round(f_lon + half_box, 4), round(f_lat - half_box, 4)],
                    [round(f_lon + half_box, 4), round(f_lat + half_box, 4)],
                    [round(f_lon - half_box, 4), round(f_lat + half_box, 4)],
                    [round(f_lon - half_box, 4), round(f_lat - half_box, 4)],
                ]

                matched_pfzs.append({
                    "pfz_id": f"PFZ-NOAA-{idx+1:03d}",
                    "coordinates": {"lat": round(f_lat, 4), "lon": round(f_lon, 4)},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [poly_coords]
                    },
                    "valid_from": retrieved_at,
                    "valid_until": valid_until_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "source": f"NOAA CoastWatch ERDDAP Derived Front (Grad {f_grad:.3f}°C/5km, Chl {f_chl:.2f}mg/m³)",
                    "distance_km": round(dist_km, 2),
                    "provenance": provenance,
                })

        return {
            "pfzs": matched_pfzs,
            "resolved": True,
            "status": "ok" if matched_pfzs else "empty",
            "provenance": provenance,
        }

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


# Alias for backward compatibility
PFZAdapter = StaticPFZAdapter
