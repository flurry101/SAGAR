"""Thread-safe in-memory cache for the latest AIS vessel states."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from threading import RLock
from typing import Dict, Iterable, List, Optional

from app.schemas.ais import VesselState


def decode_ship_type(code: int) -> str:
    """Map AIS type codes to the categories used by SAGAR traffic responses."""
    try:
        code = int(code)
    except (TypeError, ValueError):
        return "other"
    if 70 <= code <= 79:
        return "cargo"
    if 80 <= code <= 89:
        return "tanker"
    # Codes 35 and 55 are explicitly reserved for military/defense in SAGAR.
    if code in (35, 55):
        return "military/defense"
    if 30 <= code <= 39:
        return "fishing"
    if 60 <= code <= 69:
        return "passenger"
    if code in (50, 52):
        return "tug"
    return "other"


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in nautical miles."""
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 3440.065 * 2 * asin(sqrt(a))


class TrafficCache:
    def __init__(self) -> None:
        self._vessels: Dict[str, VesselState] = {}
        self._lock = RLock()

    def upsert_vessel(self, vessel: VesselState) -> VesselState:
        with self._lock:
            self._vessels[str(vessel.mmsi)] = vessel
        return vessel

    def get_vessel(self, mmsi: str) -> Optional[VesselState]:
        with self._lock:
            return self._vessels.get(str(mmsi))

    def get_all_vessels(self) -> List[VesselState]:
        with self._lock:
            return list(self._vessels.values())

    def prune_stale_vessels(self, max_age_minutes: float = 30.0) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        with self._lock:
            stale = [mmsi for mmsi, vessel in self._vessels.items() if vessel.timestamp < cutoff]
            for mmsi in stale:
                del self._vessels[mmsi]
        return len(stale)

    def get_active_vessels_in_radius(self, lat: float, lon: float, radius_nm: float) -> List[VesselState]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        return [
            vessel for vessel in self.get_all_vessels()
            if vessel.timestamp >= cutoff and haversine_nm(lat, lon, vessel.lat, vessel.lon) <= radius_nm
        ]

    def to_geojson(self, vessels: Optional[Iterable[VesselState]] = None) -> Dict:
        vessels = self.get_all_vessels() if vessels is None else vessels
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [vessel.lon, vessel.lat]},
                    "properties": {
                        "mmsi": vessel.mmsi, "name": vessel.name,
                        "ship_type": vessel.ship_type, "ship_category": vessel.ship_category,
                        "sog_knots": vessel.sog_knots, "cog_deg": vessel.cog_deg,
                        "heading": vessel.heading, "timestamp": vessel.timestamp.isoformat(),
                        "destination": vessel.destination, "flag": vessel.flag,
                        "length": vessel.length, "width": vessel.width,
                    },
                }
                for vessel in vessels
            ],
        }
