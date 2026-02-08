"""Feature flags API for plan-based capabilities.

Provides GET /api/features/me endpoint with Redis caching (STORY-171).
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import require_auth
from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/features", tags=["features"])


class FeatureInfo(BaseModel):
    """Single feature flag information."""
    key: str
    enabled: bool
    metadata: Optional[dict] = None


class UserFeaturesResponse(BaseModel):
    """Response containing user's enabled features."""
    features: list[FeatureInfo]
    plan_id: str
    billing_period: str
    cached_at: Optional[str] = None  # ISO 8601 timestamp


def get_redis_client():
    """Get Redis client with graceful fallback.

    Returns:
        Redis client or None if not configured/unavailable
    """
    import os

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.debug("REDIS_URL not configured, caching disabled")
        return None

    try:
        import redis
        client = redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        # Test connection
        client.ping()
        return client
    except ImportError:
        logger.warning("redis package not installed, caching disabled")
        return None
    except Exception as e:
        logger.warning(f"Redis connection failed (graceful degradation): {e}")
        return None


def fetch_features_from_db(user_id: str) -> UserFeaturesResponse:
    """Fetch user features from Supabase (cache miss).

    Args:
        user_id: User UUID

    Returns:
        UserFeaturesResponse with features, plan_id, billing_period
    """
    from supabase_client import get_supabase

    sb = get_supabase()

    # Get user's current subscription
    try:
        sub_result = (
            sb.table("user_subscriptions")
            .select("plan_id, billing_period")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not sub_result.data or len(sub_result.data) == 0:
            # No active subscription - return free_trial defaults
            logger.info(f"No active subscription for user {mask_user_id(user_id)}, using free_trial")
            return UserFeaturesResponse(
                features=[],
                plan_id="free_trial",
                billing_period="monthly",
                cached_at=None,
            )

        subscription = sub_result.data[0]
        plan_id = subscription["plan_id"]
        billing_period = subscription["billing_period"]

    except Exception as e:
        logger.error(f"Failed to fetch subscription for user {mask_user_id(user_id)}: {e}")
        # Fail open with free_trial
        return UserFeaturesResponse(
            features=[],
            plan_id="free_trial",
            billing_period="monthly",
            cached_at=None,
        )

    # Get features for this plan + billing_period
    try:
        features_result = (
            sb.table("plan_features")
            .select("feature_key, enabled, metadata")
            .eq("plan_id", plan_id)
            .eq("billing_period", billing_period)
            .eq("enabled", True)
            .execute()
        )

        features = [
            FeatureInfo(
                key=f["feature_key"],
                enabled=f["enabled"],
                metadata=f.get("metadata"),
            )
            for f in features_result.data
        ]

        logger.info(
            f"Fetched {len(features)} features for user {mask_user_id(user_id)} "
            f"(plan={plan_id}, billing={billing_period})"
        )

        return UserFeaturesResponse(
            features=features,
            plan_id=plan_id,
            billing_period=billing_period,
            cached_at=None,
        )

    except Exception as e:
        logger.error(f"Failed to fetch plan_features: {e}")
        # Return empty features list (fail safe)
        return UserFeaturesResponse(
            features=[],
            plan_id=plan_id,
            billing_period=billing_period,
            cached_at=None,
        )


@router.get("/me", response_model=UserFeaturesResponse)
async def get_my_features(user: dict = Depends(require_auth)):
    """Get current user's enabled features.

    CACHING STRATEGY:
    - Redis cache with 5-minute TTL
    - Cache key: `features:{user_id}`
    - Cache miss: Fetch from Supabase (JOIN user_subscriptions + plan_features)
    - Graceful degradation if Redis unavailable (direct DB query)

    CACHE INVALIDATION:
    - POST /api/subscriptions/update-billing-period invalidates on success
    - Manual: DELETE features:{user_id} via redis-cli

    Returns:
        UserFeaturesResponse with features array, plan_id, billing_period, cached_at
    """
    user_id = user["id"]
    cache_key = f"features:{user_id}"
    redis_client = get_redis_client()

    # Try cache first (if Redis available)
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                cached_json = json.loads(cached_data)
                logger.debug(f"Redis cache HIT for user {mask_user_id(user_id)}")
                return UserFeaturesResponse(**cached_json)
        except Exception as e:
            logger.warning(f"Redis cache read failed (non-critical): {e}")

    # Cache miss - fetch from database
    logger.debug(f"Redis cache MISS for user {mask_user_id(user_id)}, querying database")
    response = fetch_features_from_db(user_id)

    # Add cached_at timestamp
    response.cached_at = datetime.utcnow().isoformat()

    # Store in cache (if Redis available)
    if redis_client:
        try:
            # 5-minute TTL (300 seconds)
            cache_ttl = 300
            redis_client.setex(
                cache_key,
                cache_ttl,
                response.model_dump_json()  # Pydantic v2 method
            )
            logger.debug(
                f"Cached features for user {mask_user_id(user_id)} (TTL={cache_ttl}s)"
            )
        except Exception as e:
            logger.warning(f"Redis cache write failed (non-critical): {e}")

    return response
