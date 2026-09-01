"""
OrcaState — LangGraph Shared State Definition

This TypedDict defines the single data object passed between all LangGraph
nodes in the ORCA Trip Planner workflow.

Reference: 07_DATA_MODEL.md, Section 3 (LangGraph Shared State)

Architecture:
    LangGraph decides → Supabase remembers → LangChain Copilot explains
"""

from __future__ import annotations

import operator
from typing import Any, TypedDict, Annotated


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
    agent_name: str  # "planner", "geo", "weather", "marine", "risk", "supervisor"
    status: str  # "running", "completed", "failed"
    started_at: str
    completed_at: str | None
    input_summary: dict[str, Any]
    output_data: dict[str, Any]
    data_sources: list[str]
    confidence: float | None
    error: str | None


# ---------------------------------------------------------------------------
# Supervisor & Autonomous Planning Types
# ---------------------------------------------------------------------------

# Approved capability registry — Supervisor may ONLY select from these
APPROVED_CAPABILITIES = [
    "geo", "marine", "weather", "ocean_analytics", "route",
    "risk", "visualization", "reporting", "knowledge", "copilot",
]

SAFETY_CAPABILITIES = {"geo", "weather", "marine", "risk"}


class TaskPlan(TypedDict, total=False):
    """Structured task plan produced by the Supervisor.

    The Supervisor uses LLM structured output to generate this plan.
    The Safety Guard may add mandatory capabilities.
    The Dynamic Router uses required_capabilities to decide which nodes execute.
    """
    intent: str  # e.g. "safe_fishing_trip", "pfz_query", "knowledge_question"
    required_capabilities: list[str]  # subset of APPROVED_CAPABILITIES
    priority: str  # "safety", "information", "planning"
    requires_safety_assessment: bool
    requires_route: bool
    requires_visualization: bool
    requires_report: bool
    clarification_required: bool
    clarification_question: str | None
    reasoning_summary: str  # brief rationale for capability selection


class EvidenceItem(TypedDict, total=False):
    """A single piece of structured evidence from any agent/node."""
    evidence_id: str
    category: str  # "weather", "marine", "geofence", "risk", "route"
    value: Any
    unit: str | None
    source: str
    timestamp: str | None
    lat: float | None
    lon: float | None
    confidence: float | None
    agent: str  # which node produced this


class OceanAnalysis(TypedDict, total=False):
    """Output of the Ocean Analytics component."""
    productivity_score: float | None
    sst_status: str  # "favourable", "unfavourable", "unknown"
    chlorophyll_status: str  # "high", "moderate", "low", "unknown"
    pfz_alignment: bool | None
    fishing_opportunity: str  # "good", "moderate", "poor", "unknown"
    confidence: float | None
    evidence_ids: list[str]
    summary: str


class RouteCandidate(TypedDict, total=False):
    """A single candidate route from the Route Optimization component."""
    route_id: str
    waypoints: list[dict[str, Any]]
    total_distance_nm: float | None
    safety_score: float | None
    weather_risk_score: float | None
    geofence_clear: bool
    selected: bool
    reason: str


class Alert(TypedDict, total=False):
    """A proactive safety or environmental alert."""
    alert_type: str  # "HIGH_WAVES", "CYCLONE", "LIGHTNING", "RESTRICTED_ZONE", etc.
    severity: str  # "INFO", "WARNING", "SEVERE"
    message: str
    source: str
    timestamp: str | None
    lat: float | None
    lon: float | None
    evidence_ids: list[str]


class VisualizationSpec(TypedDict, total=False):
    """Structured visualization specification for the frontend."""
    layers: list[dict[str, Any]]
    center: dict[str, float] | None  # {"lat": ..., "lon": ...}
    bounds: list[float] | None  # [min_lon, min_lat, max_lon, max_lat]
    recommended_zoom: int | None


class Report(TypedDict, total=False):
    """Structured evidence-backed report."""
    summary: str
    recommendation: str
    risk: dict[str, Any] | None
    route: dict[str, Any] | None
    alerts: list[Alert]
    evidence: list[EvidenceItem]
    sources: list[str]
    uncertainty: list[str]
    limitations: list[str]


# ---------------------------------------------------------------------------
# The main LangGraph state object
# ---------------------------------------------------------------------------

class OrcaState(TypedDict, total=False):
    """LangGraph Shared State — the single data object passed between all nodes.

    Reference: 07_DATA_MODEL.md, Section 3

    State Ownership:
        conversation_history   — Planner writes/reads
        trip_context           — Planner/Supervisor writes → all read
        vessel_profile         — Planner/Supervisor writes → Geo, Risk read
        trajectory             — Geo writes → Marine, Weather, Risk read
        marine_observations    — Marine writes → Risk reads
        weather_observations   — Weather writes → Risk reads
        spatial_constraints    — Geo writes → Risk reads
        pfz_data               — Marine writes → Geo, Planner read
        geofence_results       — Geo writes → Risk reads
        risk_evidence          — Risk writes → Planner reads
        advisory               — Planner writes → Frontend reads
        task_plan              — Supervisor writes → Router reads
        evidence_registry      — All nodes append → Reporting reads
        visualization_spec     — Visualization writes → Frontend reads
        report                 — Reporting writes → Frontend reads
        ocean_analysis         — OceanAnalytics writes → Reporting reads
        route_candidates       — Route writes → Risk, Visualization read
        alerts                 — Weather/Geo writes → Reporting, Frontend reads
        workflow_status        — All nodes update
        errors                 — Any node writes
        provenance_registry    — Adapters write → all read
        agent_executions       — Each node writes its own record
    """

    # --- Conversation ---
    conversation_history: list[dict[str, str]]

    # --- Supervisor & Autonomous Planning ---
    task_plan: TaskPlan

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

    # --- Ocean Analytics ---
    ocean_analysis: OceanAnalysis

    # --- Route Optimization ---
    route_candidates: list[RouteCandidate]

    # --- Alerts ---
    alerts: Annotated[list[Alert], operator.add]

    # --- Risk & Advisory ---
    risk_evidence: RiskEvidence
    overall_risk_level: str  # "LOW", "MODERATE", "HIGH", "SEVERE", "UNKNOWN"
    advisory: Advisory

    # --- Evidence Registry ---
    evidence_registry: Annotated[list[EvidenceItem], operator.add]

    # --- Visualization & Reporting ---
    visualization_spec: VisualizationSpec
    report: Report

    # --- Workflow Control ---
    workflow_status: str  # "RECEIVED", "VALIDATED", "TRAJECTORY_READY", etc.
    persistence_status: str  # "success", "partial", "failed", "supabase_not_configured"
    errors: Annotated[list[dict[str, Any]], operator.add]
    provenance_registry: Annotated[list[Provenance], operator.add]

    # --- Agent Execution Tracking ---
    agent_executions: Annotated[list[AgentExecution], operator.add]

    # --- Language ---
    language: str  # ISO 639-1 code, e.g. "en", "hi", "ta"
    hazard_alerts: dict[str, Any]  # Raw hazard data from GDACS

