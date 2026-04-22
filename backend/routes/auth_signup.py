"""POST /v1/auth/signup — Backend signup with Stripe trial (STORY-CONV-003a AC1).

Flow:

1. Pydantic validates email + password + optional Stripe PM id.
2. Rate-limit the caller IP (3 req / 10 min) to deter multi-account abuse.
3. Create the Supabase auth user via `auth.admin.create_user` (server-side
   trigger `handle_new_user` populates the `profiles` row).
4. If `stripe_payment_method_id` was provided and the feature is wired up,
   call `services.stripe_signup.create_customer_and_subscription` and
   persist the resulting ids on `profiles` (UPDATE, not INSERT — the
   trigger already created the row).
5. Return `SignupResponse` with `trial_end_ts` (Stripe trial_end when a
   subscription exists; otherwise now + 14d).

Failure policy (STORY-CONV-003a AC2): if Stripe fails AFTER the Supabase
user was created, we log + mark profile `subscription_status='payment_failed'`
and return 200 with `stripe_customer_id=None`. The user can access the app
during the grace period (SUBSCRIPTION_GRACE_DAYS) and billing
reconciliation can retry asynchronously.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from rate_limiter import require_rate_limit, SIGNUP_RATE_LIMIT_PER_10MIN
from schemas.common import validate_password
from schemas.user import SignupRequest, SignupResponse
from services.stripe_signup import (
    StripeSignupError,
    create_customer_and_subscription,
)
from utils.disposable_emails import is_disposable_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth-signup"])


def _compute_local_trial_end_ts(days: int = 14) -> int:
    """Return Unix seconds for now + `days` (fallback when no Stripe sub)."""
    return int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp())


def _get_supabase():
    """Lazy supabase client for test patchability.

    Tests patch ``routes.auth_signup.get_supabase`` per CLAUDE.md testing
    guidance — import inside the function so the patch target exists at
    call time.
    """
    from supabase_client import get_supabase

    return get_supabase()


def _update_profile_with_stripe(
    sb,
    user_id: str,
    *,
    customer_id: Optional[str],
    subscription_id: Optional[str],
    pm_id: Optional[str],
    subscription_status: str,
    company: Optional[str] = None,
) -> None:
    """UPDATE profiles row with Stripe ids. Non-fatal on failure.

    The `handle_new_user` trigger already INSERTed the profile — we just
    patch the Stripe columns. We swallow DB errors so billing recon can
    pick up the divergence later (STORY-314) instead of 500-ing the user.
    """
    updates: dict = {}
    if customer_id is not None:
        updates["stripe_customer_id"] = customer_id
    if subscription_id is not None:
        updates["stripe_subscription_id"] = subscription_id
    if pm_id is not None:
        updates["stripe_default_pm_id"] = pm_id
    if subscription_status:
        updates["subscription_status"] = subscription_status
    if company:
        updates["company"] = company

    if not updates:
        return

    try:
        sb.table("profiles").update(updates).eq("id", user_id).execute()
    except Exception:  # noqa: BLE001 — intentional broad catch
        logger.exception(
            "profiles update failed post-signup (user_id=%s***) — billing recon will retry",
            user_id[:8],
        )


@router.post("/signup", response_model=SignupResponse)
async def signup(
    request: Request,
    body: SignupRequest,
    _rl=Depends(require_rate_limit(SIGNUP_RATE_LIMIT_PER_10MIN, 600)),
) -> SignupResponse:
    """STORY-CONV-003a AC1+AC2+AC3: Signup with optional Stripe trial.

    Returns 200 with `SignupResponse`. Error modes:

    - 400: disposable email domain or weak password.
    - 400: invalid `stripe_payment_method_id` shape (Pydantic regex).
    - 409: email already registered (detected via Supabase error).
    - 500: Supabase auth.create_user failed (NOT Stripe — Stripe fails open).
    """

    email = body.email.lower().strip()

    # Defense-in-depth: frontend already validates, but stop disposable
    # domains here too (MED-SEC-001 pattern in auth_email.py).
    if is_disposable_email(email):
        raise HTTPException(
            status_code=400,
            detail="Este provedor de email não é aceito. Use um email corporativo ou pessoal.",
        )

    is_valid_pw, pw_err = validate_password(body.password)
    if not is_valid_pw:
        raise HTTPException(status_code=400, detail=pw_err)

    sb = _get_supabase()

    # 1. Create the Supabase auth user. The handle_new_user trigger inserts
    #    the matching profiles row synchronously inside the transaction.
    try:
        user_metadata = {}
        if body.full_name:
            user_metadata["full_name"] = body.full_name
        if body.company:
            user_metadata["company"] = body.company

        auth_result = sb.auth.admin.create_user(
            {
                "email": email,
                "password": body.password,
                "email_confirm": False,  # user must confirm via email link
                "user_metadata": user_metadata,
            }
        )
    except Exception as exc:  # noqa: BLE001 — normalize Supabase SDK errors
        message = str(exc).lower()
        if "already" in message or "exists" in message or "duplicate" in message:
            raise HTTPException(
                status_code=409,
                detail="Email já cadastrado. Faça login ou recupere sua senha.",
            ) from exc
        logger.error("Supabase create_user failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Erro ao criar conta. Tente novamente em instantes.",
        ) from exc

    user = getattr(auth_result, "user", None) or auth_result.get("user") if isinstance(auth_result, dict) else getattr(auth_result, "user", None)
    if user is None:
        logger.error("Supabase create_user returned no user object")
        raise HTTPException(status_code=500, detail="Erro ao criar conta.")

    user_id = str(getattr(user, "id", None) or user["id"])

    # Audit (non-blocking). Lazy import so tests can inject a stub
    # (see tests/test_auth_signup_ratelimit.py pattern).
    try:
        import audit

        if hasattr(audit, "log_audit_event"):
            audit.log_audit_event(
                event_type="auth.signup",
                details={
                    "user_id": user_id,
                    "has_payment_method": bool(body.stripe_payment_method_id),
                },
                level="INFO",
            )
    except Exception:  # noqa: BLE001
        logger.debug("Audit log failed for signup", exc_info=True)

    # 2. No card → legacy trial path. Compute local trial_end and return.
    if not body.stripe_payment_method_id:
        _update_profile_with_stripe(
            sb,
            user_id,
            customer_id=None,
            subscription_id=None,
            pm_id=None,
            subscription_status="free_trial",
            company=body.company,
        )
        # STORY-CONV-003c AC4: observability for the legacy branch of the
        # rollout. Used to compute the card-vs-legacy ratio during canário
        # progression (e.g. if PCT=10, card branch should be ~10% of total).
        try:
            from metrics import TRIAL_SIGNUP_WITH_CARD

            TRIAL_SIGNUP_WITH_CARD.labels(branch="legacy").inc()
        except Exception:  # noqa: BLE001 — metrics must never break signup
            pass
        return SignupResponse(
            user_id=user_id,
            email=email,
            trial_end_ts=_compute_local_trial_end_ts(),
            stripe_customer_id=None,
            stripe_subscription_id=None,
            subscription_status="free_trial",
            requires_email_confirmation=True,
        )

    # 3. Card path → Stripe Customer + Subscription with 14d trial.
    try:
        stripe_result = create_customer_and_subscription(
            email=email,
            payment_method_id=body.stripe_payment_method_id,
            user_id=user_id,
        )
    except StripeSignupError as exc:
        # Fail open per AC2 line 33. Still mark profile for recon.
        logger.warning(
            "Stripe signup failed; user %s*** created without subscription (step=%s)",
            user_id[:8],
            exc.step,
        )
        _update_profile_with_stripe(
            sb,
            user_id,
            customer_id=exc.customer_id,  # may be set if failure happened post-customer
            subscription_id=None,
            pm_id=None,
            subscription_status="payment_failed",
            company=body.company,
        )
        return SignupResponse(
            user_id=user_id,
            email=email,
            trial_end_ts=_compute_local_trial_end_ts(),
            stripe_customer_id=exc.customer_id,
            stripe_subscription_id=None,
            subscription_status="payment_failed",
            requires_email_confirmation=True,
        )

    _update_profile_with_stripe(
        sb,
        user_id,
        customer_id=stripe_result["customer_id"],
        subscription_id=stripe_result["subscription_id"],
        pm_id=stripe_result["default_pm_id"],
        subscription_status="trialing",
        company=body.company,
    )

    # STORY-CONV-003c AC4: trial_card_captured observability.
    # Emitted only when the full card path succeeds — Customer + SetupIntent +
    # Subscription all created. This is the "card in file for auto-charge"
    # moment that defines the card rollout branch. Mixpanel via log-sink;
    # Prometheus counter for real-time rollout monitoring.
    try:
        from metrics import TRIAL_SIGNUP_WITH_CARD

        TRIAL_SIGNUP_WITH_CARD.labels(branch="card").inc()
    except Exception:  # noqa: BLE001 — metrics must never break signup
        pass
    logger.info(
        "analytics.trial_card_captured",
        extra={
            "event": "trial_card_captured",
            "user_id": user_id,
            "rollout_branch": "card",
            "stripe_customer_id": stripe_result["customer_id"],
            "stripe_subscription_id": stripe_result["subscription_id"],
        },
    )

    trial_end_ts = stripe_result["trial_end_ts"] or _compute_local_trial_end_ts()

    return SignupResponse(
        user_id=user_id,
        email=email,
        trial_end_ts=trial_end_ts,
        stripe_customer_id=stripe_result["customer_id"],
        stripe_subscription_id=stripe_result["subscription_id"],
        subscription_status="trialing",
        requires_email_confirmation=True,
    )
