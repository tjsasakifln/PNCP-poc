"""Search sessions/history routes.

Extracted from main.py as part of STORY-202 monolith decomposition.
"""

import logging

from fastapi import APIRouter, Depends, Query
from auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sessions"])


@router.get("/sessions")
async def get_sessions(
    user: dict = Depends(require_auth),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get user's search session history."""
    from supabase_client import get_supabase
    sb = get_supabase()

    result = (
        sb.table("search_sessions")
        .select("*", count="exact")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "sessions": result.data,
        "total": result.count or 0,
        "limit": limit,
        "offset": offset,
    }
