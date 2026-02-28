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
# STORY-316: Health Canary Cron Job (every 5 minutes)
# ============================================================================

HEALTH_CANARY_INTERVAL_SECONDS = 5 * 60  # 5 minutes


async def start_health_canary_task() -> asyncio.Task:
    """STORY-316 AC6: Start the periodic health canary background task.

    Runs every 5 minutes. Saves results to health_checks table.
    Detects incidents and auto-resolves after 3 consecutive healthy.
    Respects HEALTH_CANARY_ENABLED feature flag.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_health_canary_loop(), name="health_canary")
    logger.info("STORY-316: Health canary task started (interval: 5m)")
    return task


async def run_health_canary() -> dict:
    """STORY-316 AC6: Execute a single health canary check.

    1. Run realistic source checks (PNCP tamanhoPagina=50, PCP v2, ComprasGov)
    2. Check component health (Redis, Supabase, ARQ)
    3. Save result to health_checks table
    4. Detect incidents (AC8) and auto-resolve (AC10)
    5. Update Prometheus metrics (AC18)
    """
    import time as _time
    from config import HEALTH_CANARY_ENABLED

    if not HEALTH_CANARY_ENABLED:
        return {"status": "disabled"}

    start = _time.time()

    try:
        from health import get_public_status, save_health_check, detect_incident
        from metrics import HEALTH_CANARY_DURATION, HEALTH_CANARY_STATUS

        # Get full status (AC1: realistic canary)
        status_data = await get_public_status()
        duration = _time.time() - start

        overall = status_data.get("status", "unhealthy")
        sources = status_data.get("sources", {})
        components = status_data.get("components", {})

        # Calculate average latency
        latencies = [
            s.get("latency_ms", 0) for s in sources.values()
            if isinstance(s, dict) and s.get("latency_ms") is not None
        ]
        avg_latency = int(sum(latencies) / len(latencies)) if latencies else None

        # Save to DB (AC6)
        await save_health_check(overall, sources, components, avg_latency)

        # Detect incidents (AC8/AC10)
        await detect_incident(overall, sources)

        # Update metrics (AC18)
        try:
            HEALTH_CANARY_DURATION.observe(duration)
            status_value = {"healthy": 1.0, "degraded": 0.5, "unhealthy": 0.0}.get(overall, 0.0)
            HEALTH_CANARY_STATUS.set(status_value)
        except Exception:
            pass

        # Periodic cleanup of old health checks
        from health import cleanup_old_health_checks
        await cleanup_old_health_checks()

        logger.info(
            "STORY-316 canary: status=%s, latency=%s ms, duration=%.1fs",
            overall, avg_latency, duration,
        )

        return {
            "status": overall,
            "latency_ms": avg_latency,
            "duration_s": round(duration, 2),
            "sources": {k: v.get("status") for k, v in sources.items() if isinstance(v, dict)},
        }

    except Exception as e:
        logger.error("STORY-316 canary error: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}


async def _health_canary_loop() -> None:
    """STORY-316 AC6: Run health canary every 5 minutes."""
    from config import HEALTH_CANARY_ENABLED, HEALTH_CANARY_INTERVAL_SECONDS as interval

    if not HEALTH_CANARY_ENABLED:
        logger.info("STORY-316: Health canary disabled (HEALTH_CANARY_ENABLED=false)")
        return

    # Wait 30s after startup to let app stabilize
    await asyncio.sleep(30)

    while True:
        try:
            await run_health_canary()
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("STORY-316: Health canary task cancelled")
            break
        except Exception as e:
            logger.error("STORY-316 canary loop error: %s", e, exc_info=True)
            await asyncio.sleep(60)


# ============================================================================
# STORY-266: Trial Reminder Emails (legacy — replaced by STORY-310 sequence)
# ============================================================================

# Trial reminder check interval: every 6 hours (runs ~4x/day for robustness)
TRIAL_REMINDER_INTERVAL_SECONDS = 6 * 60 * 60

# Day milestones for email triggers (days since account creation)
# DEPRECATED: Kept for backward compat. STORY-310 uses TRIAL_EMAIL_SEQUENCE.
TRIAL_EMAIL_MILESTONES = {
    3: "midpoint",
    5: "expiring",
    6: "last_day",
    8: "expired",
}

# ============================================================================
# STORY-310: Trial Email Sequence (daily, 08:00 BRT)
# ============================================================================

# Daily check interval (24h). Cron runs daily at 08:00 BRT (11:00 UTC).
TRIAL_SEQUENCE_INTERVAL_SECONDS = 24 * 60 * 60

# Max emails per execution cycle (AC9)
TRIAL_SEQUENCE_BATCH_SIZE = 50


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


# ============================================================================
# STORY-309 AC4: Pre-Dunning Card Expiry Warning
# ============================================================================

# Check interval: every 24 hours (check once per day)
PRE_DUNNING_INTERVAL_SECONDS = 24 * 60 * 60


async def start_pre_dunning_task() -> asyncio.Task:
    """STORY-309 AC4: Start the periodic pre-dunning card expiry check.

    Runs once on startup (after 120s delay), then every 24 hours.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_pre_dunning_loop(), name="pre_dunning")
    logger.info("Pre-dunning card expiry check started (interval: 24h)")
    return task


async def check_pre_dunning_cards() -> dict:
    """STORY-309 AC4: Check for cards expiring within 7 days and send warnings.

    Uses Stripe API to list customers with cards about to expire.
    For each expiring card, sends a pre-dunning email via the dunning service.

    Returns:
        dict with counts: {"sent": N, "skipped": M, "errors": E}
    """
    import os

    try:
        import stripe
        stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        if not stripe_key:
            logger.debug("Pre-dunning: STRIPE_SECRET_KEY not set, skipping")
            return {"sent": 0, "skipped": 0, "errors": 0, "disabled": True}

        from supabase_client import get_supabase, sb_execute
        from services.dunning import send_pre_dunning_email

        sb = get_supabase()
        now = datetime.now(timezone.utc)

        # Target: cards expiring in the current month (7 days from now)
        target_date = now + timedelta(days=7)
        target_month = target_date.month
        target_year = target_date.year

        sent = 0
        skipped = 0
        errors = 0

        # Find active subscribers with Stripe customer IDs
        subs_result = await sb_execute(
            sb.table("user_subscriptions")
            .select("user_id, stripe_customer_id")
            .eq("is_active", True)
            .eq("subscription_status", "active")
            .not_.is_("stripe_customer_id", "null")
        )

        if not subs_result.data:
            return {"sent": 0, "skipped": 0, "errors": 0}

        for sub in subs_result.data:
            try:
                customer_id = sub.get("stripe_customer_id")
                user_id = sub.get("user_id")

                if not customer_id or not user_id:
                    continue

                # Check customer's default payment method via Stripe API
                customer = stripe.Customer.retrieve(
                    customer_id,
                    api_key=stripe_key,
                    expand=["default_source", "invoice_settings.default_payment_method"],
                )

                # Get card details from default payment method
                pm = customer.get("invoice_settings", {}).get("default_payment_method")
                card_info = None

                if pm and hasattr(pm, "card"):
                    card_info = pm.card
                elif customer.get("default_source") and hasattr(customer.default_source, "exp_month"):
                    card_info = customer.default_source

                if not card_info:
                    skipped += 1
                    continue

                exp_month = getattr(card_info, "exp_month", None) or card_info.get("exp_month")
                exp_year = getattr(card_info, "exp_year", None) or card_info.get("exp_year")
                last4 = getattr(card_info, "last4", None) or card_info.get("last4", "****")

                if not exp_month or not exp_year:
                    skipped += 1
                    continue

                # Check if card expires this target month
                if exp_year == target_year and exp_month == target_month:
                    await send_pre_dunning_email(user_id, last4, exp_month, exp_year)
                    sent += 1
                else:
                    skipped += 1

            except Exception as e:
                errors += 1
                logger.debug(f"Pre-dunning check failed for customer: {e}")

        logger.info(f"Pre-dunning check: sent={sent}, skipped={skipped}, errors={errors}")
        return {"sent": sent, "skipped": skipped, "errors": errors}

    except Exception as e:
        logger.error(f"Pre-dunning check failed: {e}", exc_info=True)
        return {"sent": 0, "skipped": 0, "errors": 1, "error": str(e)}


async def _pre_dunning_loop() -> None:
    """STORY-309 AC4: Run pre-dunning card check periodically."""
    # Delay 120s after startup
    await asyncio.sleep(120)

    while True:
        try:
            result = await check_pre_dunning_cards()
            logger.info(
                f"Pre-dunning cycle: {result} "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
            await asyncio.sleep(PRE_DUNNING_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Pre-dunning task cancelled")
            break
        except Exception as e:
            logger.error(f"Pre-dunning loop error: {e}", exc_info=True)
            await asyncio.sleep(60)


# ============================================================================
# STORY-310: Trial Email Sequence (daily at 08:00 BRT)
# ============================================================================

# ============================================================================
# STORY-315 AC8: Search Alerts (daily at 08:00 BRT = 11:00 UTC)
# ============================================================================

ALERTS_LOCK_KEY = "smartlic:alerts:lock"
ALERTS_LOCK_TTL = 30 * 60  # 30 minutes


async def start_alerts_task() -> asyncio.Task:
    """STORY-315 AC8: Start the daily search alerts background task.

    Calculates initial delay to align with ALERTS_HOUR_UTC (08:00 BRT),
    then runs every 24 hours with Redis lock protection.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_alerts_loop(), name="search_alerts")
    logger.info("STORY-315: Search alerts task started (daily at 08:00 BRT)")
    return task


async def run_search_alerts() -> dict:
    """Execute a single search alerts run with lock protection.

    AC8: Uses Redis lock with 30min TTL to prevent duplicate execution.
    Processes max 100 alerts per run, 10 concurrent.
    Respects ALERTS_ENABLED flag.
    """
    import time as _time

    from config import ALERTS_ENABLED

    if not ALERTS_ENABLED:
        logger.info("STORY-315: Alerts disabled (ALERTS_ENABLED=false)")
        return {"status": "disabled"}

    # Acquire Redis lock
    lock_acquired = False
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            lock_acquired = await redis.set(
                ALERTS_LOCK_KEY,
                datetime.now(timezone.utc).isoformat(),
                nx=True,
                ex=ALERTS_LOCK_TTL,
            )
            if not lock_acquired:
                logger.info("STORY-315: Alerts skipped — lock already held")
                return {"status": "skipped", "reason": "lock_held"}
    except Exception as e:
        logger.warning(f"STORY-315: Redis lock check failed (proceeding): {e}")
        lock_acquired = True  # Proceed without lock on Redis failure

    try:
        from services.alert_matcher import match_alerts, finalize_matched_alert
        from services.alert_service import get_sent_item_ids
        from templates.emails.alert_digest import (
            render_alert_digest_email,
            get_alert_digest_subject,
        )
        from routes.alerts import get_alert_unsubscribe_url
        from email_service import send_email_async
        from metrics import (
            ALERTS_PROCESSED,
            ALERTS_ITEMS_MATCHED,
            ALERTS_EMAILS_SENT,
            ALERTS_PROCESSING_DURATION,
        )

        start = _time.time()

        # AC8: Run matching engine (max 100 alerts)
        result = await match_alerts(max_alerts=100, batch_size=10)

        # Send emails for matched alerts
        emails_sent = 0
        for payload in result.get("payloads", []):
            try:
                items = payload.get("new_items", [])
                if not items:
                    continue

                alert_id = payload["alert_id"]
                unsubscribe_url = get_alert_unsubscribe_url(alert_id)
                alert_name = payload.get("alert_name", "suas licitacoes")

                # AC5: Render email (max 20 items)
                html = render_alert_digest_email(
                    user_name=payload["full_name"],
                    alert_name=alert_name,
                    opportunities=items[:20],
                    total_count=len(items),
                    unsubscribe_url=unsubscribe_url,
                )
                subject = get_alert_digest_subject(len(items), alert_name)

                # AC7: Send with List-Unsubscribe header
                send_email_async(
                    to=payload["email"],
                    subject=subject,
                    html=html,
                    headers={
                        "List-Unsubscribe": f"<{unsubscribe_url}>",
                        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                    },
                    tags=[
                        {"name": "category", "value": "alert_digest"},
                        {"name": "alert_id", "value": alert_id[:8]},
                    ],
                )

                # Track sent items for dedup
                item_ids = [item["id"] for item in items if item.get("id")]
                await finalize_matched_alert(alert_id, item_ids)

                emails_sent += 1
                ALERTS_EMAILS_SENT.labels(mode="individual").inc()
                ALERTS_ITEMS_MATCHED.inc(len(items))

            except Exception as e:
                logger.error(
                    "STORY-315: Failed to send alert email for %s: %s",
                    payload.get("alert_id", "?")[:8], e,
                )

        # Record metrics
        ALERTS_PROCESSED.labels(outcome="matched").inc(result.get("matched", 0))
        ALERTS_PROCESSED.labels(outcome="skipped").inc(result.get("skipped", 0))
        ALERTS_PROCESSED.labels(outcome="error").inc(result.get("errors", 0))

        duration = _time.time() - start
        ALERTS_PROCESSING_DURATION.observe(duration)

        result["emails_sent"] = emails_sent
        result["duration_s"] = round(duration, 2)

        logger.info(
            "STORY-315: Alert cycle complete — "
            "matched=%d, emails=%d, skipped=%d, errors=%d, duration=%.1fs",
            result.get("matched", 0),
            emails_sent,
            result.get("skipped", 0),
            result.get("errors", 0),
            duration,
        )

        return result

    finally:
        # Release lock
        if lock_acquired:
            try:
                from redis_pool import get_redis_pool
                redis = await get_redis_pool()
                if redis:
                    await redis.delete(ALERTS_LOCK_KEY)
            except Exception:
                pass


async def _alerts_loop() -> None:
    """STORY-315 AC8: Run search alerts daily at configured hour."""
    from config import ALERTS_ENABLED, ALERTS_HOUR_UTC

    if not ALERTS_ENABLED:
        logger.info("STORY-315: Alerts disabled (ALERTS_ENABLED=false)")
        return

    # Calculate delay until next target hour
    now = datetime.now(timezone.utc)
    next_run = now.replace(
        hour=ALERTS_HOUR_UTC, minute=0, second=0, microsecond=0,
    )
    if now.hour >= ALERTS_HOUR_UTC:
        next_run += timedelta(days=1)

    initial_delay = (next_run - now).total_seconds()
    initial_delay = max(60, min(initial_delay, 86400))

    logger.info(
        "STORY-315: Alerts first run in %.0fs (target: %s)",
        initial_delay, next_run.isoformat(),
    )
    await asyncio.sleep(initial_delay)

    while True:
        try:
            result = await run_search_alerts()
            logger.info(
                "STORY-315 alert cycle: %s at %s",
                result, datetime.now(timezone.utc).isoformat(),
            )
            await asyncio.sleep(24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("STORY-315: Alerts task cancelled")
            break
        except Exception as e:
            logger.error(f"STORY-315: Alerts loop error: {e}", exc_info=True)
            await asyncio.sleep(300)


# ============================================================================
# STORY-314: Stripe ⇄ DB Reconciliation (daily at 03:00 BRT = 06:00 UTC)
# ============================================================================

RECONCILIATION_LOCK_KEY = "smartlic:reconciliation:lock"
RECONCILIATION_LOCK_TTL = 30 * 60  # 30 minutes


async def start_reconciliation_task() -> asyncio.Task:
    """STORY-314 AC5: Start the daily Stripe reconciliation background task.

    Calculates initial delay to align with RECONCILIATION_HOUR_UTC,
    then runs every 24 hours with Redis lock protection.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_reconciliation_loop(), name="stripe_reconciliation")
    logger.info("STORY-314: Stripe reconciliation task started (daily at 03:00 BRT)")
    return task


async def run_reconciliation() -> dict:
    """Execute a single reconciliation run with lock protection.

    AC6: Uses Redis lock with 30min TTL to prevent duplicate execution.
    Returns the reconciliation result dict, or a skip-status dict if locked.
    """
    from services.stripe_reconciliation import (
        reconcile_subscriptions,
        save_reconciliation_report,
        send_reconciliation_alert,
    )

    # AC6: Acquire Redis lock
    lock_acquired = False
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            lock_acquired = await redis.set(
                RECONCILIATION_LOCK_KEY,
                datetime.now(timezone.utc).isoformat(),
                nx=True,
                ex=RECONCILIATION_LOCK_TTL,
            )
            if not lock_acquired:
                logger.info("Reconciliation skipped — lock already held")
                return {"status": "skipped", "reason": "lock_held"}
    except Exception as e:
        logger.warning(f"Redis lock check failed (proceeding without lock): {e}")
        lock_acquired = True  # Proceed without lock on Redis failure

    try:
        result = await reconcile_subscriptions()
        await save_reconciliation_report(result)
        await send_reconciliation_alert(result)
        return result
    finally:
        # Release lock
        if lock_acquired:
            try:
                from redis_pool import get_redis_pool
                redis = await get_redis_pool()
                if redis:
                    await redis.delete(RECONCILIATION_LOCK_KEY)
            except Exception:
                pass  # Lock will expire via TTL


async def _reconciliation_loop() -> None:
    """STORY-314 AC5: Run Stripe reconciliation daily at configured hour."""
    from config import RECONCILIATION_ENABLED, RECONCILIATION_HOUR_UTC

    if not RECONCILIATION_ENABLED:
        logger.info("Reconciliation disabled (RECONCILIATION_ENABLED=false)")
        return

    # Calculate delay until next target hour
    now = datetime.now(timezone.utc)
    next_run = now.replace(
        hour=RECONCILIATION_HOUR_UTC, minute=0, second=0, microsecond=0
    )
    if now.hour >= RECONCILIATION_HOUR_UTC:
        next_run += timedelta(days=1)

    initial_delay = (next_run - now).total_seconds()
    initial_delay = max(60, min(initial_delay, 86400))

    logger.info(
        f"STORY-314: Reconciliation first run in {initial_delay:.0f}s "
        f"(target: {next_run.isoformat()})"
    )
    await asyncio.sleep(initial_delay)

    while True:
        try:
            result = await run_reconciliation()
            logger.info(
                f"STORY-314 reconciliation cycle: "
                f"checked={result.get('total_checked', 0)}, "
                f"divergences={result.get('divergences_found', 0)} "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
            await asyncio.sleep(24 * 60 * 60)  # 24 hours
        except asyncio.CancelledError:
            logger.info("Reconciliation task cancelled")
            break
        except Exception as e:
            logger.error(f"Reconciliation loop error: {e}", exc_info=True)
            await asyncio.sleep(300)  # Retry in 5min on error


async def start_trial_sequence_task() -> asyncio.Task:
    """STORY-310 AC9: Start the daily trial email sequence background task.

    Calculates initial delay to align with 08:00 BRT (11:00 UTC),
    then runs every 24 hours.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_trial_sequence_loop(), name="trial_email_sequence")
    logger.info("STORY-310: Trial email sequence task started (daily at 08:00 BRT)")
    return task


async def _trial_sequence_loop() -> None:
    """STORY-310 AC9: Run trial email sequence daily at ~08:00 BRT."""
    # Calculate delay until next 11:00 UTC (08:00 BRT)
    now = datetime.now(timezone.utc)
    target_hour = 11  # 08:00 BRT = 11:00 UTC
    next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    if now.hour >= target_hour:
        next_run += timedelta(days=1)

    initial_delay = (next_run - now).total_seconds()
    # Cap at 24h max, minimum 60s
    initial_delay = max(60, min(initial_delay, 86400))

    logger.info(
        f"STORY-310: Trial sequence first run in {initial_delay:.0f}s "
        f"(target: {next_run.isoformat()})"
    )
    await asyncio.sleep(initial_delay)

    while True:
        try:
            from services.trial_email_sequence import process_trial_emails
            result = await process_trial_emails(batch_size=TRIAL_SEQUENCE_BATCH_SIZE)
            logger.info(
                f"STORY-310 trial sequence cycle: {result} "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
            await asyncio.sleep(TRIAL_SEQUENCE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Trial email sequence task cancelled")
            break
        except Exception as e:
            logger.error(f"Trial email sequence loop error: {e}", exc_info=True)
            await asyncio.sleep(300)  # Retry in 5min on error
