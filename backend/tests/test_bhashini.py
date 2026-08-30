"""
Test Suite — Bhashini Translation

Tests the Bhashini adapter and translation node behavior.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.adapters.bhashini_adapter import BhashiniAdapter, BHASHINI_SUPPORTED_LANGUAGES
from app.graph.nodes.translation import translation_node


# ---- Test A: Adapter returns unavailable when not configured ----

def test_bhashini_unconfigured():
    """Adapter should gracefully return unavailable when API key is missing."""
    adapter = BhashiniAdapter(api_key="", user_id="")
    result = adapter.translate("Hello", "en", "hi")
    assert result["success"] is False
    assert result["translation_provider"] == "unavailable"
    assert "not configured" in result["error"]


# ---- Test B: Passthrough for same language ----

def test_bhashini_same_language():
    """If source == target, no API call should be made."""
    adapter = BhashiniAdapter(api_key="test", user_id="test")
    result = adapter.translate("Hello", "en", "en")
    assert result["success"] is True
    assert result["translated_text"] == "Hello"
    assert result["translation_provider"] == "passthrough"


# ---- Test C: Unsupported language ----

def test_bhashini_unsupported_language():
    """Unsupported languages should return an error."""
    adapter = BhashiniAdapter(api_key="test", user_id="test")
    result = adapter.translate("Hello", "en", "xx")
    assert result["success"] is False
    assert "not supported" in result["error"]


# ---- Test D: Supported languages list ----

def test_bhashini_supported_languages():
    """All 10 Indian languages should be supported."""
    expected = {"hi", "ta", "te", "kn", "ml", "bn", "mr", "gu", "pa", "or"}
    assert BHASHINI_SUPPORTED_LANGUAGES == expected


# ---- Test E: Translation node skips English ----

def test_translation_node_skips_english():
    """Translation node should skip when language is English."""
    state = {
        "advisory": {
            "recommendation_text": "Avoid departure at 05:00.",
            "reason": "High waves detected.",
            "language": "en",
        },
        "trip_context": {"language": "en"},
        "agent_executions": [],
    }
    result = translation_node(state)
    assert result["advisory"]["translation_provider"] == "none_required"
    assert result["advisory"]["recommendation_text"] == "Avoid departure at 05:00."


# ---- Test F: Translation node uses Gemini fallback when Bhashini not configured ----

def test_translation_node_gemini_fallback():
    """When Bhashini is not configured, should attempt Gemini fallback."""
    state = {
        "advisory": {
            "recommendation_text": "Avoid departure.",
            "reason": "High waves.",
            "language": "hi",
        },
        "trip_context": {"language": "hi"},
        "agent_executions": [],
    }

    # Without GOOGLE_API_KEY set, both should fail
    with patch.dict("os.environ", {"GOOGLE_API_KEY": ""}, clear=False):
        result = translation_node(state)
        # Should fall through to unavailable since both Bhashini and Gemini are unconfigured
        assert result["advisory"]["translation_provider"] in ("unavailable", "gemini_fallback")


# ---- Test G: Empty text handling ----

def test_bhashini_empty_text():
    """Empty text should be handled gracefully."""
    adapter = BhashiniAdapter(api_key="test", user_id="test")
    result = adapter.translate("", "en", "hi")
    assert result["success"] is False
    assert "Empty" in result["error"]
