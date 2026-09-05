from fastapi import APIRouter, Header, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import json

logger = logging.getLogger(__name__)

router = APIRouter()

# Optional shared-secret for webhook authentication.
# Only enforced when VEXYL_WEBHOOK_TOKEN is set in the environment.
_WEBHOOK_TOKEN = os.environ.get("VEXYL_WEBHOOK_TOKEN", "")


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
    payload: VexylWebhookRequest,
    x_webhook_token: Optional[str] = Header(None, alias="X-Webhook-Token"),
):
    """
    Webhook for VEXYL Gateway Custom LLM.
    Receives transcribed text -> calls ORCA Conversational Copilot -> returns text for TTS.
    """
    # Verify shared-secret when configured
    if _WEBHOOK_TOKEN and x_webhook_token != _WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing webhook token")

    logger.debug(f"[VOICE] Received webhook for session {payload.sessionId}")
    
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

@router.post("/transcribe", response_model=VexylWebhookResponse)
async def voice_transcribe(
    audio: UploadFile = File(...),
    sessionId: str = Form(default=""),
    history: str = Form(default="[]"),
):
    """
    Direct Audio REST Endpoint using Groq whisper-large-v3.
    """
    import json
    try:
        history_list = json.loads(history)
    except:
        history_list = []
        
    try:
        from groq import Groq
        from app.config import settings
        groq_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if not groq_key:
            return VexylWebhookResponse(response="Groq API key not configured.", action="continue")
            
        client = Groq(api_key=groq_key)
        audio_content = await audio.read()
        
        filename = audio.filename if audio.filename else "audio.webm"
        if not filename.endswith((".webm", ".wav", ".mp3", ".ogg", ".m4a")):
            filename += ".webm"
            
        logger.info(f"[VOICE] Transcribing audio ({len(audio_content)} bytes) using Groq whisper-large-v3")
        transcription = client.audio.transcriptions.create(
            file=(filename, audio_content),
            model="whisper-large-v3",
            response_format="json",
            language="en"
        )
        
        transcribed_text = transcription.text
        logger.info(f"[VOICE] Transcription: {transcribed_text}")
        
        if not transcribed_text.strip():
            return VexylWebhookResponse(response="I didn't catch that.", action="continue")
            
        return VexylWebhookResponse(
            response=transcribed_text,
            action="transcribed"
        )
        
    except Exception as e:
        logger.error(f"[VOICE] Transcription failed: {e}")
        return VexylWebhookResponse(
            response=f"I'm sorry, I encountered an error: {str(e)}",
            action="continue"
        )

