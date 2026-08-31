# attr: m1
# [vessel repository for supabase and local persistence]
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def get_vessel_by_id(vessel_id: str) -> Optional[Dict[str, Any]]:
    # [retrieve vessel profile by vessel_id from supabase]
    client = get_supabase_client()
    if not client:
        logger.debug("supabase client not configured, returning none for vessel lookup")
        return None

    try:
        response = client.table("vessels").select("*").eq("id", vessel_id).limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception as e:
        logger.warning(f"failed to fetch vessel {vessel_id} from supabase: {e}")

    return None


def upsert_vessel(fisher_id: Optional[str], vessel_data: Dict[str, Any]) -> Dict[str, Any]:
    # [create or update vessel profile record in supabase]
    client = get_supabase_client()
    record = dict(vessel_data)
    if "vessel_id" in record and record["vessel_id"]:
        record["id"] = record.pop("vessel_id")
    elif "id" not in record:
        record["id"] = str(uuid.uuid4())

    if fisher_id:
        record["fisher_id"] = fisher_id

    if client:
        try:
            response = client.table("vessels").upsert(record).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            logger.warning(f"failed to upsert vessel to supabase: {e}")

    return record
# attr: m1

