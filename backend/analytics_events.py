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


def track_funnel_event(
    event_name: str,
    user_id: str,
    properties: dict[str, Any] | None = None,
    variant: str | None = None,
) -> None:
    """Track a conversion funnel event with user cohort enrichment. Fire-and-forget."""
    try:
        props = dict(properties) if properties else {}
        props["user_id"] = user_id

        # Enrich with trial cohort properties
        try:
            from services.trial_stats import get_trial_usage_stats
            stats = get_trial_usage_stats(user_id)
            stats_dict = stats.model_dump()
            props["searches_count"] = stats_dict.get("searches_count", 0)
            props["opportunities_found"] = stats_dict.get("opportunities_found", 0)
            props["total_value"] = stats_dict.get("total_value_estimated", 0.0)
            props["pipeline_items"] = stats_dict.get("pipeline_items_count", 0)

            # Engagement tier
            value = stats_dict.get("total_value_estimated", 0.0)
            searches = stats_dict.get("searches_count", 0)
            if value > 100_000:
                props["engagement_tier"] = "high_value"
            elif searches > 0:
                props["engagement_tier"] = "active"
            else:
                props["engagement_tier"] = "dormant"
        except Exception:
            pass  # Enrichment is best-effort

        # Enrich with A/B experiment variants
        try:
            if variant is not None:
                props["ab_variant"] = variant
            from services.ab_testing import get_user_experiments
            experiment_variants = get_user_experiments(user_id)
            if experiment_variants:
                props["experiment_variants"] = experiment_variants
        except Exception:
            pass  # Enrichment is best-effort

        track_event(event_name, props)
    except Exception:
        pass  # Fire-and-forget


def reset_for_testing() -> None:
    """Reset module state for test isolation."""
    global _mixpanel_client, _mixpanel_initialized
    _mixpanel_client = None
    _mixpanel_initialized = False
