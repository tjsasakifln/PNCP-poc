"""Supabase client singleton for backend operations.

STORY-291: Circuit breaker pattern for Supabase calls.
Supabase is the ONLY external dependency without a circuit breaker on the hot path.
When Supabase has latency or downtime, 100% of searches fail without CB protection.
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
        logger.info("Supabase client initialized")
    return _supabase_client


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
    """

    def __init__(
        self,
        window_size: int = 10,
        failure_rate_threshold: float = 0.5,
        cooldown_seconds: float = 60.0,
        trial_calls_max: int = 3,
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

    def _record_failure(self) -> None:
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
                from_state=old_state, to_state=new_state
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
        except Exception:
            self._record_failure()
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
        except Exception:
            self._record_failure()
            raise

    def reset(self) -> None:
        """Reset CB to CLOSED state (for testing)."""
        with self._lock:
            self._state = "CLOSED"
            self._window.clear()
            self._trial_successes = 0
            self._opened_at = None


# Global singleton — used by all modules
supabase_cb = SupabaseCircuitBreaker()


async def sb_execute(query):
    """Non-blocking Supabase query execution with circuit breaker (STORY-290 + STORY-291).

    Offloads synchronous postgrest-py .execute() to the default
    thread pool executor, preventing event loop blocking.

    STORY-291: Wrapped with circuit breaker. When CB is open,
    raises CircuitBreakerOpenError — callers must handle fallback.

    Usage:
        # Before (blocks event loop):
        result = db.table("profiles").select("*").eq("id", uid).execute()

        # After (non-blocking + CB protected):
        result = await sb_execute(db.table("profiles").select("*").eq("id", uid))
    """
    from metrics import SUPABASE_EXECUTE_DURATION
    start = time.monotonic()

    current_state = supabase_cb.state
    if current_state == "OPEN":
        raise CircuitBreakerOpenError(
            "Supabase circuit breaker is OPEN — sb_execute rejected"
        )

    try:
        result = await asyncio.to_thread(query.execute)
        SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
        supabase_cb._record_success()
        return result
    except Exception:
        SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
        supabase_cb._record_failure()
        raise
