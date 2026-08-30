"""
OrcaState — LangGraph Shared State Definition

This TypedDict defines the single data object passed between all LangGraph
nodes in the ORCA Trip Planner workflow.

Reference: 07_DATA_MODEL.md, Section 3 (LangGraph Shared State)

Architecture:
    LangGraph decides → Supabase remembers → LangChain Copilot explains
"""

from __future__ import annotations

from typing import Any, TypedDict


class TripContext(TypedDict, total=False):
    """Extracted trip parameters from the fisher's natural language request."""
    trip_id: str
    fisher_id: str
    origin: str
    origin_lat: float
    origin_lon: float
    destination_type: str  # "PFZ", "CUSTOM", "HARBOR"
    destination_lat: float | None
    destination_lon: float | None
    departure_time_iso: str | None
    return_time_iso: str | None
    purpose: str  # "fishing", "transit", "exploration"


class VesselProfile(TypedDict, total=False):
    """Vessel specifications used for safety threshold calculations."""
    vessel_id: str
    vessel_type: str  # "mechanized_trawler", "motorized_gillnet", etc.
    beam_width_m: float
    length_m: float
    cruising_speed_kmh: float
    has_ais: bool


class Waypoint(TypedDict):
    """A single point on the vessel's spatio-temporal trajectory."""
    lat: float
    lon: float
    eta_iso: str  # ISO 8601 UTC
    phase: str  # "outbound", "fishing", "return"


class Provenance(TypedDict, total=False):
    """Source attribution and data quality metadata."""
    source_name: str
    source_type: str  # "authoritative", "ml_inference", "static_fallback"
    retrieved_at: str  # ISO 8601 UTC
    valid_until: str | None
    fallback_tier: int  # 1, 2, or 3
    confidence: float | None


class WeatherObservation(TypedDict, total=False):
    """Weather conditions at a specific waypoint and time."""
    waypoint_index: int
    lat: float
    lon: float
    time_iso: str
    wave_height_m: float | None
    wind_speed_kmh: float | None
    wind_direction_deg: float | None
    swell_height_m: float | None
    swell_direction_deg: float | None
    visibility_km: float | None
    precipitation_mm: float | None
    provenance: Provenance


class MarineObservation(TypedDict, total=False):
    """Marine/ocean conditions at a specific waypoint and time."""
    waypoint_index: int
    lat: float
    lon: float
    time_iso: str
    sst_celsius: float | None
    chlorophyll_mg_m3: float | None
    current_speed_ms: float | None
    current_direction_deg: float | None
    hab_detected: bool | None
    provenance: Provenance


class PFZData(TypedDict, total=False):
    """Potential Fishing Zone information."""
    pfz_id: str
    lat: float
    lon: float
    validity_start: str
    validity_end: str
    species_advisory: str | None
    source: str
    provenance: Provenance


class GeofenceResult(TypedDict, total=False):
    """Result of checking a route segment against a restricted area."""
    zone_name: str
    zone_type: str  # "MPA", "EEZ", "restricted"
    intersects: bool
    waypoint_indices: list[int]
    is_critical: bool


class HazardFlag(TypedDict):
    """A single hazard identified by the Risk Engine."""
    hazard_type: str  # "WAVE_HEIGHT_EXCEEDED", "WIND_SPEED_EXCEEDED", etc.
    phase: str  # "outbound", "fishing", "return"
    waypoint_index: int
    observed_value: float
    threshold_value: float
    severity: str  # "WARNING", "SEVERE"
    provenance: Provenance


class RiskEvidence(TypedDict, total=False):
    """Complete structured output from the deterministic Risk Engine."""
    advisory_category: str  # "FAVORABLE", "ELEVATED_RISK_IDENTIFIED", etc.
    risk_level: str  # "LOW", "MODERATE", "HIGH", "SEVERE", "UNKNOWN"
    hazard_flags: list[HazardFlag]
    confidence: float | None
    evaluated_at: str  # ISO 8601 UTC


class Advisory(TypedDict, total=False):
    """The final human-readable output synthesized by the Planner."""
    advisory_category: str
    recommendation_text: str
    reason: str
    affected_phase: str
    affected_time: str
    affected_location: str
    vessel_context: str
    evidence_summary: str
    uncertainty_notes: str
    disclaimer: str
    language: str


class AgentExecution(TypedDict, total=False):
    """Tracking record for what a single agent did during a trip assessment.

    Reference: 07_DATA_MODEL.md, Section 2.13
    Critical Rule: Do NOT persist internal LLM chain-of-thought.
    """
    id: str
    trip_id: str
    agent_name: str  # "planner", "geo", "weather", "marine", "risk"
    status: str  # "running", "completed", "failed"
    started_at: str
    completed_at: str | None
    input_summary: dict[str, Any]
    output_data: dict[str, Any]
    data_sources: list[str]
    confidence: float | None
    error: str | None


# ---------------------------------------------------------------------------
# The main LangGraph state object
# ---------------------------------------------------------------------------

class OrcaState(TypedDict, total=False):
    """LangGraph Shared State — the single data object passed between all nodes.

    Reference: 07_DATA_MODEL.md, Section 3

    State Ownership:
        conversation_history   — Planner writes/reads
        trip_context           — Planner writes → all read
        vessel_profile         — Planner writes → Geo, Risk read
        trajectory             — Geo writes → Marine, Weather, Risk read
        marine_observations    — Marine writes → Risk reads
        weather_observations   — Weather writes → Risk reads
        spatial_constraints    — Geo writes → Risk reads
        pfz_data               — Marine writes → Geo, Planner read
        geofence_results       — Geo writes → Risk reads
        risk_evidence          — Risk writes → Planner reads
        advisory               — Planner writes → Frontend reads
        workflow_status        — All nodes update
        errors                 — Any node writes
        provenance_registry    — Adapters write → all read
        agent_executions       — Each node writes its own record
    """

    # --- Conversation ---
    conversation_history: list[dict[str, str]]

    # --- Trip & Vessel ---
    trip_context: TripContext
    vessel_profile: VesselProfile

    # --- Geospatial ---
    trajectory: list[Waypoint]
    geofence_results: list[GeofenceResult]
    spatial_constraints: list[dict[str, Any]]

    # --- Environmental ---
    weather_observations: list[WeatherObservation]
    marine_observations: list[MarineObservation]
    pfz_data: list[PFZData]

    # --- Risk & Advisory ---
    risk_evidence: RiskEvidence
    advisory: Advisory

    # --- Workflow Control ---
    workflow_status: str  # "RECEIVED", "VALIDATED", "TRAJECTORY_READY", etc.
    errors: list[dict[str, Any]]
    provenance_registry: list[Provenance]

    # --- Agent Execution Tracking ---
    agent_executions: list[AgentExecution]
""", "Description": "OrcaState TypedDict matching 07_DATA_MODEL.md Section 3 exactly, including the new AgentExecution tracking entity."
