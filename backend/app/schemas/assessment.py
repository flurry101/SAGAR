# attr: m1
# [assessment detail and persistence schemas]
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AssessmentDetailResponse(BaseModel):
    # [complete persisted assessment record]
    assessment_id: str = Field(..., description="unique assessment identifier")
    trip_id: Optional[str] = Field(default=None, description="trip identifier")
    origin: Optional[str] = Field(default=None, description="departure port")
    departure_time: Optional[str] = Field(default=None, description="departure timestamp")
    language: Optional[str] = Field(default="en", description="assessment language")
    overall_risk_level: Optional[str] = Field(default="UNKNOWN", description="safety risk level")
    workflow_status: Optional[str] = Field(default="UNKNOWN", description="pipeline status")
    created_at: Optional[str] = Field(default=None, description="creation timestamp")
    task_plan: Optional[Dict[str, Any]] = Field(default=None, description="supervisor task plan")
    advisories: Optional[List[Dict[str, Any]]] = Field(default=None, description="persisted advisory rows")
    risk_evidence: Optional[List[Dict[str, Any]]] = Field(default=None, description="persisted risk evidence rows")
    weather_evidence: Optional[List[Dict[str, Any]]] = Field(default=None, description="persisted weather observations")
    marine_evidence: Optional[List[Dict[str, Any]]] = Field(default=None, description="persisted marine observations")
    agent_executions: Optional[List[Dict[str, Any]]] = Field(default=None, description="agent execution logs")
    reports: Optional[List[Dict[str, Any]]] = Field(default=None, description="generated mission reports")
# attr: m1

