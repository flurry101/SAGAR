"""
Reporting Node — Structured Evidence-Backed Report Generation

Aggregates all available evidence into a structured JSON report.
Does NOT use an LLM for report generation — produces deterministic,
evidence-backed structured data.

Reference: SIH26176 — Reporting, explainability, evidence
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def reporting_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a structured evidence-backed report.

    Reads: trip_context, trajectory, weather_observations, marine_observations,
           pfz_data, risk_evidence, ocean_analysis, route_candidates,
           geofence_results, alerts, agent_executions

    Writes: state["report"]
    """
    trip = state.get("trip_context", {})
    risk = state.get("risk_evidence", {})
    ocean = state.get("ocean_analysis", {})
    routes = state.get("route_candidates", [])
    weather_obs = state.get("weather_observations", [])
    marine_obs = state.get("marine_observations", [])
    geofence = state.get("geofence_results", [])
    alerts = state.get("alerts", [])
    overall_risk = state.get("overall_risk_level", "UNKNOWN")

    # --- Build summary ---
    summary_parts = []
    summary_parts.append(f"Trip from {trip.get('origin', 'unknown')}.")

    if overall_risk and overall_risk != "UNKNOWN":
        summary_parts.append(f"Overall risk: {overall_risk}.")
    if ocean.get("fishing_opportunity"):
        summary_parts.append(f"Fishing opportunity: {ocean['fishing_opportunity']}.")
    if geofence:
        summary_parts.append(f"Geofence violations: {len(geofence)}.")

    summary = " ".join(summary_parts)

    # --- Build recommendation ---
    if overall_risk in ("SEVERE", "HIGH"):
        recommendation = (
            "Trip is NOT recommended. Significant safety risks detected. "
            "Please consult official INCOIS/IMD advisories."
        )
    elif overall_risk == "MODERATE":
        recommendation = (
            "Trip may proceed with caution. Monitor weather conditions closely."
        )
    elif overall_risk == "UNKNOWN":
        recommendation = (
            "Insufficient data to make a safety assessment. "
            "Do not assume it is safe."
        )
    else:
        recommendation = "Conditions appear favorable. Exercise standard caution."

    # --- Collect evidence ---
    evidence: List[Dict[str, Any]] = []

    for obs in weather_obs:
        w = obs.get("weather", {})
        evidence.append({
            "category": "weather",
            "value": w.get("wave_height_m"),
            "unit": "m",
            "source": "Open-Meteo",
            "agent": "weather",
        })

    for obs in marine_obs:
        m = obs.get("marine", {})
        if m.get("sst_celsius") is not None:
            evidence.append({
                "category": "marine_sst",
                "value": m["sst_celsius"],
                "unit": "°C",
                "source": "SST Adapter",
                "agent": "marine",
            })
        if m.get("chlorophyll_mg_m3") is not None:
            evidence.append({
                "category": "marine_chlorophyll",
                "value": m["chlorophyll_mg_m3"],
                "unit": "mg/m³",
                "source": "Marine Adapter",
                "agent": "marine",
            })

    # --- Collect sources ---
    sources = set()
    for exec_record in state.get("agent_executions", []):
        for src in exec_record.get("data_sources", []):
            sources.add(src)

    # --- Uncertainty ---
    uncertainty = []
    if not weather_obs:
        uncertainty.append("Weather data unavailable — safety assessment may be incomplete.")
    if not marine_obs:
        uncertainty.append("Marine data unavailable — fishing opportunity unknown.")
    if overall_risk == "UNKNOWN":
        uncertainty.append("Insufficient data for definitive risk classification.")

    # --- Route info ---
    selected_route = next((r for r in routes if r.get("selected")), None)
    route_info = None
    if selected_route:
        route_info = {
            "route_id": selected_route.get("route_id"),
            "safety_score": selected_route.get("safety_score"),
            "geofence_clear": selected_route.get("geofence_clear"),
            "reason": selected_route.get("reason"),
        }

    report = {
        "summary": summary,
        "recommendation": recommendation,
        "risk": {
            "level": overall_risk,
            "category": risk.get("advisory_category"),
            "summary": risk.get("summary"),
        } if risk else None,
        "route": route_info,
        "alerts": alerts,
        "evidence": evidence,
        "sources": sorted(sources),
        "uncertainty": uncertainty,
        "limitations": [
            "ORCA provides decision support only. Follow official alerts from INCOIS and IMD.",
        ],
    }

    updates = {"report": report}
    updates.setdefault("agent_executions", []).append({
        "agent_name": "reporting",
        "status": "completed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": list(sources),
        "output_summary": f"Generated report. Risk: {overall_risk}. Evidence items: {len(evidence)}.",
    })

    return updates
