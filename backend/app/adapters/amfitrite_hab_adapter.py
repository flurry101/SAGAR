"""
amfitrite_hab_adapter.py
========================
FROZEN CONTRACT (do not break class name, fetch_data signature, or Step 09 §17.3 keys):
    class AmfitriteHABAdapter(MarineDataAdapter)
    fetch_data(lat, lon, timestamp=None) -> dict
    Always include: source, lat, lon, timestamp, hab_detected, hab_probability, severity
Additive PathFinder fields (time_iso, provenance, resolved, marine extras) are allowed.

Adapter for detecting Harmful Algal Blooms (HABs) using Sentinel-2 Level-2A imagery.
Integrates Microsoft Planetary Computer STAC API with the
'kostaspic/AMFITRITE-Sentinel2-HAB-RDNet' model.

DEMO_HAB_MOCK: when env is 1/true/yes/on, skip STAC and use the original lat>20
heuristic, labelled fallback_tier=3 demo mode. Default is live-first.

Resilience Fallback Chain:
    Tier 2 -- Live Sentinel-2 L2A via Microsoft Planetary Computer STAC + RDNet ML Inference.
              - Searches the most recent 30 days for usable imagery.
              - Iterates tiles from most-recent-first until a cloud-free ROI is found.
              - Downloads SCL (Scene Classification Layer) and computes pixel-level
                cloud-free fraction of the actual ROI.
              - Only runs RDNet when ROI has >= MIN_USABLE_FRACTION usable pixels.
              - Feeds REAL Sentinel-2 satellite pixels into RDNet.
              - NEVER uses randomized/synthetic pixels, or latitude-based heuristics.
    Tier 3 -- Honest "no usable imagery" result when:
              - No cloud-free Sentinel-2 tile found within 30-day lookback.
              - ML dependencies (torch/timm/rasterio/numpy) are absent.
              - STAC API is unreachable or times out.
              - Model weights file not provided or missing.
              NOTE: The previous latitude-based mock (lat > 20.0 heuristic) is REMOVED.
              Tier 3 returns resolved=False with an explicit honest message.

Output Schema: MarineObservation subset (Step 07, Section 2.6.2):
    lat              -- float
    lon              -- float
    time_iso         -- str (ISO 8601 UTC)
    sst_celsius      -- None (sourced from SSTAdapter)
    chlorophyll_mgm3 -- None
    hab_detected     -- bool | None (None when no usable imagery)
    hab_probability  -- float | None (0.0 to 1.0, None when no usable imagery)
    current_speed_kmh-- None
    current_direction_deg -- None
    resolved         -- bool
    provenance       -- Provenance dictionary (includes sentinel2_item_id, roi_cloud_free_pct,
                        rdnet_received_real_pixels when available)
"""
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .base_adapter import MarineDataAdapter

# ---------------------------------------------------------------------------
# Optional ML and geospatial dependencies
# ---------------------------------------------------------------------------
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import timm
    TIMM_AVAILABLE = True
except ImportError:
    TIMM_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import rasterio
    from rasterio.windows import from_bounds, Window
    from rasterio.enums import Resampling
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

try:
    import planetary_computer
    PLANETARY_COMPUTER_AVAILABLE = True
except ImportError:
    PLANETARY_COMPUTER_AVAILABLE = False

# ---------------------------------------------------------------------------
# STAC and Model Constants
# ---------------------------------------------------------------------------
_STAC_SEARCH_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
_SAS_SIGN_URL    = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"
_STAC_TIMEOUT_S  = 15.0

# Lookback window for Sentinel-2 search
_MAX_DAYS_LOOKBACK = 30

# Scene-level cloud pre-filter — skip downloading SCL for very cloudy scenes
_MAX_SCENE_CLOUD = 80.0

# Pixel-level quality thresholds
# ROI must have at least this fraction of usable (non-cloud) pixels
_MIN_USABLE_FRACTION = 0.40   # 40%

# SCL band resolution for masking (fast downsampled read)
_SCL_READ_SHAPE = (64, 64)

# RDNet input resolution
_BAND_READ_SHAPE = (256, 256)

# Sentinel-2 SCL class values
# Scene Classification Layer: https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/scene-classifier/
_SCL_CLOUD_CLASSES = frozenset({
    1,   # Saturated / Defective
    3,   # Cloud Shadow
    8,   # Cloud Medium Probability
    9,   # Cloud High Probability
    10,  # Thin Cirrus
})
# No-data class
_SCL_NO_DATA = 0

# 10 spectral bands required by AMFITRITE RDNet architecture (in order)
_HAB_BANDS = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]


class AmfitriteHABAdapter(MarineDataAdapter):
    """
    Adapter for Harmful Algal Bloom (HAB) detection using real Sentinel-2 imagery.

    Execution path:
    1. Search Planetary Computer STAC for Sentinel-2 L2A tiles (30-day lookback).
    2. For each candidate tile (most recent first):
       a. Download SCL band and compute pixel-level cloud-free fraction of ROI.
       b. If ROI has >= 40% usable pixels, download 10 HAB bands.
       c. Feed real satellite pixels into RDNet (if weights loaded) → Tier 2 result.
    3. If no usable tile found → honest Tier-3 unresolved result (no fabricated score).

    NEVER uses randomized generation or synthetic imagery.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the PyTorch RDNet model.

        Args:
            model_path: Local path to 'model.pth' weights file.
                        If None or file missing, Tier 2 ML inference is unavailable.
        """
        self.model = None
        self.model_loaded = False

        if TORCH_AVAILABLE and TIMM_AVAILABLE and model_path and os.path.exists(model_path):
            try:
                # RDNet Base architecture — 10 spectral input channels, 2 output classes
                # DO NOT modify this architecture (M4 contract)
                self.model = timm.create_model(
                    "rdnet_base", pretrained=False, num_classes=2, in_chans=10
                )
                state_dict = torch.load(model_path, map_location="cpu")
                self.model.load_state_dict(state_dict)
                self.model.eval()
                self.model_loaded = True
            except Exception:
                self.model = None
                self.model_loaded = False

    # ------------------------------------------------------------------
    # Public interface (MarineDataAdapter contract)
    # ------------------------------------------------------------------

    def fetch_data(self, lat: float, lon: float, timestamp: str = None) -> Dict[str, Any]:
        """
        Run HAB detection for a specific coordinate and time.

        Parameters
        ----------
        lat, lon  : Query coordinate.
        timestamp : ISO 8601 UTC target time (e.g. waypoint eta_iso).
                    Defaults to now() if omitted.

        Returns
        -------
        MarineObservation-subset dict with hab_detected, hab_probability, and provenance.
        """
        time_iso     = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Explicit demo mock — never used unless DEMO_HAB_MOCK is set
        if self._demo_hab_mock_enabled():
            return self._attach_frozen_keys(
                self._demo_mock_result(lat, lon, time_iso, retrieved_at)
            )

        # --- Tier 2: Live STAC Search + Pixel-Level Cloud Masking + RDNet ---
        try:
            live_result = self._fetch_live_sentinel2_hab(lat, lon, time_iso, retrieved_at)
            if live_result is not None:
                return self._attach_frozen_keys(live_result)
        except Exception:
            pass

        # --- Tier 3: Honest unresolved result (NO mock classification) -------
        return self._attach_frozen_keys(
            self._no_imagery_result(lat, lon, time_iso, retrieved_at)
        )

    @staticmethod
    def _demo_hab_mock_enabled() -> bool:
        val = os.environ.get("DEMO_HAB_MOCK", "").strip().lower()
        return val in {"1", "true", "yes", "on"}

    @staticmethod
    def _severity_from_probability(hab_detected: Optional[bool], prob: Optional[float]) -> Optional[str]:
        if hab_detected is None or prob is None:
            return None
        if prob > 0.8:
            return "HIGH"
        if hab_detected:
            return "MODERATE"
        return "LOW"

    def _attach_frozen_keys(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Keep Step 09 §17.3 keys alongside additive PathFinder fields."""
        time_iso = result.get("time_iso")
        result["timestamp"] = time_iso
        provenance = result.get("provenance") or {}
        result["source"] = provenance.get("source")
        if "severity" not in result or result.get("severity") is None:
            if result.get("resolved") and result.get("hab_detected") is not None:
                result["severity"] = self._severity_from_probability(
                    result.get("hab_detected"), result.get("hab_probability")
                )
            else:
                result.setdefault("severity", None)
        return result

    def _demo_mock_result(
        self, lat: float, lon: float, time_iso: str, retrieved_at: str
    ) -> Dict[str, Any]:
        """
        Original lat>20 heuristic, only when DEMO_HAB_MOCK is set.
        Labelled as Tier 3 demo — not live imagery or model inference.
        """
        is_toxic_zone = lat > 20.0
        prob = 0.95 if is_toxic_zone else 0.05
        return {
            "lat":                    lat,
            "lon":                    lon,
            "time_iso":               time_iso,
            "sst_celsius":            None,
            "chlorophyll_mgm3":       None,
            "hab_detected":           is_toxic_zone,
            "hab_probability":        prob,
            "current_speed_kmh":      None,
            "current_direction_deg":  None,
            "resolved":               True,
            "severity":               "HIGH" if is_toxic_zone else "LOW",
            "provenance": {
                "source": (
                    "AMFITRITE-Sentinel2-HAB-RDNet (Mock Dataset) — "
                    "DEMO_HAB_MOCK=1, not live imagery"
                ),
                "retrieved_at":           retrieved_at,
                "validity_time":          time_iso,
                "fallback_tier":          3,
                "confidence":             "LOW",
                "demo_mode":              True,
                "rdnet_received_real_pixels": False,
            },
        }

    # ------------------------------------------------------------------
    # Tier 2: Live STAC Search with Pixel-Level Cloud Masking
    # ------------------------------------------------------------------

    def _fetch_live_sentinel2_hab(
        self,
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Search Planetary Computer STAC for usable Sentinel-2 L2A tiles.
        Iterates from most-recent to oldest, testing each tile's ROI cloud cover.
        """
        if not (RASTERIO_AVAILABLE and NUMPY_AVAILABLE):
            return None

        # Build 30-day lookback window
        try:
            target_dt = datetime.fromisoformat(time_iso.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            target_dt = datetime.now(timezone.utc)

        start_dt = target_dt - timedelta(days=_MAX_DAYS_LOOKBACK)
        dt_range  = (
            f"{start_dt.strftime('%Y-%m-%dT00:00:00Z')}/"
            f"{target_dt.strftime('%Y-%m-%dT23:59:59Z')}"
        )

        # 0.1° ROI (~11km) around query point
        roi_bbox = [
            round(lon - 0.05, 4), round(lat - 0.05, 4),
            round(lon + 0.05, 4), round(lat + 0.05, 4),
        ]

        payload = {
            "collections": ["sentinel-2-l2a"],
            "bbox":        roi_bbox,
            "datetime":    dt_range,
            "query":       {"eo:cloud_cover": {"lt": _MAX_SCENE_CLOUD}},
            "sortby":      [{"field": "properties.datetime", "direction": "desc"}],
            "limit":       10,
        }

        resp = httpx.post(_STAC_SEARCH_URL, json=payload, timeout=_STAC_TIMEOUT_S)
        if resp.status_code != 200:
            return None
        stac_data = resp.json()

        features = stac_data.get("features", [])
        if not features:
            return None

        # Iterate tiles most-recent-first
        for feature in features:
            result = self._try_tile(feature, lat, lon, roi_bbox, time_iso, retrieved_at)
            if result is not None:
                return result

        return None

    def _try_tile(
        self,
        feature: Dict[str, Any],
        lat: float,
        lon: float,
        roi_bbox: List[float],
        time_iso: str,
        retrieved_at: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to produce a HAB result from one Sentinel-2 tile.

        Steps:
        1. Download SCL band → compute pixel-level cloud-free fraction.
        2. Reject tile if ROI cloud-free fraction < MIN_USABLE_FRACTION.
        3. Download 10 HAB bands as real satellite pixels.
        4. Run RDNet if model weights loaded → Tier 2 result.
        5. If model not loaded but ROI is usable → Tier 3, resolved=False,
           but with honest sentinel2_item_id provenance.
        """
        props  = feature.get("properties", {})
        assets = feature.get("assets", {})
        tile_id       = feature.get("id", "UNKNOWN")
        scene_cloud   = float(props.get("eo:cloud_cover", 100.0))
        tile_datetime = props.get("datetime", time_iso)

        # Step 1: pixel-level cloud masking via SCL band
        scl_asset = assets.get("SCL") or assets.get("scl")
        if not scl_asset:
            return None

        scl_href = self._sign_asset_url(scl_asset.get("href", ""))
        if not scl_href:
            return None

        try:
            cloud_free_frac = self._compute_roi_cloud_free_fraction(scl_href, roi_bbox)
        except Exception:
            return None  # Can't assess this tile; try next

        # Step 2: Reject if ROI too cloudy
        if cloud_free_frac < _MIN_USABLE_FRACTION:
            return None  # Try next tile

        # Shared metadata recorded in provenance regardless of model availability
        prov_meta = {
            "sentinel2_item_id":   tile_id,
            "sentinel2_datetime":  tile_datetime,
            "scene_cloud_cover":   round(scene_cloud, 2),
            "roi_cloud_free_pct":  round(cloud_free_frac * 100, 1),
            "bands_used":          _HAB_BANDS,
        }

        # Step 3: Download real pixel data only when RDNet inference is available.
        # A usable SCL tile can still be reported honestly when model weights are
        # absent, without requiring the inference bands to be accessible.
        if self.model_loaded and self.model is not None and TORCH_AVAILABLE:
            tensor_10band = self._read_and_assemble_tensor(assets, roi_bbox)
            if tensor_10band is None:
                return None
            try:
                with torch.no_grad():
                    output = self.model(tensor_10band)
                    prob   = float(torch.softmax(output, dim=1)[0, 1].item())
            except Exception:
                return None

            is_bloom   = prob > 0.5
            confidence = "HIGH" if cloud_free_frac > 0.70 and scene_cloud < 15.0 else "MODERATE"

            return {
                "lat":                    lat,
                "lon":                    lon,
                "time_iso":               time_iso,
                "sst_celsius":            None,
                "chlorophyll_mgm3":       None,
                "hab_detected":           is_bloom,
                "hab_probability":        round(prob, 4),
                "current_speed_kmh":      None,
                "current_direction_deg":  None,
                "resolved":               True,
                "provenance": {
                    "source": (
                        f"Sentinel-2 L2A ({tile_id}, scene cloud {scene_cloud:.1f}%, "
                        f"ROI usable {cloud_free_frac*100:.1f}%) "
                        "via Planetary Computer + AMFITRITE RDNet"
                    ),
                    "retrieved_at":           retrieved_at,
                    "validity_time":          tile_datetime,
                    "fallback_tier":          2,
                    "confidence":             confidence,
                    "rdnet_received_real_pixels": True,
                    **prov_meta,
                },
            }

        # Model weights absent but imagery is usable — honest report, no inference
        return {
            "lat":                    lat,
            "lon":                    lon,
            "time_iso":               time_iso,
            "sst_celsius":            None,
            "chlorophyll_mgm3":       None,
            "hab_detected":           None,
            "hab_probability":        None,
            "current_speed_kmh":      None,
            "current_direction_deg":  None,
            "resolved":               False,
            "provenance": {
                "source": (
                    f"Sentinel-2 L2A ({tile_id}, scene cloud {scene_cloud:.1f}%, "
                    f"ROI usable {cloud_free_frac*100:.1f}%) via Planetary Computer -- "
                    "RDNet weights not available (model_path not provided or file missing)"
                ),
                "retrieved_at":           retrieved_at,
                "validity_time":          tile_datetime,
                "fallback_tier":          3,
                "confidence":             "LOW",
                "rdnet_received_real_pixels": False,
                **prov_meta,
            },
        }

    # ------------------------------------------------------------------
    # SCL pixel-level cloud masking
    # ------------------------------------------------------------------

    def _compute_roi_cloud_free_fraction(
        self, scl_signed_href: str, roi_bbox: List[float]
    ) -> float:
        """
        Download the SCL band for the ROI and compute the cloud-free fraction.

        Cloud-free fraction = usable pixels / total pixels.
        Usable = not cloud (classes 1,3,8,9,10) and not no-data (class 0).

        Returns
        -------
        float in [0.0, 1.0]
        """
        with rasterio.open(scl_signed_href) as src:
            # Reproject the WGS84 roi_bbox into the raster's native CRS (typically UTM)
            # before computing the pixel window. Without this, passing lat/lon coordinates
            # to a UTM-projected raster produces nonsensical window offsets.
            try:
                native_bbox = self._reproject_bbox_to_crs(
                    roi_bbox, src.crs
                )
                requested_window = from_bounds(
                    native_bbox[0], native_bbox[1], native_bbox[2], native_bbox[3],
                    src.transform,
                )
                dataset_window = Window(0, 0, src.width, src.height)
                window = requested_window.intersection(dataset_window)
            except Exception:
                # Tile does not overlap ROI or CRS conversion failed
                return 0.0

            if window.width <= 0 or window.height <= 0:
                return 0.0

            scl = src.read(
                1,
                window=window,
                out_shape=_SCL_READ_SHAPE,
                resampling=Resampling.nearest,
            )

        cloud_mask   = np.isin(scl, list(_SCL_CLOUD_CLASSES))
        no_data_mask = scl == _SCL_NO_DATA
        unusable     = cloud_mask | no_data_mask

        total   = scl.size
        usable  = int((~unusable).sum())
        return usable / total if total > 0 else 0.0

    # ------------------------------------------------------------------
    # Sentinel-2 band download and tensor assembly
    # ------------------------------------------------------------------

    def _read_and_assemble_tensor(
        self, assets: Dict[str, Any], roi_bbox: List[float]
    ) -> Optional[Any]:
        """
        Download all 10 Sentinel-2 HAB bands within the ROI and assemble a
        (1, 10, 256, 256) float32 tensor from actual rasterio reads.

        Returns None if any band is missing or unreadable.
        NEVER generates synthetic or random pixel data.
        """
        if not (TORCH_AVAILABLE and RASTERIO_AVAILABLE and NUMPY_AVAILABLE):
            return None

        band_arrays: List[Any] = []

        for b_name in _HAB_BANDS:
            asset = assets.get(b_name)
            if not asset:
                return None
            raw_href = asset.get("href", "")
            if not raw_href:
                return None

            signed_url = self._sign_asset_url(raw_href)

            try:
                with rasterio.open(signed_url) as src:
                    # Reproject WGS84 roi_bbox into the raster's native CRS (typically UTM)
                    try:
                        native_bbox = self._reproject_bbox_to_crs(roi_bbox, src.crs)
                        requested_window = from_bounds(
                            native_bbox[0], native_bbox[1], native_bbox[2], native_bbox[3],
                            src.transform,
                        )
                        dataset_window = Window(0, 0, src.width, src.height)
                        window = requested_window.intersection(dataset_window)
                    except Exception:
                        return None  # CRS conversion failed or tile does not overlap

                    if window.width <= 0 or window.height <= 0:
                        return None  # Band does not overlap tile

                    data = src.read(
                        1,
                        window=window,
                        out_shape=_BAND_READ_SHAPE,
                        resampling=Resampling.bilinear,
                    )
                    # Normalize Sentinel-2 DN (0–10 000) → surface reflectance (0.0–1.0)
                    band_arr = data.astype("float32") / 10000.0
                    band_arrays.append(band_arr)
            except Exception:
                return None

        if len(band_arrays) != 10:
            return None

        # Stack into (10, 256, 256) from real satellite pixels
        stacked = np.stack(band_arrays, axis=0)
        # Add batch dim → (1, 10, 256, 256)
        tensor  = torch.from_numpy(stacked).unsqueeze(0)
        return tensor

    # ------------------------------------------------------------------
    # CRS reprojection helper
    # ------------------------------------------------------------------

    def _reproject_bbox_to_crs(
        self, wgs84_bbox: List[float], target_crs: Any
    ) -> List[float]:
        """
        Reproject a WGS84 bounding box [west, south, east, north] into target_crs.
        Returns [left, bottom, right, top] in the target CRS.
        """
        from rasterio.crs import CRS as RasterioCRS  # lazy — avoids affecting RASTERIO_AVAILABLE
        from rasterio.warp import transform_bounds
        wgs84 = RasterioCRS.from_epsg(4326)
        left, bottom, right, top = transform_bounds(
            wgs84, target_crs,
            wgs84_bbox[0], wgs84_bbox[1], wgs84_bbox[2], wgs84_bbox[3],
        )
        return [left, bottom, right, top]

    # ------------------------------------------------------------------
    # Asset URL signing
    # ------------------------------------------------------------------

    def _sign_asset_url(self, href: str) -> str:
        """Sign a Planetary Computer asset href using the SDK or REST SAS endpoint."""
        if not href:
            return href

        if PLANETARY_COMPUTER_AVAILABLE:
            try:
                return planetary_computer.sign(href)
            except Exception:
                pass

        try:
            r = httpx.get(f"{_SAS_SIGN_URL}?href={href}", timeout=5.0)
            if r.status_code == 200:
                return r.json().get("href", href)
        except Exception:
            pass

        return href

    # ------------------------------------------------------------------
    # Tier 3: Honest unresolved result
    # ------------------------------------------------------------------

    def _no_imagery_result(
        self, lat: float, lon: float, time_iso: str, retrieved_at: str
    ) -> Dict[str, Any]:
        """
        Return an honest, unresolved Tier-3 result when no cloud-free
        Sentinel-2 imagery exists in the 30-day lookback window.

        hab_detected and hab_probability are explicitly None.
        The previous latitude-based heuristic (lat > 20.0) is intentionally absent.
        """
        return {
            "lat":                    lat,
            "lon":                    lon,
            "time_iso":               time_iso,
            "sst_celsius":            None,
            "chlorophyll_mgm3":       None,
            "hab_detected":           None,
            "hab_probability":        None,
            "current_speed_kmh":      None,
            "current_direction_deg":  None,
            "resolved":               False,
            "provenance": {
                "source": (
                    f"AMFITRITE-Sentinel2-HAB-RDNet -- No usable cloud-free Sentinel-2 "
                    f"imagery found within {_MAX_DAYS_LOOKBACK}-day lookback window"
                ),
                "retrieved_at":           retrieved_at,
                "validity_time":          time_iso,
                "fallback_tier":          3,
                "confidence":             "LOW",
                "rdnet_received_real_pixels": False,
            },
        }
