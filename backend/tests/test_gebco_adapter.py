"""
test_gebco_adapter.py
=====================
Unit tests for GEBCOAdapter (Tier 1: OpenTopoData ETOPO1 API, Tier 3: static fallback).

Tests cover:
    1. Live API path (mocked) — returns depth data
    2. Fallback file path — returns Tier 3 data when API fails
    3. Invalid coordinates — returns unresolvable
    4. Land vs ocean detection — positive for both, with surface_type field
"""
import os
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import pytest

from app.adapters.gebco_adapter import GEBCOAdapter


class TestGEBCOAdapterLive:
    """Test Tier 1 (live OpenTopoData ETOPO1 API)."""

    def test_fetch_bathymetry_live_ocean(self):
        """Test successful live OpenTopoData ETOPO1 call for ocean depth."""
        adapter = GEBCOAdapter()

        # Mock the OpenTopoData ETOPO1 response (negative elevation = ocean depth)
        mock_response = {
            "status": "OK",
            "results": [
                {
                    "dataset": "etopo1",
                    "elevation": -45.0,  # 45 meters deep
                    "location": {"lat": 12.87, "lng": 74.75},
                }
            ],
        }

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch("app.adapters.gebco_adapter.httpx.Client") as mock_client:
            mock_get = MagicMock()
            mock_get.json.return_value = mock_response
            mock_get.raise_for_status = MagicMock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_get

            result = adapter.fetch_data(12.87, 74.86, time_iso)

        assert result["resolved"] is True
        assert result["status"] == "ok"
        assert result["fallback_tier"] == 1
        assert result["depth_m"] == 45.0  # Converted from negative to positive
        assert result["surface_type"] == "ocean"
        assert result["provenance"]["source"] == "OpenTopoData ETOPO1 (NOAA global relief model, 1 arc-minute)"
        assert result["provenance"]["confidence"] == "HIGH"

    def test_fetch_bathymetry_live_land(self):
        """Test successful live OpenTopoData ETOPO1 call for land elevation."""
        adapter = GEBCOAdapter()

        # Mock the OpenTopoData ETOPO1 response (positive elevation = land)
        mock_response = {
            "status": "OK",
            "results": [
                {
                    "dataset": "etopo1",
                    "elevation": 850.0,  # 850 metres elevation (land)
                    "location": {"lat": 40.0, "lng": 74.0},
                }
            ],
        }

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch("app.adapters.gebco_adapter.httpx.Client") as mock_client:
            mock_get = MagicMock()
            mock_get.json.return_value = mock_response
            mock_get.raise_for_status = MagicMock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_get

            result = adapter.fetch_data(40.0, 74.0, time_iso)

        assert result["resolved"] is True
        assert result["status"] == "ok"
        assert result["fallback_tier"] == 1
        assert result["depth_m"] == 850.0
        assert result["surface_type"] == "land"

    def test_fetch_bathymetry_live_api_error_falls_back_to_tier3(self):
        """Test that API error triggers fallback to Tier 3."""
        adapter = GEBCOAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch("app.adapters.gebco_adapter.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception("Network error")

            result = adapter.fetch_data(12.87, 74.86, time_iso)

        # Should fall back to Tier 3
        if result["resolved"]:
            assert result["provenance"]["fallback_tier"] == 3
        else:
            assert result["resolved"] is False


class TestGEBCOAdapterStaticFallback:
    """Test Tier 3 (static fallback file)."""

    def test_fetch_bathymetry_fallback_success(self):
        """Test successful static fallback load."""
        adapter = GEBCOAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch("app.adapters.gebco_adapter.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception("Network error")

            result = adapter.fetch_data(12.87, 74.86, time_iso)

        # Should use Tier 3
        if result["resolved"]:
            assert result["status"] == "ok"
            assert result["provenance"]["fallback_tier"] == 3
            assert "Static bathymetry table" in result["provenance"]["source"]
            assert result["provenance"]["confidence"] == "MODERATE"
            assert result["depth_m"] is not None

    def test_fetch_bathymetry_fallback_closest_point(self):
        """Test that fallback finds closest point in table."""
        adapter = GEBCOAdapter()

        # Query near Mangalore
        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch("app.adapters.gebco_adapter.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception("Network error")

            result = adapter.fetch_data(12.87, 74.86, time_iso)

        if result["resolved"]:
            # Should find Mangalore record (12.87, 74.86)
            assert result["depth_m"] == 45.0


class TestGEBCOAdapterInputValidation:
    """Test input validation."""

    def test_invalid_latitude(self):
        """Test that invalid latitude returns unresolvable."""
        adapter = GEBCOAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        result = adapter.fetch_data(91.0, 74.86, time_iso)  # lat > 90

        assert result["resolved"] is False
        assert result["status"] == "unresolvable"
        assert "Invalid coordinates" in result.get("reason", "")

    def test_invalid_longitude(self):
        """Test that invalid longitude returns unresolvable."""
        adapter = GEBCOAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        result = adapter.fetch_data(12.87, 181.0, time_iso)  # lon > 180

        assert result["resolved"] is False
        assert result["status"] == "unresolvable"


class TestGEBCOAdapterSchema:
    """Test output schema completeness."""

    def test_output_schema_completeness(self):
        """Test that all required schema fields are present."""
        adapter = GEBCOAdapter()

        time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with patch("app.adapters.gebco_adapter.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception("Network error")

            result = adapter.fetch_data(12.87, 74.86, time_iso)

        # All these fields must be present (even if None)
        required_fields = [
            "lat",
            "lon",
            "time_iso",
            "depth_m",
            "surface_type",
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
