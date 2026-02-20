"""Analytics event tracking module (GTM-RESILIENCE-B05 AC1).

Provides fire-and-forget event tracking with:
- Mixpanel SDK integration (when MIXPANEL_TOKEN is configured)
- Logger.debug() fallback (development/no-token mode)
- Never raises exceptions (silent failure)
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_mixpanel_client = None
_mixpanel_initialized = False


def _get_mixpanel():
    """Lazy-init Mixpanel client. Returns None if unavailable."""
    global _mixpanel_client, _mixpanel_initialized
    if _mixpanel_initialized:
        return _mixpanel_client
    _mixpanel_initialized = True

    token = os.getenv("MIXPANEL_TOKEN", "").strip()
    if not token:
        logger.debug("MIXPANEL_TOKEN not configured — analytics events will be logged only")
        return None

    try:
        from mixpanel import Mixpanel
        _mixpanel_client = Mixpanel(token)
        logger.info("Mixpanel analytics initialized")
        return _mixpanel_client
    except ImportError:
        logger.debug("mixpanel-python not installed — analytics events will be logged only")
        return None
    except Exception as e:
        logger.debug(f"Mixpanel init failed: {e}")
        return None


def track_event(event_name: str, properties: dict[str, Any] | None = None) -> None:
    """Track an analytics event. Fire-and-forget, never raises.

    Args:
        event_name: Event name (e.g., "cache_operation", "search_completed")
        properties: Event properties dict
    """
    try:
        props = dict(properties) if properties else {}
        mp = _get_mixpanel()
        if mp:
            distinct_id = str(props.pop("user_id", "system"))
            mp.track(distinct_id, event_name, props)
        else:
            logger.debug(f"analytics_event: {event_name} {props}")
    except Exception:
        pass  # Fire-and-forget — never fail


def reset_for_testing() -> None:
    """Reset module state for test isolation."""
    global _mixpanel_client, _mixpanel_initialized
    _mixpanel_client = None
    _mixpanel_initialized = False
