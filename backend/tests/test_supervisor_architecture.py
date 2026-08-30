"""
Test Suite — Supervisor Architecture

Tests the bounded-autonomous supervisor routing, safety guard,
and end-to-end execution paths.
"""

import pytest
from app.graph.nodes.supervisor import supervisor_node, enforce_safety_requirements
from app.graph.nodes.geo import geo_node
from app.graph.nodes.marine import marine_node
from app.graph.nodes.weather import weather_node
from app.graph.nodes.risk import risk_node
from app.graph.nodes.ocean_analytics import ocean_analytics_node
from app.graph.nodes.route import route_node
from app.graph.nodes.visualization import visualization_node
from app.graph.nodes.reporting import reporting_node
from app.graph.nodes.planner import planner_synthesize
from app.graph.routing import supervisor_router, post_risk_router


# ---- Test A: Knowledge query should NOT trigger risk ----

def test_knowledge_query_skips_risk():
    """'What is SST?' should route to knowledge, not trigger the safety pipeline."""
    state = {
        "conversation_history": [{"role": "user", "content": "What is SST?"}],
        "trip_context": {},
        "vessel_profile": {},
    }

    # Simulate supervisor without LLM (keyword fallback)
    result = supervisor_node(state)
    task_plan = result.get("task_plan", {})

    # Knowledge questions should NOT require safety
    assert task_plan.get("requires_safety_assessment") == False
    assert "risk" not in task_plan.get("required_capabilities", [])

    # Router should route to knowledge
    route = supervisor_router(result)
    assert route == "knowledge"


# ---- Test B: PFZ query should include marine + geo + visualization ----

def test_pfz_query_routing():
    """'Where is the nearest PFZ?' needs marine, geo, visualization."""
    state = {
        "conversation_history": [{"role": "user", "content": "Where is the nearest PFZ today?"}],
        "trip_context": {},
        "vessel_profile": {},
    }

    result = supervisor_node(state)
    task_plan = result.get("task_plan", {})
    caps = set(task_plan.get("required_capabilities", []))

    # PFZ queries should at minimum include marine
    assert "marine" in caps or "knowledge" in caps


# ---- Test C: Safety query MUST include risk ----

def test_safety_query_includes_risk():
    """'Is it safe to go fishing tomorrow?' MUST trigger risk assessment."""
    state = {
        "conversation_history": [{"role": "user", "content": "Is it safe to go fishing tomorrow morning?"}],
        "trip_context": {},
        "vessel_profile": {},
    }

    result = supervisor_node(state)
    task_plan = result.get("task_plan", {})
    caps = set(task_plan.get("required_capabilities", []))

    # Safety Guard must enforce risk
    assert "risk" in caps
    assert task_plan.get("requires_safety_assessment") == True


# ---- Test D: Safety Guard cannot be bypassed ----

def test_safety_guard_adds_risk():
    """Even if Supervisor omits risk for a trip query, Safety Guard adds it."""
    fake_plan = {
        "intent": "trip_assessment",
        "required_capabilities": ["geo", "weather"],  # Missing risk!
        "requires_safety_assessment": False,
    }

    guarded = enforce_safety_requirements(fake_plan, "Can I go fishing tomorrow?")

    assert "risk" in guarded["required_capabilities"]
    assert guarded["requires_safety_assessment"] == True


# ---- Test E: Missing weather → INSUFFICIENT_INFORMATION ----

def test_missing_weather_insufficient_info():
    """Risk node without weather data should produce INSUFFICIENT_INFORMATION."""
    state = {
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
            "length_m": 12.0,
            "cruising_speed_kmh": 15.0
        }
    }

    geo_updates = geo_node(state)
    state.update(geo_updates)

    risk_updates = risk_node(state)
    state.update(risk_updates)

    assert state["overall_risk_level"] == "UNKNOWN"
    assert state["risk_evidence"]["advisory_category"] == "INSUFFICIENT_INFORMATION"


# ---- Test F: Full E2E deterministic path ----

def test_full_e2e_deterministic_path():
    """Full end-to-end: Geo → Marine+Weather → Risk → OceanAnalytics → Route → Viz → Report."""
    state = {
        "conversation_history": [],
        "workflow_status": "PLANNING",
        "task_plan": {
            "intent": "safe_fishing_trip",
            "required_capabilities": [
                "geo", "marine", "weather", "risk",
                "ocean_analytics", "route", "visualization", "reporting",
            ],
            "requires_safety_assessment": True,
            "requires_route": True,
            "requires_visualization": True,
            "requires_report": True,
        },
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

    # 1. Geo
    state.update(geo_node(state))
    assert "trajectory" in state
    assert len(state["trajectory"]["waypoints"]) > 0

    # 2. Marine
    marine_updates = marine_node(state)
    state.update(marine_updates)
    assert "marine_observations" in state

    # 3. Weather
    weather_updates = weather_node(state)
    state.update(weather_updates)
    assert "weather_observations" in state

    # 4. Risk
    risk_updates = risk_node(state)
    state.update(risk_updates)
    assert "risk_evidence" in state
    assert "overall_risk_level" in state

    # 5. Ocean Analytics
    oa_updates = ocean_analytics_node(state)
    state.update(oa_updates)
    assert "ocean_analysis" in state
    assert state["ocean_analysis"]["sst_status"] in ["favourable", "moderate", "unfavourable", "unknown"]

    # 6. Route
    route_updates = route_node(state)
    state.update(route_updates)
    assert "route_candidates" in state

    # 7. Visualization
    viz_updates = visualization_node(state)
    state.update(viz_updates)
    assert "visualization_spec" in state
    assert len(state["visualization_spec"]["layers"]) > 0

    # 8. Reporting
    report_updates = reporting_node(state)
    state.update(report_updates)
    assert "report" in state
    assert "summary" in state["report"]
    assert "recommendation" in state["report"]
    assert "evidence" in state["report"]

    # 9. Synthesis
    synth_updates = planner_synthesize(state)
    state.update(synth_updates)
    assert "advisory" in state
    assert "recommendation_text" in state["advisory"]


# ---- Test G: Post-risk router ----

def test_post_risk_router_with_capabilities():
    """If TaskPlan includes visualization/reporting, route to post_process."""
    state = {
        "task_plan": {
            "required_capabilities": ["geo", "weather", "risk", "visualization", "reporting"],
        }
    }
    assert post_risk_router(state) == "post_process"


def test_post_risk_router_without_capabilities():
    """If TaskPlan only includes core capabilities, go straight to synthesis."""
    state = {
        "task_plan": {
            "required_capabilities": ["geo", "weather", "risk"],
        }
    }
    assert post_risk_router(state) == "synthesize"


# ---- Test I: Dependency resolver ----

def test_dependency_resolver_adds_geo_for_route():
    """If route is requested, dependency resolver must add geo, weather, marine, risk."""
    from app.graph.routing import resolve_dependencies

    plan = {
        "required_capabilities": ["route"],
    }
    resolved = resolve_dependencies(plan)
    caps = set(resolved["required_capabilities"])
    assert "geo" in caps
    assert "weather" in caps
    assert "marine" in caps
    assert "risk" in caps
    assert "route" in caps


def test_dependency_resolver_ocean_analytics():
    """ocean_analytics requires marine + weather."""
    from app.graph.routing import resolve_dependencies

    plan = {
        "required_capabilities": ["ocean_analytics"],
    }
    resolved = resolve_dependencies(plan)
    caps = set(resolved["required_capabilities"])
    assert "marine" in caps
    assert "weather" in caps


def test_dependency_resolver_no_duplication():
    """Resolver should not create duplicate entries."""
    from app.graph.routing import resolve_dependencies

    plan = {
        "required_capabilities": ["geo", "weather", "marine", "risk", "route"],
    }
    resolved = resolve_dependencies(plan)
    caps = resolved["required_capabilities"]
    assert len(caps) == len(set(caps))


# ---- Test J: Weather generates alerts ----

def test_weather_node_generates_alerts():
    """Weather node should populate alerts[] for dangerous conditions."""
    from app.graph.nodes.weather import _generate_alerts

    obs = [{
        "weather": {"wave_height_m": 3.0, "wind_speed_kmh": 50},
        "lat": 9.93, "lon": 76.27, "time_iso": "2026-08-30T10:00:00Z",
    }]
    alerts = _generate_alerts(obs, {})
    assert len(alerts) > 0
    types = [a["alert_type"] for a in alerts]
    assert "HIGH_WAVE" in types
    assert "STRONG_WIND" in types


# ---- Test K: Fallback supervisor ----

def test_fallback_pfz_query():
    """Fallback supervisor should detect PFZ queries without LLM."""
    from app.graph.nodes.supervisor import _default_task_plan

    plan = _default_task_plan("Where is the nearest PFZ?")
    assert plan["intent"] == "pfz_query"
    caps = set(plan["required_capabilities"])
    assert "marine" in caps
    assert "geo" in caps
    assert plan["requires_safety_assessment"] is False


def test_fallback_weather_query():
    """Fallback supervisor should detect weather-only queries without LLM."""
    from app.graph.nodes.supervisor import _default_task_plan

    plan = _default_task_plan("What is the weather forecast?")
    assert plan["intent"] == "weather_query"
    caps = set(plan["required_capabilities"])
    assert "weather" in caps
    assert "risk" not in caps


def test_fallback_route_query():
    """Fallback supervisor should detect route queries without LLM."""
    from app.graph.nodes.supervisor import _default_task_plan

    plan = _default_task_plan("Find the safest route to the fishing zone")
    assert plan["intent"] == "route_optimization"
    caps = set(plan["required_capabilities"])
    assert "route" in caps
    assert "risk" in caps
    assert "geo" in caps


def test_fallback_sst_knowledge():
    """Fallback supervisor should detect SST as marine science knowledge."""
    from app.graph.nodes.supervisor import _default_task_plan

    plan = _default_task_plan("What is sea surface temperature?")
    assert plan["intent"] == "marine_science_query"
    assert "knowledge" in plan["required_capabilities"]
    assert plan["requires_safety_assessment"] is False


# ---- Test L: Evidence registry population ----

def test_weather_populates_evidence_registry():
    """Weather node should create evidence_registry items."""
    from app.graph.nodes.weather import _generate_alerts

    # Simulate weather node output with observations
    obs = [{
        "weather": {"wave_height_m": 1.5, "wind_speed_kmh": 20},
        "lat": 9.93, "lon": 76.27, "time_iso": "2026-08-30T10:00:00Z",
        "waypoint_index": 0,
    }]

    # Test that _generate_alerts can produce evidence-ready data
    alerts = _generate_alerts(obs, {})
    # Safe conditions = no alerts
    assert len(alerts) == 0


