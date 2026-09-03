"""
marine_tools.py
===============
LangGraph-compatible tool wrappers for the Marine Agent.

Strict chain:
    Marine Agent (LangGraph) -> tool -> Adapter -> Source

Tools implemented here:
    fetch_pfz                  -- PFZ lookup within a radius of the origin
    fetch_chlorophyll          -- Chlorophyll at a single waypoint (from ERDDAP if available)
    fetch_sst                  -- single waypoint SST
    detect_hab                 -- single waypoint HAB detection
    fetch_marine_forecast_batch -- batch: one MarineObservation per trajectory waypoint

Each function is a plain Python callable.  If your teammate wraps them with
@tool from langgraph/langchain, the signatures are already compatible.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.adapters.amfitrite_hab_adapter import AmfitriteHABAdapter
from app.adapters.sst_adapter import SSTAdapter
from app.adapters.static_pfz_adapter import StaticPFZAdapter
from app.adapters.chlorophyll_adapter import ChlorophyllAdapter

# ---------------------------------------------------------------------------
# Module-level adapter singletons (instantiated once per process)
# ---------------------------------------------------------------------------
# Live-first HAB: STAC + RDNet when possible. Unresolved if imagery/weights fail.
# Mock lat>20 heuristic only when DEMO_HAB_MOCK is set on the adapter path.
_hab_adapter = AmfitriteHABAdapter()
_sst_adapter = SSTAdapter()
_pfz_adapter = StaticPFZAdapter()
_chlorophyll_adapter = ChlorophyllAdapter()

# One HAB inference per ~0.1° ROI (matches Sentinel-2 search bbox scale)
_HAB_ROI_CACHE: Dict[Tuple[float, float], Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clear_hab_roi_cache() -> None:
    """Drop ROI HAB cache (tests / new trajectory)."""
    _HAB_ROI_CACHE.clear()


def _hab_roi_key(lat: float, lon: float) -> Tuple[float, float]:
    return (round(float(lat), 1), round(float(lon), 1))


def _copy_hab_for_query(cached: Dict[str, Any], lat: float, lon: float, time_iso: str) -> Dict[str, Any]:
    out = dict(cached)
    out["lat"] = lat
    out["lon"] = lon
    out["time_iso"] = time_iso
    out["timestamp"] = time_iso
    return out


def _cached_hab_fetch(lat: float, lon: float, time_iso: str) -> Dict[str, Any]:
    key = _hab_roi_key(lat, lon)
    if key not in _HAB_ROI_CACHE:
        _HAB_ROI_CACHE[key] = _hab_adapter.fetch_data(lat, lon, time_iso)
    return _copy_hab_for_query(_HAB_ROI_CACHE[key], lat, lon, time_iso)


def _trajectory_hab_anchor(waypoints: List[Dict[str, Any]]) -> Tuple[float, float, str]:
    """Prefer fishing-phase centroid; otherwise all-waypoint centroid."""
    fishing = [w for w in waypoints if str(w.get("phase", "")).upper() == "FISHING"]
    pool = fishing or list(waypoints)
    lat = sum(float(w["lat"]) for w in pool) / len(pool)
    lon = sum(float(w["lon"]) for w in pool) / len(pool)
    eta_iso = pool[0].get("eta_iso") or _now_iso()
    return lat, lon, eta_iso


# ---------------------------------------------------------------------------
# Single-point tools (Step 09, Section 16.2)
# ---------------------------------------------------------------------------

def fetch_pfz(
    origin: Dict[str, float],
    radius_km: float = 100.0,
) -> Dict[str, Any]:
    """
    Return Potential Fishing Zones within `radius_km` of the fisher's origin.

    Invoked by: Marine Agent
    Deterministic: Data retrieval (static file -- always same result)
    Adapter: StaticPFZAdapter (always Tier 3 for MVP)

    Parameters
    ----------
    origin    : {"lat": float, "lon": float}
    radius_km : Search radius in kilometres (default 100 km).

    Returns
    -------
    {
        "pfzs"      : [FishingZone, ...],
        "provenance": Provenance
    }
    """
    result = _pfz_adapter.fetch_data(
        lat=origin["lat"],
        lon=origin["lon"],
        radius_km=radius_km,
    )
    return {
        "pfzs":      result.get("pfzs", []),
        "provenance": result.get("provenance"),
    }


def fetch_sst(lat: float, lon: float, time_iso: str) -> Dict[str, Any]:
    """
    Return Sea Surface Temperature for a single waypoint / time.

    Invoked by: Marine Agent
    Adapter: SSTAdapter (Tier 1 live stub -> Tier 3 climatology fallback)

    Parameters
    ----------
    lat, lon : Waypoint coordinates.
    time_iso : ISO 8601 UTC target time.

    Returns
    -------
    {
        "sst_celsius": float | None,
        "provenance" : Provenance
    }
    """
    obs = _sst_adapter.fetch_data(lat, lon, time_iso)
    return {
        "sst_celsius": obs.get("sst_celsius"),
        "provenance":  obs.get("provenance"),
    }


def fetch_chlorophyll(lat: float, lon: float, time_iso: str = None) -> Dict[str, Any]:
    """
    Return chlorophyll-a concentration (productivity indicator) at a waypoint.

    Invoked by: Marine Agent (when assessing fishing productivity)
    Adapter: StaticPFZAdapter.fetch_chlorophyll_at_point()
    Live source: NOAA CoastWatch ERDDAP (ESA-CCI/VIIRS 4km chlorophyll)
    Fallback: None (no Tier 3 data available; returns unresolvable if live fails)

    Parameters
    ----------
    lat, lon : Waypoint coordinates.
    time_iso : ISO 8601 UTC target time (optional, unused; chlorophyll is location-dependent).

    Returns
    -------
    {
        "chlorophyll_mg_m3": float | None,
        "resolved"         : bool,
        "status"           : str,
        "provenance"       : Provenance
    }
    """
    time_iso = time_iso or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    obs = _pfz_adapter.fetch_chlorophyll_at_point(lat, lon, time_iso)
    return {
        "chlorophyll_mg_m3": obs.get("chlorophyll_mg_m3"),
        "resolved":          obs.get("resolved"),
        "status":            obs.get("status"),
        "provenance":        obs.get("provenance"),
    }


def detect_hab(lat: float, lon: float, time_iso: str) -> Dict[str, Any]:
    """
    Detect Harmful Algal Blooms at a specific location and time.

    Invoked by: Marine Agent
    Deterministic: No (ML inference — Tier 2 when imagery+weights available)
    Default: live-first STAC; unresolved if imagery/weights fail.
    Mock: original lat>20 heuristic only when DEMO_HAB_MOCK is set.
    Adapter: AmfitriteHABAdapter

    Repeat calls for the same ~0.1° ROI reuse a process cache.

    Parameters
    ----------
    lat, lon : Query coordinates.
    time_iso : ISO 8601 UTC target time.

    Returns
    -------
    {
        "hab_detected"   : bool | None,
        "hab_probability": float | None,
        "provenance"     : Provenance
    }
    """
    obs = _cached_hab_fetch(lat, lon, time_iso)
    return {
        "hab_detected":    obs.get("hab_detected"),
        "hab_probability": obs.get("hab_probability"),
        "provenance":      obs.get("provenance"),
    }


# ---------------------------------------------------------------------------
# Batch tool -- one full MarineObservation per trajectory waypoint
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


def fetch_marine_forecast_batch(
    waypoints: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Fetch a complete MarineObservation for every waypoint in a trajectory.

    Combines:
        - SST from SSTAdapter
        - Chlorophyll from ChlorophyllAdapter
        - HAB from AmfitriteHABAdapter

    HAB is evaluated once per trajectory at the fishing-phase centroid
    and reused for every waypoint.
    """
    import concurrent.futures
    
    results: List[Dict[str, Any]] = []

    # ---------------------------------------------------------------
    # HAB: calculate once for the trajectory
    # ---------------------------------------------------------------
    if waypoints:
        try:
            alat, alon, aeta = _trajectory_hab_anchor(waypoints)
            hab_obs = _cached_hab_fetch(alat, alon, aeta)
        except Exception:
            hab_obs = {
                "hab_detected": None,
                "hab_probability": None,
                "provenance": None,
                "resolved": False,
            }
    else:
        hab_obs = {
            "hab_detected": None,
            "hab_probability": None,
            "provenance": None,
            "resolved": False,
        }

    def fetch_single_wp(wp):
        wp = _normalize_waypoint_contract(wp)

        lat = float(wp["lat"])
        lon = float(wp["lon"])
        eta_iso = wp.get("eta_iso") or _now_iso()
        idx = wp.get("waypoint_index", 0)
        phase = wp.get("phase", "UNKNOWN")

        # -----------------------------------------------------------
        # SST
        # -----------------------------------------------------------
        try:
            sst_obs = _sst_adapter.fetch_data(
                lat,
                lon,
                eta_iso,
            )
        except Exception:
            sst_obs = {
                "sst_celsius": None,
                "provenance": None,
                "resolved": False,
            }

        # -----------------------------------------------------------
        # CHLOROPHYLL
        # -----------------------------------------------------------
        try:
            chlorophyll_obs = _chlorophyll_adapter.fetch_data(
                lat,
                lon,
                eta_iso,
            )
        except Exception:
            chlorophyll_obs = {
                "chlorophyll_mg_m3": None,
                "chlorophyll_mgm3": None,
                "provenance": None,
                "resolved": False,
            }

        # -----------------------------------------------------------
        # Provenance
        # -----------------------------------------------------------
        merged_provenance = (
            sst_obs.get("provenance")
            or chlorophyll_obs.get("provenance")
            or hab_obs.get("provenance")
        )

        # -----------------------------------------------------------
        # Complete MarineObservation
        # -----------------------------------------------------------
        marine_obs: Dict[str, Any] = {
            "lat": lat,
            "lon": lon,
            "time_iso": eta_iso,

            "sst_celsius": sst_obs.get("sst_celsius"),

            "chlorophyll_mg_m3": chlorophyll_obs.get("chlorophyll_mg_m3"),
            "chlorophyll_mgm3": chlorophyll_obs.get("chlorophyll_mgm3"),

            "hab_detected": hab_obs.get("hab_detected"),
            "hab_probability": hab_obs.get("hab_probability"),

            "current_speed_kmh": None,
            "current_direction_deg": None,

            "resolved": (
                sst_obs.get("resolved", False)
                or chlorophyll_obs.get("resolved", False)
                or hab_obs.get("resolved", False)
            ),

            "provenance": merged_provenance,
        }

        return {
            "waypoint_index": idx,
            "phase": phase,
            "lat": lat,
            "lon": lon,
            "time_iso": eta_iso,
            "marine": marine_obs,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_single_wp, waypoints))

    return results