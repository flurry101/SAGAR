"""Risk Engine data schemas and models."""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.gis.schemas import Trajectory


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class RuleStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class VesselProfile(BaseModel):
    """Vessel parameters required for safety math."""

    vessel_id: Optional[str] = Field(None, description="Unique vessel identifier")
    vessel_name: Optional[str] = Field(None, description="Vessel name")
    vessel_type: Optional[str] = Field("fishing_boat", description="Vessel classification type")
    beam_m: Optional[float] = Field(None, description="Vessel maximum beam (width) in meters (m)", ge=0.0)
    draft_m: Optional[float] = Field(None, description="Vessel draft in meters (m)", ge=0.0)
    length_m: Optional[float] = Field(None, description="Vessel overall length in meters (m)", ge=0.0)
    max_speed_knots: Optional[float] = Field(10.0, description="Vessel maximum design speed in knots", ge=0.0)


class EnvironmentalObservation(BaseModel):
    """Spatio-temporal environmental / marine observation at a waypoint."""

    waypoint_index: Optional[int] = Field(None, description="Index of associated waypoint in trajectory")
    timestamp: Optional[str] = Field(None, description="ISO timestamp string")
    lat: Optional[float] = Field(None, description="Latitude")
    lon: Optional[float] = Field(None, description="Longitude")
    wave_height_m: Optional[float] = Field(None, description="Significant wave height in meters (m)", ge=0.0)
    wind_speed_knots: Optional[float] = Field(None, description="Wind speed in knots (kt)", ge=0.0)
    visibility_km: Optional[float] = Field(None, description="Visibility in kilometers (km)", ge=0.0)
    cyclone_warning: Optional[bool] = Field(False, description="Flag indicating active cyclone warning")
    cyclone_details: Optional[Dict[str, Any]] = Field(None, description="Additional cyclone warning metadata")


class RiskInput(BaseModel):
    """Complete input object passed into RiskEngine.evaluate()."""

    vessel: Optional[VesselProfile] = Field(None, description="Vessel specifications")
    trajectory: Optional[Trajectory] = Field(None, description="Planned voyage trajectory")
    environmental_observations: List[EnvironmentalObservation] = Field(
        default_factory=list, description="Observations aligned to trajectory waypoints"
    )
    geofence_violations: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of detected geofence violation dicts"
    )


class RuleResult(BaseModel):
    """Result returned by an individual safety rule evaluation."""

    rule_id: str = Field(..., description="Unique ID of the rule")
    rule_name: str = Field(..., description="Human readable rule name")
    status: RuleStatus = Field(..., description="Evaluation status: PASSED, FAILED, or INSUFFICIENT_INFORMATION")
    risk_level: RiskLevel = Field(..., description="Risk level assigned by rule: SAFE, MODERATE, HIGH, SEVERE")
    details: str = Field(..., description="Human readable explanation of rule finding")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Quantitative evidence trace metrics")
    is_override: bool = Field(False, description="True if this rule result forces an overall SEVERE override")


class RiskEvidence(BaseModel):
    """Final aggregated output object of RiskEngine."""

    overall_risk_level: RiskLevel = Field(..., description="Overall aggregated risk level across all rules")
    rule_results: List[RuleResult] = Field(default_factory=list, description="Detailed findings per rule")
    evidence_trace: Dict[str, Any] = Field(default_factory=dict, description="Structured quantitative evidence summary")
    summary: str = Field(..., description="Synthesized executive summary of risk evaluation")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of evaluation execution")
