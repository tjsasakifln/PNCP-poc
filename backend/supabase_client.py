"""Supabase client singleton for backend operations.

STORY-291: Circuit breaker pattern for Supabase calls.
CRIT-046: Connection pool exhaustion fix — enlarged httpx pool,
explicit timeouts, pool utilization metrics, ConnectionError retry.
"""

import asyncio
import os
import logging
import threading
import time
from collections import deque
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Lazy import to avoid breaking existing tests that don't have supabase installed
_supabase_client = None

# ============================================================================
# CRIT-046: Connection pool configuration
# ============================================================================

_POOL_MAX_CONNECTIONS = 50
_POOL_MAX_KEEPALIVE = 20
_POOL_TIMEOUT = 30.0
_POOL_CONNECT_TIMEOUT = 10.0
_POOL_HIGH_WATER_RATIO = 0.8  # Log warning when pool > 80% utilization
_RETRY_DELAY_S = 1.0  # AC5: delay between retries

# Thread-safe active connection counter (for high-water logging)
_pool_active_lock = threading.Lock()
_pool_active_count = 0


def _get_config():
    """Get Supabase configuration from environment."""
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
            "Get these from your Supabase project settings."
        )
    return url, service_key


def get_supabase():
    """Get or create Supabase admin client (uses service role key).

    Returns:
        supabase.Client: Authenticated Supabase client with admin privileges.

    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set.
    """
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        url, key = _get_config()
        _supabase_client = create_client(url, key)
        _configure_httpx_pool(_supabase_client)
        logger.info("Supabase client initialized")
    return _supabase_client


def _configure_httpx_pool(client):
    """CRIT-046 AC3/AC4: Enlarge httpx connection pool and set explicit timeouts.

    Default httpx pool: max_connections=10, max_keepalive_connections=5.
    With 2 Gunicorn workers + ARQ + SWR + cron, easily > 10 concurrent connections.

    New pool: max_connections=50, max_keepalive_connections=20.
    Timeout: 30s total, 10s connect (instead of httpx default 5s).
    """
    try:
        import httpx

        postgrest = client.postgrest
        old_session = postgrest.session

        new_session = httpx.Client(
            base_url=old_session.base_url,
            headers=dict(old_session.headers),
            timeout=httpx.Timeout(_POOL_TIMEOUT, connect=_POOL_CONNECT_TIMEOUT),
            transport=httpx.HTTPTransport(
                limits=httpx.Limits(
                    max_connections=_POOL_MAX_CONNECTIONS,
                    max_keepalive_connections=_POOL_MAX_KEEPALIVE,
                ),
                http2=True,
            ),
            follow_redirects=True,
        )

        old_session.close()
        postgrest.session = new_session

        logger.info(
            "CRIT-046: httpx pool configured — max_connections=%d, "
            "max_keepalive=%d, timeout=%.0fs/connect=%.0fs",
            _POOL_MAX_CONNECTIONS, _POOL_MAX_KEEPALIVE,
            _POOL_TIMEOUT, _POOL_CONNECT_TIMEOUT,
        )
    except Exception as e:
        logger.warning("CRIT-046: Failed to configure httpx pool: %s", e)


def get_supabase_url() -> str:
    """Get Supabase project URL."""
    return os.getenv("SUPABASE_URL", "")


def get_supabase_anon_key() -> str:
    """Get Supabase anon key (for frontend JWT verification)."""
    return os.getenv("SUPABASE_ANON_KEY", "")


# ============================================================================
# STORY-291: Supabase Circuit Breaker
# ============================================================================

class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open and no fallback is provided."""
    pass


class SupabaseCircuitBreaker:
    """Circuit breaker for Supabase calls on the search hot path.

    Protects against cascading failures when Supabase has latency or downtime.

    States:
        CLOSED  — Normal operation. Failures tracked in sliding window.
        OPEN    — Fast-fail all calls (use fallback). Waiting for cooldown.
        HALF_OPEN — Allow up to trial_calls_max calls to test recovery.

    Configuration (AC2):
        window_size=10, failure_rate_threshold=0.5 (50%),
        cooldown_seconds=60, trial_calls_max=3

    CRIT-040: exclude_predicates — list of callables that inspect an exception
    and return True if it should NOT count as a CB failure (e.g. schema errors).
    """

    def __init__(
        self,
        window_size: int = 10,
        failure_rate_threshold: float = 0.5,
        cooldown_seconds: float = 60.0,
        trial_calls_max: int = 3,
        exclude_predicates: Optional[list[Callable[[Exception], bool]]] = None,
    ):
        self._state: str = "CLOSED"
        self._window: deque[bool] = deque(maxlen=window_size)
        self._window_size = window_size
        self._failure_rate_threshold = failure_rate_threshold
        self._cooldown = cooldown_seconds
        self._trial_calls_max = trial_calls_max
        self._trial_successes = 0
        self._opened_at: Optional[float] = None
        self._lock = threading.Lock()
        self._exclude_predicates: list[Callable[[Exception], bool]] = exclude_predicates or []

    @property
    def state(self) -> str:
        """Current CB state, accounting for cooldown expiry."""
        with self._lock:
            if self._state == "OPEN" and self._opened_at is not None:
                if time.monotonic() - self._opened_at >= self._cooldown:
                    self._transition_locked("HALF_OPEN")
            return self._state

    def _record_success(self) -> None:
        with self._lock:
            self._window.append(True)
            if self._state == "HALF_OPEN":
                self._trial_successes += 1
                if self._trial_successes >= self._trial_calls_max:
                    self._transition_locked("CLOSED")

    def _record_failure(self, exc: Optional[Exception] = None) -> None:
        # CRIT-040 AC2/AC4: Check exclude predicates before counting failure
        if exc is not None:
            for pred in self._exclude_predicates:
                try:
                    if pred(exc):
                        logger.warning("CB: excluded error from failure count: %s", exc)
                        return  # Don't count this as a failure
                except Exception:
                    pass  # Predicate errors are best-effort

        with self._lock:
            self._window.append(False)
            if self._state == "HALF_OPEN":
                self._transition_locked("OPEN")
            elif self._state == "CLOSED":
                if len(self._window) >= self._window_size:
                    failures = sum(1 for ok in self._window if not ok)
                    rate = failures / len(self._window)
                    if rate >= self._failure_rate_threshold:
                        self._transition_locked("OPEN")

    def _transition_locked(self, new_state: str) -> None:
        """Transition to new state (must hold self._lock)."""
        old_state = self._state
        if old_state == new_state:
            return
        self._state = new_state
        if new_state == "OPEN":
            self._opened_at = time.monotonic()
        elif new_state == "HALF_OPEN":
            self._trial_successes = 0
        elif new_state == "CLOSED":
            self._window.clear()
            self._trial_successes = 0
            self._opened_at = None

        # Emit metrics (lazy import to avoid circular deps)
        try:
            from metrics import SUPABASE_CB_STATE, SUPABASE_CB_TRANSITIONS
            state_val = {"CLOSED": 0, "OPEN": 1, "HALF_OPEN": 2}
            SUPABASE_CB_STATE.set(state_val.get(new_state, 0))
            SUPABASE_CB_TRANSITIONS.labels(
                from_state=old_state, to_state=new_state, source="app"
            ).inc()
        except Exception:
            pass  # Metrics are best-effort

        logger.warning(
            "Supabase circuit breaker: %s → %s", old_state, new_state
        )

    def call_sync(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a synchronous function with circuit breaker protection.

        Args:
            func: The sync function to call.
            *args, **kwargs: Arguments forwarded to func.

        Returns:
            The function result.

        Raises:
            CircuitBreakerOpenError: If CB is open and no fallback available.
            Exception: Re-raises the original exception after recording failure.
        """
        current = self.state  # triggers cooldown check
        if current == "OPEN":
            raise CircuitBreakerOpenError(
                "Supabase circuit breaker is OPEN — call rejected"
            )

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise

    async def call_async(self, coro):
        """Execute an async coroutine with circuit breaker protection.

        Args:
            coro: An awaitable (coroutine).

        Returns:
            The coroutine result.

        Raises:
            CircuitBreakerOpenError: If CB is open.
        """
        current = self.state
        if current == "OPEN":
            raise CircuitBreakerOpenError(
                "Supabase circuit breaker is OPEN — call rejected"
            )

        try:
            result = await coro
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise

    def reset(self) -> None:
        """Reset CB to CLOSED state (for testing)."""
        with self._lock:
            self._state = "CLOSED"
            self._window.clear()
            self._trial_successes = 0
            self._opened_at = None


def _is_schema_error(exc: Exception) -> bool:
    """CRIT-040 AC3: Detect PostgREST/PostgreSQL schema errors.

    These indicate missing tables/columns in PostgREST cache — NOT
    a Supabase outage. Must not trip the circuit breaker.

    Excluded codes:
        PGRST205 — schema cache miss (table not found)
        PGRST204 — schema cache miss (column not found)
        42703    — PostgreSQL: undefined column
        42P01    — PostgreSQL: undefined table
    """
    msg = str(exc)
    return any(code in msg for code in ("PGRST205", "PGRST204", "42703", "42P01"))


# Global singleton — used by all modules
supabase_cb = SupabaseCircuitBreaker(
    exclude_predicates=[_is_schema_error],
)


async def sb_execute(query):
    """Non-blocking Supabase query execution with circuit breaker (STORY-290 + STORY-291).

    Offloads synchronous postgrest-py .execute() to the default
    thread pool executor, preventing event loop blocking.

    STORY-291: Wrapped with circuit breaker. When CB is open,
    raises CircuitBreakerOpenError — callers must handle fallback.

    CRIT-046: Pool utilization metrics (AC1/AC2) + ConnectionError retry (AC5).

    Usage:
        # Before (blocks event loop):
        result = db.table("profiles").select("*").eq("id", uid).execute()

        # After (non-blocking + CB protected):
        result = await sb_execute(db.table("profiles").select("*").eq("id", uid))
    """
    from metrics import SUPABASE_EXECUTE_DURATION, SUPABASE_POOL_ACTIVE, SUPABASE_RETRY_TOTAL
    start = time.monotonic()

    current_state = supabase_cb.state
    if current_state == "OPEN":
        raise CircuitBreakerOpenError(
            "Supabase circuit breaker is OPEN — sb_execute rejected"
        )

    global _pool_active_count
    SUPABASE_POOL_ACTIVE.inc()
    with _pool_active_lock:
        _pool_active_count += 1
        current_active = _pool_active_count

    # AC2: Log when pool > 80% utilization
    high_water = int(_POOL_MAX_CONNECTIONS * _POOL_HIGH_WATER_RATIO)
    if current_active > high_water:
        logger.warning(
            "CRIT-046: Supabase pool > 80%% utilization: %d/%d active",
            current_active, _POOL_MAX_CONNECTIONS,
        )

    try:
        result = await asyncio.to_thread(query.execute)
        SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
        supabase_cb._record_success()
        return result
    except ConnectionError as e:
        # AC5: Retry once with delay for ConnectionError
        logger.warning("CRIT-046: ConnectionError in sb_execute, retrying in %.1fs: %s", _RETRY_DELAY_S, e)
        SUPABASE_RETRY_TOTAL.labels(outcome="attempt").inc()
        await asyncio.sleep(_RETRY_DELAY_S)
        try:
            result = await asyncio.to_thread(query.execute)
            SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
            supabase_cb._record_success()
            SUPABASE_RETRY_TOTAL.labels(outcome="success").inc()
            return result
        except Exception as retry_exc:
            SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
            supabase_cb._record_failure(retry_exc)
            SUPABASE_RETRY_TOTAL.labels(outcome="failure").inc()
            raise
    except Exception as e:
        SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
        supabase_cb._record_failure(e)
        raise
    finally:
        SUPABASE_POOL_ACTIVE.dec()
        with _pool_active_lock:
            _pool_active_count -= 1


async def sb_execute_direct(query):
    """Execute Supabase query bypassing circuit breaker (CRIT-042).

    NEVER use for user-facing operations. This is exclusively for
    internal health monitoring operations (canary, incident detection,
    cleanup) that must not affect the application circuit breaker.

    CRIT-042: Health canary failures were opening the shared supabase_cb,
    causing the monitoring mechanism to sabotage the system it monitors.

    CRIT-046: Shares the same httpx pool — tracks active connections.
    """
    from metrics import SUPABASE_EXECUTE_DURATION, SUPABASE_POOL_ACTIVE
    start = time.monotonic()

    global _pool_active_count
    SUPABASE_POOL_ACTIVE.inc()
    with _pool_active_lock:
        _pool_active_count += 1

    try:
        result = await asyncio.to_thread(query.execute)
        SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
        return result
    except Exception:
        SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
        raise
    finally:
        SUPABASE_POOL_ACTIVE.dec()
        with _pool_active_lock:
            _pool_active_count -= 1
