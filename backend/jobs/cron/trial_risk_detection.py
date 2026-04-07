"""Zero-churn P1 S7.2: At-risk trial detection cron.

Daily job that identifies trial users who are at risk of not converting:
- critical: 0 searches after 2+ days (trigger activation nudge)
- at_risk: 1-3 searches AND value < R$100k after 5+ days
- healthy: 3+ searches AND value > R$100k

Logs results and can trigger intervention emails.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from jobs.cron.canary import _is_cb_or_connection_error

logger = logging.getLogger(__name__)

TRIAL_RISK_HOUR_UTC = 12  # 09:00 BRT


def _next_utc_hour(target_hour: int) -> float:
    now = datetime.now(timezone.utc)
    next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    if now.hour >= target_hour:
        next_run += timedelta(days=1)
    return max(60.0, min((next_run - now).total_seconds(), 86400.0))


async def detect_at_risk_trials() -> dict:
    """Identify and categorize at-risk trial users.

    Returns:
        dict with counts: {"critical": N, "at_risk": M, "healthy": H, "errors": E}
    """
    try:
        from supabase_client import get_supabase, sb_execute
        from services.trial_stats import get_trial_usage_stats
        from analytics_events import track_event

        sb = get_supabase()
        now = datetime.now(timezone.utc)

        # Find all active trial users created 2+ days ago
        cutoff = (now - timedelta(days=2)).isoformat()

        users_result = await sb_execute(
            sb.table("profiles")
            .select("id, email, created_at, plan_type")
            .eq("plan_type", "free_trial")
            .lt("created_at", cutoff)
            .limit(200)
        )

        if not users_result.data:
            logger.info("at_risk_detection: no eligible trial users found")
            return {"critical": 0, "at_risk": 0, "healthy": 0, "total": 0, "errors": 0}

        critical = 0
        at_risk = 0
        healthy = 0
        errors = 0

        for user in users_result.data:
            try:
                user_id = user["id"]
                created_at = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
                trial_day = (now - created_at).days

                stats = get_trial_usage_stats(user_id)
                stats_dict = stats.model_dump()
                searches = stats_dict.get("searches_count", 0)
                value = stats_dict.get("total_value_estimated", 0.0)

                from services.trial_risk import categorize_trial_risk
                category = categorize_trial_risk(searches, value, trial_day)
                if category == "critical":
                    critical += 1
                elif category == "at_risk":
                    at_risk += 1
                else:
                    healthy += 1

                track_event("trial_risk_assessed", {
                    "user_id": user_id,
                    "category": category,
                    "trial_day": trial_day,
                    "searches": searches,
                    "value": value,
                })

            except Exception as e:
                errors += 1
                logger.debug(f"at_risk_detection: error processing user: {e}")

        total = critical + at_risk + healthy
        logger.info(
            f"at_risk_detection: total={total}, critical={critical}, "
            f"at_risk={at_risk}, healthy={healthy}, errors={errors}"
        )

        return {
            "critical": critical,
            "at_risk": at_risk,
            "healthy": healthy,
            "total": total,
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"at_risk_detection failed: {e}", exc_info=True)
        return {"critical": 0, "at_risk": 0, "healthy": 0, "total": 0, "errors": 1, "error": str(e)}


async def _trial_risk_loop() -> None:
    """Daily loop: run at TRIAL_RISK_HOUR_UTC."""
    await asyncio.sleep(_next_utc_hour(TRIAL_RISK_HOUR_UTC))
    while True:
        try:
            result = await detect_at_risk_trials()
            logger.info("Zero-churn P1 trial risk cycle: %s", result)
            await asyncio.sleep(24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("Trial risk detection task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("Trial risk detection skipped (Supabase unavailable): %s", e)
            else:
                logger.error("Trial risk detection loop error: %s", e, exc_info=True)
            await asyncio.sleep(600)


async def start_trial_risk_task() -> asyncio.Task:
    task = asyncio.create_task(_trial_risk_loop(), name="trial_risk_detection")
    logger.info("Zero-churn P1: Trial risk detection task started (daily at %02d:00 UTC)", TRIAL_RISK_HOUR_UTC)
    return task
