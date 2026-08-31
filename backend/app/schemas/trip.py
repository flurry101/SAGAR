# attr: m1
# [trip planning and langgraph chat schemas]
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.vessel import VesselProfile
from app.schemas.trajectory import Trajectory
from app.schemas.weather import WeatherObservation, Alert
from app.schemas.marine import MarineObservation, PFZData
from app.schemas.advisory import RiskEvidence, Advisory, VisualizationSpec, Report


class TripContext(BaseModel):
    # [extracted parameters defining the voyage]
    trip_id: Optional[str] = Field(default=None, description="unique trip identifier")
    fisher_id: Optional[str] = Field(default=None, description="requesting fisher identifier")
    origin: Optional[str] = Field(default=None, description="departure location name e.g. Mangalore")
    origin_lat: Optional[float] = Field(default=None, description="resolved departure latitude")
    origin_lon: Optional[float] = Field(default=None, description="resolved departure longitude")
    destination_type: Optional[str] = Field(default="PFZ", description="destination category: PFZ, CUSTOM, HARBOR")
    destination_lat: Optional[float] = Field(default=None, description="destination latitude")
    destination_lon: Optional[float] = Field(default=None, description="destination longitude")
    departure_time_iso: Optional[str] = Field(default=None, description="departure timestamp in iso 8601 utc")
    return_time_iso: Optional[str] = Field(default=None, description="expected return timestamp in iso 8601 utc")
    purpose: Optional[str] = Field(default="fishing", description="voyage purpose: fishing, transit, exploration")


class TripAssessRequest(BaseModel):
    # [fisher trip planning input request]
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="natural language fishing trip request or query",
    )
    fisher_id: Optional[str] = Field(default=None, description="authenticated fisher profile id")
    session_id: Optional[str] = Field(default=None, description="session thread id for multi turn conversation")
    language: Optional[str] = Field(default="en", description="preferred response language code")
    vessel_profile: Optional[VesselProfile] = Field(default=None, description="optional vessel parameters")


class TripContinueRequest(BaseModel):
    # [multi-turn clarification response request]
    session_id: str = Field(..., description="active conversation session thread id")
    message: str = Field(..., min_length=1, max_length=2000, description="clarification reply text")
    language: Optional[str] = Field(default="en", description="preferred response language")


class ChatRequest(BaseModel):
    # [primary chat interface request payload]
    message: str = Field(..., min_length=1, max_length=2000, description="user message to trip planner")
    session_id: Optional[str] = Field(default=None, description="conversation thread id")
    fisher_id: Optional[str] = Field(default=None, description="user id")
    language: Optional[str] = Field(default="en", description="response language code")
    vessel_profile: Optional[VesselProfile] = Field(default=None, description="vessel specifications")


class TripResponseData(BaseModel):
    # [complete structured assessment data returned by langgraph]
    session_id: Optional[str] = Field(default=None, description="thread session id")
    trip_id: Optional[str] = Field(default=None, description="trip assessment identifier")
    workflow_status: str = Field(default="RECEIVED", description="pipeline execution status")
    task_plan: Optional[Dict[str, Any]] = Field(default=None, description="supervisor task plan")
    trip_context: Optional[TripContext] = Field(default=None, description="trip context")
    vessel_profile: Optional[VesselProfile] = Field(default=None, description="vessel profile evaluated")
    trajectory: Optional[Trajectory] = Field(default=None, description="trajectory with waypoints")
    weather_observations: Optional[List[WeatherObservation]] = Field(default=None, description="weather forecasts")
    marine_observations: Optional[List[MarineObservation]] = Field(default=None, description="marine observations")
    pfz_data: Optional[List[PFZData]] = Field(default=None, description="pfz advisories")
    alerts: Optional[List[Alert]] = Field(default=None, description="proactive alerts")
    risk_evidence: Optional[RiskEvidence] = Field(default=None, description="deterministic risk evidence")
    overall_risk_level: Optional[str] = Field(default=None, description="overall risk level rating")
    advisory: Optional[Advisory] = Field(default=None, description="synthesized advisory")
    visualization_spec: Optional[VisualizationSpec] = Field(default=None, description="map visualization spec")
    report: Optional[Report] = Field(default=None, description="evidence backed report")
    persistence_status: Optional[str] = Field(default=None, description="supabase storage status")
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="non-fatal warning errors")
# attr: m1

