# attr: m1
# [trip repository for trip records persistence]
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def get_trip_by_id(trip_id: str) -> Optional[Dict[str, Any]]:
    # [retrieve trip record by trip_id from supabase]
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = client.table("trips").select("*").eq("id", trip_id).limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception as e:
        logger.warning(f"failed to fetch trip {trip_id} from supabase: {e}")

    return None


def save_trip(trip_data: Dict[str, Any]) -> Dict[str, Any]:
    # [persist trip record to supabase]
    client = get_supabase_client()
    record = dict(trip_data)
    if "id" not in record:
        record["id"] = str(uuid.uuid4())

    if client:
        try:
            response = client.table("trips").insert(record).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            logger.warning(f"failed to save trip to supabase: {e}")

    return record
# attr: m1

