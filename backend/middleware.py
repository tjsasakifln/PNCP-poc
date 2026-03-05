"""Request correlation, observability, and security middleware."""
import logging
import re
import time
import uuid
from collections import defaultdict
from contextvars import ContextVar
from starlette.datastructures import State
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# CRIT-034: Worker timeout tracking — graceful import
try:
    from worker_lifecycle import set_active_request, clear_active_request
    _HAS_LIFECYCLE = True
except ImportError:
    _HAS_LIFECYCLE = False

# CRIT-034: Extract search_id from URL paths like /buscar-progress/{id} or /v1/search/{id}/...
_SEARCH_ID_PATH_RE = re.compile(r"/(?:buscar-progress|v1/search)/([^/]+)")

# Context variable for request ID (accessible from any async context)
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
# CRIT-004 AC5: search_id for end-to-end search journey correlation
search_id_var: ContextVar[str] = ContextVar("search_id", default="-")
# CRIT-004 AC6: correlation_id from browser (per-tab session)
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="-")


class RequestIDFilter(logging.Filter):
    """
    Inject request_id, trace_id, and span_id into all log records.

    SYS-L04: Ensures all log records have a request_id field for correlation.
    F-02 AC20: Also injects trace_id and span_id for log-trace correlation.
    Falls back to "-" if no request context exists (e.g., startup logs).
    """
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = request_id_var.get("-")
        # CRIT-004 AC8: search_id for end-to-end correlation
        if not hasattr(record, 'search_id'):
            record.search_id = search_id_var.get("-")
        # CRIT-004 AC8: correlation_id from browser session
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = correlation_id_var.get("-")
        # F-02 AC20: trace_id and span_id for log-trace correlation
        if not hasattr(record, 'trace_id'):
            try:
                from telemetry import get_trace_id, get_span_id
                record.trace_id = get_trace_id() or "-"
                record.span_id = get_span_id() or "-"
            except Exception:
                record.trace_id = "-"
                record.span_id = "-"
        return True


class CorrelationIDMiddleware:
    """
    Pure ASGI middleware for correlation/request ID and distributed tracing.

    CRIT-023: Must be pure ASGI (not BaseHTTPMiddleware) to preserve
    OpenTelemetry contextvar propagation. BaseHTTPMiddleware creates a
    new async task for dispatch(), which breaks OTel span context.

    SYS-L04: Produces exactly one log line per request with:
    - HTTP method, path, status code, duration
    - Request ID for correlation across distributed services
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract headers from raw ASGI scope
        headers = {k: v for k, v in scope.get("headers", [])}
        req_id = (headers.get(b"x-request-id", b"").decode() or
                  str(uuid.uuid4()))
        corr_id = headers.get(b"x-correlation-id", b"").decode() or "-"

        # Set context vars (now in same task as OTel ASGI middleware)
        request_id_var.set(req_id)
        correlation_id_var.set(corr_id)

        # Store in scope state for access via request.state in handlers
        if "state" not in scope:
            scope["state"] = State()
        elif isinstance(scope["state"], dict):
            scope["state"] = State(scope["state"])
        scope["state"].request_id = req_id
        scope["state"].correlation_id = corr_id

        # F-02 AC19: Link X-Request-ID to active OpenTelemetry span
        try:
            from telemetry import get_current_span
            span = get_current_span()
            if span and span.is_recording():
                span.set_attribute("http.request_id", req_id)
        except Exception:
            pass

        method = scope.get("method", "?")
        path = scope.get("path", "?")
        start_time = time.time()
        status_code = 0

        # CRIT-034: Track active request for worker timeout diagnostics.
        # Extracts search_id from X-Search-ID header or URL path.
        if _HAS_LIFECYCLE:
            raw_search_id = headers.get(b"x-search-id", b"").decode() or ""
            if not raw_search_id:
                m = _SEARCH_ID_PATH_RE.search(path)
                if m:
                    raw_search_id = m.group(1)
            set_active_request(path, raw_search_id or None)

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                # Inject X-Request-ID into response headers
                raw_headers = list(message.get("headers", []))
                raw_headers.append((b"x-request-id", req_id.encode()))
                message = {**message, "headers": raw_headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            duration_ms = int((time.time() - start_time) * 1000)
            # SYS-L04: Single consolidated log line per request
            logger.info(
                f"{method} {path} -> {status_code} ({duration_ms}ms) "
                f"[req_id={req_id}]"
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            # SYS-L04: Single log line for errors
            logger.error(
                f"{method} {path} -> ERROR ({duration_ms}ms) "
                f"[req_id={req_id}] {type(e).__name__}: {str(e)}"
            )
            raise
        finally:
            # CRIT-034: Always clear active request tracking
            if _HAS_LIFECYCLE:
                clear_active_request()


class DeprecationMiddleware(BaseHTTPMiddleware):
    """
    STORY-226 AC14: Add deprecation headers to legacy (non-prefixed) routes.

    Legacy routes (mounted without /v1/ prefix) receive:
    - Deprecation: true — RFC 8594 standard deprecation signal
    - Sunset: 2026-06-01 — date after which legacy routes may be removed
    - Link: </v1{path}>; rel="successor-version" — points to versioned equivalent

    Logs a warning ONCE per unique route path to avoid log spam.
    Does NOT affect core utility routes (/, /health, /docs, /redoc, /openapi.json).
    """

    # Class-level set to track which paths have been logged
    _warned_paths: set[str] = set()

    # Paths that are NOT considered legacy (they live at root by design)
    _exempt_paths: set[str] = {
        "/",
        "/health",
        "/health/ready",
        "/sources/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/debug/pncp-test",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        response = await call_next(request)

        # Skip: already versioned, exempt, or static/internal paths
        if (
            path.startswith("/v1/")
            or path in self._exempt_paths
            or path.startswith("/docs")
            or path.startswith("/redoc")
        ):
            return response

        # Check if this path has a /v1/ equivalent by checking if it matches
        # a known router pattern (any path with a non-empty segment after /)
        path_segments = path.strip("/").split("/")
        if not path_segments or not path_segments[0]:
            return response

        # This is a legacy route — add deprecation headers
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = "2026-06-01"
        response.headers["Link"] = f"</v1{path}>; rel=\"successor-version\""

        # Log warning once per unique path
        if path not in self._warned_paths:
            self._warned_paths.add(path)
            logger.warning(
                f"DEPRECATED route accessed: {request.method} {path} — "
                f"migrate to /v1{path} before 2026-06-01"
            )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    STORY-210 AC10 + STORY-311 AC9/AC11/AC16: Security headers for all responses.

    Headers applied:
    - X-Content-Type-Options: nosniff — prevent MIME type sniffing
    - X-Frame-Options: DENY — prevent clickjacking
    - X-XSS-Protection: 1; mode=block — legacy XSS protection
    - Referrer-Policy: strict-origin-when-cross-origin — control referrer leakage
    - Permissions-Policy: camera=(), microphone=(), geolocation=() — disable unused APIs (AC11)
    - Strict-Transport-Security: max-age=31536000; includeSubDomains; preload (AC16)
    - Cache-Control: no-store on authenticated endpoints (AC9)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # AC16: HSTS with preload directive for hstspreload.org eligibility
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        # AC9: Prevent caching of authenticated responses
        if request.headers.get("authorization"):
            response.headers["Cache-Control"] = "no-store"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """STORY-311 AC10: Per-IP rate limiting for public endpoints.

    Limits:
    - /health, /v1/health: 60 req/min
    - /plans, /v1/plans: 30 req/min
    - /webhook/stripe: exempt (Stripe IPs)
    - /buscar: uses existing Redis token bucket (not handled here)
    """

    LIMITS: dict[str, int] = {
        "/health": 60,
        "/v1/health": 60,
        "/v1/health/cache": 60,
        "/plans": 30,
        "/v1/plans": 30,
    }

    EXEMPT: set[str] = {
        "/webhook/stripe",
        "/v1/webhook/stripe",
    }

    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._cleanup_counter: int = 0

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_allowed(self, key: str, limit: int) -> bool:
        now = time.time()
        cutoff = now - 60
        entries = self._requests[key]
        self._requests[key] = [t for t in entries if t > cutoff]
        if len(self._requests[key]) >= limit:
            return False
        self._requests[key].append(now)
        self._cleanup_counter += 1
        if self._cleanup_counter >= 200:
            self._cleanup_counter = 0
            self._cleanup()
        return True

    def _cleanup(self):
        cutoff = time.time() - 60
        stale = [k for k, v in self._requests.items() if not v or v[-1] < cutoff]
        for k in stale:
            del self._requests[k]

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in self.EXEMPT:
            return await call_next(request)
        limit = self.LIMITS.get(path)
        if limit is None:
            return await call_next(request)
        ip = self._get_client_ip(request)
        key = f"{ip}:{path}"
        if not self._is_allowed(key, limit):
            return JSONResponse(
                {"detail": "Rate limit exceeded. Try again later."},
                status_code=429,
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
