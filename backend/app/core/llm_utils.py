import json
import logging
from typing import Any, Dict
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


def normalize_content(resp_content: Any) -> str:
    """Normalize Gemini content which might be a string or a list of blocks."""
    if isinstance(resp_content, list):
        return " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in resp_content
        )
    return str(resp_content)


def extract_json(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from LLM response, stripping markdown fences."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
        
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}. Text: {text}")
        raise ValueError(f"Invalid JSON structure returned by LLM: {e}")


def parse_natural_time(text: str, default_timezone=None) -> str:
    """Safely parse natural language time to ISO 8601 string.
    
    Handles relative terms like 'tomorrow', 'today', 'tonight' that
    dateutil.parser cannot resolve on its own.
    """
    import re
    from datetime import timezone, timedelta

    ist = default_timezone or timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)

    # --- Pre-process relative date words ---
    normalized = text.strip().lower()
    
    # Map relative words to concrete dates
    date_replacements = {
        "tomorrow": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
        "day after tomorrow": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
        "today": now.strftime("%Y-%m-%d"),
        "tonight": now.strftime("%Y-%m-%d"),
        "yesterday": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
    }

    processed = normalized
    for word, date_str in date_replacements.items():
        if word in processed:
            processed = processed.replace(word, date_str)
            break

    try:
        dt = date_parser.parse(processed)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ist)
        return dt.isoformat()
    except Exception:
        pass

    # --- Fallback: extract hour + AM/PM manually ---
    time_match = re.search(r'(\d{1,2})\s*(am|pm|AM|PM)', text, re.IGNORECASE)
    if time_match:
        hour = int(time_match.group(1))
        ampm = time_match.group(2).upper()
        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0

        base_date = now.date()
        if "tomorrow" in normalized:
            base_date = (now + timedelta(days=1)).date()

        dt = datetime(base_date.year, base_date.month, base_date.day, hour, 0, 0, tzinfo=ist)
        return dt.isoformat()

    logger.warning(f"Failed to parse time '{text}', returning raw text")
    return text

