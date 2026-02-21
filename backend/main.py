"""
BidIQ Uniformes POC - Backend API

FastAPI application for searching and analyzing uniform procurement bids
from Brazil's PNCP (Portal Nacional de Contratações Públicas).

This API provides endpoints for:
- Searching procurement opportunities by state and date range
- Filtering results by keywords and value thresholds
- Generating Excel reports with formatted data
- Creating AI-powered executive summaries (GPT-4.1-nano)

STORY-202: Monolith decomposition — routes extracted to:
  - routes/search.py (buscar + progress SSE)
  - routes/user.py (profile, change-password)
  - routes/billing.py (plans, checkout)
  - routes/sessions.py (search history)
  - authorization.py (admin/master role helpers)
"""

import logging
import os
import signal
import time
from contextlib import asynccontextmanager
from dotenv import load_dotenv

import httpx  # GTM-RESILIENCE-E02: for transient error fingerprinting

# STORY-211: Sentry error tracking
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from log_sanitizer import mask_email, mask_token, mask_user_id, mask_ip_address, sanitize_dict, sanitize_string

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from config import setup_logging, ENABLE_NEW_PRICING, get_cors_origins, log_feature_flags, validate_env_vars, METRICS_TOKEN
from pncp_client import PNCPClient
from sectors import list_sectors
from schemas import (
    RootResponse, HealthResponse, SourcesHealthResponse, SetoresResponse, DebugPNCPResponse,
)
from middleware import CorrelationIDMiddleware, SecurityHeadersMiddleware, DeprecationMiddleware  # STORY-202 SYS-M01, STORY-210 AC10, STORY-226 AC14
from redis_pool import startup_redis, shutdown_redis  # STORY-217: Redis pool lifecycle

# Existing routers
from admin import router as admin_router
from routes.subscriptions import router as subscriptions_router
from routes.features import router as features_router
from routes.messages import router as messages_router
from routes.analytics import router as analytics_router
from routes.auth_oauth import router as oauth_router  # STORY-180: Google OAuth
from routes.export_sheets import router as export_sheets_router  # STORY-180: Google Sheets Export
from webhooks.stripe import router as stripe_webhook_router

# STORY-202: Decomposed routers
from routes.search import router as search_router
from routes.user import router as user_router
from routes.billing import router as billing_router
from routes.sessions import router as sessions_router
from routes.plans import router as plans_router  # STORY-203 CROSS-M01
from routes.emails import router as emails_router  # STORY-225: Transactional emails
from routes.pipeline import router as pipeline_router  # STORY-250: Pipeline de Oportunidades
from routes.onboarding import router as onboarding_router  # GTM-004: First analysis after onboarding
from routes.auth_email import router as auth_email_router  # GTM-FIX-009: Email confirmation recovery
from routes.health import router as cache_health_router  # UX-303: Cache health endpoint
from routes.feedback import router as feedback_router  # GTM-RESILIENCE-D05: User feedback loop
from routes.admin_trace import router as admin_trace_router  # CRIT-004 AC21: Search trace endpoint

# Configure structured logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# STORY-220 AC6: Log feature flags AFTER setup_logging() (not at import time)
log_feature_flags()

# CRIT-010 AC5: Startup readiness tracking
_startup_time: float | None = None  # Set when lifespan startup completes

# STORY-210 AC8: Disable API docs in production to prevent reconnaissance
_env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
_is_production = _env in ("production", "prod")

# STORY-211: Sentry Error Tracking — must init BEFORE app creation (AC2)
APP_VERSION = "0.2.0"


def scrub_pii(event, hint):
    """Sentry before_send callback to strip PII from error events (AC3).

    Leverages log_sanitizer.py patterns for consistent masking.
    Strips: email addresses, JWT tokens, user IDs, API keys.
    """
    # Scrub request headers (Authorization, cookies, API keys)
    if "request" in event:
        request = event["request"]
        if "headers" in request:
            request["headers"] = {
                k: (mask_token(v) if k.lower() in ("authorization", "cookie", "x-api-key") else v)
                for k, v in request["headers"].items()
            }
        if "data" in request and isinstance(request["data"], dict):
            request["data"] = sanitize_dict(request["data"])

    # Scrub user context
    if "user" in event:
        user = event["user"]
        if "email" in user:
            user["email"] = mask_email(user["email"])
        if "id" in user:
            user["id"] = mask_user_id(str(user["id"]))
        if "ip_address" in user:
            user["ip_address"] = mask_ip_address(user["ip_address"])

    # Scrub breadcrumb messages
    if "breadcrumbs" in event:
        for crumb in event.get("breadcrumbs", {}).get("values", []):
            if "message" in crumb:
                crumb["message"] = sanitize_string(crumb["message"])
            if "data" in crumb and isinstance(crumb["data"], dict):
                crumb["data"] = sanitize_dict(crumb["data"])

    # Scrub exception values
    if "exception" in event:
        for exc in event.get("exception", {}).get("values", []):
            if "value" in exc:
                exc["value"] = sanitize_string(exc["value"])

    return event


def _fingerprint_transients(event, hint):
    """Fingerprint transient errors to avoid Sentry issue flood (GTM-RESILIENCE-E02 AC4).

    Groups httpx timeouts and PNCP transients under custom fingerprints
    and downgrades their level to 'warning' so they don't trigger alerts.
    """
    exc_info = hint.get("exc_info")
    if exc_info and exc_info[1] is not None:
        exc = exc_info[1]
        if isinstance(exc, (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout)):
            event["fingerprint"] = ["transient-timeout", type(exc).__name__]
            event["level"] = "warning"
        elif type(exc).__name__ in ("PNCPRateLimitError", "PNCPDegradedError"):
            event["fingerprint"] = [f"transient-{type(exc).__name__}"]
            event["level"] = "warning"
    return event


def _before_send(event, hint):
    """Combined before_send: PII scrubbing + transient fingerprinting (GTM-RESILIENCE-E02)."""
    event = scrub_pii(event, hint)
    if event is None:
        return None
    return _fingerprint_transients(event, hint)


def _traces_sampler(sampling_context):
    """Exclude health checks from Sentry traces (GTM-RESILIENCE-E02 AC5)."""
    path = sampling_context.get("asgi_scope", {}).get("path", "")
    if path in ("/health", "/v1/health", "/v1/health/cache"):
        return 0.0  # Never trace health checks
    return 0.1  # 10% for everything else


_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[FastApiIntegration(), StarletteIntegration()],
        traces_sampler=_traces_sampler,
        environment=_env,
        release=APP_VERSION,
        before_send=_before_send,
    )
    logger.info("Sentry initialized for error tracking")
else:
    logger.info("Sentry DSN not configured — error tracking disabled")


# ============================================================================
# STORY-221: Lifespan Context Manager (replaces deprecated @app.on_event)
# ============================================================================

async def _check_cache_schema() -> None:
    """CRIT-001 AC4: Validate search_results_cache schema on startup.

    Compares actual DB columns against SearchResultsCacheRow model.
    Logs CRITICAL for missing columns, WARNING for extras, INFO on success.
    Never crashes — graceful degradation if DB is unavailable.
    """
    try:
        from models.cache import SearchResultsCacheRow
        from supabase_client import get_supabase

        db = get_supabase()
        # Use PostgREST RPC to query information_schema
        # This avoids needing direct DB access — works with Supabase client
        try:
            result = db.rpc(
                "get_table_columns_simple",
                {"p_table_name": "search_results_cache"},
            ).execute()
            actual_columns = {row["column_name"] for row in result.data} if result.data else set()
        except Exception as rpc_err:
            logger.warning(f"CRIT-004: RPC get_table_columns_simple failed ({rpc_err}) — trying direct query")
            try:
                result = db.table("search_results_cache").select("*").limit(0).execute()
                logger.info("CRIT-004: Table search_results_cache exists (column validation skipped)")
                return
            except Exception as fallback_err:
                logger.warning(
                    f"CRIT-004: Schema validation FAILED — RPC: {rpc_err}, Fallback: {fallback_err}"
                )
                return

        expected_columns = SearchResultsCacheRow.expected_columns()

        missing = expected_columns - actual_columns
        extra = actual_columns - expected_columns

        if missing:
            logger.critical(
                f"CRIT-001: search_results_cache MISSING columns: {sorted(missing)}. "
                f"Run migration 033_fix_missing_cache_columns.sql"
            )
        if extra:
            logger.warning(
                f"CRIT-001: search_results_cache has EXTRA columns not in model: {sorted(extra)}"
            )
        if not missing and not extra:
            logger.info(
                f"CRIT-001: Schema validation passed for search_results_cache "
                f"({len(expected_columns)} columns)"
            )
    except Exception as e:
        # Never crash on health check failure
        logger.warning(f"CRIT-001: Schema health check failed (non-fatal): {type(e).__name__}: {e}")


def _log_registered_routes(app_instance: FastAPI) -> None:
    """Diagnostic logging for route registration (HOTFIX STORY-183).

    Logs all registered routes for debugging route 404 issues.
    """
    logger.info("=" * 60)
    logger.info("REGISTERED ROUTES:")
    logger.info("=" * 60)
    for route in app_instance.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ','.join(route.methods) if route.methods else 'N/A'
            logger.info(f"  {methods:8s} {route.path}")
    logger.info("=" * 60)

    # Specifically check for export route
    export_routes = [r for r in app_instance.routes if hasattr(r, 'path') and '/export' in r.path]
    if export_routes:
        logger.info(f"Export routes found: {len(export_routes)}")
        for r in export_routes:
            methods = ','.join(r.methods) if hasattr(r, 'methods') and r.methods else 'N/A'
            logger.info(f"   {methods:8s} {r.path}")
    else:
        logger.error("NO EXPORT ROUTES FOUND - /api/export/google-sheets will return 404!")
    logger.info("=" * 60)


async def _mark_inflight_sessions_timed_out() -> None:
    """CRIT-002 AC15: Mark in-flight sessions as timed_out on server shutdown.

    Called during SIGTERM/shutdown. Updates any sessions with status 'created'
    or 'processing' to 'timed_out' so users see what happened in their history.
    Timeout: 5s max to avoid blocking shutdown.
    """
    import asyncio
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        async def _do_update():
            from datetime import datetime, timezone
            result = (
                sb.table("search_sessions")
                .update({
                    "status": "timed_out",
                    "error_message": "Server shutdown (SIGTERM)",
                    "error_code": "timeout",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
                .in_("status", ["created", "processing"])
                .execute()
            )
            n = len(result.data) if result.data else 0
            if n > 0:
                logger.critical(
                    f"CRIT-002 AC15: Marked {n} in-flight sessions as timed_out due to shutdown"
                )
            else:
                logger.info("CRIT-002 AC15: No in-flight sessions to mark on shutdown")

        await asyncio.wait_for(_do_update(), timeout=5.0)
    except asyncio.TimeoutError:
        logger.error("CRIT-002 AC15: Timeout marking in-flight sessions (5s limit)")
    except Exception as e:
        logger.error(f"CRIT-002 AC15: Failed to mark in-flight sessions: {e}")


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Application lifespan context manager.

    Handles startup and shutdown events for the FastAPI application.
    Replaces deprecated @app.on_event("startup") and @app.on_event("shutdown").

    Startup:
        - Validate environment variables (AC12-AC14)
        - Initialize Redis pool (STORY-217)
        - Log registered routes for diagnostics

    Shutdown:
        - Close Redis pool gracefully
    """
    # === STARTUP ===
    # GTM-RESILIENCE-F02: Initialize OpenTelemetry tracing (before anything else)
    from telemetry import init_tracing, shutdown_tracing
    init_tracing()

    # AC12-AC14: Validate environment variables
    validate_env_vars()

    # STORY-217: Initialize Redis pool
    await startup_redis()

    # GTM-RESILIENCE-F01: Initialize ARQ job queue pool
    from job_queue import get_arq_pool
    await get_arq_pool()

    # UX-303 AC8: Start periodic cache cleanup
    from cron_jobs import start_cache_cleanup_task, start_session_cleanup_task
    cleanup_task = await start_cache_cleanup_task()

    # CRIT-011 AC7: Start periodic session cleanup (stale + old sessions)
    session_cleanup_task = await start_session_cleanup_task()

    # CRIT-001 AC4: Schema health check for search_results_cache
    await _check_cache_schema()

    # GTM-CRIT-005 AC5: Initialize circuit breakers from Redis
    from pncp_client import get_circuit_breaker
    pncp_cb = get_circuit_breaker("pncp")
    pcp_cb = get_circuit_breaker("pcp")
    await pncp_cb.initialize()
    await pcp_cb.initialize()
    logger.info("GTM-CRIT-005: Circuit breakers initialized from Redis")

    # CRIT-004: Validate schema contract for critical tables
    from schema_contract import validate_schema_contract, emit_degradation_warning
    try:
        from supabase_client import get_supabase
        db = get_supabase()
        passed, missing = validate_schema_contract(db)
        if not passed:
            logger.critical(
                f"SCHEMA CONTRACT VIOLATED: missing {missing}. "
                f"Run migrations before deploying. Refusing to start."
            )
            raise SystemExit(1)
        logger.info(f"CRIT-004: Schema contract validated — 0 missing columns")
    except SystemExit:
        raise  # Re-raise SystemExit
    except Exception as e:
        logger.warning(f"CRIT-004: Schema validation could not run ({e}) — proceeding with caution")

    # CRIT-003 AC16-AC18: Recover stale searches from previous server instance
    from search_state_manager import recover_stale_searches
    await recover_stale_searches(max_age_minutes=10)

    # HOTFIX STORY-183: Diagnostic route logging
    _log_registered_routes(app_instance)

    # CRIT-001 AC4: Probe Supabase connectivity before accepting traffic
    try:
        from supabase_client import get_supabase
        db = get_supabase()
        db.table("profiles").select("id").limit(1).execute()
        logger.info("STARTUP GATE: Supabase connectivity confirmed")
    except Exception as e:
        logger.critical(f"STARTUP GATE FAILED: Supabase unreachable — {e}")
        raise  # Crash on startup = Railway will retry

    # CRIT-001 AC5: Redis connectivity check (non-blocking)
    if os.getenv("REDIS_URL"):
        from redis_pool import is_redis_available
        if await is_redis_available():
            logger.info("STARTUP GATE: Redis connectivity confirmed")
        else:
            logger.warning("STARTUP GATE: Redis configured but unavailable — proceeding without Redis")

    logger.info("STARTUP GATE: Supabase OK, Redis %s — setting ready=true",
                "OK" if os.getenv("REDIS_URL") and await is_redis_available() else "not configured")

    # CRIT-010 AC4+AC5: Mark application as ready for traffic
    global _startup_time
    _startup_time = time.monotonic()
    logger.info("APPLICATION READY — all routes registered, accepting traffic")

    # CRIT-010 AC7: SIGTERM handler for graceful shutdown logging
    def _sigterm_handler(signum, frame):
        logger.info("SIGTERM received — starting graceful shutdown")

    signal.signal(signal.SIGTERM, _sigterm_handler)

    yield

    # === SHUTDOWN ===
    # CRIT-002 AC15: Mark in-flight sessions as timed_out on shutdown
    await _mark_inflight_sessions_timed_out()

    # UX-303: Cancel cache cleanup
    cleanup_task.cancel()
    try:
        await cleanup_task
    except Exception:
        pass

    # CRIT-011: Cancel session cleanup
    session_cleanup_task.cancel()
    try:
        await session_cleanup_task
    except Exception:
        pass

    # GTM-RESILIENCE-F01: Close ARQ pool
    from job_queue import close_arq_pool
    await close_arq_pool()

    # GTM-RESILIENCE-F02: Flush and shut down tracing
    shutdown_tracing()

    # STORY-217: Close Redis pool
    await shutdown_redis()


# Initialize FastAPI application
app = FastAPI(
    title="BidIQ Uniformes API",
    description=(
        "API para busca e análise de licitações em fontes oficiais. "
        "Permite filtrar oportunidades por estado, valor e setor, "
        "gerando relatórios Excel e avaliação estratégica via IA."
    ),
    version=APP_VERSION,
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
    lifespan=lifespan,  # STORY-221: Lifespan context manager for startup/shutdown
)

# CORS Configuration
cors_origins = get_cors_origins()
logger.info(f"CORS configured for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With", "X-Request-ID"],
)

# STORY-202 SYS-M01: Add correlation ID middleware for distributed tracing
app.add_middleware(CorrelationIDMiddleware)

# STORY-210 AC10: Add security headers to all responses
app.add_middleware(SecurityHeadersMiddleware)

# STORY-226 AC14: Add deprecation headers to legacy (non-versioned) routes
app.add_middleware(DeprecationMiddleware)

# ============================================================================
# SYS-M08: API Versioning with /v1/ prefix
# ============================================================================

# Mount all routers under /v1/ prefix for versioning
app.include_router(admin_router, prefix="/v1")
app.include_router(subscriptions_router, prefix="/v1")
app.include_router(features_router, prefix="/v1")
app.include_router(messages_router, prefix="/v1")
app.include_router(analytics_router, prefix="/v1")
app.include_router(oauth_router, prefix="/v1")  # STORY-180: Google OAuth routes
app.include_router(export_sheets_router, prefix="/v1")  # STORY-180: Google Sheets Export routes
app.include_router(stripe_webhook_router, prefix="/v1")
# STORY-202: Decomposed routers
app.include_router(search_router, prefix="/v1")
app.include_router(user_router, prefix="/v1")
app.include_router(billing_router, prefix="/v1")
app.include_router(sessions_router, prefix="/v1")
app.include_router(plans_router, prefix="/v1")  # STORY-203 CROSS-M01
app.include_router(emails_router, prefix="/v1")  # STORY-225
app.include_router(pipeline_router, prefix="/v1")  # STORY-250: Pipeline
app.include_router(onboarding_router, prefix="/v1")  # GTM-004: First analysis
app.include_router(auth_email_router, prefix="/v1")  # GTM-FIX-009: Email confirmation recovery
app.include_router(cache_health_router, prefix="/v1")  # UX-303: Cache health
app.include_router(feedback_router, prefix="/v1")  # GTM-RESILIENCE-D05: User feedback loop
app.include_router(admin_trace_router)  # CRIT-004 AC21: Search trace (already has /v1/admin prefix)

# ============================================================================
# SYS-M08: Backward Compatibility - Mount routers without /v1/ prefix
# ============================================================================
# For gradual migration, also mount at original paths (will be deprecated)
app.include_router(admin_router)
app.include_router(subscriptions_router)
app.include_router(features_router)
app.include_router(messages_router)
app.include_router(analytics_router)
app.include_router(oauth_router)
app.include_router(export_sheets_router)
app.include_router(stripe_webhook_router)
app.include_router(search_router)
app.include_router(user_router)
app.include_router(billing_router)
app.include_router(sessions_router)
app.include_router(plans_router)
app.include_router(emails_router)  # STORY-225
app.include_router(pipeline_router)  # STORY-250: Pipeline
app.include_router(onboarding_router)  # GTM-004: First analysis
app.include_router(auth_email_router)  # GTM-FIX-009: Email confirmation recovery
app.include_router(cache_health_router)  # UX-303: Cache health
app.include_router(feedback_router)  # GTM-RESILIENCE-D05: User feedback loop

# ============================================================================
# GTM-RESILIENCE-E03: Prometheus /metrics endpoint
# ============================================================================
from metrics import get_metrics_app

_metrics_app = get_metrics_app()
if _metrics_app:
    from starlette.requests import Request as StarletteRequest
    from starlette.responses import JSONResponse as StarletteJSONResponse

    @app.middleware("http")
    async def metrics_auth(request, call_next):
        """Protect /metrics endpoint with Bearer token authentication."""
        if request.url.path == "/metrics" or request.url.path.startswith("/metrics/"):
            if METRICS_TOKEN:
                token = request.headers.get("Authorization", "")
                expected = f"Bearer {METRICS_TOKEN}"
                if token != expected:
                    return StarletteJSONResponse(
                        status_code=401, content={"detail": "Unauthorized"}
                    )
        return await call_next(request)

    app.mount("/metrics", _metrics_app)
    logger.info("Prometheus /metrics endpoint mounted (auth=%s)", "enabled" if METRICS_TOKEN else "open")
else:
    logger.info("Prometheus metrics disabled or prometheus_client not installed")

logger.info(
    "FastAPI application initialized — PORT=%s",
    os.getenv("PORT", "8000"),
)

# Log feature flag states
logger.info(
    "Feature Flags — ENABLE_NEW_PRICING=%s",
    ENABLE_NEW_PRICING,
)


# ============================================================================
# Core utility endpoints (stay in main.py)
# ============================================================================

@app.get("/", response_model=RootResponse)
async def root():
    """
    API root endpoint - provides navigation to documentation.

    SYS-M08: Informs clients about API versioning.
    """
    return {
        "name": "BidIQ Uniformes API",
        "version": "0.2.0",
        "api_version": "v1",  # SYS-M08: Current API version
        "description": "API para busca de licitações de uniformes no PNCP",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "openapi": "/openapi.json",
            "v1_api": "/v1",  # SYS-M08: Versioned API endpoint
        },
        "versioning": {  # SYS-M08: API versioning information
            "current": "v1",
            "supported": ["v1"],
            "deprecated": [],
            "note": "All endpoints available at /v1/<endpoint> and /<endpoint> (legacy)",
        },
        "status": "operational",
    }


@app.get("/health/ready")
async def health_ready():
    """Lightweight readiness probe for Railway health checks.

    CRIT-001 AC1: Zero I/O, zero dependency checks. Just reads _startup_time.
    Returns in <50ms guaranteed.
    """
    is_ready = _startup_time is not None
    uptime = round(time.monotonic() - _startup_time, 3) if is_ready else 0.0
    return {"ready": is_ready, "uptime_seconds": uptime}


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint for monitoring and load balancers.

    Provides lightweight service health verification including dependency
    checks for Supabase, OpenAI, and Redis connectivity.
    """
    from datetime import datetime, timezone

    dependencies = {
        "supabase": "unconfigured",
        "openai": "unconfigured",
        "redis": "unconfigured",
    }

    # Check Supabase configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_url and supabase_key:
        try:
            from supabase_client import get_supabase
            get_supabase()
            dependencies["supabase"] = "healthy"
        except Exception as e:
            dependencies["supabase"] = f"error: {str(e)[:50]}"
    else:
        dependencies["supabase"] = "missing_env_vars"

    # Check OpenAI configuration
    if os.getenv("OPENAI_API_KEY"):
        dependencies["openai"] = "configured"
    else:
        dependencies["openai"] = "missing_api_key"

    # Check Redis connectivity (optional dependency)
    # SYS-L06: Add Redis health check to health endpoint
    # B-04 AC8: Add redis_connected, redis_latency_ms, redis_memory_used_mb
    redis_url = os.getenv("REDIS_URL")
    redis_metrics = None
    if redis_url:
        try:
            from redis_pool import get_redis_pool, is_redis_available
            import time as _time
            redis_available = await is_redis_available()
            dependencies["redis"] = "healthy" if redis_available else "unavailable"

            if redis_available:
                pool = await get_redis_pool()
                # Measure ping latency
                t0 = _time.monotonic()
                await pool.ping()
                latency_ms = round((_time.monotonic() - t0) * 1000, 2)
                # Get memory usage
                memory_mb = None
                try:
                    info = await pool.info("memory")
                    used_bytes = info.get("used_memory", 0)
                    memory_mb = round(used_bytes / (1024 * 1024), 2)
                except Exception:
                    pass
                redis_metrics = {
                    "connected": True,
                    "latency_ms": latency_ms,
                    "memory_used_mb": memory_mb,
                }
            else:
                redis_metrics = {"connected": False, "latency_ms": None, "memory_used_mb": None}
        except Exception as e:
            dependencies["redis"] = f"error: {str(e)[:50]}"
            redis_metrics = {"connected": False, "latency_ms": None, "memory_used_mb": None}
    else:
        # Redis is optional - not configured is not an error
        dependencies["redis"] = "not_configured"

    # AC27: Add per-source health status from SourceHealthRegistry
    from source_config.sources import source_health_registry
    from pncp_client import get_circuit_breaker

    sources = {}
    source_names = ["PNCP", "Portal Transparência", "Licitar Digital", "ComprasGov", "BLL", "BNC"]
    for source_name in source_names:
        sources[source_name] = source_health_registry.get_status(source_name)

    # B-06 AC9: Circuit breaker shared state (replaces simple string status)
    pncp_cb = get_circuit_breaker("pncp")
    pcp_cb = get_circuit_breaker("pcp")
    if hasattr(pncp_cb, "get_state"):
        sources["PNCP_circuit_breaker"] = await pncp_cb.get_state()
        sources["PCP_circuit_breaker"] = await pcp_cb.get_state()
    else:
        sources["PNCP_circuit_breaker"] = {
            "status": "degraded" if pncp_cb.is_degraded else "healthy",
            "failures": pncp_cb.consecutive_failures,
            "degraded": pncp_cb.is_degraded,
            "backend": "local",
        }
        sources["PCP_circuit_breaker"] = {
            "status": "degraded" if pcp_cb.is_degraded else "healthy",
            "failures": pcp_cb.consecutive_failures,
            "degraded": pcp_cb.is_degraded,
            "backend": "local",
        }

    # B-06 AC10: Rate limiter metrics
    from rate_limiter import pncp_rate_limiter, pcp_rate_limiter
    sources["rate_limiter"] = {
        "pncp": await pncp_rate_limiter.get_stats(),
        "pcp": await pcp_rate_limiter.get_stats(),
    }

    # Determine overall health status
    # Supabase is critical, Redis is optional
    supabase_ok = not dependencies["supabase"].startswith("error")
    redis_degraded = dependencies["redis"].startswith("error") or dependencies["redis"] == "unavailable"

    if not supabase_ok:
        status = "unhealthy"
    elif redis_degraded and redis_url:  # Only degrade if Redis is configured but failing
        status = "degraded"
    else:
        status = "healthy"

    # B-04 AC8: Include redis_metrics in dependencies
    if redis_metrics:
        dependencies["redis_metrics"] = redis_metrics

    # GTM-RESILIENCE-F01 AC4: ARQ job queue health
    try:
        from job_queue import get_queue_health
        dependencies["queue"] = await get_queue_health()
    except Exception:
        dependencies["queue"] = "unavailable"

    # F-02 AC21: Report tracing status
    from telemetry import is_tracing_enabled
    dependencies["tracing"] = "enabled" if is_tracing_enabled() else "disabled"

    # CRIT-010 AC5: Startup readiness signal
    is_ready = _startup_time is not None
    uptime = round(time.monotonic() - _startup_time, 3) if is_ready else 0.0

    response_data = {
        "status": status,
        "ready": is_ready,
        "uptime_seconds": uptime,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
        "dependencies": dependencies,
        "sources": sources,
    }

    # Always return 200 for Railway health checks — report status in body
    # Returning 503 prevents Railway from starting the container entirely,
    # which is worse than running with degraded dependencies.
    return response_data


@app.get("/sources/health", response_model=SourcesHealthResponse)
async def sources_health():
    """
    Health check for all configured procurement data sources.

    Returns status, response time, and priority for each source.
    """
    from datetime import datetime, timezone

    enable_multi_source = os.getenv("ENABLE_MULTI_SOURCE", "false").lower() == "true"
    from source_config.sources import get_source_config
    source_config = get_source_config()

    sources_info = []

    if source_config.pncp.enabled:
        sources_info.append({
            "code": "PNCP",
            "name": source_config.pncp.name,
            "enabled": True,
            "priority": source_config.pncp.priority,
        })

    if source_config.compras_gov.enabled:
        sources_info.append({
            "code": "COMPRAS_GOV",
            "name": source_config.compras_gov.name,
            "enabled": True,
            "priority": source_config.compras_gov.priority,
        })

    if source_config.portal.enabled:
        sources_info.append({
            "code": "PORTAL_COMPRAS",
            "name": source_config.portal.name,
            "enabled": True,
            "priority": source_config.portal.priority,
        })

    if enable_multi_source:
        from consolidation import ConsolidationService
        from clients.compras_gov_client import ComprasGovAdapter
        from clients.portal_compras_client import PortalComprasAdapter

        adapters = {}
        if source_config.compras_gov.enabled:
            adapters["COMPRAS_GOV"] = ComprasGovAdapter(timeout=source_config.compras_gov.timeout)
        if source_config.portal.enabled and source_config.portal.credentials.has_api_key():
            adapters["PORTAL_COMPRAS"] = PortalComprasAdapter(
                api_key=source_config.portal.credentials.api_key,
                timeout=source_config.portal.timeout,
            )

        if adapters:
            svc = ConsolidationService(adapters=adapters)
            health_results = await svc.health_check_all()
            await svc.close()

            for info in sources_info:
                code = info["code"]
                if code in health_results:
                    info["status"] = health_results[code]["status"]
                    info["response_ms"] = health_results[code]["response_ms"]
                elif code == "PNCP":
                    info["status"] = "available"
                    info["response_ms"] = 0
                else:
                    info["status"] = "unknown"
                    info["response_ms"] = 0
        else:
            for info in sources_info:
                info["status"] = "available" if info["code"] == "PNCP" else "unknown"
                info["response_ms"] = 0
    else:
        for info in sources_info:
            info["status"] = "available" if info["code"] == "PNCP" else "disabled"
            info["response_ms"] = 0

    total_enabled = len([s for s in sources_info if s["enabled"]])
    total_available = len([s for s in sources_info if s.get("status") == "available"])

    return {
        "sources": sources_info,
        "multi_source_enabled": enable_multi_source,
        "total_enabled": total_enabled,
        "total_available": total_available,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/setores", response_model=SetoresResponse)
@app.get("/v1/setores", response_model=SetoresResponse)
async def listar_setores():
    """Return available procurement sectors for frontend dropdown.

    STORY-252 Track 5 (AC24): Mounted at both /setores (legacy) and /v1/setores (versioned).
    """
    return {"setores": list_sectors()}


# STORY-210 AC9: Protect debug endpoint with admin auth
from admin import require_admin as _require_admin


@app.get("/debug/pncp-test", response_model=DebugPNCPResponse)
async def debug_pncp_test(admin: dict = Depends(_require_admin)):
    """Diagnostic: test if PNCP API is reachable from this server. Admin only."""
    import time as t
    from datetime import date, timedelta

    start = t.time()
    try:
        client = PNCPClient()
        hoje = date.today()
        tres_dias = hoje - timedelta(days=3)
        response = client.fetch_page(
            data_inicial=tres_dias.strftime("%Y-%m-%d"),
            data_final=hoje.strftime("%Y-%m-%d"),
            modalidade=6,
            pagina=1,
            tamanho=10,
        )
        elapsed = int((t.time() - start) * 1000)
        return {
            "success": True,
            "total_registros": response.get("totalRegistros", 0),
            "items_returned": len(response.get("data", [])),
            "elapsed_ms": elapsed,
        }
    except Exception as e:
        elapsed = int((t.time() - start) * 1000)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "elapsed_ms": elapsed,
        }
