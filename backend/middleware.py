"""Request correlation and observability middleware."""
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
    """Inject request_id into all log records."""
    def filter(self, record):
        record.request_id = request_id_var.get("-")
        return True


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Add correlation/request ID to every request for distributed tracing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use incoming X-Request-ID or generate new
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(req_id)

        # Store in request state for access in route handlers
        request.state.request_id = req_id

        start_time = time.time()
        method = request.method
        path = request.url.path

        logger.info(f"→ {method} {path}")

        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(f"← {method} {path} {response.status_code} ({duration_ms}ms)")
            response.headers["X-Request-ID"] = req_id
            return response
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"✗ {method} {path} ERROR ({duration_ms}ms): {e}")
            raise
