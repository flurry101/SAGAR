"""
Test Suite — Alert Generation

Tests that the weather node generates structured alerts from observations.
"""

import pytest
from app.graph.nodes.weather import _generate_alerts


# ---- Test A: High wave alert ----

def test_high_wave_alert():
    """Wave height >= 2.0m should generate HIGH_WAVE alert."""
    obs = [{"weather": {"wave_height_m": 2.5, "wind_speed_kmh": 10}, "lat": 9.0, "lon": 76.0, "time_iso": "2026-08-30T10:00:00Z"}]
    alerts = _generate_alerts(obs, {})
    types = [a["alert_type"] for a in alerts]
    assert "HIGH_WAVE" in types
    high_wave = next(a for a in alerts if a["alert_type"] == "HIGH_WAVE")
    assert high_wave["severity"] == "HIGH"
    assert "2.5" in high_wave["message"]


# ---- Test B: Extreme wave alert ----

def test_extreme_wave_alert():
    """Wave height >= 4.0m should generate EXTREME_WAVE (SEVERE)."""
    obs = [{"weather": {"wave_height_m": 5.0, "wind_speed_kmh": 10}, "lat": 9.0, "lon": 76.0, "time_iso": "2026-08-30T10:00:00Z"}]
    alerts = _generate_alerts(obs, {})
    types = [a["alert_type"] for a in alerts]
    assert "EXTREME_WAVE" in types
    extreme = next(a for a in alerts if a["alert_type"] == "EXTREME_WAVE")
    assert extreme["severity"] == "SEVERE"


# ---- Test C: Strong wind alert ----

def test_strong_wind_alert():
    """Wind >= 40 km/h should generate STRONG_WIND alert."""
    obs = [{"weather": {"wave_height_m": 1.0, "wind_speed_kmh": 45}, "lat": 9.0, "lon": 76.0, "time_iso": "2026-08-30T10:00:00Z"}]
    alerts = _generate_alerts(obs, {})
    types = [a["alert_type"] for a in alerts]
    assert "STRONG_WIND" in types


# ---- Test D: Cyclone alert from hazard data ----

def test_cyclone_alert():
    """Active cyclone should generate CYCLONE alert with SEVERE severity."""
    obs = [{"weather": {"wave_height_m": 1.0, "wind_speed_kmh": 10}, "lat": 9.0, "lon": 76.0, "time_iso": "2026-08-30T10:00:00Z"}]
    hazard_data = {"cyclone_active": True, "hazards": []}
    alerts = _generate_alerts(obs, hazard_data)
    types = [a["alert_type"] for a in alerts]
    assert "CYCLONE" in types
    cyclone = next(a for a in alerts if a["alert_type"] == "CYCLONE")
    assert cyclone["severity"] == "SEVERE"


# ---- Test E: Low visibility alert ----

def test_low_visibility_alert():
    """Visibility < 1 km should generate LOW_VISIBILITY alert."""
    obs = [{"weather": {"wave_height_m": 1.0, "wind_speed_kmh": 10, "visibility_km": 0.5}, "lat": 9.0, "lon": 76.0, "time_iso": "2026-08-30T10:00:00Z"}]
    alerts = _generate_alerts(obs, {})
    types = [a["alert_type"] for a in alerts]
    assert "LOW_VISIBILITY" in types


# ---- Test F: No alerts when conditions are safe ----

def test_no_alerts_safe_conditions():
    """Safe conditions should produce zero alerts."""
    obs = [{"weather": {"wave_height_m": 0.5, "wind_speed_kmh": 10, "visibility_km": 10}, "lat": 9.0, "lon": 76.0, "time_iso": "2026-08-30T10:00:00Z"}]
    alerts = _generate_alerts(obs, {})
    assert len(alerts) == 0


# ---- Test G: Multiple alerts from single observation ----

def test_multiple_alerts():
    """Extreme conditions should generate multiple alerts."""
    obs = [{"weather": {"wave_height_m": 5.0, "wind_speed_kmh": 70, "visibility_km": 0.3}, "lat": 9.0, "lon": 76.0, "time_iso": "2026-08-30T10:00:00Z"}]
    alerts = _generate_alerts(obs, {"cyclone_active": True, "hazards": []})
    types = [a["alert_type"] for a in alerts]
    assert "EXTREME_WAVE" in types
    assert "EXTREME_WIND" in types
    assert "LOW_VISIBILITY" in types
    assert "CYCLONE" in types
