"""
Ocean Analytics Node — Heterogeneous Data Correlation

Correlates SST, chlorophyll, PFZ, and marine observations to produce
a structured Fishing Opportunity analysis. Uses deterministic scoring,
not LLM reasoning, for numerical calculations.

Reference: SIH26176 — Ocean analytics, heterogeneous data correlation
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def ocean_analytics_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Correlate marine observations to produce fishing opportunity analysis.

    Reads:
        state["marine_observations"]
        state["pfz_data"]
        state["weather_observations"]

    Writes:
        state["ocean_analysis"]
    """
    marine_obs = state.get("marine_observations", [])
    pfz_data = state.get("pfz_data", {})
    weather_obs = state.get("weather_observations", [])

    # --- SST Analysis (deterministic) ---
    sst_values = [
        obs.get("marine", {}).get("sst_celsius")
        for obs in marine_obs
        if obs.get("marine", {}).get("sst_celsius") is not None
    ]
    avg_sst = sum(sst_values) / len(sst_values) if sst_values else None

    if avg_sst is None:
        sst_status = "unknown"
    elif 25.0 <= avg_sst <= 30.0:
        sst_status = "favourable"
    elif 22.0 <= avg_sst < 25.0 or 30.0 < avg_sst <= 32.0:
        sst_status = "moderate"
    else:
        sst_status = "unfavourable"

    # --- Chlorophyll Analysis (deterministic) ---
    chl_values = [
        obs.get("marine", {}).get("chlorophyll_mg_m3")
        for obs in marine_obs
        if obs.get("marine", {}).get("chlorophyll_mg_m3") is not None
    ]
    avg_chl = sum(chl_values) / len(chl_values) if chl_values else None

    if avg_chl is None:
        chl_status = "unknown"
    elif avg_chl >= 1.0:
        chl_status = "high"
    elif avg_chl >= 0.3:
        chl_status = "moderate"
    else:
        chl_status = "low"

    # --- PFZ Alignment ---
    pfz_list = pfz_data.get("pfzs", []) if isinstance(pfz_data, dict) else []
    pfz_alignment = len(pfz_list) > 0

    # --- Composite Productivity Score (0.0 to 1.0) ---
    score_components = []

    if sst_status == "favourable":
        score_components.append(0.9)
    elif sst_status == "moderate":
        score_components.append(0.6)
    elif sst_status == "unfavourable":
        score_components.append(0.2)

    if chl_status == "high":
        score_components.append(0.95)
    elif chl_status == "moderate":
        score_components.append(0.6)
    elif chl_status == "low":
        score_components.append(0.2)

    if pfz_alignment:
        score_components.append(0.9)
    else:
        score_components.append(0.3)

    productivity_score = (
        round(sum(score_components) / len(score_components), 2)
        if score_components else None
    )

    # --- Fishing Opportunity Classification ---
    if productivity_score is None:
        fishing_opportunity = "unknown"
    elif productivity_score >= 0.7:
        fishing_opportunity = "good"
    elif productivity_score >= 0.4:
        fishing_opportunity = "moderate"
    else:
        fishing_opportunity = "poor"

    # --- Confidence ---
    data_points = len(sst_values) + len(chl_values) + len(pfz_list)
    confidence = min(round(data_points / 10.0, 2), 1.0) if data_points > 0 else None

    # --- Build summary ---
    parts = []
    if avg_sst is not None:
        parts.append(f"SST: {avg_sst:.1f}°C ({sst_status})")
    if avg_chl is not None:
        parts.append(f"Chlorophyll: {avg_chl:.2f} mg/m³ ({chl_status})")
    parts.append(f"PFZ available: {'Yes' if pfz_alignment else 'No'}")
    parts.append(f"Fishing opportunity: {fishing_opportunity}")
    summary = ". ".join(parts) + "."

    analysis = {
        "productivity_score": productivity_score,
        "sst_status": sst_status,
        "chlorophyll_status": chl_status,
        "pfz_alignment": pfz_alignment,
        "fishing_opportunity": fishing_opportunity,
        "confidence": confidence,
        "evidence_ids": [],
        "summary": summary,
    }

    # --- Populate evidence registry ---
    evidence_items = []
    now_iso = datetime.now(timezone.utc).isoformat()
    if avg_sst is not None:
        evidence_items.append({
            "evidence_id": "ocean_sst_avg",
            "category": "marine",
            "value": round(avg_sst, 2),
            "unit": "°C",
            "source": "SST Adapter",
            "timestamp": now_iso,
            "confidence": confidence,
            "agent": "ocean_analytics",
        })
    if avg_chl is not None:
        evidence_items.append({
            "evidence_id": "ocean_chlorophyll_avg",
            "category": "marine",
            "value": round(avg_chl, 3),
            "unit": "mg/m³",
            "source": "Marine Adapter",
            "timestamp": now_iso,
            "confidence": confidence,
            "agent": "ocean_analytics",
        })
    if productivity_score is not None:
        evidence_items.append({
            "evidence_id": "ocean_productivity",
            "category": "analysis",
            "value": productivity_score,
            "unit": "score",
            "source": "Ocean Analytics",
            "timestamp": now_iso,
            "confidence": confidence,
            "agent": "ocean_analytics",
        })

    updates = {"ocean_analysis": analysis}
    if evidence_items:
        updates["evidence_registry"] = evidence_items

    updates.setdefault("agent_executions", []).append({
        "agent_name": "ocean_analytics",
        "status": "completed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": ["marine_observations", "pfz_data"],
        "output_summary": summary,
        "evidence_count": len(evidence_items),
    })

    return updates

