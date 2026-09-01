"""Deterministic, explainable COLREGs encounter assessment."""
from __future__ import annotations

from math import atan2, cos, degrees, radians, sin
from typing import Any, Dict, Mapping

from app.adapters.traffic_cache import haversine_nm


def _value(vessel: Mapping[str, Any], name: str, default: float = 0.0) -> float:
    value = vessel.get(name, default)
    return float(value if value is not None else default)


def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlon = radians(lon2 - lon1)
    y = sin(dlon) * cos(radians(lat2))
    x = cos(radians(lat1)) * sin(radians(lat2)) - sin(radians(lat1)) * cos(radians(lat2)) * cos(dlon)
    return (degrees(atan2(y, x)) + 360) % 360


def _velocity(speed: float, course: float) -> tuple[float, float]:
    """Knots in local east/north components."""
    return speed * sin(radians(course)), speed * cos(radians(course))


def compute_relative_kinematics(own: Mapping[str, Any], target: Mapping[str, Any]) -> Dict[str, float | bool]:
    """Compute range, bearing, closest point of approach and time to CPA (hours)."""
    own_lat, own_lon = _value(own, "lat"), _value(own, "lon")
    target_lat, target_lon = _value(target, "lat"), _value(target, "lon")
    distance = haversine_nm(own_lat, own_lon, target_lat, target_lon)
    bearing = _bearing(own_lat, own_lon, target_lat, target_lon)
    own_course, target_course = _value(own, "cog_deg", _value(own, "heading")), _value(target, "cog_deg", _value(target, "heading"))
    relative_bearing = (bearing - own_course) % 360
    reciprocal = _bearing(target_lat, target_lon, own_lat, own_lon)
    aspect = (reciprocal - target_course) % 360
    # Equirectangular local range vector in nautical miles, sufficient for encounter ranges.
    north = (target_lat - own_lat) * 60.0
    east = (target_lon - own_lon) * 60.0 * cos(radians((own_lat + target_lat) / 2))
    own_v = _velocity(_value(own, "sog_knots"), own_course)
    target_v = _velocity(_value(target, "sog_knots"), target_course)
    relative_v = (target_v[0] - own_v[0], target_v[1] - own_v[1])
    speed_sq = relative_v[0] ** 2 + relative_v[1] ** 2
    tcpa = -(east * relative_v[0] + north * relative_v[1]) / speed_sq if speed_sq else 0.0
    cpa_east, cpa_north = east + relative_v[0] * tcpa, north + relative_v[1] * tcpa
    cpa = (cpa_east ** 2 + cpa_north ** 2) ** 0.5
    return {"distance_nm": distance, "relative_bearing_deg": relative_bearing, "aspect_deg": aspect,
            "cpa_nm": cpa, "tcpa_hours": tcpa, "converging": tcpa > 0 and cpa < distance}


def calculate_collision_risk_index(kinematics: Mapping[str, Any], safe_cpa_nm: float = 1.0, horizon_hours: float = 0.5) -> float:
    """Return a bounded 0--1 risk score based on CPA and positive TCPA."""
    cpa = max(0.0, float(kinematics.get("cpa_nm", 999)))
    tcpa = float(kinematics.get("tcpa_hours", 999))
    if tcpa <= 0:
        return 0.0
    cpa_factor = max(0.0, min(1.0, 1.0 - cpa / safe_cpa_nm))
    time_factor = max(0.0, min(1.0, 1.0 - tcpa / horizon_hours))
    return round(0.65 * cpa_factor + 0.35 * time_factor, 3)


def classify_colregs_encounter(own: Mapping[str, Any], target: Mapping[str, Any]) -> str:
    kinematics = compute_relative_kinematics(own, target)
    relative_bearing, aspect = kinematics["relative_bearing_deg"], kinematics["aspect_deg"]
    course_difference = abs((_value(own, "cog_deg") - _value(target, "cog_deg") + 180) % 360 - 180)
    if not kinematics["converging"] or kinematics["cpa_nm"] > 2.0:
        return "Safe"
    if relative_bearing <= 10 or relative_bearing >= 350:
        if course_difference >= 150:
            return "Head-on (Rule 14)"
    if 112.5 <= relative_bearing <= 247.5 and 112.5 <= aspect <= 247.5:
        return "Overtaking (Rule 13)"
    if 0 < relative_bearing < 112.5:
        return "Crossing Give-Way (Rule 15)"
    if 247.5 < relative_bearing < 360:
        return "Crossing Stand-On"
    return "Safe"
