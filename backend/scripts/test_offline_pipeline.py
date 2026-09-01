#!/usr/bin/env python3
import os
import logging
import asyncio
import wave
import struct

# Force offline mode for all adapters
os.environ["STT_ONLINE_ENABLED"] = "false"
os.environ["TRANSLATION_ONLINE_ENABLED"] = "false"
os.environ["TTS_ONLINE_ENABLED"] = "false"
os.environ["GOOGLE_API_KEY"] = ""

from app.adapters.voice_adapter import voice_adapter
from app.core.llm import get_llm
from langchain_core.messages import HumanMessage
from app.services.model_manager import model_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dummy_wav(filename="dummy_test.wav"):
    """Creates a very short, valid 16kHz mono WAV file."""
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        # Write 0.1 seconds of silence
        for _ in range(1600):
            f.writeframesraw(struct.pack('<h', 0))
    return filename

async def run_end_to_end():
    logger.info("Starting true end-to-end offline pipeline test on 4GB VRAM constraint...")
    
    # 1. Dummy Audio
    wav_path = create_dummy_wav()
    with open(wav_path, "rb") as f:
        audio_bytes = f.read()
    logger.info("Created dummy audio bytes.")
    
    try:
        # 2. Local STT (IndicConformer)
        logger.info("\n--- Phase 1: Local STT (IndicConformer) ---")
        regional_text = voice_adapter.transcribe(audio_bytes, language="hi")
        logger.info(f"STT Output: {regional_text}")
        
        # 3. Local Translation (Regional -> English via IndicTrans2)
        logger.info("\n--- Phase 2: Local Translation (IndicTrans2 HI->EN) ---")
        english_text = voice_adapter.translate(regional_text, source_lang="hi", target_lang="en")
        logger.info(f"Translation Output: {english_text}")
        
        # 4. Local Reasoning (Qwen 7B 4-bit)
        logger.info("\n--- Phase 3: Local Reasoning (Qwen 7B 4-bit) ---")
        llm = get_llm(temperature=0.1)
        # We manually invoke the LLM to bypass the LangGraph for this stress test
        response = llm.invoke([HumanMessage(content=f"Fisher asks: {english_text}. Generate a short safety advisory JSON.")])
        english_advisory = getattr(response, 'content', str(response))
        logger.info(f"Qwen Output: {english_advisory[:100]}...")
        
        # 5. Local Translation (English -> Regional via IndicTrans2)
        logger.info("\n--- Phase 4: Local Translation (IndicTrans2 EN->HI) ---")
        regional_advisory = voice_adapter.translate(english_advisory, source_lang="en", target_lang="hi")
        logger.info(f"Translation Output: {regional_advisory[:100]}...")
        
        # 6. Local TTS (IndicF5)
        logger.info("\n--- Phase 5: Local TTS (IndicF5) ---")
        tts_bytes = voice_adapter.synthesize(regional_advisory, language="hi")
        logger.info(f"TTS Output: Generated {len(tts_bytes)} bytes of audio.")
        
        print("\n================================")
        print("✅ OFFLINE READY = true")
        print("The entire voice pipeline successfully ran sequentially without OOM!")
        print("================================\n")
        
    except Exception as e:
        logger.error(f"❌ OFFLINE READY = false. End-to-end test failed: {e}")
        exit(1)
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
        model_manager.unload_all()

if __name__ == "__main__":
    asyncio.run(run_end_to_end())
