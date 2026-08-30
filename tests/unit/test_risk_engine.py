"""Unit tests for Risk Engine (SVAS rule, Geofence rule, Cyclone rule, RiskEvidenceBuilder)."""

import pytest
from app.risk_engine.schemas import (
    RiskInput,
    VesselProfile,
    EnvironmentalObservation,
    RiskLevel,
    RuleStatus,
)
from app.risk_engine.rules.svas_rule import SVASCapSizeRule, SVAS_CAPSIZE_RATIO_LIMIT
from app.risk_engine.rules.geofence_rule import GeofenceViolationRule, CycloneOverrideRule
from app.risk_engine.engine import RiskEngine, RiskEvidenceBuilder


class TestSVASCapSizeRule:
    def test_svas_safe_below_threshold(self):
        rule = SVASCapSizeRule()
        # Vessel beam = 4.0m, Wave height = 2.0m -> Ratio = 0.5 (safe)
        risk_input = RiskInput(
            vessel=VesselProfile(beam_m=4.0),
            environmental_observations=[
                EnvironmentalObservation(wave_height_m=2.0)
            ],
        )
        res = rule.evaluate(risk_input)
        assert res.status == RuleStatus.PASSED
        assert res.risk_level == RiskLevel.SAFE

    def test_svas_failed_above_threshold(self):
        rule = SVASCapSizeRule()
        # Vessel beam = 3.0m, Wave height = 15.0m -> Ratio = 5.0 (> 4.0 limit -> SEVERE)
        risk_input = RiskInput(
            vessel=VesselProfile(beam_m=3.0),
            environmental_observations=[
                EnvironmentalObservation(wave_height_m=15.0)
            ],
        )
        res = rule.evaluate(risk_input)
        assert res.status == RuleStatus.FAILED
        assert res.risk_level == RiskLevel.SEVERE

    def test_svas_missing_vessel_beam_yields_insufficient_info(self):
        rule = SVASCapSizeRule()
        risk_input = RiskInput(
            vessel=VesselProfile(beam_m=None),
            environmental_observations=[
                EnvironmentalObservation(wave_height_m=3.0)
            ],
        )
        res = rule.evaluate(risk_input)
        assert res.status == RuleStatus.INSUFFICIENT_INFORMATION

    def test_svas_missing_wave_height_yields_insufficient_info(self):
        rule = SVASCapSizeRule()
        risk_input = RiskInput(
            vessel=VesselProfile(beam_m=4.0),
            environmental_observations=[],
        )
        res = rule.evaluate(risk_input)
        assert res.status == RuleStatus.INSUFFICIENT_INFORMATION


class TestGeofenceAndCycloneRules:
    def test_geofence_violation_rule_fails_when_violations_present(self):
        rule = GeofenceViolationRule()
        risk_input = RiskInput(
            geofence_violations=[
                {"zone_id": "TEST_ZONE", "zone_name": "Naval Base", "restriction_type": "Naval"}
            ]
        )
        res = rule.evaluate(risk_input)
        assert res.status == RuleStatus.FAILED
        assert res.risk_level == RiskLevel.SEVERE

    def test_cyclone_override_rule_triggers_override(self):
        rule = CycloneOverrideRule()
        risk_input = RiskInput(
            environmental_observations=[
                EnvironmentalObservation(cyclone_warning=True, cyclone_details={"name": "Cyclone Vardah"})
            ]
        )
        res = rule.evaluate(risk_input)
        assert res.status == RuleStatus.FAILED
        assert res.risk_level == RiskLevel.SEVERE
        assert res.is_override is True


class TestRiskEngineAggregation:
    def test_risk_engine_safe_voyage(self):
        engine = RiskEngine()
        risk_input = RiskInput(
            vessel=VesselProfile(beam_m=5.0),
            environmental_observations=[
                EnvironmentalObservation(wave_height_m=1.0, cyclone_warning=False)
            ],
            geofence_violations=[],
        )
        evidence = engine.evaluate(risk_input)
        assert evidence.overall_risk_level == RiskLevel.SAFE
        assert evidence.evidence_trace["failed_rules"] == 0

    def test_cyclone_override_forces_overall_severe_risk(self):
        engine = RiskEngine()
        # Even with safe SVAS (wave 1m, beam 10m) and 0 geofence violations, cyclone warning must force SEVERE overall risk
        risk_input = RiskInput(
            vessel=VesselProfile(beam_m=10.0),
            environmental_observations=[
                EnvironmentalObservation(wave_height_m=1.0, cyclone_warning=True)
            ],
            geofence_violations=[],
        )
        evidence = engine.evaluate(risk_input)
        assert evidence.overall_risk_level == RiskLevel.SEVERE
        assert evidence.evidence_trace["has_override"] is True
