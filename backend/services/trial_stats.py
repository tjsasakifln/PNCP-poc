"""STORY-266 AC5-AC6: Trial usage statistics collection.

Provides TrialUsageStats model and get_trial_usage_stats() function
for personalized trial reminder emails.
"""

import logging
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)


class TrialUsageStats(BaseModel):
    """AC6: Pydantic model for trial usage statistics.

    Reusable by email templates and API endpoints.
    """
    searches_count: int = 0
    opportunities_found: int = 0
    total_value_estimated: float = 0.0
    pipeline_items_count: int = 0
    sectors_searched: list[str] = []


def get_trial_usage_stats(user_id: str) -> TrialUsageStats:
    """AC5: Collect trial usage stats for a user.

    Queries:
    - monthly_quota: searches count
    - search_sessions: opportunities found + total value + sectors
    - user_pipeline: pipeline items count

    Returns:
        TrialUsageStats with all fields populated (zeros if no data).
    """
    from supabase_client import get_supabase

    stats = TrialUsageStats()

    try:
        sb = get_supabase()

        # Searches count from monthly_quota
        try:
            from quota import get_monthly_quota_used
            stats.searches_count = get_monthly_quota_used(user_id)
        except Exception as e:
            logger.debug(f"Could not fetch quota for {user_id[:8]}***: {e}")

        # Opportunities and value from search_sessions
        try:
            sessions_result = (
                sb.table("search_sessions")
                .select("total_filtered, valor_total, sectors")
                .eq("user_id", user_id)
                .execute()
            )
            if sessions_result.data:
                total_opps = 0
                total_val = 0.0
                sectors_set: set[str] = set()
                for session in sessions_result.data:
                    total_opps += session.get("total_filtered") or 0
                    total_val += session.get("valor_total") or 0.0
                    session_sectors = session.get("sectors") or []
                    if isinstance(session_sectors, list):
                        sectors_set.update(session_sectors)
                stats.opportunities_found = total_opps
                stats.total_value_estimated = total_val
                stats.sectors_searched = sorted(sectors_set)
        except Exception as e:
            logger.debug(f"Could not fetch sessions for {user_id[:8]}***: {e}")

        # Pipeline items count
        try:
            pipeline_result = (
                sb.table("user_pipeline")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            stats.pipeline_items_count = pipeline_result.count or 0
        except Exception as e:
            logger.debug(f"Could not fetch pipeline for {user_id[:8]}***: {e}")

    except Exception as e:
        logger.error(f"Error collecting trial stats for {user_id[:8]}***: {e}")

    return stats
