"""Supabase client management for backend operations.

SYS-023: Per-user Supabase tokens for user-scoped operations.

Client types:
    - get_supabase() — ADMIN client (service_role key, bypasses RLS).
      Use for: admin endpoints, cron jobs, system health, user management,
      background workers (ARQ), cross-user aggregations.

    - get_user_supabase(access_token) — USER-SCOPED client (anon key + user JWT).
      Use for: user-facing reads/writes where RLS should enforce row ownership.
      Examples: profile reads, search history, pipeline CRUD, messages.
      RLS policies on the table will automatically filter to the user's rows.

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
# CRIT-046 + DEBT-018 SYS-020: Connection pool configuration
# SYS-020: Pool limits are per-worker to prevent connection exhaustion.
# With 2 Gunicorn workers, total = 2 x per-worker limit.
# Default: 25 per worker (50 total), down from 50 per worker (100 total).
# ============================================================================

_POOL_MAX_CONNECTIONS = int(os.getenv("SUPABASE_POOL_MAX_CONNECTIONS", "25"))
_POOL_MAX_KEEPALIVE = int(os.getenv("SUPABASE_POOL_MAX_KEEPALIVE", "10"))
_POOL_TIMEOUT = float(os.getenv("SUPABASE_POOL_TIMEOUT", "30.0"))
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

    BYPASSES RLS. Use only for:
        - Admin endpoints (/admin/*)
        - Background jobs (ARQ workers, cron)
        - System health checks and monitoring
        - User management (auth.admin.*)
        - Cross-user aggregations and analytics
        - Operations where the caller is NOT acting on behalf of a specific user

    For user-scoped operations, prefer get_user_supabase(access_token) instead.

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
# SYS-023: Per-user Supabase client (user-scoped, respects RLS)
# ============================================================================

def get_user_supabase(access_token: str):
    """Create a Supabase client scoped to a specific user's JWT.

    This client uses the anon key + the user's access token as the
    Authorization header. Supabase PostgREST will apply RLS policies
    based on the authenticated user's identity (auth.uid()).

    IMPORTANT: These clients are NOT cached/pooled — each call creates
    a new client. This is intentional because:
      1. User tokens expire and rotate frequently
      2. Each request may have a different user
      3. The supabase-py client is lightweight (no heavy init)

    Use for all user-facing operations where RLS should enforce access:
        - Profile reads/updates (own profile only)
        - Pipeline CRUD (own items only)
        - Search history (own sessions only)
        - Messages (own conversations only)
        - Alert preferences (own settings only)

    Args:
        access_token: The user's JWT access token (from Authorization header).

    Returns:
        supabase.Client: User-scoped Supabase client that respects RLS.

    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_ANON_KEY not set.

    Example:
        from supabase_client import get_user_supabase

        @router.get("/my-data")
        async def get_my_data(user: dict = Depends(require_auth), request: Request):
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            user_db = get_user_supabase(token)
            # RLS automatically filters to user's rows
            result = await sb_execute(user_db.table("profiles").select("*"))
            return result.data
    """
    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not anon_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set for user-scoped clients. "
            "SUPABASE_ANON_KEY is the public anon key from your Supabase project settings."
        )

    from supabase import create_client

    # Create client with anon key (public, RLS-enforced)
    client = create_client(url, anon_key)

    # Override the Authorization header on the PostgREST session
    # to use the user's JWT instead of the anon key's default token.
    # This makes PostgREST evaluate RLS policies as the authenticated user.
    try:
        postgrest = client.postgrest
        session = postgrest.session
        # Update the Authorization header to use the user's Bearer token
        session.headers["Authorization"] = f"Bearer {access_token}"
        # Also set the apikey header (required by Supabase gateway)
        session.headers["apikey"] = anon_key
    except Exception as e:
        logger.warning("SYS-023: Failed to set user auth header on client: %s", e)

    logger.debug("SYS-023: Created user-scoped Supabase client")
    return client


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

    STORY-416 additions:
        * ``name`` for observability (emits label on metrics/logs).
        * Hybrid AND/OR trip mode: when
          ``consecutive_failures_threshold`` is set, the CB trips either
          when the sliding-window rate exceeds the threshold **or** after
          N back-to-back failures — whichever happens first. This kills
          the "cascade" failure mode where slow drift pollutes the window
          without ever flipping the gate.
    """

    def __init__(
        self,
        window_size: int = 10,
        failure_rate_threshold: float = 0.5,
        cooldown_seconds: float = 60.0,
        trial_calls_max: int = 3,
        exclude_predicates: Optional[list[Callable[[Exception], bool]]] = None,
        *,
        # STORY-416: default ``name="app"`` for backward compatibility.
        # Pre-STORY-416 tests (STORY-291, CRIT-042) construct bare
        # SupabaseCircuitBreaker() instances and assert against
        # ``source="app"`` on the transitions counter. The segregated
        # read/write/rpc CBs below pass an explicit name so they emit
        # their own label.
        name: str = "app",
        consecutive_failures_threshold: Optional[int] = None,
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
        self._name = name
        self._consecutive_threshold = consecutive_failures_threshold
        self._consecutive_failures = 0

    @property
    def name(self) -> str:
        return self._name

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
            self._consecutive_failures = 0  # STORY-416: reset streak on any success
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
                        logger.warning(
                            "CB[%s]: excluded error from failure count: %s",
                            self._name,
                            exc,
                        )
                        return  # Don't count this as a failure
                except Exception:
                    pass  # Predicate errors are best-effort

        with self._lock:
            self._window.append(False)
            self._consecutive_failures += 1  # STORY-416: track streak for hybrid trip
            if self._state == "HALF_OPEN":
                self._transition_locked("OPEN")
            elif self._state == "CLOSED":
                # STORY-416: hybrid AND/OR trip — open when either the
                # sliding-window rate OR the consecutive-failures streak
                # exceeds its threshold. Reduces flakiness on slow drift
                # without losing burst detection.
                window_full = len(self._window) >= self._window_size
                rate_trip = False
                if window_full:
                    failures = sum(1 for ok in self._window if not ok)
                    rate = failures / len(self._window)
                    rate_trip = rate >= self._failure_rate_threshold

                streak_trip = (
                    self._consecutive_threshold is not None
                    and self._consecutive_failures >= self._consecutive_threshold
                )

                if rate_trip or streak_trip:
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

        # Emit metrics (lazy import to avoid circular deps).
        # STORY-416: also emit per-category gauges so the dashboard can
        # tell read/write/rpc apart instead of staring at one global state.
        try:
            from metrics import SUPABASE_CB_STATE, SUPABASE_CB_TRANSITIONS
            state_val = {"CLOSED": 0, "OPEN": 1, "HALF_OPEN": 2}
            SUPABASE_CB_STATE.set(state_val.get(new_state, 0))
            SUPABASE_CB_TRANSITIONS.labels(
                from_state=old_state, to_state=new_state, source=self._name,
            ).inc()
        except Exception:
            pass  # Metrics are best-effort

        try:
            from metrics import SUPABASE_CB_STATE_BY_CATEGORY
            state_val = {"CLOSED": 0, "OPEN": 1, "HALF_OPEN": 2}
            SUPABASE_CB_STATE_BY_CATEGORY.labels(category=self._name).set(
                state_val.get(new_state, 0)
            )
        except Exception:
            pass  # Optional metric — may not exist yet in older deployments

        logger.warning(
            "Supabase circuit breaker[%s]: %s → %s",
            self._name,
            old_state,
            new_state,
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


# DEBT-110 AC1: CB thresholds configurable via env vars
_CB_WINDOW_SIZE = int(os.getenv("SUPABASE_CB_WINDOW_SIZE", "10"))
# STORY-416 (decided 2026-04-10): raise the sliding-window failure-rate
# threshold from 0.5 → 0.7 so we do not trip on brief latency blips that
# are not a real outage, and add a consecutive-failure streak guard so a
# hard burst still opens the gate fast.
_CB_FAILURE_RATE = float(os.getenv("SUPABASE_CB_FAILURE_RATE", "0.7"))
_CB_COOLDOWN_S = float(os.getenv("SUPABASE_CB_COOLDOWN_SECONDS", "60.0"))
# STORY-416: drop trial_calls 3 → 2 so recovery is faster once the
# upstream is healthy again (two consecutive successes in HALF_OPEN).
_CB_TRIAL_CALLS = int(os.getenv("SUPABASE_CB_TRIAL_CALLS", "2"))

# STORY-416: per-category thresholds. Reads are cheap so we tolerate a
# longer streak before tripping; writes and RPC calls are critical paths
# with lower acceptable failure budget.
_CB_READ_STREAK = int(os.getenv("SUPABASE_CB_READ_STREAK", "5"))
_CB_WRITE_STREAK = int(os.getenv("SUPABASE_CB_WRITE_STREAK", "3"))
_CB_RPC_STREAK = int(os.getenv("SUPABASE_CB_RPC_STREAK", "4"))

# Global singleton — preserved for backward compatibility with hundreds
# of existing call sites and tests that patch ``supabase_cb`` directly.
# New code should prefer ``sb_execute(..., category="read"|"write"|"rpc")``
# which routes through the segregated CBs below.
#
# NB: the legacy CB keeps ``name="app"`` because several STORY-291 /
# CRIT-042 tests assert on the ``source="app"`` label of
# ``smartlic_supabase_cb_transitions_total``. Changing the label would
# silently break every existing Grafana alert that filters on it.
supabase_cb = SupabaseCircuitBreaker(
    window_size=_CB_WINDOW_SIZE,
    failure_rate_threshold=_CB_FAILURE_RATE,
    cooldown_seconds=_CB_COOLDOWN_S,
    trial_calls_max=_CB_TRIAL_CALLS,
    exclude_predicates=[_is_schema_error],
    name="app",
)

# STORY-416: segregated circuit breakers per operation category.
# A read outage must not starve writes (and vice versa), because the
# production incident on 2026-04-10 showed one cascading failure mode
# (slow reads) taking down the entire ``sb_execute`` path — including
# the write side that kept search sessions and trial emails alive.
read_cb = SupabaseCircuitBreaker(
    window_size=_CB_WINDOW_SIZE,
    failure_rate_threshold=_CB_FAILURE_RATE,
    cooldown_seconds=_CB_COOLDOWN_S,
    trial_calls_max=_CB_TRIAL_CALLS,
    exclude_predicates=[_is_schema_error],
    name="read",
    consecutive_failures_threshold=_CB_READ_STREAK,
)
write_cb = SupabaseCircuitBreaker(
    window_size=_CB_WINDOW_SIZE,
    failure_rate_threshold=_CB_FAILURE_RATE,
    cooldown_seconds=_CB_COOLDOWN_S,
    trial_calls_max=_CB_TRIAL_CALLS,
    exclude_predicates=[_is_schema_error],
    name="write",
    consecutive_failures_threshold=_CB_WRITE_STREAK,
)
rpc_cb = SupabaseCircuitBreaker(
    window_size=_CB_WINDOW_SIZE,
    failure_rate_threshold=_CB_FAILURE_RATE,
    cooldown_seconds=_CB_COOLDOWN_S,
    trial_calls_max=_CB_TRIAL_CALLS,
    exclude_predicates=[_is_schema_error],
    name="rpc",
    consecutive_failures_threshold=_CB_RPC_STREAK,
)


_CB_REGISTRY: dict[str, SupabaseCircuitBreaker] = {
    "read": read_cb,
    "write": write_cb,
    "rpc": rpc_cb,
    # "legacy" and "app" both resolve to the pre-STORY-416 global CB
    # so existing callers that asked for ``category="legacy"`` keep
    # working even after we renamed the instance to ``name="app"``.
    "legacy": supabase_cb,
    "app": supabase_cb,
}


def get_cb(category: str) -> SupabaseCircuitBreaker:
    """STORY-416: Look up the segregated circuit breaker for a category.

    Unknown categories fall back to the legacy global singleton so
    existing callers keep working even if they pass a typo — the
    fallback is logged once at warning level.
    """
    if category in _CB_REGISTRY:
        return _CB_REGISTRY[category]
    logger.warning(
        "STORY-416: unknown CB category '%s' — falling back to legacy CB",
        category,
    )
    return supabase_cb


def reset_all_circuit_breakers() -> dict[str, str]:
    """STORY-416 AC5: Reset every segregated CB to CLOSED.

    Returns a dict of ``{category: previous_state}`` for audit logging.
    Intended for ``POST /admin/cb/reset`` (admin-only) after a deploy has
    fixed an upstream issue and the on-call wants traffic to flow again
    without waiting for the cooldown window.
    """
    snapshots: dict[str, str] = {}
    for category, cb in _CB_REGISTRY.items():
        snapshots[category] = cb.state
        cb.reset()
    logger.warning("STORY-416: reset_all_circuit_breakers — previous states=%s", snapshots)
    return snapshots


async def sb_execute(query, *, category: str = "read"):
    """Non-blocking Supabase query execution with circuit breaker (STORY-290 + STORY-291).

    Offloads synchronous postgrest-py .execute() to the default
    thread pool executor, preventing event loop blocking.

    STORY-291: Wrapped with circuit breaker. When CB is open,
    raises CircuitBreakerOpenError — callers must handle fallback.

    STORY-416: ``category`` routes the call through one of three
    segregated circuit breakers (``read`` / ``write`` / ``rpc``) so a
    failure mode on one path does not cascade into the others. Every
    call still records its outcome against the legacy global CB as well
    so that older monitoring dashboards keep working. Unknown categories
    fall back to the legacy CB.

    CRIT-046: Pool utilization metrics (AC1/AC2) + ConnectionError retry (AC5).

    SYS-023: Works with both admin and user-scoped clients. The circuit
    breaker and metrics apply regardless of which client type is used.

    Usage:
        # Before (blocks event loop):
        result = db.table("profiles").select("*").eq("id", uid).execute()

        # After (non-blocking + CB protected):
        result = await sb_execute(db.table("profiles").select("*").eq("id", uid))

        # STORY-416: explicit category for writes / RPCs
        result = await sb_execute(
            db.table("profiles").update(...).eq("id", uid),
            category="write",
        )
    """
    from metrics import SUPABASE_EXECUTE_DURATION, SUPABASE_POOL_ACTIVE, SUPABASE_RETRY_TOTAL
    start = time.monotonic()

    category_cb = get_cb(category)
    # STORY-416: the fast-fail gate is the OR of the per-category CB
    # and the legacy global CB. Here is the reasoning:
    #
    #   * Per-category CB (read/write/rpc) has a tight streak trigger
    #     (5/3/4) that opens faster than the legacy rate trigger. This
    #     is the new segregation guarantee — a burst on one category
    #     opens that category alone.
    #
    #   * Legacy supabase_cb is still consulted so that (a) the pre-
    #     STORY-416 tests that force the global into OPEN continue to
    #     pass, and (b) the runtime keeps a single emergency kill
    #     switch the on-call can flip via ``supabase_cb.reset()`` /
    #     manual poke without knowing about the three sub-instances.
    #
    #   * Because the legacy CB uses the higher 0.7 rate threshold and
    #     no streak guard, it only opens on sustained wide outages —
    #     exactly the blast-radius we want it to stop. Per-category
    #     bursts reach the legacy CB via ``_record_failure_all`` but
    #     typically do not accumulate enough events to trip it before
    #     the category CB already cut off the bleed.
    legacy_state = supabase_cb.state
    category_state = category_cb.state
    if category_state == "OPEN":
        raise CircuitBreakerOpenError(
            f"Supabase circuit breaker[{category}] is OPEN — sb_execute rejected"
        )
    if legacy_state == "OPEN":
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

    def _record_success_all() -> None:
        # STORY-416: record success on both the category CB (to reset its
        # streak) and the legacy CB (so dashboards see the same signal).
        category_cb._record_success()
        if category_cb is not supabase_cb:
            supabase_cb._record_success()

    def _record_failure_all(exc: Exception) -> None:
        category_cb._record_failure(exc)
        if category_cb is not supabase_cb:
            supabase_cb._record_failure(exc)

    try:
        result = await asyncio.to_thread(query.execute)
        SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
        _record_success_all()
        return result
    except ConnectionError as e:
        # AC5: Retry once with delay for ConnectionError
        logger.warning("CRIT-046: ConnectionError in sb_execute, retrying in %.1fs: %s", _RETRY_DELAY_S, e)
        SUPABASE_RETRY_TOTAL.labels(outcome="attempt").inc()
        await asyncio.sleep(_RETRY_DELAY_S)
        try:
            result = await asyncio.to_thread(query.execute)
            SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
            _record_success_all()
            SUPABASE_RETRY_TOTAL.labels(outcome="success").inc()
            return result
        except Exception as retry_exc:
            SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
            _record_failure_all(retry_exc)
            SUPABASE_RETRY_TOTAL.labels(outcome="failure").inc()
            raise
    except Exception as e:
        SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
        _record_failure_all(e)
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
