"""Format normalized marine observations for a future broadcast layer."""

from datetime import datetime, timezone
from typing import Any, Dict


def format_marine_event_for_broadcast(observation: Dict[str, Any]) -> Dict[str, Any]:
    """Return a stable, JSON-friendly event payload for WebSocket delivery."""
    provenance = observation.get("provenance")
    return {
        "event_type": "marine_observation",
        "occurred_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": {
            "lat": observation.get("lat"),
            "lon": observation.get("lon"),
        },
        "time_iso": observation.get("time_iso"),
        "data": {
            "sst_celsius": observation.get("sst_celsius"),
            "chlorophyll_mg_m3": observation.get("chlorophyll_mg_m3"),
            "tide_height_m": observation.get("tide_height_m"),
            "depth_m": observation.get("depth_m"),
            "hab_detected": observation.get("hab_detected"),
            "hab_probability": observation.get("hab_probability"),
            "resolved": observation.get("resolved", False),
            "status": observation.get("status"),
        },
        "provenance": provenance,
    }
