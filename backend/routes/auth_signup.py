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
from saas_commerce import require_saas_commerce
from pydantic import BaseModel, EmailStr, Field

from rate_limiter import (
    AUTH_RATE_LIMIT_PER_5MIN,
    require_rate_limit,
    SIGNUP_RATE_LIMIT_PER_10MIN,
)
from schemas.common import validate_password
from schemas.user import SignupRequest, SignupResponse
from services.stripe_signup import (
    StripeSignupError,
    create_customer_and_subscription,
)
from utils.disposable_emails import is_disposable_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth-signup"])

# MFA-EXT-001: brute-force trigger threshold + grace window.
BRUTEFORCE_FAIL_THRESHOLD = 3
BRUTEFORCE_FORCE_MFA_DAYS = 7
ATTEMPT_IDLE_RESET_HOURS = 24


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


async def _update_profile_with_stripe(
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
    from supabase_client import sb_execute

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
        await sb_execute(sb.table("profiles").update(updates).eq("id", user_id))
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
    _frozen=Depends(require_saas_commerce),
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

    # CONV-INST-003: Track confirmation email sent event (fire-and-forget, never raises)
    try:
        from analytics_events import track_event
        track_event("email_confirmation_sent", {"user_id": user_id, "source": "signup"})
    except Exception:  # noqa: BLE001
        pass

    # 2. No card → legacy trial path. Compute local trial_end and return.
    if not body.stripe_payment_method_id:
        await _update_profile_with_stripe(
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
        try:
            from analytics_events import track_event
            track_event("trial_created", {
                "user_id": user_id,
                "rollout_branch": "legacy",
                "source": body.source,
                "ref": body.ref,
                "email_domain": email.split("@")[1] if "@" in email else None,
            })
        except Exception:  # noqa: BLE001
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
        await _update_profile_with_stripe(
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

    await _update_profile_with_stripe(
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

    try:
        from analytics_events import track_event
        track_event("trial_created", {
            "user_id": user_id,
            "rollout_branch": "card",
            "source": body.source,
            "ref": body.ref,
            "email_domain": email.split("@")[1] if "@" in email else None,
        })
    except Exception:  # noqa: BLE001
        pass

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


# ─── MFA-EXT-001: brute-force tracking ─────────────────────────────────────────


class LoginAttemptRequest(BaseModel):
    """Frontend reports the outcome of a Supabase signInWithPassword call.

    The endpoint is unauthenticated by design (failures happen before a
    session exists). To avoid leaking user existence, the endpoint always
    returns 200; if the email is unknown we no-op silently.
    """

    email: EmailStr
    success: bool = Field(
        ...,
        description="True if Supabase auth.signInWithPassword resolved with a session.",
    )


class LoginAttemptResponse(BaseModel):
    """Always 200 to avoid email-existence oracle. Body is intentionally bland."""

    ok: bool = True
    force_mfa_triggered: bool = False


async def _resolve_user_id_by_email(sb, email: str) -> Optional[str]:
    """Look up the user_id for an email via the indexed ``profiles.email`` column.

    Returns None on any error or miss so the caller can no-op silently —
    never raises (avoids user-existence oracle via timing).

    Async-safe: uses ``sb_execute`` (asyncio.to_thread wrapper) to keep the
    event loop free, matching the resilience pattern from the 2026-04-27
    outage cycle (memory project_backend_outage_2026_04_27 — sync
    ``.execute()`` inside async handlers wedged the worker).

    Replaces the previous ``sb.auth.admin.list_users()`` call which:
      * returned at most ``per_page=50`` users by default — silently
        bypassing the bruteforce shield for any user not in the first 50;
      * was synchronous and blocked the event loop on every login attempt.

    Trade-off: queries ``profiles.email`` (mirrored from auth.users via
    the ``handle_new_user`` trigger). Users whose trigger silently failed
    (rare orphan auth.users rows — see PR #696 / memory
    feedback_secdef_search_path_trap) will still no-op. This is a strictly
    narrower miss than the previous >50-user silent-skip.
    """
    try:
        from supabase_client import sb_execute
        result = await sb_execute(
            sb.table("profiles")
            .select("id")
            .ilike("email", email)
            .limit(1),
            category="read",
        )
        rows = result.data or []
        if rows:
            return str(rows[0].get("id"))
    except Exception:
        # Don't leak via timing — silent failure is the contract.
        logger.debug("MFA-EXT-001: user lookup failed for login-attempt", exc_info=True)
    return None


def _trigger_mfa_email(user_id: str, email: str, days: int) -> None:
    """Fire-and-forget bruteforce MFA enrollment email."""
    try:
        from email_service import send_email_async
        from templates.emails.mfa_enrollment_required import (
            render_mfa_enrollment_required_email,
        )

        local_part = (email.split("@", 1)[0]) if "@" in email else email
        html = render_mfa_enrollment_required_email(
            user_name=local_part,
            variant="bruteforce",
            grace_days=days,
        )
        send_email_async(
            to=email,
            subject="Atividade suspeita detectada — Configure MFA",
            html=html,
            tags=[
                {"name": "category", "value": "security"},
                {"name": "story", "value": "mfa-ext-001"},
            ],
        )
    except Exception:
        logger.warning(
            "MFA-EXT-001: bruteforce email dispatch failed for user %s",
            user_id[:8],
            exc_info=True,
        )


def _emit_bruteforce_sentry(user_id: str) -> None:
    """Sentry warning ``auth.bruteforce.mfa_forced`` (AC5).

    Dedup fingerprint per-user so repeated trips don't flood the issue
    list. Severity = warning (not error) — this is a security signal,
    not a system failure.
    """
    try:
        import sentry_sdk
    except Exception:
        return
    try:
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("auth.bruteforce", "mfa_forced")
            scope.set_tag("user_id_hash", user_id[:8])
            scope.fingerprint = ["auth.bruteforce.mfa_forced", user_id]
            sentry_sdk.capture_message(
                "auth.bruteforce.mfa_forced",
                level="warning",
            )
    except Exception:
        logger.debug("Sentry warning emit failed", exc_info=True)


@router.post("/login-attempt", response_model=LoginAttemptResponse)
async def record_login_attempt(
    request: Request,
    body: LoginAttemptRequest,
    _rl=Depends(require_rate_limit(AUTH_RATE_LIMIT_PER_5MIN, 300)),
) -> LoginAttemptResponse:
    """MFA-EXT-001 AC5/AC6: track password attempts to drive MFA enforcement.

    Frontend (``AuthProvider``) calls this endpoint immediately after a
    Supabase ``signInWithPassword`` call to report the outcome:

      * ``success=true``  -> reset counter to 0, set ``last_success_at``
      * ``success=false`` -> increment counter; if it crosses
        ``BRUTEFORCE_FAIL_THRESHOLD`` (3), set
        ``profiles.force_mfa_enrollment_until = NOW() + 7d`` and email
        the user.

    Trust model: the endpoint is unauthenticated; an attacker can lie
    about the outcome but gains nothing — self-reported success without
    a real session never produces a forced MFA window. Documented in
    ADR-MFA-EXT-001.

    Always returns 200 (no user-existence oracle).
    """
    email = body.email.lower().strip()

    sb = _get_supabase()
    user_id = await _resolve_user_id_by_email(sb, email)
    if not user_id:
        # Unknown email -> silent no-op. Same response as success path
        # so attackers can't enumerate the user base via timing.
        return LoginAttemptResponse(ok=True, force_mfa_triggered=False)

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    try:
        from supabase_client import sb_execute
    except Exception as e:
        logger.warning("MFA-EXT-001: sb_execute import failed: %s", type(e).__name__)
        return LoginAttemptResponse(ok=True, force_mfa_triggered=False)

    # ----- Success path: reset counter --------------------------------
    if body.success:
        try:
            await sb_execute(
                sb.table("auth_attempts").upsert(
                    {
                        "user_id": user_id,
                        "consecutive_failures": 0,
                        "last_success_at": now_iso,
                    },
                    on_conflict="user_id",
                ),
                category="write",
            )
        except Exception as e:
            logger.warning(
                "MFA-EXT-001: success-path upsert failed for user %s: %s",
                user_id[:8],
                type(e).__name__,
            )
        return LoginAttemptResponse(ok=True, force_mfa_triggered=False)

    # ----- Failure path: increment with 24h idle reset ----------------
    prior_failures = 0
    try:
        existing = await sb_execute(
            sb.table("auth_attempts")
            .select("consecutive_failures, last_failure_at")
            .eq("user_id", user_id)
            .limit(1),
            category="read",
        )
        rows = existing.data or []
        if rows:
            prior_failures = int(rows[0].get("consecutive_failures") or 0)
            last_failure_raw = rows[0].get("last_failure_at")
            if last_failure_raw:
                try:
                    iso_in = (
                        last_failure_raw.replace("Z", "+00:00")
                        if isinstance(last_failure_raw, str)
                        else last_failure_raw.isoformat()
                    )
                    last_dt = datetime.fromisoformat(iso_in)
                    if last_dt.tzinfo is None:
                        last_dt = last_dt.replace(tzinfo=timezone.utc)
                    if (now - last_dt) > timedelta(hours=ATTEMPT_IDLE_RESET_HOURS):
                        prior_failures = 0
                except Exception:
                    # Best-effort 24h-idle reset: if the timestamp is malformed
                    # we leave prior_failures untouched and let the cron
                    # (jobs.cron.auth_cleanup) handle the reset on the next run.
                    pass
    except Exception as e:
        logger.warning(
            "MFA-EXT-001: prior-failures fetch failed for user %s: %s",
            user_id[:8],
            type(e).__name__,
        )

    new_failures = prior_failures + 1
    crosses_threshold = (
        prior_failures < BRUTEFORCE_FAIL_THRESHOLD
        and new_failures >= BRUTEFORCE_FAIL_THRESHOLD
    )

    try:
        await sb_execute(
            sb.table("auth_attempts").upsert(
                {
                    "user_id": user_id,
                    "consecutive_failures": new_failures,
                    "last_failure_at": now_iso,
                },
                on_conflict="user_id",
            ),
            category="write",
        )
    except Exception as e:
        logger.warning(
            "MFA-EXT-001: failure-path upsert failed for user %s: %s",
            user_id[:8],
            type(e).__name__,
        )
        return LoginAttemptResponse(ok=True, force_mfa_triggered=False)

    if not crosses_threshold:
        return LoginAttemptResponse(ok=True, force_mfa_triggered=False)

    # Threshold crossed (transition prior<3 -> new>=3). Skip if user
    # already has MFA — the bruteforce flag is for users *without* MFA.
    try:
        from auth import _user_has_verified_mfa
        if await _user_has_verified_mfa(user_id):
            return LoginAttemptResponse(ok=True, force_mfa_triggered=False)
    except Exception:
        pass  # fall through and still set the window — fail-safe

    force_until = (now + timedelta(days=BRUTEFORCE_FORCE_MFA_DAYS)).isoformat()
    try:
        await sb_execute(
            sb.table("profiles")
            .update({"force_mfa_enrollment_until": force_until})
            .eq("id", user_id),
            category="write",
        )
    except Exception as e:
        logger.warning(
            "MFA-EXT-001: force_mfa write failed for user %s: %s",
            user_id[:8],
            type(e).__name__,
        )
        return LoginAttemptResponse(ok=True, force_mfa_triggered=False)

    _emit_bruteforce_sentry(user_id)
    _trigger_mfa_email(user_id, email, BRUTEFORCE_FORCE_MFA_DAYS)
    logger.info(
        "MFA-EXT-001: bruteforce trigger fired for user %s (failures=%d)",
        user_id[:8],
        new_failures,
    )

    return LoginAttemptResponse(ok=True, force_mfa_triggered=True)
