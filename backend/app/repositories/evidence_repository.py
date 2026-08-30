"""
Evidence Repository — Centralized Evidence Persistence

Persists the evidence registry items from the ORCA pipeline.

Reference: SIH26176 — Evidence tracking, provenance
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _get_client():
    """Get the Supabase client, or None if not configured."""
    try:
        from app.core.supabase import get_supabase_client
        return get_supabase_client()
    except Exception:
        return None


def persist_evidence_registry(
    evidence_items: List[Dict[str, Any]],
    assessment_id: str,
) -> Dict[str, Any]:
    """Persist evidence registry items to Supabase.

    Args:
        evidence_items: List of EvidenceItem dicts.
        assessment_id: The assessment ID to associate with.

    Returns:
        {"status": "success"|"failed"|"supabase_not_configured", "count": int}
    """
    client = _get_client()
    if not client:
        return {"status": "supabase_not_configured", "count": 0}

    if not evidence_items:
        return {"status": "success", "count": 0}

    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        rows = []
        for item in evidence_items:
            rows.append({
                "assessment_id": assessment_id,
                "evidence_id": item.get("evidence_id"),
                "category": item.get("category"),
                "value": str(item.get("value")),
                "unit": item.get("unit"),
                "source": item.get("source"),
                "agent": item.get("agent"),
                "lat": item.get("lat"),
                "lon": item.get("lon"),
                "confidence": item.get("confidence"),
                "timestamp": item.get("timestamp"),
                "created_at": now_iso,
            })

        client.table("evidence_registry").insert(rows).execute()
        return {"status": "success", "count": len(rows)}

    except Exception as e:
        logger.warning(f"Evidence registry persistence failed: {e}")
        return {"status": "failed", "count": 0, "error": str(e)}
