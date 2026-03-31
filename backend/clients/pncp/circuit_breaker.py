"""Circuit breaker implementations for PNCP and other data sources.

Contains PNCPCircuitBreaker (in-memory), RedisCircuitBreaker (shared across
Gunicorn workers), module-level singletons, and get_circuit_breaker factory.
"""

import asyncio
import logging
import time
from typing import Optional

from config import (
    RetryConfig, DEFAULT_MODALIDADES, MODALIDADES_EXCLUIDAS,
    PNCP_CIRCUIT_BREAKER_THRESHOLD, PNCP_CIRCUIT_BREAKER_COOLDOWN,
    PCP_CIRCUIT_BREAKER_THRESHOLD, PCP_CIRCUIT_BREAKER_COOLDOWN,
    COMPRASGOV_CIRCUIT_BREAKER_THRESHOLD, COMPRASGOV_CIRCUIT_BREAKER_COOLDOWN,
    PNCP_TIMEOUT_PER_MODALITY, PNCP_MODALITY_RETRY_BACKOFF,
    PNCP_TIMEOUT_PER_UF, PNCP_TIMEOUT_PER_UF_DEGRADED,
    PNCP_BATCH_SIZE, PNCP_BATCH_DELAY_S,
    USE_REDIS_CIRCUIT_BREAKER, CB_REDIS_TTL,
    LICITAJA_CIRCUIT_BREAKER_THRESHOLD, LICITAJA_CIRCUIT_BREAKER_COOLDOWN,
)
from metrics import CIRCUIT_BREAKER_STATE

logger = logging.getLogger(__name__)


class PNCPCircuitBreaker:
    """Circuit breaker for API sources to prevent cascading failures.

    After ``threshold`` consecutive timeouts, the circuit breaker marks the
    source as *degraded* for ``cooldown_seconds``. While degraded, callers
    should skip that source and use alternatives.

    Each source (PNCP, PCP, etc.) gets its own named instance so failures
    in one source don't cascade to others (GTM-FIX-005 AC9).

    Thread-safety: asyncio.Lock around state mutations.

    Attributes:
        name: Identifier for this circuit breaker instance (e.g. "pncp", "pcp").
        consecutive_failures: Running count of consecutive timeout failures.
        degraded_until: Unix timestamp until which source is considered degraded.
        threshold: Number of consecutive failures before tripping.
        cooldown_seconds: Duration in seconds to stay degraded after tripping.
    """

    def __init__(
        self,
        name: str = "pncp",
        threshold: int = PNCP_CIRCUIT_BREAKER_THRESHOLD,
        cooldown_seconds: int = PNCP_CIRCUIT_BREAKER_COOLDOWN,
    ):
        self.name = name
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds
        self.consecutive_failures: int = 0
        self.degraded_until: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def is_degraded(self) -> bool:
        """Return True if the circuit breaker is currently in degraded state.

        Read-only check — no side effects. Use try_recover() to actually reset.
        """
        if self.degraded_until is None:
            return False
        if time.time() >= self.degraded_until:
            return False  # Cooldown expired, but don't mutate here
        return True

    async def record_failure(self) -> None:
        """Record a timeout/failure. Trips the breaker after ``threshold`` consecutive failures."""
        async with self._lock:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.threshold and not self.is_degraded:
                self.degraded_until = time.time() + self.cooldown_seconds
                CIRCUIT_BREAKER_STATE.labels(source=self.name).set(1)
                logger.warning(
                    f"Circuit breaker [{self.name}] TRIPPED after {self.consecutive_failures} "
                    f"consecutive failures — degraded for {self.cooldown_seconds}s"
                )
                # STORY-305 AC13: Sentry breadcrumb on state transition
                try:
                    import sentry_sdk
                    sentry_sdk.add_breadcrumb(
                        category="circuit_breaker",
                        message=f"CB [{self.name}] OPEN after {self.consecutive_failures} failures",
                        level="warning",
                        data={"source": self.name, "failures": self.consecutive_failures, "cooldown_s": self.cooldown_seconds},
                    )
                except Exception:
                    pass

    async def record_success(self) -> None:
        """Record a successful request. Resets the failure counter."""
        async with self._lock:
            self.consecutive_failures = 0

    async def try_recover(self) -> bool:
        """Check if cooldown has expired and reset if so. Must be called with await.

        Returns True if the breaker was reset (recovered), False if still degraded.
        """
        if self.degraded_until is None:
            return True  # Already healthy

        if time.time() < self.degraded_until:
            return False  # Still in cooldown

        try:
            await asyncio.wait_for(self._lock.acquire(), timeout=1.0)
            try:
                # Double-check under lock
                if self.degraded_until is not None and time.time() >= self.degraded_until:
                    self.degraded_until = None
                    self.consecutive_failures = 0
                    CIRCUIT_BREAKER_STATE.labels(source=self.name).set(0)
                    logger.info(
                        f"Circuit breaker [{self.name}] cooldown expired — resetting to healthy"
                    )
                    # STORY-305 AC13: Sentry breadcrumb on state transition
                    try:
                        import sentry_sdk
                        sentry_sdk.add_breadcrumb(
                            category="circuit_breaker",
                            message=f"CB [{self.name}] CLOSED (recovered)",
                            level="info",
                            data={"source": self.name},
                        )
                    except Exception:
                        pass
                    return True
            finally:
                self._lock.release()
        except asyncio.TimeoutError:
            logger.warning(
                f"Circuit breaker [{self.name}] lock timeout in try_recover — "
                f"proceeding with current state"
            )

        return not self.is_degraded

    async def initialize(self) -> None:
        """Initialize circuit breaker (no-op for base class).

        RedisCircuitBreaker overrides this to restore state from Redis.
        Base class has no persistent state to restore.
        """
        pass

    def reset(self) -> None:
        """Manually reset the circuit breaker (for testing or admin use)."""
        self.consecutive_failures = 0
        self.degraded_until = None


class RedisCircuitBreaker(PNCPCircuitBreaker):
    """Circuit breaker with Redis-backed shared state (B-06).

    Extends PNCPCircuitBreaker to share state across Gunicorn workers via Redis.
    Falls back to per-worker local state when Redis is unavailable.

    All public methods and properties remain backward-compatible with
    PNCPCircuitBreaker — callers don't need any changes (AC11).

    Redis keys (per source):
        circuit_breaker:{name}:failures       → INT  (INCR atomic)
        circuit_breaker:{name}:degraded_until → STRING (unix timestamp)
    """

    # Lua script for atomic record_failure (AC3)
    # Keys: [1] failures, [2] degraded_until
    # Args: [1] threshold, [2] cooldown, [3] now (timestamp), [4] key TTL
    _FAILURE_SCRIPT = """
local failures = redis.call('INCR', KEYS[1])
redis.call('EXPIRE', KEYS[1], tonumber(ARGV[4]))
if failures >= tonumber(ARGV[1]) then
    local existing = redis.call('GET', KEYS[2])
    if not existing then
        local until_ts = tonumber(ARGV[3]) + tonumber(ARGV[2])
        redis.call('SET', KEYS[2], tostring(until_ts))
        redis.call('EXPIRE', KEYS[2], tonumber(ARGV[2]))
        return {failures, 1}
    end
end
return {failures, 0}
"""

    def __init__(
        self,
        name: str = "pncp",
        threshold: int = PNCP_CIRCUIT_BREAKER_THRESHOLD,
        cooldown_seconds: int = PNCP_CIRCUIT_BREAKER_COOLDOWN,
    ):
        super().__init__(name, threshold, cooldown_seconds)
        self._key_failures = f"circuit_breaker:{name}:failures"
        self._key_degraded = f"circuit_breaker:{name}:degraded_until"
        self._ttl = CB_REDIS_TTL

    async def _get_redis(self):
        """Get Redis pool (delegates to redis_pool module caching)."""
        from redis_pool import get_redis_pool
        return await get_redis_pool()

    async def record_failure(self) -> None:
        """Record failure atomically via Redis Lua script (AC3).

        Falls back to local state if Redis is unavailable.
        """
        redis = await self._get_redis()
        if redis:
            try:
                result = await redis.eval(
                    self._FAILURE_SCRIPT,
                    2,
                    self._key_failures,
                    self._key_degraded,
                    str(self.threshold),
                    str(self.cooldown_seconds),
                    str(time.time()),
                    str(self._ttl),
                )
                # Sync local state for sync property access
                self.consecutive_failures = int(result[0])
                if int(result[1]) == 1:
                    self.degraded_until = time.time() + self.cooldown_seconds
                    CIRCUIT_BREAKER_STATE.labels(source=self.name).set(1)
                    logger.warning(
                        f"Circuit breaker [{self.name}] TRIPPED after "
                        f"{self.consecutive_failures} consecutive failures "
                        f"— degraded for {self.cooldown_seconds}s"
                    )
                return
            except Exception as e:
                logger.debug(f"Redis CB record_failure fallback: {e}")
        await super().record_failure()

    async def record_success(self) -> None:
        """Reset failure counter in Redis (AC4).

        Falls back to local state if Redis is unavailable.
        """
        redis = await self._get_redis()
        if redis:
            try:
                pipe = redis.pipeline()
                pipe.set(self._key_failures, 0)
                pipe.expire(self._key_failures, self._ttl)
                pipe.delete(self._key_degraded)
                await pipe.execute()
                self.consecutive_failures = 0
                self.degraded_until = None
                return
            except Exception as e:
                logger.debug(f"Redis CB record_success fallback: {e}")
        await super().record_success()

    async def try_recover(self) -> bool:
        """Check Redis for cooldown expiry and reset if expired (AC5).

        Falls back to local state if Redis is unavailable.
        """
        redis = await self._get_redis()
        if redis:
            try:
                val = await redis.get(self._key_degraded)
                if val is None:
                    self.degraded_until = None
                    self.consecutive_failures = 0
                    return True
                degraded_until = float(val)
                if time.time() >= degraded_until:
                    pipe = redis.pipeline()
                    pipe.delete(self._key_degraded)
                    pipe.set(self._key_failures, 0)
                    pipe.expire(self._key_failures, self._ttl)
                    await pipe.execute()
                    self.degraded_until = None
                    self.consecutive_failures = 0
                    CIRCUIT_BREAKER_STATE.labels(source=self.name).set(0)
                    logger.info(
                        f"Circuit breaker [{self.name}] cooldown expired "
                        f"— resetting to healthy"
                    )
                    return True
                self.degraded_until = degraded_until
                return False
            except Exception as e:
                logger.debug(f"Redis CB try_recover fallback: {e}")
        return await super().try_recover()

    async def is_degraded_async(self) -> bool:
        """Async check of degraded state from Redis (AC2, AC9).

        Unlike the sync ``is_degraded`` property (which reads local state),
        this method queries Redis for the authoritative cross-worker state.
        """
        redis = await self._get_redis()
        if redis:
            try:
                val = await redis.get(self._key_degraded)
                if val is None:
                    return False
                return time.time() < float(val)
            except Exception as e:
                logger.debug(f"Redis CB fallback (is_degraded_async): {e}")
        return self.is_degraded

    async def get_state(self) -> dict:
        """Get full circuit breaker state for health endpoint (AC9)."""
        redis = await self._get_redis()
        if redis:
            try:
                pipe = redis.pipeline()
                pipe.get(self._key_failures)
                pipe.get(self._key_degraded)
                results = await pipe.execute()
                failures = int(results[0]) if results[0] else 0
                degraded_until = float(results[1]) if results[1] else None
                is_degraded = (
                    degraded_until is not None and time.time() < degraded_until
                )
                return {
                    "status": "degraded" if is_degraded else "healthy",
                    "failures": failures,
                    "degraded": is_degraded,
                    "degraded_until": degraded_until,
                    "backend": "redis",
                }
            except Exception as e:
                logger.debug(f"Redis CB fallback (get_state): {e}")
        return {
            "status": "degraded" if self.is_degraded else "healthy",
            "failures": self.consecutive_failures,
            "degraded": self.is_degraded,
            "degraded_until": self.degraded_until,
            "backend": "local",
        }

    async def initialize(self) -> None:
        """Initialize circuit breaker by restoring state from Redis (GTM-CRIT-005 AC5).

        Should be called once at application startup to sync local state with
        the authoritative Redis state. This ensures that after a worker restart,
        the circuit breaker reflects any degraded state persisted by other workers.

        If Redis is unavailable, local state remains at defaults (healthy).
        """
        redis = await self._get_redis()
        if redis:
            try:
                pipe = redis.pipeline()
                pipe.get(self._key_failures)
                pipe.get(self._key_degraded)
                results = await pipe.execute()

                # Restore failure count
                if results[0]:
                    self.consecutive_failures = int(results[0])
                    logger.debug(
                        f"Circuit breaker [{self.name}] restored {self.consecutive_failures} "
                        f"failures from Redis"
                    )

                # Restore degraded state if still active
                if results[1]:
                    degraded_until = float(results[1])
                    if time.time() < degraded_until:
                        self.degraded_until = degraded_until
                        CIRCUIT_BREAKER_STATE.labels(source=self.name).set(1)
                        logger.warning(
                            f"Circuit breaker [{self.name}] restored DEGRADED state "
                            f"from Redis — degraded until {degraded_until:.0f}"
                        )
                    else:
                        # Cooldown expired in Redis — clean up
                        logger.info(
                            f"Circuit breaker [{self.name}] found expired degraded state "
                            f"in Redis — resetting to healthy"
                        )
                        await self.try_recover()
            except Exception as e:
                logger.debug(f"Circuit breaker [{self.name}] initialize fallback: {e}")

    async def reset_async(self) -> None:
        """Reset both local and Redis state."""
        super().reset()
        redis = await self._get_redis()
        if redis:
            try:
                pipe = redis.pipeline()
                pipe.delete(self._key_failures)
                pipe.delete(self._key_degraded)
                await pipe.execute()
            except Exception as e:
                logger.debug(f"Redis CB fallback (reset_async): {e}")


# Module-level singletons — one per data source (GTM-FIX-005 AC9)
# B-06: Use RedisCircuitBreaker for shared state across workers when enabled.
# Fallback to PNCPCircuitBreaker (per-worker) when USE_REDIS_CIRCUIT_BREAKER=false
# or when Redis is unavailable at runtime.
_CBClass = RedisCircuitBreaker if USE_REDIS_CIRCUIT_BREAKER else PNCPCircuitBreaker
_circuit_breaker = _CBClass(
    name="pncp",
    threshold=PNCP_CIRCUIT_BREAKER_THRESHOLD,
    cooldown_seconds=PNCP_CIRCUIT_BREAKER_COOLDOWN,
)
_pcp_circuit_breaker = _CBClass(
    name="pcp",
    threshold=PCP_CIRCUIT_BREAKER_THRESHOLD,
    cooldown_seconds=PCP_CIRCUIT_BREAKER_COOLDOWN,
)
# STORY-305 AC1/AC2: ComprasGov circuit breaker — same class, same CB implementation
_comprasgov_circuit_breaker = _CBClass(
    name="comprasgov",
    threshold=COMPRASGOV_CIRCUIT_BREAKER_THRESHOLD,
    cooldown_seconds=COMPRASGOV_CIRCUIT_BREAKER_COOLDOWN,
)
# LicitaJá circuit breaker
_licitaja_circuit_breaker = _CBClass(
    name="licitaja",
    threshold=LICITAJA_CIRCUIT_BREAKER_THRESHOLD,
    cooldown_seconds=LICITAJA_CIRCUIT_BREAKER_COOLDOWN,
)


def get_circuit_breaker(source: str = "pncp") -> PNCPCircuitBreaker:
    """Return the circuit breaker singleton for a given data source.

    Args:
        source: "pncp" (default), "pcp", "comprasgov", or "licitaja".
    """
    if source == "pcp":
        return _pcp_circuit_breaker
    if source == "comprasgov":
        return _comprasgov_circuit_breaker
    if source == "licitaja":
        return _licitaja_circuit_breaker
    return _circuit_breaker
