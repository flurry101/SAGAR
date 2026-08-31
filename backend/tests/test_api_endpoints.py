from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.trip import get_graph
from app.api.copilot import get_copilot_chat_runner

client = TestClient(app)


def test_root_and_health_endpoints():
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "ok"

    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    res_ready = client.get("/api/v1/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


def test_request_id_middleware():
    res = client.get("/api/v1/health", headers={"X-Request-ID": "custom-uuid-999"})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == "custom-uuid-999"


def test_weather_forecast_endpoint():
    payload = {
        "waypoints": [
            {"waypoint_index": 0, "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-31T05:00:00Z"}
        ]
    }
    response = client.post("/api/v1/weather/forecast", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    assert "observations" in res_json["data"]


def test_weather_hazards_endpoint():
    payload = {
        "bbox": {"lat_min": 10.0, "lat_max": 15.0, "lon_min": 70.0, "lon_max": 76.0}
    }
    response = client.post("/api/v1/weather/hazards", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    assert "hazards" in res_json["data"]


def test_marine_pfz_endpoint():
    payload = {
        "origin": {"lat": 12.87, "lon": 74.84},
        "radius_km": 100.0
    }
    response = client.post("/api/v1/marine/pfz", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    assert "pfzs" in res_json["data"]


def test_marine_observations_endpoint():
    payload = {
        "waypoints": [
            {"waypoint_index": 0, "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-31T05:00:00Z"}
        ]
    }
    response = client.post("/api/v1/marine/observations", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    assert "observations" in res_json["data"]


def test_risk_evaluate_endpoint():
    payload = {
        "vessel": {
            "beam_m": 4.5,
            "draft_m": 1.5,
            "length_m": 12.0
        },
        "environmental_observations": [
            {
                "waypoint_index": 0,
                "wave_height_m": 0.8,
                "wind_speed_kmh": 25.0,
                "depth_m": 15.0,
                "tide_height_m": 0.5
            }
        ]
    }
    response = client.post("/api/v1/risk/evaluate", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    assert res_json["data"]["overall_risk_level"] == "SAFE"


def test_copilot_chat_endpoint():
    mock_runner = AsyncMock()
    mock_runner.return_value = {
        "response": "Potential Fishing Zones (PFZ) are identified using satellite ocean data.",
        "tool_calls": [{"tool": "search_marine_knowledge", "args": {"query": "pfz"}}],
    }

    app.dependency_overrides[get_copilot_chat_runner] = lambda: mock_runner

    try:
        payload = {
            "message": "What is a PFZ?",
        }

        res = client.post("/api/v1/copilot", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "Potential Fishing Zones" in data["data"]["response"]
        assert len(data["data"]["tool_calls"]) == 1
    finally:
        app.dependency_overrides.pop(get_copilot_chat_runner, None)


def test_chat_trip_planner_endpoint():
    mock_graph = AsyncMock()
    mock_graph.ainvoke.return_value = {
        "workflow_status": "ADVISORY_READY",
        "trip_context": {"trip_id": "trip-test-123", "origin": "Mangalore"},
        "advisory": {
            "advisory_category": "CONDITIONS_FAVORABLE",
            "recommendation_text": "Conditions are safe for fishing trip.",
            "disclaimer": "Safety disclaimer.",
            "language": "en",
        },
        "overall_risk_level": "SAFE",
    }

    app.dependency_overrides[get_graph] = lambda: mock_graph

    try:
        payload = {
            "message": "I want to go fishing from Mangalore at 5 AM",
            "language": "en",
        }

        res = client.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["data"]["trip_id"] == "trip-test-123"
        assert "X-Request-ID" in res.headers
    finally:
        app.dependency_overrides.pop(get_graph, None)


def test_trip_assess_endpoint():
    payload = {
        "message": "I want to leave Mangalore at 5 AM tomorrow for fishing and return at 2 PM.",
        "language": "en"
    }
    response = client.post("/api/v1/trip/assess", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] in ("success", "needs_clarification", "insufficient_information")
    assert "workflow_status" in res_json["data"]


def test_assessment_get_endpoint():
    response = client.get("/api/v1/assessment/nonexistent-id")
    assert response.status_code in (200, 404)


@patch("app.api.vessel.get_vessel_by_id")
def test_vessel_endpoints(mock_get_vessel):
    mock_get_vessel.return_value = {
        "id": "vessel-789",
        "vessel_type": "mechanized_trawler",
        "beam_width_m": 4.2,
        "cruising_speed_kmh": 16.0,
        "has_ais": True,
    }

    res = client.get("/api/v1/vessel/vessel-789")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["data"]["beam_width_m"] == 4.2
