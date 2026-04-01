"""jobs.cron.billing — Billing reconciliation, dunning, revenue share, and plan sync crons."""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from jobs.cron.canary import _is_cb_or_connection_error

logger = logging.getLogger(__name__)

RECONCILIATION_LOCK_KEY = "smartlic:reconciliation:lock"
RECONCILIATION_LOCK_TTL = 30 * 60
PRE_DUNNING_INTERVAL_SECONDS = 24 * 60 * 60
REVENUE_SHARE_LOCK_KEY = "smartlic:revenue_share:lock"
REVENUE_SHARE_LOCK_TTL = 30 * 60
PLAN_RECONCILIATION_LOCK_KEY = "smartlic:plan_reconciliation:lock"
PLAN_RECONCILIATION_LOCK_TTL = 10 * 60
PLAN_RECONCILIATION_INTERVAL = 12 * 60 * 60
STRIPE_EVENTS_RETENTION_DAYS = 90
STRIPE_PURGE_INTERVAL_SECONDS = 24 * 60 * 60

_MONITORED_TABLES = [
    "search_results_cache", "search_results_store", "search_sessions",
    "stripe_webhook_events", "profiles", "user_subscriptions",
    "conversations", "messages", "alert_runs", "classification_feedback",
]


async def _acquire_lock(key: str, ttl: int) -> bool:
    """Acquire a Redis NX lock. Returns True if acquired (or Redis unavailable)."""
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            acquired = await redis.set(key, datetime.now(timezone.utc).isoformat(), nx=True, ex=ttl)
            if not acquired:
                return False
    except Exception as e:
        logger.warning(f"Redis lock check failed (proceeding): {e}")
    return True


async def _release_lock(key: str) -> None:
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            await redis.delete(key)
    except Exception:
        pass


def _next_utc_hour(target_hour: int, max_delay: float = 86400.0) -> float:
    now = datetime.now(timezone.utc)
    next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    if now.hour >= target_hour:
        next_run += timedelta(days=1)
    return max(60.0, min((next_run - now).total_seconds(), max_delay))


async def run_reconciliation() -> dict:
    from services.stripe_reconciliation import reconcile_subscriptions, save_reconciliation_report, send_reconciliation_alert
    if not await _acquire_lock(RECONCILIATION_LOCK_KEY, RECONCILIATION_LOCK_TTL):
        logger.info("Reconciliation skipped — lock already held")
        return {"status": "skipped", "reason": "lock_held"}
    try:
        result = await reconcile_subscriptions()
        await save_reconciliation_report(result)
        await send_reconciliation_alert(result)
        return result
    finally:
        await _release_lock(RECONCILIATION_LOCK_KEY)


async def _reconciliation_loop() -> None:
    from config import RECONCILIATION_ENABLED, RECONCILIATION_HOUR_UTC
    if not RECONCILIATION_ENABLED:
        logger.info("Reconciliation disabled")
        return
    await asyncio.sleep(_next_utc_hour(RECONCILIATION_HOUR_UTC))
    while True:
        try:
            result = await run_reconciliation()
            logger.info("STORY-314 reconciliation cycle: checked=%d, divergences=%d", result.get("total_checked", 0), result.get("divergences_found", 0))
            await asyncio.sleep(24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("Reconciliation task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("Reconciliation skipped (Supabase unavailable): %s", e)
            else:
                logger.error(f"Reconciliation loop error: {e}", exc_info=True)
            await asyncio.sleep(300)


async def check_pre_dunning_cards() -> dict:
    import os
    try:
        import stripe
        stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        if not stripe_key:
            return {"sent": 0, "skipped": 0, "errors": 0, "disabled": True}
        from supabase_client import get_supabase, sb_execute
        from services.dunning import send_pre_dunning_email
        sb = get_supabase()
        now = datetime.now(timezone.utc)
        target_date = now + timedelta(days=7)
        sent = skipped = errors = 0
        subs_result = await sb_execute(sb.table("user_subscriptions").select("user_id, stripe_customer_id").eq("is_active", True).eq("subscription_status", "active").not_.is_("stripe_customer_id", "null"))
        if not subs_result.data:
            return {"sent": 0, "skipped": 0, "errors": 0}
        for sub in subs_result.data:
            try:
                customer_id = sub.get("stripe_customer_id")
                user_id = sub.get("user_id")
                if not customer_id or not user_id:
                    continue
                customer = stripe.Customer.retrieve(customer_id, api_key=stripe_key, expand=["default_source", "invoice_settings.default_payment_method"])
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
                if exp_year == target_date.year and exp_month == target_date.month:
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
        if _is_cb_or_connection_error(e):
            logger.warning("Pre-dunning check skipped (Supabase unavailable): %s", e)
        else:
            logger.error(f"Pre-dunning check failed: {e}", exc_info=True)
        return {"sent": 0, "skipped": 0, "errors": 1, "error": str(e)}


async def _pre_dunning_loop() -> None:
    await asyncio.sleep(120)
    while True:
        try:
            result = await check_pre_dunning_cards()
            logger.info(f"Pre-dunning cycle: {result}")
            await asyncio.sleep(PRE_DUNNING_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Pre-dunning task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("Pre-dunning loop skipped (Supabase unavailable): %s", e)
            else:
                logger.error(f"Pre-dunning loop error: {e}", exc_info=True)
            await asyncio.sleep(60)


async def run_revenue_share_report() -> dict:
    if not await _acquire_lock(REVENUE_SHARE_LOCK_KEY, REVENUE_SHARE_LOCK_TTL):
        logger.info("STORY-323: Revenue share report skipped — lock held")
        return {"status": "skipped", "reason": "lock_held"}
    try:
        from services.partner_service import generate_monthly_revenue_report
        now = datetime.now(timezone.utc)
        report_year = now.year - 1 if now.month == 1 else now.year
        report_month = 12 if now.month == 1 else now.month - 1
        result = await generate_monthly_revenue_report(report_year, report_month)
        logger.info("STORY-323: Revenue share report generated — %d/%d, %d partners, total_share=R$%.2f", report_month, report_year, len(result.get("partner_reports", [])), result.get("total_share", 0))
        return result
    finally:
        await _release_lock(REVENUE_SHARE_LOCK_KEY)


async def _revenue_share_loop() -> None:
    now = datetime.now(timezone.utc)
    if now.month == 12:
        next_run = datetime(now.year + 1, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    else:
        next_run = datetime(now.year, now.month + 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    initial_delay = max(60.0, min((next_run - now).total_seconds(), 31 * 86400.0))
    logger.info("STORY-323: Revenue share report first run in %.0fs (target: %s)", initial_delay, next_run.isoformat())
    await asyncio.sleep(initial_delay)
    while True:
        try:
            result = await run_revenue_share_report()
            logger.info("STORY-323 revenue share cycle: %s", result.get("total_share", "N/A"))
            await asyncio.sleep(30 * 24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("STORY-323: Revenue share report task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("STORY-323: Revenue share skipped (Supabase unavailable): %s", e)
            else:
                logger.error(f"STORY-323: Revenue share loop error: {e}", exc_info=True)
            await asyncio.sleep(3600)


async def run_plan_reconciliation() -> dict:
    from supabase_client import get_supabase, sb_execute
    from metrics import PLAN_RECONCILIATION_RUNS, PLAN_RECONCILIATION_DRIFT
    PLAN_RECONCILIATION_RUNS.inc()
    if not await _acquire_lock(PLAN_RECONCILIATION_LOCK_KEY, PLAN_RECONCILIATION_LOCK_TTL):
        logger.info("DEBT-010: Plan reconciliation skipped — lock held")
        return {"status": "skipped", "reason": "lock_held"}
    try:
        sb = get_supabase()
        profiles_result = await sb_execute(sb.table("profiles").select("id, plan_type"))
        profiles = {p["id"]: p["plan_type"] for p in (profiles_result.data or [])}
        subs_result = await sb_execute(sb.table("user_subscriptions").select("user_id, plan_id").eq("is_active", True))
        subs = {s["user_id"]: s["plan_id"] for s in (subs_result.data or [])}
        drift_details = []
        for user_id, plan_type in profiles.items():
            sub_plan = subs.get(user_id)
            if sub_plan is None:
                if plan_type not in ("free_trial", "cancelled", None, ""):
                    drift_details.append({"user_id": user_id[:8] + "...", "profile_plan": plan_type, "sub_plan": None, "direction": "orphan_profile"})
                    PLAN_RECONCILIATION_DRIFT.labels(direction="orphan_profile").inc()
            elif plan_type != sub_plan:
                drift_details.append({"user_id": user_id[:8] + "...", "profile_plan": plan_type, "sub_plan": sub_plan, "direction": "profiles_stale"})
                PLAN_RECONCILIATION_DRIFT.labels(direction="profiles_stale").inc()
        if drift_details:
            logger.warning("DEBT-010: Plan reconciliation found %d drifts: %s", len(drift_details), drift_details[:5])
        else:
            logger.info("DEBT-010: Plan reconciliation clean — %d profiles, %d active subs", len(profiles), len(subs))
        return {"status": "completed", "total_profiles": len(profiles), "total_active_subs": len(subs), "drift_count": len(drift_details), "drift_details": drift_details[:20], "checked_at": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("DEBT-010: Plan reconciliation skipped (Supabase unavailable): %s", e)
        else:
            logger.error("DEBT-010: Plan reconciliation error: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        await _release_lock(PLAN_RECONCILIATION_LOCK_KEY)


async def update_table_size_metrics() -> dict:
    from supabase_client import get_supabase, sb_execute_direct
    from metrics import DB_TABLE_SIZE_BYTES
    sizes = {}
    try:
        sb = get_supabase()
        for table_name in _MONITORED_TABLES:
            try:
                result = await sb_execute_direct(sb.rpc("pg_total_relation_size_safe", {"tbl": table_name}))
                if result and result.data is not None:
                    size_bytes = int(result.data) if not isinstance(result.data, list) else (int(result.data[0]) if result.data else 0)
                    DB_TABLE_SIZE_BYTES.labels(table_name=table_name).set(size_bytes)
                    sizes[table_name] = size_bytes
            except Exception as e:
                logger.debug("DEBT-010: Table size query failed for %s: %s", table_name, e)
                sizes[table_name] = -1
        logger.info("DEBT-010: Table sizes updated — %d tables", len(sizes))
        return {"status": "ok", "sizes": sizes}
    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("DEBT-010: Table size metrics skipped (Supabase unavailable): %s", e)
        else:
            logger.error("DEBT-010: Table size metrics error: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}


async def _plan_reconciliation_loop() -> None:
    await asyncio.sleep(300)
    while True:
        try:
            await run_plan_reconciliation()
            await update_table_size_metrics()
            await asyncio.sleep(PLAN_RECONCILIATION_INTERVAL)
        except asyncio.CancelledError:
            logger.info("DEBT-010: Plan reconciliation task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("DEBT-010: Reconciliation loop skipped: %s", e)
            else:
                logger.error("DEBT-010: Reconciliation loop error: %s", e, exc_info=True)
            await asyncio.sleep(300)


async def purge_old_stripe_events() -> dict:
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=STRIPE_EVENTS_RETENTION_DAYS)).isoformat()
        result = await sb_execute(sb.table("stripe_webhook_events").delete().lt("processed_at", cutoff))
        deleted = len(result.data) if result and result.data else 0
        logger.info("HARDEN-028: Purged %d Stripe webhook events older than %d days", deleted, STRIPE_EVENTS_RETENTION_DAYS)
        return {"deleted": deleted, "cutoff": cutoff}
    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("HARDEN-028: Stripe events purge skipped (Supabase unavailable): %s", e)
        else:
            logger.error("HARDEN-028: Stripe events purge error: %s", e, exc_info=True)
        return {"deleted": 0, "error": str(e)}


async def _stripe_events_purge_loop() -> None:
    while True:
        try:
            result = await purge_old_stripe_events()
            logger.info("HARDEN-028 purge cycle: %s", result)
            await asyncio.sleep(STRIPE_PURGE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("HARDEN-028: Stripe events purge task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("HARDEN-028 purge loop skipped: %s", e)
            else:
                logger.error("HARDEN-028 purge loop error: %s", e, exc_info=True)
            await asyncio.sleep(300)


async def start_reconciliation_task() -> asyncio.Task:
    task = asyncio.create_task(_reconciliation_loop(), name="stripe_reconciliation")
    logger.info("STORY-314: Stripe reconciliation task started (daily at 03:00 BRT)")
    return task


async def start_pre_dunning_task() -> asyncio.Task:
    task = asyncio.create_task(_pre_dunning_loop(), name="pre_dunning")
    logger.info("Pre-dunning card expiry check started (interval: 24h)")
    return task


async def start_revenue_share_task() -> asyncio.Task:
    task = asyncio.create_task(_revenue_share_loop(), name="revenue_share_report")
    logger.info("STORY-323: Revenue share report task started (monthly, day 1, 09:00 BRT)")
    return task


async def start_plan_reconciliation_task() -> asyncio.Task:
    task = asyncio.create_task(_plan_reconciliation_loop(), name="plan_reconciliation")
    logger.info("DEBT-010: Plan reconciliation task started (interval: 12h)")
    return task


async def start_stripe_events_purge_task() -> asyncio.Task:
    task = asyncio.create_task(_stripe_events_purge_loop(), name="stripe_events_purge")
    logger.info("HARDEN-028: Stripe events purge task started (interval: 24h, retention: %dd)", STRIPE_EVENTS_RETENTION_DAYS)
    return task
