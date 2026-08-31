"""
Assessment Detail and Persistence Schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AssessmentRecord(BaseModel):
    assessment_id: str = Field(..., description="Unique assessment identifier")
    trip_id: Optional[str] = Field(default=None, description="Trip identifier")
    origin: Optional[str] = Field(default=None, description="Departure port")
    departure_time: Optional[str] = Field(default=None, description="Departure timestamp")
    language: Optional[str] = Field(default="en", description="Assessment language")
    overall_risk_level: Optional[str] = Field(default="UNKNOWN", description="Safety risk level")
    workflow_status: Optional[str] = Field(default="UNKNOWN", description="Pipeline status")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    task_plan: Optional[Dict[str, Any]] = Field(default=None, description="Supervisor task plan")
    advisories: Optional[List[Dict[str, Any]]] = Field(default=None, description="Persisted advisory rows")
    risk_evidence: Optional[List[Dict[str, Any]]] = Field(default=None, description="Persisted risk evidence rows")
    weather_evidence: Optional[List[Dict[str, Any]]] = Field(default=None, description="Persisted weather observations")
    marine_evidence: Optional[List[Dict[str, Any]]] = Field(default=None, description="Persisted marine observations")
    agent_executions: Optional[List[Dict[str, Any]]] = Field(default=None, description="Agent execution logs")
    reports: Optional[List[Dict[str, Any]]] = Field(default=None, description="Generated mission reports")


class AssessmentDetailResponse(BaseModel):
    status: str = Field("success", description="Status string")
    data: Dict[str, Any] = Field(default_factory=dict, description="Complete assessment and evidence payload")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
