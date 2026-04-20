"""
Trial Cancel Token Service (STORY-CONV-003c AC2).

JWT-based one-click cancellation tokens for trial subscriptions. Used in
email D-1 warning: user receives email with a signed link; clicking cancels
the trial in 1 click, minimizing chargebacks pre-first-charge.

Tokens are single-purpose (action="cancel_trial"), short-lived (48h default),
and signed with TRIAL_CANCEL_JWT_SECRET. HMAC-SHA256.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from log_sanitizer import get_sanitized_logger

logger = get_sanitized_logger(__name__)


DEFAULT_EXPIRY_HOURS = 48
ACTION_CANCEL_TRIAL = "cancel_trial"


class TrialCancelTokenError(Exception):
    """Raised when token validation fails for any reason."""

    def __init__(self, reason: str, *, user_id: Optional[str] = None):
        super().__init__(reason)
        self.reason = reason
        self.user_id = user_id


def _get_secret() -> str:
    secret = os.getenv("TRIAL_CANCEL_JWT_SECRET", "")
    if not secret:
        # Fall back to the Supabase JWT secret so local dev still works
        # (production MUST set TRIAL_CANCEL_JWT_SECRET explicitly).
        secret = os.getenv("SUPABASE_JWT_SECRET", "")
    if not secret:
        raise TrialCancelTokenError("jwt_secret_missing")
    return secret


def create_cancel_trial_token(
    user_id: str,
    *,
    expiry_hours: int = DEFAULT_EXPIRY_HOURS,
    now: Optional[datetime] = None,
) -> str:
    """
    Sign a token that authorizes cancelling a specific user's trial.

    Args:
        user_id: Supabase profile id (uuid str).
        expiry_hours: TTL in hours (default 48).
        now: Override for tests.

    Returns:
        Compact JWS string.
    """
    if not user_id:
        raise TrialCancelTokenError("user_id_required")

    _now = now or datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "action": ACTION_CANCEL_TRIAL,
        "iat": int(_now.timestamp()),
        "exp": int((_now + timedelta(hours=expiry_hours)).timestamp()),
    }
    secret = _get_secret()
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_cancel_trial_token(
    token: str,
    *,
    now: Optional[datetime] = None,
) -> str:
    """
    Validate a cancel-trial token. Returns the user_id on success.

    Raises TrialCancelTokenError with machine-readable ``reason`` on:
      - token_required (empty)
      - jwt_secret_missing (server misconfigured)
      - expired
      - invalid_signature
      - invalid_payload (missing/incorrect fields)
      - wrong_action (token exists but for a different purpose)
    """
    if not token:
        raise TrialCancelTokenError("token_required")

    secret = _get_secret()

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise TrialCancelTokenError("expired") from exc
    except jwt.InvalidSignatureError as exc:
        raise TrialCancelTokenError("invalid_signature") from exc
    except jwt.InvalidTokenError as exc:
        raise TrialCancelTokenError("invalid_payload") from exc

    action = payload.get("action")
    user_id = payload.get("user_id")

    if action != ACTION_CANCEL_TRIAL:
        raise TrialCancelTokenError("wrong_action", user_id=user_id)
    if not user_id:
        raise TrialCancelTokenError("invalid_payload")

    # Defensive: re-check expiry ourselves so clock-skew tolerance is explicit.
    _now = now or datetime.now(timezone.utc)
    exp = payload.get("exp")
    if exp is not None and int(_now.timestamp()) > int(exp):
        raise TrialCancelTokenError("expired", user_id=user_id)

    return user_id
