import pytest
import os
from app.adapters.voice_adapter import voice_adapter
from unittest.mock import patch

def test_transcribe_fallback():
    # Force online STT to fail (already mocked in the adapter to fail)
    os.environ["STT_ONLINE_ENABLED"] = "true"
    
    # Should fall back to IndicConformer
    result = voice_adapter.transcribe(b"dummy_audio", "hi")
    assert "IndicConformer" in result

def test_translate_fallback():
    os.environ["TRANSLATION_ONLINE_ENABLED"] = "true"
    
    # Should fall back to IndicTrans2
    result = voice_adapter.translate("hello", "en", "hi")
    assert "IndicTrans2" in result

def test_synthesize_fallback():
    os.environ["TTS_ONLINE_ENABLED"] = "true"
    
    # Should fall back to IndicF5
    result = voice_adapter.synthesize("advisory", "hi")
    assert b"IndicF5" in result
