"""
LangGraph RISK Node wrapper.
Applies deterministic safety rules against Trajectory and Environmental observations.

Bridges M4 weather/marine output format into M3 RiskEngine input format.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from app.risk_engine.schemas import RiskInput, VesselProfile, EnvironmentalObservation
from app.risk_engine.engine import RiskEngine


def _build_environmental_observations(state: Dict[str, Any]) -> List[EnvironmentalObservation]:
    """Bridge M4's separate weather/marine observations into RiskEngine format.

    M4 writes:
        state["weather_observations"] → list of {waypoint_index, phase, lat, lon, time_iso, weather: {...}}
        state["marine_observations"] → list of {waypoint_index, phase, lat, lon, time_iso, marine: {...}}

    RiskEngine expects:
        List[EnvironmentalObservation] with wave_height_m, wind_speed_knots, cyclone_warning, etc.
    """
    observations: List[EnvironmentalObservation] = []

    # Index marine observations by waypoint_index for merging
    marine_by_idx: Dict[int, Dict[str, Any]] = {}
    for m_obs in state.get("marine_observations", []):
        idx = m_obs.get("waypoint_index", 0)
        marine_by_idx[idx] = m_obs.get("marine", {})

    hazard_alerts = state.get("hazard_alerts") or {}
    cyclone_active = bool(hazard_alerts.get("cyclone_active", False))

    for w_obs in state.get("weather_observations", []):
        idx = w_obs.get("waypoint_index", 0)
        weather = w_obs.get("weather", {})
        marine = marine_by_idx.get(idx, {})

        # Convert wind_speed_kmh to knots (1 knot ≈ 1.852 km/h)
        wind_kmh = weather.get("wind_speed_kmh")
        wind_knots = round(wind_kmh / 1.852, 2) if wind_kmh is not None else None

        observations.append(EnvironmentalObservation(
            waypoint_index=idx,
            timestamp=w_obs.get("time_iso"),
            lat=w_obs.get("lat"),
            lon=w_obs.get("lon"),
            wave_height_m=weather.get("wave_height_m"),
            wind_speed_knots=wind_knots,
            wind_speed_kmh=wind_kmh,
            gust_speed_kmh=weather.get("gust_speed_kmh"),
            depth_m=marine.get("depth_m"),
            tide_height_m=marine.get("tide_height_m"),
            visibility_km=weather.get("visibility_km"),
            cyclone_warning=bool(weather.get("cyclone_alert", False)) or cyclone_active,
            cyclone_details={"source": hazard_alerts.get("provenance", {}).get("source"), "cyclone_active": cyclone_active},
        ))

    return observations


def risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for Risk Engine evaluation.

    Input state keys (matching OrcaState):
        - trajectory: dict matching Trajectory schema (from geo_node)
        - vessel_profile: dict matching VesselProfile schema (from planner)
        - weather_observations: list from weather_node (M4 format)
        - marine_observations: list from marine_node (M4 format)
        - geofence_results: list of violation dicts (from geo_node)

    Returns updated state with:
        - risk_evidence: dict / RiskEvidence dump
        - overall_risk_level: str
    """
    # Read vessel_profile (OrcaState key), not "vessel"
    vessel_data = state.get("vessel_profile", {})
    if vessel_data:
        # Map OrcaState VesselProfile field names to RiskEngine VesselProfile
        vessel = VesselProfile(
            beam_m=vessel_data.get("beam_width_m"),
            draft_m=vessel_data.get("draft_m"),
            length_m=vessel_data.get("length_m"),
            vessel_type=vessel_data.get("vessel_type"),
            max_speed_knots=vessel_data.get("cruising_speed_kmh", 10.0) / 1.852,
        )
    else:
        vessel = VesselProfile(beam_m=4.0)

    # Bridge M4's separate weather/marine observations into RiskEngine format
    observations = _build_environmental_observations(state)

    # Read geofence_results (OrcaState key), not "geofence_violations"
    violations = state.get("geofence_results", [])
    traj_data = state.get("trajectory")

    risk_input = RiskInput(
        vessel=vessel,
        trajectory=traj_data,
        environmental_observations=observations,
        geofence_violations=violations,
    )

    engine = RiskEngine()
    evidence = engine.evaluate(risk_input)
    
    evidence_dump = evidence.model_dump()
    overall_risk_value = getattr(evidence.overall_risk_level, "value", evidence.overall_risk_level)
    overall_risk = str(overall_risk_value)

    if overall_risk == "UNKNOWN":
        evidence_dump["advisory_category"] = "INSUFFICIENT_INFORMATION"
    elif overall_risk in {"SEVERE", "HIGH"}:
        evidence_dump["advisory_category"] = "ELEVATED_RISK_IDENTIFIED"
    else:
        evidence_dump["advisory_category"] = "FAVORABLE"
        
    updates = {
        "risk_evidence": evidence_dump,
        "overall_risk_level": overall_risk,
    }
    
    updates["agent_executions"] = [{
        "agent_name": "risk",
        "status": "completed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": ["deterministic_rules"],
        "output_summary": f"Risk level assessed as {overall_risk}. {evidence.summary}"
    }]

    return updates

