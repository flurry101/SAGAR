"""
Visualization Node — Structured Map Layer Specification

Generates a JSON visualization specification for the frontend.
Does NOT produce actual UI code — only structured layer data.

Dynamically determines which layers are useful based on available evidence.

Reference: SIH26176 — Maps, charts, geospatial visualizations
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def visualization_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate structured visualization specification based on available data.

    Reads: trajectory, pfz_data, weather_observations, geofence_results,
           route_candidates, risk_evidence, ocean_analysis, alerts

    Writes: state["visualization_spec"]
    """
    layers: List[Dict[str, Any]] = []
    center = None
    bounds = None

    # --- Trajectory Layer ---
    trajectory = state.get("trajectory", {})
    waypoints = trajectory.get("waypoints", [])
    if waypoints:
        coords = [{"lat": wp.get("lat"), "lon": wp.get("lon")} for wp in waypoints]
        layers.append({
            "type": "route",
            "name": "Vessel Trajectory",
            "coordinates": coords,
            "style": {"color": "#2196F3", "weight": 3},
        })
        # Set center to midpoint of trajectory
        mid_idx = len(coords) // 2
        center = coords[mid_idx] if coords else None

    # --- PFZ Layer ---
    pfz_data = state.get("pfz_data", {})
    pfz_list = pfz_data.get("pfzs", []) if isinstance(pfz_data, dict) else []
    if pfz_list:
        pfz_points = []
        for pfz in pfz_list:
            pfz_points.append({
                "lat": pfz.get("lat"),
                "lon": pfz.get("lon"),
                "label": pfz.get("species_advisory", "PFZ"),
                "validity": pfz.get("validity_end"),
            })
        layers.append({
            "type": "pfz",
            "name": "Potential Fishing Zones",
            "points": pfz_points,
            "style": {"color": "#4CAF50", "icon": "fish"},
        })

    # --- Weather Hazard Layer ---
    hazard_alerts = state.get("hazard_alerts", {})
    hazard_list = []
    if isinstance(hazard_alerts, dict):
        hazard_list = hazard_alerts.get("hazards", [])
    elif isinstance(hazard_alerts, list):
        hazard_list = hazard_alerts

    if hazard_list:
        hazard_points = []
        for alert in hazard_list:
            if isinstance(alert, dict):
                hazard_points.append({
                    "lat": alert.get("lat"),
                    "lon": alert.get("lon"),
                    "type": alert.get("hazard_type", alert.get("type", "unknown")),
                    "severity": alert.get("severity", "unknown"),
                    "description": alert.get("description", ""),
                })
        if hazard_points:
            layers.append({
                "type": "hazard",
                "name": "Weather Hazards",
                "points": hazard_points,
                "style": {"color": "#F44336", "icon": "warning"},
            })

    # --- Geofence Layer ---
    geofence_results = state.get("geofence_results", [])
    if geofence_results:
        geofence_markers = []
        for violation in geofence_results:
            wp = violation.get("waypoint", {})
            geofence_markers.append({
                "lat": wp.get("lat") if isinstance(wp, dict) else getattr(wp, "lat", None),
                "lon": wp.get("lon") if isinstance(wp, dict) else getattr(wp, "lon", None),
                "zone_name": violation.get("zone_name"),
                "restriction_type": violation.get("restriction_type"),
            })
        layers.append({
            "type": "geofence",
            "name": "Restricted Zones",
            "markers": geofence_markers,
            "style": {"color": "#FF9800", "icon": "restricted"},
        })

    # --- Risk Overlay ---
    risk_evidence = state.get("risk_evidence", {})
    overall_risk = state.get("overall_risk_level", "UNKNOWN")
    if risk_evidence:
        risk_color = {
            "SAFE": "#4CAF50",
            "MODERATE": "#FF9800",
            "HIGH": "#F44336",
            "SEVERE": "#B71C1C",
            "UNKNOWN": "#9E9E9E",
        }.get(overall_risk, "#9E9E9E")

        layers.append({
            "type": "risk_indicator",
            "name": "Risk Assessment",
            "level": overall_risk,
            "style": {"color": risk_color},
            "summary": risk_evidence.get("summary", ""),
        })

    # --- Bounds from spatial constraints ---
    spatial_constraints = state.get("spatial_constraints", [])
    for sc in spatial_constraints:
        if sc.get("type") == "bbox":
            bounds = sc.get("coordinates")
            break

    spec = {
        "layers": layers,
        "center": center,
        "bounds": bounds,
        "recommended_zoom": 8 if layers else None,
    }

    updates = {"visualization_spec": spec}
    updates.setdefault("agent_executions", []).append({
        "agent_name": "visualization",
        "status": "completed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": ["trajectory", "pfz_data", "geofence_results", "risk_evidence"],
        "output_summary": f"Generated visualization with {len(layers)} layer(s).",
    })

    return updates
