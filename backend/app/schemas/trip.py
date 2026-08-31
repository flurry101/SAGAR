"""
Trip Planning and Assessment Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VesselInputSchema(BaseModel):
    vessel_id: Optional[str] = None
    vessel_name: Optional[str] = None
    vessel_type: Optional[str] = "fishing_boat"
    beam_width_m: Optional[float] = Field(None, ge=0.0, description="Beam width in meters")
    draft_m: Optional[float] = Field(None, ge=0.0, description="Draft depth in meters")
    length_m: Optional[float] = Field(None, ge=0.0, description="Length in meters")
    cruising_speed_kmh: Optional[float] = Field(15.0, ge=0.0, description="Speed in km/h")


class TripAssessRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="Natural language fishing query")
    session_id: Optional[str] = Field(None, description="Session / thread ID for multi-turn conversations")
    fisher_id: Optional[str] = Field(None, description="Fisher identifier")
    language: Optional[str] = Field("en", description="Preferred response language code (e.g. 'en', 'hi', 'ta')")
    origin: Optional[str] = Field(None, description="Origin port or harbor name")
    departure_time: Optional[str] = Field(None, description="Departure time in ISO format or natural text")
    vessel: Optional[VesselInputSchema] = Field(None, description="Vessel specifications")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Previous messages")


class TripAssessResponse(BaseModel):
    status: str = Field("success", description="Response status: success, needs_clarification, insufficient_information, error")
    data: Dict[str, Any] = Field(default_factory=dict, description="Payload containing advisory, risk, trajectory, alerts")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata including request_id, timestamp, version")
