# attr: m1
# [unit tests for pydantic data schemas]
import pytest
from app.schemas.common import APIResponse, ErrorResponse, Meta, ErrorDetails
from app.schemas.provenance import Provenance
from app.schemas.trajectory import Waypoint, Trajectory, GeofenceResult
from app.schemas.weather import WeatherObservation, Alert
from app.schemas.marine import MarineObservation, PFZData
from app.schemas.vessel import VesselProfile, VesselCreate, VesselUpdate
from app.schemas.advisory import HazardFlag, RiskEvidence, Advisory, VisualizationSpec, Report
from app.schemas.trip import (
    TripContext,
    TripAssessRequest,
    TripContinueRequest,
    ChatRequest,
    TripResponseData,
)
from app.schemas.copilot import CopilotRequest, CopilotResponse, CopilotMessage
from app.schemas.assessment import AssessmentDetailResponse


def test_meta_and_common_envelopes():
    # [test apiresponse envelope serialization]
    meta = Meta(request_id="req-123", version="v1")
    assert meta.request_id == "req-123"

    res = APIResponse(
        status="success",
        data={"message": "ok"},
        meta=meta,
    )
    assert res.status == "success"
    assert res.data["message"] == "ok"
    assert res.meta.request_id == "req-123"

    err = ErrorResponse(
        status="error",
        error=ErrorDetails(code="TEST_ERROR", message="something went wrong"),
        meta=meta,
    )
    assert err.error.code == "TEST_ERROR"


def test_vessel_profile_schemas():
    # [test vessel validation constraints]
    vessel = VesselProfile(
        vessel_id="ves-001",
        vessel_type="mechanized_trawler",
        beam_width_m=4.5,
        length_m=12.0,
        cruising_speed_kmh=18.0,
        has_ais=True,
    )
    assert vessel.beam_width_m == 4.5
    assert vessel.cruising_speed_kmh == 18.0

    # [test validation failure on negative beam]
    with pytest.raises(Exception):
        VesselProfile(beam_width_m=-1.0)


def test_trajectory_and_waypoint_schemas():
    # [test trajectory waypoints serialization]
    wp1 = Waypoint(lat=12.87, lon=74.84, eta_iso="2026-08-31T05:00:00Z", phase="outbound")
    wp2 = Waypoint(lat=12.75, lon=74.50, eta_iso="2026-08-31T07:00:00Z", phase="fishing")

    traj = Trajectory(
        route_id="ROUTE-01",
        total_distance_km=85.4,
        waypoints=[wp1, wp2],
        geofence_intersections=[
            GeofenceResult(zone_name="Kochi Naval Exclusion", intersects=False),
        ],
    )
    assert len(traj.waypoints) == 2
    assert traj.total_distance_km == 85.4


def test_weather_and_marine_schemas():
    # [test weather and marine observations]
    prov = Provenance(
        source_name="Open-Meteo",
        source_type="authoritative",
        retrieved_at="2026-08-31T04:00:00Z",
        fallback_tier=1,
    )

    weather = WeatherObservation(
        lat=12.87,
        lon=74.84,
        time_iso="2026-08-31T05:00:00Z",
        wave_height_m=1.8,
        wind_speed_kmh=22.5,
        provenance=prov,
    )
    assert weather.wave_height_m == 1.8

    marine = MarineObservation(
        lat=12.87,
        lon=74.84,
        time_iso="2026-08-31T05:00:00Z",
        sst_celsius=28.5,
        hab_detected=False,
        provenance=prov,
    )
    assert marine.sst_celsius == 28.5


def test_advisory_and_risk_evidence():
    # [test risk evidence and advisory synthesis schemas]
    flag = HazardFlag(
        hazard_type="WAVE_HEIGHT_EXCEEDED",
        phase="return",
        waypoint_index=3,
        observed_value=2.8,
        threshold_value=1.125,
        severity="SEVERE",
    )
    risk = RiskEvidence(
        advisory_category="SEVERE_HAZARD_OVERLAP",
        risk_level="SEVERE",
        hazard_flags=[flag],
    )
    assert risk.risk_level == "SEVERE"
    assert len(risk.hazard_flags) == 1

    adv = Advisory(
        advisory_category="SEVERE_HAZARD_OVERLAP",
        recommendation_text="Return earlier due to high wave conditions.",
        reason="Wave height exceeds vessel stability threshold.",
        language="en",
    )
    assert adv.advisory_category == "SEVERE_HAZARD_OVERLAP"


def test_trip_and_chat_requests():
    # [test trip assess and chat request validation]
    req = ChatRequest(
        message="Leave at 5 AM from Mangalore to PFZ and return at 2 PM",
        language="kn",
    )
    assert req.message.startswith("Leave at 5 AM")
    assert req.language == "kn"

    copilot_req = CopilotRequest(
        message="Why did ORCA say my return trip is risky?",
        conversation_history=[
            CopilotMessage(role="user", content="hello"),
            CopilotMessage(role="assistant", content="hello! how can i help?"),
        ],
    )
    assert len(copilot_req.conversation_history) == 2
# attr: m1

