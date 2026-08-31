# attr: m1
# [integration tests for fastapi api endpoints]
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.api.chat import get_graph
from app.api.copilot import get_copilot_chat_runner

client = TestClient(app)


def test_root_and_health_endpoints():
    # [test basic health check routes]
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
    # [verify x-request-id is returned in response headers]
    res = client.get("/api/v1/health", headers={"X-Request-ID": "custom-uuid-999"})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == "custom-uuid-999"


def test_chat_trip_planner_endpoint():
    # [test post /api/v1/chat invocation using dependency override]
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
        "overall_risk_level": "LOW",
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
        assert data["data"]["advisory"]["advisory_category"] == "CONDITIONS_FAVORABLE"
        assert "X-Request-ID" in res.headers
    finally:
        app.dependency_overrides.pop(get_graph, None)


def test_copilot_chat_endpoint():
    # [test post /api/v1/copilot invocation with mock runner]
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


@patch("app.api.assessment.get_assessment_by_id")
def test_assessment_retrieval_endpoint(mock_get_assessment):
    # [test get /api/v1/assessment/{id}]
    mock_get_assessment.return_value = {
        "assessment_id": "assess-uuid-456",
        "trip_id": "trip-uuid-456",
        "origin": "Kochi",
        "overall_risk_level": "MODERATE",
        "workflow_status": "COMPLETED",
        "advisories": [{"recommendation_text": "Proceed with caution."}],
    }

    res = client.get("/api/v1/assessment/assess-uuid-456")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["data"]["assessment_id"] == "assess-uuid-456"
    assert data["data"]["origin"] == "Kochi"


@patch("app.api.assessment.get_assessment_by_id")
def test_assessment_not_found(mock_get_assessment):
    # [test get /api/v1/assessment/{id} 404 behavior]
    mock_get_assessment.return_value = None

    res = client.get("/api/v1/assessment/nonexistent-id")
    assert res.status_code == 404
    data = res.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "HTTP_ERROR"


@patch("app.api.vessel.get_vessel_by_id")
def test_vessel_endpoints(mock_get_vessel):
    # [test get /api/v1/vessel/{id}]
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
# attr: m1

