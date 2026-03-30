"""Search sessions/history routes.

Extracted from main.py as part of STORY-202 monolith decomposition.
"""

import logging

from typing import Optional

from fastapi import APIRouter, Depends, Query
from auth import require_auth
from database import get_db
from schemas import SessionsListResponse
from supabase_client import sb_execute

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sessions"])


@router.get("/sessions", response_model=SessionsListResponse)
async def get_sessions(
    user: dict = Depends(require_auth),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None, description="Filter by session status (completed, failed, timed_out)"),
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

        result = await sb_execute(
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )

        return {
            "sessions": result.data,
            "total": result.count or 0,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Error fetching sessions for user {user['id']}: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Histórico temporariamente indisponível")
