"""
Risk Engine core orchestrator and RiskEvidenceBuilder.
"""

from datetime import datetime, timezone
from typing import List, Optional
from app.risk_engine.schemas import (
    RiskInput,
    RuleResult,
    RiskEvidence,
    RiskLevel,
    RuleStatus,
)
from app.risk_engine.rules.base import BaseRule
from app.risk_engine.rules.svas_rule import SVASCapSizeRule
from app.risk_engine.rules.geofence_rule import GeofenceViolationRule, CycloneOverrideRule
from app.risk_engine.rules.wind_rule import WindLimitRule
from app.risk_engine.rules.bathymetry_rule import BathymetryGroundingRule
from app.risk_engine.rules.tidal_rule import TidalClearanceRule

RISK_WEIGHTS = {
    RiskLevel.SAFE: 0,
    RiskLevel.MODERATE: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.SEVERE: 3,
}


class RiskEvidenceBuilder:
    """Aggregates RuleResults into a final RiskEvidence object."""

    @staticmethod
    def build(rule_results: List[RuleResult]) -> RiskEvidence:
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if not rule_results:
            return RiskEvidence(
                overall_risk_level=RiskLevel.SAFE,
                rule_results=[],
                evidence_trace={"passed_rules": 0, "failed_rules": 0, "insufficient_info_rules": 0},
                summary="No safety rules executed. Voyage evaluated as SAFE by default.",
                timestamp=now_utc,
            )

        # 1. Check for Cyclone / Safety Override (CycloneOverrideRule)
        override_rule = next((r for r in rule_results if r.is_override and r.status == RuleStatus.FAILED), None)
        
        # 2. Determine highest risk level across rules
        max_risk_level = RiskLevel.SAFE
        max_weight = -1

        failed_count = 0
        passed_count = 0
        insufficient_count = 0

        for res in rule_results:
            if res.status == RuleStatus.FAILED:
                failed_count += 1
            elif res.status == RuleStatus.PASSED:
                passed_count += 1
            elif res.status == RuleStatus.INSUFFICIENT_INFORMATION:
                insufficient_count += 1

            weight = RISK_WEIGHTS.get(res.risk_level, 0)
            if weight > max_weight:
                max_weight = weight
                max_risk_level = res.risk_level

        # If an override rule fired, force SEVERE overall risk
        if override_rule:
            overall_risk = RiskLevel.SEVERE
            summary_prefix = f"OVERRIDE TRIGGERED ({override_rule.rule_name}): "
        elif insufficient_count > 0:
            overall_risk = RiskLevel.UNKNOWN
            summary_prefix = ""
        else:
            overall_risk = max_risk_level
            summary_prefix = ""

        # Construct summary string
        if overall_risk in (RiskLevel.HIGH, RiskLevel.SEVERE):
            failed_names = [r.rule_name for r in rule_results if r.status == RuleStatus.FAILED]
            summary = (
                f"{summary_prefix}Voyage presents {overall_risk.value} risk. "
                f"Failed rules: {', '.join(failed_names) if failed_names else 'Safety threshold breach'}."
            )
        elif overall_risk == RiskLevel.UNKNOWN:
            summary = f"Voyage assessed as UNKNOWN risk. {insufficient_count} rule(s) lacked sufficient safety-critical data."
        elif overall_risk == RiskLevel.MODERATE:
            summary = "Voyage presents MODERATE risk. Operational caution recommended."
        else:
            summary = "Voyage assessed as SAFE. All safety rules passed."

        evidence_trace = {
            "total_rules_evaluated": len(rule_results),
            "passed_rules": passed_count,
            "failed_rules": failed_count,
            "insufficient_info_rules": insufficient_count,
            "has_override": override_rule is not None,
            "rule_evidence_map": {r.rule_id: r.evidence for r in rule_results},
        }

        return RiskEvidence(
            overall_risk_level=overall_risk,
            rule_results=rule_results,
            evidence_trace=evidence_trace,
            summary=summary,
            timestamp=now_utc,
        )


class RiskEngine:
    """Standalone pure deterministic Risk Engine applying safety rules."""

    def __init__(self, rules: Optional[List[BaseRule]] = None):
        if rules is not None:
            self.rules = rules
        else:
            # Default deterministic safety rule pipeline
            self.rules = [
                SVASCapSizeRule(),
                GeofenceViolationRule(),
                CycloneOverrideRule(),
                WindLimitRule(),
                BathymetryGroundingRule(),
                TidalClearanceRule(),
            ]

    def evaluate(self, risk_input: RiskInput) -> RiskEvidence:
        """
        Evaluate RiskInput through all applicable rules and aggregate results.
        Pure & deterministic: same input -> same output.
        """
        results: List[RuleResult] = []
        for rule in self.rules:
            if rule.applies(risk_input):
                result = rule.evaluate(risk_input)
                results.append(result)

        return RiskEvidenceBuilder.build(results)
