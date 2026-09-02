from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.ais_adapter import AISAdapter
from app.adapters.traffic_cache import TrafficCache, decode_ship_type, haversine_nm
from app.navigation.colregs import (
    calculate_collision_risk_index,
    classify_colregs_encounter,
    compute_relative_kinematics,
)
from app.schemas.ais import VesselState
from app.services.ais_websocket import AISWebSocketListener, normalize_ais_message


def vessel(mmsi="419000001", lat=10.0, lon=75.0, timestamp=None):
    return VesselState(mmsi=mmsi, name="Test vessel", ship_type=70, ship_category="cargo",
                       lat=lat, lon=lon, sog_knots=10, cog_deg=90, heading=90,
                       timestamp=timestamp or datetime.now(timezone.utc))


def test_ship_types_and_haversine():
    assert decode_ship_type(70) == "cargo"
    assert decode_ship_type(80) == "tanker"
    assert decode_ship_type(30) == "fishing"
    assert decode_ship_type(35) == "military/defense"
    assert decode_ship_type(60) == "passenger"
    assert decode_ship_type(52) == "tug"
    assert decode_ship_type(99) == "other"
    assert haversine_nm(0, 0, 1, 0) == pytest.approx(60.04, rel=0.01)


def test_cache_upsert_prune_radius_and_geojson():
    cache = TrafficCache()
    cache.upsert_vessel(vessel())
    cache.upsert_vessel(vessel("419000002", lat=20, lon=75))
    cache.upsert_vessel(vessel("old", timestamp=datetime.now(timezone.utc) - timedelta(hours=1)))
    assert cache.get_vessel("419000001").name == "Test vessel"
    assert len(cache.get_active_vessels_in_radius(10, 75, 5)) == 1
    assert cache.prune_stale_vessels(30) == 1
    feature = cache.to_geojson(cache.get_active_vessels_in_radius(10, 75, 5))["features"][0]
    assert feature["geometry"]["coordinates"] == [75.0, 10.0]
    assert feature["properties"]["ship_category"] == "cargo"


def test_fallback_adapter_uses_tier_three_and_filters():
    result = AISAdapter(cache=TrafficCache(), api_key="").get_vessels(18.94, 72.82, 50)
    assert result["provenance"] == {"source": "mock_fallback", "tier": 3}
    assert result["geojson"]["type"] == "FeatureCollection"
    assert result["geojson"]["features"]


def test_ais_message_normalization_merges_static_data():
    cache = TrafficCache()
    normalize_ais_message({"MessageType": "PositionReport", "Message": {"PositionReport": {
        "UserID": 123, "Latitude": 10.0, "Longitude": 75.0, "Sog": 8, "Cog": 90, "TrueHeading": 91
    }}}, cache)
    updated = normalize_ais_message({"MessageType": "ShipStaticData", "Message": {"ShipStaticData": {
        "UserID": 123, "Name": "  Vessel One ", "Type": 80, "Destination": "KOCHI",
        "Dimension": {"A": 100, "B": 20, "C": 10, "D": 10}
    }}}, cache)
    assert updated.name == "Vessel One"
    assert updated.ship_category == "tanker"
    assert updated.length == 120


def test_listener_retries_connection_failures(monkeypatch):
    import asyncio

    async def scenario():
        listener = AISWebSocketListener(cache=TrafficCache(), api_key="test")
        attempts = 0

        async def fail_once():
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise OSError("network unavailable")
            raise asyncio.CancelledError()

        monkeypatch.setattr(listener, "_connect_and_consume", fail_once)
        task = asyncio.create_task(listener._run())
        await asyncio.sleep(1.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return attempts

    assert asyncio.run(scenario()) >= 1


def test_colregs_head_on_crossing_and_safe():
    own = {"lat": 0, "lon": 0, "sog_knots": 12, "cog_deg": 0}
    head_on = {"lat": 0.1, "lon": 0, "sog_knots": 12, "cog_deg": 180}
    crossing = {"lat": 0.05, "lon": 0.05, "sog_knots": 12, "cog_deg": 270}
    safe = {"lat": 1, "lon": 1, "sog_knots": 10, "cog_deg": 90}
    assert classify_colregs_encounter(own, head_on) == "Head-on (Rule 14)"
    assert classify_colregs_encounter(own, crossing) == "Crossing Give-Way (Rule 15)"
    assert classify_colregs_encounter(own, safe) == "Safe"
    kin = compute_relative_kinematics(own, head_on)
    assert kin["cpa_nm"] == pytest.approx(0, abs=0.01)
    assert kin["tcpa_hours"] == pytest.approx(0.25, rel=0.05)
    assert 0 <= calculate_collision_risk_index(kin) <= 1
