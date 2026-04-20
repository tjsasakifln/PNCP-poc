"""
Invoice/payment webhook handlers.

Events:
- invoice.payment_succeeded (renewal + dunning recovery — STORY-309 AC11)
- invoice.payment_failed (dunning email — STORY-309 AC3)
- invoice.payment_action_required (3D Secure / SCA — STORY-309 AC10)
"""

import stripe
from datetime import datetime, timezone, timedelta

from log_sanitizer import get_sanitized_logger
from webhooks.handlers._shared import invalidate_user_caches

logger = get_sanitized_logger(__name__)


async def handle_invoice_payment_succeeded(sb, event: stripe.Event) -> None:
    """
    Handle invoice.payment_succeeded event (renewal).

    Extends subscription expiry and syncs profiles.plan_type.
    STORY-309 AC11: Detects dunning recovery and sends recovery email.
    """
    invoice_data = event.data.object
    subscription_id = invoice_data.get("subscription")

    if not subscription_id:
        logger.debug("Invoice has no subscription_id, skipping")
        return

    logger.info(f"Invoice paid: subscription_id={subscription_id}")

    sub_result = (
        sb.table("user_subscriptions")
        .select("id, user_id, plan_id")
        .eq("stripe_subscription_id", subscription_id)
        .limit(1)
        .execute()
    )

    if not sub_result.data:
        logger.warning(f"No local subscription for invoice stripe_sub {subscription_id[:8]}***")
        return

    local_sub = sub_result.data[0]
    user_id = local_sub["user_id"]
    plan_id = local_sub["plan_id"]

    # Get plan duration for new expiry
    plan_result = sb.table("plans").select("duration_days").eq("id", plan_id).single().execute()
    duration_days = plan_result.data["duration_days"] if plan_result.data else 30

    new_expires = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()

    # STORY-309 AC11 + STORY-CONV-003c AC3: Detect prior status to branch the
    # post-charge path — dunning recovery email vs welcome_to_pro (first charge
    # after trial) vs standard renewal confirmation — and to emit the
    # trial_converted_auto analytics event when applicable.
    was_past_due = False
    was_trialing = False
    try:
        profile_check = sb.table("profiles").select("subscription_status").eq("id", user_id).single().execute()
        prior_status = (profile_check.data or {}).get("subscription_status")
        if prior_status == "past_due":
            was_past_due = True
        elif prior_status == "trialing":
            was_trialing = True
    except Exception as e:
        logger.warning(f"Failed to check prior subscription status for user_id={user_id}: {e}")

    # Reactivate, extend, and clear dunning state (first_failed_at -> None)
    sb.table("user_subscriptions").update({
        "is_active": True,
        "expires_at": new_expires,
        "subscription_status": "active",
        "first_failed_at": None,
    }).eq("id", local_sub["id"]).execute()

    # Sync profiles.plan_type AND subscription_status (keeps fallback current)
    sb.table("profiles").update({
        "plan_type": plan_id,
        "subscription_status": "active",
    }).eq("id", user_id).execute()

    await invalidate_user_caches(user_id, f"Annual renewal processed, new_expires={new_expires[:10]}")

    # STORY-225 AC12 + STORY-CONV-003c AC3: Send confirmation email.
    # Trial→paid conversion uses `welcome_to_pro` (first charge after
    # trial); renewals use the generic `payment_confirmation` template.
    _send_payment_confirmation_email(
        sb,
        user_id,
        plan_id,
        invoice_data,
        new_expires,
        is_first_charge_after_trial=was_trialing,
    )

    # STORY-309 AC11: Send recovery email if was in dunning
    if was_past_due:
        try:
            from services.dunning import send_recovery_email
            await send_recovery_email(user_id, plan_id)
        except Exception as e:
            logger.warning(f"Failed to send dunning recovery email for user_id={user_id}: {e}")

    # STORY-CONV-003c AC3: Trial→Active transition observability event.
    # First successful charge after a 14-day trial with card — the *conversion*
    # moment for CONV-003 funnel. Pipe via log-sink to Mixpanel.
    if was_trialing:
        amount_paid_cents = invoice_data.get("amount_paid", 0) or 0
        logger.info(
            "analytics.trial_converted_auto",
            extra={
                "event": "trial_converted_auto",
                "user_id": user_id,
                "plan_id": plan_id,
                "amount_brl": round(amount_paid_cents / 100, 2),
                "stripe_subscription_id": subscription_id,
            },
        )


async def handle_invoice_payment_failed(sb, event: stripe.Event) -> None:
    """
    Handle invoice.payment_failed event (GTM-FIX-007 Track 1 AC2-AC5, AC15).

    Updates subscription status to past_due, logs to Sentry, sends dunning email.
    """
    invoice_data = event.data.object
    stripe_customer_id = invoice_data.get("customer")
    stripe_subscription_id = invoice_data.get("subscription")

    if not stripe_subscription_id:
        logger.debug("Invoice payment failed has no subscription_id, skipping")
        return

    logger.warning(
        f"Payment failed: subscription_id={stripe_subscription_id}, "
        f"customer={stripe_customer_id[:8] if stripe_customer_id else 'unknown'}***"
    )

    # Find subscription to get user_id and plan
    sub_result = (
        sb.table("user_subscriptions")
        .select("id, user_id, plan_id")
        .eq("stripe_subscription_id", stripe_subscription_id)
        .limit(1)
        .execute()
    )

    if not sub_result.data:
        logger.warning(f"No local subscription for failed payment stripe_sub {stripe_subscription_id[:8]}***")
        return

    local_sub = sub_result.data[0]
    user_id = local_sub["user_id"]
    plan_id = local_sub["plan_id"]

    # Extract attempt count and decline details (STORY-309 AC3)
    attempt_count = invoice_data.get("attempt_count", 1)
    amount = invoice_data.get("amount_due", 0)

    charge = invoice_data.get("charge") or {}
    decline_type = "soft"
    decline_code = ""
    if isinstance(charge, dict):
        outcome = charge.get("outcome") or {}
        if isinstance(outcome, dict) and outcome.get("type") == "blocked":
            decline_type = "hard"
        decline_code = charge.get("decline_code", "") or charge.get("failure_code", "") or ""

    # Set first_failed_at on first failure, update status to past_due (STORY-309 AC7)
    if attempt_count <= 1:
        sb.table("user_subscriptions").update({
            "subscription_status": "past_due",
            "first_failed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", local_sub["id"]).is_("first_failed_at", "null").execute()
    else:
        sb.table("user_subscriptions").update({
            "subscription_status": "past_due",
        }).eq("id", local_sub["id"]).execute()

    # Also update profiles.subscription_status
    sb.table("profiles").update({
        "subscription_status": "past_due",
    }).eq("id", user_id).execute()

    # Log to Sentry with customer context (AC4)
    try:
        import sentry_sdk
        sentry_sdk.capture_message(
            f"Payment failed: user_id={user_id}, plan={plan_id}, attempt={attempt_count}",
            level="warning",
            extras={
                "user_id": user_id,
                "plan_id": plan_id,
                "stripe_customer_id": stripe_customer_id,
                "stripe_subscription_id": stripe_subscription_id,
                "attempt_count": attempt_count,
                "amount_due": amount,
                "decline_type": decline_type,
                "decline_code": decline_code,
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send Sentry event: {e}")

    # AC15: Track payment failed event
    logger.info(
        "payment_failed_event",
        extra={
            "event": "payment_failed",
            "user_id": user_id,
            "plan": plan_id,
            "amount": amount / 100,  # Convert cents to BRL
            "attempt_count": attempt_count,
            "decline_type": decline_type,
            "decline_code": decline_code,
        }
    )

    # STORY-309 AC3: Send dunning email via dunning service
    try:
        from services.dunning import send_dunning_email
        await send_dunning_email(user_id, attempt_count, invoice_data, decline_type)
    except Exception as e:
        logger.warning(f"Failed to send dunning email for user_id={user_id}: {e}")

    logger.info(f"Payment failed handling complete: user_id={user_id}, status=past_due, decline_type={decline_type}")


async def handle_payment_action_required(sb, event: stripe.Event) -> None:
    """Handle invoice.payment_action_required event (STORY-309 AC10).

    Sent when payment requires 3D Secure / SCA authentication.
    """
    invoice_data = event.data.object
    stripe_subscription_id = invoice_data.get("subscription")

    if not stripe_subscription_id:
        return

    # Find user
    sub_result = (
        sb.table("user_subscriptions")
        .select("id, user_id, plan_id")
        .eq("stripe_subscription_id", stripe_subscription_id)
        .limit(1)
        .execute()
    )
    if not sub_result.data:
        logger.warning(
            f"No local subscription for payment_action_required: "
            f"stripe_sub={stripe_subscription_id[:8]}***"
        )
        return

    user_id = sub_result.data[0]["user_id"]

    # Extract hosted_invoice_url for 3DS completion
    hosted_url = invoice_data.get("hosted_invoice_url", "")

    logger.info(
        f"Payment action required (3DS/SCA): user_id={user_id}, "
        f"stripe_sub={stripe_subscription_id[:8]}***, has_hosted_url={bool(hosted_url)}"
    )

    _send_payment_action_required_email(sb, user_id, hosted_url)


# ============================================================================
# Email helpers (fire-and-forget)
# ============================================================================

def _send_payment_confirmation_email(
    sb,
    user_id: str,
    plan_id: str,
    invoice_data: dict,
    new_expires: str,
    *,
    is_first_charge_after_trial: bool = False,
) -> None:
    """Send payment confirmation email (AC12 + CONV-003c AC3). Never raises.

    ``is_first_charge_after_trial`` selects the welcome-to-pro template
    (lifecycle-aware copy) over the generic renewal confirmation. The
    trial→paid moment is where chargebacks cluster for SaaS — explicit
    acknowledgement of what the user is paying for reduces "eu não sabia
    que ia cobrar" tickets.
    """
    try:
        from email_service import send_email_async
        from templates.emails.billing import (
            render_payment_confirmation_email,
            render_welcome_to_pro_email,
        )
        from quota import PLAN_NAMES

        profile = sb.table("profiles").select("email, full_name").eq("id", user_id).single().execute()
        if not profile.data or not profile.data.get("email"):
            return

        email = profile.data["email"]
        name = profile.data.get("full_name") or email.split("@")[0]
        plan_name = PLAN_NAMES.get(plan_id, plan_id)

        # Format amount from Stripe (cents -> BRL)
        amount_cents = invoice_data.get("amount_paid", 0)
        amount = f"R$ {amount_cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # Determine billing period
        billing_period = "mensal"
        lines = invoice_data.get("lines", {}).get("data", [])
        if lines:
            interval = lines[0].get("plan", {}).get("interval", "month")
            interval_count = lines[0].get("plan", {}).get("interval_count", 1)
            if interval == "year":
                billing_period = "anual"
            elif interval == "month" and interval_count == 6:
                billing_period = "semestral"
            else:
                billing_period = "mensal"

        # Format renewal date
        try:
            from datetime import datetime
            renewal_dt = datetime.fromisoformat(new_expires.replace("Z", "+00:00"))
            renewal_date = renewal_dt.strftime("%d/%m/%Y")
        except Exception:
            renewal_date = new_expires[:10]

        if is_first_charge_after_trial:
            html = render_welcome_to_pro_email(
                user_name=name,
                plan_name=plan_name,
                amount=amount,
                next_renewal_date=renewal_date,
                billing_period=billing_period,
            )
            subject = f"Bem-vindo ao SmartLic Pro — {plan_name}"
            category = "welcome_to_pro"
        else:
            html = render_payment_confirmation_email(
                user_name=name,
                plan_name=plan_name,
                amount=amount,
                next_renewal_date=renewal_date,
                billing_period=billing_period,
            )
            subject = f"Pagamento confirmado — {plan_name}"
            category = "payment_confirmation"
        send_email_async(
            to=email,
            subject=subject,
            html=html,
            tags=[{"name": "category", "value": category}],
        )
        logger.info(
            "Confirmation email queued (user_id=%s, category=%s)",
            user_id,
            category,
        )
    except Exception as e:
        logger.warning(f"Failed to send payment confirmation email: {e}")


def _send_payment_action_required_email(sb, user_id: str, hosted_url: str) -> None:
    """Send 3D Secure authentication required email (STORY-309 AC10). Never raises."""
    try:
        from email_service import send_email_async
        from templates.emails.base import email_base, FRONTEND_URL

        profile = sb.table("profiles").select("email, full_name").eq("id", user_id).single().execute()
        if not profile.data or not profile.data.get("email"):
            return

        email = profile.data["email"]
        name = profile.data.get("full_name") or email.split("@")[0]

        action_url = hosted_url or f"{FRONTEND_URL}/conta"
        body = f'''
        <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">Autenticação necessária para pagamento</h1>
        <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
          Olá, {name}! Seu banco requer uma autenticação adicional (3D Secure) para processar o pagamento da sua assinatura SmartLic.
        </p>
        <p style="text-align: center; margin: 24px 0 16px;">
          <a href="{action_url}" class="btn" style="display: inline-block; padding: 14px 32px; background-color: #2E7D32; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">Completar Autenticação</a>
        </p>
        <p style="color: #888; font-size: 14px; line-height: 1.6; margin: 24px 0 0;">Basta clicar no botão acima e seguir as instruções do seu banco.</p>
        '''
        html = email_base(title="Autenticação necessária — SmartLic", body_html=body, is_transactional=True)
        send_email_async(
            to=email,
            subject="Autenticação necessária para pagamento — SmartLic",
            html=html,
            tags=[{"name": "category", "value": "payment_action_required"}],
        )
        logger.info(f"Payment action required email queued for user_id={user_id}")
    except Exception as e:
        logger.warning(f"Failed to send payment action required email: {e}")


def _send_payment_failed_email(sb, user_id: str, plan_id: str, invoice_data: dict) -> None:
    """Send payment failed email (GTM-FIX-007 AC5-AC6). Never raises. Kept for backward compatibility."""
    try:
        from email_service import send_email_async
        from templates.emails.billing import render_payment_failed_email
        from quota import PLAN_NAMES

        profile = sb.table("profiles").select("email, full_name").eq("id", user_id).single().execute()
        if not profile.data or not profile.data.get("email"):
            return

        email = profile.data["email"]
        name = profile.data.get("full_name") or email.split("@")[0]
        plan_name = PLAN_NAMES.get(plan_id, plan_id)

        # Format amount from Stripe (cents -> BRL)
        amount_cents = invoice_data.get("amount_due", 0)
        amount = f"R$ {amount_cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # Extract failure reason
        failure_reason = "Não foi possível processar o pagamento"
        if invoice_data.get("charge"):
            charge = invoice_data.get("charge")
            if isinstance(charge, str):
                pass
            elif isinstance(charge, dict):
                failure_message = charge.get("failure_message", "")
                if failure_message:
                    failure_reason = failure_message

        # Extract next attempt info
        attempt_count = invoice_data.get("attempt_count", 1)
        days_until_cancellation = max(0, 14 - (attempt_count * 3))

        html = render_payment_failed_email(
            user_name=name,
            plan_name=plan_name,
            amount=amount,
            failure_reason=failure_reason,
            days_until_cancellation=days_until_cancellation,
        )
        send_email_async(
            to=email,
            subject="Falha no pagamento — SmartLic",
            html=html,
            tags=[{"name": "category", "value": "payment_failed"}],
        )
        logger.info(f"Payment failed email queued for user_id={user_id}")
    except Exception as e:
        logger.warning(f"Failed to send payment failed email: {e}")
