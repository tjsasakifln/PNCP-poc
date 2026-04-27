"""Core configuration utilities: logging, env helpers, validation."""

import logging
import os
import sys


def str_to_bool(value: str | None) -> bool:
    """Convert string environment variable to boolean.

    Accepts: 'true', '1', 'yes', 'on' (case-insensitive) as True.
    Everything else (including None) is False.
    """
    if value is None:
        return False
    return value.lower() in ("true", "1", "yes", "on")


logger = logging.getLogger("config")


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application.

    SECURITY (Issue #168): In production, DEBUG logs are suppressed.
    STORY-220 AC4: JSON for production, text for development.
    STORY-202 SYS-M01: RequestIDFilter for request_id in all logs.
    STORY-330 AC1: Removes duplicate Gunicorn handlers.
    """
    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
    is_production = env in ("production", "prod")

    effective_level = level.upper()
    if is_production and effective_level == "DEBUG":
        effective_level = "INFO"

    # STORY-220 AC4: Configurable format
    log_format = os.getenv("LOG_FORMAT", "").lower()
    if not log_format:
        log_format = "json" if is_production else "text"

    # STORY-202 SYS-M01: RequestIDFilter
    from middleware import RequestIDFilter
    request_id_filter = RequestIDFilter()

    if log_format == "json":
        from pythonjsonlogger import jsonlogger
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d %(request_id)s %(search_id)s %(correlation_id)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger_name",
            },
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | req=%(request_id)s | search=%(search_id)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(request_id_filter)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, effective_level))

    # STORY-330 AC1: Remove pre-existing stdout/stderr handlers
    for existing in root_logger.handlers[:]:
        if isinstance(existing, logging.StreamHandler):
            stream = getattr(existing, "stream", None)
            if stream in (sys.stdout, sys.stderr):
                root_logger.removeHandler(existing)
                existing.close()

    root_logger.addHandler(handler)
    root_logger.addFilter(request_id_filter)

    if is_production and level.upper() == "DEBUG":
        root_logger.warning(
            "SECURITY: DEBUG level elevated to INFO in production (Issue #168)"
        )

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def validate_env_vars() -> None:
    """Validate required and recommended environment variables at startup.

    AC12: Check required vars: SUPABASE_URL, SERVICE_ROLE_KEY, JWT_SECRET, STRIPE_WEBHOOK_SECRET
    AC13: Warn on recommended vars: OPENAI_API_KEY, STRIPE_SECRET_KEY, SENTRY_DSN
    AC14: Raise RuntimeError if critical vars missing AND ENVIRONMENT=production

    MON-FN-005: MIXPANEL_TOKEN promoted to required in production. Memory
    `reference_mixpanel_backend_token_gap_2026_04_24` — token was silently
    absent in prod, suppressing paywall_hit/trial_started events for an
    unknown period. Funnel analytics is oxygen for monetization decisions.
    """
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_JWT_SECRET", "STRIPE_WEBHOOK_SECRET", "MIXPANEL_TOKEN"]
    recommended_vars = ["OPENAI_API_KEY", "STRIPE_SECRET_KEY", "SENTRY_DSN"]

    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
    is_production = env in ("production", "prod")

    missing_required = [var for var in required_vars if not os.getenv(var)]
    missing_recommended = [var for var in recommended_vars if not os.getenv(var)]

    if missing_required:
        msg = f"Missing required environment variables: {', '.join(missing_required)}"
        if is_production:
            raise RuntimeError(f"FATAL: {msg}. Cannot start in production without these.")
        else:
            logger.warning(f"{msg} (non-production, continuing with degraded functionality)")

    if missing_recommended:
        logger.warning(f"Missing recommended environment variables: {', '.join(missing_recommended)}")
