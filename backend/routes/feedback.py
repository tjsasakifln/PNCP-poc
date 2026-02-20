"""GTM-RESILIENCE-D05: User Feedback Loop for Classification Improvement.

Endpoints:
- POST /v1/feedback — Submit feedback on a search result (AC1)
- DELETE /v1/feedback/{feedback_id} — Delete own feedback (AC9)
- GET /v1/admin/feedback/patterns — Admin pattern analysis (AC6)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from auth import require_auth
from admin import require_admin
from config import USER_FEEDBACK_ENABLED, USER_FEEDBACK_RATE_LIMIT, get_feature_flag
from schemas import (
    FeedbackRequest, FeedbackResponse, FeedbackDeleteResponse,
    FeedbackPatternsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])


def _check_feedback_enabled():
    """AC10: Check feature flag at runtime."""
    if not get_feature_flag("USER_FEEDBACK_ENABLED"):
        raise HTTPException(status_code=503, detail="User feedback is temporarily disabled")


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    body: FeedbackRequest,
    user=Depends(require_auth),
):
    """AC1: Submit classification feedback for a search result.

    AC5: Upserts — if user already gave feedback for this search_id + bid_id, update it.
    AC3: Captures context fields (setor_id, bid_objeto, etc.) from the request body.
    """
    _check_feedback_enabled()

    user_id = user.get("sub") or user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    # AC1: Rate limit — max N feedbacks per user per hour
    await _check_rate_limit(user_id)

    from supabase_client import get_supabase
    db = get_supabase()

    now = datetime.now(timezone.utc).isoformat()

    # AC5: Upsert — check if feedback already exists
    existing = (
        db.table("classification_feedback")
        .select("id")
        .eq("user_id", user_id)
        .eq("search_id", body.search_id)
        .eq("bid_id", body.bid_id)
        .execute()
    )

    record = {
        "user_id": user_id,
        "search_id": body.search_id,
        "bid_id": body.bid_id,
        "setor_id": body.setor_id or "unknown",
        "user_verdict": body.user_verdict.value,
        "reason": body.reason[:500] if body.reason else None,
        "category": body.category.value if body.category else None,
        "bid_objeto": (body.bid_objeto[:200] if body.bid_objeto else None),
        "bid_valor": body.bid_valor,
        "bid_uf": body.bid_uf,
        "confidence_score": body.confidence_score,
        "relevance_source": body.relevance_source,
    }

    updated = False
    if existing.data and len(existing.data) > 0:
        # AC5: Update existing record
        feedback_id = existing.data[0]["id"]
        db.table("classification_feedback").update(record).eq("id", feedback_id).execute()
        updated = True
        logger.info(f"Feedback updated: user={user_id[:8]}... bid={body.bid_id} verdict={body.user_verdict.value}")
    else:
        # Insert new record
        result = db.table("classification_feedback").insert(record).execute()
        feedback_id = result.data[0]["id"] if result.data else "unknown"
        logger.info(f"Feedback created: user={user_id[:8]}... bid={body.bid_id} verdict={body.user_verdict.value}")

    return FeedbackResponse(
        id=feedback_id,
        received_at=now,
        updated=updated,
    )


@router.delete("/feedback/{feedback_id}", response_model=FeedbackDeleteResponse)
async def delete_feedback(
    feedback_id: str,
    user=Depends(require_auth),
):
    """AC9: Delete own feedback for LGPD compliance."""
    _check_feedback_enabled()

    user_id = user.get("sub") or user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    from supabase_client import get_supabase
    db = get_supabase()

    # Verify ownership
    existing = (
        db.table("classification_feedback")
        .select("id, user_id")
        .eq("id", feedback_id)
        .execute()
    )

    if not existing.data or len(existing.data) == 0:
        raise HTTPException(status_code=404, detail="Feedback not found")

    if existing.data[0].get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's feedback")

    db.table("classification_feedback").delete().eq("id", feedback_id).execute()
    logger.info(f"Feedback deleted: id={feedback_id} user={user_id[:8]}...")

    return FeedbackDeleteResponse(deleted=True)


@router.get("/admin/feedback/patterns", response_model=FeedbackPatternsResponse)
async def feedback_patterns(
    setor_id: Optional[str] = Query(None, description="Filter by sector ID"),
    days: int = Query(30, ge=1, le=365, description="Look-back period in days"),
    admin=Depends(require_admin),
):
    """AC6: Admin endpoint for feedback pattern analysis.

    Requires admin role (via require_admin dependency).
    """
    _check_feedback_enabled()

    from supabase_client import get_supabase
    db = get_supabase()

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    query = (
        db.table("classification_feedback")
        .select("*")
        .gte("created_at", since)
    )
    if setor_id:
        query = query.eq("setor_id", setor_id)

    result = query.execute()
    feedbacks = result.data or []

    # Load sector keywords if available
    sector_keywords = None
    if setor_id:
        try:
            from sectors import get_sector
            sector = get_sector(setor_id)
            if sector:
                sector_keywords = sector.get("keywords", [])
        except Exception:
            pass

    from feedback_analyzer import analyze_feedback_patterns
    analysis = analyze_feedback_patterns(feedbacks, sector_keywords)

    return FeedbackPatternsResponse(**analysis)


async def _check_rate_limit(user_id: str) -> None:
    """AC1: Enforce rate limit of N feedbacks per user per hour."""
    from supabase_client import get_supabase
    db = get_supabase()

    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    count_result = (
        db.table("classification_feedback")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .gte("created_at", one_hour_ago)
        .execute()
    )

    count = count_result.count if count_result.count is not None else 0
    if count >= USER_FEEDBACK_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {USER_FEEDBACK_RATE_LIMIT} feedbacks per hour.",
        )
