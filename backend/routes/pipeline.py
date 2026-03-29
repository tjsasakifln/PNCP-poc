"""Pipeline management routes for STORY-250.

Provides CRUD endpoints for tracking procurement opportunities
through pipeline stages: descoberta -> analise -> preparando -> enviada -> resultado.

SYS-023: GET /pipeline migrated to user-scoped Supabase client as example.
Other endpoints use get_supabase() (admin) because they call internal helpers
(_check_pipeline_write_access, _check_pipeline_limit) that use service-role queries.
Future migration: move remaining endpoints to user-scoped client incrementally.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from auth import require_auth
from supabase_client import get_supabase, sb_execute
from log_sanitizer import mask_user_id
from schemas import (
    PipelineItemCreate,
    PipelineItemResponse,
    PipelineItemUpdate,
    PipelineListResponse,
    PipelineAlertsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pipeline"])

VALID_STAGES = {"descoberta", "analise", "preparando", "enviada", "resultado"}


async def _check_pipeline_read_access(user: dict) -> None:
    """Check if user's plan allows pipeline READ access.

    STORY-265 AC3: Trial expired users can VIEW pipeline (read-only).
    This incentivizes conversion by showing saved opportunities.
    """
    from quota import check_quota
    from authorization import has_master_access

    user_id = user["id"]

    # Masters/admins always have access
    try:
        is_master = await has_master_access(user_id)
        if is_master:
            return
    except Exception as e:
        logger.warning(f"Master access check failed, falling through: {e}")

    # Check plan capabilities
    try:
        quota_info = await asyncio.to_thread(check_quota, user_id)
    except Exception as e:
        # Fail-open for read access: transient quota/DB errors should not block pipeline reads
        logger.warning(
            f"check_quota failed for pipeline read access (fail-open), user={mask_user_id(user_id)}: {e}"
        )
        return
    caps = quota_info.capabilities

    # STORY-265 AC3: Allow read access for expired trials (read-only incentive)
    # Only block if the plan doesn't have pipeline capability at all
    if not caps.get("allow_pipeline", False) and quota_info.allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Pipeline de oportunidades disponível para assinantes SmartLic Pro.",
                "error_code": "pipeline_not_available",
                "upgrade_cta": "Assinar SmartLic Pro",
                "suggested_plan": "smartlic_pro",
                "suggested_plan_name": "SmartLic Pro",
                "suggested_plan_price": "R$ 397/mês",
            },
        )


async def _check_pipeline_write_access(user: dict) -> None:
    """Check if user's plan allows pipeline WRITE access (POST/PATCH/DELETE).

    STORY-265 AC2: Trial expired cannot add/modify/delete pipeline items.
    Uses require_active_plan for trial expiry check, then capability check.
    """
    from quota import require_active_plan, check_quota
    from authorization import has_master_access

    user_id = user["id"]

    # Masters/admins always have access
    try:
        is_master = await has_master_access(user_id)
        if is_master:
            return
    except Exception as e:
        logger.warning(f"Master access check failed, falling through: {e}")

    # STORY-265 AC2: Block expired trials (raises 403 with trial_expired)
    await require_active_plan(user)

    # Check plan capabilities for pipeline access
    quota_info = await asyncio.to_thread(check_quota, user_id)
    caps = quota_info.capabilities

    if not caps.get("allow_pipeline", False):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Pipeline de oportunidades disponível para assinantes SmartLic Pro.",
                "error_code": "pipeline_not_available",
                "upgrade_cta": "Assinar SmartLic Pro",
                "suggested_plan": "smartlic_pro",
                "suggested_plan_name": "SmartLic Pro",
                "suggested_plan_price": "R$ 397/mês",
            },
        )


async def _check_pipeline_limit(user: dict) -> None:
    """STORY-356: Check if user has reached their pipeline item limit.

    Trial users: max TRIAL_PAYWALL_MAX_PIPELINE (5) items.
    Paid users: no limit.
    Masters/admins: no limit.
    """
    from quota import check_quota
    from authorization import has_master_access
    from config import TRIAL_PAYWALL_MAX_PIPELINE

    user_id = user["id"]

    # Masters/admins have no limit
    try:
        is_master = await has_master_access(user_id)
        if is_master:
            return
    except Exception:
        pass

    # Only trial users have a pipeline limit
    quota_info = await asyncio.to_thread(check_quota, user_id)
    if quota_info.plan_id != "free_trial":
        return

    limit = TRIAL_PAYWALL_MAX_PIPELINE

    # Count current items (uses admin client for count query)
    sb = get_supabase()
    result = await sb_execute(
        sb.table("pipeline_items")
        .select("id", count="exact")
        .eq("user_id", user_id)
    )
    current = result.count if result.count is not None else len(result.data or [])

    if current >= limit:
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "PIPELINE_LIMIT_EXCEEDED",
                "limit": limit,
                "current": current,
            },
        )


@router.post("/pipeline", status_code=201)
async def create_pipeline_item(
    item: PipelineItemCreate,
    user: dict = Depends(require_auth),
):
    """Add a procurement opportunity to the user's pipeline (AC2).

    ISSUE-021 fix: Reverted to admin client (get_supabase) — user-scoped client
    caused HTTP 500 due to fragile session header mutation in get_user_db.
    Defense-in-depth: .eq("user_id", user_id) prevents cross-user access.
    STORY-265 AC2: Trial expired cannot add items.
    STORY-356: Enforce pipeline item limit (trial: 5 items max).
    Returns 409 if the item already exists (UNIQUE constraint on user_id + pncp_id).
    """
    await _check_pipeline_write_access(user)
    await _check_pipeline_limit(user)

    user_id = user["id"]

    data = {
        "user_id": user_id,
        "pncp_id": item.pncp_id,
        "objeto": item.objeto,
        "orgao": item.orgao,
        "uf": item.uf,
        "valor_estimado": float(item.valor_estimado) if item.valor_estimado is not None else None,
        "data_encerramento": item.data_encerramento,
        "link_pncp": item.link_pncp,
        "stage": item.stage or "descoberta",
        "notes": item.notes,
        "search_id": item.search_id,
    }

    try:
        # ISSUE-021: Use upsert for idempotent add (avoids 409 on duplicate)
        result = await sb_execute(
            get_supabase().table("pipeline_items")
            .upsert(data, on_conflict="user_id,pncp_id", ignore_duplicates=True)
        )

        if result.data and len(result.data) > 0:
            logger.info(f"Pipeline item created for user {mask_user_id(user_id)}: pncp_id={item.pncp_id}")
            return PipelineItemResponse(**result.data[0])

        # ignore_duplicates returns empty on conflict — fetch existing row
        existing = await sb_execute(
            get_supabase().table("pipeline_items")
            .select("*")
            .eq("user_id", user_id)
            .eq("pncp_id", item.pncp_id)
            .limit(1)
        )
        if existing.data and len(existing.data) > 0:
            logger.info(f"Pipeline item already exists for user {mask_user_id(user_id)}: pncp_id={item.pncp_id}")
            return PipelineItemResponse(**existing.data[0])

        raise HTTPException(status_code=500, detail="Falha ao criar item no pipeline.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating pipeline item for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao adicionar ao pipeline.")


@router.get("/pipeline", response_model=PipelineListResponse)
async def list_pipeline_items(
    stage: Optional[str] = Query(None, description="Filter by stage"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user: dict = Depends(require_auth),
):
    """List pipeline items for the authenticated user (AC3).

    ISSUE-021 fix: Switched to admin client (get_supabase) — user-scoped client
    (get_user_db) had fragile JWT header mutation that silently failed, causing
    PostgREST to evaluate RLS as anonymous user and return 0 rows.
    Defense-in-depth: .eq("user_id", user_id) prevents cross-user access,
    consistent with POST/PATCH/DELETE handlers.

    STORY-265 AC3: Trial expired can VIEW pipeline (read-only).
    Supports filtering by stage and pagination via limit/offset.
    """
    try:
        await _check_pipeline_read_access(user)
    except HTTPException:
        raise
    except Exception as e:
        # Transient error in access check (circuit breaker, DB timeout) — fail-open for reads
        logger.warning(f"Pipeline read access check raised unexpectedly (fail-open), user={mask_user_id(user['id'])}: {e}")

    user_id = user["id"]

    # Validate stage if provided
    if stage and stage not in VALID_STAGES:
        raise HTTPException(
            status_code=422,
            detail=f"Stage inválido: '{stage}'. Valores válidos: {sorted(VALID_STAGES)}",
        )

    try:
        sb = get_supabase()  # ISSUE-021: Admin client, consistent with POST/PATCH/DELETE
        query = (
            sb.table("pipeline_items")
            .select("*", count="exact")
            .eq("user_id", user_id)  # Defense-in-depth: explicit user filter
            .order("updated_at", desc=True)
        )

        if stage:
            query = query.eq("stage", stage)

        result = await sb_execute(query.range(offset, offset + limit - 1))

        items = []
        for row in (result.data or []):
            try:
                items.append(PipelineItemResponse(**row))
            except Exception as row_err:
                # ISSUE-038: Skip malformed rows instead of failing the entire request
                logger.warning(
                    f"Skipping malformed pipeline row for user {mask_user_id(user_id)}: "
                    f"pncp_id={row.get('pncp_id', '?')}, error={row_err}"
                )
        total = result.count if result.count is not None else len(items)

        return PipelineListResponse(items=items, total=total, limit=limit, offset=offset)

    except HTTPException:
        raise
    except Exception as e:
        # ISSUE-038: Distinguish transient DB errors from unexpected failures.
        # For read-only pipeline listing, return empty instead of 500 when
        # Supabase is temporarily unavailable (CB open, timeout, etc.)
        from supabase_client import CircuitBreakerOpenError
        if isinstance(e, CircuitBreakerOpenError):
            logger.warning(
                f"Pipeline list returning empty (CB open) for user {mask_user_id(user_id)}: {e}"
            )
            return PipelineListResponse(items=[], total=0, limit=limit, offset=offset)
        logger.error(f"Error listing pipeline for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar pipeline.")


@router.patch("/pipeline/{item_id}")
async def update_pipeline_item(
    item_id: str,
    update: PipelineItemUpdate,
    user: dict = Depends(require_auth),
):
    """Update stage and/or notes of a pipeline item (AC4).

    ISSUE-021 fix: Reverted to admin client — user-scoped client caused HTTP 500.
    Defense-in-depth: .eq("user_id", user_id) prevents cross-user access.
    STORY-265 AC2: Trial expired cannot modify items.
    Validates that stage is a valid enum value.
    Returns 404 if item doesn't exist or doesn't belong to user.
    """
    await _check_pipeline_write_access(user)

    user_id = user["id"]
    sb = get_supabase()

    # Build update payload (only non-None fields)
    payload = {}
    if update.stage is not None:
        if update.stage not in VALID_STAGES:
            raise HTTPException(
                status_code=422,
                detail=f"Stage inválido: '{update.stage}'. Valores válidos: {sorted(VALID_STAGES)}",
            )
        payload["stage"] = update.stage
    if update.notes is not None:
        payload["notes"] = update.notes

    if not payload:
        raise HTTPException(status_code=422, detail="Nenhum campo para atualizar.")

    try:
        # STORY-307 AC9: Optimistic locking — include version in WHERE clause
        query = (
            sb.table("pipeline_items")
            .update({**payload, "version": sb.table("pipeline_items").version + 1} if False else payload)
            .eq("id", item_id)
            .eq("user_id", user_id)
        )

        if update.version is not None:
            # AC9: WHERE version = $current_version — reject stale updates
            query = (
                sb.table("pipeline_items")
                .update({**payload, "version": update.version + 1})
                .eq("id", item_id)
                .eq("user_id", user_id)
                .eq("version", update.version)
            )
            result = await sb_execute(query)

            # AC10: If 0 rows affected, version mismatch -> 409 Conflict
            if not result.data or len(result.data) == 0:
                # Check if item exists at all (404 vs 409)
                exists = await sb_execute(
                    sb.table("pipeline_items")
                    .select("id, version")
                    .eq("id", item_id)
                    .eq("user_id", user_id)
                )
                if exists.data:
                    raise HTTPException(
                        status_code=409,
                        detail="Item foi atualizado por outra operação. Recarregue a página.",
                    )
                raise HTTPException(
                    status_code=404,
                    detail="Item não encontrado no seu pipeline.",
                )
        else:
            # Legacy path: no version sent (backward compatible)
            result = await sb_execute(query)
            if not result.data or len(result.data) == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Item não encontrado no seu pipeline.",
                )

        logger.info(f"Pipeline item {item_id[:8]}... updated for user {mask_user_id(user_id)}: {list(payload.keys())}")
        return PipelineItemResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating pipeline item {item_id[:8]}... for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar item do pipeline.")


@router.delete("/pipeline/{item_id}", status_code=200)
async def delete_pipeline_item(
    item_id: str,
    user: dict = Depends(require_auth),
):
    """Remove an item from the pipeline (AC5).

    ISSUE-021 fix: Reverted to admin client — user-scoped client caused HTTP 500.
    Defense-in-depth: .eq("user_id", user_id) prevents cross-user access.
    STORY-265 AC2: Trial expired cannot delete items.
    Returns 404 if item doesn't exist or doesn't belong to user.
    """
    await _check_pipeline_write_access(user)

    user_id = user["id"]
    sb = get_supabase()

    try:
        result = await sb_execute(
            sb.table("pipeline_items")
            .delete()
            .eq("id", item_id)
            .eq("user_id", user_id)
        )

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Item não encontrado no seu pipeline.",
            )

        logger.info(f"Pipeline item {item_id[:8]}... deleted for user {mask_user_id(user_id)}")
        return {"success": True, "message": "Item removido do pipeline."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pipeline item {item_id[:8]}... for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao remover item do pipeline.")


@router.get("/pipeline/alerts", response_model=PipelineAlertsResponse)
async def get_pipeline_alerts(
    user: dict = Depends(require_auth),
):
    """Get pipeline items with deadlines within 7 days (DEBT-127 AC1).

    STORY-265 AC3: Trial expired can view alerts (read-only).
    Returns items where data_encerramento < now() + 7 days
    and stage is NOT in ('enviada', 'resultado').
    """
    try:
        await _check_pipeline_read_access(user)
    except HTTPException:
        raise
    except Exception as e:
        # Transient error in access check — fail-open, return empty alerts instead of 500
        logger.warning(f"Pipeline alerts access check raised unexpectedly (fail-open), user={mask_user_id(user['id'])}: {e}")

    user_id = user["id"]
    sb = get_supabase()

    try:
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

        result = await sb_execute(
            sb.table("pipeline_items")
            .select("*")
            .eq("user_id", user_id)
            .not_.in_("stage", ["enviada", "resultado"])
            .not_.is_("data_encerramento", "null")
            .lte("data_encerramento", deadline)
            .order("data_encerramento", desc=False)
        )

        items = [PipelineItemResponse(**row) for row in (result.data or [])]

        return PipelineAlertsResponse(
            items=items,
            total=len(items),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Transient error fetching pipeline alerts for user {mask_user_id(user_id)}, returning empty: {e}")
        return PipelineAlertsResponse(items=[], total=0)
