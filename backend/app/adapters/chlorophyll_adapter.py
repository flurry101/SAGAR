"""
MOSDAC Chlorophyll-a adapter.

Reads chlorophyll-a (chla) from the MOSDAC NetCDF product and returns
the value at the nearest available grid cell.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import xarray as xr

from .base_adapter import MarineDataAdapter


_DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "fallback"
    / "chlorophyll"
    / "chlorophyll.nc"
)


class ChlorophyllAdapter(MarineDataAdapter):
    """Reads MOSDAC chlorophyll-a satellite data from NetCDF."""

    def fetch_data(
        self,
        lat: float,
        lon: float,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:

        time_iso = timestamp or datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        retrieved_at = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        # Validate coordinates
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return self._unresolvable(
                lat, lon, time_iso, retrieved_at, "Invalid latitude/longitude."
            )

        if not _DATA_FILE.exists():
            return self._unresolvable(
                lat,
                lon,
                time_iso,
                retrieved_at,
                f"MOSDAC chlorophyll file not found: {_DATA_FILE}",
            )

        try:
            with xr.open_dataset(_DATA_FILE) as ds:
                chla = ds["chla"].isel(time=0, lev=0)

                # Convert longitude to 0..360 convention used by dataset
                dataset_lon = lon % 360.0

                # Select nearest cell point once
                nearest_cell = chla.sel(lat=lat, lon=dataset_lon, method="nearest")
                value = nearest_cell.item()

                # Handle land mask / invalid pixels (NaN / Inf)
                if value is None or not np.isfinite(value):
                    return self._unresolvable(
                        lat,
                        lon,
                        time_iso,
                        retrieved_at,
                        "MOSDAC chlorophyll value is unavailable at the nearest grid cell.",
                    )

                selected_lat = float(nearest_cell.lat.item())
                selected_lon = float(nearest_cell.lon.item())

                # Convert 0..360 back to -180..180 for standard GeoJSON output
                if selected_lon > 180:
                    selected_lon -= 360.0

                # Clean ISO conversion for numpy.datetime64 or datetime
                raw_time = ds["time"].isel(time=0).values
                try:
                    validity_time = str(np.datetime_as_string(raw_time, unit="S")) + "Z"
                except Exception:
                    validity_time = str(raw_time)

                return {
                    "lat": lat,
                    "lon": lon,
                    "time_iso": time_iso,
                    "chlorophyll_mg_m3": float(value),
                    "chlorophyll_mgm3": float(value),
                    "resolved": True,
                    "status": "ok",
                    "grid_lat": selected_lat,
                    "grid_lon": selected_lon,
                    "provenance": {
                        "source": "MOSDAC E06OCML4AC chlorophyll-a satellite product",
                        "retrieved_at": retrieved_at,
                        "validity_time": validity_time,
                        "fallback_tier": 1,
                        "confidence": "HIGH",
                    },
                }

        except Exception as exc:
            return self._unresolvable(
                lat,
                lon,
                time_iso,
                retrieved_at,
                f"Failed to read MOSDAC chlorophyll product: {exc}",
            )

    @staticmethod
    def _unresolvable(
        lat: float,
        lon: float,
        time_iso: str,
        retrieved_at: str,
        reason: str,
    ) -> Dict[str, Any]:
        return {
            "lat": lat,
            "lon": lon,
            "time_iso": time_iso,
            "chlorophyll_mg_m3": None,
            "chlorophyll_mgm3": None,
            "resolved": False,
            "status": "unresolvable",
            "reason": reason,
            "provenance": {
                "source": "MOSDAC E06OCML4AC chlorophyll-a satellite product",
                "retrieved_at": retrieved_at,
                "validity_time": time_iso,
                "fallback_tier": 1,
                "confidence": "LOW",
            },
        }