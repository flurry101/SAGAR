"""
Tidal Window and Harbor Clearance Safety Rule.

Safety Context:
  Evaluates tidal height and departure/arrival tidal windows for coastal ports and shallow estuaries.
  Extreme low tides can restrict port access, ground vessels in navigation channels, or create
  dangerous tidal rips.

Thresholds:
  - Tide Height < -1.0m (Extreme Low Tide / Surge Deficit): HIGH Risk (Harbor access restricted)
  - Tide Height < 0.0m (Low Tide caution): MODERATE Risk
  - Tide Height >= 0.0m: SAFE
"""

from typing import List, Optional
from app.risk_engine.rules.base import BaseRule
from app.risk_engine.schemas import RiskInput, RuleResult, RuleStatus, RiskLevel

LOW_TIDE_WARNING_M: float = -1.0
LOW_TIDE_CAUTION_M: float = 0.0


class TidalClearanceRule(BaseRule):
    """Rule evaluating tidal window and harbor depth clearance."""

    @property
    def rule_id(self) -> str:
        return "RULE_TIDAL_CLEARANCE_01"

    @property
    def rule_name(self) -> str:
        return "Tidal Window & Harbor Clearance Rule"

    def applies(self, risk_input: RiskInput) -> bool:
        """Applies to all voyage evaluations."""
        return True

    def evaluate(self, risk_input: RiskInput) -> RuleResult:
        if not risk_input.environmental_observations:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.SAFE,
                details="No tidal observations provided along trajectory.",
                evidence={"tidal_data_available": False},
            )

        tides = [
            obs.tide_height_m
            for obs in risk_input.environmental_observations
            if obs.tide_height_m is not None
        ]

        if not tides:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.SAFE,
                details="Tidal height observations not specified; standard clearance assumed.",
                evidence={"tidal_data_available": False},
            )

        min_tide_m = min(tides)
        max_tide_m = max(tides)

        evidence_data = {
            "min_tide_height_m": round(min_tide_m, 2),
            "max_tide_height_m": round(max_tide_m, 2),
            "low_tide_warning_threshold_m": LOW_TIDE_WARNING_M,
        }

        if min_tide_m <= LOW_TIDE_WARNING_M:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.FAILED,
                risk_level=RiskLevel.HIGH,
                details=(
                    f"Extreme low tide detected ({min_tide_m:.2f}m). Risk of harbor channel shoaling and "
                    "stranding during port entry or departure."
                ),
                evidence=evidence_data,
            )

        if min_tide_m < LOW_TIDE_CAUTION_M:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.MODERATE,
                details=f"Low tide conditions ({min_tide_m:.2f}m). Navigate with caution in shallow estuaries.",
                evidence=evidence_data,
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=RuleStatus.PASSED,
            risk_level=RiskLevel.SAFE,
            details=f"Favorable tidal conditions across all waypoints (range {min_tide_m:.2f}m to {max_tide_m:.2f}m).",
            evidence=evidence_data,
        )
