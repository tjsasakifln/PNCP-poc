"""jobs.cron.notifications — Alerts, trial sequence, SLA, volume, and sector stats crons."""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from jobs.cron.canary import _is_cb_or_connection_error

logger = logging.getLogger(__name__)

TRIAL_SEQUENCE_INTERVAL_SECONDS = 2 * 60 * 60  # Every 2h to cover all timezones
TRIAL_SEQUENCE_BATCH_SIZE = 50
ALERTS_LOCK_KEY = "smartlic:alerts:lock"
ALERTS_LOCK_TTL = 30 * 60
SECTOR_STATS_HOUR_UTC = 6
DAILY_VOLUME_HOUR_UTC = 7


def _next_utc_hour(target_hour: int) -> float:
    now = datetime.now(timezone.utc)
    next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    if now.hour >= target_hour:
        next_run += timedelta(days=1)
    return max(60.0, min((next_run - now).total_seconds(), 86400.0))


async def run_search_alerts() -> dict:
    import time as _time
    from config import ALERTS_ENABLED, ALERTS_SYSTEM_ENABLED
    if not ALERTS_SYSTEM_ENABLED:
        return {"status": "disabled", "reason": "ALERTS_SYSTEM_ENABLED=false"}
    if not ALERTS_ENABLED:
        return {"status": "disabled"}
    lock_acquired = False
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            lock_acquired = await redis.set(ALERTS_LOCK_KEY, datetime.now(timezone.utc).isoformat(), nx=True, ex=ALERTS_LOCK_TTL)
            if not lock_acquired:
                return {"status": "skipped", "reason": "lock_held"}
    except Exception as e:
        logger.warning(f"STORY-315: Redis lock check failed (proceeding): {e}")
        lock_acquired = True
    try:
        from services.alert_matcher import match_alerts, finalize_matched_alert
        from templates.emails.alert_digest import render_alert_digest_email, get_alert_digest_subject
        from routes.alerts import get_alert_unsubscribe_url
        from email_service import send_email_async
        from metrics import ALERTS_PROCESSED, ALERTS_ITEMS_MATCHED, ALERTS_EMAILS_SENT, ALERTS_PROCESSING_DURATION
        start = _time.time()
        result = await match_alerts(max_alerts=100, batch_size=10)
        emails_sent = 0
        for payload in result.get("payloads", []):
            try:
                items = payload.get("new_items", [])
                if not items:
                    continue
                alert_id = payload["alert_id"]
                unsubscribe_url = get_alert_unsubscribe_url(alert_id)
                alert_name = payload.get("alert_name", "suas licitacoes")
                html = render_alert_digest_email(user_name=payload["full_name"], alert_name=alert_name, opportunities=items[:20], total_count=len(items), unsubscribe_url=unsubscribe_url)
                subject = get_alert_digest_subject(len(items), alert_name)
                send_email_async(to=payload["email"], subject=subject, html=html, headers={"List-Unsubscribe": f"<{unsubscribe_url}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}, tags=[{"name": "category", "value": "alert_digest"}, {"name": "alert_id", "value": alert_id[:8]}])
                item_ids = [item["id"] for item in items if item.get("id")]
                await finalize_matched_alert(alert_id, item_ids)
                emails_sent += 1
                ALERTS_EMAILS_SENT.labels(mode="individual").inc()
                ALERTS_ITEMS_MATCHED.inc(len(items))
            except Exception as e:
                logger.error("STORY-315: Failed to send alert email for %s: %s", payload.get("alert_id", "?")[:8], e)
        ALERTS_PROCESSED.labels(outcome="matched").inc(result.get("matched", 0))
        ALERTS_PROCESSED.labels(outcome="skipped").inc(result.get("skipped", 0))
        ALERTS_PROCESSED.labels(outcome="error").inc(result.get("errors", 0))
        duration = _time.time() - start
        ALERTS_PROCESSING_DURATION.observe(duration)
        result["emails_sent"] = emails_sent
        result["duration_s"] = round(duration, 2)
        logger.info("STORY-315: Alert cycle complete — matched=%d, emails=%d, skipped=%d, errors=%d, duration=%.1fs", result.get("matched", 0), emails_sent, result.get("skipped", 0), result.get("errors", 0), duration)
        return result
    finally:
        if lock_acquired:
            try:
                from redis_pool import get_redis_pool
                redis = await get_redis_pool()
                if redis:
                    await redis.delete(ALERTS_LOCK_KEY)
            except Exception:
                pass


async def _alerts_loop() -> None:
    from config import ALERTS_ENABLED, ALERTS_SYSTEM_ENABLED, ALERTS_HOUR_UTC
    if not ALERTS_SYSTEM_ENABLED or not ALERTS_ENABLED:
        logger.info("STORY-315: Alerts disabled")
        return
    await asyncio.sleep(_next_utc_hour(ALERTS_HOUR_UTC))
    while True:
        try:
            result = await run_search_alerts()
            logger.info("STORY-315 alert cycle: %s", result)
            await asyncio.sleep(24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("STORY-315: Alerts task cancelled")
            break
        except Exception as e:
            logger.error(f"STORY-315: Alerts loop error: {e}", exc_info=True)
            await asyncio.sleep(300)


async def _trial_sequence_loop() -> None:
    await asyncio.sleep(60)  # Small initial delay for startup
    while True:
        try:
            from services.trial_email_sequence import process_trial_emails
            result = await process_trial_emails(batch_size=TRIAL_SEQUENCE_BATCH_SIZE)
            logger.info("STORY-310 trial sequence cycle: %s", result)

            # STORY-418: drain the DLQ right after the forward pass so
            # any transient failure from this cycle (or previous ones)
            # gets a retry without waiting a full day for the next
            # scheduled run. ``reprocess_pending`` is already idempotent
            # and best-effort, so any error is logged and swallowed.
            try:
                from services.trial_email_dlq import reprocess_pending
                dlq_stats = await reprocess_pending(limit=100)
                if dlq_stats.get("considered", 0) > 0:
                    logger.info("STORY-418 trial_email_dlq cycle: %s", dlq_stats)
            except Exception as dlq_err:
                logger.error("STORY-418: DLQ reprocess failed: %s", dlq_err)

            await asyncio.sleep(TRIAL_SEQUENCE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Trial email sequence task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("Trial email sequence skipped (Supabase unavailable): %s", e)
            else:
                logger.error(f"Trial email sequence loop error: {e}", exc_info=True)
            await asyncio.sleep(300)


async def check_unanswered_messages() -> dict:
    import os
    from config import MESSAGES_ENABLED
    if not MESSAGES_ENABLED:
        return {"checked": 0, "breached": 0, "alerted": 0, "disabled": True}
    try:
        from supabase_client import get_supabase, sb_execute
        from business_hours import calculate_business_hours
        from config import SUPPORT_SLA_ALERT_THRESHOLD_HOURS
        from metrics import SUPPORT_PENDING_MESSAGES
        sb = get_supabase()
        now = datetime.now(timezone.utc)
        result = await sb_execute(sb.table("conversations").select("id, user_id, subject, category, created_at").is_("first_response_at", "null").neq("status", "resolvido").order("created_at", desc=False))
        conversations = result.data or []
        SUPPORT_PENDING_MESSAGES.set(len(conversations))
        if not conversations:
            return {"checked": 0, "breached": 0, "alerted": 0}
        breached = []
        for conv in conversations:
            from dateutil.parser import isoparse
            elapsed_hours = calculate_business_hours(isoparse(conv["created_at"]), now)
            if elapsed_hours >= SUPPORT_SLA_ALERT_THRESHOLD_HOURS:
                breached.append({"id": conv["id"], "subject": conv["subject"], "category": conv["category"], "elapsed_hours": elapsed_hours, "created_at": conv["created_at"]})
        alerted = 0
        if breached:
            admin_email = os.getenv("ADMIN_EMAIL", "tiago.sasaki@gmail.com")
            try:
                from email_service import send_email_async
                items_html = "".join(f"<tr><td>{b['subject']}</td><td>{b['category']}</td><td>{b['elapsed_hours']:.1f}h</td><td>{b['created_at'][:16]}</td></tr>" for b in breached)
                html = f"""<h2>Alerta de SLA de Suporte</h2><p>{len(breached)} mensagem(ns) sem resposta excederam {SUPPORT_SLA_ALERT_THRESHOLD_HOURS}h uteis.</p><table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;"><tr style="background:#f0f0f0;"><th>Assunto</th><th>Categoria</th><th>Horas uteis</th><th>Criada em</th></tr>{items_html}</table><p>Acesse <a href="https://smartlic.tech/mensagens">SmartLic Mensagens</a> para responder.</p>"""
                send_email_async(to=admin_email, subject=f"[SLA] {len(breached)} mensagem(ns) sem resposta > {SUPPORT_SLA_ALERT_THRESHOLD_HOURS}h", html=html, tags=[{"name": "category", "value": "sla_alert"}])
                alerted = len(breached)
                logger.warning("STORY-353 SLA alert: %d breached conversations, email sent to %s", len(breached), admin_email)
            except Exception as e:
                logger.error("STORY-353: Failed to send SLA alert email: %s", e)
        logger.info("STORY-353 SLA check: checked=%d, breached=%d, alerted=%d", len(conversations), len(breached), alerted)
        return {"checked": len(conversations), "breached": len(breached), "alerted": alerted}
    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("STORY-353: Support SLA check skipped (Supabase unavailable): %s", e)
        else:
            logger.error("STORY-353: Support SLA check error: %s", e, exc_info=True)
        return {"checked": 0, "breached": 0, "alerted": 0, "error": str(e)}


async def _support_sla_loop() -> None:
    from config import SUPPORT_SLA_CHECK_INTERVAL_SECONDS
    await asyncio.sleep(60)
    while True:
        try:
            result = await check_unanswered_messages()
            logger.info("STORY-353 SLA cycle: %s", result)
            await asyncio.sleep(SUPPORT_SLA_CHECK_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("STORY-353: Support SLA task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("STORY-353 SLA loop skipped (Supabase unavailable): %s", e)
            else:
                logger.error("STORY-353 SLA loop error: %s", e, exc_info=True)
            await asyncio.sleep(300)


async def record_daily_volume() -> dict:
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        now = datetime.now(timezone.utc)
        yesterday = (now - timedelta(hours=24)).isoformat()
        result = await sb_execute(sb.table("search_sessions").select("total_raw").gte("created_at", yesterday).in_("status", ["completed", "completed_partial"]))
        sessions = result.data or []
        total_bids = sum(s.get("total_raw") or 0 for s in sessions)
        logger.info("STORY-358 daily volume: %d bids processed across %d sessions in last 24h", total_bids, len(sessions))
        return {"total_bids_24h": total_bids, "session_count": len(sessions), "recorded_at": now.isoformat()}
    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("STORY-358: Daily volume recording skipped (Supabase unavailable): %s", e)
        else:
            logger.error("STORY-358: Daily volume recording error: %s", e, exc_info=True)
        return {"total_bids_24h": 0, "session_count": 0, "error": str(e)}


async def _daily_volume_loop() -> None:
    await asyncio.sleep(_next_utc_hour(DAILY_VOLUME_HOUR_UTC))
    while True:
        try:
            result = await record_daily_volume()
            logger.info("STORY-358 daily volume cycle: %s", result)
            await asyncio.sleep(24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("STORY-358: Daily volume task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("STORY-358 daily volume loop skipped (Supabase unavailable): %s", e)
            else:
                logger.error("STORY-358 daily volume loop error: %s", e, exc_info=True)
            await asyncio.sleep(600)


async def _sector_stats_loop() -> None:
    await asyncio.sleep(_next_utc_hour(SECTOR_STATS_HOUR_UTC))
    while True:
        try:
            from routes.sectors_public import refresh_all_sector_stats
            refreshed = await refresh_all_sector_stats()
            logger.info("STORY-324: Sector stats refreshed: %d/15 sectors", refreshed)
            await asyncio.sleep(24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("Sector stats refresh task cancelled")
            break
        except Exception as e:
            logger.error(f"Sector stats refresh error: {e}", exc_info=True)
            await asyncio.sleep(600)


async def start_alerts_task() -> asyncio.Task:
    task = asyncio.create_task(_alerts_loop(), name="search_alerts")
    logger.info("STORY-315: Search alerts task started (daily at 08:00 BRT)")
    return task


async def start_trial_sequence_task() -> asyncio.Task:
    task = asyncio.create_task(_trial_sequence_loop(), name="trial_email_sequence")
    logger.info("STORY-310: Trial email sequence task started (daily at 08:00 BRT)")
    return task


async def start_support_sla_task() -> asyncio.Task:
    task = asyncio.create_task(_support_sla_loop(), name="support_sla")
    logger.info("STORY-353: Support SLA check started (interval: 4h)")
    return task


async def start_daily_volume_task() -> asyncio.Task:
    task = asyncio.create_task(_daily_volume_loop(), name="daily_volume")
    logger.info("STORY-358: Daily volume recording task started (daily at 07:00 UTC)")
    return task


async def start_sector_stats_task() -> asyncio.Task:
    task = asyncio.create_task(_sector_stats_loop(), name="sector_stats_refresh")
    logger.info("STORY-324: Sector stats refresh task started (daily at 06:00 UTC)")
    return task
