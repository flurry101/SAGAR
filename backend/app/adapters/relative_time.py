"""
relative_time.py
================
Resolve rolling fallback timestamps so static JSON never goes stale.

Fallback files store hour offsets from the current UTC hour instead of
fixed calendar dates. Adapters convert those offsets at read time.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


def utc_hour_floor(now: Optional[datetime] = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
    return now.replace(minute=0, second=0, microsecond=0)


def iso_from_hour_offset(offset_hours: float, now: Optional[datetime] = None) -> str:
    dt = utc_hour_floor(now) + timedelta(hours=float(offset_hours))
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_record_time(record: Dict[str, Any], now: Optional[datetime] = None) -> Optional[str]:
    """Return an ISO UTC time for a forecast record (hour_offset preferred)."""
    if record.get("hour_offset") is not None:
        return iso_from_hour_offset(record["hour_offset"], now=now)
    return record.get("time")


def resolve_validity_window(
    props: Dict[str, Any], now: Optional[datetime] = None
) -> Dict[str, Optional[str]]:
    """
    Resolve valid_from / valid_until from offset hours when present.
    Absolute ISO strings are kept as a backward-compatible fallback.
    """
    valid_from = props.get("valid_from")
    valid_until = props.get("valid_until")
    if props.get("valid_from_offset_hours") is not None:
        valid_from = iso_from_hour_offset(props["valid_from_offset_hours"], now=now)
    if props.get("valid_until_offset_hours") is not None:
        valid_until = iso_from_hour_offset(props["valid_until_offset_hours"], now=now)
    return {"valid_from": valid_from, "valid_until": valid_until}
