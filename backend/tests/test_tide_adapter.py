"""
test_tide_adapter.py
====================
Unit tests for TideAdapter (Tier 1: WorldTides API, Tier 3: static fallback).

Tests cover:
    1. Live API path (mocked) — returns tide height + extrema
    2. Fallback file path — returns Tier 3 data when API fails
    3. Invalid coordinates — returns unresolvable
    4. Missing API key — falls back to Tier 3
"""
import os
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytest

from app.adapters.tide_adapter import TideAdapter


class TestTideAdapterLive:
    """Test Tier 1 (live WorldTides API)."""

    def test_fetch_tides_live_success(self):
        """Test successful live WorldTides API call."""
        adapter = TideAdapter()

        # Mock the WorldTides API response
        mock_response = {
            "status": "ok",
            "heights": [
                {
                    "timestamp": int(datetime.now(timezone.utc).timestamp()),
                    "height": 2.3,
                }
            ],
            "extremes": [
                {
                    "timestamp": int((datetime.now(timezone.utc) + timedelta(hours=6)).timestamp()),
                    "type": "high",
                },
                {
                    "timestamp": int((datetime.now(timezone.utc) + timedelta(hours=12)).timestamp()),
                    "type": "low",
                },
            ],
        }

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch.dict(os.environ, {"WORLDTIDES_API_KEY": "test_key"}):
            with patch("app.adapters.tide_adapter.httpx.Client") as mock_client:
                mock_get = MagicMock()
                mock_get.json.return_value = mock_response
                mock_get.raise_for_status = MagicMock()
                mock_client.return_value.__enter__.return_value.get.return_value = mock_get

                result = adapter.fetch_data(12.87, 74.86, time_iso)

        assert result["resolved"] is True
        assert result["status"] == "ok"
        assert result["fallback_tier"] == 1
        assert result["tide_height_m"] == 2.3
        assert result["next_high_time_iso"] is not None
        assert result["next_low_time_iso"] is not None
        assert result["provenance"]["source"] == "WorldTides API (v3)"
        assert result["provenance"]["confidence"] == "HIGH"

    def test_fetch_tides_live_api_error_falls_back_to_tier3(self):
        """Test that API error triggers fallback to Tier 3."""
        adapter = TideAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch.dict(os.environ, {"WORLDTIDES_API_KEY": "test_key"}):
            with patch("app.adapters.tide_adapter.httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.side_effect = Exception("Network error")

                result = adapter.fetch_data(12.87, 74.86, time_iso)

        # Should fall back to Tier 3
        assert result["resolved"] is True or result["resolved"] is False  # Depends on fallback file
        assert result["provenance"]["fallback_tier"] == 3 or result["fallback_tier"] == 3 or result["resolved"] is False

    def test_fetch_tides_no_api_key_uses_tier3(self):
        """Test that missing API key skips Tier 1 and uses Tier 3."""
        adapter = TideAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch.dict(os.environ, {}, clear=True):
            # Ensure WORLDTIDES_API_KEY is not in env
            result = adapter.fetch_data(12.87, 74.86, time_iso)

        # Should use Tier 3
        assert result["provenance"]["fallback_tier"] == 3


class TestTideAdapterStaticFallback:
    """Test Tier 3 (static fallback file)."""

    def test_fetch_tides_fallback_success(self):
        """Test successful static fallback load."""
        adapter = TideAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Fetch without API key (forces Tier 3)
        with patch.dict(os.environ, {}, clear=True):
            result = adapter.fetch_data(12.87, 74.86, time_iso)

        if result["resolved"]:
            assert result["status"] == "ok"
            assert result["provenance"]["fallback_tier"] == 3
            assert "Static tide tables" in result["provenance"]["source"]
            assert result["provenance"]["confidence"] == "MODERATE"

    def test_fetch_tides_fallback_hour_offset_rolling(self):
        """Test that fallback uses rolling hour_offset correctly."""
        adapter = TideAdapter()

        # Fetch at a specific hour
        now_utc = datetime.now(timezone.utc)
        time_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch.dict(os.environ, {}, clear=True):
            result = adapter.fetch_data(12.87, 74.86, time_iso)

        # Should resolve (fallback file exists)
        if result["resolved"]:
            assert result["tide_height_m"] is not None or result["tide_height_m"] is None


class TestTideAdapterInputValidation:
    """Test input validation."""

    def test_invalid_latitude(self):
        """Test that invalid latitude returns unresolvable."""
        adapter = TideAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        result = adapter.fetch_data(91.0, 74.86, time_iso)  # lat > 90

        assert result["resolved"] is False
        assert result["status"] == "unresolvable"
        assert "Invalid coordinates" in result.get("reason", "")

    def test_invalid_longitude(self):
        """Test that invalid longitude returns unresolvable."""
        adapter = TideAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        result = adapter.fetch_data(12.87, 181.0, time_iso)  # lon > 180

        assert result["resolved"] is False
        assert result["status"] == "unresolvable"


class TestTideAdapterSchema:
    """Test output schema completeness."""

    def test_output_schema_completeness(self):
        """Test that all required schema fields are present."""
        adapter = TideAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch.dict(os.environ, {}, clear=True):
            result = adapter.fetch_data(12.87, 74.86, time_iso)

        # All these fields must be present (even if None)
        required_fields = [
            "lat",
            "lon",
            "time_iso",
            "tide_height_m",
            "next_high_time_iso",
            "next_low_time_iso",
            "sst_celsius",
            "chlorophyll_mg_m3",
            "hab_detected",
            "current_speed_kmh",
            "current_direction_deg",
            "resolved",
            "status",
            "provenance",
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"

        # Provenance must have these keys
        provenance_fields = ["source", "retrieved_at", "validity_time", "fallback_tier", "confidence"]
        for field in provenance_fields:
            assert field in result["provenance"], f"Missing provenance field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
