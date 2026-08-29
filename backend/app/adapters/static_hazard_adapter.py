"""
static_hazard_adapter.py
========================
Hazard and Cyclone Alert Adapter for PathFinder.

Resilience Fallback Chain:
    Tier 1 -- Live GDACS API (Global Disaster Alert and Coordination System)
              Endpoint: https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=TC
              Retrieves active Tropical Cyclone (TC) advisories and alerts.
    Tier 3 -- Local JSON fallback file: backend/data/fallback/hazard_sample.json
              Used if the GDACS API times out, is unreachable, or fails.
    Unresolvable -- Error schema if both live API and fallback file fail.

Returns a structure matching the `fetch_hazard_alerts` tool contract (Step 09, Section 16.2):
    {
        "hazards"       : [HazardSegment, ...],
        "cyclone_active": bool,    # True if ANY returned hazard is an active cyclone
        "resolved"      : bool,
        "status"        : "ok" | "empty" | "error",
        "provenance"    : Provenance
    }

Adapter chain:
    Weather Agent -> fetch_hazard_alerts tool -> StaticHazardAdapter -> GDACS API / hazard_sample.json
"""
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from .base_adapter import MarineDataAdapter
from .relative_time import resolve_validity_window

# ---------------------------------------------------------------------------
# Endpoints and configuration
# ---------------------------------------------------------------------------
_GDACS_TC_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=TC"
_TIMEOUT_S = 10.0

# Path to the static fallback file (relative to this file)
_FALLBACK_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "data", "fallback", "hazard_sample.json"
    )
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 string to a UTC-aware datetime. Returns None on failure."""
    if not ts:
        return None
    try:
        norm = ts.strip()
        if norm.endswith("Z"):
            norm = norm[:-1] + "+00:00"
        elif "+" not in norm and "-" not in norm[10:]:
            norm += "+00:00"
        dt = datetime.fromisoformat(norm)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _format_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _bbox_intersects(
    h_lat_min: float, h_lat_max: float, h_lon_min: float, h_lon_max: float,
    q_lat_min: float, q_lat_max: float, q_lon_min: float, q_lon_max: float,
) -> bool:
    """Return True if two axis-aligned bounding boxes overlap."""
    return (
        h_lat_max >= q_lat_min and h_lat_min <= q_lat_max
        and h_lon_max >= q_lon_min and h_lon_min <= q_lon_max
    )


def _time_window_overlaps(
    h_from: Optional[datetime], h_until: Optional[datetime],
    q_from: Optional[datetime], q_until: Optional[datetime],
) -> bool:
    """Return True if two time intervals overlap. None boundaries are unbounded."""
    if h_until is not None and q_from is not None and h_until < q_from:
        return False
    if h_from is not None and q_until is not None and h_from > q_until:
        return False
    return True


def _map_gdacs_severity(alert_level: str, severity_val: Optional[float] = None) -> str:
    """Map GDACS alert level and severity to standard schema severity string."""
    lvl = (alert_level or "").strip().lower()
    if lvl == "red":
        return "SEVERE"
    if lvl == "orange":
        return "SEVERE" if (severity_val and severity_val > 120.0) else "MODERATE"
    if lvl == "green":
        return "LOW"
    return "MODERATE"


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class StaticHazardAdapter(MarineDataAdapter):
    """
    Adapter for hazard alerts and cyclone warnings.

    Attempts Tier 1 live query via GDACS Tropical Cyclone API first.
    Degrades to Tier 3 static fallback (hazard_sample.json) if the live API is unavailable.
    """

    def fetch_data(
        self,
        lat: float,
        lon: float,
        timestamp: str = None,
    ) -> Dict[str, Any]:
        """
        Single-point query shim -- delegates to fetch_hazards_for_bbox with a
        0.5-degree box around (lat, lon).
        """
        return self.fetch_hazards_for_bbox(
            bbox={
                "lat_min": lat - 0.5,
                "lat_max": lat + 0.5,
                "lon_min": lon - 0.5,
                "lon_max": lon + 0.5,
            },
            time_window={"from": timestamp, "to": None},
        )

    def fetch_hazards_for_bbox(
        self,
        bbox: Dict[str, float],
        time_window: Optional[Dict[str, Optional[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Return all hazard / cyclone segments that:
        1. Spatially intersect the supplied bounding box, AND
        2. Temporally overlap the supplied time window.

        Attempts Tier 1 live GDACS feed first, falling back to Tier 3 static JSON on failure.
        """
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # --- Tier 1: Live GDACS Tropical Cyclone Feed ---------------------
        try:
            live_result = self._fetch_live_gdacs(bbox, time_window, retrieved_at)
            if live_result is not None:
                return live_result
        except Exception:
            pass

        # --- Tier 3: Static Fallback File ---------------------------------
        try:
            fallback_result = self._fetch_static_fallback(bbox, time_window, retrieved_at)
            if fallback_result is not None:
                return fallback_result
        except Exception as exc:
            pass

        # --- Fully Exhausted: Unresolvable / Error -----------------------
        return {
            "hazards": [],
            "cyclone_active": False,
            "resolved": False,
            "status": "error",
            "reason": "GDACS live API failed and local hazard fallback file could not be loaded.",
            "provenance": {
                "source": None,
                "retrieved_at": retrieved_at,
                "validity_time": None,
                "fallback_tier": 3,
                "confidence": "LOW",
            },
        }

    # ------------------------------------------------------------------
    # Tier 1: Live GDACS Query
    # ------------------------------------------------------------------

    def _fetch_live_gdacs(
        self,
        bbox: Dict[str, float],
        time_window: Optional[Dict[str, Optional[str]]],
        retrieved_at: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Query GDACS for active tropical cyclone events and filter by bbox/time.
        Returns a normalized dict or None to trigger fallback.
        """
        with httpx.Client(timeout=_TIMEOUT_S) as client:
            resp = client.get(_GDACS_TC_URL)
            resp.raise_for_status()
            geojson = resp.json()

        features = geojson.get("features", [])

        tw = time_window or {}
        q_from = _parse_iso(tw.get("from"))
        q_until = _parse_iso(tw.get("to"))

        matched_hazards: List[Dict[str, Any]] = []
        cyclone_active = False

        provenance = {
            "source": "GDACS (Global Disaster Alert and Coordination System)",
            "retrieved_at": retrieved_at,
            "validity_time": tw.get("from"),
            "fallback_tier": 1,
            "confidence": "HIGH",
        }

        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            event_type = props.get("eventtype")

            # Filter to Tropical Cyclone events only
            if event_type != "TC":
                continue

            # Extract spatial region from bbox or point geometry
            f_bbox = feat.get("bbox")
            if f_bbox and len(f_bbox) >= 4:
                # GeoJSON standard bbox: [min_lon, min_lat, max_lon, max_lat]
                h_lon_min, h_lat_min, h_lon_max, h_lat_max = float(f_bbox[0]), float(f_bbox[1]), float(f_bbox[2]), float(f_bbox[3])
                # If bbox is a single point, buffer by 0.5 degrees
                if h_lat_min == h_lat_max:
                    h_lat_min -= 0.5
                    h_lat_max += 0.5
                if h_lon_min == h_lon_max:
                    h_lon_min -= 0.5
                    h_lon_max += 0.5
            elif geom.get("type") == "Point" and len(geom.get("coordinates", [])) >= 2:
                lon_val, lat_val = float(geom["coordinates"][0]), float(geom["coordinates"][1])
                h_lat_min, h_lat_max = lat_val - 0.5, lat_val + 0.5
                h_lon_min, h_lon_max = lon_val - 0.5, lon_val + 0.5
            else:
                continue

            affected_region = {
                "lat_min": h_lat_min,
                "lat_max": h_lat_max,
                "lon_min": h_lon_min,
                "lon_max": h_lon_max,
            }

            # Spatial filter
            if not _bbox_intersects(
                h_lat_min, h_lat_max, h_lon_min, h_lon_max,
                bbox.get("lat_min", -90.0), bbox.get("lat_max", 90.0),
                bbox.get("lon_min", -180.0), bbox.get("lon_max", 180.0),
            ):
                continue

            # Temporal filter
            h_from = _parse_iso(props.get("fromdate"))
            h_until = _parse_iso(props.get("todate"))
            if not _time_window_overlaps(h_from, h_until, q_from, q_until):
                continue

            # Severity mapping
            alert_lvl = props.get("alertlevel", "Orange")
            sev_data = props.get("severitydata", {})
            sev_val = sev_data.get("severity")
            severity = _map_gdacs_severity(alert_lvl, sev_val)

            event_id = props.get("eventid", "0")
            episode_id = props.get("episodeid", "0")
            hazard_id = f"GDACS-TC-{event_id}-{episode_id}"

            name = props.get("name") or props.get("eventname") or "Tropical Cyclone"
            desc = props.get("description") or props.get("htmldescription") or f"{name} advisory from GDACS"

            matched_hazards.append({
                "hazard_id": hazard_id,
                "hazard_type": "CYCLONE_WARNING",
                "severity": severity,
                "description": desc,
                "affected_region": affected_region,
                "valid_from": _format_iso(h_from) or props.get("fromdate"),
                "valid_until": _format_iso(h_until) or props.get("todate"),
                "cyclone_active": True,
                "source": "GDACS (Global Disaster Alert and Coordination System)",
                "provenance": provenance,
            })

            cyclone_active = True

        return {
            "hazards": matched_hazards,
            "cyclone_active": cyclone_active,
            "resolved": True,
            "status": "ok" if matched_hazards else "empty",
            "provenance": provenance,
        }

    # ------------------------------------------------------------------
    # Tier 3: Static Fallback File
    # ------------------------------------------------------------------

    def _fetch_static_fallback(
        self,
        bbox: Dict[str, float],
        time_window: Optional[Dict[str, Optional[str]]],
        retrieved_at: str,
    ) -> Optional[Dict[str, Any]]:
        """Read fallback JSON file and filter by bbox/time."""
        if not os.path.exists(_FALLBACK_PATH):
            return None

        with open(_FALLBACK_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        # If demo mode is enabled, load demo hazards from a separate file
        demo_mode = os.getenv("PF_DEMO_MODE", "false").lower() in ("1", "true", "yes")
        if demo_mode:
            demo_path = os.path.normpath(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "data", "fallback", "hazard_demo.json",
                )
            )
            try:
                if os.path.exists(demo_path):
                    with open(demo_path, "r", encoding="utf-8") as dfh:
                        demo_data = json.load(dfh)
                        # Prepend demo hazards so they're visible for demo runs
                        data_haz = data.get("hazards", [])
                        demo_haz = demo_data.get("hazards", [])
                        data["hazards"] = demo_haz + data_haz
            except Exception:
                # If demo loading fails, continue with non-demo data
                pass

        tw = time_window or {}
        q_from = _parse_iso(tw.get("from"))
        q_until = _parse_iso(tw.get("to"))

        # Build provenance using _source metadata when available
        file_source = data.get("_source")
        if file_source and isinstance(file_source, dict):
            source_text = f"{file_source.get('name')} ({file_source.get('doi') or file_source.get('url')})"
        else:
            source_text = "IMD/INCOIS Hazard Advisory (Static Fallback -- hazard_sample.json)"

        provenance = {
            "source": source_text,
            "retrieved_at": retrieved_at,
            "validity_time": tw.get("from"),
            "fallback_tier": 3,
            "confidence": "MODERATE",
        }

        matched: List[Dict[str, Any]] = []
        cyclone_active = False

        for hazard in data.get("hazards", []):
            region = hazard.get("affected_region", {})

            # Spatial filter
            if not _bbox_intersects(
                region.get("lat_min", -90), region.get("lat_max", 90),
                region.get("lon_min", -180), region.get("lon_max", 180),
                bbox.get("lat_min", -90), bbox.get("lat_max", 90),
                bbox.get("lon_min", -180), bbox.get("lon_max", 180),
            ):
                continue

            validity = resolve_validity_window(hazard)
            # Temporal filter
            h_from = _parse_iso(validity["valid_from"])
            h_until = _parse_iso(validity["valid_until"])
            if not _time_window_overlaps(h_from, h_until, q_from, q_until):
                continue

            matched.append({
                "hazard_id": hazard.get("hazard_id"),
                "hazard_type": hazard.get("hazard_type"),
                "severity": hazard.get("severity"),
                "description": hazard.get("description"),
                "affected_region": region,
                "valid_from": validity["valid_from"],
                "valid_until": validity["valid_until"],
                "cyclone_active": hazard.get("cyclone_active", False),
                "source": hazard.get("source", "IMD (Static Fallback)"),
                "provenance": provenance,
            })

            if hazard.get("cyclone_active", False):
                cyclone_active = True

        return {
            "hazards": matched,
            "cyclone_active": cyclone_active,
            "resolved": True,
            "status": "ok" if matched else "empty",
            "provenance": provenance,
        }


# Alias for backward compatibility
HazardAdapter = StaticHazardAdapter
