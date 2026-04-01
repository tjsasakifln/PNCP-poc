"""Stage 1: ValidateRequest — validate input, check quota, resolve plan.

Extracted from SearchPipeline.stage_validate (DEBT-015 SYS-002).
"""

import asyncio
import logging
import time as sync_time_module
from datetime import datetime, timezone as _tz

import quota
from authorization import get_admin_ids, get_master_quota_info
from cache.manager import get_from_cache as _supabase_get_cache
from search_context import SearchContext
from log_sanitizer import mask_user_id
from fastapi import HTTPException
from pipeline.helpers import _maybe_send_quota_email

logger = logging.getLogger(__name__)


async def stage_validate(pipeline, ctx: SearchContext) -> None:
    """Validate request, check quota, resolve plan capabilities.

    May raise HTTPException (403, 429, 503) — these propagate to the wrapper.
    """

    deps = pipeline.deps

    # Admin/Master detection
    ctx.is_admin, ctx.is_master = await deps.check_user_roles(ctx.user["id"])
    if ctx.user["id"].lower() in get_admin_ids():
        ctx.is_admin = True
        ctx.is_master = True

    # Rate limiting (before quota check)
    if not (ctx.is_admin or ctx.is_master):
        try:
            quick_quota = await asyncio.to_thread(quota.check_quota, ctx.user["id"])
            max_rpm = quick_quota.capabilities.get("max_requests_per_min", 10)
        except Exception as e:
            logger.warning(f"Failed to get rate limit for user {mask_user_id(ctx.user['id'])}: {e}")
            max_rpm = 10

        rate_allowed, retry_after = await deps.rate_limiter.check_rate_limit(ctx.user["id"], max_rpm)

        if not rate_allowed:
            logger.warning(
                f"Rate limit exceeded for user {mask_user_id(ctx.user['id'])}: "
                f"{max_rpm} req/min limit, retry after {retry_after}s"
            )
            raise HTTPException(
                status_code=429,
                detail=f"Limite de requisições excedido ({max_rpm}/min). Aguarde {retry_after} segundos.",
                headers={"Retry-After": str(retry_after)},
            )

        logger.debug(f"Rate limit check passed for user {mask_user_id(ctx.user['id'])}: {max_rpm} req/min")

    # CRIT-002 AC5: Register session BEFORE quota consumption
    try:
        ctx.session_id = await quota.register_search_session(
            user_id=ctx.user["id"],
            sectors=[ctx.request.setor_id],
            ufs=ctx.request.ufs,
            data_inicial=ctx.request.data_inicial,
            data_final=ctx.request.data_final,
            custom_keywords=ctx.request.termos_busca.split(",") if ctx.request.termos_busca else None,
            search_id=ctx.request.search_id,
        )
        if ctx.session_id is None:
            # AC23: Graceful degradation — continue without session tracking
            logger.critical(
                "Failed to register search session — continuing without session tracking"
            )
    except Exception as reg_err:
        # AC23: Registration failure does NOT block search
        logger.critical(
            f"Failed to register search session — continuing without session tracking: {reg_err}"
        )
        ctx.session_id = None

    # GTM-ARCH-001 AC8: Skip quota consumption if already done in POST (async path)
    if ctx.quota_pre_consumed:
        logger.debug(f"ARCH-001: Quota pre-consumed for {mask_user_id(ctx.user['id'])} — skipping quota check")
        ctx.quota_info = await asyncio.to_thread(quota.check_quota, ctx.user["id"])
        return

    # GTM-INFRA-003 AC5-AC8: Check cache BEFORE quota — skip quota if fully cached
    if not (ctx.is_admin or ctx.is_master) and deps.ENABLE_NEW_PRICING:
        try:
            _cache_params = {
                "setor_id": ctx.request.setor_id,
                "ufs": ctx.request.ufs,
                "status": ctx.request.status.value if ctx.request.status else None,
                "modalidades": ctx.request.modalidades,
                "modo_busca": ctx.request.modo_busca if hasattr(ctx.request, "modo_busca") else None,
            }
            _cache_result = await _supabase_get_cache(ctx.user["id"], _cache_params)
            if _cache_result and _cache_result.get("results"):
                # AC5: Cache hit — skip quota consumption entirely
                ctx.from_cache = True
                ctx.quota_info = await asyncio.to_thread(quota.check_quota, ctx.user["id"])
                if not ctx.quota_info.allowed:
                    raise HTTPException(status_code=403, detail=ctx.quota_info.error_message)
                # AC10: Structured log
                from cache.enums import compute_search_hash
                _ph = compute_search_hash(_cache_params)
                logger.info(
                    f"Quota skipped for user {mask_user_id(ctx.user['id'])}: "
                    f"response fully cached (params_hash={_ph[:12]})"
                )
                # AC9: Increment metric
                from metrics import CACHE_QUOTA_SKIPPED
                CACHE_QUOTA_SKIPPED.inc()
                # CRIT-002 AC7: Still mark session as processing
                if ctx.session_id:
                    asyncio.create_task(
                        quota.update_search_session_status(
                            ctx.session_id, status="processing", pipeline_stage="validate"
                        )
                    )
                return
        except HTTPException:
            raise
        except Exception as cache_check_err:
            # Cache check failed — proceed with normal quota flow
            logger.debug(f"INFRA-003: Pre-quota cache check failed (proceeding normally): {cache_check_err}")

    # Quota resolution
    if ctx.is_admin or ctx.is_master:
        role = "ADMIN" if ctx.is_admin else "MASTER"
        logger.info(f"{role} user detected: {mask_user_id(ctx.user['id'])} - bypassing quota check")
        ctx.quota_info = get_master_quota_info(is_admin=ctx.is_admin)
    elif deps.ENABLE_NEW_PRICING:
        logger.debug("New pricing enabled, checking quota and plan capabilities")
        try:
            ctx.quota_info = await asyncio.to_thread(quota.check_quota, ctx.user["id"])

            if not ctx.quota_info.allowed:
                raise HTTPException(status_code=403, detail=ctx.quota_info.error_message)

            # CRIT-050 AC7: Safe .get() access on capabilities dict
            _max_monthly = ctx.quota_info.capabilities.get("max_requests_per_month", 1000)
            allowed, new_quota_used, quota_remaining_after = await asyncio.to_thread(
                quota.check_and_increment_quota_atomic,
                ctx.user["id"],
                _max_monthly,
            )

            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        f"Limite de {_max_monthly} "
                        f"análises mensais atingido. Renova em "
                        f"{ctx.quota_info.quota_reset_date.strftime('%d/%m/%Y')}."
                    )
                )

            ctx.quota_info.quota_used = new_quota_used
            ctx.quota_info.quota_remaining = quota_remaining_after

            # CRIT-002 AC7: Set status='processing' after quota passes
            if ctx.session_id:
                asyncio.create_task(
                    quota.update_search_session_status(
                        ctx.session_id, status="processing", pipeline_stage="validate"
                    )
                )

            # STORY-225 AC10/AC11: Quota email notifications (fire-and-forget)
            # STORY-290-patch: offload sync Supabase query to thread pool
            asyncio.create_task(
                asyncio.to_thread(_maybe_send_quota_email, ctx.user["id"], new_quota_used, ctx.quota_info)
            )
        except HTTPException as http_exc:
            # CRIT-002 AC5: If quota fails after registration, mark session as failed
            if ctx.session_id:
                asyncio.create_task(
                    quota.update_search_session_status(
                        ctx.session_id,
                        status="failed",
                        error_code="quota_exceeded",
                        error_message=str(http_exc.detail)[:500],
                        pipeline_stage="validate",
                        completed_at=datetime.now(_tz.utc).isoformat(),
                        duration_ms=int((sync_time_module.time() - ctx.start_time) * 1000),
                    )
                )
            raise
        except RuntimeError as e:
            logger.error(f"Supabase configuration error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Serviço temporariamente indisponível. Tente novamente em alguns minutos."
            )
        except Exception as e:
            logger.warning(f"Quota check failed (continuing with fallback): {e}")
            ctx.quota_info = quota.create_fallback_quota_info(ctx.user["id"])
    else:
        logger.debug("New pricing disabled, using legacy behavior (no quota limits)")
        ctx.quota_info = quota.create_legacy_quota_info()
