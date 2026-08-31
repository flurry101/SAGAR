"""
Assessment Retrieval Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AssessmentDetailResponse(BaseModel):
    status: str = Field("success", description="Status string")
    data: Dict[str, Any] = Field(default_factory=dict, description="Complete assessment and evidence payload")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
