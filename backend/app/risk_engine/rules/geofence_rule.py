"""
Geofence Violation Rule & Cyclone Override Rule for Risk Engine.
"""

from app.risk_engine.rules.base import BaseRule
from app.risk_engine.schemas import RiskInput, RuleResult, RuleStatus, RiskLevel


class GeofenceViolationRule(BaseRule):
    """Flags HIGH or SEVERE risk if trajectory intersects restricted zones."""

    @property
    def rule_id(self) -> str:
        return "RULE_GEOFENCE_VIOLATION_01"

    @property
    def rule_name(self) -> str:
        return "Geofence Restricted Zone Rule"

    def applies(self, risk_input: RiskInput) -> bool:
        return True

    def evaluate(self, risk_input: RiskInput) -> RuleResult:
        violations = risk_input.geofence_violations
        if not violations:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.SAFE,
                details="No geofence or restricted zone violations detected along trajectory.",
                evidence={"violation_count": 0},
            )

        violated_zones = sorted(list(set(v.get("zone_name", "Restricted Zone") for v in violations)))
        violation_count = len(violations)

        # Flag SEVERE if 3 or more points violate or naval defense zone, else HIGH
        has_naval = any("naval" in v.get("zone_name", "").lower() or "defense" in v.get("restriction_type", "").lower() for v in violations)
        risk_lvl = RiskLevel.SEVERE if (has_naval or violation_count >= 3) else RiskLevel.HIGH

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=RuleStatus.FAILED,
            risk_level=risk_lvl,
            details=f"Trajectory violates {violation_count} restricted zone location(s): {', '.join(violated_zones)}.",
            evidence={
                "violation_count": violation_count,
                "violated_zones": violated_zones,
                "raw_violations": violations,
            },
        )


class CycloneOverrideRule(BaseRule):
    """
    Evaluates cyclone warning signals. If active cyclone warnings are present,
    forces an overall SEVERE risk override across the Risk Engine.
    """

    @property
    def rule_id(self) -> str:
        return "RULE_CYCLONE_OVERRIDE_01"

    @property
    def rule_name(self) -> str:
        return "Cyclone Proximity Override Rule"

    def applies(self, risk_input: RiskInput) -> bool:
        return True

    def evaluate(self, risk_input: RiskInput) -> RuleResult:
        cyclone_observations = [
            obs for obs in risk_input.environmental_observations
            if obs.cyclone_warning is True
        ]

        if not cyclone_observations:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.SAFE,
                details="No cyclone proximity or storm warnings detected.",
                evidence={"cyclone_active": False},
            )

        details_list = [
            obs.cyclone_details for obs in cyclone_observations if obs.cyclone_details
        ]

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=RuleStatus.FAILED,
            risk_level=RiskLevel.SEVERE,
            details=f"CRITICAL SAFETY WARNING: Active cyclone warning present across {len(cyclone_observations)} waypoint(s).",
            evidence={
                "cyclone_active": True,
                "warning_waypoint_count": len(cyclone_observations),
                "cyclone_details": details_list,
            },
            is_override=True,  # Signals RiskEvidenceBuilder to force SEVERE overall risk
        )
