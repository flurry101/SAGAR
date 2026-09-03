"""
test_adapters.py
================
Unit tests for all M4 adapters:
    - StaticPFZAdapter (radius filtering, GeoJSON parsing, error path)
    - StaticHazardAdapter (bbox intersection, time-window filtering, cyclone flag)
    - SSTAdapter:
        * Tier 1 live path (mocked HTTP to Open-Meteo Marine API)
        * Option A: null SST from API falls through to Tier 3 climatology
        * Timeout / HTTP error falls through to Tier 3 climatology
        * Climatology fallback (unresolvable on bad timestamp)
        * Provenance never falsely labelled Tier 1 when static is used
    - StaticPFZ / StaticHazard provenance never labels static data as live
    - AmfitriteHABAdapter (normalized schema: time_iso, provenance, graceful mock)
"""
import json
import os
import unittest
from datetime import timezone, datetime, timedelta
from typing import Any, Dict, List
import sys
from unittest.mock import patch, mock_open, MagicMock

# Mock rasterio if it is not installed so that tests can import and run with RASTERIO_AVAILABLE=True
if "rasterio" not in sys.modules:
    _mock_window = MagicMock()
    _mock_window.width  = 10
    _mock_window.height = 10
    _mock_window.intersection.return_value = _mock_window  # intersection returns same mock

    mock_rasterio = MagicMock()
    mock_rasterio.enums.Resampling.nearest  = 1
    mock_rasterio.enums.Resampling.bilinear = 2
    mock_rasterio.windows.from_bounds = MagicMock(return_value=_mock_window)
    mock_rasterio.windows.Window      = MagicMock(return_value=_mock_window)
    # Stub crs and warp so `from rasterio.crs import CRS` succeeds
    mock_rasterio.crs.CRS  = MagicMock()
    mock_rasterio.warp.transform_bounds = MagicMock(return_value=[0.0, 0.0, 1.0, 1.0])

    sys.modules["rasterio"]         = mock_rasterio
    sys.modules["rasterio.windows"] = mock_rasterio.windows
    sys.modules["rasterio.enums"]   = mock_rasterio.enums
    sys.modules["rasterio.crs"]     = mock_rasterio.crs
    sys.modules["rasterio.warp"]    = mock_rasterio.warp

import httpx

from backend.app.adapters.static_pfz_adapter import StaticPFZAdapter, _haversine_km
from backend.app.adapters.static_hazard_adapter import StaticHazardAdapter
from backend.app.adapters.sst_adapter import SSTAdapter
from backend.app.adapters.amfitrite_hab_adapter import AmfitriteHABAdapter
from backend.app.adapters.open_meteo_client import clear_open_meteo_cache


# ---------------------------------------------------------------------------
# Helpers -- shared fixture data
# ---------------------------------------------------------------------------

PFZ_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "pfz_id": "PFZ-TEST-001",
                "source": "Test Source",
                "valid_from": "2026-08-21T00:00:00Z",
                "valid_until": "2026-08-28T23:59:59Z",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [74.20, 12.80],
                        [74.60, 12.80],
                        [74.60, 12.50],
                        [74.20, 12.50],
                        [74.20, 12.80],
                    ]
                ],
            },
        },
        {
            "type": "Feature",
            "properties": {
                "pfz_id": "PFZ-TEST-FAR",
                "source": "Test Source Far",
                "valid_from": "2026-08-21T00:00:00Z",
                "valid_until": "2026-08-28T23:59:59Z",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [80.00, 25.00],
                        [80.50, 25.00],
                        [80.50, 24.50],
                        [80.00, 24.50],
                        [80.00, 25.00],
                    ]
                ],
            },
        },
    ],
}

HAZARD_JSON = {
    "hazards": [
        {
            "hazard_id": "HAZ-001",
            "hazard_type": "HIGH_WAVES",
            "severity": "MODERATE",
            "description": "Big waves",
            "affected_region": {"lat_min": 8.0, "lat_max": 15.0, "lon_min": 72.0, "lon_max": 77.0},
            "valid_from": "2026-08-21T00:00:00Z",
            "valid_until": "2026-08-28T23:59:59Z",
            "source": "IMD (Static Fallback)",
            "cyclone_active": False,
        },
        {
            "hazard_id": "HAZ-CYC",
            "hazard_type": "CYCLONE_WARNING",
            "severity": "SEVERE",
            "description": "Cyclone approaching",
            "affected_region": {"lat_min": 12.0, "lat_max": 22.0, "lon_min": 60.0, "lon_max": 75.0},
            "valid_from": "2026-08-26T00:00:00Z",
            "valid_until": "2026-08-30T23:59:59Z",
            "source": "IMD (Static Fallback)",
            "cyclone_active": True,
        },
        {
            "hazard_id": "HAZ-NORTH",
            "hazard_type": "STRONG_WINDS",
            "severity": "LOW",
            "description": "Winds in north",
            "affected_region": {"lat_min": 20.0, "lat_max": 25.0, "lon_min": 65.0, "lon_max": 70.0},
            "valid_from": "2026-08-21T00:00:00Z",
            "valid_until": "2026-08-28T23:59:59Z",
            "source": "IMD (Static Fallback)",
            "cyclone_active": False,
        },
    ]
}


# ===========================================================================
# 1. StaticPFZAdapter
# ===========================================================================

# ===========================================================================
# 1. StaticPFZAdapter / Live NOAA ERDDAP Front Detection
# ===========================================================================

ERDDAP_SST_SAMPLE = {
    "table": {
        "columnNames": ["time", "latitude", "longitude", "sea_surface_temperature"],
        "rows": [
            # 3x3 grid with a strong horizontal thermal gradient between lon 74.0 and 74.2
            ["2026-08-28T00:00:00Z", 12.0, 74.0, 26.0],
            ["2026-08-28T00:00:00Z", 12.0, 74.1, 27.5],
            ["2026-08-28T00:00:00Z", 12.0, 74.2, 29.0],
            ["2026-08-28T00:00:00Z", 12.1, 74.0, 26.0],
            ["2026-08-28T00:00:00Z", 12.1, 74.1, 27.5],
            ["2026-08-28T00:00:00Z", 12.1, 74.2, 29.0],
            ["2026-08-28T00:00:00Z", 12.2, 74.0, 26.0],
            ["2026-08-28T00:00:00Z", 12.2, 74.1, 27.5],
            ["2026-08-28T00:00:00Z", 12.2, 74.2, 29.0],
        ]
    }
}

ERDDAP_CHL_SAMPLE = {
    "table": {
        "columnNames": ["time", "latitude", "longitude", "chlor_a"],
        "rows": [
            ["2026-08-28T00:00:00Z", 12.1, 74.1, 0.85]
        ]
    }
}


class TestStaticPFZAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = StaticPFZAdapter()
        self.pfz_json_str = json.dumps(PFZ_GEOJSON)

    # --- Haversine sanity check -------------------------------------------

    def test_haversine_same_point(self):
        self.assertAlmostEqual(_haversine_km(12.87, 74.84, 12.87, 74.84), 0.0, places=3)

    def test_haversine_known_distance(self):
        # Mangalore (12.87, 74.84) to approx. 1 degree north (~111 km)
        d = _haversine_km(12.87, 74.84, 13.87, 74.84)
        self.assertAlmostEqual(d, 111.2, delta=2.0)

    # --- Live INCOIS WFS tests (mocked HTTP) ------------------------------

    def test_incois_live_wfs_returns_pfzs(self):
        # Mock INCOIS WFS response
        mock_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "Category": "sst",
                        "UID": 2026243001.0,
                        "Length": 31.65
                    },
                    "geometry": {
                        "type": "MultiLineString",
                        "coordinates": [
                            [
                                [74.10, 12.10],
                                [74.15, 12.15]
                            ]
                        ]
                    }
                }
            ]
        }

        def _mock_get(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status.return_value = None
            mock_resp.json.return_value = mock_geojson
            return mock_resp

        with patch("httpx.Client.get", side_effect=_mock_get):
            result = self.adapter.fetch_data(lat=12.125, lon=74.125, radius_km=100.0)

        self.assertTrue(result["resolved"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["provenance"]["fallback_tier"], 1)
        self.assertEqual(result["provenance"]["confidence"], "HIGH")
        self.assertEqual(result["provenance"]["source"], "INCOIS PFZ")
        self.assertGreater(len(result["pfzs"]), 0)
        p = result["pfzs"][0]
        self.assertIn("PFZ-INCOIS-", p["pfz_id"])
        self.assertAlmostEqual(p["coordinates"]["lat"], 12.125, places=3)
        self.assertAlmostEqual(p["coordinates"]["lon"], 74.125, places=3)


    # --- Radius filtering on fallback -------------------------------------

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_pfz_nearby_returned_on_fallback(self, mock_json_load, mock_file_open):
        mock_json_load.return_value = PFZ_GEOJSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=12.65, lon=74.40, radius_km=200.0)

        self.assertTrue(result["resolved"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["provenance"]["fallback_tier"], 3)
        pfz_ids = [p["pfz_id"] for p in result["pfzs"]]
        self.assertIn("PFZ-TEST-001", pfz_ids)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_pfz_far_excluded_on_fallback(self, mock_json_load, mock_file_open):
        mock_json_load.return_value = PFZ_GEOJSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=12.65, lon=74.40, radius_km=100.0)

        pfz_ids = [p["pfz_id"] for p in result["pfzs"]]
        self.assertNotIn("PFZ-TEST-FAR", pfz_ids)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_pfz_empty_when_none_nearby(self, mock_json_load, mock_file_open):
        mock_json_load.return_value = PFZ_GEOJSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=0.0, lon=0.0, radius_km=10.0)

        self.assertTrue(result["resolved"])
        self.assertEqual(result["status"], "empty")
        self.assertEqual(result["pfzs"], [])

    # --- Provenance shape on fallback -------------------------------------

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_pfz_provenance_shape(self, mock_json_load, mock_file_open):
        mock_json_load.return_value = PFZ_GEOJSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=12.65, lon=74.40, radius_km=200.0)

        prov = result["provenance"]
        self.assertIn("source", prov)
        self.assertIn("retrieved_at", prov)
        self.assertIn("validity_time", prov)
        self.assertIn("fallback_tier", prov)
        self.assertIn("confidence", prov)
        self.assertEqual(prov["fallback_tier"], 3)
        self.assertEqual(prov["confidence"], "MODERATE")

    # --- FishingZone shape --------------------------------------------------

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_pfz_fishingzone_fields(self, mock_json_load, mock_file_open):
        mock_json_load.return_value = PFZ_GEOJSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=12.65, lon=74.40, radius_km=200.0)

        self.assertGreater(len(result["pfzs"]), 0)
        pfz = result["pfzs"][0]
        self.assertIn("pfz_id", pfz)
        self.assertIn("coordinates", pfz)
        self.assertIn("geometry", pfz)
        self.assertIn("valid_from", pfz)
        self.assertIn("valid_until", pfz)
        self.assertIn("source", pfz)
        self.assertIn("distance_km", pfz)
        self.assertIn("provenance", pfz)
        self.assertIn("lat", pfz["coordinates"])
        self.assertIn("lon", pfz["coordinates"])

    # --- Error path ---------------------------------------------------------

    def test_pfz_file_not_found_returns_error(self):
        adapter = StaticPFZAdapter()
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("backend.app.adapters.static_pfz_adapter._FALLBACK_PATH", "/nonexistent/pfz.geojson"):
                result = adapter.fetch_data(lat=12.65, lon=74.40)
        self.assertFalse(result["resolved"])
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["provenance"]["source"])
        self.assertEqual(result["provenance"]["confidence"], "LOW")



# ===========================================================================
# 2. StaticHazardAdapter / Live GDACS
# ===========================================================================

GDACS_SAMPLE_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "bbox": [72.0, 12.0, 75.0, 15.0],
            "geometry": {"type": "Point", "coordinates": [73.5, 13.5]},
            "properties": {
                "eventtype": "TC",
                "eventid": 1009999,
                "episodeid": 1,
                "eventname": "TEST-CYCLONE-26",
                "name": "Tropical Cyclone TEST-CYCLONE-26",
                "description": "Active Tropical Cyclone advisory in Arabian Sea",
                "alertlevel": "Orange",
                "fromdate": "2026-08-20T00:00:00",
                "todate": "2026-08-30T00:00:00",
                "severitydata": {"severity": 140.0, "severitytext": "Category 1", "severityunit": "km/h"}
            }
        },
        {
            "type": "Feature",
            "bbox": [130.0, 20.0, 135.0, 25.0],
            "geometry": {"type": "Point", "coordinates": [132.5, 22.5]},
            "properties": {
                "eventtype": "TC",
                "eventid": 1008888,
                "episodeid": 2,
                "eventname": "PACIFIC-CYCLONE-26",
                "name": "Tropical Cyclone PACIFIC-CYCLONE-26",
                "description": "Active Tropical Cyclone in Pacific Ocean",
                "alertlevel": "Red",
                "fromdate": "2026-08-20T00:00:00",
                "todate": "2026-08-30T00:00:00",
                "severitydata": {"severity": 200.0}
            }
        }
    ]
}


class TestStaticHazardAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = StaticHazardAdapter()

    # --- Live GDACS tests (mocked HTTP) -----------------------------------

    def test_gdacs_live_match_returns_cyclone(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = GDACS_SAMPLE_GEOJSON
        mock_resp.raise_for_status.return_value = None

        with patch("httpx.Client.get", return_value=mock_resp):
            result = self.adapter.fetch_hazards_for_bbox(
                bbox={"lat_min": 10.0, "lat_max": 16.0, "lon_min": 70.0, "lon_max": 76.0},
                time_window={"from": "2026-08-22T00:00:00Z", "to": "2026-08-28T00:00:00Z"},
            )

        self.assertTrue(result["resolved"])
        self.assertTrue(result["cyclone_active"])
        self.assertEqual(result["provenance"]["fallback_tier"], 1)
        self.assertEqual(result["provenance"]["confidence"], "HIGH")
        self.assertEqual(result["provenance"]["source"], "GDACS (Global Disaster Alert and Coordination System)")
        self.assertEqual(len(result["hazards"]), 1)
        h = result["hazards"][0]
        self.assertEqual(h["hazard_id"], "GDACS-TC-1009999-1")
        self.assertEqual(h["hazard_type"], "CYCLONE_WARNING")
        self.assertEqual(h["severity"], "SEVERE")

    def test_gdacs_live_spatial_filter_excludes_distant_cyclone(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = GDACS_SAMPLE_GEOJSON
        mock_resp.raise_for_status.return_value = None

        with patch("httpx.Client.get", return_value=mock_resp):
            # Query Bay of Bengal (lon 82-88E) — Arabian Sea cyclone and Pacific cyclone should not match
            result = self.adapter.fetch_hazards_for_bbox(
                bbox={"lat_min": 10.0, "lat_max": 16.0, "lon_min": 82.0, "lon_max": 88.0},
                time_window=None,
            )

        self.assertTrue(result["resolved"])
        self.assertFalse(result["cyclone_active"])
        self.assertEqual(result["hazards"], [])
        self.assertEqual(result["provenance"]["fallback_tier"], 1)

    # --- Tier 3 Fallback tests (when live API fails) ----------------------

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_bbox_match_returns_hazard_on_fallback(self, mock_json_load, _):
        mock_json_load.return_value = HAZARD_JSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_hazards_for_bbox(
                bbox={"lat_min": 10.0, "lat_max": 14.0, "lon_min": 73.0, "lon_max": 76.0},
                time_window={"from": "2026-08-22T00:00:00Z", "to": "2026-08-23T00:00:00Z"},
            )
        self.assertTrue(result["resolved"])
        self.assertEqual(result["provenance"]["fallback_tier"], 3)
        ids = [h["hazard_id"] for h in result["hazards"]]
        self.assertIn("HAZ-001", ids)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_bbox_mismatch_excluded(self, mock_json_load, _):
        mock_json_load.return_value = HAZARD_JSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_hazards_for_bbox(
                bbox={"lat_min": 21.0, "lat_max": 23.0, "lon_min": 66.0, "lon_max": 68.0},
                time_window=None,
            )
        ids = [h["hazard_id"] for h in result["hazards"]]
        self.assertNotIn("HAZ-001", ids)
        self.assertIn("HAZ-NORTH", ids)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_time_window_excludes_old_hazard(self, mock_json_load, _):
        mock_json_load.return_value = HAZARD_JSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_hazards_for_bbox(
                bbox={"lat_min": 13.0, "lat_max": 20.0, "lon_min": 62.0, "lon_max": 74.0},
                time_window={"from": "2026-08-21T00:00:00Z", "to": "2026-08-25T23:59:59Z"},
            )
        ids = [h["hazard_id"] for h in result["hazards"]]
        self.assertNotIn("HAZ-CYC", ids)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_cyclone_flag_set_when_cyclone_present(self, mock_json_load, _):
        mock_json_load.return_value = HAZARD_JSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_hazards_for_bbox(
                bbox={"lat_min": 13.0, "lat_max": 21.0, "lon_min": 61.0, "lon_max": 74.0},
                time_window={"from": "2026-08-27T00:00:00Z", "to": "2026-08-28T00:00:00Z"},
            )
        self.assertTrue(result["cyclone_active"])

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_cyclone_flag_false_when_no_cyclone(self, mock_json_load, _):
        mock_json_load.return_value = HAZARD_JSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_hazards_for_bbox(
                bbox={"lat_min": 10.0, "lat_max": 14.0, "lon_min": 73.0, "lon_max": 76.0},
                time_window={"from": "2026-08-22T00:00:00Z", "to": "2026-08-23T00:00:00Z"},
            )
        self.assertFalse(result["cyclone_active"])

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_hazard_provenance_shape(self, mock_json_load, _):
        mock_json_load.return_value = HAZARD_JSON
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_hazards_for_bbox(
                bbox={"lat_min": 10.0, "lat_max": 14.0, "lon_min": 73.0, "lon_max": 76.0},
                time_window=None,
            )
        prov = result["provenance"]
        self.assertIn("source", prov)
        self.assertIn("retrieved_at", prov)
        self.assertIn("validity_time", prov)
        self.assertIn("fallback_tier", prov)
        self.assertIn("confidence", prov)
        self.assertEqual(prov["fallback_tier"], 3)

    def test_hazard_file_not_found_returns_error(self):
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("backend.app.adapters.static_hazard_adapter._FALLBACK_PATH", "/no/such/file.json"):
                result = self.adapter.fetch_hazards_for_bbox(
                    bbox={"lat_min": 10.0, "lat_max": 14.0, "lon_min": 73.0, "lon_max": 76.0},
                )
        self.assertFalse(result["resolved"])
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["provenance"]["source"])



# ===========================================================================
# 3. SSTAdapter
# ===========================================================================

def _sst_marine_response(target_iso: str, sst_value=27.5) -> dict:
    """Build a minimal Open-Meteo Marine API response for SST testing."""
    # Open-Meteo returns naive UTC strings (no Z)
    t = target_iso.replace("Z", "").replace("+00:00", "")
    return {
        "hourly": {
            "time": [t],
            "sea_surface_temperature": [sst_value],
        }
    }


def _mock_sst_http_response(json_data: dict, status_code: int = 200):
    """Create a mock httpx.Response for SST tests."""
    mock_resp = MagicMock()
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


class TestSSTAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = SSTAdapter()
        clear_open_meteo_cache()

    # --- Existing climatology tests (unchanged) --------------------------------

    def test_sst_fallback_returns_value_for_august(self):
        """When live API is unavailable, August climatology returns 27.0."""
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        self.assertIsNotNone(result["sst_celsius"])
        self.assertEqual(result["sst_celsius"], 27.0)
        self.assertTrue(result["resolved"])
        self.assertEqual(result["status"], "ok")

    def test_sst_fallback_returns_different_value_for_may(self):
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-05-15T12:00:00Z")
        self.assertEqual(result["sst_celsius"], 30.0)

    def test_sst_provenance_tier_3(self):
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        prov = result["provenance"]
        self.assertEqual(prov["fallback_tier"], 3)
        self.assertEqual(prov["confidence"], "MODERATE")
        self.assertIn("source", prov)
        self.assertIn("retrieved_at", prov)
        self.assertIn("validity_time", prov)

    def test_sst_unresolvable_on_bad_timestamp(self):
        result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp="NOT_A_DATE")
        self.assertIsNone(result["sst_celsius"])
        self.assertFalse(result["resolved"])
        self.assertEqual(result["status"], "unresolvable")
        prov = result["provenance"]
        self.assertIsNone(prov["source"])
        self.assertEqual(prov["confidence"], "LOW")
        self.assertEqual(prov["fallback_tier"], 3)

    def test_sst_returns_all_marine_observation_fields(self):
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        for field in ("lat", "lon", "time_iso", "sst_celsius", "chlorophyll_mgm3",
                      "hab_detected", "hab_probability", "current_speed_kmh",
                      "current_direction_deg", "resolved", "provenance"):
            self.assertIn(field, result, msg=f"Missing field: {field}")

    # --- NEW: Live path tests (mocked HTTP) -----------------------------------

    def test_sst_live_path_returns_tier1_provenance(self):
        """Scenario §10.10: SST must actually be retrieved from a live source."""
        ts = "2026-08-28T14:00:00Z"
        marine_json = _sst_marine_response(ts, sst_value=29.4)
        with patch("httpx.Client.get",
                   return_value=_mock_sst_http_response(marine_json)):
            result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertTrue(result["resolved"])
        self.assertEqual(result["provenance"]["fallback_tier"], 1)
        self.assertEqual(result["provenance"]["confidence"], "HIGH")
        self.assertIn("Open-Meteo", result["provenance"]["source"])

    def test_sst_live_path_returns_api_value_not_hardcoded(self):
        """The sst_celsius value must come from the API response, not a hardcoded number."""
        ts = "2026-08-28T14:00:00Z"
        marine_json = _sst_marine_response(ts, sst_value=31.7)
        with patch("httpx.Client.get",
                   return_value=_mock_sst_http_response(marine_json)):
            result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertAlmostEqual(result["sst_celsius"], 31.7, places=3)

    def test_sst_live_path_lat_lon_sent_to_api(self):
        """The requested lat/lon must be forwarded to the Open-Meteo API."""
        ts = "2026-08-28T14:00:00Z"
        marine_json = _sst_marine_response(ts)
        with patch("httpx.Client.get",
                   return_value=_mock_sst_http_response(marine_json)) as mock_get:
            self.adapter.fetch_data(lat=15.5, lon=72.3, timestamp=ts)
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or (call_kwargs.args[1] if len(call_kwargs.args) > 1 else {})
        self.assertEqual(params.get("latitude"), 15.5)
        self.assertEqual(params.get("longitude"), 72.3)

    def test_sst_option_a_null_from_api_falls_to_climatology(self):
        """
        Option A (approved 2026-08-28): if the API returns sea_surface_temperature=null
        for the requested location/time, fall through to the Tier 3 climatology table.
        The returned provenance must clearly indicate Tier 3, NOT Tier 1.
        """
        ts = "2026-08-28T14:00:00Z"   # August -> climatology = 27.0
        marine_json = _sst_marine_response(ts, sst_value=None)
        with patch("httpx.Client.get",
                   return_value=_mock_sst_http_response(marine_json)):
            result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        # Must have fallen through to climatology
        self.assertEqual(result["sst_celsius"], 27.0)
        self.assertEqual(result["provenance"]["fallback_tier"], 3)
        self.assertIn("NOAA", result["provenance"]["source"])
        self.assertIn("NOT a live", result["provenance"]["source"])

    def test_sst_timeout_falls_to_climatology(self):
        ts = "2026-08-28T14:00:00Z"
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertEqual(result["provenance"]["fallback_tier"], 3)
        self.assertEqual(result["sst_celsius"], 27.0)   # August climatology

    def test_sst_http_500_falls_to_climatology(self):
        ts = "2026-08-28T14:00:00Z"
        with patch("httpx.Client.get",
                   return_value=_mock_sst_http_response({}, status_code=500)):
            result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertEqual(result["provenance"]["fallback_tier"], 3)
        self.assertIsNotNone(result["sst_celsius"])

    def test_sst_climatology_source_never_claims_live(self):
        """Scenario §10.11: static/climatology data must never be labelled as live."""
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        source = result["provenance"]["source"]
        self.assertIn("NOT a live", source)
        self.assertNotIn("Tier 1", source)

    # --- NEW: Coordinate validation (Issue 2 fix) --------------------------

    def test_sst_invalid_lat_returns_unresolvable(self):
        """
        Issue 2 fix: an impossible lat (e.g. GPS glitch = 999.0) must NOT
        return a plausible climatology value.  The adapter must return
        resolved=False so the upstream caller can surface the data-quality
        problem, not silently mask it with a fabricated SST reading.
        """
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("t/o")):
            result = self.adapter.fetch_data(lat=999.0, lon=74.84,
                                             timestamp="2026-08-29T07:00:00Z")
        self.assertFalse(result["resolved"],
                         "Invalid lat=999 must yield resolved=False")
        self.assertEqual(result["status"], "unresolvable")
        self.assertIsNone(result["sst_celsius"])
        self.assertIsNone(result["provenance"]["source"])
        self.assertEqual(result["provenance"]["confidence"], "LOW")
        # Reason must mention the bad coordinate
        self.assertIn("lat=999", result.get("reason", ""))

    def test_sst_invalid_lon_returns_unresolvable(self):
        """
        Same guard fires for an out-of-range longitude (lon=-999).
        """
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("t/o")):
            result = self.adapter.fetch_data(lat=12.87, lon=-999.0,
                                             timestamp="2026-08-29T07:00:00Z")
        self.assertFalse(result["resolved"],
                         "Invalid lon=-999 must yield resolved=False")
        self.assertEqual(result["status"], "unresolvable")
        self.assertIsNone(result["sst_celsius"])


# ===========================================================================
# 5. Static data honesty — provenance must never claim Tier 1
# ===========================================================================

class TestStaticDataProvenance(unittest.TestCase):
    """
    Scenario §10.11: static PFZ and hazard data must NEVER be labelled as live
    (fallback_tier=1) or as current real-world observations.
    """

    def test_pfz_provenance_is_always_tier3(self):
        import json
        from unittest.mock import patch, mock_open
        pfz_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"pfz_id": "PFZ-T", "source": "Test",
                                   "valid_from": "2026-08-01T00:00:00Z",
                                   "valid_until": "2026-08-31T23:59:59Z"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[74.0, 12.5], [74.5, 12.5],
                                          [74.5, 12.0], [74.0, 12.0], [74.0, 12.5]]],
                    },
                }
            ],
        }
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("builtins.open", mock_open()):
                with patch("json.load", return_value=pfz_data):
                    result = StaticPFZAdapter().fetch_data(lat=12.25, lon=74.25, radius_km=500.0)
        self.assertEqual(result["provenance"]["fallback_tier"], 3)
        self.assertNotEqual(result["provenance"]["fallback_tier"], 1)
        self.assertIn("Static Fallback", result["provenance"]["source"])

    def test_hazard_provenance_is_always_tier3(self):
        hazard_data = {
            "hazards": [
                {
                    "hazard_id": "HAZ-T",
                    "hazard_type": "HIGH_WAVES",
                    "severity": "MODERATE",
                    "description": "Test",
                    "affected_region": {"lat_min": 8.0, "lat_max": 15.0,
                                        "lon_min": 72.0, "lon_max": 77.0},
                    "valid_from": "2026-08-01T00:00:00Z",
                    "valid_until": "2026-08-31T23:59:59Z",
                    "source": "IMD (Static Fallback)",
                    "cyclone_active": False,
                }
            ]
        }
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
            with patch("builtins.open", mock_open()):
                with patch("json.load", return_value=hazard_data):
                    result = StaticHazardAdapter().fetch_hazards_for_bbox(
                        bbox={"lat_min": 10.0, "lat_max": 14.0, "lon_min": 73.0, "lon_max": 76.0}
                    )
        self.assertEqual(result["provenance"]["fallback_tier"], 3)
        self.assertNotEqual(result["provenance"]["fallback_tier"], 1)
        self.assertIn("Static Fallback", result["provenance"]["source"])

# ===========================================================================
# 4. AmfitriteHABAdapter -- normalized schema
# ===========================================================================

class TestAmfitriteHABAdapterNormalized(unittest.TestCase):

    def setUp(self):
        # No model path -> no imagery -> honest unresolved result
        self.adapter = AmfitriteHABAdapter()
        self._stac_patcher = patch("httpx.post", return_value=_mock_stac_response([]))
        self._stac_patcher.start()
        self.addCleanup(self._stac_patcher.stop)

    def test_output_has_time_iso_and_timestamp(self):
        result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        self.assertIn("time_iso", result)
        self.assertIn("timestamp", result)
        self.assertEqual(result["time_iso"], result["timestamp"])

    def test_time_iso_equals_input_timestamp(self):
        ts = "2026-08-21T06:00:00Z"
        result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp=ts)
        self.assertEqual(result["time_iso"], ts)
        self.assertEqual(result["timestamp"], ts)

    def test_output_has_provenance_and_frozen_source_key(self):
        result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        self.assertIn("provenance", result)
        self.assertIn("source", result)
        self.assertEqual(result["source"], result["provenance"]["source"])
        self.assertIn("severity", result)
        self.assertIsNone(result["severity"])
        self.assertIsNone(result["hab_detected"])

    def test_provenance_shape(self):
        result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        prov = result["provenance"]
        for key in ("source", "retrieved_at", "validity_time", "fallback_tier", "confidence"):
            self.assertIn(key, prov, msg=f"Missing provenance key: {key}")

    def test_all_marine_observation_fields_present(self):
        result = self.adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        for field in ("lat", "lon", "time_iso", "sst_celsius", "chlorophyll_mgm3",
                      "hab_detected", "hab_probability", "current_speed_kmh",
                      "current_direction_deg", "resolved", "provenance"):
            self.assertIn(field, result, msg=f"Missing field: {field}")

    def test_bundled_resnet_checkpoint_loads_and_infers(self):
        """The bundled checkpoint must load into the 10-channel ResNet model."""
        try:
            import torch
        except ImportError:
            self.skipTest("torch is not installed in this environment")

        adapter = AmfitriteHABAdapter()
        self.assertTrue(adapter.model_loaded)
        self.assertEqual(tuple(adapter.model.conv1.weight.shape), (64, 10, 7, 7))
        self.assertEqual(adapter.model.fc.out_features, 2)
        with torch.no_grad():
            output = adapter.model(torch.zeros((1, 10, 256, 256)))
        self.assertEqual(tuple(output.shape), (1, 2))

    def test_model_unavailable_keeps_honest_fallback(self):
        """A missing checkpoint must preserve the unresolved Tier-3 contract."""
        adapter = AmfitriteHABAdapter(model_path="missing-amfitrite-checkpoint.pth")
        self.assertFalse(adapter.model_loaded)
        with patch("httpx.post", return_value=_mock_stac_response([])):
            result = adapter.fetch_data(12.87, 74.84, "2026-08-21T06:00:00Z")
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["hab_detected"])
        self.assertIsNone(result["hab_probability"])
        self.assertIn("severity", result)


# ===========================================================================
# 5. AmfitriteHABAdapter -- real imagery pipeline (new requirements)
# ===========================================================================

def _make_stac_feature(
    tile_id: str = "S2B_TEST_TILE",
    cloud_cover: float = 25.0,
    tile_datetime: str = "2026-08-25T05:30:00Z",
    include_scl: bool = True,
    include_hab_bands: bool = True,
) -> Dict[str, Any]:
    """Build a minimal synthetic STAC feature that mirrors the Planetary Computer schema."""
    assets: Dict[str, Any] = {}
    if include_scl:
        assets["SCL"] = {"href": "https://fake.blob.core.windows.net/scl.tif"}
    if include_hab_bands:
        for b in ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]:
            assets[b] = {"href": f"https://fake.blob.core.windows.net/{b}.tif"}
    return {
        "id":    tile_id,
        "type":  "Feature",
        "bbox":  [74.79, 12.82, 74.89, 12.92],
        "geometry": {"type": "Point", "coordinates": [74.84, 12.87]},
        "properties": {
            "datetime":       tile_datetime,
            "eo:cloud_cover": cloud_cover,
        },
        "assets": assets,
    }


def _mock_stac_response(features: list, status_code: int = 200) -> MagicMock:
    """Build a mock httpx response for the STAC POST endpoint."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"features": features}
    return resp


def _make_scl_array(usable_fraction: float, shape=(64, 64)):
    """
    Build a fake SCL numpy array with the given usable fraction.
    Usable pixels = SCL class 6 (water). Cloud pixels = SCL class 9.
    """
    import numpy as np
    total  = shape[0] * shape[1]
    n_good = int(total * usable_fraction)
    arr    = np.zeros(total, dtype=np.uint8)
    arr[:n_good]    = 6    # water — usable
    arr[n_good:]    = 9    # cloud high prob — unusable
    return arr.reshape(shape)


def _make_band_array(shape=(256, 256)):
    """Return a deterministic non-zero band array (not torch.rand)."""
    import numpy as np
    return np.full(shape, fill_value=500, dtype=np.uint16)


class TestAmfitriteHABRealImageryPipeline(unittest.TestCase):
    """
    Tests for the pixel-level HAB pipeline:
      - real imagery path (RDNet receives real pixels)
      - cloudy ROI rejection
      - no imagery → honest unresolved result (no fabricated score)
      - STAC error → honest unresolved result
      - no mock/synthetic/torch.rand() in any code path
    """

    def test_torch_rand_never_in_adapter_source(self):
        """torch.rand() must not appear anywhere in the HAB adapter source."""
        adapter_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "app", "adapters", "amfitrite_hab_adapter.py",
        )
        with open(adapter_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn(
            "torch.rand",
            source,
            msg="torch.rand() was found in amfitrite_hab_adapter.py — synthetic pixels are forbidden",
        )

    def test_no_synthetic_random_in_source(self):
        """np.random and random() must not appear in the normal data path."""
        adapter_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "app", "adapters", "amfitrite_hab_adapter.py",
        )
        with open(adapter_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        for pattern in ("torch.rand", "np.random", "random.random", "random.randint"):
            self.assertNotIn(
                pattern, source,
                msg=f"Synthetic data pattern '{pattern}' found in adapter source",
            )

    def test_no_stac_features_returns_unresolved(self):
        """STAC returns 0 features → resolved=False, hab_detected=None, tier=3."""
        adapter = AmfitriteHABAdapter()
        with patch("httpx.post", return_value=_mock_stac_response([])):
            result = adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")

        self.assertFalse(result["resolved"], msg="resolved must be False when no imagery found")
        self.assertIsNone(result["hab_detected"], msg="hab_detected must be None — no fabrication")
        self.assertIsNone(result["hab_probability"], msg="hab_probability must be None — no fabrication")
        self.assertEqual(result["provenance"]["fallback_tier"], 3)
        self.assertEqual(result["provenance"]["confidence"], "LOW")
        self.assertIn("No usable", result["provenance"]["source"])

    def test_no_imagery_never_fabricates_classification(self):
        """The Tier-3 no-imagery result must not use the old lat > 20.0 heuristic."""
        adapter = AmfitriteHABAdapter()
        with patch("httpx.post", return_value=_mock_stac_response([])):
            result = adapter.fetch_data(lat=22.0, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        self.assertIsNone(
            result["hab_detected"],
            msg="No-imagery Tier-3 must not fabricate a positive HAB classification for lat>20N",
        )

    def test_stac_timeout_returns_unresolved(self):
        """STAC timeout → resolved=False, no fabricated classification."""
        adapter = AmfitriteHABAdapter()
        with patch("httpx.post", side_effect=httpx.TimeoutException("timeout")):
            result = adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["hab_detected"])
        self.assertEqual(result["provenance"]["fallback_tier"], 3)

    def test_stac_http_error_returns_unresolved(self):
        """STAC non-200 → resolved=False."""
        adapter = AmfitriteHABAdapter()
        with patch("httpx.post", return_value=_mock_stac_response([], status_code=503)):
            result = adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["hab_detected"])

    def test_cloudy_roi_skips_tile_and_returns_unresolved(self):
        """
        Scene-level cloud cover is OK (<80%) but SCL shows the ROI is 15% cloud-free
        (<40% threshold). The adapter must reject the tile and return unresolved.
        """
        adapter = AmfitriteHABAdapter()
        feature  = _make_stac_feature(cloud_cover=45.0)
        scl_array = _make_scl_array(usable_fraction=0.15)

        mock_src = MagicMock()
        mock_src.__enter__ = lambda s: s
        mock_src.__exit__  = MagicMock(return_value=False)
        mock_src.read.return_value = scl_array
        mock_src.transform = MagicMock()
        mock_src.width  = 100
        mock_src.height = 100

        roi_bbox = [74.79, 12.82, 74.89, 12.92]
        identity = lambda self_, bbox, crs: bbox  # noqa: E731

        with patch("httpx.post", return_value=_mock_stac_response([feature])):
            with patch("rasterio.open", return_value=mock_src):
                with patch.object(AmfitriteHABAdapter, "_reproject_bbox_to_crs", identity):
                    result = adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")

        self.assertFalse(result["resolved"],
                         msg="resolved must be False when ROI is too cloudy")
        self.assertIsNone(result["hab_detected"])

    def test_good_roi_fraction_allows_tile_through(self):
        """
        ROI SCL shows 70% usable pixels — tile should be accepted.
        Without model weights, result should be resolved=False but with
        sentinel2_item_id in provenance (image was found and assessed).
        """
        adapter = AmfitriteHABAdapter(model_path="missing-amfitrite-checkpoint.pth")
        feature  = _make_stac_feature(tile_id="S2B_USABLE_TILE", cloud_cover=30.0)
        scl_array  = _make_scl_array(usable_fraction=0.70)
        band_array = _make_band_array()

        call_count = {"n": 0}
        mock_src   = MagicMock()
        mock_src.__enter__ = lambda s: s
        mock_src.__exit__  = MagicMock(return_value=False)
        mock_src.transform = MagicMock()
        mock_src.width  = 100
        mock_src.height = 100

        def read_side(*args, **kwargs):
            call_count["n"] += 1
            return scl_array if call_count["n"] == 1 else band_array

        mock_src.read.side_effect = read_side

        identity = lambda self_, bbox, crs: bbox  # noqa: E731

        with patch("httpx.post", return_value=_mock_stac_response([feature])):
            with patch("rasterio.open", return_value=mock_src):
                with patch.object(AmfitriteHABAdapter, "_reproject_bbox_to_crs", identity):
                    result = adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")

        prov = result["provenance"]
        self.assertIn("sentinel2_item_id", prov)
        self.assertEqual(prov["sentinel2_item_id"], "S2B_USABLE_TILE")
        self.assertGreater(prov["roi_cloud_free_pct"], 0)
        self.assertFalse(prov["rdnet_received_real_pixels"])

    def test_real_imagery_path_rdnet_receives_real_pixels(self):
        """
        Full path: usable tile, model loaded, real pixels → RDNet.
        """
        try:
            import torch
        except ImportError:
            self.skipTest("torch not installed")

        adapter    = AmfitriteHABAdapter()
        mock_model = MagicMock()
        mock_model.return_value = torch.tensor([[0.2, 0.8]])  # prob(bloom)=0.8
        adapter.model        = mock_model
        adapter.model_loaded = True

        feature    = _make_stac_feature(tile_id="S2B_REAL_TILE", cloud_cover=20.0)
        scl_array  = _make_scl_array(usable_fraction=0.75)
        band_array = _make_band_array()

        call_count = {"n": 0}
        mock_src   = MagicMock()
        mock_src.__enter__ = lambda s: s
        mock_src.__exit__  = MagicMock(return_value=False)
        mock_src.transform = MagicMock()

        def read_side(*args, **kwargs):
            call_count["n"] += 1
            return scl_array if call_count["n"] == 1 else band_array

        mock_src.read.side_effect = read_side

        identity = lambda self_, bbox, crs: bbox  # noqa: E731

        with patch("httpx.post", return_value=_mock_stac_response([feature])):
            with patch("rasterio.open", return_value=mock_src):
                with patch.object(AmfitriteHABAdapter, "_reproject_bbox_to_crs", identity):
                    with patch("torch.no_grad"):
                        result = adapter.fetch_data(
                            lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z"
                        )

        self.assertTrue(result["resolved"])
        self.assertEqual(result["provenance"]["fallback_tier"], 2)
        self.assertTrue(result["provenance"]["rdnet_received_real_pixels"])
        self.assertEqual(result["provenance"]["sentinel2_item_id"], "S2B_REAL_TILE")
        self.assertIsNotNone(result["hab_probability"])
        self.assertIn("B02", result["provenance"]["bands_used"])
        self.assertEqual(call_count["n"], 11)

    def test_real_imagery_path_tier2_provenance_fields(self):
        """All Tier-2 provenance fields must be present when RDNet runs."""
        try:
            import torch
        except ImportError:
            self.skipTest("torch not installed")

        adapter    = AmfitriteHABAdapter()
        mock_model = MagicMock()
        mock_model.return_value = torch.tensor([[0.6, 0.4]])
        adapter.model        = mock_model
        adapter.model_loaded = True

        feature   = _make_stac_feature(tile_id="S2A_PROV_TEST", cloud_cover=15.0)
        scl_array = _make_scl_array(usable_fraction=0.80)
        band_arr  = _make_band_array()

        call_count = {"n": 0}
        mock_src   = MagicMock()
        mock_src.__enter__ = lambda s: s
        mock_src.__exit__  = MagicMock(return_value=False)
        mock_src.transform = MagicMock()

        def read_side(*args, **kwargs):
            call_count["n"] += 1
            return scl_array if call_count["n"] == 1 else band_arr

        mock_src.read.side_effect = read_side

        identity = lambda self_, bbox, crs: bbox  # noqa: E731

        with patch("httpx.post", return_value=_mock_stac_response([feature])):
            with patch("rasterio.open", return_value=mock_src):
                with patch.object(AmfitriteHABAdapter, "_reproject_bbox_to_crs", identity):
                    with patch("torch.no_grad"):
                        result = adapter.fetch_data(
                            lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z"
                        )

        prov = result["provenance"]
        for key in (
            "source", "retrieved_at", "validity_time", "fallback_tier", "confidence",
            "sentinel2_item_id", "sentinel2_datetime", "scene_cloud_cover",
            "roi_cloud_free_pct", "bands_used", "rdnet_received_real_pixels",
        ):
            self.assertIn(key, prov, msg=f"Tier-2 provenance missing field: {key}")
        self.assertEqual(prov["fallback_tier"], 2)
        self.assertListEqual(
            prov["bands_used"],
            ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"],
        )

    def test_tile_missing_scl_is_skipped(self):
        """A tile without an SCL asset must be silently skipped."""
        adapter = AmfitriteHABAdapter()
        feature = _make_stac_feature(include_scl=False)
        with patch("httpx.post", return_value=_mock_stac_response([feature])):
            result = adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["hab_detected"])

    def test_tile_missing_hab_band_model_not_called(self):
        """A tile missing one of the 10 HAB bands must not run RDNet inference."""
        try:
            import torch
        except ImportError:
            self.skipTest("torch not installed")

        adapter    = AmfitriteHABAdapter()
        mock_model = MagicMock()
        mock_model.return_value = torch.tensor([[0.3, 0.7]])
        adapter.model        = mock_model
        adapter.model_loaded = True

        feature = _make_stac_feature(include_scl=True, include_hab_bands=True)
        del feature["assets"]["B12"]

        scl_array = _make_scl_array(usable_fraction=0.80)
        band_arr  = _make_band_array()

        call_count = {"n": 0}
        mock_src   = MagicMock()
        mock_src.__enter__ = lambda s: s
        mock_src.__exit__  = MagicMock(return_value=False)
        mock_src.transform = MagicMock()

        def read_side(*args, **kwargs):
            call_count["n"] += 1
            return scl_array if call_count["n"] == 1 else band_arr

        mock_src.read.side_effect = read_side

        identity = lambda self_, bbox, crs: bbox  # noqa: E731

        with patch("httpx.post", return_value=_mock_stac_response([feature])):
            with patch("rasterio.open", return_value=mock_src):
                with patch.object(AmfitriteHABAdapter, "_reproject_bbox_to_crs", identity):
                    result = adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")

        mock_model.assert_not_called()
        self.assertFalse(result["resolved"])

    def test_stac_request_uses_30_day_window(self):
        """The STAC payload must use a 30-day lookback window."""
        adapter  = AmfitriteHABAdapter()
        captured = {}

        def fake_post(url, json=None, **kwargs):
            captured["payload"] = json
            return _mock_stac_response([])

        with patch("httpx.post", side_effect=fake_post):
            adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-29T00:00:00Z")

        dt_range = captured.get("payload", {}).get("datetime", "")
        self.assertIn("/", dt_range)
        start_str, end_str = dt_range.split("/", 1)
        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end_dt   = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        diff_days = (end_dt - start_dt).days
        self.assertGreaterEqual(diff_days, 29)

    def test_stac_request_sorted_most_recent_first(self):
        """The STAC payload must request results sorted by datetime descending."""
        adapter  = AmfitriteHABAdapter()
        captured = {}

        def fake_post(url, json=None, **kwargs):
            captured["payload"] = json
            return _mock_stac_response([])

        with patch("httpx.post", side_effect=fake_post):
            adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-29T00:00:00Z")

        sortby = captured.get("payload", {}).get("sortby", [])
        self.assertTrue(
            any(s.get("direction", "").lower() == "desc" for s in sortby)
        )

    def test_compute_roi_cloud_free_fraction_correct(self):
        """_compute_roi_cloud_free_fraction correctly computes usable pixel ratio."""
        adapter   = AmfitriteHABAdapter()
        scl_array = _make_scl_array(usable_fraction=0.60)

        mock_src = MagicMock()
        mock_src.__enter__ = lambda s: s
        mock_src.__exit__  = MagicMock(return_value=False)
        mock_src.transform = MagicMock()
        mock_src.width  = 100
        mock_src.height = 100
        mock_src.read.return_value = scl_array

        identity = lambda self_, bbox, crs: bbox  # noqa: E731

        with patch("rasterio.open", return_value=mock_src):
            with patch.object(AmfitriteHABAdapter, "_reproject_bbox_to_crs", identity):
                frac = adapter._compute_roi_cloud_free_fraction(
                    "https://fake.tif", [74.79, 12.82, 74.89, 12.92]
                )

        self.assertAlmostEqual(frac, 0.60, delta=0.02)


class TestAmfitriteHABDemoMock(unittest.TestCase):
    """DEMO_HAB_MOCK restores lat>20 heuristic as labelled Tier-3 demo only."""

    def test_demo_mock_skips_stac_and_labels_tier3(self):
        adapter = AmfitriteHABAdapter()
        with patch.dict(os.environ, {"DEMO_HAB_MOCK": "1"}, clear=False):
            with patch("httpx.post") as mock_post:
                north = adapter.fetch_data(lat=22.0, lon=74.84, timestamp="2026-08-21T06:00:00Z")
                south = adapter.fetch_data(lat=12.87, lon=74.84, timestamp="2026-08-21T06:00:00Z")

        self.assertTrue(north["hab_detected"])
        self.assertEqual(north["hab_probability"], 0.95)
        self.assertEqual(north["severity"], "HIGH")
        self.assertEqual(north["provenance"]["fallback_tier"], 3)
        self.assertTrue(north["provenance"].get("demo_mode"))
        self.assertIn("DEMO_HAB_MOCK", north["source"])
        self.assertFalse(south["hab_detected"])
        self.assertEqual(south["severity"], "LOW")

    def test_default_live_first_does_not_use_lat_heuristic(self):
        adapter = AmfitriteHABAdapter()
        with patch.dict(os.environ, {"DEMO_HAB_MOCK": ""}, clear=False):
            with patch("httpx.post", return_value=_mock_stac_response([])):
                result = adapter.fetch_data(lat=22.0, lon=74.84, timestamp="2026-08-21T06:00:00Z")
        self.assertIsNone(result["hab_detected"])
        self.assertIsNone(result["severity"])


if __name__ == "__main__":
    unittest.main()
