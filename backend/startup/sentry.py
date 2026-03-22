"""Sentry initialization and PII scrubbing callbacks."""

import logging
import os
import re

import httpx
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from log_sanitizer import mask_email, mask_token, mask_user_id, mask_ip_address, sanitize_dict, sanitize_string

logger = logging.getLogger(__name__)


def scrub_pii(event, hint):
    """Sentry before_send callback to strip PII from error events (AC3)."""
    if "request" in event:
        request = event["request"]
        if "headers" in request:
            request["headers"] = {
                k: (mask_token(v) if k.lower() in ("authorization", "cookie", "x-api-key") else v)
                for k, v in request["headers"].items()
            }
        if "data" in request and isinstance(request["data"], dict):
            request["data"] = sanitize_dict(request["data"])

    if "user" in event:
        user = event["user"]
        if "email" in user:
            user["email"] = mask_email(user["email"])
        if "id" in user:
            user["id"] = mask_user_id(str(user["id"]))
        if "ip_address" in user:
            user["ip_address"] = mask_ip_address(user["ip_address"])

    if "breadcrumbs" in event:
        for crumb in event.get("breadcrumbs", {}).get("values", []):
            if "message" in crumb:
                crumb["message"] = sanitize_string(crumb["message"])
            if "data" in crumb and isinstance(crumb["data"], dict):
                crumb["data"] = sanitize_dict(crumb["data"])

    if "exception" in event:
        for exc in event.get("exception", {}).get("values", []):
            if "value" in exc:
                exc["value"] = sanitize_string(exc["value"])

    return event


def _fingerprint_transients(event, hint):
    """Fingerprint transient errors to avoid Sentry issue flood (GTM-RESILIENCE-E02 AC4)."""
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
    """Combined before_send: PII scrubbing + transient fingerprinting + noise filtering."""
    exc_info = hint.get("exc_info")
    if exc_info and exc_info[1] is not None:
        exc = exc_info[1]
        if type(exc).__name__ == "CircuitBreakerOpenError":
            return None

    message = event.get("message", "")
    exc_values = event.get("exception", {}).get("values", [])
    for ev in exc_values:
        ev_value = ev.get("value", "")
        if "PGRST205" in ev_value:
            return None
        if "status 400" in ev_value or "status=400" in ev_value:
            if any(marker in ev_value for marker in ("pagina': 5", "pagina': 4", "pagina': 3", "pagina': 2", "page ")):
                return None
    if "PGRST205" in message:
        return None
    if ("status 400" in message or "status=400" in message) and "pagina" in message:
        pagina_match = re.search(r"pagina['\"]?\s*[:=]\s*(\d+)", message)
        if pagina_match and int(pagina_match.group(1)) > 1:
            return None

    for ev in exc_values:
        ev_value = ev.get("value", "")
        if any(marker in ev_value for marker in (
            "ReadTimeoutError", "ConnectTimeoutError", "Max retries exceeded",
            "pncp.gov.br", "timed out", "PNCPAPIError",
        )):
            return None
    if exc_info and exc_info[1] is not None:
        exc_type_name = type(exc_info[1]).__name__
        if exc_type_name in ("PNCPAPIError", "TimeoutError", "ReadTimeout"):
            return None

    event = scrub_pii(event, hint)
    if event is None:
        return None
    return _fingerprint_transients(event, hint)


def _traces_sampler(sampling_context):
    """Exclude health checks from Sentry traces."""
    path = sampling_context.get("asgi_scope", {}).get("path", "")
    if path in ("/health", "/health/live", "/health/ready", "/v1/health", "/v1/health/cache"):
        return 0.0
    return 0.1


def init_sentry(env: str, version: str) -> None:
    """Initialize Sentry SDK if DSN is configured."""
    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        from supabase_client import CircuitBreakerOpenError
        # CRIT-SIGSEGV: StarletteIntegration DISABLED — causes Segmentation Fault
        # on POST requests with Python 3.12 + cryptography>=46 (sentry-python#3421).
        # The _sentry_receive hook in starlette.py triggers SIGSEGV during TLS
        # handshake in auth middleware. FastApiIntegration alone captures errors fine.
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(transaction_style="endpoint", failed_request_status_codes=set()),
            ],
            traces_sampler=_traces_sampler,
            environment=env,
            release=version,
            before_send=_before_send,
            ignore_errors=[CircuitBreakerOpenError],
            enable_tracing=False,  # Disable performance tracing (SIGSEGV source)
            profiles_sample_rate=0,  # Disable profiling (SIGSEGV source)
        )
        logger.info("Sentry initialized for error tracking")
    else:
        logger.info("Sentry DSN not configured — error tracking disabled")
