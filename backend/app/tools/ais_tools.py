"""Agent-facing AIS traffic helpers."""
from app.adapters.ais_adapter import AISAdapter

_adapter = AISAdapter()


def get_nearby_vessels(lat: float, lon: float, radius_nm: float = 50.0):
    return _adapter.get_vessels(lat, lon, radius_nm)
