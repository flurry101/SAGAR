"""
test_open_meteo_adapter.py
==========================
Comprehensive unit tests for OpenMeteoAdapter.

ALL HTTP calls are mocked — no internet connectivity required.

Test scenarios covered (per requirements §10):
    1.  Live Marine + Weather APIs respond successfully → all fields present, Tier 1
    2.  Live response includes SST and ocean current fields (from Marine API)
    3.  API timeout (httpx.TimeoutException) → Tier 3 fallback
    4.  API HTTP 500 error → Tier 3 fallback
    5.  Marine response missing wave_height field → value is None (not fabricated)
    6.  Closest forecast time > 3 h → Tier 3 fallback
    7.  Both live AND static fallback exhausted → unresolvable
    8.  wave_height_m is NEVER a fabricated/hardcoded value (None when unresolvable)
    9.  Provenance fallback_tier=1 on live success
    10. Provenance fallback_tier=3 when using static file
    11. Batch tool uses a distinct eta_iso per waypoint
    12. SST null from Marine API → falls through to Tier 3 (Option A)
    13. cyclone_alert is always explicitly None (never False)
"""
import json
import os
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, mock_open

import httpx

from backend.app.adapters.open_meteo_adapter import OpenMeteoAdapter
from backend.app.adapters.open_meteo_client import clear_open_meteo_cache


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

def _future_iso(hours_ahead: int = 2) -> str:
    """Return an ISO 8601 UTC string `hours_ahead` from now (rounded to hour)."""
    dt = datetime.now(timezone.utc) + timedelta(hours=hours_ahead)
    return dt.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:00:00Z")


def _make_marine_json(
    target_iso: str,
    wave: float = 1.5,
    swell: float = 0.9,
    sst: float = 28.3,
    current_v: float = 2.1,
    current_d: float = 135.0,
    sst_null: bool = False,
) -> dict:
    """Build a minimal Open-Meteo Marine API JSON response."""
    # Use target_iso as the sole time entry for deterministic matching
    t = target_iso.replace("Z", "").replace("+00:00", "")   # strip tz for Open-Meteo format
    return {
        "hourly": {
            "time":                    [t],
            "wave_height":             [wave],
            "wave_direction":          [220.0],
            "swell_wave_height":       [swell],
            "swell_wave_direction":    [210.0],
            "sea_surface_temperature": [None if sst_null else sst],
            "ocean_current_velocity":  [current_v],
            "ocean_current_direction": [current_d],
        }
    }


def _make_weather_json(target_iso: str, wind: float = 25.0, vis_m: float = 7500.0) -> dict:
    t = target_iso.replace("Z", "").replace("+00:00", "")
    return {
        "hourly": {
            "time":             [t],
            "wind_speed_10m":   [wind],
            "wind_direction_10m": [180.0],
            "visibility":       [vis_m],
        }
    }


def _make_mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Create a mock httpx.Response that returns json_data."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=mock_resp,
        )
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp


def _patch_http(marine_json: dict, weather_json: dict):
    """
    Return a context manager that patches httpx.Client.get so:
        - MARINE_URL calls return marine_json
        - WEATHER_URL calls return weather_json
    """
    def _side_effect(url, **kwargs):
        if "marine-api" in url:
            return _make_mock_response(marine_json)
        return _make_mock_response(weather_json)

    return patch("httpx.Client.get", side_effect=_side_effect)


# ---------------------------------------------------------------------------
# Static fallback fixture (mirrors the file format used by marine_forecast_sample.json)
# ---------------------------------------------------------------------------

def _fallback_json(target_iso: str) -> dict:
    return {
        "disclaimer": "Hand-built test data",
        "forecasts": [
            {
                "time":               target_iso,
                "wave_height_m":      1.1,
                "wave_direction_deg": 200.0,
                "swell_height_m":     0.6,
                "swell_direction_deg": 195.0,
                "wind_speed_kmh":     18.0,
                "wind_direction_deg": 170.0,
                "visibility_km":      6.0,
            }
        ],
    }


# ===========================================================================
# Tests
# ===========================================================================

class TestOpenMeteoAdapterLivePath(unittest.TestCase):
    """Tests for Tier 1 — live API path."""

    def setUp(self):
        clear_open_meteo_cache()

    def _adapter(self):
        return OpenMeteoAdapter()

    # ---- Scenario 1: Full live success ------------------------------------------

    def test_live_success_resolves_true(self):
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts), _make_weather_json(ts)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertTrue(result["resolved"])

    def test_live_success_fallback_tier_is_1(self):
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts), _make_weather_json(ts)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertEqual(result["provenance"]["fallback_tier"], 1)

    def test_live_success_source_is_open_meteo(self):
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts), _make_weather_json(ts)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertIn("Open-Meteo", result["provenance"]["source"])

    def test_live_success_wave_height_from_api(self):
        """wave_height_m must equal the value in the mocked Marine API response."""
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts, wave=2.7), _make_weather_json(ts)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertAlmostEqual(result["wave_height_m"], 2.7, places=3)

    def test_live_success_wind_speed_from_api(self):
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts), _make_weather_json(ts, wind=32.5)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertAlmostEqual(result["wind_speed_kmh"], 32.5, places=3)

    def test_live_success_swell_height_from_api(self):
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts, swell=1.8), _make_weather_json(ts)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertAlmostEqual(result["swell_height_m"], 1.8, places=3)

    def test_live_success_visibility_converted_to_km(self):
        """visibility is returned in metres by Open-Meteo — adapter must divide by 1000."""
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts), _make_weather_json(ts, vis_m=8000.0)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertAlmostEqual(result["visibility_km"], 8.0, places=3)

    # ---- Scenario 2: SST and ocean current from Marine API ----------------------

    def test_live_success_sst_from_marine_api(self):
        """sst_celsius must equal the value from the Marine API — never fabricated."""
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts, sst=29.1), _make_weather_json(ts)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertAlmostEqual(result["sst_celsius"], 29.1, places=3)

    def test_live_success_ocean_current_from_marine_api(self):
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts, current_v=3.4, current_d=95.0), _make_weather_json(ts)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertAlmostEqual(result["current_speed_kmh"],    3.4, places=3)
        self.assertAlmostEqual(result["current_direction_deg"], 95.0, places=3)

    # ---- Scenario 12: SST null from API → fall through to Tier 3 ---------------

    def test_sst_null_from_api_falls_to_tier3(self):
        """
        When Marine API response has sea_surface_temperature=null for a grid cell,
        the full response still succeeds (resolved=True) but sst_celsius comes
        from the Tier 3 fallback file (Option A, approved 2026-08-28).
        The OpenMeteoAdapter returns sst_celsius=None from Tier 3 since the
        static file has no SST values.
        """
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts, sst_null=True), _make_weather_json(ts)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        # The live call still succeeds for wave/swell/wind; sst_celsius is None
        # because the static fallback doesn't carry SST either
        self.assertIsNone(result["sst_celsius"])

    # ---- Scenario 13: cyclone_alert is always None ------------------------------

    def test_cyclone_alert_is_none_not_false(self):
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts), _make_weather_json(ts)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertIsNone(result["cyclone_alert"])


class TestOpenMeteoAdapterFallback(unittest.TestCase):
    """Tests for Tier 3 static fallback path."""

    def setUp(self):
        clear_open_meteo_cache()

    def _adapter(self):
        return OpenMeteoAdapter()

    # ---- Scenario 3: Timeout → Tier 3 ------------------------------------------

    def test_timeout_triggers_tier3_fallback(self):
        ts = _future_iso(2)
        fallback = _fallback_json(ts)
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=json.dumps(fallback))):
                    result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertTrue(result["resolved"])
        self.assertEqual(result["provenance"]["fallback_tier"], 3)

    def test_timeout_fallback_wave_from_static_file(self):
        ts = _future_iso(2)
        fallback = _fallback_json(ts)
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=json.dumps(fallback))):
                    result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertAlmostEqual(result["wave_height_m"], 1.1, places=3)

    # ---- Scenario 4: HTTP 500 → Tier 3 -----------------------------------------

    def test_http_500_triggers_tier3_fallback(self):
        ts = _future_iso(2)
        fallback = _fallback_json(ts)

        def _500_response(url, **kwargs):
            return _make_mock_response({}, status_code=500)

        with patch("httpx.Client.get", side_effect=_500_response):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=json.dumps(fallback))):
                    result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertEqual(result["provenance"]["fallback_tier"], 3)

    # ---- Scenario 5: Missing wave_height field ----------------------------------

    def test_missing_wave_field_returns_none_not_fabricated(self):
        """
        If the Marine API response omits wave_height, the result must be None.
        The adapter must NEVER substitute a hardcoded value.
        """
        ts = _future_iso(2)
        marine = _make_marine_json(ts)
        # Remove wave_height from the response
        del marine["hourly"]["wave_height"]
        weather = _make_weather_json(ts)
        with _patch_http(marine, weather):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertIsNone(result["wave_height_m"])
        # Other fields must still come from the live API
        self.assertEqual(result["provenance"]["fallback_tier"], 1)

    # ---- Scenario 6: Time > 3 h → Tier 3 ----------------------------------------

    def test_time_mismatch_over_3h_triggers_tier3(self):
        """
        If the closest API forecast is more than 3 hours from the requested time,
        the adapter must reject the live data and fall through to Tier 3.
        """
        # Request far-future time that no forecast will cover
        far_future = "2050-01-01T12:00:00Z"
        ts_near    = _future_iso(1)   # file record uses a near time
        fallback   = _fallback_json(ts_near)

        with _patch_http(_make_marine_json(ts_near), _make_weather_json(ts_near)):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=json.dumps(fallback))):
                    result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=far_future)
        # Static fallback record is also near (not 2050), so it too will be rejected
        # → unresolvable
        self.assertFalse(result["resolved"])
        self.assertEqual(result["status"], "unresolvable")

    # ---- Scenario 9 & 10: Provenance tier correctness ---------------------------

    def test_provenance_tier1_on_live_success(self):
        ts = _future_iso(2)
        with _patch_http(_make_marine_json(ts), _make_weather_json(ts)):
            result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertEqual(result["provenance"]["fallback_tier"], 1)
        self.assertEqual(result["provenance"]["confidence"], "HIGH")

    def test_provenance_tier3_on_fallback(self):
        ts = _future_iso(2)
        fallback = _fallback_json(ts)
        with patch("httpx.Client.get", side_effect=httpx.ConnectError("no route")):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=json.dumps(fallback))):
                    result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertEqual(result["provenance"]["fallback_tier"], 3)
        self.assertEqual(result["provenance"]["confidence"], "MODERATE")


class TestOpenMeteoAdapterUnresolvable(unittest.TestCase):
    """Tests for the fully exhausted / unresolvable path."""

    def setUp(self):
        clear_open_meteo_cache()

    def _adapter(self):
        return OpenMeteoAdapter()

    # ---- Scenario 7: Both tiers exhausted → unresolvable -----------------------

    def test_fully_exhausted_returns_unresolvable(self):
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("os.path.exists", return_value=False):  # static file missing
                result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=_future_iso(2))
        self.assertFalse(result["resolved"])
        self.assertEqual(result["status"], "unresolvable")

    # ---- Scenario 8: wave_height_m NEVER fabricated ----------------------------

    def test_wave_height_is_none_when_unresolvable(self):
        """wave_height_m must be None on unresolvable — never 0.0 or any guessed value."""
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("os.path.exists", return_value=False):
                result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=_future_iso(2))
        self.assertIsNone(result["wave_height_m"])

    def test_wind_speed_is_none_when_unresolvable(self):
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("os.path.exists", return_value=False):
                result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=_future_iso(2))
        self.assertIsNone(result["wind_speed_kmh"])

    def test_swell_is_none_when_unresolvable(self):
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("os.path.exists", return_value=False):
                result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=_future_iso(2))
        self.assertIsNone(result["swell_height_m"])

    def test_unresolvable_provenance_has_correct_shape(self):
        """Even on unresolvable, provenance must be present with source=None, confidence=LOW."""
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("os.path.exists", return_value=False):
                result = self._adapter().fetch_data(lat=12.87, lon=74.84, timestamp=_future_iso(2))
        prov = result["provenance"]
        self.assertIn("source", prov)
        self.assertIn("retrieved_at", prov)
        self.assertIn("validity_time", prov)
        self.assertIn("fallback_tier", prov)
        self.assertIn("confidence", prov)
        self.assertIsNone(prov["source"])
        self.assertEqual(prov["confidence"], "LOW")


class TestOpenMeteoAdapterBatch(unittest.TestCase):
    """Tests for the batch tool's per-waypoint ETA handling."""

    # ---- Scenario 11: Each waypoint uses its own eta_iso ----------------------

    def test_batch_calls_adapter_per_waypoint_eta(self):
        """
        fetch_weather_forecast_batch must call the adapter with each waypoint's
        individual eta_iso — not a shared timestamp.
        """
        from backend.app.tools.weather_tools import fetch_weather_forecast_batch

        ts_a = "2026-08-28T06:00:00Z"
        ts_b = "2026-08-28T10:00:00Z"
        waypoints = [
            {"waypoint_index": 0, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84, "eta_iso": ts_a},
            {"waypoint_index": 1, "phase": "RETURN",   "lat": 12.90, "lon": 74.90, "eta_iso": ts_b},
        ]

        mock_obs = {
            "lat": 12.87, "lon": 74.84, "time_iso": ts_a,
            "wave_height_m": 1.2, "wind_speed_kmh": 20.0,
            "wind_direction_deg": 200, "swell_height_m": 0.8,
            "swell_direction_deg": 195, "cyclone_alert": None,
            "visibility_km": 7.0, "sst_celsius": None,
            "current_speed_kmh": None, "current_direction_deg": None,
            "resolved": True,
            "provenance": {
                "source": "Open-Meteo Marine & Weather API",
                "retrieved_at": "2026-08-28T05:30:00Z",
                "validity_time": ts_a,
                "fallback_tier": 1,
                "confidence": "HIGH",
            },
        }

        with patch("backend.app.tools.weather_tools._weather_adapter") as mock_adapter:
            mock_adapter.fetch_data.return_value = mock_obs
            results = fetch_weather_forecast_batch(waypoints)

        # Two calls, one per waypoint
        self.assertEqual(mock_adapter.fetch_data.call_count, 2)

        # Verify each call used its waypoint's eta_iso
        call_timestamps = [call.args[2] for call in mock_adapter.fetch_data.call_args_list]
        self.assertIn(ts_a, call_timestamps)
        self.assertIn(ts_b, call_timestamps)

    def test_batch_result_count_matches_waypoint_count(self):
        from backend.app.tools.weather_tools import fetch_weather_forecast_batch

        waypoints = [
            {"waypoint_index": i, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84,
             "eta_iso": f"2026-08-28T0{i}:00:00Z"}
            for i in range(3)
        ]
        mock_obs = {
            "wave_height_m": 1.0, "wind_speed_kmh": 20.0, "wind_direction_deg": 200,
            "swell_height_m": 0.5, "swell_direction_deg": 190, "cyclone_alert": None,
            "visibility_km": 8.0, "sst_celsius": None,
            "current_speed_kmh": None, "current_direction_deg": None,
            "resolved": True,
            "provenance": {"source": "x", "retrieved_at": "x", "validity_time": "x",
                           "fallback_tier": 1, "confidence": "HIGH"},
        }
        with patch("backend.app.tools.weather_tools._weather_adapter") as mock_adapter:
            mock_adapter.fetch_data.return_value = mock_obs
            results = fetch_weather_forecast_batch(waypoints)
        self.assertEqual(len(results), 3)


# ===========================================================================
# Time-parsing and _closest_index helper tests
# ===========================================================================

class TestOpenMeteoAdapterHelpers(unittest.TestCase):

    def test_parse_utc_handles_z_suffix(self):
        dt = OpenMeteoAdapter._parse_utc("2026-08-28T14:00:00Z")
        self.assertEqual(dt.tzinfo, timezone.utc)
        self.assertEqual(dt.hour, 14)

    def test_parse_utc_handles_plus_offset(self):
        dt = OpenMeteoAdapter._parse_utc("2026-08-28T19:30:00+05:30")
        self.assertEqual(dt.hour, 14)   # converted to UTC

    def test_parse_utc_returns_now_when_none(self):
        dt = OpenMeteoAdapter._parse_utc(None)
        now = datetime.now(timezone.utc)
        self.assertLess(abs((now - dt).total_seconds()), 2.0)

    def test_closest_index_exact_match(self):
        times = ["2026-08-28T06:00", "2026-08-28T07:00", "2026-08-28T08:00"]
        target = OpenMeteoAdapter._parse_utc("2026-08-28T07:00:00Z")
        idx, diff = OpenMeteoAdapter._closest_index(times, target)
        self.assertEqual(idx, 1)
        self.assertEqual(diff, 0.0)

    def test_closest_index_empty_list(self):
        target = OpenMeteoAdapter._parse_utc("2026-08-28T07:00:00Z")
        idx, diff = OpenMeteoAdapter._closest_index([], target)
        self.assertEqual(idx, -1)
        self.assertEqual(diff, float("inf"))


if __name__ == "__main__":
    unittest.main()
