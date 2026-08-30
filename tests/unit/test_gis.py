"""Unit tests for GIS module (geocoder, trajectory, geofence)."""

import pytest
import os
from datetime import datetime, timezone
from app.gis.geocoder import geocode, COASTAL_PORTS_DB
from app.gis.trajectory import (
    calculate_trajectory,
    haversine_distance_nm,
    interpolate_waypoint,
)
from app.gis.geofence import check_geofence
from app.gis.schemas import Waypoint, LegLabel


class TestGeocoder:
    def test_geocode_known_port(self):
        lat, lon = geocode("Cochin")
        assert lat == pytest.approx(9.9674)
        assert lon == pytest.approx(76.2429)

    def test_geocode_case_insensitive(self):
        lat, lon = geocode("MANGALORE")
        assert lat == pytest.approx(12.9141)
        assert lon == pytest.approx(74.8560)

    def test_geocode_unknown_port_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown location"):
            geocode("NonExistentPort123")

    def test_geocode_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="Location name cannot be empty"):
            geocode("   ")


class TestTrajectoryCalculations:
    def test_haversine_distance_sanity(self):
        # Distance between Cochin (9.9674, 76.2429) and Mangalore (12.9141, 74.8560) ~198 nm
        dist = haversine_distance_nm(9.9674, 76.2429, 12.9141, 74.8560)
        assert 190.0 < dist < 210.0

    def test_haversine_zero_distance(self):
        dist = haversine_distance_nm(10.0, 75.0, 10.0, 75.0)
        assert dist == pytest.approx(0.0)

    def test_calculate_trajectory_waypoint_counts_and_legs(self):
        traj = calculate_trajectory(
            origin_lat=9.9674,
            origin_lon=76.2429,
            dest_lat=12.9141,
            dest_lon=74.8560,
            departure_time="2026-08-29T10:00:00Z",
            vessel_speed_knots=10.0,
            sample_interval_nm=50.0,
            fishing_duration_hours=2.0,
        )

        assert len(traj.waypoints) > 5
        legs = set(wp.leg_label for wp in traj.waypoints)
        assert LegLabel.OUTBOUND in legs
        assert LegLabel.FISHING in legs
        assert LegLabel.RETURN in legs

    def test_calculate_trajectory_monotonically_increasing_timestamps(self):
        traj = calculate_trajectory(
            origin_lat=9.9674,
            origin_lon=76.2429,
            dest_lat=12.9141,
            dest_lon=74.8560,
            departure_time="2026-08-29T10:00:00Z",
            vessel_speed_knots=12.0,
        )

        timestamps = [
            datetime.fromisoformat(wp.timestamp.replace("Z", "+00:00"))
            for wp in traj.waypoints
        ]
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i - 1]

    def test_calculate_trajectory_zero_distance_trip(self):
        traj = calculate_trajectory(
            origin_lat=9.9674,
            origin_lon=76.2429,
            dest_lat=9.9674,
            dest_lon=76.2429,
            departure_time="2026-08-29T10:00:00Z",
            vessel_speed_knots=10.0,
            fishing_duration_hours=2.0,
        )

        assert traj.total_distance_nm == 0.0
        assert traj.total_duration_hours == 2.0
        assert len(traj.waypoints) == 2


class TestGeofenceChecking:
    def test_check_geofence_inside_zone(self):
        # Kochi naval zone in restricted_zones.geojson: lat 9.90 to 9.98, lon 76.15 to 76.25
        inside_wp = Waypoint(
            lat=9.94,
            lon=76.20,
            timestamp="2026-08-29T10:00:00Z",
            leg_label=LegLabel.OUTBOUND,
        )
        violations = check_geofence([inside_wp])
        assert len(violations) == 1
        assert violations[0]["zone_id"] == "RESTRICTED_NAVAL_01"

    def test_check_geofence_outside_zone(self):
        outside_wp = Waypoint(
            lat=15.0,
            lon=70.0,
            timestamp="2026-08-29T10:00:00Z",
            leg_label=LegLabel.OUTBOUND,
        )
        violations = check_geofence([outside_wp])
        assert len(violations) == 0
