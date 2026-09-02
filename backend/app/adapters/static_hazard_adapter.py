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
from typing import Any, Dict, List, Optional, Tuple
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

def _point_in_polygon(lat: float, lon: float, polygon: List[List[List[float]]]) -> bool:
    """
    Check whether a latitude/longitude point is inside a GeoJSON Polygon.

    GeoJSON coordinate order is [longitude, latitude].
    Uses the ray-casting algorithm.
    """
    if not polygon:
        return False

    # A GeoJSON Polygon may contain an outer ring plus inner holes.
    # We check the outer ring first.
    outer_ring = polygon[0]

    if len(outer_ring) < 3:
        return False

    inside = False
    j = len(outer_ring) - 1

    for i in range(len(outer_ring)):
        lon_i, lat_i = outer_ring[i][0], outer_ring[i][1]
        lon_j, lat_j = outer_ring[j][0], outer_ring[j][1]

        intersects = (
            ((lat_i > lat) != (lat_j > lat))
            and (
                lon
                < (lon_j - lon_i) * (lat - lat_i) / (lat_j - lat_i)
                + lon_i
            )
        )

        if intersects:
            inside = not inside

        j = i

    return inside


def _extract_geometry_bbox(geometry: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Calculate a simple bounding box from GeoJSON geometry.

    Returns:
        {
            "lat_min": ...,
            "lat_max": ...,
            "lon_min": ...,
            "lon_max": ...
        }

    Supports Point, LineString, Polygon and MultiPolygon.
    """
    if not geometry:
        return None

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if not coordinates:
        return None

    points: List[Tuple[float, float]] = []

    def collect_points(value: Any) -> None:
        if (
            isinstance(value, list)
            and len(value) >= 2
            and isinstance(value[0], (int, float))
            and isinstance(value[1], (int, float))
        ):
            # GeoJSON = [longitude, latitude]
            points.append((float(value[0]), float(value[1])))
            return

        if isinstance(value, list):
            for item in value:
                collect_points(item)

    collect_points(coordinates)

    if not points:
        return None

    lons = [p[0] for p in points]
    lats = [p[1] for p in points]

    return {
        "lat_min": min(lats),
        "lat_max": max(lats),
        "lon_min": min(lons),
        "lon_max": max(lons),
    }


def _geometry_matches_bbox(
    geometry: Dict[str, Any],
    bbox: Dict[str, float],
) -> bool:
    """
    Determine whether a cyclone GeoJSON geometry is relevant to the
    requested bounding box.

    For Polygon:
        checks whether any corner of the query box is inside the polygon,
        or whether the geometry bounding box overlaps the query box.

    For LineString / Point:
        uses geometry bounding-box intersection.

    The bounding-box test intentionally acts as a safety net so that
    cyclone warning areas are not missed because of exact point geometry.
    """
    geometry_bbox = _extract_geometry_bbox(geometry)

    if not geometry_bbox:
        return False

    if not _bbox_intersects(
        geometry_bbox["lat_min"],
        geometry_bbox["lat_max"],
        geometry_bbox["lon_min"],
        geometry_bbox["lon_max"],
        bbox.get("lat_min", -90.0),
        bbox.get("lat_max", 90.0),
        bbox.get("lon_min", -180.0),
        bbox.get("lon_max", 180.0),
    ):
        return False

    geometry_type = geometry.get("type")

    # For polygons, additionally check the actual query-box corners.
    if geometry_type == "Polygon":
        coordinates = geometry.get("coordinates", [])

        query_points = [
            (bbox.get("lat_min", -90.0), bbox.get("lon_min", -180.0)),
            (bbox.get("lat_min", -90.0), bbox.get("lon_max", 180.0)),
            (bbox.get("lat_max", 90.0), bbox.get("lon_min", -180.0)),
            (bbox.get("lat_max", 90.0), bbox.get("lon_max", 180.0)),
        ]

        for q_lat, q_lon in query_points:
            if _point_in_polygon(q_lat, q_lon, coordinates):
                return True

    # Bounding-box overlap is retained as the final match condition.
    return True    


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
        Query GDACS for current Tropical Cyclone events.

        Process:
            1. Get TC event list.
            2. Keep current events only.
            3. Retrieve the actual GDACS geometry for each event.
            4. Check whether the geometry overlaps the requested bbox.
            5. Normalize matching cyclone information.

        Returns a normalized dict or None to trigger Tier-3 fallback.
        """

        # ---------------------------------------------------------------
        # Step 1: Get Tropical Cyclone event list
        # ---------------------------------------------------------------

        with httpx.Client(timeout=_TIMEOUT_S) as client:
            resp = client.get(_GDACS_TC_URL)
            resp.raise_for_status()
            event_data = resp.json()

            features = event_data.get("features", [])

            tw = time_window or {}
            q_from = _parse_iso(tw.get("from"))
            q_until = _parse_iso(tw.get("to"))

            matched_hazards: List[Dict[str, Any]] = []

            provenance = {
                "source": "GDACS (Global Disaster Alert and Coordination System)",
                "retrieved_at": retrieved_at,
                "validity_time": tw.get("from"),
                "fallback_tier": 1,
                "confidence": "HIGH",
            }

            # -----------------------------------------------------------
            # Step 2: Process each cyclone event
            # -----------------------------------------------------------

            for feat in features:
                props = feat.get("properties", {})

                # Only Tropical Cyclones
                if props.get("eventtype") != "TC":
                    continue

                # -------------------------------------------------------
                # IMPORTANT:
                # Ignore historical cyclones.
                # GDACS returns old events as well.
                # -------------------------------------------------------

                is_current = props.get("iscurrent")

                if isinstance(is_current, str):
                    is_current = is_current.strip().lower() == "true"

                if is_current is False:
                    continue

                # -------------------------------------------------------
                # India-specific filtering
                # -------------------------------------------------------

                country = str(props.get("country", "")).strip().lower()
                iso3 = str(props.get("iso3", "")).strip().upper()

                affected_countries = props.get("affectedcountries", [])

                india_affected = (
                    country == "india"
                    or iso3 == "IND"
                    or any(
                        isinstance(c, dict)
                        and (
                            str(c.get("iso3", "")).upper() == "IND"
                            or str(c.get("iso2", "")).upper() == "IN"
                        )
                        for c in affected_countries
                    )
                )
                has_india_metadata = bool(country or iso3 or affected_countries)

                # If GDACS explicitly identifies another country and not India,
                # don't treat it as an India cyclone.
                if has_india_metadata and not india_affected:
                    continue

                # -------------------------------------------------------
                # Step 3: Temporal filtering
                # -------------------------------------------------------

                h_from = _parse_iso(props.get("fromdate"))
                h_until = _parse_iso(props.get("todate"))

                if not _time_window_overlaps(
                    h_from,
                    h_until,
                    q_from,
                    q_until,
                ):
                    continue

                # -------------------------------------------------------
                # Step 4: Get actual cyclone geometry
                # -------------------------------------------------------

                event_id = props.get("eventid")
                episode_id = props.get("episodeid")

                geometry_url = (
                    props.get("url", {}).get("geometry")
                    if isinstance(props.get("url"), dict)
                    else None
                )

                geometry_features: List[Dict[str, Any]] = []

                if geometry_url:
                    try:
                        geometry_resp = client.get(geometry_url)
                        geometry_resp.raise_for_status()
                        geometry_data = geometry_resp.json()

                        geometry_features = geometry_data.get("features", [])

                    except Exception:
                        # If detailed geometry fails, fall back to the
                        # event-list feature geometry.
                        geometry_features = [feat]

                else:
                    geometry_features = [feat]

                # -------------------------------------------------------
                # Step 5: Check cyclone geometry against requested bbox
                # -------------------------------------------------------

                event_matches = False
                best_region: Optional[Dict[str, float]] = None

                for geometry_feature in geometry_features:
                    geometry = geometry_feature.get("geometry", {})

                    if not geometry:
                        continue

                    if not _geometry_matches_bbox(
                        geometry,
                        bbox,
                    ):
                        continue

                    event_matches = True

                    geometry_bbox = _extract_geometry_bbox(geometry)

                    if geometry_bbox:
                        if best_region is None:
                            best_region = geometry_bbox
                        else:
                            best_region = {
                                "lat_min": min(
                                    best_region["lat_min"],
                                    geometry_bbox["lat_min"],
                                ),
                                "lat_max": max(
                                    best_region["lat_max"],
                                    geometry_bbox["lat_max"],
                                ),
                                "lon_min": min(
                                    best_region["lon_min"],
                                    geometry_bbox["lon_min"],
                                ),
                                "lon_max": max(
                                    best_region["lon_max"],
                                    geometry_bbox["lon_max"],
                                ),
                            }

                if not event_matches:
                    continue

                # -------------------------------------------------------
                # Step 6: Severity
                # -------------------------------------------------------

                alert_lvl = props.get("alertlevel", "Orange")

                sev_data = props.get("severitydata", {})

                if not isinstance(sev_data, dict):
                    sev_data = {}

                sev_val = sev_data.get("severity")

                try:
                    sev_val = float(sev_val) if sev_val is not None else None
                except (TypeError, ValueError):
                    sev_val = None

                severity = _map_gdacs_severity(
                    alert_lvl,
                    sev_val,
                )

                # -------------------------------------------------------
                # Step 7: Build normalized hazard
                # -------------------------------------------------------

                hazard_id = (
                    f"GDACS-TC-{event_id}-{episode_id}"
                )

                name = (
                    props.get("eventname")
                    or props.get("name")
                    or "Tropical Cyclone"
                )

                description = (
                    props.get("description")
                    or props.get("htmldescription")
                    or f"{name} advisory from GDACS"
                )

                # If geometry did not produce a bbox, use the requested bbox.
                if best_region is None:
                    best_region = {
                        "lat_min": bbox.get("lat_min", -90.0),
                        "lat_max": bbox.get("lat_max", 90.0),
                        "lon_min": bbox.get("lon_min", -180.0),
                        "lon_max": bbox.get("lon_max", 180.0),
                    }

                matched_hazards.append({
                    "hazard_id": hazard_id,
                    "hazard_type": "CYCLONE_WARNING",
                    "severity": severity,
                    "description": description,

                    "affected_region": best_region,

                    "valid_from": (
                        _format_iso(h_from)
                        or props.get("fromdate")
                    ),

                    "valid_until": (
                        _format_iso(h_until)
                        or props.get("todate")
                    ),

                    "cyclone_active": True,

                    "source": (
                        "GDACS (Global Disaster Alert and "
                        "Coordination System)"
                    ),

                    "provenance": provenance,

                    # Extra useful cyclone information.
                    # These do not break the existing contract.
                    "cyclone_name": props.get("eventname"),
                    "event_id": event_id,
                    "episode_id": episode_id,
                    "alert_level": alert_lvl,
                    "wind_speed_kmph": sev_val,
                    "wind_description": sev_data.get("severitytext"),
                    "source_agency": props.get("source"),
                    "forecast": props.get("forecast"),
                })

            # ---------------------------------------------------------------
            # Step 8: Return successful live result
            # ---------------------------------------------------------------

            return {
                "hazards": matched_hazards,
                "cyclone_active": bool(matched_hazards),
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
