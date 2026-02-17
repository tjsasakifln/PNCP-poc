"""Pipeline management routes for STORY-250.

Provides CRUD endpoints for tracking procurement opportunities
through pipeline stages: descoberta → analise → preparando → enviada → resultado.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from auth import require_auth
from supabase_client import get_supabase
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


def _check_pipeline_access(user: dict) -> None:
    """Check if user's plan allows pipeline access (AC12).

    Pipeline is available for maquina and sala_guerra plans.
    Free trial and consultor_agil get upgrade prompt (AC13).
    """
    from quota import check_quota
    from authorization import has_master_access
    import asyncio

    user_id = user["id"]

    # Masters/admins always have access
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                is_master = pool.submit(asyncio.run, has_master_access(user_id)).result()
        else:
            is_master = asyncio.run(has_master_access(user_id))
        if is_master:
            return
    except Exception:
        pass  # Fall through to plan check

    # Check plan capabilities
    quota_info = check_quota(user_id)
    plan_id = quota_info.plan_id

    # Pipeline available for smartlic_pro and legacy plans
    allowed_plans = {"smartlic_pro", "maquina", "sala_guerra"}
    if plan_id not in allowed_plans:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Pipeline de oportunidades disponível para assinantes SmartLic Pro.",
                "error_code": "pipeline_not_available",
                "upgrade_cta": "Assinar SmartLic Pro",
                "suggested_plan": "smartlic_pro",
                "suggested_plan_name": "SmartLic Pro",
                "suggested_plan_price": "R$ 1.999/mês",
            },
        )


@router.post("/pipeline", status_code=201)
async def create_pipeline_item(
    item: PipelineItemCreate,
    user: dict = Depends(require_auth),
):
    """Add a procurement opportunity to the user's pipeline (AC2).

    Returns 409 if the item already exists (UNIQUE constraint on user_id + pncp_id).
    """
    _check_pipeline_access(user)

    user_id = user["id"]
    sb = get_supabase()

    try:
        result = (
            sb.table("pipeline_items")
            .insert({
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
            })
            .execute()
        )

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=500, detail="Falha ao criar item no pipeline.")

        logger.info(f"Pipeline item created for user {mask_user_id(user_id)}: pncp_id={item.pncp_id}")
        return PipelineItemResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "duplicate" in error_msg.lower() or "unique" in error_msg.lower() or "23505" in error_msg:
            raise HTTPException(
                status_code=409,
                detail="Esta licitação já está no seu pipeline.",
            )
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

    Supports filtering by stage and pagination via limit/offset.
    """
    _check_pipeline_access(user)

    user_id = user["id"]
    sb = get_supabase()

    # Validate stage if provided
    if stage and stage not in VALID_STAGES:
        raise HTTPException(
            status_code=422,
            detail=f"Stage inválido: '{stage}'. Valores válidos: {sorted(VALID_STAGES)}",
        )

    try:
        query = (
            sb.table("pipeline_items")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
        )

        if stage:
            query = query.eq("stage", stage)

        result = query.range(offset, offset + limit - 1).execute()

        items = [PipelineItemResponse(**row) for row in (result.data or [])]
        total = result.count if result.count is not None else len(items)

        return PipelineListResponse(items=items, total=total, limit=limit, offset=offset)

    except Exception as e:
        logger.error(f"Error listing pipeline for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar pipeline.")


@router.patch("/pipeline/{item_id}")
async def update_pipeline_item(
    item_id: str,
    update: PipelineItemUpdate,
    user: dict = Depends(require_auth),
):
    """Update stage and/or notes of a pipeline item (AC4).

    Validates that stage is a valid enum value.
    Returns 404 if item doesn't exist or doesn't belong to user.
    """
    _check_pipeline_access(user)

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
        result = (
            sb.table("pipeline_items")
            .update(payload)
            .eq("id", item_id)
            .eq("user_id", user_id)
            .execute()
        )

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

    Returns 404 if item doesn't exist or doesn't belong to user.
    """
    _check_pipeline_access(user)

    user_id = user["id"]
    sb = get_supabase()

    try:
        result = (
            sb.table("pipeline_items")
            .delete()
            .eq("id", item_id)
            .eq("user_id", user_id)
            .execute()
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
    """Get pipeline items with deadlines within 3 days (AC6).

    Returns items where data_encerramento < now() + 3 days
    and stage is NOT in ('enviada', 'resultado').
    """
    _check_pipeline_access(user)

    user_id = user["id"]
    sb = get_supabase()

    try:
        deadline = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

        result = (
            sb.table("pipeline_items")
            .select("*")
            .eq("user_id", user_id)
            .not_.in_("stage", ["enviada", "resultado"])
            .not_.is_("data_encerramento", "null")
            .lte("data_encerramento", deadline)
            .order("data_encerramento", desc=False)
            .execute()
        )

        items = [PipelineItemResponse(**row) for row in (result.data or [])]

        return PipelineAlertsResponse(
            items=items,
            total=len(items),
        )

    except Exception as e:
        logger.error(f"Error fetching pipeline alerts for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar alertas do pipeline.")
