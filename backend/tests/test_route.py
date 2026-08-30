"""
Test Suite — Route Optimization

Tests multi-candidate route generation, scoring, and selection.
"""

import pytest
from app.graph.nodes.route import route_node, _score_route, _offset_waypoints


# ---- Test A: Multi-candidate generation ----

def test_multi_candidate_routes():
    """Route node should generate 3 candidates (primary, coastal, offshore)."""
    state = {
        "trajectory": {
            "waypoints": [
                {"lat": 9.93, "lon": 76.27, "eta_iso": "2026-08-30T10:00:00Z"},
                {"lat": 10.0, "lon": 76.5, "eta_iso": "2026-08-30T12:00:00Z"},
                {"lat": 10.1, "lon": 76.7, "eta_iso": "2026-08-30T14:00:00Z"},
            ],
            "total_distance_nm": 30.0,
            "total_duration_hours": 4.0,
        },
        "weather_observations": [
            {"weather": {"wave_height_m": 1.0, "wind_speed_kmh": 15}, "lat": 9.93, "lon": 76.27, "time_iso": "2026-08-30T10:00:00Z"},
        ],
        "geofence_results": [],
        "spatial_constraints": [],
        "task_plan": {"required_capabilities": ["route"]},
    }

    updates = route_node(state)
    candidates = updates["route_candidates"]

    assert len(candidates) == 3
    ids = [c["route_id"] for c in candidates]
    assert "primary" in ids
    assert "coastal" in ids
    assert "offshore" in ids


# ---- Test B: Best route selected ----

def test_best_route_selected():
    """Exactly one route should be selected as best."""
    state = {
        "trajectory": {
            "waypoints": [{"lat": 9.93, "lon": 76.27, "eta_iso": "2026-08-30T10:00:00Z"}],
            "total_distance_nm": 10.0,
            "total_duration_hours": 2.0,
        },
        "weather_observations": [],
        "geofence_results": [],
        "spatial_constraints": [],
        "task_plan": {"required_capabilities": ["route"]},
    }

    updates = route_node(state)
    selected = [c for c in updates["route_candidates"] if c["selected"]]
    assert len(selected) == 1


# ---- Test C: Geofence violation lowers safety score ----

def test_geofence_penalty():
    """Route with geofence violations should have lower safety score."""
    wps = [{"lat": 9.93, "lon": 76.27}]
    weather = [{"weather": {"wave_height_m": 1.0, "wind_speed_kmh": 10}}]
    traj = {"total_distance_nm": 10.0, "total_duration_hours": 2.0}

    clean_route = _score_route("clean", wps, weather, [], traj, "Clean")
    violated_route = _score_route("violated", wps, weather, [{"zone": "restricted"}], traj, "Violated")

    assert clean_route["safety_score"] > violated_route["safety_score"]
    assert clean_route["geofence_clear"] is True
    assert violated_route["geofence_clear"] is False


# ---- Test D: No trajectory → empty candidates ----

def test_no_trajectory_empty_candidates():
    """Without trajectory, route node should return empty candidates."""
    state = {
        "trajectory": {},
        "weather_observations": [],
        "geofence_results": [],
        "task_plan": {"required_capabilities": ["route"]},
    }

    updates = route_node(state)
    assert updates["route_candidates"] == []


# ---- Test E: Offset waypoints ----

def test_offset_waypoints():
    """Coastal offset should move latitude closer to equator."""
    wps = [{"lat": 10.0, "lon": 76.0}]
    coastal = _offset_waypoints(wps, offset_nm=-10.0)
    offshore = _offset_waypoints(wps, offset_nm=10.0)

    # Coastal offset (-10nm → ~-0.167 deg)
    assert coastal[0]["lat"] < wps[0]["lat"]
    # Offshore offset (+10nm → ~+0.167 deg)
    assert offshore[0]["lat"] > wps[0]["lat"]
