"""routes/notifications.py — In-app notification endpoints.

STORY-445: New bid count badge — authenticated endpoints to read / clear the
``new_bids_count:{user_id}`` Redis counter that is populated daily by the
``new_bids_notifier`` cron job.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import require_auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


class NewBidsCountResponse(BaseModel):
    count: int


@router.get("/new-bids-count", response_model=NewBidsCountResponse)
async def get_new_bids_count(
    user: dict = Depends(require_auth),
) -> NewBidsCountResponse:
    """Return count of new bids available for the user since last check.

    Returns 0 when no Redis key exists (cron not yet run, or badge was cleared).
    """
    user_id = user["id"]
    try:
        from redis_pool import get_redis_pool

        redis = await get_redis_pool()
        if redis:
            val = await redis.get(f"new_bids_count:{user_id}")
            if val is not None:
                return NewBidsCountResponse(count=int(val))
    except Exception as e:
        logger.warning(
            "STORY-445: Redis get failed for user %s: %s",
            str(user_id)[:8],
            e,
        )
    return NewBidsCountResponse(count=0)


@router.delete("/new-bids-count")
async def clear_new_bids_count(
    user: dict = Depends(require_auth),
) -> dict:
    """Clear the new-bids badge for the user (called after they run a search).

    Idempotent — safe to call even if the key does not exist.
    """
    user_id = user["id"]
    try:
        from redis_pool import get_redis_pool

        redis = await get_redis_pool()
        if redis:
            await redis.delete(f"new_bids_count:{user_id}")
    except Exception as e:
        logger.warning(
            "STORY-445: Redis delete failed for user %s: %s",
            str(user_id)[:8],
            e,
        )
    return {"ok": True}
