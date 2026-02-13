"""Feature flags API for plan-based capabilities.

Provides GET /api/features/me endpoint with Redis caching (STORY-171).
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import require_auth
from cache import redis_cache
from log_sanitizer import mask_user_id
from quota import get_plan_from_profile, SUBSCRIPTION_GRACE_DAYS

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


def fetch_features_from_db(user_id: str) -> UserFeaturesResponse:
    """Fetch user features from Supabase (cache miss).

    Args:
        user_id: User UUID

    Returns:
        UserFeaturesResponse with features, plan_id, billing_period

    Multi-layer fallback strategy (AC6-AC7):
    1. Active subscription (primary source)
    2. Recently-expired subscription within grace period (billing gap tolerance)
    3. profiles.plan_type (last known plan - reliable fallback)
    4. free_trial (absolute last resort)
    """
    from supabase_client import get_supabase
    from datetime import timedelta

    sb = get_supabase()

    plan_id = None
    billing_period = "monthly"  # Default

    # --- Layer 1: Active subscription ---
    try:
        sub_result = (
            sb.table("user_subscriptions")
            .select("plan_id, billing_period, expires_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if sub_result.data and len(sub_result.data) > 0:
            subscription = sub_result.data[0]
            plan_id = subscription["plan_id"]
            billing_period = subscription["billing_period"]
        else:
            # No active subscription found
            logger.info(f"No active subscription for user {mask_user_id(user_id)}")

    except Exception as e:
        logger.error(f"Failed to fetch subscription for user {mask_user_id(user_id)}: {e}")

    # --- Layer 2: Recently-expired subscription (grace period) ---
    if not plan_id:
        try:
            grace_cutoff = (datetime.now(timezone.utc) - timedelta(days=SUBSCRIPTION_GRACE_DAYS)).isoformat()
            grace_result = (
                sb.table("user_subscriptions")
                .select("plan_id, billing_period, expires_at")
                .eq("user_id", user_id)
                .gte("expires_at", grace_cutoff)
                .order("expires_at", desc=True)
                .limit(1)
                .execute()
            )

            if grace_result.data and len(grace_result.data) > 0:
                subscription = grace_result.data[0]
                plan_id = subscription["plan_id"]
                billing_period = subscription["billing_period"]
                logger.info(
                    f"Using grace-period subscription for user {mask_user_id(user_id)}: "
                    f"plan={plan_id}"
                )
        except Exception as e:
            logger.warning(f"Failed to fetch grace-period subscription for user {mask_user_id(user_id)}: {e}")

    # --- Layer 3: Profile-based fallback (last known plan) ---
    if not plan_id:
        profile_plan = get_plan_from_profile(user_id, sb)
        if profile_plan and profile_plan != "free_trial":
            logger.warning(
                f"FALLBACK ACTIVATED for user {mask_user_id(user_id)}: "
                f"using profiles.plan_type='{profile_plan}' (no active subscription found)"
            )
            plan_id = profile_plan
            # Default billing_period to monthly for profile fallback
            billing_period = "monthly"

    # --- Layer 4: Absolute last resort ---
    if not plan_id:
        logger.info(f"Using free_trial for user {mask_user_id(user_id)} (no subscription or profile plan)")
        plan_id = "free_trial"
        billing_period = "monthly"

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

    CACHING STRATEGY (STORY-217: unified pool):
    - Redis cache with 5-minute TTL via shared pool
    - Cache key: ``features:{user_id}``
    - Cache miss: Fetch from Supabase (JOIN user_subscriptions + plan_features)
    - Graceful degradation via InMemoryCache fallback
    """
    user_id = user["id"]
    cache_key = f"features:{user_id}"

    # Try cache first (redis_cache handles Redis/InMemoryCache fallback)
    try:
        cached_data = await redis_cache.get(cache_key)
        if cached_data:
            cached_json = json.loads(cached_data)
            logger.debug(f"Cache HIT for user {mask_user_id(user_id)}")
            return UserFeaturesResponse(**cached_json)
    except Exception as e:
        logger.warning(f"Cache read failed (non-critical): {e}")

    # Cache miss - fetch from database
    logger.debug(f"Cache MISS for user {mask_user_id(user_id)}, querying database")
    response = fetch_features_from_db(user_id)

    # Add cached_at timestamp
    response.cached_at = datetime.now(timezone.utc).isoformat()

    # Store in cache
    try:
        cache_ttl = 300  # 5-minute TTL
        await redis_cache.setex(
            cache_key,
            cache_ttl,
            response.model_dump_json(),
        )
        logger.debug(
            f"Cached features for user {mask_user_id(user_id)} (TTL={cache_ttl}s)"
        )
    except Exception as e:
        logger.warning(f"Cache write failed (non-critical): {e}")

    return response
