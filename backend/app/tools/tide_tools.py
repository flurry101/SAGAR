"""
tide_tools.py
=============
LangGraph-compatible tool wrapper for the Tide data.

Strict chain:
    Marine Agent (LangGraph) -> tool -> Adapter -> Source

Tool implemented here:
    fetch_tides -- Single waypoint tide height and extrema

Each function is a plain Python callable. If your teammate wraps it with
@tool from langgraph/langchain, the signatures are already compatible.

Reference: Step 09, Section 16.2 (tools contract)
"""
from datetime import datetime, timezone
from typing import Any, Dict

from app.adapters.tide_adapter import TideAdapter

# ---------------------------------------------------------------------------
# Module-level adapter singleton (instantiated once per process)
# ---------------------------------------------------------------------------
_tide_adapter = TideAdapter()


# ---------------------------------------------------------------------------
# Single-point tool
# ---------------------------------------------------------------------------

def fetch_tides(
    lat: float,
    lon: float,
    time_iso: str = None,
) -> Dict[str, Any]:
    """
    Return tide height and nearest high/low tide times at (lat, lon).

    Invoked by: Marine Agent
    Deterministic: Data retrieval (live API or static fallback — repeatable)
    Adapter: TideAdapter (Tier 1: WorldTides API, Tier 3: static table)

    Parameters
    ----------
    lat          : Latitude of query point
    lon          : Longitude of query point
    time_iso     : ISO 8601 UTC time string (defaults to now() if omitted)

    Returns
    -------
    Dict with keys:
        lat, lon, time_iso,
        tide_height_m (float | None),
        next_high_time_iso (str | None),
        next_low_time_iso (str | None),
        resolved (bool),
        status (str: "ok" | "unresolvable"),
        provenance (dict with source, fallback_tier, confidence)

    Example
    -------
    >>> fetch_tides(12.87, 74.86, "2026-08-31T10:00:00Z")
    {
        "lat": 12.87,
        "lon": 74.86,
        "time_iso": "2026-08-31T10:00:00Z",
        "tide_height_m": 2.3,
        "next_high_time_iso": "2026-08-31T16:30:00Z",
        "next_low_time_iso": "2026-09-01T04:15:00Z",
        "resolved": True,
        "status": "ok",
        "provenance": {
            "source": "WorldTides API (v3)",
            "fallback_tier": 1,
            "confidence": "HIGH"
        }
    }
    """
    time_iso = time_iso or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return _tide_adapter.fetch_data(lat, lon, time_iso)
