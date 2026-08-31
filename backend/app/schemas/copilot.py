"""
Copilot Conversational RAG Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="Fisherman question or explanation request")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Prior conversation messages")
    trip_id: Optional[str] = Field(None, description="Optional trip ID for context grounding")
    fisher_id: Optional[str] = Field(None, description="Optional authenticated fisher ID")


class CopilotChatResponse(BaseModel):
    status: str = Field("success", description="Status code: success, error")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response body with response text and tool calls")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
