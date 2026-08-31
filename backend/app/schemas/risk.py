"""
Risk Engine Micro-Endpoint Schemas.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.risk_engine.schemas import RiskInput, RiskEvidence


class RiskEvaluateApiResponse(BaseModel):
    status: str = Field("success", description="Status")
    data: Dict[str, Any] = Field(default_factory=dict, description="Calculated RiskEvidence payload")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
