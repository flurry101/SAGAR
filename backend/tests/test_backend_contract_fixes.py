"""Focused regression checks for the backend data-contract fixes."""

from app.gis.trajectory import calculate_trajectory
from app.graph.nodes.geo import geo_node
from app.graph.nodes.risk import risk_node
from app.tools.weather_tools import fetch_weather_forecast_batch


def test_geo_node_sets_origin_coordinates_and_bbox():
    state = {
        "trip_context": {
            "origin": "Mangalore",
            "departure_time_iso": "2026-09-01T08:00:00Z",
        },
        "vessel_profile": {"cruising_speed_kmh": 12.0},
    }

    original = state.copy()
    result = geo_node(state)

    assert result["trip_context"]["origin_lat"] is not None
    assert result["trip_context"]["origin_lon"] is not None
    assert isinstance(result["bbox"], dict)
    assert {"lat_min", "lat_max", "lon_min", "lon_max"}.issubset(result["bbox"].keys())
    assert result["trip_context"] != original["trip_context"]


def test_weather_batch_accepts_legacy_trajectory_waypoint_contract():
    waypoints = [
        {
            "waypoint_index": 0,
            "lat": 12.87,
            "lon": 74.88,
            "timestamp": "2026-09-01T08:00:00Z",
            "leg_label": "outbound",
        }
    ]

    observations = fetch_weather_forecast_batch(waypoints)

    assert observations[0]["time_iso"] == "2026-09-01T08:00:00Z"
    assert observations[0]["phase"] == "OUTBOUND"


def test_risk_node_uses_hazard_alerts_and_sets_cyclone_override():
    trajectory = calculate_trajectory(
        origin_lat=12.8,
        origin_lon=74.8,
        dest_lat=13.1,
        dest_lon=74.9,
        departure_time="2026-09-01T08:00:00Z",
        vessel_speed_knots=5.0,
        sample_interval_nm=20.0,
        fishing_duration_hours=1.0,
    )

    state = {
        "trajectory": trajectory.model_dump(),
        "vessel_profile": {"beam_width_m": 4.0, "length_m": 10.0, "cruising_speed_kmh": 15.0},
        "weather_observations": [
            {
                "waypoint_index": 0,
                "lat": 12.8,
                "lon": 74.8,
                "time_iso": "2026-09-01T08:00:00Z",
                "weather": {"wind_speed_kmh": 30.0, "wave_height_m": 1.0},
            }
        ],
        "hazard_alerts": {"cyclone_active": True, "hazards": []},
        "marine_observations": [
            {
                "waypoint_index": 0,
                "lat": 12.8,
                "lon": 74.8,
                "time_iso": "2026-09-01T08:00:00Z",
                "marine": {"depth_m": 30.0, "tide_height_m": 1.0},
            }
        ],
    }

    result = risk_node(state)

    assert result["overall_risk_level"] == "SEVERE"
    assert result["risk_evidence"]["overall_risk_level"] == "SEVERE"


def test_live_marine_pfz_uses_adapter_fetch_data():
    from app.chatbot.tools import live_data_tools

    def fake_fetch_data(lat, lon, timestamp=None, radius_km=100.0, **kwargs):
        return {"pfzs": [{"pfz_id": "x", "coordinates": {"lat": lat, "lon": lon}}], "resolved": True}

    import app.adapters.static_pfz_adapter as static_pfz

    original = static_pfz.StaticPFZAdapter.fetch_data
    static_pfz.StaticPFZAdapter.fetch_data = fake_fetch_data
    try:
        data = live_data_tools.get_live_marine_conditions(12.8, 74.8)
    finally:
        static_pfz.StaticPFZAdapter.fetch_data = original

    assert data["pfz"]["count"] >= 1
