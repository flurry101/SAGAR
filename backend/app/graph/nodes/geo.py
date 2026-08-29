"""
LangGraph GEO Node wrapper.
Calculates trajectory and geofence violations from state input.
"""

from typing import Dict, Any
from app.gis.geocoder import geocode
from app.gis.trajectory import calculate_trajectory
from app.gis.geofence import check_geofence


def geo_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for GIS processing.

    Input state keys expected:
        - origin: str or dict with lat/lon
        - destination: str or dict with lat/lon
        - departure_time: ISO string
        - vessel_speed_knots: float (default 10.0)

    Returns updated state with:
        - trajectory: dict / Trajectory dump
        - geofence_violations: list of violation dicts
    """
    origin = state.get("origin", "Cochin")
    destination = state.get("destination", "Mangalore")
    departure_time = state.get("departure_time", "2026-08-29T10:00:00Z")
    speed = float(state.get("vessel_speed_knots", 10.0))

    # Resolve origin coords
    if isinstance(origin, str):
        origin_lat, origin_lon = geocode(origin)
        origin_name = origin
    else:
        origin_lat, origin_lon = origin.get("lat"), origin.get("lon")
        origin_name = origin.get("name", "Origin")

    # Resolve dest coords
    if isinstance(destination, str):
        dest_lat, dest_lon = geocode(destination)
        destination_name = destination
    else:
        dest_lat, dest_lon = destination.get("lat"), destination.get("lon")
        destination_name = destination.get("name", "Destination")

    trajectory = calculate_trajectory(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
        departure_time=departure_time,
        vessel_speed_knots=speed,
        origin_name=origin_name,
        destination_name=destination_name,
    )

    violations = check_geofence(trajectory.waypoints)

    return {
        "trajectory": trajectory.model_dump(),
        "geofence_violations": violations,
    }
