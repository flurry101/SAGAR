"""
Copilot Conversational RAG API Router.
Wires FastAPI HTTP requests to the LangChain Copilot agent.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.copilot import CopilotChatRequest, CopilotChatResponse
from app.chatbot.chatbot import chat as copilot_chat
from app.core.auth import get_current_user_optional
from app.models.user import User

router = APIRouter()


@router.post("/copilot", response_model=CopilotChatResponse, summary="Chat with ORCA Copilot (Knowledge & Explanation)")
async def chat_with_copilot(
    request: CopilotChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Submits a conversational question to the ORCA Fisherman Copilot.
    Uses LangChain with 3 tool layers: Knowledge RAG, ORCA context reads, and live marine data.
    """
    request_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    fisher_id = request.fisher_id or (str(current_user.id) if current_user else None)

    try:
        chat_result = await copilot_chat(
            user_message=request.message,
            conversation_history=request.conversation_history,
            trip_id=request.trip_id,
            fisher_id=fisher_id,
        )

        return CopilotChatResponse(
            status="success",
            data={
                "response": chat_result.get("response", ""),
                "tool_calls": chat_result.get("tool_calls", []),
                "trip_id": request.trip_id,
            },
            meta={
                "request_id": request_id,
                "timestamp": now_iso,
                "version": "v1",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot error: {str(e)}",
        )
