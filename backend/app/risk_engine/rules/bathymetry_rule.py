"""
Bathymetry and Shallow Water Grounding Safety Rule.

Safety Context:
  Evaluates water depth (bathymetry) along the planned voyage against the vessel draft.
  Sufficient Under-Keel Clearance (UKC) is essential to prevent grounding on shallow sandbars,
  reefs, and shoals.

Thresholds:
  - Water depth <= vessel draft: SEVERE Risk (Imminent grounding / hull impact)
  - Water depth < 1.5 * vessel draft: HIGH Risk (Insufficient under-keel clearance)
  - Water depth < 2.0 * vessel draft: MODERATE Risk (Shallow coastal maneuvering)
"""

from typing import List, Optional
from app.risk_engine.rules.base import BaseRule
from app.risk_engine.schemas import RiskInput, RuleResult, RuleStatus, RiskLevel

DEFAULT_MIN_SAFE_RATIO: float = 1.5
MIN_CAUTION_RATIO: float = 2.0


class BathymetryGroundingRule(BaseRule):
    """Rule evaluating grounding risk from shallow water bathymetry."""

    @property
    def rule_id(self) -> str:
        return "RULE_BATHYMETRY_GROUNDING_01"

    @property
    def rule_name(self) -> str:
        return "Bathymetry & Shallow Water Grounding Rule"

    def applies(self, risk_input: RiskInput) -> bool:
        """Applies when vessel specifications are provided."""
        return True

    def evaluate(self, risk_input: RiskInput) -> RuleResult:
        if not risk_input.vessel or risk_input.vessel.draft_m is None or risk_input.vessel.draft_m <= 0:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.SAFE,
                details="Vessel draft not specified; assuming standard shallow draft clearance.",
                evidence={"draft_specified": False},
            )

        draft_m = risk_input.vessel.draft_m

        if not risk_input.environmental_observations:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.SAFE,
                details="No bathymetry observations available along trajectory.",
                evidence={"vessel_draft_m": draft_m},
            )

        depths = [
            obs.depth_m
            for obs in risk_input.environmental_observations
            if obs.depth_m is not None
        ]

        if not depths:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.SAFE,
                details="Bathymetry depth data is not present in observations; assumed clear.",
                evidence={"vessel_draft_m": draft_m, "bathymetry_available": False},
            )

        min_depth_m = min(depths)
        clearance_ratio = min_depth_m / draft_m

        evidence_data = {
            "vessel_draft_m": draft_m,
            "min_water_depth_m": min_depth_m,
            "clearance_ratio": round(clearance_ratio, 2),
            "safe_clearance_ratio_limit": DEFAULT_MIN_SAFE_RATIO,
        }

        if min_depth_m <= draft_m:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.FAILED,
                risk_level=RiskLevel.SEVERE,
                details=(
                    f"Imminent grounding hazard: Minimum water depth {min_depth_m:.1f}m is less than or equal to "
                    f"vessel draft {draft_m:.1f}m."
                ),
                evidence=evidence_data,
            )

        if clearance_ratio < DEFAULT_MIN_SAFE_RATIO:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.FAILED,
                risk_level=RiskLevel.HIGH,
                details=(
                    f"Shallow water hazard: Depth {min_depth_m:.1f}m provides insufficient Under-Keel Clearance "
                    f"for draft {draft_m:.1f}m (ratio {clearance_ratio:.2f} < {DEFAULT_MIN_SAFE_RATIO:.1f})."
                ),
                evidence=evidence_data,
            )

        if clearance_ratio < MIN_CAUTION_RATIO:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.MODERATE,
                details=(
                    f"Marginal water depth: Minimum depth {min_depth_m:.1f}m requires cautious navigation for draft {draft_m:.1f}m."
                ),
                evidence=evidence_data,
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=RuleStatus.PASSED,
            risk_level=RiskLevel.SAFE,
            details=f"Adequate depth clearance along trajectory (min depth {min_depth_m:.1f}m vs draft {draft_m:.1f}m).",
            evidence=evidence_data,
        )
