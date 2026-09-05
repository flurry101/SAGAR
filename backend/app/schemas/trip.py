"""
Trip Planning and LangGraph Chat Schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from app.schemas.vessel import VesselProfile
from app.schemas.trajectory import Trajectory
from app.schemas.weather import WeatherObservation, Alert
from app.schemas.marine import MarineObservation, PFZData
from app.schemas.advisory import RiskEvidence, Advisory, VisualizationSpec, Report


class VesselInputSchema(BaseModel):
    vessel_id: Optional[str] = None
    vessel_name: Optional[str] = None
    vessel_type: Optional[str] = "fishing_boat"
    beam_width_m: Optional[float] = Field(None, ge=0.0, description="Beam width in meters")
    draft_m: Optional[float] = Field(None, ge=0.0, description="Draft depth in meters")
    length_m: Optional[float] = Field(None, ge=0.0, description="Length in meters")
    cruising_speed_kmh: Optional[float] = Field(15.0, ge=0.0, description="Speed in km/h")


class TripContext(BaseModel):
    trip_id: Optional[str] = Field(default=None, description="unique trip identifier")
    fisher_id: Optional[str] = Field(default=None, description="requesting fisher identifier")
    origin: Optional[str] = Field(default=None, description="departure location name e.g. Mangalore")
    origin_lat: Optional[float] = Field(default=None, description="resolved departure latitude")
    origin_lon: Optional[float] = Field(default=None, description="resolved departure longitude")
    destination_name: Optional[str] = Field(default=None, description="destination location name")
    destination_type: Optional[str] = Field(default=None, description="destination category: PFZ, CUSTOM, HARBOR")
    destination_lat: Optional[float] = Field(default=None, description="destination latitude")
    destination_lon: Optional[float] = Field(default=None, description="destination longitude")
    departure_time_iso: Optional[str] = Field(default=None, description="departure timestamp in iso 8601 utc")
    return_time_iso: Optional[str] = Field(default=None, description="expected return timestamp in iso 8601 utc")
    purpose: Optional[str] = Field(default="fishing", description="voyage purpose: fishing, transit, exploration")


class TripAssessRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="Natural language fishing trip request or query")
    session_id: Optional[str] = Field(default=None, description="Session thread id for multi turn conversation")
    fisher_id: Optional[str] = Field(default=None, description="Fisher identifier")
    language: Optional[str] = Field(default="en", description="Preferred response language code")
    origin: Optional[str] = Field(default=None, description="Origin port or harbor name")
    departure_time: Optional[str] = Field(default=None, description="Departure time in ISO format or natural text")
    vessel: Optional[Union[VesselInputSchema, VesselProfile, Dict[str, Any]]] = Field(default=None, description="Vessel specifications")
    vessel_profile: Optional[Union[VesselInputSchema, VesselProfile, Dict[str, Any]]] = Field(default=None, description="Vessel specifications alias")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Prior conversation messages")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User message to trip planner")
    session_id: Optional[str] = Field(default=None, description="Conversation thread id")
    fisher_id: Optional[str] = Field(default=None, description="User id")
    language: Optional[str] = Field(default="en", description="Response language code")
    vessel: Optional[Union[VesselInputSchema, VesselProfile, Dict[str, Any]]] = Field(default=None, description="Vessel specifications")
    vessel_profile: Optional[Union[VesselInputSchema, VesselProfile, Dict[str, Any]]] = Field(default=None, description="Vessel specifications")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Prior conversation messages")


class TripContinueRequest(BaseModel):
    session_id: str = Field(..., description="Active conversation session thread id")
    message: str = Field(..., min_length=1, max_length=4000, description="Clarification reply text")
    language: Optional[str] = Field(default="en", description="Preferred response language")


class TripResponseData(BaseModel):
    session_id: Optional[str] = Field(default=None, description="thread session id")
    trip_id: Optional[str] = Field(default=None, description="trip assessment identifier")
    workflow_status: str = Field(default="RECEIVED", description="pipeline execution status")
    task_plan: Optional[Dict[str, Any]] = Field(default=None, description="supervisor task plan")
    trip_context: Optional[TripContext] = Field(default=None, description="trip context")
    vessel_profile: Optional[Union[VesselProfile, Dict[str, Any]]] = Field(default=None, description="vessel profile evaluated")
    trajectory: Optional[Union[Trajectory, Dict[str, Any]]] = Field(default=None, description="trajectory with waypoints")
    weather_observations: Optional[List[Union[WeatherObservation, Dict[str, Any]]]] = Field(default=None, description="weather forecasts")
    marine_observations: Optional[List[Union[MarineObservation, Dict[str, Any]]]] = Field(default=None, description="marine observations")
    pfz_data: Optional[Union[List[PFZData], Dict[str, Any]]] = Field(default=None, description="pfz advisories")
    alerts: Optional[List[Union[Alert, Dict[str, Any]]]] = Field(default=None, description="proactive alerts")
    risk_evidence: Optional[Union[RiskEvidence, Dict[str, Any]]] = Field(default=None, description="deterministic risk evidence")
    overall_risk_level: Optional[str] = Field(default=None, description="overall risk level rating")
    advisory: Optional[Union[Advisory, Dict[str, Any]]] = Field(default=None, description="synthesized advisory")
    visualization_spec: Optional[Union[VisualizationSpec, Dict[str, Any]]] = Field(default=None, description="map visualization spec")
    report: Optional[Union[Report, Dict[str, Any]]] = Field(default=None, description="evidence backed report")
    persistence_status: Optional[str] = Field(default=None, description="supabase storage status")
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="non-fatal warning errors")


class TripAssessResponse(BaseModel):
    status: str = Field("success", description="Response status: success, needs_clarification, insufficient_information, error")
    data: Dict[str, Any] = Field(default_factory=dict, description="Payload containing advisory, risk, trajectory, alerts")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata including request_id, timestamp, version")
