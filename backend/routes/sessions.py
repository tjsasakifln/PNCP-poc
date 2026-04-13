"""Search sessions/history routes.

Extracted from main.py as part of STORY-202 monolith decomposition.
"""

import io
import logging

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from auth import require_auth
from database import get_db
from schemas import SessionsListResponse
from supabase_client import sb_execute, CircuitBreakerOpenError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sessions"])


@router.get("/sessions", response_model=SessionsListResponse)
async def get_sessions(
    user: dict = Depends(require_auth),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None, description="Filter by session status (completed, failed, timed_out)"),
    hide_old_failures: bool = Query(default=True, description="UX-433 AC3: hide failed/timed_out entries older than 7 days from default listing"),
    db=Depends(get_db),
):
    """Get user's search session history."""
    try:
        query = (
            db.table("search_sessions")
            .select("*", count="exact")
            .eq("user_id", user["id"])
        )

        if status and status != "all":
            if status == "failed":
                # "failed" filter includes both failed and timed_out
                query = query.in_("status", ["failed", "timed_out"])
            elif status == "completed":
                # ISSUE-040: Sessions with NULL status are legacy completed sessions.
                # Sessions with total_filtered > 0 but non-terminal status are
                # pipeline sessions that completed but didn't get status updated.
                # Include: status=completed, status=null, or has results (total_filtered > 0).
                query = query.or_("status.eq.completed,status.is.null,total_filtered.gt.0")
            else:
                query = query.eq("status", status)

        # UX-433 AC3: By default, hide failed/timed_out entries older than 7 days.
        # User can pass hide_old_failures=false to see the full unfiltered history
        # ("Mostrar todas" option in the frontend).
        if hide_old_failures and (not status or status == "all"):
            seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            query = query.or_(
                f"status.not.in.(failed,timed_out),created_at.gte.{seven_days_ago}"
            )

        result = await sb_execute(
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )

        # Zero-Churn P2 §2.2: Enrich each session with download_available flag
        from config.features import DATA_RETENTION_DAYS
        sessions = result.data or []
        now = datetime.now(timezone.utc)
        for s in sessions:
            created = s.get("created_at", "")
            is_completed = s.get("status") in ("completed", None) or (s.get("total_filtered") or 0) > 0
            within_retention = False
            if created:
                try:
                    created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    within_retention = now < created_dt + timedelta(days=DATA_RETENTION_DAYS)
                except (ValueError, TypeError):
                    pass
            s["download_available"] = is_completed and within_retention

        return {
            "sessions": sessions,
            "total": result.count or 0,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except CircuitBreakerOpenError:
        # STORY-416 AC4: CB open — return empty sessions with degraded header
        from fastapi.responses import JSONResponse
        logger.warning("Sessions CB open — returning degraded empty history for %s", user["id"])
        return JSONResponse(
            status_code=200,
            content={"sessions": [], "total": 0, "limit": limit, "offset": offset, "degraded": True},
            headers={"X-Cache-Status": "stale-due-to-cb-open"},
        )
    except Exception as e:
        logger.error(f"Error fetching sessions for user {user['id']}: {e}")
        raise HTTPException(status_code=503, detail="Histórico temporariamente indisponível")


@router.get("/sessions/{search_id}/download")
async def download_session_excel(
    search_id: str,
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """Download Excel for a previously completed search session.

    Zero-Churn P2 §2.2: Allows downloads within DATA_RETENTION_DAYS even
    after trial/subscription expires. Bypasses quota checks — only previously
    generated data can be downloaded.
    """
    from config.features import DATA_RETENTION_DAYS, GRACE_DOWNLOAD_ENABLED
    from excel import create_excel

    if not GRACE_DOWNLOAD_ENABLED:
        raise HTTPException(status_code=403, detail="Downloads durante grace period desabilitados")

    # Verify ownership
    session_result = await sb_execute(
        db.table("search_sessions")
        .select("id, user_id, created_at, status, search_params")
        .eq("id", search_id)
        .eq("user_id", user["id"])
        .single()
    )
    if not session_result.data:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")

    session = session_result.data

    # Check retention window
    created_at = session.get("created_at", "")
    if created_at:
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            retention_deadline = created_dt + timedelta(days=DATA_RETENTION_DAYS)
            if datetime.now(timezone.utc) > retention_deadline:
                raise HTTPException(status_code=410, detail="Dados expirados apos periodo de retencao")
        except HTTPException:
            raise
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse created_at for session {search_id}: {e}")

    # Load results from search_results_store
    results_result = await sb_execute(
        db.table("search_results_store")
        .select("results")
        .eq("search_id", search_id)
        .single()
    )
    if not results_result.data or not results_result.data.get("results"):
        raise HTTPException(status_code=410, detail="Resultados nao disponiveis — dados expirados")

    results = results_result.data["results"]
    if not isinstance(results, list):
        results = []

    # Extract search params for Excel
    params = session.get("search_params") or {}
    sector_name = params.get("setor", "")
    ufs = params.get("ufs", [])
    if not isinstance(ufs, list):
        ufs = []

    logger.info(
        f"Grace period download: user={user['id']} search_id={search_id} "
        f"results={len(results)} sector={sector_name}"
    )

    excel_buf = create_excel(results)
    filename = f"smartlic-{search_id[:8]}.xlsx"
    return StreamingResponse(
        io.BytesIO(excel_buf.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
