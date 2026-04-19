"""CROSS-003 + DEBT-205: Feature Flags Admin + Public API.

Admin endpoints to list, update, and reload feature flags at runtime.
Public endpoint for frontend consumption (DEBT-SYS-009 / DEBT-FE-008).

Architecture:
- Source of truth: _FEATURE_FLAG_REGISTRY in config/features.py
- Runtime overrides stored in Redis (key prefix: smartlic:ff:)
- Fallback: in-memory dict when Redis is unavailable
- Priority: Redis override > env var > registry default

Endpoints:
- GET  /feature-flags                -- Public: list flags for frontend consumption
- GET  /admin/feature-flags          -- Admin: list all flags with metadata
- PATCH /admin/feature-flags/{name}  -- Admin: toggle a flag at runtime
- POST /admin/feature-flags/reload   -- Admin: reload all flags from env
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from admin import require_admin
from auth import require_auth
from config.features import (
    _FEATURE_FLAG_REGISTRY,
    _feature_flag_cache,
    get_feature_flag,
    reload_feature_flags,
)
from config.base import str_to_bool
from audit import audit_logger
from log_sanitizer import log_admin_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/feature-flags", tags=["admin", "feature-flags"])

# ---------------------------------------------------------------------------
# In-memory runtime overrides (fallback when Redis is unavailable)
# ---------------------------------------------------------------------------
_runtime_overrides: dict[str, bool] = {}

_REDIS_PREFIX = "smartlic:ff:"


# ---------------------------------------------------------------------------
# Redis helpers
# ---------------------------------------------------------------------------

async def _redis_get_override(flag_name: str) -> Optional[bool]:
    """Read a single flag override from Redis. Returns None if not set."""
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            val = await redis.get(f"{_REDIS_PREFIX}{flag_name}")
            if val is not None:
                return str_to_bool(val)
    except Exception as e:
        logger.debug("Redis GET for flag %s failed: %s", flag_name, e)
    return None


async def _redis_set_override(flag_name: str, value: bool) -> bool:
    """Persist a flag override to Redis. Returns True on success."""
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            await redis.set(f"{_REDIS_PREFIX}{flag_name}", "true" if value else "false")
            return True
    except Exception as e:
        logger.warning("Redis SET for flag %s failed: %s", flag_name, e)
    return False


async def _redis_delete_override(flag_name: str) -> None:
    """Remove a flag override from Redis."""
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            await redis.delete(f"{_REDIS_PREFIX}{flag_name}")
    except Exception:
        pass


async def _redis_get_all_overrides() -> dict[str, bool]:
    """Load all flag overrides from Redis."""
    overrides: dict[str, bool] = {}
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            keys = []
            async for key in redis.scan_iter(match=f"{_REDIS_PREFIX}*", count=100):
                keys.append(key)
            if keys:
                values = await redis.mget(keys)
                for key, val in zip(keys, values):
                    flag_name = key.removeprefix(_REDIS_PREFIX)
                    if val is not None:
                        overrides[flag_name] = str_to_bool(val)
    except Exception as e:
        logger.debug("Redis SCAN for flag overrides failed: %s", e)
    return overrides


async def _redis_clear_all_overrides() -> int:
    """Remove all flag overrides from Redis. Returns count deleted."""
    count = 0
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            keys = []
            async for key in redis.scan_iter(match=f"{_REDIS_PREFIX}*", count=100):
                keys.append(key)
            if keys:
                count = await redis.delete(*keys)
    except Exception as e:
        logger.warning("Redis DELETE all flag overrides failed: %s", e)
    return count


# ---------------------------------------------------------------------------
# Resolve effective value for a flag
# ---------------------------------------------------------------------------

async def _resolve_flag_value(flag_name: str) -> tuple[bool, str]:
    """Return (value, source) for a flag.

    Priority: redis_override > memory_override > env_var > registry_default
    """
    # 1. Check Redis override
    redis_val = await _redis_get_override(flag_name)
    if redis_val is not None:
        return redis_val, "redis"

    # 2. Check in-memory override
    if flag_name in _runtime_overrides:
        return _runtime_overrides[flag_name], "memory"

    # 3. Check env var / registry default via existing function
    import os
    if flag_name in _FEATURE_FLAG_REGISTRY:
        env_var, default_str = _FEATURE_FLAG_REGISTRY[flag_name]
        env_value = os.getenv(env_var)
        if env_value is not None:
            return str_to_bool(env_value), "env"
        return str_to_bool(default_str), "default"

    # Unknown flag -- use get_feature_flag which handles non-registry flags
    return get_feature_flag(flag_name), "default"


# ---------------------------------------------------------------------------
# Flag descriptions (human-readable)
# ---------------------------------------------------------------------------

_FLAG_DESCRIPTIONS: dict[str, str] = {
    # LLM & Classification
    "ENABLE_NEW_PRICING": "New pricing model (STORY-165)",
    "LLM_ARBITER_ENABLED": "LLM classification arbiter for relevance scoring",
    "LLM_ZERO_MATCH_ENABLED": "LLM zero-match classification (GPT-4.1-nano YES/NO)",
    "ASYNC_ZERO_MATCH_ENABLED": "Async background zero-match via ARQ jobs",
    "LLM_FALLBACK_PENDING_ENABLED": "LLM fallback to pending-review status on failure",
    "BID_ANALYSIS_ENABLED": "Deep bid analysis with LLM",
    # Filter Pipeline
    "ZERO_RESULTS_RELAXATION_ENABLED": "Relax filters when zero results found",
    "CO_OCCURRENCE_RULES_ENABLED": "Keyword co-occurrence filtering rules",
    "SECTOR_RED_FLAGS_ENABLED": "Sector-specific red flag detection",
    "PROXIMITY_CONTEXT_ENABLED": "Proximity context window for keyword matching",
    "ITEM_INSPECTION_ENABLED": "Item-level inspection for gray-zone contracts",
    "FILTER_DEBUG_MODE": "Verbose filter debug logging (dev only)",
    # Term Search Quality
    "TERM_SEARCH_LLM_AWARE": "LLM-aware term search quality parity",
    "TERM_SEARCH_SYNONYMS": "Synonym expansion for term search",
    "TERM_SEARCH_VIABILITY_GENERIC": "Generic viability for term search",
    "TERM_SEARCH_FILTER_CONTEXT": "Filter context propagation for term search",
    # Data Sources
    "COMPRASGOV_ENABLED": "ComprasGov v3 data source (offline since 2026-03-03)",
    "PCP_V2_ENABLED": "Portal de Compras Publicas v2 data source",
    "DATALAKE_ENABLED": "ETL ingestion pipeline (pncp_raw_bids)",
    "DATALAKE_QUERY_ENABLED": "Query local datalake instead of live APIs",
    # Cache
    "CACHE_LEGACY_KEY_FALLBACK": "Fallback to legacy cache key format",
    "SHOW_CACHE_FALLBACK_BANNER": "Show cache fallback banner in frontend",
    "SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE": "Serve expired cache during total outage",
    # Search Pipeline
    "SEARCH_ASYNC_ENABLED": "Async search via ARQ job queue",
    "PARTIAL_DATA_SSE_ENABLED": "Partial data delivery via SSE events",
    # Cron & Operations
    "HEALTH_CANARY_ENABLED": "PNCP health canary checks (5-min interval)",
    "DIGEST_ENABLED": "Email digest cron job",
    "ALERTS_ENABLED": "Alert notifications cron job",
    "RECONCILIATION_ENABLED": "Stripe reconciliation cron job",
    # Trial & Billing
    "TRIAL_EMAILS_ENABLED": "Automated trial lifecycle emails",
    "TRIAL_PAYWALL_ENABLED": "Trial paywall after day 7 (limited results)",
    # Feature Gates (unreleased)
    "ORGANIZATIONS_ENABLED": "Organizations feature (unreleased)",
    "MESSAGES_ENABLED": "Messaging system",
    "ALERTS_SYSTEM_ENABLED": "Alerts system feature (unreleased)",
    "PARTNERS_ENABLED": "Partners feature (unreleased)",
    # Infra
    "METRICS_ENABLED": "Prometheus metrics collection",
    "RATE_LIMITING_ENABLED": "Redis token-bucket rate limiting",
    "USER_FEEDBACK_ENABLED": "User feedback collection on search results",
    "USE_REDIS_CIRCUIT_BREAKER": "Redis-backed circuit breaker (vs in-memory)",
    "COMPRASGOV_CB_ENABLED": "ComprasGov circuit breaker enabled",
}


# ---------------------------------------------------------------------------
# DEBT-205: Flag lifecycle metadata (owner, category, lifecycle)
# ---------------------------------------------------------------------------

_FLAG_LIFECYCLE: dict[str, dict] = {
    # LLM & Classification — permanent, core pipeline
    "ENABLE_NEW_PRICING": {"owner": "billing", "category": "billing", "lifecycle": "permanent", "created": "2025-11"},
    "LLM_ARBITER_ENABLED": {"owner": "search", "category": "llm", "lifecycle": "permanent", "created": "2025-10"},
    "LLM_ZERO_MATCH_ENABLED": {"owner": "search", "category": "llm", "lifecycle": "permanent", "created": "2025-10"},
    "ASYNC_ZERO_MATCH_ENABLED": {"owner": "search", "category": "llm", "lifecycle": "experimental", "created": "2025-12"},
    "LLM_FALLBACK_PENDING_ENABLED": {"owner": "search", "category": "llm", "lifecycle": "permanent", "created": "2025-12"},
    "BID_ANALYSIS_ENABLED": {"owner": "search", "category": "llm", "lifecycle": "permanent", "created": "2026-01"},
    # Filter Pipeline — permanent
    "ZERO_RESULTS_RELAXATION_ENABLED": {"owner": "search", "category": "filter", "lifecycle": "permanent", "created": "2025-11"},
    "CO_OCCURRENCE_RULES_ENABLED": {"owner": "search", "category": "filter", "lifecycle": "permanent", "created": "2025-12"},
    "SECTOR_RED_FLAGS_ENABLED": {"owner": "search", "category": "filter", "lifecycle": "permanent", "created": "2025-12"},
    "PROXIMITY_CONTEXT_ENABLED": {"owner": "search", "category": "filter", "lifecycle": "permanent", "created": "2025-12"},
    "ITEM_INSPECTION_ENABLED": {"owner": "search", "category": "filter", "lifecycle": "permanent", "created": "2025-12"},
    "FILTER_DEBUG_MODE": {"owner": "search", "category": "debug", "lifecycle": "ops-toggle", "created": "2025-10"},
    # Term Search Quality — experimental, remove when graduated
    "TERM_SEARCH_LLM_AWARE": {"owner": "search", "category": "experimental", "lifecycle": "experimental", "created": "2026-01"},
    "TERM_SEARCH_SYNONYMS": {"owner": "search", "category": "experimental", "lifecycle": "experimental", "created": "2026-01"},
    "TERM_SEARCH_VIABILITY_GENERIC": {"owner": "search", "category": "experimental", "lifecycle": "experimental", "created": "2026-01"},
    "TERM_SEARCH_FILTER_CONTEXT": {"owner": "search", "category": "experimental", "lifecycle": "experimental", "created": "2026-01"},
    # Data Sources
    "COMPRASGOV_ENABLED": {"owner": "data", "category": "source", "lifecycle": "ops-toggle", "created": "2025-10"},
    "PCP_V2_ENABLED": {"owner": "data", "category": "source", "lifecycle": "permanent", "created": "2025-10"},
    "DATALAKE_ENABLED": {"owner": "data", "category": "source", "lifecycle": "permanent", "created": "2026-01"},
    "DATALAKE_QUERY_ENABLED": {"owner": "data", "category": "source", "lifecycle": "permanent", "created": "2026-01"},
    # Cache
    "CACHE_LEGACY_KEY_FALLBACK": {"owner": "infra", "category": "cache", "lifecycle": "deprecating", "created": "2026-02", "remove_after": "2026-06"},
    "SHOW_CACHE_FALLBACK_BANNER": {"owner": "frontend", "category": "cache", "lifecycle": "ops-toggle", "created": "2026-02"},
    "SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE": {"owner": "infra", "category": "cache", "lifecycle": "permanent", "created": "2026-01"},
    # Search Pipeline
    "SEARCH_ASYNC_ENABLED": {"owner": "search", "category": "pipeline", "lifecycle": "experimental", "created": "2025-12"},
    "PARTIAL_DATA_SSE_ENABLED": {"owner": "search", "category": "pipeline", "lifecycle": "permanent", "created": "2025-12"},
    # Cron & Operations
    "HEALTH_CANARY_ENABLED": {"owner": "infra", "category": "ops", "lifecycle": "permanent", "created": "2025-11"},
    "DIGEST_ENABLED": {"owner": "email", "category": "ops", "lifecycle": "experimental", "created": "2025-12"},
    "ALERTS_ENABLED": {"owner": "email", "category": "ops", "lifecycle": "permanent", "created": "2025-12"},
    "RECONCILIATION_ENABLED": {"owner": "billing", "category": "ops", "lifecycle": "permanent", "created": "2025-12"},
    # Trial & Billing
    "TRIAL_EMAILS_ENABLED": {"owner": "billing", "category": "trial", "lifecycle": "permanent", "created": "2025-12"},
    "TRIAL_PAYWALL_ENABLED": {"owner": "billing", "category": "trial", "lifecycle": "permanent", "created": "2025-12"},
    # Feature Gates
    "ORGANIZATIONS_ENABLED": {"owner": "product", "category": "gate", "lifecycle": "gate", "created": "2026-01"},
    "MESSAGES_ENABLED": {"owner": "product", "category": "gate", "lifecycle": "gate", "created": "2025-12"},
    "ALERTS_SYSTEM_ENABLED": {"owner": "product", "category": "gate", "lifecycle": "gate", "created": "2026-01"},
    "PARTNERS_ENABLED": {"owner": "product", "category": "gate", "lifecycle": "gate", "created": "2026-01"},
    # Infra
    "METRICS_ENABLED": {"owner": "infra", "category": "infra", "lifecycle": "permanent", "created": "2025-11"},
    "RATE_LIMITING_ENABLED": {"owner": "infra", "category": "infra", "lifecycle": "permanent", "created": "2025-11"},
    "USER_FEEDBACK_ENABLED": {"owner": "product", "category": "infra", "lifecycle": "permanent", "created": "2025-12"},
    "USE_REDIS_CIRCUIT_BREAKER": {"owner": "infra", "category": "infra", "lifecycle": "permanent", "created": "2025-12"},
    "COMPRASGOV_CB_ENABLED": {"owner": "infra", "category": "infra", "lifecycle": "permanent", "created": "2026-02"},
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class FeatureFlagLifecycle(BaseModel):
    owner: str = Field("", description="Team/domain that owns this flag")
    category: str = Field("", description="Flag category (llm, filter, source, cache, etc.)")
    lifecycle: str = Field("", description="permanent | experimental | ops-toggle | gate | deprecating")
    created: str = Field("", description="Month created (YYYY-MM)")
    remove_after: str | None = Field(None, description="Planned removal date (YYYY-MM) if deprecating")


class FeatureFlagItem(BaseModel):
    name: str = Field(..., description="Flag name (e.g. LLM_ARBITER_ENABLED)")
    value: bool = Field(..., description="Current effective value")
    source: str = Field(..., description="Value source: redis, memory, env, or default")
    description: str = Field("", description="Human-readable description")
    env_var: str = Field("", description="Environment variable name")
    default: str = Field("", description="Registry default value")
    lifecycle: FeatureFlagLifecycle | None = Field(None, description="Flag lifecycle metadata")


class FeatureFlagListResponse(BaseModel):
    flags: list[FeatureFlagItem]
    total: int
    redis_available: bool


class PublicFeatureFlagItem(BaseModel):
    name: str = Field(..., description="Flag name")
    value: bool = Field(..., description="Current effective value")
    description: str = Field("", description="Human-readable description")
    category: str = Field("", description="Flag category")


class PublicFeatureFlagListResponse(BaseModel):
    flags: list[PublicFeatureFlagItem]
    total: int


class FeatureFlagUpdateRequest(BaseModel):
    value: bool = Field(..., description="New flag value (true/false)")


class FeatureFlagUpdateResponse(BaseModel):
    name: str
    value: bool
    source: str
    previous_value: bool
    previous_source: str


class FeatureFlagReloadResponse(BaseModel):
    success: bool
    flags: dict[str, bool]
    overrides_cleared: int
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=FeatureFlagListResponse)
async def list_feature_flags(
    admin: dict = Depends(require_admin),
):
    """List all registered feature flags with current values and sources.

    Returns each flag's effective value, where it comes from (redis override,
    env var, or default), its description, and registry metadata.

    Admin only.
    """
    from redis_pool import is_redis_available
    redis_ok = await is_redis_available()

    flags: list[FeatureFlagItem] = []
    for flag_name in sorted(_FEATURE_FLAG_REGISTRY.keys()):
        value, source = await _resolve_flag_value(flag_name)
        env_var, default_str = _FEATURE_FLAG_REGISTRY[flag_name]
        description = _FLAG_DESCRIPTIONS.get(flag_name, "")
        lc_data = _FLAG_LIFECYCLE.get(flag_name)
        lifecycle = FeatureFlagLifecycle(**lc_data) if lc_data else None

        flags.append(FeatureFlagItem(
            name=flag_name,
            value=value,
            source=source,
            description=description,
            env_var=env_var,
            default=default_str,
            lifecycle=lifecycle,
        ))

    return FeatureFlagListResponse(
        flags=flags,
        total=len(flags),
        redis_available=redis_ok,
    )


@router.patch("/{flag_name}", response_model=FeatureFlagUpdateResponse)
async def update_feature_flag(
    body: FeatureFlagUpdateRequest,
    flag_name: str = Path(..., description="Feature flag name from the registry"),
    admin: dict = Depends(require_admin),
):
    """Update a feature flag value at runtime (admin only).

    The new value is persisted to Redis (if available) and stored in-memory.
    Takes effect immediately -- no container restart required.

    The change persists across process restarts as long as Redis is available.
    Use POST /admin/feature-flags/reload to clear all overrides.
    """
    if flag_name not in _FEATURE_FLAG_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"Flag '{flag_name}' not found in registry. "
                   f"Available flags: {', '.join(sorted(_FEATURE_FLAG_REGISTRY.keys())[:10])}...",
        )

    # Capture previous state
    prev_value, prev_source = await _resolve_flag_value(flag_name)

    new_value = body.value

    # Persist to Redis (primary) and in-memory (fallback)
    redis_stored = await _redis_set_override(flag_name, new_value)
    _runtime_overrides[flag_name] = new_value

    # Clear the TTL cache so get_feature_flag() picks up new value
    if flag_name in _feature_flag_cache:
        del _feature_flag_cache[flag_name]

    source = "redis" if redis_stored else "memory"

    log_admin_action(
        logger,
        admin_id=admin["id"],
        action="update-feature-flag",
        target_user_id=admin["id"],
        details={
            "flag": flag_name,
            "old_value": prev_value,
            "new_value": new_value,
            "source": source,
        },
    )

    await audit_logger.log(
        event_type="admin.feature_flag_change",
        actor_id=admin["id"],
        target_id=flag_name,
        ip_address=None,
        details={
            "flag_name": flag_name,
            "old_value": str(prev_value),
            "new_value": str(new_value),
            "old_source": prev_source,
        },
    )

    logger.info(
        "Feature flag %s changed: %s -> %s (source=%s, by=%s)",
        flag_name, prev_value, new_value, source, admin["id"][:8],
    )

    return FeatureFlagUpdateResponse(
        name=flag_name,
        value=new_value,
        source=source,
        previous_value=prev_value,
        previous_source=prev_source,
    )


@router.post("/reload", response_model=FeatureFlagReloadResponse)
async def reload_flags_endpoint(
    admin: dict = Depends(require_admin),
):
    """Reload all feature flags from environment variables (admin only).

    This clears:
    1. All Redis overrides (smartlic:ff:* keys)
    2. All in-memory overrides
    3. The feature flag TTL cache

    After reload, flags return to their env var or registry default values.
    Useful after updating env vars via Railway dashboard without restarting.
    """
    # Clear Redis overrides
    redis_cleared = await _redis_clear_all_overrides()

    # Clear in-memory overrides
    memory_cleared = len(_runtime_overrides)
    _runtime_overrides.clear()

    # Reload from env via existing function (clears TTL cache)
    current_values = reload_feature_flags()

    total_cleared = redis_cleared + memory_cleared

    log_admin_action(
        logger,
        admin_id=admin["id"],
        action="reload-feature-flags-full",
        target_user_id=admin["id"],
        details={
            "redis_cleared": redis_cleared,
            "memory_cleared": memory_cleared,
            "flags": current_values,
        },
    )

    logger.info(
        "Feature flags fully reloaded: %d Redis + %d memory overrides cleared (by=%s)",
        redis_cleared, memory_cleared, admin["id"][:8],
    )

    return FeatureFlagReloadResponse(
        success=True,
        flags=current_values,
        overrides_cleared=total_cleared,
        message=f"All flags reloaded from environment. {total_cleared} override(s) cleared.",
    )


# ---------------------------------------------------------------------------
# DEBT-205: Public Feature Flags endpoint (for frontend consumption)
# ---------------------------------------------------------------------------

public_router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


@public_router.get("/experiments")
async def get_experiments(user: dict = Depends(require_auth)):
    """Return active experiment variants for the authenticated user."""
    from services.ab_testing import get_user_experiments
    user_id = user.get("id", "")
    variants = get_user_experiments(user_id)
    return {"experiments": variants}


@public_router.get("", response_model=PublicFeatureFlagListResponse)
async def list_public_feature_flags(
    _user: dict = Depends(require_auth),
):
    """List all feature flags with current values (authenticated users).

    DEBT-205 / DEBT-SYS-009: Public endpoint consumed by frontend via SWR.
    Returns flag name, value, description, and category — no admin metadata.
    """
    flags: list[PublicFeatureFlagItem] = []
    for flag_name in sorted(_FEATURE_FLAG_REGISTRY.keys()):
        value, _source = await _resolve_flag_value(flag_name)
        description = _FLAG_DESCRIPTIONS.get(flag_name, "")
        lc_data = _FLAG_LIFECYCLE.get(flag_name, {})
        category = lc_data.get("category", "other")

        flags.append(PublicFeatureFlagItem(
            name=flag_name,
            value=value,
            description=description,
            category=category,
        ))

    return PublicFeatureFlagListResponse(flags=flags, total=len(flags))
