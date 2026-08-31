# attr: m1
# [copilot chatbot conversational schemas]
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CopilotMessage(BaseModel):
    # [single conversation message]
    role: str = Field(..., description="message author role: user or assistant")
    content: str = Field(..., description="message text content")


class CopilotRequest(BaseModel):
    # [request payload for fisherman copilot]
    message: str = Field(..., min_length=1, max_length=2000, description="question or query for copilot")
    conversation_history: Optional[List[CopilotMessage]] = Field(
        default_factory=list,
        description="prior conversation turns",
    )
    trip_id: Optional[str] = Field(default=None, description="optional active trip id for contextual answers")
    fisher_id: Optional[str] = Field(default=None, description="optional fisher user id")


class CopilotResponse(BaseModel):
    # [copilot answer with tool call audit]
    response: str = Field(..., description="grounded assistant response")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="tools executed during answering")
# attr: m1

