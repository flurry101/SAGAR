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
    """Safely parse natural language time to ISO 8601 string."""
    try:
        dt = date_parser.parse(text)
        if dt.tzinfo is None:
            # Default to IST (UTC+5:30) if no timezone is specified
            from datetime import timezone, timedelta
            ist = timezone(timedelta(hours=5, minutes=30))
            dt = dt.replace(tzinfo=default_timezone or ist)
        return dt.isoformat()
    except Exception as e:
        logger.warning(f"Failed to parse time '{text}': {e}")
        return text
