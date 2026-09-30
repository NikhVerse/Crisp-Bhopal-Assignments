import logging
from datetime import datetime
from typing import Any, Dict

# Set up logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AI-Assistant")

def format_unix_time(timestamp: int, timezone_offset: int = 0) -> str:
    """
    Converts a unix timestamp to a standard readable string (e.g. 06:30 AM).
    Includes the timezone offset if provided.
    """
    try:
        utc_time = datetime.utcfromtimestamp(timestamp + timezone_offset)
        return utc_time.strftime("%I:%M %p")
    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp}: {e}")
        return "N/A"

def parse_date_string(date_str: str) -> datetime:
    """
    Parses an ISO format date string into a datetime object.
    Handles 'Z' or timezone offset.
    """
    cleaned = date_str.replace("Z", "")
    if "+" in cleaned:
        cleaned = cleaned.split("+")[0]
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError as e:
        logger.error(f"Error parsing date string {date_str}: {e}")
        raise ValueError(f"Invalid date format: {date_str}. Must be ISO 8601 (e.g. YYYY-MM-DDTHH:MM:SS)")
