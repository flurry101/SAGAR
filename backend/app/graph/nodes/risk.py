"""
LangGraph RISK Node wrapper.
Applies deterministic safety rules against Trajectory and Environmental observations.
"""

from typing import Dict, Any, List
from app.risk_engine.schemas import RiskInput, VesselProfile, EnvironmentalObservation
from app.risk_engine.engine import RiskEngine


def risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for Risk Engine evaluation.

    Input state keys expected:
        - trajectory: dict matching Trajectory schema
        - vessel: dict matching VesselProfile schema
        - environmental_observations: list of dicts matching EnvironmentalObservation
        - geofence_violations: list of violation dicts

    Returns updated state with:
        - risk_evidence: dict / RiskEvidence dump
        - overall_risk_level: str
    """
    vessel_data = state.get("vessel", {})
    vessel = VesselProfile(**vessel_data) if vessel_data else VesselProfile(beam_m=4.0)

    obs_data = state.get("environmental_observations", [])
    observations: List[EnvironmentalObservation] = [
        EnvironmentalObservation(**obs) for obs in obs_data
    ]

    violations = state.get("geofence_violations", [])
    traj_data = state.get("trajectory")

    risk_input = RiskInput(
        vessel=vessel,
        trajectory=traj_data,
        environmental_observations=observations,
        geofence_violations=violations,
    )

    engine = RiskEngine()
    evidence = engine.evaluate(risk_input)

    return {
        "risk_evidence": evidence.model_dump(),
        "overall_risk_level": evidence.overall_risk_level.value,
    }
