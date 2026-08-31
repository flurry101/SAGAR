"""
Copilot Conversational RAG Schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class CopilotMessage(BaseModel):
    role: str = Field(..., description="Message author role: user or assistant")
    content: str = Field(..., description="Message text content")


class CopilotRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="Question or query for copilot")
    conversation_history: Optional[List[Union[CopilotMessage, Dict[str, Any]]]] = Field(
        default_factory=list,
        description="Prior conversation turns",
    )
    trip_id: Optional[str] = Field(default=None, description="Optional active trip id for contextual answers")
    fisher_id: Optional[str] = Field(default=None, description="Optional fisher user id")


class CopilotResponse(BaseModel):
    response: str = Field(..., description="Grounded assistant response")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tools executed during answering")
    trip_id: Optional[str] = Field(default=None, description="Trip ID context")


# Aliases for compatibility
CopilotChatRequest = CopilotRequest


class CopilotChatResponse(BaseModel):
    status: str = Field("success", description="Status code: success, error")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response body with response text and tool calls")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
