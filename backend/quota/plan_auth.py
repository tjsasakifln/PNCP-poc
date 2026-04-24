"""FastAPI plan-auth dependencies for quota enforcement.

TD-007: Extracted from plan_enforcement.py as part of DEBT-07 module split.
Contains require_active_plan, _require_active_plan_dep, get_active_plan_dependency.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from analytics_events import track_funnel_event
from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)


async def require_active_plan(user: dict) -> dict:
    """FastAPI dependency: ensures user has an active plan (valid trial OR paid subscription).

    STORY-265 AC7: Encapsulates verification of active plan status.
    STORY-265 AC8: Returns HTTP 403 with structured body on expired trial/plan.
    STORY-265 AC9: Read-only endpoints (GET /pipeline, GET /sessions, GET /me)
                   should NOT use this dependency.
    STORY-291 AC4: When Supabase CB is open, allows user through (fail-open).
    STORY-309 AC5: Returns HTTP 402 when user is in dunning grace_period or blocked phase.
    """
    from fastapi import HTTPException
    from authorization import has_master_access
    from supabase_client import CircuitBreakerOpenError
    from quota.plan_enforcement import check_quota

    user_id = user["id"]

    try:
        if await has_master_access(user_id):
            return user
    except CircuitBreakerOpenError:
        logger.warning(
            f"STORY-291 CB OPEN: Bypassing master check for user {mask_user_id(user_id)} (fail-open)"
        )
        return user
    except Exception:
        pass

    try:
        quota_info = await asyncio.to_thread(check_quota, user_id)
    except CircuitBreakerOpenError:
        logger.warning(
            f"STORY-291 CB OPEN: Bypassing plan check for user {mask_user_id(user_id)} (fail-open)"
        )
        return user

    # STORY-309 AC5: Dunning phase enforcement
    _dunning_phase = getattr(quota_info, "dunning_phase", "healthy")
    _days_since_failure = getattr(quota_info, "days_since_failure", None)
    if _dunning_phase == "blocked":
        logger.info(
            "dunning_blocked",
            extra={
                "user_id": mask_user_id(user_id),
                "dunning_phase": "blocked",
                "days_since_failure": _days_since_failure,
                "plan_id": quota_info.plan_id,
            },
        )
        track_funnel_event(
            "paywall_hit",
            user_id=user_id,
            properties={
                "reason": "dunning_blocked",
                "plan_id": quota_info.plan_id,
                "days_since_failure": _days_since_failure,
            },
        )
        raise HTTPException(
            status_code=402,
            detail={
                "error": "dunning_blocked",
                "message": getattr(quota_info, "error_message", "") or "Atualize seu método de pagamento para continuar.",
                "upgrade_url": "/planos",
                "dunning_phase": "blocked",
                "days_since_failure": _days_since_failure,
            },
        )
    elif _dunning_phase == "grace_period":
        logger.info(
            "dunning_grace_period_blocked",
            extra={
                "user_id": mask_user_id(user_id),
                "dunning_phase": "grace_period",
                "days_since_failure": _days_since_failure,
                "plan_id": quota_info.plan_id,
            },
        )
        track_funnel_event(
            "paywall_hit",
            user_id=user_id,
            properties={
                "reason": "dunning_grace_period",
                "plan_id": quota_info.plan_id,
                "days_since_failure": _days_since_failure,
            },
        )
        raise HTTPException(
            status_code=402,
            detail={
                "error": "dunning_grace_period",
                "message": getattr(quota_info, "error_message", "") or "Seu pagamento está pendente. Acesso somente leitura.",
                "upgrade_url": "/planos",
                "dunning_phase": "grace_period",
                "days_since_failure": _days_since_failure,
            },
        )

    if not quota_info.allowed:
        is_trial = quota_info.plan_id == "free_trial"
        error_type = "trial_expired" if is_trial else "plan_expired"

        days_overdue = 0
        if quota_info.trial_expires_at:
            delta = datetime.now(timezone.utc) - quota_info.trial_expires_at
            days_overdue = max(0, delta.days)

        logger.info(
            "trial_blocked",
            extra={
                "user_id": mask_user_id(user_id),
                "error_type": error_type,
                "plan_id": quota_info.plan_id,
                "expired_at": quota_info.trial_expires_at.isoformat() if quota_info.trial_expires_at else None,
                "days_overdue": days_overdue,
            },
        )
        track_funnel_event(
            "paywall_hit",
            user_id=user_id,
            properties={
                "reason": error_type,
                "plan_id": quota_info.plan_id,
                "trial_days_past": days_overdue if is_trial else None,
                "expired_at": quota_info.trial_expires_at.isoformat() if quota_info.trial_expires_at else None,
            },
        )

        raise HTTPException(
            status_code=403,
            detail={
                "error": error_type,
                "message": quota_info.error_message or "Seu acesso expirou. Reative para continuar analisando oportunidades.",
                "upgrade_url": "/planos",
            },
        )

    return user


async def _require_active_plan_dep(user: dict = None) -> dict:
    """Internal: chains require_auth + require_active_plan for use as Depends()."""
    return await require_active_plan(user)


def get_active_plan_dependency():
    """Create a FastAPI dependency that chains require_auth → require_active_plan.

    STORY-265 AC7: Use this on endpoints that must block expired trials.
    STORY-265 AC9: Do NOT use on read-only endpoints.

    Returns:
        A FastAPI Depends-compatible callable.
    """
    from fastapi import Depends
    from auth import require_auth

    async def _dep(user: dict = Depends(require_auth)):
        return await require_active_plan(user)

    return _dep
