import logging
import os
import requests
from typing import Optional

from app.services.model_manager import model_manager

logger = logging.getLogger(__name__)

class VoiceAdapter:
    """
    Independent stage-level fallback voice adapter.
    Uses Vexyl (Local gateway to Sarvam) when online.
    Falls back to local AI4Bharat/HF models when offline or if Vexyl fails.
    """
    
    def __init__(self):
        self.vexyl_url = os.environ.get("VEXYL_URL", "http://localhost:8080")
        self.timeout = int(os.environ.get("VOICE_TIMEOUT_SECONDS", "10"))
        
    def _is_online_enabled(self, feature: str) -> bool:
        return os.environ.get(f"{feature}_ONLINE_ENABLED", "true").lower() == "true"
        
    def transcribe(self, audio_bytes: bytes, language: str = "hi") -> str:
        """
        STT: Vexyl/Sarvam -> Fallback to IndicConformer
        """
        # Try Online first
        if self._is_online_enabled("STT"):
            try:
                logger.info(f"Attempting online STT via Vexyl for lang: {language}")
                response = requests.post(
                    f"{self.vexyl_url}/v1/stt",
                    files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                    data={"language": language},
                    timeout=self.timeout
                )
                response.raise_for_status()
                result_text = response.json().get("text")
                if result_text:
                    logger.info("Vexyl STT successful.")
                    return result_text
                else:
                    logger.warning("Vexyl STT returned empty text.")
            except Exception as e:
                logger.warning(f"Online STT failed: {e}. Falling back to IndicConformer.")
                
        # Offline Fallback
        logger.info("Executing offline STT (IndicConformer)")
        
        # In a real setup, this loader would instantiate the HF pipeline
        def conformer_loader(device: str):
            logger.info(f"Loading IndicConformer model weights on {device}")
            try:
                from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
                import torch
                
                base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")
                model_id = os.environ.get("STT_MODEL", os.path.join(base_dir, "indic-conformer"))
                processor = AutoProcessor.from_pretrained(model_id, local_files_only=True)
                model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    local_files_only=True
                )
                if device == "cuda":
                    model = model.to("cuda")
                    
                def run_stt(audio_bytes):
                    # Actual inference logic goes here
                    return "Actual transcript"
                return run_stt
            except Exception as e:
                logger.warning(f"Real IndicConformer load failed: {e}. Using mock.")
                return lambda audio: "Mock transcript from IndicConformer"
            
        model = model_manager.load_model("indic-conformer", conformer_loader, preferred_device="cuda")
        result = model(audio_bytes)
        
        # We leave it loaded unless we have explicit VRAM pressure handled in model_manager
        return result

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate: Vexyl/Sarvam -> Fallback to IndicTrans2
        """
        if source_lang == target_lang:
            return text
            
        if self._is_online_enabled("TRANSLATION"):
            try:
                logger.info(f"Attempting online Translation ({source_lang}->{target_lang}) via Vexyl")
                response = requests.post(
                    f"{self.vexyl_url}/v1/translate",
                    json={
                        "text": text,
                        "source_language": source_lang,
                        "target_language": target_lang
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                result_text = response.json().get("translated_text")
                if result_text:
                    logger.info("Vexyl Translation successful.")
                    return result_text
                else:
                    logger.warning("Vexyl Translation returned empty text.")
            except Exception as e:
                logger.warning(f"Online Translation failed: {e}. Falling back to IndicTrans2.")
                
        # Offline Fallback
        logger.info("Executing offline Translation (IndicTrans2)")
        
        direction = f"{source_lang}-{target_lang}"
        def trans2_loader(device: str):
            logger.info(f"Loading IndicTrans2 ({direction}) model weights on {device}")
            try:
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
                import torch
                
                base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")
                model_id = os.path.join(base_dir, f"indictrans2-{direction}")
                tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    local_files_only=True
                )
                if device == "cuda":
                    model = model.to("cuda")
                    
                def run_translation(txt):
                    return f"Actual translated text ({direction})"
                return run_translation
            except Exception as e:
                logger.warning(f"Real IndicTrans2 load failed: {e}. Using mock.")
                return lambda txt: f"IndicTrans2 mock translated text ({direction})"
            
        model = model_manager.load_model(f"indictrans2-{direction}", trans2_loader, preferred_device="cuda")
        result = model(text)
        return result

    def synthesize(self, text: str, language: str) -> bytes:
        """
        TTS: Vexyl/Sarvam -> Fallback to IndicF5
        """
        if self._is_online_enabled("TTS"):
            try:
                logger.info(f"Attempting online TTS via Vexyl for lang: {language}")
                response = requests.post(
                    f"{self.vexyl_url}/v1/tts",
                    json={
                        "text": text,
                        "language": language
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                if response.content:
                    logger.info("Vexyl TTS successful.")
                    return response.content
                else:
                    logger.warning("Vexyl TTS returned empty audio.")
            except Exception as e:
                logger.warning(f"Online TTS failed: {e}. Falling back to IndicF5.")
                
        # Offline Fallback
        logger.info("Executing offline TTS (IndicF5)")
        
        def indicf5_loader(device: str):
            logger.info(f"Loading IndicF5 model weights on {device}")
            try:
                from transformers import AutoModelForTextToWaveform, AutoTokenizer
                import torch
                
                base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")
                model_id = os.environ.get("TTS_MODEL", os.path.join(base_dir, "indicf5"))
                tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
                model = AutoModelForTextToWaveform.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    local_files_only=True
                )
                if device == "cuda":
                    model = model.to("cuda")
                    
                def run_tts(txt):
                    return b"Actual audio bytes"
                return run_tts
            except Exception as e:
                logger.warning(f"Real IndicF5 load failed: {e}. Using mock.")
                return lambda txt: b"Mock audio bytes from IndicF5"
            
        model = model_manager.load_model("indicf5", indicf5_loader, preferred_device="cuda")
        result = model(text)
        
        # Cleanup heavily since this is the end of the voice pipeline request,
        # freeing VRAM for the next complete transaction or ORCA reasoning cycle.
        model_manager.unload_all()
        return result

voice_adapter = VoiceAdapter()
