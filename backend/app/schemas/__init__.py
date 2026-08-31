# attr: m1
# [schemas package init]
from app.schemas.common import APIResponse, ErrorResponse, Meta, ErrorDetails
from app.schemas.provenance import Provenance
from app.schemas.trajectory import Waypoint, Trajectory, GeofenceResult
from app.schemas.weather import WeatherObservation, Alert
from app.schemas.marine import MarineObservation, PFZData
from app.schemas.vessel import VesselProfile, VesselCreate, VesselUpdate
from app.schemas.advisory import HazardFlag, RiskEvidence, Advisory, VisualizationSpec, Report
from app.schemas.trip import (
    TripContext,
    TripAssessRequest,
    TripContinueRequest,
    ChatRequest,
    TripResponseData,
)
from app.schemas.copilot import CopilotRequest, CopilotResponse, CopilotMessage
from app.schemas.assessment import AssessmentDetailResponse
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserCreateResponse

__all__ = [
    "APIResponse",
    "ErrorResponse",
    "Meta",
    "ErrorDetails",
    "Provenance",
    "Waypoint",
    "Trajectory",
    "GeofenceResult",
    "WeatherObservation",
    "Alert",
    "MarineObservation",
    "PFZData",
    "VesselProfile",
    "VesselCreate",
    "VesselUpdate",
    "HazardFlag",
    "RiskEvidence",
    "Advisory",
    "VisualizationSpec",
    "Report",
    "TripContext",
    "TripAssessRequest",
    "TripContinueRequest",
    "ChatRequest",
    "TripResponseData",
    "CopilotRequest",
    "CopilotResponse",
    "CopilotMessage",
    "AssessmentDetailResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserCreateResponse",
]
# attr: m1
