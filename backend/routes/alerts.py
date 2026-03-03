"""Email alert CRUD routes — STORY-301 Email Alert System.

AC1:  POST   /alerts                    — Create alert
AC2:  GET    /alerts                    — List user's alerts (with sent_count)
AC3:  PATCH  /alerts/{alert_id}         — Edit alert (partial update)
AC4:  DELETE /alerts/{alert_id}         — Delete alert (cascading)
AC9:  GET    /alerts/{alert_id}/unsubscribe — One-click unsubscribe (RFC 8058)
AC13: GET    /alerts/{alert_id}/history — Paginated sent-item history
"""

import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from auth import require_auth
from config import ALERTS_SYSTEM_ENABLED
from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["alerts"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UNSUBSCRIBE_SECRET = os.getenv("UNSUBSCRIBE_SECRET", "smartlic-unsub-default-key")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://smartlic.tech")
MAX_ALERTS_PER_USER = int(os.getenv("MAX_ALERTS_PER_USER", "20"))

# ---------------------------------------------------------------------------
# Pydantic models (inline per codebase convention)
# ---------------------------------------------------------------------------


class AlertFilters(BaseModel):
    """Filter criteria that define which bids match this alert."""
    setor: Optional[str] = Field(None, description="Sector ID from sectors_data.yaml")
    ufs: Optional[List[str]] = Field(None, description="UF codes (e.g. ['SP', 'RJ'])", max_length=27)
    valor_min: Optional[float] = Field(None, ge=0, description="Minimum estimated value")
    valor_max: Optional[float] = Field(None, ge=0, description="Maximum estimated value")
    keywords: Optional[List[str]] = Field(None, description="Extra keyword filters", max_length=50)


class CreateAlertRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="Alert display name")
    filters: AlertFilters


class UpdateAlertRequest(BaseModel):
    """Partial update — all fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    filters: Optional[AlertFilters] = None
    active: Optional[bool] = None


class AlertResponse(BaseModel):
    id: str
    user_id: str
    name: str
    filters: Dict[str, Any]
    active: bool
    sent_count: int = 0
    created_at: str
    updated_at: str


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int


class AlertHistoryItem(BaseModel):
    id: str
    alert_id: str
    item_id: str
    sent_at: str


class AlertHistoryResponse(BaseModel):
    items: List[AlertHistoryItem]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_alert_unsubscribe_token(alert_id: str) -> str:
    """Generate HMAC-based unsubscribe token for an alert (RFC 8058)."""
    return hmac.new(
        UNSUBSCRIBE_SECRET.encode(),
        alert_id.encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


def get_alert_unsubscribe_url(alert_id: str) -> str:
    """Build one-click unsubscribe URL for email headers / footer."""
    token = _generate_alert_unsubscribe_token(alert_id)
    backend_url = os.getenv(
        "BACKEND_URL",
        "https://smartlic-backend-production.up.railway.app",
    )
    return f"{backend_url}/v1/alerts/{alert_id}/unsubscribe?token={token}"


def _validate_filters(filters: AlertFilters) -> None:
    """Raise 422 if filter values are logically invalid."""
    if filters.valor_min is not None and filters.valor_max is not None:
        if filters.valor_min > filters.valor_max:
            raise HTTPException(
                status_code=422,
                detail="valor_min não pode ser maior que valor_max.",
            )
    if filters.ufs:
        for uf in filters.ufs:
            if len(uf) != 2 or not uf.isalpha():
                raise HTTPException(
                    status_code=422,
                    detail=f"UF inválida: '{uf}'. Use siglas de 2 letras (ex: SP, RJ).",
                )


def _row_to_response(row: Dict[str, Any], sent_count: int = 0) -> AlertResponse:
    """Convert a Supabase row dict into an AlertResponse."""
    return AlertResponse(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        filters=row.get("filters") or {},
        active=row.get("active", True),
        sent_count=sent_count,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------------------------------------------------------------------------
# AC1: POST /alerts — Create alert
# ---------------------------------------------------------------------------


@router.post("/alerts", status_code=201)
async def create_alert(
    body: CreateAlertRequest,
    user: dict = Depends(require_auth),
):
    """Create a new email alert for the authenticated user.

    AC1: Persists alert definition with filter criteria.
    Enforces a per-user limit to prevent abuse.
    """
    if not ALERTS_SYSTEM_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    from supabase_client import get_supabase, sb_execute

    user_id = user["id"]
    sb = get_supabase()

    _validate_filters(body.filters)

    # Enforce per-user alert limit
    try:
        count_result = await sb_execute(
            sb.table("alerts")
            .select("id", count="exact")
            .eq("user_id", user_id)
        )
        current_count = count_result.count if count_result.count is not None else 0
        if current_count >= MAX_ALERTS_PER_USER:
            raise HTTPException(
                status_code=409,
                detail=f"Limite de {MAX_ALERTS_PER_USER} alertas atingido. Remova um alerta existente.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Failed to check alert count for user {mask_user_id(user_id)}: {e}")
        # Continue — better to allow than to block on a count check failure

    now = datetime.now(timezone.utc).isoformat()

    try:
        result = await sb_execute(
            sb.table("alerts")
            .insert({
                "user_id": user_id,
                "name": body.name.strip(),
                "filters": body.filters.model_dump(exclude_none=True),
                "active": True,
                "created_at": now,
                "updated_at": now,
            })
        )

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=500, detail="Falha ao criar alerta.")

        logger.info(f"Alert created for user {mask_user_id(user_id)}: name={body.name!r}")
        return _row_to_response(result.data[0], sent_count=0)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar alerta.")


# ---------------------------------------------------------------------------
# AC2: GET /alerts — List user's alerts
# ---------------------------------------------------------------------------


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    user: dict = Depends(require_auth),
):
    """List all alerts for the authenticated user, ordered by created_at desc.

    AC2: Includes sent_count (number of items sent for each alert).
    """
    if not ALERTS_SYSTEM_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    from supabase_client import get_supabase, sb_execute

    user_id = user["id"]
    sb = get_supabase()

    try:
        # Fetch alerts
        alerts_result = await sb_execute(
            sb.table("alerts")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )

        alerts_data = alerts_result.data or []

        if not alerts_data:
            return AlertListResponse(alerts=[], total=0)

        # Fetch sent counts in bulk for all alert IDs
        alert_ids = [a["id"] for a in alerts_data]
        sent_counts: Dict[str, int] = {}

        try:
            for alert_id in alert_ids:
                count_result = await sb_execute(
                    sb.table("alert_sent_items")
                    .select("id", count="exact")
                    .eq("alert_id", alert_id)
                )
                sent_counts[alert_id] = count_result.count if count_result.count is not None else 0
        except Exception as e:
            logger.warning(f"Failed to fetch sent counts for user {mask_user_id(user_id)}: {e}")
            # Graceful degradation — return 0 counts rather than failing

        alerts = [
            _row_to_response(row, sent_count=sent_counts.get(row["id"], 0))
            for row in alerts_data
        ]

        return AlertListResponse(alerts=alerts, total=len(alerts))

    except Exception as e:
        logger.error(f"Error listing alerts for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar alertas.")


# ---------------------------------------------------------------------------
# AC3: PATCH /alerts/{alert_id} — Edit alert
# ---------------------------------------------------------------------------


@router.patch("/alerts/{alert_id}")
async def update_alert(
    alert_id: str,
    body: UpdateAlertRequest,
    user: dict = Depends(require_auth),
):
    """Update an existing alert (partial update).

    AC3: Only name, filters, and active status can be updated.
    Validates that the alert belongs to the authenticated user.
    """
    if not ALERTS_SYSTEM_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    from supabase_client import get_supabase, sb_execute

    user_id = user["id"]
    sb = get_supabase()

    # Build update payload (only non-None fields)
    payload: Dict[str, Any] = {}

    if body.name is not None:
        payload["name"] = body.name.strip()
    if body.filters is not None:
        _validate_filters(body.filters)
        payload["filters"] = body.filters.model_dump(exclude_none=True)
    if body.active is not None:
        payload["active"] = body.active

    if not payload:
        raise HTTPException(status_code=422, detail="Nenhum campo para atualizar.")

    payload["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        result = await sb_execute(
            sb.table("alerts")
            .update(payload)
            .eq("id", alert_id)
            .eq("user_id", user_id)
        )

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Alerta não encontrado.",
            )

        logger.info(
            f"Alert {alert_id[:8]}... updated for user {mask_user_id(user_id)}: "
            f"{list(payload.keys())}"
        )
        return _row_to_response(result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert {alert_id[:8]}... for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar alerta.")


# ---------------------------------------------------------------------------
# AC4: DELETE /alerts/{alert_id} — Delete alert
# ---------------------------------------------------------------------------


@router.delete("/alerts/{alert_id}", status_code=200)
async def delete_alert(
    alert_id: str,
    user: dict = Depends(require_auth),
):
    """Delete an alert and its sent-item history.

    AC4: Cascading delete removes associated alert_sent_items.
    Validates that the alert belongs to the authenticated user.
    """
    if not ALERTS_SYSTEM_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    from supabase_client import get_supabase, sb_execute

    user_id = user["id"]
    sb = get_supabase()

    try:
        # Delete sent items first (cascade — in case DB cascade is not configured)
        try:
            await sb_execute(
                sb.table("alert_sent_items")
                .delete()
                .eq("alert_id", alert_id)
            )
        except Exception as e:
            logger.warning(f"Failed to delete sent items for alert {alert_id[:8]}...: {e}")
            # Continue — the alert delete may still succeed if DB-level cascade handles it

        # Delete the alert itself (with ownership check)
        result = await sb_execute(
            sb.table("alerts")
            .delete()
            .eq("id", alert_id)
            .eq("user_id", user_id)
        )

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Alerta não encontrado.",
            )

        logger.info(f"Alert {alert_id[:8]}... deleted for user {mask_user_id(user_id)}")
        return {"success": True, "message": "Alerta removido com sucesso."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id[:8]}... for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao remover alerta.")


# ---------------------------------------------------------------------------
# AC9: GET /alerts/{alert_id}/unsubscribe — One-click unsubscribe (RFC 8058)
# ---------------------------------------------------------------------------


@router.get("/alerts/{alert_id}/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_alert(
    alert_id: str,
    token: str = Query(..., description="HMAC verification token"),
):
    """One-click unsubscribe from an email alert (RFC 8058).

    AC9: No authentication required — uses HMAC token verification.
    Sets the alert's active flag to false.
    Returns an HTML confirmation page.
    """
    # Verify HMAC token
    expected_token = _generate_alert_unsubscribe_token(alert_id)
    if not hmac.compare_digest(token, expected_token):
        return HTMLResponse(
            content=_unsubscribe_page("Token inválido ou expirado.", success=False),
            status_code=400,
        )

    from supabase_client import get_supabase, sb_execute

    try:
        sb = get_supabase()

        # Deactivate the alert (no ownership check — token is proof of authorization)
        result = await sb_execute(
            sb.table("alerts")
            .update({
                "active": False,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", alert_id)
        )

        if not result.data or len(result.data) == 0:
            return HTMLResponse(
                content=_unsubscribe_page("Alerta não encontrado.", success=False),
                status_code=404,
            )

        alert_name = result.data[0].get("name", "Alerta")
        logger.info(f"Alert {alert_id[:8]}... unsubscribed via one-click link")

        return HTMLResponse(
            content=_unsubscribe_page(
                f'O alerta "{alert_name}" foi desativado. '
                "Você não receberá mais notificações deste alerta. "
                "Para reativá-lo, acesse suas configurações no SmartLic.",
                success=True,
            )
        )

    except Exception as e:
        logger.error(f"Failed to process alert unsubscribe for {alert_id[:8]}...: {e}")
        return HTMLResponse(
            content=_unsubscribe_page("Erro ao processar. Tente novamente.", success=False),
            status_code=500,
        )


# ---------------------------------------------------------------------------
# STORY-315 AC12: GET /alerts/{alert_id}/preview — Dry-run matching
# ---------------------------------------------------------------------------


class AlertPreviewItem(BaseModel):
    id: str
    titulo: str
    orgao: str
    valor_estimado: float = 0.0
    uf: str = ""
    modalidade: str = ""
    link_pncp: str = ""
    viability_score: Optional[float] = None


class AlertPreviewResponse(BaseModel):
    alert_id: str
    alert_name: str
    items: List[AlertPreviewItem]
    total: int
    message: str


@router.get("/alerts/{alert_id}/preview", response_model=AlertPreviewResponse)
async def preview_alert(
    alert_id: str,
    user: dict = Depends(require_auth),
):
    """Preview what opportunities an alert would match (dry-run).

    STORY-315 AC12: Executes matching without sending email.
    Returns opportunities that would be sent, useful for validating filters.
    """
    if not ALERTS_SYSTEM_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    from supabase_client import get_supabase, sb_execute

    user_id = user["id"]
    sb = get_supabase()

    # Verify alert ownership
    try:
        alert_result = await sb_execute(
            sb.table("alerts")
            .select("id, user_id, name, filters")
            .eq("id", alert_id)
            .eq("user_id", user_id)
        )

        if not alert_result.data or len(alert_result.data) == 0:
            raise HTTPException(status_code=404, detail="Alerta não encontrado.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying alert for preview {alert_id[:8]}...: {e}")
        raise HTTPException(status_code=500, detail="Erro ao verificar alerta.")

    alert_data = alert_result.data[0]
    filters = alert_data.get("filters") or {}

    # Execute matching logic (dry run — no email, no tracking)
    try:
        from services.alert_matcher import _search_cached_results, _apply_alert_filters

        raw_results = await _search_cached_results(filters, sb)
        matched = _apply_alert_filters(raw_results, filters)

        # Cap at 20 items for preview
        preview_items = [
            AlertPreviewItem(
                id=item.get("id", ""),
                titulo=item.get("titulo", "Sem titulo"),
                orgao=item.get("orgao", ""),
                valor_estimado=item.get("valor_estimado", 0.0),
                uf=item.get("uf", ""),
                modalidade=item.get("modalidade", ""),
                link_pncp=item.get("link_pncp", ""),
                viability_score=item.get("viability_score"),
            )
            for item in matched[:20]
        ]

        total = len(matched)
        if total == 0:
            message = "Nenhuma oportunidade encontrada nas últimas 24h com esses filtros."
        elif total == 1:
            message = "1 oportunidade encontrada nas últimas 24h."
        else:
            message = f"{total} oportunidades encontradas nas últimas 24h."

        return AlertPreviewResponse(
            alert_id=alert_id,
            alert_name=alert_data.get("name", ""),
            items=preview_items,
            total=total,
            message=message,
        )

    except Exception as e:
        logger.error(f"Error previewing alert {alert_id[:8]}...: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar preview.")


# ---------------------------------------------------------------------------
# AC13: GET /alerts/{alert_id}/history — Sent-item history
# ---------------------------------------------------------------------------


@router.get("/alerts/{alert_id}/history", response_model=AlertHistoryResponse)
async def alert_history(
    alert_id: str,
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user: dict = Depends(require_auth),
):
    """Paginated history of items sent for this alert.

    AC13: Returns alert_sent_items ordered by sent_at desc.
    Only accessible if the alert belongs to the authenticated user.
    """
    if not ALERTS_SYSTEM_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    from supabase_client import get_supabase, sb_execute

    user_id = user["id"]
    sb = get_supabase()

    # Verify alert ownership
    try:
        alert_result = await sb_execute(
            sb.table("alerts")
            .select("id, user_id")
            .eq("id", alert_id)
            .eq("user_id", user_id)
        )

        if not alert_result.data or len(alert_result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Alerta não encontrado.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying alert ownership for {alert_id[:8]}...: {e}")
        raise HTTPException(status_code=500, detail="Erro ao verificar alerta.")

    # Fetch paginated sent items
    try:
        result = await sb_execute(
            sb.table("alert_sent_items")
            .select("*", count="exact")
            .eq("alert_id", alert_id)
            .order("sent_at", desc=True)
            .range(offset, offset + limit - 1)
        )

        items = [
            AlertHistoryItem(
                id=row["id"],
                alert_id=row["alert_id"],
                item_id=row["item_id"],
                sent_at=row["sent_at"],
            )
            for row in (result.data or [])
        ]
        total = result.count if result.count is not None else len(items)

        return AlertHistoryResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(
            f"Error fetching alert history for {alert_id[:8]}... "
            f"user {mask_user_id(user_id)}: {e}"
        )
        raise HTTPException(status_code=500, detail="Erro ao buscar histórico do alerta.")


# ---------------------------------------------------------------------------
# HTML template (same pattern as routes/emails.py)
# ---------------------------------------------------------------------------


def _unsubscribe_page(message: str, success: bool) -> str:
    """Render simple unsubscribe confirmation HTML page."""
    icon = "&#10003;" if success else "&#10007;"
    color = "#2E7D32" if success else "#d32f2f"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SmartLic — Cancelar alerta</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           display: flex; justify-content: center; align-items: center;
           min-height: 100vh; margin: 0; background: #f4f4f4; }}
    .card {{ background: white; padding: 48px; border-radius: 12px;
             box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; max-width: 480px; }}
    .icon {{ font-size: 48px; color: {color}; margin-bottom: 16px; }}
    h1 {{ font-size: 20px; color: #333; margin-bottom: 12px; }}
    p {{ color: #666; line-height: 1.6; }}
    a {{ color: #2E7D32; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">{icon}</div>
    <h1>{"Alerta desativado" if success else "Erro"}</h1>
    <p>{message}</p>
    <p style="margin-top: 24px;"><a href="{FRONTEND_URL}">Voltar para o SmartLic</a></p>
  </div>
</body>
</html>"""
