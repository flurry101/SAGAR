"""
test_tools.py
=============
Unit tests for the LangGraph tool wrappers:
    weather_tools: fetch_wave_forecast, fetch_wind_forecast, fetch_swell_forecast,
                   fetch_hazard_alerts, fetch_weather_forecast_batch
    marine_tools:  fetch_pfz, fetch_sst, detect_hab, fetch_marine_forecast_batch
"""
import unittest
from unittest.mock import patch, MagicMock

from backend.app.tools import weather_tools, marine_tools


# ===========================================================================
# Shared mock observations
# ===========================================================================

MOCK_WEATHER_OBS = {
    "lat": 12.87, "lon": 74.84,
    "time_iso": "2026-08-28T15:00:00Z",
    "wave_height_m": 1.2,
    "wind_speed_kmh": 25.0,
    "wind_direction_deg": 220,
    "swell_height_m": 0.8,
    "swell_direction_deg": 210,
    "cyclone_alert": None,
    "visibility_km": 7.5,
    "resolved": True,
    "provenance": {
        "source": "Open-Meteo Marine & Weather API",
        "retrieved_at": "2026-08-28T14:30:00Z",
        "validity_time": "2026-08-28T15:00:00Z",
        "fallback_tier": 1,
        "confidence": "HIGH",
    },
}

MOCK_HAZARD_RESULT = {
    "hazards": [{"hazard_id": "HAZ-001", "hazard_type": "HIGH_WAVES"}],
    "cyclone_active": False,
    "resolved": True,
    "status": "ok",
    "provenance": {
        "source": "IMD (Static Fallback)",
        "retrieved_at": "2026-08-28T14:30:00Z",
        "validity_time": None,
        "fallback_tier": 3,
        "confidence": "MODERATE",
    },
}

MOCK_PFZ_RESULT = {
    "pfzs": [{"pfz_id": "PFZ-KA-002", "coordinates": {"lat": 12.75, "lon": 74.10}}],
    "resolved": True,
    "status": "ok",
    "provenance": {
        "source": "INCOIS PFZ Advisory (Static Fallback)",
        "retrieved_at": "2026-08-28T14:30:00Z",
        "validity_time": None,
        "fallback_tier": 3,
        "confidence": "MODERATE",
    },
}

MOCK_SST_OBS = {
    "lat": 12.87, "lon": 74.84,
    "time_iso": "2026-08-28T15:00:00Z",
    "sst_celsius": 27.5,
    "chlorophyll_mgm3": None,
    "hab_detected": None,
    "hab_probability": None,
    "current_speed_kmh": None,
    "current_direction_deg": None,
    "resolved": True,
    "status": "ok",
    "provenance": {
        "source": "NOAA WOA2023 Climatology",
        "retrieved_at": "2026-08-28T14:30:00Z",
        "validity_time": "2026-08-28T15:00:00Z",
        "fallback_tier": 3,
        "confidence": "MODERATE",
    },
}

MOCK_HAB_OBS = {
    "lat": 12.87, "lon": 74.84,
    "time_iso": "2026-08-28T15:00:00Z",
    "sst_celsius": None,
    "chlorophyll_mgm3": None,
    "hab_detected": False,
    "hab_probability": 0.05,
    "current_speed_kmh": None,
    "current_direction_deg": None,
    "resolved": True,
    "provenance": {
        "source": "AMFITRITE-Sentinel2-HAB-RDNet (Mock Dataset)",
        "retrieved_at": "2026-08-28T14:30:00Z",
        "validity_time": "2026-08-28T15:00:00Z",
        "fallback_tier": 3,
        "confidence": "MODERATE",
    },
}


# ===========================================================================
# Weather Tools
# ===========================================================================

class TestWeatherTools(unittest.TestCase):

    # ---- fetch_wave_forecast -----------------------------------------------

    @patch("backend.app.tools.weather_tools._weather_adapter")
    def test_fetch_wave_forecast_returns_wave_and_provenance(self, mock_adapter):
        mock_adapter.fetch_data.return_value = MOCK_WEATHER_OBS
        result = weather_tools.fetch_wave_forecast(lat=12.87, lon=74.84, time_iso="2026-08-28T15:00:00Z")
        self.assertIn("wave_height_m", result)
        self.assertIn("provenance", result)
        self.assertEqual(result["wave_height_m"], 1.2)
        self.assertNotIn("wind_speed_kmh", result)   # only wave

    # ---- fetch_wind_forecast -----------------------------------------------

    @patch("backend.app.tools.weather_tools._weather_adapter")
    def test_fetch_wind_forecast_returns_wind_and_provenance(self, mock_adapter):
        mock_adapter.fetch_data.return_value = MOCK_WEATHER_OBS
        result = weather_tools.fetch_wind_forecast(lat=12.87, lon=74.84, time_iso="2026-08-28T15:00:00Z")
        self.assertIn("wind_speed_kmh", result)
        self.assertIn("wind_direction_deg", result)
        self.assertIn("provenance", result)
        self.assertEqual(result["wind_speed_kmh"], 25.0)
        self.assertEqual(result["wind_direction_deg"], 220)

    # ---- fetch_swell_forecast ----------------------------------------------

    @patch("backend.app.tools.weather_tools._weather_adapter")
    def test_fetch_swell_forecast_returns_swell_and_provenance(self, mock_adapter):
        mock_adapter.fetch_data.return_value = MOCK_WEATHER_OBS
        result = weather_tools.fetch_swell_forecast(lat=12.87, lon=74.84, time_iso="2026-08-28T15:00:00Z")
        self.assertIn("swell_height_m", result)
        self.assertIn("swell_direction_deg", result)
        self.assertIn("provenance", result)
        self.assertEqual(result["swell_height_m"], 0.8)
        self.assertEqual(result["swell_direction_deg"], 210)

    # ---- fetch_hazard_alerts -----------------------------------------------

    @patch("backend.app.tools.weather_tools._hazard_adapter")
    def test_fetch_hazard_alerts_returns_list_and_cyclone_flag(self, mock_adapter):
        mock_adapter.fetch_hazards_for_bbox.return_value = MOCK_HAZARD_RESULT
        result = weather_tools.fetch_hazard_alerts(
            bbox={"lat_min": 10.0, "lat_max": 14.0, "lon_min": 73.0, "lon_max": 76.0},
            time_window={"from": "2026-08-22T00:00:00Z", "to": "2026-08-23T00:00:00Z"},
        )
        self.assertIn("hazards", result)
        self.assertIn("cyclone_active", result)
        self.assertIn("provenance", result)
        self.assertFalse(result["cyclone_active"])
        self.assertEqual(len(result["hazards"]), 1)

    # ---- fetch_weather_forecast_batch --------------------------------------

    @patch("backend.app.tools.weather_tools._weather_adapter")
    def test_batch_returns_one_entry_per_waypoint(self, mock_adapter):
        mock_adapter.fetch_data.return_value = MOCK_WEATHER_OBS
        waypoints = [
            {"waypoint_index": 0, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T06:00:00Z"},
            {"waypoint_index": 1, "phase": "FISHING",  "lat": 12.75, "lon": 74.50, "eta_iso": "2026-08-28T08:00:00Z"},
            {"waypoint_index": 2, "phase": "RETURN",   "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T14:00:00Z"},
        ]
        results = weather_tools.fetch_weather_forecast_batch(waypoints)

        self.assertEqual(len(results), 3)
        for i, entry in enumerate(results):
            self.assertIn("waypoint_index", entry)
            self.assertIn("phase", entry)
            self.assertIn("lat", entry)
            self.assertIn("lon", entry)
            self.assertIn("time_iso", entry)
            self.assertIn("weather", entry)
            self.assertEqual(entry["waypoint_index"], i)

    @patch("backend.app.tools.weather_tools._weather_adapter")
    def test_batch_uses_eta_iso_per_waypoint(self, mock_adapter):
        """Verify the adapter is called with each waypoint's eta_iso, not a single shared time."""
        mock_adapter.fetch_data.return_value = MOCK_WEATHER_OBS
        waypoints = [
            {"waypoint_index": 0, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T06:00:00Z"},
            {"waypoint_index": 1, "phase": "RETURN",   "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T14:00:00Z"},
        ]
        weather_tools.fetch_weather_forecast_batch(waypoints)

        call_args = [c.args for c in mock_adapter.fetch_data.call_args_list]
        timestamps_called = [a[2] for a in call_args]
        self.assertIn("2026-08-28T06:00:00Z", timestamps_called)
        self.assertIn("2026-08-28T14:00:00Z", timestamps_called)

    @patch("backend.app.tools.weather_tools._weather_adapter")
    def test_batch_handles_adapter_exception_gracefully(self, mock_adapter):
        mock_adapter.fetch_data.side_effect = RuntimeError("unexpected crash")
        waypoints = [{"waypoint_index": 0, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T06:00:00Z"}]
        results = weather_tools.fetch_weather_forecast_batch(waypoints)
        self.assertEqual(len(results), 1)
        obs = results[0]["weather"]
        self.assertFalse(obs["resolved"])
        self.assertEqual(obs["status"], "unresolvable")
        self.assertIsNone(obs["provenance"]["source"])
        self.assertEqual(obs["provenance"]["confidence"], "LOW")


# ===========================================================================
# Marine Tools
# ===========================================================================

class TestMarineTools(unittest.TestCase):

    def setUp(self):
        marine_tools.clear_hab_roi_cache()

    # ---- fetch_pfz ---------------------------------------------------------

    @patch("backend.app.tools.marine_tools._pfz_adapter")
    def test_fetch_pfz_returns_list_and_provenance(self, mock_adapter):
        mock_adapter.fetch_data.return_value = MOCK_PFZ_RESULT
        result = marine_tools.fetch_pfz(origin={"lat": 12.87, "lon": 74.84}, radius_km=100.0)
        self.assertIn("pfzs", result)
        self.assertIn("provenance", result)
        self.assertEqual(len(result["pfzs"]), 1)
        self.assertEqual(result["pfzs"][0]["pfz_id"], "PFZ-KA-002")

    # ---- fetch_sst ---------------------------------------------------------

    @patch("backend.app.tools.marine_tools._sst_adapter")
    def test_fetch_sst_returns_celsius_and_provenance(self, mock_adapter):
        mock_adapter.fetch_data.return_value = MOCK_SST_OBS
        result = marine_tools.fetch_sst(lat=12.87, lon=74.84, time_iso="2026-08-28T15:00:00Z")
        self.assertIn("sst_celsius", result)
        self.assertIn("provenance", result)
        self.assertEqual(result["sst_celsius"], 27.5)

    @patch("backend.app.tools.marine_tools._pfz_adapter")
    def test_fetch_chlorophyll_returns_adapter_result(self, mock_adapter):
        mock_adapter.fetch_chlorophyll_at_point.return_value = {
            "chlorophyll_mg_m3": 0.8,
            "resolved": True,
            "status": "ok",
            "provenance": {"fallback_tier": 1, "confidence": "HIGH"},
        }
        result = marine_tools.fetch_chlorophyll(12.87, 74.84, "2026-08-28T15:00:00Z")
        self.assertEqual(result["chlorophyll_mg_m3"], 0.8)
        self.assertEqual(result["provenance"]["fallback_tier"], 1)

    @patch("backend.app.tools.marine_tools._sst_adapter")
    @patch("backend.app.tools.marine_tools._hab_adapter")
    def test_marine_batch_does_not_fabricate_chlorophyll(self, mock_hab, mock_sst):
        mock_sst.fetch_data.return_value = MOCK_SST_OBS
        mock_hab.fetch_data.return_value = MOCK_HAB_OBS
        waypoints = [{"waypoint_index": 0, "phase": "FISHING", "lat": 12.87, "lon": 74.84,
                      "eta_iso": "2026-08-28T06:00:00Z"}]
        result = marine_tools.fetch_marine_forecast_batch(waypoints)
        self.assertIsNone(result[0]["marine"]["chlorophyll_mg_m3"])
        self.assertIsNone(result[0]["marine"]["chlorophyll_mgm3"])

    # ---- detect_hab --------------------------------------------------------

    @patch("backend.app.tools.marine_tools._hab_adapter")
    def test_detect_hab_returns_detection_and_provenance(self, mock_adapter):
        mock_adapter.fetch_data.return_value = MOCK_HAB_OBS
        result = marine_tools.detect_hab(lat=12.87, lon=74.84, time_iso="2026-08-28T15:00:00Z")
        self.assertIn("hab_detected", result)
        self.assertIn("hab_probability", result)
        self.assertIn("provenance", result)
        self.assertFalse(result["hab_detected"])
        self.assertEqual(result["hab_probability"], 0.05)

    # ---- fetch_marine_forecast_batch ---------------------------------------

    @patch("backend.app.tools.marine_tools._sst_adapter")
    @patch("backend.app.tools.marine_tools._hab_adapter")
    def test_marine_batch_returns_one_entry_per_waypoint(self, mock_hab, mock_sst):
        mock_sst.fetch_data.return_value = MOCK_SST_OBS
        mock_hab.fetch_data.return_value = MOCK_HAB_OBS
        waypoints = [
            {"waypoint_index": 0, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T06:00:00Z"},
            {"waypoint_index": 1, "phase": "FISHING",  "lat": 12.75, "lon": 74.50, "eta_iso": "2026-08-28T08:00:00Z"},
        ]
        results = marine_tools.fetch_marine_forecast_batch(waypoints)
        self.assertEqual(len(results), 2)

    @patch("backend.app.tools.marine_tools._sst_adapter")
    @patch("backend.app.tools.marine_tools._hab_adapter")
    def test_marine_batch_entry_shape(self, mock_hab, mock_sst):
        mock_sst.fetch_data.return_value = MOCK_SST_OBS
        mock_hab.fetch_data.return_value = MOCK_HAB_OBS
        waypoints = [{"waypoint_index": 0, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T06:00:00Z"}]
        results = marine_tools.fetch_marine_forecast_batch(waypoints)
        entry = results[0]
        for field in ("waypoint_index", "phase", "lat", "lon", "time_iso", "marine"):
            self.assertIn(field, entry, msg=f"Missing field: {field}")

    @patch("backend.app.tools.marine_tools._sst_adapter")
    @patch("backend.app.tools.marine_tools._hab_adapter")
    def test_marine_batch_marine_obs_fields(self, mock_hab, mock_sst):
        mock_sst.fetch_data.return_value = MOCK_SST_OBS
        mock_hab.fetch_data.return_value = MOCK_HAB_OBS
        waypoints = [{"waypoint_index": 0, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T06:00:00Z"}]
        results = marine_tools.fetch_marine_forecast_batch(waypoints)
        obs = results[0]["marine"]
        for field in ("lat", "lon", "time_iso", "sst_celsius", "chlorophyll_mgm3",
                      "hab_detected", "hab_probability", "current_speed_kmh",
                      "current_direction_deg", "resolved", "provenance"):
            self.assertIn(field, obs, msg=f"Missing marine obs field: {field}")

    @patch("backend.app.tools.marine_tools._sst_adapter")
    @patch("backend.app.tools.marine_tools._hab_adapter")
    def test_marine_batch_uses_eta_iso_per_waypoint(self, mock_hab, mock_sst):
        mock_sst.fetch_data.return_value = MOCK_SST_OBS
        mock_hab.fetch_data.return_value = MOCK_HAB_OBS
        waypoints = [
            {"waypoint_index": 0, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T06:00:00Z"},
            {"waypoint_index": 1, "phase": "RETURN",   "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T14:00:00Z"},
        ]
        marine_tools.fetch_marine_forecast_batch(waypoints)
        sst_times = [c.args[2] for c in mock_sst.fetch_data.call_args_list]
        self.assertIn("2026-08-28T06:00:00Z", sst_times)
        self.assertIn("2026-08-28T14:00:00Z", sst_times)

    @patch("backend.app.tools.marine_tools._sst_adapter")
    @patch("backend.app.tools.marine_tools._hab_adapter")
    def test_marine_batch_calls_hab_once_for_trajectory(self, mock_hab, mock_sst):
        mock_sst.fetch_data.return_value = MOCK_SST_OBS
        mock_hab.fetch_data.return_value = MOCK_HAB_OBS
        waypoints = [
            {"waypoint_index": 0, "phase": "OUTBOUND", "lat": 12.87, "lon": 74.84, "eta_iso": "2026-08-28T06:00:00Z"},
            {"waypoint_index": 1, "phase": "FISHING",  "lat": 12.75, "lon": 74.50, "eta_iso": "2026-08-28T08:00:00Z"},
            {"waypoint_index": 2, "phase": "RETURN",   "lat": 12.90, "lon": 74.90, "eta_iso": "2026-08-28T14:00:00Z"},
        ]
        results = marine_tools.fetch_marine_forecast_batch(waypoints)
        self.assertEqual(mock_hab.fetch_data.call_count, 1)
        self.assertEqual(len(results), 3)
        hab_flags = [r["marine"]["hab_detected"] for r in results]
        self.assertEqual(hab_flags, [False, False, False])


if __name__ == "__main__":
    unittest.main()
