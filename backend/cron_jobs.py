"""UX-303 AC8 + CRIT-011 AC7 + GTM-ARCH-002 AC5-AC7: Periodic cache, session cleanup, and warmup tasks.

Runs as background asyncio tasks during FastAPI lifespan.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta, date

logger = logging.getLogger(__name__)

# Cleanup interval: every 6 hours
CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60

# GTM-ARCH-002 AC5: Cache refresh interval — every 4 hours
CACHE_REFRESH_INTERVAL_SECONDS = 4 * 60 * 60

# CRIT-011 AC7: Session cleanup thresholds
SESSION_STALE_HOURS = 1        # in_progress > 1h → timeout
SESSION_OLD_DAYS = 7           # failed/timeout > 7d → delete


async def start_cache_cleanup_task() -> asyncio.Task:
    """Start the periodic local cache cleanup background task.

    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_cache_cleanup_loop(), name="cache_cleanup")
    logger.info("Cache cleanup background task started (interval: 6h)")
    return task


async def start_session_cleanup_task() -> asyncio.Task:
    """CRIT-011 AC7: Start the periodic session cleanup background task.

    Runs immediately on startup, then every 6 hours.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_session_cleanup_loop(), name="session_cleanup")
    logger.info("Session cleanup background task started (interval: 6h)")
    return task


async def start_cache_refresh_task() -> asyncio.Task:
    """GTM-ARCH-002 AC5: Start the periodic cache refresh background task.

    Connects get_stale_entries_for_refresh() to a cron loop that runs every 4h.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_cache_refresh_loop(), name="cache_refresh")
    logger.info("Cache refresh background task started (interval: 4h)")
    return task


async def cleanup_stale_sessions() -> dict:
    """CRIT-011 AC7: Clean up stale search sessions.

    - Sessions with status='in_progress' and created_at > 1 hour → mark as 'timeout'
    - Sessions with status IN ('failed', 'timeout', 'timed_out') and created_at > 7 days → delete
    - If status column doesn't exist: delete sessions with created_at > 7 days (graceful fallback)

    Returns dict with counts: {"marked_stale": N, "deleted_old": M}
    """
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()

        now = datetime.now(timezone.utc)
        stale_cutoff = (now - timedelta(hours=SESSION_STALE_HOURS)).isoformat()
        old_cutoff = (now - timedelta(days=SESSION_OLD_DAYS)).isoformat()

        # Try status-based cleanup first; fall back if column doesn't exist
        try:
            # Mark stale in_progress sessions as timed_out
            marked_result = await sb_execute(
                sb.table("search_sessions")
                .update({
                    "status": "timed_out",
                    "error_message": "Session timed out (cleanup)",
                    "error_code": "session_timeout",
                    "completed_at": now.isoformat(),
                })
                .eq("status", "in_progress")
                .lt("created_at", stale_cutoff)
            )
            marked_stale = len(marked_result.data) if marked_result.data else 0

            # Also mark stale 'created' and 'processing' sessions
            for stale_status in ("created", "processing"):
                extra_result = await sb_execute(
                    sb.table("search_sessions")
                    .update({
                        "status": "timed_out",
                        "error_message": "Session timed out (cleanup)",
                        "error_code": "session_timeout",
                        "completed_at": now.isoformat(),
                    })
                    .eq("status", stale_status)
                    .lt("created_at", stale_cutoff)
                )
                marked_stale += len(extra_result.data) if extra_result.data else 0

            # Delete old terminal sessions
            deleted_old = 0
            for terminal_status in ("failed", "timeout", "timed_out"):
                del_result = await sb_execute(
                    sb.table("search_sessions")
                    .delete()
                    .eq("status", terminal_status)
                    .lt("created_at", old_cutoff)
                )
                deleted_old += len(del_result.data) if del_result.data else 0

            return {"marked_stale": marked_stale, "deleted_old": deleted_old}

        except Exception as col_err:
            if "42703" in str(col_err):
                # status/error columns don't exist — fallback to created_at-only cleanup
                logger.warning(
                    "Session cleanup: status column not found, "
                    "falling back to created_at-only cleanup"
                )
                del_result = await sb_execute(
                    sb.table("search_sessions")
                    .delete()
                    .lt("created_at", old_cutoff)
                )
                deleted_old = len(del_result.data) if del_result.data else 0
                return {"marked_stale": 0, "deleted_old": deleted_old}
            raise

    except Exception as e:
        logger.error(f"Session cleanup error: {e}", exc_info=True)
        return {"marked_stale": 0, "deleted_old": 0, "error": str(e)}


async def refresh_stale_cache_entries() -> dict:
    """GTM-ARCH-002 AC5: Refresh stale HOT/WARM cache entries.

    Connects get_stale_entries_for_refresh() to trigger_background_revalidation().
    Returns dict with refresh stats.
    """
    from search_cache import get_stale_entries_for_refresh, trigger_background_revalidation

    try:
        entries = await get_stale_entries_for_refresh(batch_size=25)

        if not entries:
            return {"status": "no_stale_entries", "refreshed": 0}

        refreshed = 0
        failed = 0

        for entry in entries:
            try:
                # Build request_data with dates (last 10 days as default)
                search_params = entry.get("search_params", {})
                request_data = {
                    "ufs": search_params.get("ufs", []),
                    "data_inicial": (date.today() - timedelta(days=10)).isoformat(),
                    "data_final": date.today().isoformat(),
                    "modalidades": search_params.get("modalidades"),
                }

                dispatched = await trigger_background_revalidation(
                    user_id=entry["user_id"],
                    params=search_params,
                    request_data=request_data,
                )
                if dispatched:
                    refreshed += 1

                # Small delay between dispatches to avoid hammering sources
                await asyncio.sleep(2)

            except Exception as e:
                failed += 1
                logger.debug(f"Cache refresh dispatch failed for {entry.get('params_hash', '?')[:12]}: {e}")

        logger.info(
            f"Cache refresh cycle: {refreshed} dispatched, {failed} failed "
            f"out of {len(entries)} stale entries"
        )
        return {"status": "completed", "refreshed": refreshed, "failed": failed, "total": len(entries)}

    except Exception as e:
        logger.error(f"Cache refresh error: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "refreshed": 0}


async def warmup_top_params() -> dict:
    """GTM-ARCH-002 AC6/AC7: Pre-warm top 10 popular sector+UF combinations.

    Enqueues background revalidation for the most popular search parameters.
    Used both on startup (AC7) and periodically via cron (AC6).
    """
    from search_cache import get_top_popular_params, trigger_background_revalidation

    try:
        top_params = await get_top_popular_params(limit=10)

        if not top_params:
            logger.info("Warmup: no popular params found to pre-warm")
            return {"status": "no_params", "warmed": 0}

        warmed = 0
        for params in top_params:
            try:
                request_data = {
                    "ufs": params.get("ufs", []),
                    "data_inicial": (date.today() - timedelta(days=10)).isoformat(),
                    "data_final": date.today().isoformat(),
                    "modalidades": params.get("modalidades"),
                }

                # Use a system user_id for warmup (entries go into global cache)
                dispatched = await trigger_background_revalidation(
                    user_id="00000000-0000-0000-0000-000000000000",
                    params=params,
                    request_data=request_data,
                )
                if dispatched:
                    warmed += 1

                await asyncio.sleep(1)

            except Exception as e:
                logger.debug(f"Warmup dispatch failed: {e}")

        logger.info(f"Warmup: {warmed}/{len(top_params)} popular params enqueued")
        return {"status": "completed", "warmed": warmed, "total": len(top_params)}

    except Exception as e:
        logger.error(f"Warmup error: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "warmed": 0}


async def warmup_specific_combinations(ufs: list[str], sectors: list[str]) -> dict:
    """P1.2: Pre-warm cache for specific sector+UF combinations.

    Iterates over each sector x UF pair and dispatches a background
    revalidation using the system user ID so results land in the global
    (cross-user) cache tier.  Trial users whose first search matches one
    of these combos will receive a sub-5-second response from cache.

    Args:
        ufs: List of UF codes to warm (e.g. ["SP", "RJ", "MG"]).
        sectors: List of sector IDs to warm (e.g. ["software", "saude"]).

    Returns:
        dict with keys: dispatched, skipped, failed, total.
    """
    from search_cache import trigger_background_revalidation
    from config import WARMUP_BATCH_DELAY_SECONDS

    dispatched = 0
    skipped = 0
    failed = 0
    total = len(sectors) * len(ufs)

    logger.info(
        f"P1.2 warmup: starting {total} combinations "
        f"({len(sectors)} sectors x {len(ufs)} UFs)"
    )

    for sector_id in sectors:
        for uf in ufs:
            try:
                params = {
                    "setor_id": sector_id,
                    "ufs": [uf],
                    "status": None,
                    "modalidades": None,
                    "modo_busca": None,
                }
                request_data = {
                    "ufs": [uf],
                    "data_inicial": (date.today() - timedelta(days=10)).isoformat(),
                    "data_final": date.today().isoformat(),
                    "modalidades": None,
                }

                dispatched_ok = await trigger_background_revalidation(
                    user_id="00000000-0000-0000-0000-000000000000",
                    params=params,
                    request_data=request_data,
                )

                if dispatched_ok:
                    dispatched += 1
                    logger.debug(f"P1.2 warmup: dispatched sector={sector_id} uf={uf}")
                else:
                    skipped += 1
                    logger.debug(
                        f"P1.2 warmup: skipped sector={sector_id} uf={uf} "
                        f"(dedup / cooldown active)"
                    )

                await asyncio.sleep(WARMUP_BATCH_DELAY_SECONDS)

            except Exception as e:
                failed += 1
                logger.warning(
                    f"P1.2 warmup: failed sector={sector_id} uf={uf}: {e}"
                )

    logger.info(
        f"P1.2 warmup: completed — dispatched={dispatched}, "
        f"skipped={skipped}, failed={failed}, total={total}"
    )
    return {"dispatched": dispatched, "skipped": skipped, "failed": failed, "total": total}


async def start_warmup_task() -> asyncio.Task:
    """P1.2: Start the startup cache warm-up background task.

    Waits WARMUP_STARTUP_DELAY_SECONDS (default 120s) after app boot so
    the process stabilises before issuing warm-up requests.  Fire-and-forget
    — never blocks the lifespan startup sequence.

    Returns:
        asyncio.Task that can be cancelled during shutdown.
    """
    from config import WARMUP_ENABLED, WARMUP_UFS, WARMUP_SECTORS, WARMUP_STARTUP_DELAY_SECONDS

    if not WARMUP_ENABLED:
        logger.info("P1.2 warmup: disabled via WARMUP_ENABLED=false — skipping")
        # Return a no-op task so the caller can still .cancel() safely
        task = asyncio.create_task(asyncio.sleep(0), name="warmup_noop")
        return task

    task = asyncio.create_task(
        _warmup_startup_task(WARMUP_UFS, WARMUP_SECTORS, WARMUP_STARTUP_DELAY_SECONDS),
        name="cache_warmup",
    )
    logger.info(
        f"P1.2 warmup: task started — "
        f"delay={WARMUP_STARTUP_DELAY_SECONDS}s, "
        f"sectors={WARMUP_SECTORS}, ufs={WARMUP_UFS}"
    )
    return task


async def _warmup_startup_task(
    ufs: list[str],
    sectors: list[str],
    delay_seconds: int,
) -> None:
    """P1.2: Internal coroutine — wait, then warm up the cache."""
    try:
        logger.info(f"P1.2 warmup: waiting {delay_seconds}s before starting warm-up")
        await asyncio.sleep(delay_seconds)
        result = await warmup_specific_combinations(ufs, sectors)
        logger.info(f"P1.2 warmup: startup warm-up finished: {result}")
    except asyncio.CancelledError:
        logger.info("P1.2 warmup: startup warm-up task cancelled (shutdown before completion)")
    except Exception as e:
        logger.error(f"P1.2 warmup: startup warm-up task failed: {e}", exc_info=True)


async def _session_cleanup_loop() -> None:
    """CRIT-011 AC7: Run session cleanup on startup and every 6 hours."""
    # Run immediately on startup
    try:
        result = await cleanup_stale_sessions()
        logger.info(
            f"Session cleanup (startup): marked {result['marked_stale']} stale, "
            f"deleted {result['deleted_old']} old "
            f"at {datetime.now(timezone.utc).isoformat()}"
        )
    except Exception as e:
        logger.error(f"Session cleanup error on startup: {e}", exc_info=True)

    # Then every 6 hours
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            result = await cleanup_stale_sessions()
            logger.info(
                f"Session cleanup: marked {result['marked_stale']} stale, "
                f"deleted {result['deleted_old']} old "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
        except asyncio.CancelledError:
            logger.info("Session cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Session cleanup error: {e}", exc_info=True)
            await asyncio.sleep(60)


async def _cache_cleanup_loop() -> None:
    """Run cleanup every CLEANUP_INTERVAL_SECONDS."""
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            from search_cache import cleanup_local_cache
            deleted = cleanup_local_cache()
            logger.info(
                f"Periodic cache cleanup: deleted {deleted} expired files "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}", exc_info=True)
            # Don't crash the loop on transient errors
            await asyncio.sleep(60)


async def _cache_refresh_loop() -> None:
    """GTM-ARCH-002 AC5: Run cache refresh every 4 hours."""
    # Wait a bit after startup to avoid overloading (warmup runs on startup separately)
    await asyncio.sleep(60)

    while True:
        try:
            result = await refresh_stale_cache_entries()
            logger.info(
                f"Cache refresh cycle: {result} "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
            await asyncio.sleep(CACHE_REFRESH_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Cache refresh task cancelled")
            break
        except Exception as e:
            logger.error(f"Cache refresh loop error: {e}", exc_info=True)
            await asyncio.sleep(60)


# ============================================================================
# STORY-266: Trial Reminder Emails
# ============================================================================

# Trial reminder check interval: every 6 hours (runs ~4x/day for robustness)
TRIAL_REMINDER_INTERVAL_SECONDS = 6 * 60 * 60

# Day milestones for email triggers (days since account creation)
TRIAL_EMAIL_MILESTONES = {
    3: "midpoint",
    5: "expiring",
    6: "last_day",
    8: "expired",
}


async def start_trial_reminder_task() -> asyncio.Task:
    """STORY-266 AC7: Start the periodic trial reminder email background task.

    Runs once on startup (after 60s delay), then every 6 hours.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_trial_reminder_loop(), name="trial_reminders")
    logger.info("Trial reminder background task started (interval: 6h)")
    return task


async def check_trial_reminders() -> dict:
    """STORY-266 AC7-AC9: Check and send trial reminder emails.

    AC7: Identifies users at each trial milestone day.
    AC8: Queries profiles with plan_type='free_trial' at day milestones.
    AC9: Idempotent — checks trial_email_log before sending.
    AC11: Uses send_email_async() for fire-and-forget delivery.
    AC12: Structured logging for each sent email.

    Returns:
        dict with counts: {"sent": N, "skipped": M, "errors": E}
    """
    from config import TRIAL_EMAILS_ENABLED

    if not TRIAL_EMAILS_ENABLED:
        logger.debug("Trial emails disabled (TRIAL_EMAILS_ENABLED=false)")
        return {"sent": 0, "skipped": 0, "errors": 0, "disabled": True}

    try:
        from supabase_client import get_supabase, sb_execute
        from services.trial_stats import get_trial_usage_stats
        from templates.emails.trial import (
            render_trial_midpoint_email,
            render_trial_expiring_email,
            render_trial_last_day_email,
            render_trial_expired_email,
        )
        from email_service import send_email_async
        from metrics import TRIAL_EMAILS_SENT

        sb = get_supabase()
        now = datetime.now(timezone.utc)

        sent = 0
        skipped = 0
        errors = 0

        for day, email_type in TRIAL_EMAIL_MILESTONES.items():
            try:
                # Calculate target date range: users created exactly `day` days ago
                # Use a 24h window to handle timezone differences
                target_start = (now - timedelta(days=day, hours=12)).isoformat()
                target_end = (now - timedelta(days=day - 1, hours=-12)).isoformat()

                # AC8: Find trial users at this milestone
                users_result = await sb_execute(
                    sb.table("profiles")
                    .select("id, email, full_name")
                    .eq("plan_type", "free_trial")
                    .gte("created_at", target_start)
                    .lt("created_at", target_end)
                )

                if not users_result.data:
                    continue

                for user in users_result.data:
                    user_id = user["id"]
                    email = user.get("email", "")
                    user_name = user.get("full_name") or email.split("@")[0] if email else "Usuário"

                    if not email:
                        continue

                    # AC9: Idempotency check — skip if already sent
                    try:
                        existing = await sb_execute(
                            sb.table("trial_email_log")
                            .select("id")
                            .eq("user_id", user_id)
                            .eq("email_type", email_type)
                            .limit(1)
                        )
                        if existing.data and len(existing.data) > 0:
                            skipped += 1
                            continue
                    except Exception:
                        pass  # If check fails, proceed (better to send than skip)

                    # Collect stats for personalization
                    try:
                        stats = get_trial_usage_stats(user_id)
                        stats_dict = stats.model_dump()
                    except Exception:
                        stats_dict = {}

                    # Render appropriate template
                    try:
                        if email_type == "midpoint":
                            subject = f"Você já analisou {_format_value(stats_dict.get('total_value_estimated', 0))} em oportunidades"
                            html = render_trial_midpoint_email(user_name, stats_dict)
                        elif email_type == "expiring":
                            subject = "Seu acesso completo ao SmartLic acaba em 2 dias"
                            html = render_trial_expiring_email(user_name, 2, stats_dict)
                        elif email_type == "last_day":
                            subject = "Amanhã seu acesso expira — não perca o que você construiu"
                            html = render_trial_last_day_email(user_name, stats_dict)
                        elif email_type == "expired":
                            opps = stats_dict.get("opportunities_found", 0)
                            pipeline = stats_dict.get("pipeline_items_count", 0)
                            count = pipeline if pipeline > 0 else opps
                            if count > 0:
                                subject = f"Suas {count} oportunidades estão esperando por você"
                            else:
                                subject = "As oportunidades de licitação continuam surgindo"
                            html = render_trial_expired_email(user_name, stats_dict)
                        else:
                            continue

                        # AC11: Fire-and-forget send
                        send_email_async(
                            to=email,
                            subject=subject,
                            html=html,
                            tags=[
                                {"name": "category", "value": "trial_reminder"},
                                {"name": "type", "value": email_type},
                            ],
                        )

                        # Record in log for idempotency (AC9)
                        try:
                            await sb_execute(
                                sb.table("trial_email_log").insert({
                                    "user_id": user_id,
                                    "email_type": email_type,
                                })
                            )
                        except Exception as log_err:
                            # UNIQUE constraint violation = already sent (race condition safe)
                            logger.debug(f"trial_email_log insert failed (likely dup): {log_err}")

                        # AC13: Prometheus metric
                        try:
                            TRIAL_EMAILS_SENT.labels(type=email_type).inc()
                        except Exception:
                            pass

                        # AC12: Structured logging
                        logger.info(
                            "trial_email_sent",
                            extra={
                                "user_id": user_id[:8] + "***",
                                "email_type": email_type,
                                "day": day,
                            },
                        )
                        sent += 1

                    except Exception as render_err:
                        errors += 1
                        logger.error(f"Failed to send trial email ({email_type}) to {user_id[:8]}***: {render_err}")

            except Exception as milestone_err:
                errors += 1
                logger.error(f"Failed to process trial milestone day={day}: {milestone_err}")

        logger.info(f"Trial reminders: sent={sent}, skipped={skipped}, errors={errors}")
        return {"sent": sent, "skipped": skipped, "errors": errors}

    except Exception as e:
        logger.error(f"Trial reminder check failed: {e}", exc_info=True)
        return {"sent": 0, "skipped": 0, "errors": 1, "error": str(e)}


def _format_value(value: float) -> str:
    """Format value for email subject lines."""
    if value >= 1_000_000:
        return f"R$ {value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"R$ {value / 1_000:.0f}k"
    if value > 0:
        return f"R$ {value:,.0f}".replace(",", ".")
    return "oportunidades"


async def _trial_reminder_loop() -> None:
    """STORY-266 AC7: Run trial reminder check periodically."""
    # Delay 60s after startup to avoid overloading
    await asyncio.sleep(60)

    while True:
        try:
            result = await check_trial_reminders()
            logger.info(
                f"Trial reminder cycle: {result} "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
            await asyncio.sleep(TRIAL_REMINDER_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Trial reminder task cancelled")
            break
        except Exception as e:
            logger.error(f"Trial reminder loop error: {e}", exc_info=True)
            await asyncio.sleep(60)
