"""jobs.cron.new_bids_notifier — Daily detection of new bids for in-app notification.

STORY-445: New Bid Count Badge — runs once daily at 12:00 UTC (09:00 BRT) after
morning ingestion. For each active user with profile_context, queries pncp_raw_bids
and stores count in Redis key ``new_bids_count:{user_id}`` with 26h TTL.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from jobs.cron.canary import _is_cb_or_connection_error

logger = logging.getLogger(__name__)

NEW_BIDS_NOTIFIER_HOUR_UTC = 12   # 09:00 BRT
NEW_BIDS_REDIS_TTL = 26 * 3600    # 26h — survives until next run


def _next_utc_hour(target_hour: int) -> float:
    now = datetime.now(timezone.utc)
    next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    if now.hour >= target_hour:
        next_run += timedelta(days=1)
    return max(60.0, min((next_run - now).total_seconds(), 86400.0))


async def run_new_bids_notifier() -> dict:
    """Compute per-user new-bid counts and cache them in Redis.

    For each active profile (free_trial + smartlic_pro) that has a setor_id
    and UFs configured in profile_context, counts bids ingested in the last
    26 h and writes the count to ``new_bids_count:{user_id}`` in Redis.
    """
    try:
        from supabase_client import get_supabase, sb_execute
        from redis_pool import get_redis_pool

        redis = await get_redis_pool()
        sb = get_supabase()
        now = datetime.now(timezone.utc)
        since = (now - timedelta(hours=26)).isoformat()

        # Fetch active profiles that have profile_context set
        profiles_resp = await sb_execute(
            sb.table("profiles")
            .select("id, plan_type, profile_context")
            .in_("plan_type", ["free_trial", "smartlic_pro"])
            .not_.is_("profile_context", "null")
        )
        profiles = profiles_resp.data or []

        if not profiles:
            return {"processed": 0, "reason": "no_active_profiles"}

        processed = 0
        skipped = 0
        errors = 0

        for profile in profiles:
            try:
                user_id = profile["id"]
                ctx = profile.get("profile_context") or {}

                # Support multiple field name conventions
                setor_id = (
                    ctx.get("setor_id")
                    or ctx.get("setor")
                    or ctx.get("sector_id")
                )
                ufs_raw = (
                    ctx.get("ufs")
                    or ctx.get("ufs_selecionadas")
                    or ctx.get("states")
                    or []
                )
                ufs = list(ufs_raw) if isinstance(ufs_raw, (list, tuple)) else []

                if not setor_id or not ufs:
                    skipped += 1
                    continue

                # Count bids in last 26h matching user's sector + UFs
                count_resp = await sb_execute(
                    sb.table("pncp_raw_bids")
                    .select("id", count="exact")
                    .eq("setor_id", setor_id)
                    .in_("uf", ufs)
                    .gte("ingested_at", since)
                    .eq("is_active", True)
                )
                count = count_resp.count or 0

                if redis:
                    await redis.setex(
                        f"new_bids_count:{user_id}",
                        NEW_BIDS_REDIS_TTL,
                        str(count),
                    )
                processed += 1

            except Exception as e:
                uid_prefix = profile.get("id", "?")
                if isinstance(uid_prefix, str):
                    uid_prefix = uid_prefix[:8]
                logger.warning(
                    "STORY-445: Error processing user %s: %s", uid_prefix, e
                )
                errors += 1

        logger.info(
            "STORY-445 new_bids_notifier: processed=%d, skipped=%d, errors=%d",
            processed,
            skipped,
            errors,
        )
        return {"processed": processed, "skipped": skipped, "errors": errors}

    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning(
                "STORY-445: New bids notifier skipped (Supabase unavailable): %s", e
            )
        else:
            logger.error(
                "STORY-445: New bids notifier error: %s", e, exc_info=True
            )
        return {"processed": 0, "error": str(e)}


async def _new_bids_notifier_loop() -> None:
    await asyncio.sleep(_next_utc_hour(NEW_BIDS_NOTIFIER_HOUR_UTC))
    while True:
        try:
            result = await run_new_bids_notifier()
            logger.info("STORY-445 new_bids_notifier cycle: %s", result)
            await asyncio.sleep(24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("STORY-445: New bids notifier task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning(
                    "STORY-445: New bids notifier loop skipped (Supabase unavailable): %s",
                    e,
                )
            else:
                logger.error(
                    "STORY-445: New bids notifier loop error: %s", e, exc_info=True
                )
            await asyncio.sleep(300)


async def start_new_bids_notifier_task() -> asyncio.Task:
    task = asyncio.create_task(
        _new_bids_notifier_loop(), name="new_bids_notifier"
    )
    logger.info(
        "STORY-445: New bids notifier task started (daily at 12:00 UTC / 09:00 BRT)"
    )
    return task
