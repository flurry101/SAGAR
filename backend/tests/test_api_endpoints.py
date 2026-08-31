import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


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


def test_assessment_get_endpoint():
    response = client.get("/api/v1/assessment/nonexistent-id")
    assert response.status_code in (200, 404)


@patch("app.api.copilot.copilot_chat")
def test_copilot_endpoint(mock_chat):
    mock_chat.return_value = {
        "response": "The wave threshold is calculated based on SVAS formula.",
        "tool_calls": []
    }
    payload = {
        "message": "What is the wave safety threshold?"
    }
    response = client.post("/api/v1/copilot", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    assert "SVAS formula" in res_json["data"]["response"]


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


def test_chat_alias_endpoint():
    payload = {
        "message": "Is it safe to go to PFZ from Kochi tomorrow?",
        "language": "en"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] in ("success", "needs_clarification", "insufficient_information")
