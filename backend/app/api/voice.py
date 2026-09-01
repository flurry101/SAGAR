from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging


logger = logging.getLogger(__name__)

router = APIRouter()

class VexylMessage(BaseModel):
    role: str
    content: str

class VexylWebhookRequest(BaseModel):
    sessionId: Optional[str] = ""
    message: Optional[str] = ""
    history: Optional[List[VexylMessage]] = []
    context: Optional[Dict[str, Any]] = {}

class VexylWebhookResponse(BaseModel):
    response: str
    action: str = "continue"
    metadata: Dict[str, Any] = {"should_hangup": False}

@router.post("/webhook", response_model=VexylWebhookResponse)
async def voice_webhook(
    payload: VexylWebhookRequest
):
    """
    Webhook for VEXYL Gateway Custom LLM.
    Receives transcribed text -> calls ORCA Conversational Copilot -> returns text for TTS.
    """
    logger.debug(f"[VOICE] Received webhook for call {payload.sessionId}")
    
    if not payload.message:
        return VexylWebhookResponse(response="I didn't catch that.", action="continue")
        
    try:
        # Build history format expected by Copilot
        history = [{"role": msg.role, "content": msg.content} for msg in (payload.history or [])]
        
        # Route voice queries to the Conversational Copilot Chatbot instead of the deterministic LangGraph planner
        from app.api.copilot import _execute_copilot_chat
        
        result = await _execute_copilot_chat(
            user_message=payload.message,
            conversation_history=history
        )
        
        advisory_text = result.get("response", "I didn't catch that.")
        
        logger.info(f"[VOICE] Returning Copilot response to VEXYL: {advisory_text}")
        
        return VexylWebhookResponse(
            response=advisory_text,
            action="continue"
        )
        
    except Exception as e:
        logger.error(f"[VOICE] Webhook failed: {e}")
        return VexylWebhookResponse(
            response="I'm sorry, I encountered an internal error while processing your request.",
            action="continue"
        )
