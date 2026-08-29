"""Shapely-based geofence violation checker against restricted maritime zones."""

import json
import os
from typing import List, Dict, Any, Optional
from shapely.geometry import shape, Point
from app.gis.schemas import Waypoint

DEFAULT_GEOJSON_PATH = os.path.join(
    os.path.dirname(__file__), "data", "restricted_zones.geojson"
)


def load_restricted_zones(geojson_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load spatial features from GeoJSON file into list of dicts with Shapely shapes."""
    target_path = geojson_path or DEFAULT_GEOJSON_PATH
    if not os.path.exists(target_path):
        return []

    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    zones = []
    for feature in data.get("features", []):
        geom_shape = shape(feature.get("geometry"))
        properties = feature.get("properties", {})
        zones.append(
            {
                "zone_id": properties.get("zone_id", "UNKNOWN"),
                "zone_name": properties.get("name", "Restricted Zone"),
                "restriction_type": properties.get("restriction_type", "General"),
                "shape": geom_shape,
            }
        )
    return zones


def check_geofence(
    waypoints: List[Waypoint], geojson_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Test waypoints for spatial intersection against restricted zone polygons.

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
                "restriction_type": "Naval / Defense"
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
                    }
                )

    return violations
