"""Deterministic trajectory calculation using Great-Circle / Haversine interpolation."""

import math
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from app.gis.schemas import Trajectory, Waypoint, LegLabel

EARTH_RADIUS_NM = 3440.065  # Earth radius in nautical miles


def parse_iso_timestamp(ts_str: str) -> datetime:
    """Parse ISO timestamp string to UTC datetime object."""
    # Ensure 'Z' format is handled properly for Python standard library
    cleaned = ts_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def format_iso_timestamp(dt: datetime) -> str:
    """Format datetime object to ISO 8601 UTC string with 'Z' suffix."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def haversine_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate Great-Circle distance between two points in Nautical Miles (nm).

    Units:
        lat1, lon1, lat2, lon2: decimal degrees
        returns: Nautical Miles (nm)
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_NM * c


def interpolate_waypoint(
    lat1: float, lon1: float, lat2: float, lon2: float, fraction: float
) -> Tuple[float, float]:
    """
    Great-circle spherical intermediate point interpolation.

    Args:
        fraction: 0.0 at start point, 1.0 at end point.

    Returns:
        Tuple of (latitude, longitude) in decimal degrees.
    """
    if fraction <= 0.0:
        return (lat1, lon1)
    if fraction >= 1.0:
        return (lat2, lon2)

    phi1 = math.radians(lat1)
    lambda1 = math.radians(lon1)
    phi2 = math.radians(lat2)
    lambda2 = math.radians(lon2)

    delta_phi = phi2 - phi1
    delta_lambda = lambda2 - lambda1

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    delta = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    if delta < 1e-9:
        return (lat1, lon1)

    sin_delta = math.sin(delta)
    a_weight = math.sin((1.0 - fraction) * delta) / sin_delta
    b_weight = math.sin(fraction * delta) / sin_delta

    x = a_weight * math.cos(phi1) * math.cos(lambda1) + b_weight * math.cos(phi2) * math.cos(lambda2)
    y = a_weight * math.cos(phi1) * math.sin(lambda1) + b_weight * math.cos(phi2) * math.sin(lambda2)
    z = a_weight * math.sin(phi1) + b_weight * math.sin(phi2)

    phi3 = math.atan2(z, math.sqrt(x**2 + y**2))
    lambda3 = math.atan2(y, x)

    return (math.degrees(phi3), math.degrees(lambda3))


def calculate_trajectory(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    departure_time: str,
    vessel_speed_knots: float,
    sample_interval_nm: float = 10.0,
    fishing_duration_hours: float = 2.0,
    origin_name: str = None,
    destination_name: str = None,
) -> Trajectory:
    """
    Calculate voyage trajectory with outbound, fishing, and return legs.

    Units & Mechanics:
        - Distance: Nautical Miles (nm)
        - Vessel Speed: Knots (kt) -> 1 kt = 1 nm / hour
        - Timestamps: ISO 8601 UTC strings, monotonically increasing
        - Interpolation: Great-Circle (haversine) at sample_interval_nm steps

    Args:
        origin_lat, origin_lon: Origin coordinates
        dest_lat, dest_lon: Destination / Fishing area coordinates
        departure_time: ISO 8601 UTC timestamp string
        vessel_speed_knots: Vessel cruising speed in knots (must be > 0)
        sample_interval_nm: Distance sampling interval in nm (default 10.0)
        fishing_duration_hours: Time spent at fishing zone in hours (default 2.0)
        origin_name: Optional name for origin
        destination_name: Optional name for destination

    Returns:
        Trajectory object containing ordered waypoints and aggregate metrics.
    """
    if vessel_speed_knots <= 0:
        raise ValueError(f"vessel_speed_knots must be positive, got {vessel_speed_knots}")
    if sample_interval_nm <= 0:
        raise ValueError(f"sample_interval_nm must be positive, got {sample_interval_nm}")

    start_dt = parse_iso_timestamp(departure_time)
    leg_distance = haversine_distance_nm(origin_lat, origin_lon, dest_lat, dest_lon)

    waypoints: List[Waypoint] = []
    current_dt = start_dt

    # Handle zero/very small distance trip
    if leg_distance < 1e-4:
        waypoints.append(
            Waypoint(
                lat=origin_lat,
                lon=origin_lon,
                timestamp=format_iso_timestamp(current_dt),
                leg_label=LegLabel.OUTBOUND,
            )
        )
        end_fishing_dt = current_dt + timedelta(hours=fishing_duration_hours)
        waypoints.append(
            Waypoint(
                lat=dest_lat,
                lon=dest_lon,
                timestamp=format_iso_timestamp(end_fishing_dt),
                leg_label=LegLabel.FISHING,
            )
        )
        return Trajectory(
            waypoints=waypoints,
            total_distance_nm=0.0,
            total_duration_hours=fishing_duration_hours,
            origin_name=origin_name,
            destination_name=destination_name,
            departure_time=departure_time,
        )

    # 1. OUTBOUND LEG: origin -> dest
    num_steps_outbound = max(1, math.ceil(leg_distance / sample_interval_nm))
    for i in range(num_steps_outbound):
        fraction = i / float(num_steps_outbound)
        lat, lon = interpolate_waypoint(origin_lat, origin_lon, dest_lat, dest_lon, fraction)
        step_dist = fraction * leg_distance
        travel_hours = step_dist / vessel_speed_knots
        wp_dt = start_dt + timedelta(hours=travel_hours)

        waypoints.append(
            Waypoint(
                lat=round(lat, 6),
                lon=round(lon, 6),
                timestamp=format_iso_timestamp(wp_dt),
                leg_label=LegLabel.OUTBOUND,
            )
        )

    # Waypoint at destination arrival
    outbound_hours = leg_distance / vessel_speed_knots
    arrival_dest_dt = start_dt + timedelta(hours=outbound_hours)
    waypoints.append(
        Waypoint(
            lat=round(dest_lat, 6),
            lon=round(dest_lon, 6),
            timestamp=format_iso_timestamp(arrival_dest_dt),
            leg_label=LegLabel.OUTBOUND,
        )
    )

    # 2. FISHING LEG: at destination for fishing_duration_hours
    if fishing_duration_hours > 0:
        finish_fishing_dt = arrival_dest_dt + timedelta(hours=fishing_duration_hours)
        waypoints.append(
            Waypoint(
                lat=round(dest_lat, 6),
                lon=round(dest_lon, 6),
                timestamp=format_iso_timestamp(finish_fishing_dt),
                leg_label=LegLabel.FISHING,
            )
        )
        current_dt = finish_fishing_dt
    else:
        current_dt = arrival_dest_dt

    # 3. RETURN LEG: dest -> origin
    num_steps_return = max(1, math.ceil(leg_distance / sample_interval_nm))
    for i in range(1, num_steps_return + 1):
        fraction = i / float(num_steps_return)
        lat, lon = interpolate_waypoint(dest_lat, dest_lon, origin_lat, origin_lon, fraction)
        step_dist = fraction * leg_distance
        travel_hours = step_dist / vessel_speed_knots
        wp_dt = current_dt + timedelta(hours=travel_hours)

        waypoints.append(
            Waypoint(
                lat=round(lat, 6),
                lon=round(lon, 6),
                timestamp=format_iso_timestamp(wp_dt),
                leg_label=LegLabel.RETURN,
            )
        )

    total_dist = 2.0 * leg_distance
    total_duration = (2.0 * outbound_hours) + fishing_duration_hours

    return Trajectory(
        waypoints=waypoints,
        total_distance_nm=round(total_dist, 2),
        total_duration_hours=round(total_duration, 2),
        origin_name=origin_name,
        destination_name=destination_name,
        departure_time=departure_time,
    )
