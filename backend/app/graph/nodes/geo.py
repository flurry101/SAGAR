"""
LangGraph GEO Node wrapper.
Calculates trajectory and geofence violations from state input.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from app.gis.geocoder import geocode
from app.gis.trajectory import calculate_trajectory
from app.gis.geofence import check_geofence


def geo_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for GIS processing.

    Reads trip_context and vessel_profile from state.
    Calculates trajectory and geofence violations.
    """
    trip_context = dict(state.get("trip_context", {}))
    state["trip_context"] = trip_context
    vessel_profile = state.get("vessel_profile", {})

    origin = trip_context.get("origin")
    destination_lat = trip_context.get("destination_lat")
    destination_lon = trip_context.get("destination_lon")
    departure_time = trip_context.get("departure_time_iso")
    speed_kmh = vessel_profile.get("cruising_speed_kmh")
    
    if not origin or not departure_time or not speed_kmh:
        # Cannot calculate trajectory without these
        state["workflow_status"] = "CLARIFICATION_REQUIRED"
        state["errors"] = [{
            "node": "geo",
            "message": "Missing origin, departure_time, or vessel cruising_speed_kmh for trajectory calculation."
        }]
        return state

    speed_knots = speed_kmh * 0.539957

    # Resolve origin coords
    origin_lat, origin_lon = geocode(origin)
    origin_name = origin
    
    # Destination
    if destination_lat and destination_lon:
        dest_lat, dest_lon = destination_lat, destination_lon
        destination_name = "Custom Destination"
    else:
        # Fallback to Mangalore if unspecified for demo purposes
        dest_lat, dest_lon = geocode("Mangalore")
        destination_name = "Mangalore"

    trajectory = calculate_trajectory(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
        departure_time=departure_time,
        vessel_speed_knots=speed_knots,
        origin_name=origin_name,
        destination_name=destination_name,
    )

    violations = check_geofence(trajectory.waypoints)

    # Calculate bounding box (min_lon, min_lat, max_lon, max_lat)
    lats = [wp.lat for wp in trajectory.waypoints]
    lons = [wp.lon for wp in trajectory.waypoints]
    bbox = [min(lons) - 0.5, min(lats) - 0.5, max(lons) + 0.5, max(lats) + 0.5]

    normalized_waypoints = []
    for index, wp in enumerate(trajectory.waypoints):
        normalized_waypoints.append({
            "waypoint_index": index,
            "lat": wp.lat,
            "lon": wp.lon,
            "eta_iso": wp.timestamp,
            "phase": wp.leg_label.value.upper(),
            "timestamp": wp.timestamp,
            "leg_label": wp.leg_label.value,
        })

    trajectory_payload = trajectory.model_dump()
    trajectory_payload["waypoints"] = normalized_waypoints

    state["trip_context"]["origin_lat"] = origin_lat
    state["trip_context"]["origin_lon"] = origin_lon
    state["origin"] = {"lat": origin_lat, "lon": origin_lon}
    state["trajectory"] = trajectory_payload
    state["bbox"] = {"lat_min": min(lats) - 0.5, "lat_max": max(lats) + 0.5, "lon_min": min(lons) - 0.5, "lon_max": max(lons) + 0.5}
    state["geofence_results"] = violations
    state["spatial_constraints"] = [{
        "type": "bbox",
        "coordinates": state["bbox"],
        "purpose": "hazard_alerts"
    }]
    
    # Log agent execution
    state["agent_executions"] = [{
        "agent_name": "geo",
        "status": "completed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": ["geocoder", "trajectory_engine", "geofence_db"],
        "output_summary": f"Calculated {len(trajectory.waypoints)} waypoints and found {len(violations)} geofence violations."
    }]
    
    return state
