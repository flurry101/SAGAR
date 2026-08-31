# attr: m1
# [safety advisory and risk evidence schemas]
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.provenance import Provenance
from app.schemas.weather import Alert


class HazardFlag(BaseModel):
    # [specific deterministic risk engine violation]
    hazard_type: str = Field(..., description="hazard code e.g. WAVE_HEIGHT_EXCEEDED, GEOFENCE_VIOLATION")
    phase: str = Field(default="outbound", description="affected voyage phase: outbound, fishing, return")
    waypoint_index: Optional[int] = Field(default=None, description="waypoint index where hazard was detected")
    observed_value: Optional[float] = Field(default=None, description="observed environmental metric value")
    threshold_value: Optional[float] = Field(default=None, description="vessel specific safety threshold limit")
    severity: str = Field(default="WARNING", description="hazard severity: WARNING or SEVERE")
    provenance: Optional[Provenance] = Field(default=None, description="provenance of triggering observation")


class RiskEvidence(BaseModel):
    # [deterministic risk evaluation output]
    advisory_category: str = Field(
        ...,
        description="category e.g. CONDITIONS_FAVORABLE, ELEVATED_RISK_IDENTIFIED, SEVERE_HAZARD_OVERLAP, INSUFFICIENT_INFORMATION",
    )
    risk_level: str = Field(
        default="UNKNOWN",
        description="overall risk rating: LOW, MODERATE, HIGH, SEVERE, UNKNOWN",
    )
    hazard_flags: List[HazardFlag] = Field(default_factory=list, description="list of flagged hazards")
    confidence: Optional[float] = Field(default=None, description="confidence score")
    evaluated_at: Optional[str] = Field(default=None, description="utc evaluation timestamp")


class Advisory(BaseModel):
    # [human readable synthesized advisory text]
    advisory_category: str = Field(..., description="advisory category matching risk evidence")
    recommendation_text: str = Field(..., description="primary clear recommendation to the fisher")
    reason: Optional[str] = Field(default="", description="detailed reasoning based on evidence")
    affected_phase: Optional[str] = Field(default="", description="voyage phase most impacted")
    affected_time: Optional[str] = Field(default="", description="time window of concern")
    affected_location: Optional[str] = Field(default="", description="geographic region of concern")
    vessel_context: Optional[str] = Field(default="", description="vessel stability limits explanation")
    evidence_summary: Optional[str] = Field(default="", description="summary of environmental factors")
    uncertainty_notes: Optional[str] = Field(default="", description="notes on data sources and confidence")
    disclaimer: str = Field(
        default="ORCA provides decision support only. Follow official alerts from INCOIS and IMD. Final decision rests with the fisher.",
        description="standard marine safety disclaimer",
    )
    language: str = Field(default="en", description="iso 639-1 language code of the advisory")


class VisualizationSpec(BaseModel):
    # [frontend map layer rendering specifications]
    layers: List[Dict[str, Any]] = Field(default_factory=list, description="map visualization layers")
    center: Optional[Dict[str, float]] = Field(default=None, description="map center lat/lon")
    bounds: Optional[List[float]] = Field(default=None, description="bounding box coordinates")
    recommended_zoom: Optional[int] = Field(default=8, description="initial map zoom level")


class Report(BaseModel):
    # [comprehensive evidence backed mission report]
    summary: str = Field(..., description="high level mission summary")
    recommendation: str = Field(..., description="actionable recommendation")
    risk: Optional[Dict[str, Any]] = Field(default=None, description="detailed risk breakdown")
    route: Optional[Dict[str, Any]] = Field(default=None, description="route details")
    alerts: List[Alert] = Field(default_factory=list, description="active alerts")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="structured evidence items")
    sources: List[str] = Field(default_factory=list, description="data sources referenced")
    uncertainty: List[str] = Field(default_factory=list, description="uncertainty statements")
    limitations: List[str] = Field(default_factory=list, description="operational limitations")
# attr: m1

