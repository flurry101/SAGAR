import pytest
from app.graph.builder import get_compiled_graph
from app.graph.nodes.geo import geo_node
from app.graph.nodes.marine import marine_node
from app.graph.nodes.weather import weather_node
from app.graph.nodes.risk import risk_node
from app.graph.nodes.planner import planner_synthesize

def test_graph_valid_trip_e2e():
    """Test valid trip end-to-end deterministic execution path (Geo -> Marine+Weather -> Risk)."""
    initial_state = {
        "conversation_history": [],
        "workflow_status": "PLANNING",
        "trip_context": {
            "origin": "Kochi",
            "origin_lat": 9.9312,
            "origin_lon": 76.2673,
            "departure_time_iso": "2026-08-30T10:00:00Z"
        },
        "vessel_profile": {
            "vessel_type": "fishing_boat",
            "beam_width_m": 4.0,
            "length_m": 12.0,
            "cruising_speed_kmh": 15.0
        }
    }
    
    # 1. Geo Node
    geo_updates = geo_node(initial_state)
    initial_state.update(geo_updates)
    assert "trajectory" in initial_state
    assert len(initial_state["trajectory"]["waypoints"]) > 0
    assert "spatial_constraints" in initial_state
    
    # 2. Marine Node
    marine_updates = marine_node(initial_state)
    initial_state.update(marine_updates)
    assert "marine_observations" in initial_state
    
    # 3. Weather Node
    weather_updates = weather_node(initial_state)
    initial_state.update(weather_updates)
    assert "weather_observations" in initial_state
    assert "hazard_alerts" in initial_state
    
    # 4. Risk Node
    risk_updates = risk_node(initial_state)
    initial_state.update(risk_updates)
    assert "risk_evidence" in initial_state
    assert "overall_risk_level" in initial_state
    assert initial_state["risk_evidence"]["advisory_category"] in ["FAVORABLE", "ELEVATED_RISK_IDENTIFIED", "INSUFFICIENT_INFORMATION"]
    
    # 5. Planner Synthesize
    planner_updates = planner_synthesize(initial_state)
    initial_state.update(planner_updates)
    assert "advisory" in initial_state
    assert "recommendation_text" in initial_state["advisory"]


def test_graph_insufficient_info():
    """Test Risk node correctly outputs INSUFFICIENT_INFORMATION when missing data."""
    initial_state = {
        "conversation_history": [],
        "workflow_status": "PLANNING",
        "trip_context": {
            "origin": "Kochi",
            "origin_lat": 9.9312,
            "origin_lon": 76.2673,
            "departure_time_iso": "2026-08-30T10:00:00Z"
        },
        # Missing vessel profile beam width
        "vessel_profile": {
            "vessel_type": "fishing_boat",
            "length_m": 12.0,
            "cruising_speed_kmh": 15.0
        }
    }
    
    # 1. Geo Node
    geo_updates = geo_node(initial_state)
    initial_state.update(geo_updates)
    
    # 2. Risk Node (without weather/marine data to force insufficient info)
    risk_updates = risk_node(initial_state)
    initial_state.update(risk_updates)
    
    assert initial_state["overall_risk_level"] == "UNKNOWN"
    assert initial_state["risk_evidence"]["advisory_category"] == "INSUFFICIENT_INFORMATION"
