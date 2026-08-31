"""
Wind Speed and Gust Limit Safety Rule.

Safety Context:
  Evaluates sustained wind speeds and wind gusts along the planned voyage trajectory.
  High winds cause severe sea states, spray, loss of steerage, and dynamic instability
  for small to mid-sized fishing vessels.

Thresholds:
  - Wind Speed >= 60.0 km/h (~32.4 kt / Near Gale): SEVERE Risk
  - Wind Speed >= 40.0 km/h (~21.6 kt / Strong Breeze): HIGH Risk
  - Wind Speed >= 30.0 km/h (~16.2 kt / Moderate Breeze): MODERATE Risk
  - Wind Gust >= 65.0 km/h: SEVERE Risk
"""

from typing import List, Optional
from app.risk_engine.rules.base import BaseRule
from app.risk_engine.schemas import RiskInput, RuleResult, RuleStatus, RiskLevel

WIND_SEVERE_KMH: float = 60.0
WIND_HIGH_KMH: float = 40.0
WIND_MODERATE_KMH: float = 30.0
GUST_SEVERE_KMH: float = 65.0


class WindLimitRule(BaseRule):
    """Rule evaluating sustained wind speed and wind gust hazards."""

    @property
    def rule_id(self) -> str:
        return "RULE_WIND_LIMIT_01"

    @property
    def rule_name(self) -> str:
        return "Wind Speed & Gust Safety Rule"

    def applies(self, risk_input: RiskInput) -> bool:
        """Applies to all voyage evaluations."""
        return True

    def evaluate(self, risk_input: RiskInput) -> RuleResult:
        if not risk_input.environmental_observations:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.INSUFFICIENT_INFORMATION,
                risk_level=RiskLevel.SAFE,
                details="No environmental observations provided along trajectory. Wind speed data missing.",
                evidence={"wind_high_kmh": WIND_HIGH_KMH, "wind_severe_kmh": WIND_SEVERE_KMH},
            )

        # Collect normalized wind speeds in km/h
        wind_speeds_kmh: List[float] = []
        gust_speeds_kmh: List[float] = []

        for obs in risk_input.environmental_observations:
            if obs.wind_speed_kmh is not None:
                wind_speeds_kmh.append(obs.wind_speed_kmh)
            elif obs.wind_speed_knots is not None:
                # 1 knot = 1.852 km/h
                wind_speeds_kmh.append(obs.wind_speed_knots * 1.852)

            if obs.gust_speed_kmh is not None:
                gust_speeds_kmh.append(obs.gust_speed_kmh)

        if not wind_speeds_kmh and not gust_speeds_kmh:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.INSUFFICIENT_INFORMATION,
                risk_level=RiskLevel.SAFE,
                details="Environmental observations exist but wind speed/gust data is missing across all waypoints.",
                evidence={"wind_high_kmh": WIND_HIGH_KMH, "wind_severe_kmh": WIND_SEVERE_KMH},
            )

        max_wind_kmh = max(wind_speeds_kmh) if wind_speeds_kmh else 0.0
        max_gust_kmh = max(gust_speeds_kmh) if gust_speeds_kmh else 0.0

        evidence_data = {
            "max_wind_speed_kmh": round(max_wind_kmh, 1),
            "max_gust_speed_kmh": round(max_gust_kmh, 1),
            "wind_high_threshold_kmh": WIND_HIGH_KMH,
            "wind_severe_threshold_kmh": WIND_SEVERE_KMH,
        }

        if max_wind_kmh >= WIND_SEVERE_KMH or max_gust_kmh >= GUST_SEVERE_KMH:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.FAILED,
                risk_level=RiskLevel.SEVERE,
                details=(
                    f"Extreme wind detected: sustained {max_wind_kmh:.1f} km/h (threshold {WIND_SEVERE_KMH:.1f} km/h) "
                    f"or gust {max_gust_kmh:.1f} km/h. Sea conditions are hazardous for navigation."
                ),
                evidence=evidence_data,
            )

        if max_wind_kmh >= WIND_HIGH_KMH:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.FAILED,
                risk_level=RiskLevel.HIGH,
                details=(
                    f"Strong wind detected: {max_wind_kmh:.1f} km/h exceeds safety threshold ({WIND_HIGH_KMH:.1f} km/h). "
                    "Small craft advisory recommended."
                ),
                evidence=evidence_data,
            )

        if max_wind_kmh >= WIND_MODERATE_KMH:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status=RuleStatus.PASSED,
                risk_level=RiskLevel.MODERATE,
                details=f"Moderate wind conditions: {max_wind_kmh:.1f} km/h. Operational caution advised.",
                evidence=evidence_data,
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=RuleStatus.PASSED,
            risk_level=RiskLevel.SAFE,
            details=f"Wind speeds are favorable (max {max_wind_kmh:.1f} km/h). Within safe operational limits.",
            evidence=evidence_data,
        )
