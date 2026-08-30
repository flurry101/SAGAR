"""Integration test for Member 3 GIS and Risk Engine flow."""

import pytest
from app.gis.geocoder import geocode
from app.gis.trajectory import calculate_trajectory
from app.gis.geofence import check_geofence
from app.graph.nodes.geo import geo_node
from app.graph.nodes.risk import risk_node
from app.risk_engine.schemas import RiskLevel


def test_full_member3_pipeline_integration():
    # 1. Geocode ports
    origin_lat, origin_lon = geocode("Cochin")
    dest_lat, dest_lon = geocode("Mangalore")

    # 2. Calculate Trajectory
    traj = calculate_trajectory(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
        departure_time="2026-08-29T10:00:00Z",
        vessel_speed_knots=10.0,
        sample_interval_nm=20.0,
        fishing_duration_hours=2.0,
        origin_name="Cochin",
        destination_name="Mangalore",
    )
    assert len(traj.waypoints) > 0

    # 3. Check Geofence
    violations = check_geofence(traj.waypoints)

    # 4. LangGraph Nodes execution test
    graph_state = {
        "origin": "Cochin",
        "destination": "Mangalore",
        "departure_time": "2026-08-29T10:00:00Z",
        "vessel_speed_knots": 10.0,
        "vessel": {"beam_m": 4.0, "vessel_type": "trawler"},
        "environmental_observations": [
            {
                "waypoint_index": 0,
                "wave_height_m": 1.5,
                "wind_speed_knots": 12.0,
                "cyclone_warning": False,
            }
        ],
    }

    geo_result = geo_node(graph_state)
    assert "trajectory" in geo_result
    assert "geofence_violations" in geo_result

    # Merge state and call risk node
    graph_state.update(geo_result)
    risk_result = risk_node(graph_state)

    assert "risk_evidence" in risk_result
    assert "overall_risk_level" in risk_result
    assert risk_result["overall_risk_level"] in [lvl.value for lvl in RiskLevel]
