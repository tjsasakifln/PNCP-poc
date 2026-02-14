"""Request correlation, observability, and security middleware."""
import logging
import time
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Context variable for request ID (accessible from any async context)
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIDFilter(logging.Filter):
    """
    Inject request_id into all log records.

    SYS-L04: Ensures all log records have a request_id field for correlation.
    Falls back to "-" if no request context exists (e.g., startup logs).
    """
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = request_id_var.get("-")
        return True


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Add correlation/request ID to every request for distributed tracing.

    SYS-L04: Produces exactly one log line per request with:
    - HTTP method, path, status code, duration
    - Request ID for correlation across distributed services
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use incoming X-Request-ID or generate new
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(req_id)

        # Store in request state for access in route handlers
        request.state.request_id = req_id

        start_time = time.time()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)

            # SYS-L04: Single consolidated log line per request
            logger.info(
                f"{method} {path} -> {response.status_code} ({duration_ms}ms) "
                f"[req_id={req_id}]"
            )

            response.headers["X-Request-ID"] = req_id
            return response
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # SYS-L04: Single log line for errors
            logger.error(
                f"{method} {path} -> ERROR ({duration_ms}ms) "
                f"[req_id={req_id}] {type(e).__name__}: {str(e)}"
            )
            raise


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
        "/docs",
        "/redoc",
        "/openapi.json",
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
    STORY-210 AC10: Add standard security headers to all responses.

    Headers applied:
    - X-Content-Type-Options: nosniff — prevent MIME type sniffing
    - X-Frame-Options: DENY — prevent clickjacking
    - X-XSS-Protection: 1; mode=block — legacy XSS protection
    - Referrer-Policy: strict-origin-when-cross-origin — control referrer leakage
    - Permissions-Policy: camera=(), microphone=(), geolocation=() — disable unused APIs
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
