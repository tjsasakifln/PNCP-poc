"""Rate limiting with Redis + in-memory fallback.

STORY-203 SYS-M03: In-memory rate limiter with max size limit
STORY-217: Uses unified redis_pool for Redis connections
B-06: RedisRateLimiter — shared token bucket for PNCP/PCP API requests
GTM-GO-002: Per-user/per-IP rate limiting for anti-abuse protection
"""

import asyncio
import logging
import os
import time as _time
import uuid as _uuid
from datetime import datetime, timezone

from fastapi import HTTPException, Request

from redis_pool import get_redis_pool

logger = logging.getLogger(__name__)

MAX_MEMORY_STORE_SIZE = 10_000

# ============================================================================
# GTM-GO-002: Rate Limit Configuration (env var overridable)
# ============================================================================
SEARCH_RATE_LIMIT_PER_MINUTE = int(os.getenv("SEARCH_RATE_LIMIT_PER_MINUTE", "10"))
AUTH_RATE_LIMIT_PER_5MIN = int(os.getenv("AUTH_RATE_LIMIT_PER_5MIN", "5"))
SIGNUP_RATE_LIMIT_PER_10MIN = int(os.getenv("SIGNUP_RATE_LIMIT_PER_10MIN", "3"))
SSE_MAX_CONNECTIONS = int(os.getenv("SSE_MAX_CONNECTIONS", "3"))


class RateLimiter:
    """Token bucket rate limiter using shared Redis pool + in-memory fallback.

    STORY-217: No longer creates its own Redis connection.
    """

    def __init__(self):
        self._memory_store: dict[str, tuple[int, float]] = {}

    async def check_rate_limit(self, user_id: str, max_requests_per_min: int) -> tuple[bool, int]:
        """Check if user is within rate limit.

        Returns:
            tuple: (allowed: bool, retry_after_seconds: int)
        """
        minute_key = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
        key = f"rate_limit:{user_id}:{minute_key}"

        redis = await get_redis_pool()
        if redis:
            return await self._check_redis(redis, key, max_requests_per_min)
        else:
            return self._check_memory(key, max_requests_per_min)

    async def _check_redis(self, redis, key: str, limit: int) -> tuple[bool, int]:
        """Check rate limit using shared Redis pool."""
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 60)

            if count > limit:
                ttl = await redis.ttl(key)
                return (False, max(1, ttl))

            return (True, 0)

        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e} — allowing request")
            return (True, 0)

    def _check_memory(self, key: str, limit: int) -> tuple[bool, int]:
        """Check rate limit using in-memory dict (fallback)."""
        now = datetime.now(timezone.utc).timestamp()

        cleaned_store = {
            k: (count, ts)
            for k, (count, ts) in self._memory_store.items()
            if now - ts < 60
        }

        if len(cleaned_store) > MAX_MEMORY_STORE_SIZE:
            sorted_items = sorted(cleaned_store.items(), key=lambda item: item[1][1])
            cleaned_store = dict(sorted_items[-MAX_MEMORY_STORE_SIZE:])
            logger.warning(
                f"In-memory rate limiter exceeded {MAX_MEMORY_STORE_SIZE} entries. "
                f"Evicted oldest entries (LRU)."
            )

        self._memory_store = cleaned_store

        if key in self._memory_store:
            count, timestamp = self._memory_store[key]
            if now - timestamp >= 60:
                self._memory_store[key] = (1, now)
                return (True, 0)
            elif count >= limit:
                retry_after = int(60 - (now - timestamp))
                return (False, max(1, retry_after))
            else:
                self._memory_store[key] = (count + 1, timestamp)
                return (True, 0)
        else:
            self._memory_store[key] = (1, now)
            return (True, 0)


# Global instance
rate_limiter = RateLimiter()


# ============================================================================
# B-06: Shared Token Bucket Rate Limiter (PNCP/PCP API requests)
# ============================================================================

class RedisRateLimiter:
    """Shared token bucket rate limiter via Redis (B-06 AC6).

    Ensures total request rate across all Gunicorn workers stays within limits.
    Uses atomic Lua script for token bucket implementation.

    Fallback: returns True (allows request) when Redis is unavailable,
    letting the per-worker local rate limiter handle it.

    Redis keys:
        rate_limiter:{name}:bucket          → HASH {tokens, last_refill}
        rate_limiter:{name}:requests_count  → INT (requests in current minute)
    """

    _BUCKET_SCRIPT = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or max_tokens
local last_refill = tonumber(bucket[2]) or now

local elapsed = now - last_refill
local new_tokens = math.min(max_tokens, tokens + elapsed * refill_rate)

if new_tokens >= 1 then
    redis.call('HMSET', key, 'tokens', new_tokens - 1, 'last_refill', now)
    redis.call('EXPIRE', key, 60)
    return 1
else
    redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 60)
    return 0
end
"""

    def __init__(
        self,
        name: str = "pncp",
        max_tokens: int = 10,
        refill_rate: float = 10.0,
    ):
        self.name = name
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self._key = f"rate_limiter:{name}:bucket"
        self._requests_key = f"rate_limiter:{name}:requests_count"

    async def acquire(self, timeout: float = 5.0) -> bool:
        """Acquire a token from the shared bucket.

        Returns True if token acquired or Redis unavailable (fail-open).
        Waits with exponential backoff up to ``timeout`` seconds if rate limited.
        """
        redis = await get_redis_pool()
        if not redis:
            return True  # Fail open — per-worker limiter handles it

        start = _time.time()
        backoff = 0.05  # 50ms initial

        while True:
            try:
                now = _time.time()
                result = await redis.eval(
                    self._BUCKET_SCRIPT,
                    1,
                    self._key,
                    str(self.max_tokens),
                    str(self.refill_rate),
                    str(now),
                )

                if int(result) == 1:
                    # Token acquired — track request count for metrics
                    try:
                        pipe = redis.pipeline()
                        pipe.incr(self._requests_key)
                        pipe.expire(self._requests_key, 60)
                        await pipe.execute()
                    except Exception:
                        pass
                    return True

                # Rate limited — check timeout
                elapsed = _time.time() - start
                if elapsed >= timeout:
                    return False

                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 0.5)

            except Exception as e:
                logger.debug(f"Redis rate limiter error: {e} — allowing request")
                return True  # Fail open

    async def get_stats(self) -> dict:
        """Get rate limiter statistics for health endpoint (AC10)."""
        redis = await get_redis_pool()
        if not redis:
            return {
                "backend": "local",
                "tokens_available": None,
                "requests_last_minute": None,
            }

        try:
            bucket = await redis.hmget(self._key, "tokens", "last_refill")
            tokens = float(bucket[0]) if bucket[0] else float(self.max_tokens)
            requests = await redis.get(self._requests_key)
            return {
                "backend": "redis",
                "tokens_available": round(tokens, 1),
                "requests_last_minute": int(requests) if requests else 0,
            }
        except Exception:
            return {
                "backend": "error",
                "tokens_available": None,
                "requests_last_minute": None,
            }


# Global shared rate limiter instances (B-06)
pncp_rate_limiter = RedisRateLimiter(name="pncp", max_tokens=10, refill_rate=10.0)
pcp_rate_limiter = RedisRateLimiter(name="pcp", max_tokens=5, refill_rate=5.0)


# ============================================================================
# GTM-GO-002: Flexible Rate Limiter (arbitrary time windows)
# ============================================================================

class FlexibleRateLimiter:
    """Rate limiter with configurable time windows (not just per-minute).

    Uses window-bucketing: requests are grouped into fixed-size time windows.
    Each bucket tracks count + creation timestamp.

    Redis: INCR + EXPIRE (atomic, distributed).
    InMemory: dict with LRU eviction (single-process fallback).
    """

    def __init__(self):
        self._memory_store: dict[str, tuple[int, float]] = {}

    async def check_rate_limit(
        self, key: str, max_requests: int, window_seconds: int
    ) -> tuple[bool, int]:
        """Check if key is within rate limit.

        Args:
            key: Unique identifier (e.g., "/buscar:user:abc-123").
            max_requests: Maximum requests allowed in the window.
            window_seconds: Time window in seconds.

        Returns:
            tuple: (allowed: bool, retry_after_seconds: int)
        """
        window_id = int(_time.time()) // window_seconds
        full_key = f"rl:{key}:{window_id}"

        redis = await get_redis_pool()
        if redis:
            return await self._check_redis(redis, full_key, max_requests, window_seconds)
        return self._check_memory(full_key, max_requests, window_seconds)

    async def _check_redis(
        self, redis, key: str, limit: int, window_seconds: int
    ) -> tuple[bool, int]:
        """Check rate limit using shared Redis pool."""
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window_seconds)

            if count > limit:
                ttl = await redis.ttl(key)
                return (False, max(1, ttl))

            return (True, 0)

        except Exception as e:
            logger.error(f"Redis error in flexible rate limiting: {e}")
            return self._check_memory(key, limit, window_seconds)

    def _check_memory(
        self, key: str, limit: int, window_seconds: int
    ) -> tuple[bool, int]:
        """Check rate limit using in-memory dict (fallback)."""
        now = _time.time()

        # Clean expired entries
        self._memory_store = {
            k: (count, ts)
            for k, (count, ts) in self._memory_store.items()
            if now - ts < window_seconds * 2  # Keep for 2x window to handle edge cases
        }

        if len(self._memory_store) > MAX_MEMORY_STORE_SIZE:
            sorted_items = sorted(self._memory_store.items(), key=lambda x: x[1][1])
            self._memory_store = dict(sorted_items[-MAX_MEMORY_STORE_SIZE:])

        if key in self._memory_store:
            count, timestamp = self._memory_store[key]
            if now - timestamp >= window_seconds:
                self._memory_store[key] = (1, now)
                return (True, 0)
            elif count >= limit:
                retry_after = int(window_seconds - (now - timestamp))
                return (False, max(1, retry_after))
            else:
                self._memory_store[key] = (count + 1, timestamp)
                return (True, 0)
        else:
            self._memory_store[key] = (1, now)
            return (True, 0)


# Global flexible rate limiter instance
_flexible_limiter = FlexibleRateLimiter()


# ============================================================================
# GTM-GO-002: SSE Connection Tracker (per-user concurrent limit)
# ============================================================================

_sse_connections: dict[str, int] = {}
_sse_lock = asyncio.Lock()


async def acquire_sse_connection(user_id: str) -> bool:
    """Acquire an SSE connection slot for the user.

    Returns True if slot acquired, False if at max connections.
    """
    async with _sse_lock:
        current = _sse_connections.get(user_id, 0)
        if current >= SSE_MAX_CONNECTIONS:
            return False
        _sse_connections[user_id] = current + 1
        return True


async def release_sse_connection(user_id: str) -> None:
    """Release an SSE connection slot for the user."""
    async with _sse_lock:
        current = _sse_connections.get(user_id, 0)
        if current > 0:
            _sse_connections[user_id] = current - 1
        if _sse_connections.get(user_id, 0) == 0:
            _sse_connections.pop(user_id, None)


# ============================================================================
# GTM-GO-002: require_rate_limit — FastAPI Depends for per-user/per-IP limiting
# ============================================================================

def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _extract_user_id_from_jwt(auth_header: str) -> str | None:
    """Extract user_id (sub claim) from JWT without full verification.

    Used only for rate limit keying — not a security check.
    The actual auth check is handled by require_auth dependency.
    """
    if not auth_header.startswith("Bearer "):
        return None
    try:
        import base64
        import json

        token = auth_header[7:]
        payload_b64 = token.split(".")[1]
        # Add base64 padding
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("sub")
    except Exception:
        return None


def require_rate_limit(max_requests: int, window_seconds: int):
    """FastAPI dependency for per-user/per-IP rate limiting.

    Uses user_id (from JWT sub claim) for authenticated requests,
    falls back to client IP for unauthenticated requests (AC9).

    Rate limit state uses Redis when available, InMemory fallback (AC8).
    Disabled entirely when RATE_LIMITING_ENABLED=false (AC10).

    Args:
        max_requests: Maximum requests allowed in the window.
        window_seconds: Time window in seconds.

    Returns:
        Async callable for use with FastAPI Depends.

    Examples:
        # 10 requests per minute (search endpoint)
        @router.post("/buscar")
        async def buscar(
            ...,
            _rl=Depends(require_rate_limit(10, 60)),
        ):

        # 5 requests per 5 minutes (login endpoint)
        @router.post("/login")
        async def login(
            ...,
            _rl=Depends(require_rate_limit(5, 300)),
        ):
    """

    async def _check(request: Request):
        from config import get_feature_flag

        if not get_feature_flag("RATE_LIMITING_ENABLED"):
            return

        # Determine rate limit key: user_id or IP (AC9)
        auth_header = request.headers.get("authorization", "")
        user_id = _extract_user_id_from_jwt(auth_header)

        if user_id:
            limit_key = f"user:{user_id}"
            limit_type = "user"
        else:
            ip = _get_client_ip(request)
            limit_key = f"ip:{ip}"
            limit_type = "ip"

        endpoint = request.url.path
        full_key = f"{endpoint}:{limit_key}"

        allowed, retry_after = await _flexible_limiter.check_rate_limit(
            full_key, max_requests, window_seconds
        )

        if not allowed:
            correlation_id = request.headers.get(
                "x-correlation-id", str(_uuid.uuid4())
            )

            # AC13: Log WARNING with required fields
            logger.warning(
                "Rate limit exceeded: endpoint=%s %s=%s "
                "current_count=%d limit=%d/%ds correlation_id=%s",
                endpoint,
                limit_type,
                user_id if user_id else _get_client_ip(request),
                max_requests,
                max_requests,
                window_seconds,
                correlation_id,
            )

            # AC14: Increment Prometheus counter
            try:
                from metrics import RATE_LIMIT_EXCEEDED

                RATE_LIMIT_EXCEEDED.labels(
                    endpoint=endpoint, limit_type=limit_type
                ).inc()
            except Exception:
                pass

            # AC2 + AC3: Return 429 with structured body and Retry-After header
            raise HTTPException(
                status_code=429,
                detail={
                    "detail": f"Limite de requisições excedido. Tente novamente em {retry_after} segundos.",
                    "retry_after_seconds": retry_after,
                    "correlation_id": correlation_id,
                },
                headers={"Retry-After": str(retry_after)},
            )

    return _check
