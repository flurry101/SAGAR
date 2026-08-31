# attr: m1
# [assessment read queries repository]
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def get_assessment_by_id(assessment_id: str) -> Optional[Dict[str, Any]]:
    # [retrieve full assessment record and related evidence tables by id]
    client = get_supabase_client()
    if not client:
        logger.debug("supabase client not configured")
        return None

    try:
        res = client.table("assessments").select("*").eq("assessment_id", assessment_id).limit(1).execute()
        if not res.data or len(res.data) == 0:
            return None

        assessment = res.data[0]

        # [fetch linked advisory]
        try:
            adv_res = client.table("advisories").select("*").eq("assessment_id", assessment_id).execute()
            assessment["advisories"] = adv_res.data or []
        except Exception as e:
            logger.debug(f"error querying advisories: {e}")
            assessment["advisories"] = []

        # [fetch linked risk evidence]
        try:
            risk_res = client.table("risk_evidence").select("*").eq("assessment_id", assessment_id).execute()
            assessment["risk_evidence"] = risk_res.data or []
        except Exception as e:
            logger.debug(f"error querying risk_evidence: {e}")
            assessment["risk_evidence"] = []

        # [fetch linked weather evidence]
        try:
            wea_res = client.table("weather_evidence").select("*").eq("assessment_id", assessment_id).execute()
            assessment["weather_evidence"] = wea_res.data or []
        except Exception as e:
            logger.debug(f"error querying weather_evidence: {e}")
            assessment["weather_evidence"] = []

        # [fetch linked marine evidence]
        try:
            mar_res = client.table("marine_evidence").select("*").eq("assessment_id", assessment_id).execute()
            assessment["marine_evidence"] = mar_res.data or []
        except Exception as e:
            logger.debug(f"error querying marine_evidence: {e}")
            assessment["marine_evidence"] = []

        # [fetch agent execution history]
        try:
            exec_res = client.table("agent_executions").select("*").eq("assessment_id", assessment_id).execute()
            assessment["agent_executions"] = exec_res.data or []
        except Exception as e:
            logger.debug(f"error querying agent_executions: {e}")
            assessment["agent_executions"] = []

        # [fetch reports]
        try:
            rep_res = client.table("reports").select("*").eq("assessment_id", assessment_id).execute()
            assessment["reports"] = rep_res.data or []
        except Exception as e:
            logger.debug(f"error querying reports: {e}")
            assessment["reports"] = []

        return assessment

    except Exception as e:
        logger.warning(f"failed to retrieve assessment {assessment_id}: {e}")
        return None
# attr: m1

