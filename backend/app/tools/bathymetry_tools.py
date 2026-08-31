"""
bathymetry_tools.py
===================
LangGraph-compatible tool wrapper for bathymetry (ocean depth) data.

Strict chain:
    Risk Engine / Geo Node (LangGraph) -> tool -> Adapter -> Source

Tool implemented here:
    fetch_bathymetry -- Single point bathymetry/depth lookup

Each function is a plain Python callable. If your teammate wraps it with
@tool from langgraph/langchain, the signatures are already compatible.

Reference: Step 09, Section 16.2 (tools contract)
"""
from datetime import datetime, timezone
from typing import Any, Dict

from app.adapters.gebco_adapter import GEBCOAdapter

# ---------------------------------------------------------------------------
# Module-level adapter singleton (instantiated once per process)
# ---------------------------------------------------------------------------
_gebco_adapter = GEBCOAdapter()


# ---------------------------------------------------------------------------
# Single-point tool
# ---------------------------------------------------------------------------

def fetch_bathymetry(
    lat: float,
    lon: float,
) -> Dict[str, Any]:
    """
    Return ocean depth (bathymetry) or land elevation at (lat, lon).

    Invoked by: Risk Engine / Geo Node (for grounding prevention, route planning)
    Deterministic: Data retrieval (live API or static fallback — repeatable)
    Adapter: GEBCOAdapter (Tier 1: OpenZenith/GEBCO 2025, Tier 3: static table)

    Parameters
    ----------
    lat  : Latitude of query point
    lon  : Longitude of query point

    Returns
    -------
    Dict with keys:
        lat, lon,
        depth_m (float | None)  - positive for ocean depth (meters below sea level),
                                   positive for land elevation (meters above sea level)
        surface_type (str | None) - "ocean" or "land"
        resolved (bool),
        status (str: "ok" | "unresolvable"),
        provenance (dict with source, fallback_tier, confidence)

    Example
    -------
    >>> fetch_bathymetry(12.87, 74.86)
    {
        "lat": 12.87,
        "lon": 74.86,
        "depth_m": 45.0,
        "surface_type": "ocean",
        "resolved": True,
        "status": "ok",
        "provenance": {
            "source": "OpenZenith Elevation API (GEBCO 2025 + Copernicus GLO-30)",
            "fallback_tier": 1,
            "confidence": "HIGH"
        }
    }
    """
    time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return _gebco_adapter.fetch_data(lat, lon, time_iso)
