# attr: m1
# [copilot knowledge and reasoning chat router]
from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Dict, List, Optional
from fastapi import APIRouter, Depends, Request
from app.core.auth import get_current_user_optional
from app.schemas.common import APIResponse, Meta
from app.schemas.copilot import CopilotRequest, CopilotResponse

logger = logging.getLogger(__name__)
router = APIRouter()


async def _execute_copilot_chat(
    user_message: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    trip_id: Optional[str] = None,
    fisher_id: Optional[str] = None,
) -> Dict[str, Any]:
    # [lazy load and execute langchain fisherman copilot]
    try:
        from app.chatbot.chatbot import chat as copilot_chat
        return await copilot_chat(
            user_message=user_message,
            conversation_history=conversation_history,
            trip_id=trip_id,
            fisher_id=fisher_id,
        )
    except ImportError as e:
        logger.warning(f"chatbot dependencies not installed: {e}")
        return {
            "response": "Fisherman Copilot dependencies are not installed on the server.",
            "tool_calls": [],
        }


def get_copilot_chat_runner() -> Callable:
    # [dependency injection hook for copilot chat runner]
    return _execute_copilot_chat


@router.post("/copilot", response_model=APIResponse[CopilotResponse])
async def chat_with_copilot(
    payload: CopilotRequest,
    request: Request,
    user=Depends(get_current_user_optional),
    chat_runner: Callable = Depends(get_copilot_chat_runner),
):
    # [invoke langchain fisherman copilot agent]
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    fisher_id = payload.fisher_id or (str(user.user_id) if user and hasattr(user, "user_id") else None)

    history = [msg.model_dump() for msg in payload.conversation_history] if payload.conversation_history else None

    result = await chat_runner(
        user_message=payload.message,
        conversation_history=history,
        trip_id=payload.trip_id,
        fisher_id=fisher_id,
    )

    response_data = CopilotResponse(
        response=result.get("response", ""),
        tool_calls=result.get("tool_calls", []),
    )

    return APIResponse(
        status="success",
        data=response_data,
        meta=Meta(request_id=request_id),
    )
# attr: m1

