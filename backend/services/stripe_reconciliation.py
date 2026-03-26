"""STORY-314: Stripe ⇄ DB Reconciliation Service.

Batch worker that compares Stripe subscription state (source of truth) with
local DB state, detects divergences, and auto-fixes them with an audit trail.

Runs daily at 03:00 BRT (06:00 UTC) via cron_jobs.py, with Redis lock protection
against duplicate execution.

Key design decisions:
- Stripe is ALWAYS the source of truth. DB is updated to match Stripe.
- past_due is a valid state during dunning — NOT treated as divergence.
- pending_payment (Boleto/PIX) is a valid transient state — NOT treated as divergence.
- Uses Supabase service role (not user JWT) for admin-level DB operations.
- Fire-and-forget email alert on divergences > 0.
"""

import os
import time
from datetime import datetime, timezone, timedelta

import stripe

from cache import redis_cache
from log_sanitizer import get_sanitized_logger, mask_user_id
from metrics import (
    RECONCILIATION_RUNS,
    RECONCILIATION_DIVERGENCES,
    RECONCILIATION_FIXES,
    RECONCILIATION_DURATION,
)
from supabase_client import get_supabase

logger = get_sanitized_logger(__name__)


# Stripe subscription status → DB subscription_status mapping
# https://docs.stripe.com/api/subscriptions/object#subscription_object-status
_STRIPE_STATUS_MAP = {
    "active": "active",
    "past_due": "past_due",
    "unpaid": "past_due",
    "canceled": "canceled",
    "incomplete": "pending_payment",
    "incomplete_expired": "canceled",
    "trialing": "active",
    "paused": "canceled",
}


def _determine_billing_period(stripe_sub: stripe.Subscription) -> str:
    """Extract billing_period from a Stripe subscription object."""
    items = stripe_sub.get("items", {}).get("data", [])
    if not items:
        return "monthly"
    plan = items[0].get("plan", {})
    interval = plan.get("interval", "month")
    interval_count = plan.get("interval_count", 1)
    if interval == "year":
        return "annual"
    if interval == "month" and interval_count == 6:
        return "semiannual"
    return "monthly"


def _determine_plan_id(stripe_sub: stripe.Subscription) -> str | None:
    """Extract plan_id from Stripe subscription metadata."""
    metadata = stripe_sub.get("metadata", {}) or {}
    return metadata.get("plan_id")


async def reconcile_subscriptions() -> dict:
    """Compare all Stripe subscriptions with local DB and fix divergences.

    Returns:
        dict with keys: total_checked, divergences, auto_fixed, manual_review,
        duration_ms, details (list of divergence records).
    """
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        logger.warning("STRIPE_SECRET_KEY not set — reconciliation skipped")
        return {
            "total_checked": 0,
            "divergences_found": 0,
            "auto_fixed": 0,
            "manual_review": 0,
            "duration_ms": 0,
            "details": [],
        }

    sb = get_supabase()
    start = time.monotonic()
    details: list[dict] = []
    total_checked = 0
    auto_fixed = 0
    manual_review = 0

    try:
        # 1. Fetch ALL Stripe subscriptions (paginated)
        stripe_subs: list[stripe.Subscription] = []
        has_more = True
        starting_after = None

        while has_more:
            params: dict = {"status": "all", "limit": 100, "api_key": stripe_key}
            if starting_after:
                params["starting_after"] = starting_after
            response = stripe.Subscription.list(**params)
            stripe_subs.extend(response.data)
            has_more = response.has_more
            if response.data:
                starting_after = response.data[-1].id

        logger.info(f"Reconciliation: fetched {len(stripe_subs)} Stripe subscriptions")

        # 2. Build lookup: stripe_subscription_id → local DB row
        all_local = (
            sb.table("user_subscriptions")
            .select("id, user_id, plan_id, billing_period, subscription_status, "
                    "is_active, expires_at, stripe_subscription_id, stripe_customer_id")
            .not_.is_("stripe_subscription_id", "null")
            .execute()
        )
        local_by_stripe_id: dict[str, dict] = {}
        for row in (all_local.data or []):
            sid = row.get("stripe_subscription_id")
            if sid:
                local_by_stripe_id[sid] = row

        # 3. Compare each Stripe subscription with local DB
        for stripe_sub in stripe_subs:
            total_checked += 1
            stripe_sub_id = stripe_sub.id
            stripe_status = stripe_sub.status
            mapped_status = _STRIPE_STATUS_MAP.get(stripe_status, stripe_status)
            stripe_is_active = stripe_status in ("active", "trialing", "past_due")
            stripe_billing_period = _determine_billing_period(stripe_sub)
            stripe_plan_id = _determine_plan_id(stripe_sub)

            local = local_by_stripe_id.get(stripe_sub_id)

            if not local:
                # AC3: Orphan subscription — exists in Stripe but not in DB
                orphan_detail = await _handle_orphan(
                    sb, stripe_sub, stripe_key, mapped_status, stripe_is_active,
                    stripe_billing_period, stripe_plan_id
                )
                details.append(orphan_detail)
                if orphan_detail.get("action_taken") == "created":
                    auto_fixed += 1
                else:
                    manual_review += 1
                RECONCILIATION_DIVERGENCES.labels(
                    field="orphan", direction="stripe_ahead"
                ).inc()
                continue

            # Check each field for divergence
            user_id = local["user_id"]
            local_id = local["id"]

            # Skip pending_payment (Boleto/PIX waiting for async confirmation)
            if local.get("subscription_status") == "pending_payment":
                continue

            field_checks = [
                (
                    "is_active",
                    stripe_is_active,
                    local.get("is_active"),
                    "stripe_ahead" if stripe_is_active else "db_ahead",
                ),
                (
                    "subscription_status",
                    mapped_status,
                    local.get("subscription_status"),
                    "stripe_ahead",
                ),
                (
                    "billing_period",
                    stripe_billing_period,
                    local.get("billing_period"),
                    "stripe_ahead",
                ),
            ]

            # Only check plan_id if Stripe metadata has it
            if stripe_plan_id:
                field_checks.append((
                    "plan_id",
                    stripe_plan_id,
                    local.get("plan_id"),
                    "stripe_ahead",
                ))

            updates: dict = {}
            for field_name, stripe_val, db_val, direction in field_checks:
                if stripe_val != db_val:
                    detail = {
                        "user_id": mask_user_id(user_id),
                        "stripe_subscription_id": stripe_sub_id[:12] + "***",
                        "field": field_name,
                        "stripe_value": stripe_val,
                        "db_value": db_val,
                        "direction": direction,
                        "action_taken": "auto_fix",
                    }
                    details.append(detail)
                    updates[field_name] = stripe_val
                    logger.info(
                        f"Reconciliation divergence: {detail}"
                    )
                    RECONCILIATION_DIVERGENCES.labels(
                        field=field_name, direction=direction
                    ).inc()

            if updates:
                # AC2: Auto-fix — update DB to match Stripe
                sb.table("user_subscriptions").update(updates).eq(
                    "id", local_id
                ).execute()
                auto_fixed += 1
                RECONCILIATION_FIXES.inc()

                # Sync profiles.plan_type (existing pattern)
                plan_to_sync = updates.get("plan_id") or local.get("plan_id")
                if not stripe_is_active:
                    plan_to_sync = "free_trial"
                sb.table("profiles").update(
                    {"plan_type": plan_to_sync}
                ).eq("id", user_id).execute()

                # Invalidate Redis cache
                try:
                    await redis_cache.delete(f"features:{user_id}")
                except Exception as cache_err:
                    logger.debug(f"Cache invalidation failed (non-fatal): {cache_err}")

        # 4. AC4: Detect zombie subscriptions — active in DB but not in Stripe
        stripe_sub_ids = {s.id for s in stripe_subs}
        for stripe_sub_id, local in local_by_stripe_id.items():
            if stripe_sub_id not in stripe_sub_ids and local.get("is_active"):
                user_id = local["user_id"]
                detail = {
                    "user_id": mask_user_id(user_id),
                    "stripe_subscription_id": stripe_sub_id[:12] + "***",
                    "field": "zombie",
                    "stripe_value": "not_found",
                    "db_value": "active",
                    "direction": "db_ahead",
                    "action_taken": "auto_fix",
                }
                details.append(detail)
                logger.warning(f"Reconciliation zombie: {detail}")

                # Deactivate zombie
                sb.table("user_subscriptions").update(
                    {"is_active": False, "subscription_status": "canceled"}
                ).eq("id", local["id"]).execute()

                sb.table("profiles").update(
                    {"plan_type": "free_trial"}
                ).eq("id", user_id).execute()

                try:
                    await redis_cache.delete(f"features:{user_id}")
                except Exception:
                    pass

                auto_fixed += 1
                RECONCILIATION_FIXES.inc()
                RECONCILIATION_DIVERGENCES.labels(
                    field="zombie", direction="db_ahead"
                ).inc()

    except Exception as e:
        logger.error(f"Reconciliation error: {e}", exc_info=True)
        details.append({"error": str(e), "action_taken": "error"})

    elapsed_ms = int((time.monotonic() - start) * 1000)
    RECONCILIATION_RUNS.inc()
    RECONCILIATION_DURATION.observe(elapsed_ms / 1000)

    result = {
        "total_checked": total_checked,
        "divergences_found": len(details),
        "auto_fixed": auto_fixed,
        "manual_review": manual_review,
        "duration_ms": elapsed_ms,
        "details": details,
    }

    logger.info(
        f"Reconciliation complete: checked={total_checked}, "
        f"divergences={len(details)}, fixed={auto_fixed}, "
        f"manual={manual_review}, duration={elapsed_ms}ms"
    )

    return result


async def _handle_orphan(
    sb,
    stripe_sub: stripe.Subscription,
    stripe_key: str,
    mapped_status: str,
    stripe_is_active: bool,
    billing_period: str,
    plan_id: str | None,
) -> dict:
    """Handle orphan subscription — exists in Stripe but not in DB.

    AC3: If customer email matches a profile, create the subscription row.
    Otherwise, log for manual investigation.
    """
    customer_id = stripe_sub.get("customer")
    stripe_sub_id = stripe_sub.id

    # Try to resolve customer email → user_id
    user_id = None
    try:
        customer = stripe.Customer.retrieve(customer_id, api_key=stripe_key)
        customer_email = customer.get("email", "")
        if customer_email:
            profile_result = (
                sb.table("profiles")
                .select("id")
                .eq("email", customer_email)
                .limit(1)
                .execute()
            )
            if profile_result.data:
                user_id = profile_result.data[0]["id"]
    except Exception as e:
        logger.debug(f"Orphan customer lookup failed: {e}")

    if not user_id:
        logger.warning(
            f"Orphan subscription {stripe_sub_id[:12]}*** — "
            f"no matching profile for customer {str(customer_id)[:12]}***"
        )
        return {
            "stripe_subscription_id": stripe_sub_id[:12] + "***",
            "field": "orphan",
            "stripe_value": mapped_status,
            "db_value": "not_found",
            "direction": "stripe_ahead",
            "action_taken": "manual_review",
        }

    # Create subscription row
    plan_result = sb.table("plans").select("duration_days, max_searches").eq(
        "id", plan_id or "smartlic_pro"
    ).limit(1).execute()
    duration_days = 30
    max_searches = 1000
    if plan_result.data:
        duration_days = plan_result.data[0].get("duration_days", 30) or 30
        max_searches = plan_result.data[0].get("max_searches", 1000) or 1000

    expires_at = None
    if stripe_is_active:
        current_period_end = stripe_sub.get("current_period_end")
        if current_period_end:
            expires_at = datetime.fromtimestamp(
                current_period_end, tz=timezone.utc
            ).isoformat()
        else:
            expires_at = (
                datetime.now(timezone.utc) + timedelta(days=duration_days)
            ).isoformat()

    sb.table("user_subscriptions").insert({
        "user_id": user_id,
        "plan_id": plan_id or "smartlic_pro",
        "billing_period": billing_period,
        "credits_remaining": max_searches if stripe_is_active else 0,
        "expires_at": expires_at,
        "stripe_subscription_id": stripe_sub_id,
        "stripe_customer_id": customer_id,
        "is_active": stripe_is_active,
        "subscription_status": mapped_status,
    }).execute()

    # Sync profiles.plan_type
    if stripe_is_active:
        sb.table("profiles").update(
            {"plan_type": plan_id or "smartlic_pro"}
        ).eq("id", user_id).execute()

    logger.info(
        f"Orphan subscription {stripe_sub_id[:12]}*** — "
        f"created for user {mask_user_id(user_id)}"
    )

    return {
        "user_id": mask_user_id(user_id),
        "stripe_subscription_id": stripe_sub_id[:12] + "***",
        "field": "orphan",
        "stripe_value": mapped_status,
        "db_value": "not_found",
        "direction": "stripe_ahead",
        "action_taken": "created",
    }


async def save_reconciliation_report(result: dict) -> None:
    """AC8: Save reconciliation report to reconciliation_log table."""
    try:
        sb = get_supabase()
        sb.table("reconciliation_log").insert({
            "total_checked": result["total_checked"],
            "divergences_found": result["divergences_found"],
            "auto_fixed": result["auto_fixed"],
            "manual_review": result["manual_review"],
            "duration_ms": result["duration_ms"],
            "details": result["details"],
        }).execute()
        logger.info("Reconciliation report saved to reconciliation_log")
    except Exception as e:
        logger.error(f"Failed to save reconciliation report: {e}")


async def send_reconciliation_alert(result: dict) -> None:
    """AC9: Send email alert to admin if divergences > 0."""
    if result["divergences_found"] == 0:
        return

    try:
        from email_service import send_email_async
        from templates.emails.base import email_base

        admin_email = os.getenv("ADMIN_ALERT_EMAIL", "tiago.sasaki@gmail.com")

        body = f'''
        <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">
            Reconciliacao Stripe — {result["divergences_found"]} divergencia(s)
        </h1>
        <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Verificados</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{result["total_checked"]}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Divergencias</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{result["divergences_found"]}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Auto-corrigidas</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{result["auto_fixed"]}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Revisao manual</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{result["manual_review"]}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Duracao</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{result["duration_ms"]}ms</td>
            </tr>
        </table>
        <p style="color: #555; font-size: 14px;">
            Detalhes completos no admin dashboard: /admin → Reconciliacao
        </p>
        '''
        html = email_base(
            title="Reconciliacao Stripe — SmartLic",
            body_html=body,
            is_transactional=True,
        )
        send_email_async(
            to=admin_email,
            subject=f"[SmartLic] Reconciliacao: {result['divergences_found']} divergencia(s)",
            html=html,
            tags=[{"name": "category", "value": "reconciliation_alert"}],
        )
        logger.info(f"Reconciliation alert sent to {admin_email}")
    except Exception as e:
        logger.warning(f"Failed to send reconciliation alert: {e}")
