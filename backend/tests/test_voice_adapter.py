import pytest
import os
from unittest.mock import patch, MagicMock
from app.adapters.voice_adapter import voice_adapter


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Ensure env vars set in a test don't leak to other tests."""
    yield
    for key in ("STT_ONLINE_ENABLED", "TRANSLATION_ONLINE_ENABLED", "TTS_ONLINE_ENABLED"):
        monkeypatch.delenv(key, raising=False)


def test_transcribe_fallback(monkeypatch):
    """When the online STT POST fails, the adapter should fall back to IndicConformer."""
    monkeypatch.setenv("STT_ONLINE_ENABLED", "true")

    with patch("requests.post", side_effect=Exception("simulated online STT failure")):
        result = voice_adapter.transcribe(b"dummy_audio", "hi")
    assert "IndicConformer" in result


def test_translate_fallback(monkeypatch):
    """When the online translation POST fails, the adapter should fall back to IndicTrans2."""
    monkeypatch.setenv("TRANSLATION_ONLINE_ENABLED", "true")

    with patch("requests.post", side_effect=Exception("simulated online translation failure")):
        result = voice_adapter.translate("hello", "en", "hi")
    assert "IndicTrans2" in result


def test_synthesize_fallback(monkeypatch):
    """When the online TTS POST fails, the adapter should fall back to IndicF5."""
    monkeypatch.setenv("TTS_ONLINE_ENABLED", "true")

    with patch("requests.post", side_effect=Exception("simulated online TTS failure")):
        result = voice_adapter.synthesize("advisory", "hi")
    assert b"IndicF5" in result

