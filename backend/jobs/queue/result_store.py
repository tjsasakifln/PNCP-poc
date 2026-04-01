"""jobs.queue.result_store — Job result persistence, cancel flags, concurrent search slots."""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CANCEL_KEY_PREFIX = "smartlic:search_cancel:"
_CANCEL_TTL = 600
_CONCURRENT_SEARCH_KEY_PREFIX = "smartlic:concurrent_searches:"
_CONCURRENT_SEARCH_TTL = 600
_PENDING_REVIEW_KEY_PREFIX = "smartlic:pending_review:"
_ZERO_MATCH_KEY_PREFIX = "smartlic:zero_match:"


async def set_cancel_flag(search_id: str) -> bool:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return False
    try:
        await redis.set(f"{_CANCEL_KEY_PREFIX}{search_id}", "1", ex=_CANCEL_TTL)
        logger.info(f"STORY-281: Cancel flag SET for search_id={search_id}")
        return True
    except Exception as e:
        logger.warning(f"STORY-281: Failed to set cancel flag for {search_id}: {e}")
        return False


async def check_cancel_flag(search_id: str) -> bool:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return False
    try:
        result = await redis.get(f"{_CANCEL_KEY_PREFIX}{search_id}")
        if result:
            logger.info(f"STORY-281: Cancel flag DETECTED for search_id={search_id} — aborting worker")
        return result is not None
    except Exception:
        return False


async def clear_cancel_flag(search_id: str) -> None:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return
    try:
        await redis.delete(f"{_CANCEL_KEY_PREFIX}{search_id}")
    except Exception:
        pass


async def persist_job_result(search_id: str, field: str, value: Any) -> None:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return
    try:
        serialized = json.dumps(value) if not isinstance(value, str) else value
        await redis.set(f"smartlic:job_result:{search_id}:{field}", serialized, ex=3600)
    except Exception as e:
        logger.warning(f"Failed to persist job result {field} for {search_id}: {e}")


async def get_job_result(search_id: str, field: str) -> Optional[Any]:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return None
    try:
        raw = await redis.get(f"smartlic:job_result:{search_id}:{field}")
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw
    except Exception as e:
        logger.warning(f"Failed to get job result {field} for {search_id}: {e}")
        return None


async def _update_results_excel_url(search_id: str, download_url: str) -> None:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return
    try:
        key = f"smartlic:results:{search_id}"
        raw = await redis.get(key)
        if raw:
            data = json.loads(raw)
            data["download_url"] = download_url
            data["excel_status"] = "ready"
            await redis.set(key, json.dumps(data), keepttl=True)
            logger.info(f"[Excel] Updated main results key with excel_url: {search_id}")
    except Exception as e:
        logger.warning(f"Failed to update results with excel_url for {search_id}: {e}")


async def acquire_search_slot(user_id: str, search_id: str) -> bool:
    from redis_pool import get_redis_pool
    from config import MAX_CONCURRENT_SEARCHES
    redis = await get_redis_pool()
    if redis is None:
        return True
    key = f"{_CONCURRENT_SEARCH_KEY_PREFIX}{user_id}"
    now = time.time()
    try:
        await redis.zremrangebyscore(key, 0, now - _CONCURRENT_SEARCH_TTL)
        if await redis.zcard(key) >= MAX_CONCURRENT_SEARCHES:
            logger.info(f"STORY-363 AC14: User {user_id[:8]}... exceeded concurrent search limit")
            return False
        await redis.zadd(key, {search_id: now})
        await redis.expire(key, _CONCURRENT_SEARCH_TTL)
        return True
    except Exception as e:
        logger.warning(f"STORY-363: acquire_search_slot failed (allowing through): {e}")
        return True


async def release_search_slot(user_id: str, search_id: str) -> None:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return
    try:
        await redis.zrem(f"{_CONCURRENT_SEARCH_KEY_PREFIX}{user_id}", search_id)
    except Exception as e:
        logger.debug(f"STORY-363: release_search_slot failed (non-fatal): {e}")


async def store_pending_review_bids(search_id: str, bids: list[dict], sector_name: str = "") -> bool:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        logger.warning(f"STORY-354: Cannot store pending bids — Redis unavailable (search_id={search_id})")
        return False
    from config import PENDING_REVIEW_TTL_SECONDS
    try:
        payload = json.dumps({"bids": bids, "sector_name": sector_name, "stored_at": time.time()})
        await redis.setex(f"{_PENDING_REVIEW_KEY_PREFIX}{search_id}", PENDING_REVIEW_TTL_SECONDS, payload)
        logger.info(f"STORY-354: Stored {len(bids)} pending review bids for search_id={search_id}")
        return True
    except Exception as e:
        logger.error(f"STORY-354: Failed to store pending bids: {e}")
        return False


async def store_zero_match_results(search_id: str, results: list[dict]) -> bool:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return False
    try:
        await redis.setex(f"{_ZERO_MATCH_KEY_PREFIX}{search_id}", 3600, json.dumps({"results": results, "stored_at": time.time()}))
        logger.info(f"CRIT-059: Stored {len(results)} zero-match results for search_id={search_id}")
        return True
    except Exception as e:
        logger.error(f"CRIT-059: Failed to store zero-match results: {e}")
        return False


async def get_zero_match_results(search_id: str) -> list[dict] | None:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return None
    try:
        raw = await redis.get(f"{_ZERO_MATCH_KEY_PREFIX}{search_id}")
        if not raw:
            return None
        return json.loads(raw).get("results", [])
    except Exception as e:
        logger.warning(f"CRIT-059: Failed to load zero-match results: {e}")
        return None
