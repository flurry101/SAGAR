"""AISstream.io background consumer with resilient reconnect behaviour."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.adapters.traffic_cache import TrafficCache, decode_ship_type
from app.config import settings
from app.schemas.ais import VesselState

logger = logging.getLogger(__name__)
AISSTREAM_URL = "wss://stream.aisstream.io/v0/stream"
INDIAN_OCEAN_BBOX = [[[0.0, 50.0], [25.0, 100.0]]]
traffic_cache = TrafficCache()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _timestamp(value: Any) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def normalize_ais_message(payload: Dict[str, Any], cache: TrafficCache = traffic_cache) -> Optional[VesselState]:
    """Merge AIS position/static messages into one normalized vessel state."""
    message_type = payload.get("MessageType")
    message = payload.get("Message", {}).get(message_type, payload.get(message_type, {}))
    if not isinstance(message, dict):
        return None
    mmsi = message.get("UserID") or message.get("MMSI") or message.get("Mmsi")
    if mmsi is None:
        return None
    existing = cache.get_vessel(str(mmsi))

    if message_type == "PositionReport":
        lat, lon = message.get("Latitude"), message.get("Longitude")
        if lat is None or lon is None:
            return None
        ship_type = existing.ship_type if existing else 0
        vessel = VesselState(
            mmsi=str(mmsi), name=existing.name if existing else "Unknown vessel",
            ship_type=ship_type, ship_category=decode_ship_type(ship_type),
            lat=_number(lat), lon=_number(lon), sog_knots=_number(message.get("Sog")),
            cog_deg=_number(message.get("Cog")), heading=_number(message.get("TrueHeading"), None),
            timestamp=_timestamp(message.get("Timestamp")),
            destination=existing.destination if existing else None,
            flag=existing.flag if existing else None, length=existing.length if existing else None,
            width=existing.width if existing else None,
        )
        return cache.upsert_vessel(vessel)

    if message_type == "ShipStaticData" and existing:
        dimensions = message.get("Dimension") or {}
        ship_type = int(_number(message.get("Type"), existing.ship_type))
        vessel = VesselState(
            mmsi=existing.mmsi, name=(message.get("Name") or existing.name).strip(),
            ship_type=ship_type, ship_category=decode_ship_type(ship_type), lat=existing.lat, lon=existing.lon,
            sog_knots=existing.sog_knots, cog_deg=existing.cog_deg, heading=existing.heading,
            timestamp=existing.timestamp, destination=message.get("Destination") or existing.destination,
            flag=message.get("Flag") or existing.flag,
            length=_number(dimensions.get("A")) + _number(dimensions.get("B")) or existing.length,
            width=_number(dimensions.get("C")) + _number(dimensions.get("D")) or existing.width,
        )
        return cache.upsert_vessel(vessel)
    return None


class AISWebSocketListener:
    def __init__(self, cache: TrafficCache = traffic_cache, api_key: Optional[str] = None) -> None:
        self.cache = cache
        self.api_key = api_key if api_key is not None else settings.AISSTREAM_API_KEY.strip()
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self.api_key and self._task is None:
            self._task = asyncio.create_task(self._run(), name="aisstream-listener")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        delay = 1.0
        while True:
            try:
                await self._connect_and_consume()
                delay = 1.0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("AISstream connection failed; reconnecting in %.1fs: %s", delay, exc)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60.0)

    async def _connect_and_consume(self) -> None:
        try:
            import websockets
        except ImportError as exc:  # protects deployments that omit optional live support
            raise RuntimeError("websockets dependency is not installed") from exc
        subscription = {"APIKey": self.api_key, "BoundingBoxes": INDIAN_OCEAN_BBOX}
        async with websockets.connect(AISSTREAM_URL, ping_interval=20, ping_timeout=20) as socket:
            await socket.send(json.dumps(subscription))
            async for raw_message in socket:
                try:
                    normalize_ais_message(json.loads(raw_message), self.cache)
                    self.cache.prune_stale_vessels()
                except (json.JSONDecodeError, TypeError, ValueError) as exc:
                    logger.debug("Ignoring malformed AIS message: %s", exc)
