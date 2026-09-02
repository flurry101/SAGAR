"""
Copilot Conversational RAG API Router.
Wires FastAPI HTTP requests to the LangChain Copilot agent.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.core.auth import get_current_user_optional
from app.schemas.common import APIResponse, Meta
from app.schemas.copilot import CopilotRequest, CopilotResponse
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


async def _execute_copilot_chat(
    user_message: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    trip_id: Optional[str] = None,
    fisher_id: Optional[str] = None,
    language: str = "en",
) -> Dict[str, Any]:
    try:
        from app.chatbot.chatbot import chat as copilot_chat
        return await copilot_chat(
            user_message=user_message,
            conversation_history=conversation_history,
            trip_id=trip_id,
            fisher_id=fisher_id,
            language=language,
        )
    except ImportError as e:
        logger.warning(f"chatbot dependencies not installed: {e}")
        return {
            "response": "Fisherman Copilot dependencies are not installed on the server.",
            "tool_calls": [],
        }


def get_copilot_chat_runner() -> Callable:
    return _execute_copilot_chat


@router.post("/copilot", response_model=APIResponse[CopilotResponse], summary="Chat with ORCA Copilot (Knowledge & Explanation)")
async def chat_with_copilot(
    payload: CopilotRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    chat_runner: Callable = Depends(get_copilot_chat_runner),
):
    """
    Submits a conversational question to the ORCA Fisherman Copilot.
    Uses LangChain with 3 tool layers: Knowledge RAG, ORCA context reads, and live marine data.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    fisher_id = payload.fisher_id or (str(current_user.id) if current_user else None)
    language = request.headers.get("Accept-Language", "en")

    history = []
    if payload.conversation_history:
        for msg in payload.conversation_history:
            if hasattr(msg, "model_dump"):
                history.append(msg.model_dump())
            elif isinstance(msg, dict):
                history.append(msg)

    try:
        result = await chat_runner(
            user_message=payload.message,
            conversation_history=history if history else None,
            trip_id=payload.trip_id,
            fisher_id=fisher_id,
            language=language,
        )

        response_data = CopilotResponse(
            response=result.get("response", ""),
            tool_calls=result.get("tool_calls", []),
            trip_id=payload.trip_id,
        )

        return APIResponse(
            status="success",
            data=response_data,
            meta=Meta(request_id=request_id),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot error: {str(e)}",
        )
