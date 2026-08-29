"""
test_m4_contract_fixes.py
=========================
Verification for the frozen-contract / demo-constraint audit items:
  - rolling fallback timestamps
  - shared Open-Meteo marine cache (weather + SST)
  - thin graph nodes
"""
import os
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import httpx

from backend.app.adapters.open_meteo_adapter import OpenMeteoAdapter
from backend.app.adapters.open_meteo_client import clear_open_meteo_cache
from backend.app.adapters.relative_time import iso_from_hour_offset, resolve_record_time, resolve_validity_window
from backend.app.adapters.sst_adapter import SSTAdapter
from backend.app.adapters.static_hazard_adapter import StaticHazardAdapter
from backend.app.adapters.static_pfz_adapter import StaticPFZAdapter
from backend.app.graph.nodes.marine import marine_node
from backend.app.graph.nodes.weather import weather_node


class TestRelativeFallbackFiles(unittest.TestCase):

    def test_iso_from_hour_offset_tracks_current_hour(self):
        now = datetime(2026, 9, 1, 10, 44, tzinfo=timezone.utc)
        iso = iso_from_hour_offset(2, now=now)
        self.assertEqual(iso, "2026-09-01T12:00:00Z")

    def test_marine_sample_uses_hour_offset_not_fixed_august(self):
        path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "data", "fallback", "marine_forecast_sample.json",
        )
        import json
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertGreater(len(data["forecasts"]), 0)
        for rec in data["forecasts"]:
            self.assertIn("hour_offset", rec)
            self.assertNotIn("2026-08-21", str(rec.get("time", "")))
        resolved = resolve_record_time(data["forecasts"][0])
        self.assertTrue(resolved.endswith("Z"))

    def test_open_meteo_fallback_resolves_near_now(self):
        clear_open_meteo_cache()
        adapter = OpenMeteoAdapter()
        now_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        ts = now_hour.strftime("%Y-%m-%dT%H:00:00Z")
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = adapter.fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertTrue(result["resolved"], msg="rolling marine fallback must match current hour")
        self.assertEqual(result["provenance"]["fallback_tier"], 3)
        self.assertIsNotNone(result["wave_height_m"])

    def test_pfz_fallback_valid_window_covers_now(self):
        adapter = StaticPFZAdapter()
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = adapter.fetch_data(lat=14.65, lon=74.40, radius_km=100.0)
        self.assertTrue(result["resolved"])
        self.assertGreater(len(result["pfzs"]), 0)
        now = datetime.now(timezone.utc)
        vf = datetime.fromisoformat(result["pfzs"][0]["valid_from"].replace("Z", "+00:00"))
        vu = datetime.fromisoformat(result["pfzs"][0]["valid_until"].replace("Z", "+00:00"))
        self.assertLessEqual(vf, now)
        self.assertGreaterEqual(vu, now)

    def test_hazard_fallback_window_covers_now(self):
        adapter = StaticHazardAdapter()
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = adapter.fetch_hazards_for_bbox(
                bbox={"lat_min": 8.0, "lat_max": 16.0, "lon_min": 72.0, "lon_max": 77.0},
                time_window={"from": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "to": None},
            )
        self.assertTrue(result["resolved"])
        self.assertGreater(len(result["hazards"]), 0)


class TestSharedOpenMeteoMarineCache(unittest.TestCase):

    def setUp(self):
        clear_open_meteo_cache()

    def test_weather_then_sst_issues_one_marine_http_get(self):
        ts = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        ts = ts.strftime("%Y-%m-%dT%H:00:00Z")
        t_naive = ts.replace("Z", "")
        marine = {
            "hourly": {
                "time": [t_naive],
                "wave_height": [1.4],
                "wave_direction": [220.0],
                "swell_wave_height": [0.7],
                "swell_wave_direction": [200.0],
                "sea_surface_temperature": [28.8],
                "ocean_current_velocity": [1.1],
                "ocean_current_direction": [90.0],
            }
        }
        weather = {
            "hourly": {
                "time": [t_naive],
                "wind_speed_10m": [20.0],
                "wind_direction_10m": [180.0],
                "visibility": [8000.0],
            }
        }
        calls = {"marine": 0, "weather": 0}

        def _get(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            if "marine-api" in url:
                calls["marine"] += 1
                mock_resp.json.return_value = marine
            else:
                calls["weather"] += 1
                mock_resp.json.return_value = weather
            return mock_resp

        with patch("httpx.Client.get", side_effect=_get):
            w = OpenMeteoAdapter().fetch_data(12.87, 74.84, ts)
            s = SSTAdapter().fetch_data(12.87, 74.84, ts)

        self.assertEqual(calls["marine"], 1)
        self.assertEqual(calls["weather"], 1)
        self.assertAlmostEqual(w["wave_height_m"], 1.4)
        self.assertAlmostEqual(s["sst_celsius"], 28.8)
        self.assertEqual(s["provenance"]["fallback_tier"], 1)


class TestThinGraphNodes(unittest.TestCase):

    @patch("backend.app.graph.nodes.weather.fetch_weather_forecast_batch")
    @patch("backend.app.graph.nodes.weather.fetch_hazard_alerts")
    def test_weather_node_calls_tools_only(self, mock_haz, mock_batch):
        mock_batch.return_value = [{"waypoint_index": 0, "weather": {}}]
        mock_haz.return_value = {"hazards": [], "cyclone_active": False}
        waypoints = [{"waypoint_index": 0, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T06:00:00Z"}]
        out = weather_node({
            "waypoints": waypoints,
            "bbox": {"lat_min": 10, "lat_max": 14, "lon_min": 73, "lon_max": 76},
        })
        mock_batch.assert_called_once_with(waypoints)
        mock_haz.assert_called_once()
        self.assertIn("weather_observations", out)
        self.assertIn("hazard_alerts", out)

    @patch("backend.app.graph.nodes.marine.fetch_pfz")
    @patch("backend.app.graph.nodes.marine.fetch_marine_forecast_batch")
    def test_marine_node_calls_tools_only(self, mock_batch, mock_pfz):
        mock_pfz.return_value = {"pfzs": []}
        mock_batch.return_value = []
        waypoints = [{"waypoint_index": 0, "lat": 12.87, "lon": 74.84, "eta_iso": "x", "phase": "FISHING"}]
        out = marine_node({
            "origin": {"lat": 12.87, "lon": 74.84},
            "waypoints": waypoints,
        })
        mock_pfz.assert_called_once()
        mock_batch.assert_called_once_with(waypoints)
        self.assertIn("pfz_data", out)
        self.assertIn("marine_observations", out)


class TestRelativeValidityHelper(unittest.TestCase):

    def test_resolve_validity_window_prefers_offsets(self):
        now = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        out = resolve_validity_window(
            {
                "valid_from": "2020-01-01T00:00:00Z",
                "valid_until": "2020-01-02T00:00:00Z",
                "valid_from_offset_hours": -2,
                "valid_until_offset_hours": 5,
            },
            now=now,
        )
        self.assertEqual(out["valid_from"], "2026-09-01T08:00:00Z")
        self.assertEqual(out["valid_until"], "2026-09-01T15:00:00Z")


if __name__ == "__main__":
    unittest.main()
