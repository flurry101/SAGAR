import pytest
from app.risk_engine.schemas import (
    RiskInput,
    VesselProfile,
    EnvironmentalObservation,
    RiskLevel,
    RuleStatus,
)
from app.risk_engine.engine import RiskEngine
from app.risk_engine.rules.wind_rule import WindLimitRule
from app.risk_engine.rules.bathymetry_rule import BathymetryGroundingRule
from app.risk_engine.rules.tidal_rule import TidalClearanceRule


def test_wind_rule_severe():
    rule = WindLimitRule()
    risk_input = RiskInput(
        environmental_observations=[
            EnvironmentalObservation(waypoint_index=0, wind_speed_kmh=65.0)
        ]
    )
    result = rule.evaluate(risk_input)
    assert result.status == RuleStatus.FAILED
    assert result.risk_level == RiskLevel.SEVERE


def test_wind_rule_high():
    rule = WindLimitRule()
    risk_input = RiskInput(
        environmental_observations=[
            EnvironmentalObservation(waypoint_index=0, wind_speed_kmh=45.0)
        ]
    )
    result = rule.evaluate(risk_input)
    assert result.status == RuleStatus.FAILED
    assert result.risk_level == RiskLevel.HIGH


def test_wind_rule_safe():
    rule = WindLimitRule()
    risk_input = RiskInput(
        environmental_observations=[
            EnvironmentalObservation(waypoint_index=0, wind_speed_kmh=20.0)
        ]
    )
    result = rule.evaluate(risk_input)
    assert result.status == RuleStatus.PASSED
    assert result.risk_level == RiskLevel.SAFE


def test_bathymetry_rule_grounding():
    rule = BathymetryGroundingRule()
    risk_input = RiskInput(
        vessel=VesselProfile(draft_m=2.0),
        environmental_observations=[
            EnvironmentalObservation(waypoint_index=0, depth_m=1.8)
        ]
    )
    result = rule.evaluate(risk_input)
    assert result.status == RuleStatus.FAILED
    assert result.risk_level == RiskLevel.SEVERE


def test_bathymetry_rule_shallow():
    rule = BathymetryGroundingRule()
    risk_input = RiskInput(
        vessel=VesselProfile(draft_m=2.0),
        environmental_observations=[
            EnvironmentalObservation(waypoint_index=0, depth_m=2.6)
        ]
    )
    result = rule.evaluate(risk_input)
    assert result.status == RuleStatus.FAILED
    assert result.risk_level == RiskLevel.HIGH


def test_bathymetry_rule_safe():
    rule = BathymetryGroundingRule()
    risk_input = RiskInput(
        vessel=VesselProfile(draft_m=2.0),
        environmental_observations=[
            EnvironmentalObservation(waypoint_index=0, depth_m=10.0)
        ]
    )
    result = rule.evaluate(risk_input)
    assert result.status == RuleStatus.PASSED
    assert result.risk_level == RiskLevel.SAFE


def test_tidal_rule_extreme_low_tide():
    rule = TidalClearanceRule()
    risk_input = RiskInput(
        environmental_observations=[
            EnvironmentalObservation(waypoint_index=0, tide_height_m=-1.5)
        ]
    )
    result = rule.evaluate(risk_input)
    assert result.status == RuleStatus.FAILED
    assert result.risk_level == RiskLevel.HIGH


def test_tidal_rule_safe():
    rule = TidalClearanceRule()
    risk_input = RiskInput(
        environmental_observations=[
            EnvironmentalObservation(waypoint_index=0, tide_height_m=1.2)
        ]
    )
    result = rule.evaluate(risk_input)
    assert result.status == RuleStatus.PASSED
    assert result.risk_level == RiskLevel.SAFE


def test_full_risk_engine_with_all_rules():
    engine = RiskEngine()
    # SVAS safe, geofence safe, cyclone false, wind severe -> overall SEVERE
    risk_input = RiskInput(
        vessel=VesselProfile(beam_m=5.0, draft_m=1.5),
        environmental_observations=[
            EnvironmentalObservation(
                waypoint_index=0,
                wave_height_m=1.0,
                wind_speed_kmh=62.0,
                depth_m=12.0,
                tide_height_m=0.5,
            )
        ]
    )
    evidence = engine.evaluate(risk_input)
    assert evidence.overall_risk_level == RiskLevel.SEVERE
    assert any(r.rule_id == "RULE_WIND_LIMIT_01" for r in evidence.rule_results)
