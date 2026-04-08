"""startup/middleware_setup.py — Middleware registration (DEBT-107).

Extracted from main.py. Covers CORS, custom middleware, inline HTTP middlewares,
and the conditional Prometheus /metrics mount.
"""

import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_cors_origins, METRICS_TOKEN
from config.pipeline import REQUEST_SLOW_THRESHOLD_S
from middleware import CorrelationIDMiddleware, SecurityHeadersMiddleware, DeprecationMiddleware, RateLimitMiddleware

logger = logging.getLogger(__name__)

# SYS-036: Paths protected by DOCS_ACCESS_TOKEN
_DOCS_PATHS = frozenset({"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"})

# TD-004: Paths that are allowed at root (not /v1/)
_ALLOWED_ROOT_PATHS = frozenset({
    "/", "/health", "/health/live", "/health/ready", "/sources/health",
    "/docs", "/redoc", "/openapi.json", "/metrics",
    "/debug/pncp-test", "/v1/setores",
})

DOCS_ACCESS_TOKEN = os.getenv("DOCS_ACCESS_TOKEN", "")


# DEBT-124: Paths exempt from shutdown drain (health probes must respond for LB to stop routing)
_SHUTDOWN_EXEMPT_PATHS = frozenset({
    "/health/live", "/health/ready", "/health", "/metrics",
})


async def track_legacy_routes(request, call_next):
    """TD-004 AC4: Track calls to removed legacy (non-/v1/) routes.

    DEBT-SYS-012: Extracted as module-level function for testability.
    """
    path = request.url.path
    if (
        not path.startswith("/v1/")
        and not path.startswith("/metrics")
        and not path.startswith("/webhooks/")
        and path not in _ALLOWED_ROOT_PATHS
    ):
        try:
            from metrics import LEGACY_ROUTE_CALLS
            segments = path.strip("/").split("/")[:2]
            truncated = "/" + "/".join(segments)
            LEGACY_ROUTE_CALLS.labels(method=request.method, path=truncated).inc()
        except Exception:
            pass
    return await call_next(request)


def setup_middleware(app: FastAPI) -> None:
    """Attach all middleware to *app* (order matters — last added = outermost)."""
    cors_origins = get_cors_origins()
    logger.info(f"CORS configured for origins: {cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With", "X-Request-ID"],
    )
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(DeprecationMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # DEBT-124: Graceful shutdown drain — reject new requests with 503 during shutdown
    @app.middleware("http")
    async def shutdown_drain_middleware(request: Request, call_next):
        """DEBT-124 AC1: Return 503 for new requests when shutting down."""
        import startup.state as _state
        if _state.shutting_down and request.url.path not in _SHUTDOWN_EXEMPT_PATHS:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Servidor em manutenção. Tente novamente em alguns segundos.",
                    "shutting_down": True,
                },
                headers={"Retry-After": "10"},
            )
        return await call_next(request)

    # SYS-036: Protect /docs and /redoc with DOCS_ACCESS_TOKEN in production
    @app.middleware("http")
    async def docs_access_guard(request: Request, call_next):
        """Gate OpenAPI docs behind DOCS_ACCESS_TOKEN bearer in production."""
        path = request.url.path
        if path in _DOCS_PATHS and DOCS_ACCESS_TOKEN:
            auth_header = request.headers.get("Authorization", "")
            query_token = request.query_params.get("token", "")
            if auth_header == f"Bearer {DOCS_ACCESS_TOKEN}" or query_token == DOCS_ACCESS_TOKEN:
                return await call_next(request)
            return JSONResponse(
                status_code=401,
                content={"detail": "API docs access requires DOCS_ACCESS_TOKEN. Use Authorization: Bearer <token> header or ?token=<token> query param."},
            )
        return await call_next(request)

    # STORY-299 AC2: Track HTTP responses for SLO availability metric
    @app.middleware("http")
    async def http_response_counter(request: Request, call_next):
        """Track HTTP responses for SLO availability metric."""
        response = await call_next(request)
        path = request.url.path
        if not path.startswith("/metrics") and not path.startswith("/health"):
            try:
                from metrics import HTTP_RESPONSES_TOTAL
                status_class = f"{response.status_code // 100}xx"
                HTTP_RESPONSES_TOTAL.labels(status_class=status_class, method=request.method).inc()
            except Exception:
                pass
        return response

    # TD-004 AC4: Track calls to removed legacy (non-/v1/) routes
    @app.middleware("http")
    async def _track_legacy_routes_mw(request: Request, call_next):
        return await track_legacy_routes(request, call_next)

    # DEBT-04 AC2: Slow request detection — log + Sentry when request exceeds threshold.
    # Must be outermost (added last) to cover total request time including all middleware.
    if REQUEST_SLOW_THRESHOLD_S > 0:
        @app.middleware("http")
        async def slow_request_detector(request: Request, call_next):
            """DEBT-04 AC2: Detect and log requests exceeding REQUEST_SLOW_THRESHOLD_S."""
            start = time.monotonic()
            response = await call_next(request)
            elapsed = time.monotonic() - start
            if elapsed >= REQUEST_SLOW_THRESHOLD_S:
                path = request.url.path
                method = request.method
                logger.warning(
                    "DEBT-04 slow_request detected: %s %s took %.1fs (threshold=%.0fs) — "
                    "request will be killed by Railway at 120s",
                    method,
                    path,
                    elapsed,
                    REQUEST_SLOW_THRESHOLD_S,
                    extra={"slow_request_elapsed_s": elapsed, "path": path, "method": method},
                )
                try:
                    import sentry_sdk
                    with sentry_sdk.push_scope() as scope:
                        scope.set_tag("slow_request", True)
                        scope.set_extra("elapsed_s", elapsed)
                        scope.set_extra("threshold_s", REQUEST_SLOW_THRESHOLD_S)
                        scope.set_extra("path", path)
                        scope.set_extra("method", method)
                        sentry_sdk.capture_message(
                            f"slow_request: {method} {path} ({elapsed:.1f}s)",
                            level="warning",
                        )
                except Exception:
                    pass
            return response


def setup_metrics_endpoint(app: FastAPI) -> None:
    """Mount the Prometheus /metrics endpoint (conditional on metrics app availability)."""
    from metrics import get_metrics_app
    _metrics_app = get_metrics_app()
    if not _metrics_app:
        return

    from starlette.responses import JSONResponse as StarletteJSONResponse

    @app.middleware("http")
    async def metrics_auth(request: Request, call_next):
        """Protect /metrics with Bearer token."""
        if request.url.path == "/metrics" or request.url.path.startswith("/metrics/"):
            if METRICS_TOKEN:
                token = request.headers.get("Authorization", "").strip()
                if token != f"Bearer {METRICS_TOKEN}":
                    logger.warning(
                        "Metrics auth failed: received token length=%d, expected length=%d",
                        len(token), len(f"Bearer {METRICS_TOKEN}"),
                    )
                    return StarletteJSONResponse(status_code=401, content={"detail": "Unauthorized"})
        return await call_next(request)

    app.mount("/metrics", _metrics_app)
    logger.info("Prometheus /metrics endpoint mounted (auth=%s)", "enabled" if METRICS_TOKEN else "open")
