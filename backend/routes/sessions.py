"""Search sessions/history routes.

Extracted from main.py as part of STORY-202 monolith decomposition.
"""

import logging

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
    db=Depends(get_db),
):
    """Get user's search session history."""
    try:
        result = await sb_execute(
            db.table("search_sessions")
            .select("*", count="exact")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
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
