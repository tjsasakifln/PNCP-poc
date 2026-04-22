"""
Conta — account-management public endpoints (STORY-CONV-003c AC2).

Contains the one-click trial-cancellation flow:
  GET  /v1/conta/cancelar-trial?token=<jwt>  -> returns trial metadata for confirmation UI
  POST /v1/conta/cancelar-trial              -> executes cancellation

Both endpoints are public (token-authenticated only). The JWT carries the
``user_id`` + ``action='cancel_trial'`` claim and expires in 48h by default
(see ``services/trial_cancel_token.py``).

Design notes:
- Stripe trial cancellations do NOT generate proration — user keeps access
  until ``trial_end_ts`` regardless.
- Idempotent: cancelling an already-cancelled subscription is a no-op.
- Fail-safe: Stripe errors are logged but we still mark the profile in a
  sentinel state so the user doesn't get billed.
"""

from __future__ import annotations

import logging
from typing import Optional

import stripe
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from log_sanitizer import get_sanitized_logger, mask_user_id
from services.trial_cancel_token import (
    TrialCancelTokenError,
    verify_cancel_trial_token,
)
from supabase_client import get_supabase

logger = get_sanitized_logger(__name__)
router = APIRouter(prefix="/conta", tags=["conta"])


# ============================================================================
# Response schemas
# ============================================================================


class CancelTrialInfoResponse(BaseModel):
    """Returned by GET /cancelar-trial to populate the confirmation UI."""

    user_id: str
    email: str
    plan_name: str
    trial_end_ts: Optional[int] = Field(
        None, description="Unix epoch seconds when trial ends"
    )
    already_cancelled: bool = False


class CancelTrialRequest(BaseModel):
    token: str = Field(..., min_length=20, description="Signed cancel-trial JWT")


class CancelTrialResponse(BaseModel):
    cancelled: bool
    access_until: Optional[int] = Field(
        None,
        description="Unix epoch seconds — trial access remains until this timestamp",
    )
    already_cancelled: bool = False


# ============================================================================
# Helpers
# ============================================================================


def _error_response_for(reason: str) -> HTTPException:
    """Map token error reason to stable HTTP response. Opaque to avoid leaking why."""
    if reason in ("expired",):
        return HTTPException(
            status_code=410,
            detail={"error": "token_expired", "message": "Link expirado. Gere um novo."},
        )
    if reason in ("invalid_signature", "invalid_payload", "wrong_action", "token_required"):
        return HTTPException(
            status_code=400,
            detail={"error": "token_invalid", "message": "Link inválido."},
        )
    # jwt_secret_missing or unexpected
    return HTTPException(
        status_code=500,
        detail={"error": "server_config", "message": "Erro temporário. Tente novamente."},
    )


def _load_profile_and_subscription(sb, user_id: str) -> tuple[Optional[dict], Optional[dict]]:
    """Fetch profile + active user_subscriptions row (may be None if user deleted)."""
    profile_result = (
        sb.table("profiles")
        .select("id, email, plan_type, subscription_status, stripe_subscription_id")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not profile_result.data:
        return None, None
    profile = profile_result.data[0]

    sub_result = (
        sb.table("user_subscriptions")
        .select("id, plan_id, stripe_subscription_id, is_active, subscription_status")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    subscription = sub_result.data[0] if sub_result.data else None
    return profile, subscription


def _fetch_trial_end_from_stripe(stripe_sub_id: Optional[str]) -> Optional[int]:
    """Best-effort: read trial_end from Stripe. Returns None on any error."""
    if not stripe_sub_id:
        return None
    try:
        sub = stripe.Subscription.retrieve(stripe_sub_id)
        trial_end = sub.get("trial_end") if hasattr(sub, "get") else None
        return int(trial_end) if trial_end else None
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning(f"Failed to retrieve Stripe subscription {stripe_sub_id[:8]}***: {exc}")
        return None


# ============================================================================
# Routes
# ============================================================================


@router.get("/cancelar-trial", response_model=CancelTrialInfoResponse)
def cancel_trial_info(token: str = Query(..., min_length=20)) -> CancelTrialInfoResponse:
    """
    Return trial metadata for the confirmation UI.

    Does NOT mutate state. Intended to be called by the frontend confirmation
    page (STORY-CONV-003c frontend).
    """
    try:
        user_id = verify_cancel_trial_token(token)
    except TrialCancelTokenError as exc:
        logger.info(f"cancel_trial_info: invalid token reason={exc.reason}")
        raise _error_response_for(exc.reason) from exc

    sb = get_supabase()
    profile, subscription = _load_profile_and_subscription(sb, user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail={"error": "user_not_found", "message": "Usuário não encontrado."},
        )

    stripe_sub_id = (subscription or {}).get("stripe_subscription_id") or profile.get(
        "stripe_subscription_id"
    )
    trial_end_ts = _fetch_trial_end_from_stripe(stripe_sub_id)

    subscription_status = (subscription or {}).get("subscription_status") or profile.get(
        "subscription_status", ""
    )
    already_cancelled = subscription_status in ("canceled_trial", "cancelled", "canceled")

    plan_name = (subscription or {}).get("plan_id") or profile.get("plan_type") or "free_trial"

    logger.info(
        f"cancel_trial_info: user={mask_user_id(user_id)} already_cancelled={already_cancelled}"
    )

    return CancelTrialInfoResponse(
        user_id=user_id,
        email=profile.get("email", ""),
        plan_name=plan_name,
        trial_end_ts=trial_end_ts,
        already_cancelled=already_cancelled,
    )


@router.post("/cancelar-trial", response_model=CancelTrialResponse)
def cancel_trial_execute(payload: CancelTrialRequest) -> CancelTrialResponse:
    """
    Cancel the user's active trial subscription.

    Idempotent: if already cancelled, returns ``cancelled=true`` + ``already_cancelled=true``.
    Fail-safe: Stripe errors are swallowed but profile is marked ``canceled_trial``
    so the downgrade still happens if the Stripe-side cancel retries succeed out-of-band
    via billing reconciliation (STORY-314).
    """
    try:
        user_id = verify_cancel_trial_token(payload.token)
    except TrialCancelTokenError as exc:
        logger.info(f"cancel_trial_execute: invalid token reason={exc.reason}")
        raise _error_response_for(exc.reason) from exc

    sb = get_supabase()
    profile, subscription = _load_profile_and_subscription(sb, user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail={"error": "user_not_found", "message": "Usuário não encontrado."},
        )

    subscription_status = (subscription or {}).get("subscription_status") or profile.get(
        "subscription_status", ""
    )
    if subscription_status in ("canceled_trial", "cancelled", "canceled"):
        stripe_sub_id = (subscription or {}).get("stripe_subscription_id") or profile.get(
            "stripe_subscription_id"
        )
        trial_end_ts = _fetch_trial_end_from_stripe(stripe_sub_id)
        logger.info(f"cancel_trial_execute: already cancelled user={mask_user_id(user_id)}")
        return CancelTrialResponse(
            cancelled=True, access_until=trial_end_ts, already_cancelled=True
        )

    stripe_sub_id = (subscription or {}).get("stripe_subscription_id") or profile.get(
        "stripe_subscription_id"
    )

    trial_end_ts: Optional[int] = None

    # 1) Call Stripe.Subscription.cancel — trials do NOT generate proration.
    if stripe_sub_id:
        try:
            cancelled_sub = stripe.Subscription.cancel(stripe_sub_id)
            trial_end_ts = (
                cancelled_sub.get("trial_end")
                if hasattr(cancelled_sub, "get")
                else None
            )
            if trial_end_ts is not None:
                trial_end_ts = int(trial_end_ts)
            logger.info(
                f"Trial cancelled via one-click: user={mask_user_id(user_id)} sub={stripe_sub_id[:8]}***"
            )
        except stripe.error.InvalidRequestError as exc:
            # Already cancelled on Stripe side, proceed with local cleanup
            logger.warning(
                f"Stripe cancel returned InvalidRequestError (likely already cancelled): {exc}"
            )
        except Exception as exc:  # pragma: no cover — best-effort
            logger.error(f"Stripe cancel failed for sub {stripe_sub_id[:8]}***: {exc}")
            # DO NOT raise — local state gets updated below, billing recon handles Stripe retry

    # 2) Update local state (profiles + user_subscriptions).
    try:
        sb.table("profiles").update(
            {
                "subscription_status": "canceled_trial",
                "plan_type": "free_trial",
            }
        ).eq("id", user_id).execute()
    except Exception as exc:
        logger.error(f"Failed to update profiles during trial cancel: {exc}")

    if subscription:
        try:
            sb.table("user_subscriptions").update(
                {"subscription_status": "canceled", "is_active": False}
            ).eq("id", subscription["id"]).execute()
        except Exception as exc:
            logger.error(f"Failed to update user_subscriptions during trial cancel: {exc}")

    # 3) Mixpanel-shaped structured log for CONV-003c AC4 observability.
    logger.info(
        "analytics.trial_cancelled_before_charge",
        extra={
            "event": "trial_cancelled_before_charge",
            "user_id": user_id,
            "trial_end_ts": trial_end_ts,
            "source": "one_click_email",
        },
    )
    # CONV-003c AC4 Prometheus: real-time rollout monitoring.
    try:
        from metrics import TRIAL_CANCEL_BEFORE_CHARGE

        TRIAL_CANCEL_BEFORE_CHARGE.inc()
    except Exception:  # noqa: BLE001 — metrics must never break cancel
        pass

    return CancelTrialResponse(
        cancelled=True, access_until=trial_end_ts, already_cancelled=False
    )
