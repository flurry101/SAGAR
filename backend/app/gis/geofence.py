"""Shapely-based geofence violation checker against restricted maritime zones, MPAs, and international boundaries."""

import json
import os
from typing import List, Dict, Any, Optional
from shapely.geometry import shape, Point
from app.gis.schemas import Waypoint

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_GEOJSON_PATH = os.path.join(DATA_DIR, "restricted_zones.geojson")

ACTIVE_LAYER_FILES = [
    "restricted_zones.geojson",
    "marine_protected_areas.geojson",
    "imbl_boundaries.geojson",
    "critical_marine_habitats.geojson",
    "weather_hazard_alerts.geojson",
]


def _load_single_geojson(filepath: str) -> List[Dict[str, Any]]:
    """Parse features from a single GeoJSON file."""
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    zones = []
    for feature in data.get("features", []):
        geom = feature.get("geometry")
        if not geom:
            continue

        try:
            geom_shape = shape(geom)
        except Exception:
            continue

        properties = feature.get("properties", {})
        zone_id = (
            properties.get("zone_id")
            or properties.get("mpa_id")
            or properties.get("boundary_id")
            or properties.get("habitat_id")
            or properties.get("alert_id")
            or "UNKNOWN"
        )
        zone_name = properties.get("name") or properties.get("title") or "Restricted Maritime Zone"
        restriction_type = (
            properties.get("restriction_type")
            or properties.get("category")
            or properties.get("severity_level")
            or properties.get("protection_status")
            or "Restricted / Protected"
        )
        severity = properties.get("severity_level") or properties.get("severity") or "HIGH"
        buffer_km = properties.get("buffer_alert_km") or properties.get("buffer_km") or 0.0

        # For LineStrings (like IMBL), convert buffer km to approximate degrees (~0.009 deg / km)
        if geom.get("type") in ("LineString", "MultiLineString"):
            buffer_deg = max(buffer_km, 10.0) * 0.009
            eval_shape = geom_shape.buffer(buffer_deg)
        else:
            eval_shape = geom_shape

        zones.append(
            {
                "zone_id": zone_id,
                "zone_name": zone_name,
                "restriction_type": restriction_type,
                "severity": severity,
                "legal_act": properties.get("legal_act") or properties.get("treaty_reference"),
                "penalties": properties.get("penalties"),
                "shape": eval_shape,
            }
        )

    return zones


def load_restricted_zones(geojson_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load spatial features from GeoJSON file(s) into list of dicts with Shapely shapes.

    If geojson_path is explicitly provided, loads that single file.
    Otherwise, loads all active layers from the data directory.
    """
    if geojson_path:
        return _load_single_geojson(geojson_path)

    all_zones = []
    for filename in ACTIVE_LAYER_FILES:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            all_zones.extend(_load_single_geojson(filepath))

    return all_zones


def check_geofence(
    waypoints: List[Waypoint], geojson_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Test waypoints for spatial intersection against restricted zone polygons and border buffers.

    Args:
        waypoints: List of Waypoint objects to test.
        geojson_path: Optional path to GeoJSON containing restricted zones.

    Returns:
        List of violation dictionaries for any waypoints that fall inside a restricted zone.
        Format:
        [
            {
                "waypoint_index": 2,
                "waypoint": <Waypoint>,
                "zone_id": "RESTRICTED_NAVAL_01",
                "zone_name": "Kochi Naval Exclusion Zone",
                "restriction_type": "Naval / Defense",
                "severity": "HIGH",
                "legal_act": "...",
                "penalties": "..."
            }
        ]
    """
    zones = load_restricted_zones(geojson_path)
    if not zones or not waypoints:
        return []

    violations = []

    for idx, wp in enumerate(waypoints):
        # Note: Shapely Point takes (x, y) = (lon, lat)
        pt = Point(wp.lon, wp.lat)
        for zone in zones:
            # Use intersects or contains (covers boundaries as well)
            if zone["shape"].intersects(pt):
                violations.append(
                    {
                        "waypoint_index": idx,
                        "waypoint": wp,
                        "zone_id": zone["zone_id"],
                        "zone_name": zone["zone_name"],
                        "restriction_type": zone["restriction_type"],
                        "severity": zone.get("severity", "HIGH"),
                        "legal_act": zone.get("legal_act"),
                        "penalties": zone.get("penalties"),
                    }
                )

    return violations

