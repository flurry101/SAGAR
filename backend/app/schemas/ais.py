"""Normalized AIS domain models."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class VesselState:
    mmsi: str
    name: str
    ship_type: int
    ship_category: str
    lat: float
    lon: float
    sog_knots: float
    cog_deg: float
    heading: Optional[float]
    timestamp: datetime
    destination: Optional[str] = None
    flag: Optional[str] = None
    length: Optional[float] = None
    width: Optional[float] = None

    def __post_init__(self) -> None:
        self.mmsi = str(self.mmsi)
        if isinstance(self.timestamp, str):
            value = self.timestamp.replace("Z", "+00:00")
            self.timestamp = datetime.fromisoformat(value)
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["timestamp"] = self.timestamp.astimezone(timezone.utc).isoformat()
        return result
