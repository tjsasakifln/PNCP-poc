"""Date parsing utility for multi-source procurement data.

Provides bidirectional conversion between DD/MM/AAAA (PCP format)
and YYYY-MM-DD (ISO/PNCP format) with validation.

GTM-FIX-011 AC7.
"""

import logging
import re
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Pre-compiled patterns for performance
_ISO_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BR_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def br_to_iso(date_str: str) -> Optional[str]:
    """Convert DD/MM/AAAA → YYYY-MM-DD.

    Args:
        date_str: Date in DD/MM/AAAA format.

    Returns:
        Date in YYYY-MM-DD format, or None if invalid.
    """
    if not date_str or not _BR_PATTERN.match(date_str):
        logger.warning(f"[DateParser] Invalid BR date format: {date_str!r}")
        return None
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        logger.warning(f"[DateParser] Invalid BR date value: {date_str!r}")
        return None


def iso_to_br(date_str: str) -> Optional[str]:
    """Convert YYYY-MM-DD → DD/MM/AAAA.

    Args:
        date_str: Date in YYYY-MM-DD format.

    Returns:
        Date in DD/MM/AAAA format, or None if invalid.
    """
    if not date_str or not _ISO_PATTERN.match(date_str):
        logger.warning(f"[DateParser] Invalid ISO date format: {date_str!r}")
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        logger.warning(f"[DateParser] Invalid ISO date value: {date_str!r}")
        return None


def parse_date_flexible(date_str: str) -> Optional[datetime]:
    """Parse a date string in either BR or ISO format.

    Args:
        date_str: Date in DD/MM/AAAA or YYYY-MM-DD format.

    Returns:
        datetime object, or None if invalid.
    """
    if not date_str:
        return None

    if _BR_PATTERN.match(date_str):
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            return None

    if _ISO_PATTERN.match(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

    logger.warning(f"[DateParser] Unrecognized date format: {date_str!r}")
    return None
