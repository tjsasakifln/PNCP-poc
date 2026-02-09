"""Configuration models for PNCP client."""

from dataclasses import dataclass, field
from typing import Tuple, Type, List
import logging
import os
import sys


# PNCP Modality Codes (codigoModalidadeContratacao)
# Source: https://pncp.gov.br/api/pncp/v1/modalidades
MODALIDADES_PNCP = {
    1: "Leilão - Eletrônico",
    2: "Diálogo Competitivo",
    3: "Concurso",
    4: "Concorrência - Eletrônica",
    5: "Concorrência - Presencial",
    6: "Pregão - Eletrônico",
    7: "Pregão - Presencial",
    8: "Dispensa",
    9: "Inexigibilidade",
    10: "Manifestação de Interesse",
    11: "Pré-qualificação",
    12: "Credenciamento",
    13: "Leilão - Presencial",
    14: "Inaplicabilidade da Licitação",
    15: "Chamada pública",
}

# Default modalities for BidIQ Uniformes search
# Focus on Pregão Eletrônico (6) - most common for uniforms
# NOTE: Modalidade 8 (Dispensa) has 2000+ records and causes timeouts
DEFAULT_MODALIDADES: List[int] = [
    6,  # Pregão - Eletrônico (most common for uniforms, fast response)
]


@dataclass
class RetryConfig:
    """Configuration for HTTP retry logic."""

    max_retries: int = 3
    base_delay: float = 1.5  # seconds
    max_delay: float = 15.0  # seconds
    exponential_base: int = 2
    jitter: bool = True
    timeout: int = 30  # seconds

    # HTTP status codes that should trigger retry
    retryable_status_codes: Tuple[int, ...] = field(
        default_factory=lambda: (408, 429, 500, 502, 503, 504)
    )

    # Exception types that should trigger retry
    retryable_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=lambda: (
            ConnectionError,
            TimeoutError,
        )
    )


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application.

    Sets up a consistent logging format across all modules with proper
    level filtering and suppression of verbose third-party libraries.

    SECURITY (Issue #168):
    - In production (ENVIRONMENT=production), DEBUG logs are suppressed
    - Log sanitization should be applied to sensitive data before logging
    - See log_sanitizer.py for PII protection utilities

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to INFO. In production, DEBUG is elevated to INFO
               for security.

    Example:
        >>> setup_logging("DEBUG")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
        2026-01-25 23:00:00 | INFO     | __main__ | Application started
    """
    import os

    # SECURITY: In production, enforce minimum INFO level to prevent
    # accidental debug information exposure (Issue #168)
    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
    is_production = env in ("production", "prod")

    effective_level = level.upper()
    if is_production and effective_level == "DEBUG":
        effective_level = "INFO"
        # Note: We can't log this warning yet since logging isn't configured
        # The warning will be added after root logger setup below

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, effective_level))
    root_logger.addHandler(handler)

    # Log security enforcement if level was elevated
    if is_production and level.upper() == "DEBUG":
        root_logger.warning(
            "SECURITY: DEBUG level elevated to INFO in production (Issue #168)"
        )

    # Silence verbose logs from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# ============================================
# Feature Flags
# ============================================

def str_to_bool(value: str | None) -> bool:
    """
    Convert string environment variable to boolean.
    
    Accepts: 'true', '1', 'yes', 'on' (case-insensitive) as True
    Everything else (including None) is False
    
    Args:
        value: String value from environment variable
        
    Returns:
        Boolean interpretation of the value
        
    Examples:
        >>> str_to_bool("true")
        True
        >>> str_to_bool("1")
        True
        >>> str_to_bool("false")
        False
        >>> str_to_bool(None)
        False
    """
    if value is None:
        return False
    return value.lower() in ("true", "1", "yes", "on")


# Feature Flag: New Pricing Model (STORY-165)
# Controls plan-based capabilities, quota enforcement, and Excel gating
# Default: True (enabled - new pricing is production-ready)
ENABLE_NEW_PRICING: bool = str_to_bool(os.getenv("ENABLE_NEW_PRICING", "true"))

# Log feature flag state on import
logger = logging.getLogger(__name__)
logger.info(f"Feature Flag - ENABLE_NEW_PRICING: {ENABLE_NEW_PRICING}")


# ============================================
# CORS Configuration
# ============================================

# Default allowed origins for development
DEFAULT_CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Production allowed origins (always included when CORS_ORIGINS is set)
PRODUCTION_ORIGINS: list[str] = [
    "https://bidiq-frontend-production.up.railway.app",
    "https://bidiq-uniformes-production.up.railway.app",
]


def get_cors_origins() -> list[str]:
    """
    Get allowed CORS origins from environment variable.

    Environment Variable:
        CORS_ORIGINS: Comma-separated list of allowed origins.
                     If not set, defaults to localhost origins for development.

    Security:
        - Never allows "*" wildcard in production
        - Always includes production domains in Railway/production environments
        - Falls back to safe defaults for local development

    Examples:
        # Development (no env var set, RAILWAY_ENVIRONMENT not set):
        >>> get_cors_origins()
        ['http://localhost:3000', 'http://127.0.0.1:3000']

        # Production (Railway environment detected):
        >>> get_cors_origins()
        ['http://localhost:3000', 'http://127.0.0.1:3000',
         'https://bidiq-frontend-production.up.railway.app',
         'https://bidiq-uniformes-production.up.railway.app']

        # Production (env var set):
        >>> # CORS_ORIGINS=https://myapp.com,https://api.myapp.com
        >>> get_cors_origins()
        ['https://myapp.com', 'https://api.myapp.com',
         'https://bidiq-frontend-production.up.railway.app',
         'https://bidiq-uniformes-production.up.railway.app']

    Returns:
        List of allowed origin URLs
    """
    cors_env = os.getenv("CORS_ORIGINS", "").strip()

    # Detect if running in production environment (Railway, Docker, etc.)
    is_production = (
        os.getenv("RAILWAY_ENVIRONMENT") is not None or
        os.getenv("RAILWAY_PROJECT_ID") is not None or
        os.getenv("ENVIRONMENT", "").lower() in ("production", "prod") or
        os.getenv("ENV", "").lower() in ("production", "prod")
    )

    if not cors_env:
        # No environment variable set - start with development defaults
        origins = DEFAULT_CORS_ORIGINS.copy()

        if is_production:
            # In production, always include production origins even without CORS_ORIGINS
            logger.info("Production environment detected, including production origins")
            for prod_origin in PRODUCTION_ORIGINS:
                if prod_origin not in origins:
                    origins.append(prod_origin)
        else:
            logger.info("CORS_ORIGINS not set, using development defaults only")

        return origins

    # Parse comma-separated origins
    origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

    # Security check: reject wildcard in production
    if "*" in origins:
        logger.warning(
            "SECURITY WARNING: Wildcard '*' in CORS_ORIGINS is not recommended. "
            "Replacing with production defaults for security."
        )
        origins = [o for o in origins if o != "*"]

    # Always include production origins when env var is configured
    # (indicates production/staging environment)
    for prod_origin in PRODUCTION_ORIGINS:
        if prod_origin not in origins:
            origins.append(prod_origin)

    # Remove duplicates while preserving order
    seen = set()
    unique_origins = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique_origins.append(origin)

    logger.info(f"CORS origins configured: {unique_origins}")
    return unique_origins
