"""
SVAS (Significant Wave height to vessel Beam ratio) Capsize Safety Rule.

Formula & Theory:
  SVAS Ratio = Significant Wave Height (m) / Vessel Beam (m)
  Threshold limit = 4.0

Safety Context:
  When significant wave height exceeds 4.0 times the beam of a small to mid-sized vessel,
  the risk of parametric rolling, dynamic instability, and capsize increases exponentially.
"""

from app.risk_engine.rules.base import BaseRule
from app.risk_engine.schemas import RiskInput, RuleResult, RuleStatus, RiskLevel

# Safety-critical ratio threshold constant.
# Source / Assumption: Standard stability guideline for small fishing vessels.
# MUST BE REVIEWED BY DOMAIN EXPERT BEFORE PRODUCTION USE.
SVAS_CAPSIZE_RATIO_LIMIT: float = 4.0


class SVASCapSizeRule(BaseRule):
    """Rule evaluating capsize vulnerability based on wave height to vessel beam ratio."""

    @property
    def rule_id(self) -> str:
        return "RULE_SVAS_CAPSIZE_01"

    @property
    def rule_name(self) -> str:
        return "SVAS Capsize Safety Rule"

    def applies(self, risk_input: RiskInput) -> bool:
        """Applies to all voyage evaluations."""
        return True

    def evaluate(self, risk_input: RiskInput) -> RuleResult:
        # 1. Check vessel profile and beam data
        if not risk_input.vessel or risk_input.vessel.beam_m is None or risk_input.vessel.beam_m <= 0:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.INSUFFICIENT_INFORMATION,
                risk_level=RiskLevel.SAFE,
                details="Vessel beam (beam_m) is missing or non-positive. Cannot calculate SVAS capsize ratio.",
                evidence={"svas_limit": SVAS_CAPSIZE_RATIO_LIMIT},
            )

        beam_m = risk_input.vessel.beam_m

        # 2. Check environmental wave height observations
        if not risk_input.environmental_observations:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.INSUFFICIENT_INFORMATION,
                risk_level=RiskLevel.SAFE,
                details="No environmental observations provided along trajectory. Wave height data missing.",
                evidence={"vessel_beam_m": beam_m, "svas_limit": SVAS_CAPSIZE_RATIO_LIMIT},
            )

        valid_wave_heights = [
            obs.wave_height_m
            for obs in risk_input.environmental_observations
            if obs.wave_height_m is not None
        ]

        if not valid_wave_heights:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.INSUFFICIENT_INFORMATION,
                risk_level=RiskLevel.SAFE,
                details="Environmental observations exist but wave_height_m is missing across all points.",
                evidence={"vessel_beam_m": beam_m, "svas_limit": SVAS_CAPSIZE_RATIO_LIMIT},
            )

        max_wave_height_m = max(valid_wave_heights)
        max_svas_ratio = max_wave_height_m / beam_m

        evidence_data = {
            "vessel_beam_m": beam_m,
            "max_wave_height_m": max_wave_height_m,
            "max_svas_ratio": round(max_svas_ratio, 3),
            "svas_limit": SVAS_CAPSIZE_RATIO_LIMIT,
        }

        if max_svas_ratio > SVAS_CAPSIZE_RATIO_LIMIT:
            # Extremely high wave-to-beam ratio -> Severe / High risk
            risk_lvl = RiskLevel.SEVERE if max_svas_ratio >= 5.0 else RiskLevel.HIGH
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.FAILED,
                risk_level=risk_lvl,
                details=(
                    f"SVAS ratio {max_svas_ratio:.2f} exceeds capsize limit ({SVAS_CAPSIZE_RATIO_LIMIT:.1f}). "
                    f"Max wave height of {max_wave_height_m:.1f}m against vessel beam of {beam_m:.1f}m."
                ),
                evidence=evidence_data,
            )

        if max_svas_ratio > (0.75 * SVAS_CAPSIZE_RATIO_LIMIT):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.MODERATE,
                details=(
                    f"SVAS ratio {max_svas_ratio:.2f} is within limit ({SVAS_CAPSIZE_RATIO_LIMIT:.1f}) "
                    f"but approaches threshold (wave height {max_wave_height_m:.1f}m)."
                ),
                evidence=evidence_data,
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=RuleStatus.PASSED,
            risk_level=RiskLevel.SAFE,
            details=f"SVAS ratio {max_svas_ratio:.2f} is well within safe threshold ({SVAS_CAPSIZE_RATIO_LIMIT:.1f}).",
            evidence=evidence_data,
        )
