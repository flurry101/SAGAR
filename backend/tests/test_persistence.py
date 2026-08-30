"""
Test Suite — Persistence Repository

Tests the assessment repository with mocked Supabase client.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.repositories.assessment_repository import persist_assessment


# ---- Test A: Supabase not configured → graceful response ----

def test_persist_supabase_not_configured():
    """When Supabase is not configured, persistence should return supabase_not_configured."""
    state = {
        "trip_context": {"origin": "Kochi"},
        "risk_evidence": {"advisory_category": "SAFE"},
        "overall_risk_level": "SAFE",
    }

    with patch("app.repositories.assessment_repository._get_client", return_value=None):
        result = persist_assessment(state)

    assert result["persistence_status"] == "supabase_not_configured"
    assert result["tables_written"] == []


# ---- Test B: Successful persistence ----

def test_persist_successful():
    """With a working Supabase client, all tables should be written."""
    mock_client = MagicMock()
    mock_execute = MagicMock()
    mock_execute.execute.return_value = MagicMock(data=[{"id": "test"}])

    mock_client.table.return_value.insert.return_value = mock_execute

    state = {
        "trip_context": {"origin": "Kochi", "departure_time_iso": "2026-08-30T10:00:00Z"},
        "risk_evidence": {"advisory_category": "SAFE", "summary": "Safe conditions."},
        "overall_risk_level": "SAFE",
        "workflow_status": "ADVISORY_READY",
        "weather_observations": [{"waypoint_index": 0, "lat": 9.93, "lon": 76.27, "time_iso": "2026-08-30T10:00:00Z", "weather": {}}],
        "marine_observations": [{"lat": 9.93, "lon": 76.27, "marine": {}}],
        "advisory": {"advisory_category": "SAFE", "recommendation_text": "All clear."},
        "agent_executions": [{"agent_name": "geo", "status": "completed"}],
        "task_plan": {"intent": "trip_assessment"},
    }

    with patch("app.repositories.assessment_repository._get_client", return_value=mock_client):
        result = persist_assessment(state)

    assert result["persistence_status"] == "success"
    assert "assessments" in result["tables_written"]
    assert "risk_evidence" in result["tables_written"]
    assert "advisories" in result["tables_written"]


# ---- Test C: Partial persistence (some tables fail) ----

def test_persist_partial():
    """If some tables fail, status should be 'partial'."""
    mock_client = MagicMock()

    # Make assessments succeed but risk_evidence fail
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "risk_evidence":
            mock_table.insert.side_effect = Exception("Connection timeout")
        else:
            mock_execute = MagicMock()
            mock_execute.execute.return_value = MagicMock(data=[{"id": "test"}])
            mock_table.insert.return_value = mock_execute
        return mock_table

    mock_client.table.side_effect = table_side_effect

    state = {
        "trip_context": {"origin": "Kochi"},
        "risk_evidence": {"advisory_category": "SAFE"},
        "overall_risk_level": "SAFE",
        "workflow_status": "ADVISORY_READY",
        "advisory": {"advisory_category": "SAFE", "recommendation_text": "OK"},
        "task_plan": {"intent": "trip"},
    }

    with patch("app.repositories.assessment_repository._get_client", return_value=mock_client):
        result = persist_assessment(state)

    assert result["persistence_status"] == "partial"
    assert "assessments" in result["tables_written"]
    assert len(result["errors"]) > 0


# ---- Test D: Persistence failure does not corrupt risk decision ----

def test_persist_failure_preserves_risk():
    """Even if persistence fails completely, the risk decision is not altered."""
    state = {
        "trip_context": {"origin": "Kochi"},
        "risk_evidence": {"advisory_category": "SEVERE"},
        "overall_risk_level": "SEVERE",
        "workflow_status": "ADVISORY_READY",
        "advisory": {"advisory_category": "SEVERE", "recommendation_text": "Do not go."},
    }

    # Simulate DB being down — _get_client returns None
    with patch("app.repositories.assessment_repository._get_client", return_value=None):
        result = persist_assessment(state)

    # Persistence should report not configured, but risk decision is untouched
    assert result["persistence_status"] == "supabase_not_configured"
    assert state["overall_risk_level"] == "SEVERE"
    assert state["risk_evidence"]["advisory_category"] == "SEVERE"
