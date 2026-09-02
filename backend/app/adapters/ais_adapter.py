"""Tiered AIS traffic adapter: live cache first, deterministic fallback second."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.adapters.traffic_cache import TrafficCache, decode_ship_type, haversine_nm
from app.config import settings
from app.schemas.ais import VesselState
from app.services.ais_websocket import traffic_cache

FALLBACK_PATH = Path(__file__).resolve().parents[2] / "data" / "fallback" / "ais_vessels_sample.json"


class AISAdapter:
    def __init__(self, cache: TrafficCache = traffic_cache, api_key: Optional[str] = None) -> None:
        self.cache = cache
        self.api_key = api_key if api_key is not None else settings.AISSTREAM_API_KEY.strip()

    def get_vessels(self, lat: float, lon: float, radius_nm: float = 50.0) -> Dict:
        live = self.cache.get_active_vessels_in_radius(lat, lon, radius_nm)
        if live and self.api_key:
            vessels, provenance = live, {"source": "live_aisstream", "tier": 1}
        else:
            vessels, provenance = self._fallback_vessels(lat, lon, radius_nm), {"source": "mock_fallback", "tier": 3}
        geojson = self.cache.to_geojson(vessels)
        geojson["provenance"] = provenance
        return {"vessels": [v.to_dict() for v in vessels], "geojson": geojson, "provenance": provenance}

    @staticmethod
    def _fallback_vessels(lat: float, lon: float, radius_nm: float) -> List[VesselState]:
        with FALLBACK_PATH.open(encoding="utf-8") as fallback_file:
            records = json.load(fallback_file)
        vessels = []
        for record in records:
            if haversine_nm(lat, lon, record["lat"], record["lon"]) <= radius_nm:
                code = int(record.get("ship_type", 0))
                payload = dict(record)
                payload.pop("ship_type", None)
                vessels.append(VesselState(
                    **payload, ship_type=code, ship_category=decode_ship_type(code),
                    timestamp=datetime.now(timezone.utc),
                ))
        return vessels
