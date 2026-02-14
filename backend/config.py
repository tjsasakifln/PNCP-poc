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

# Default modalities: competitive modalities most relevant for procurement search
# These four cover the vast majority of real competitive procurement opportunities
DEFAULT_MODALIDADES: List[int] = [
    4,  # Concorrência - Eletrônica
    5,  # Concorrência - Presencial
    6,  # Pregão - Eletrônico (most common for uniforms)
    7,  # Pregão - Presencial
]

# Modalities ALWAYS excluded from search results:
# These have a pre-defined winner — pure noise for users seeking opportunities
MODALIDADES_EXCLUIDAS: List[int] = [
    9,   # Inexigibilidade — inviabilidade de competição, vencedor pré-definido
    14,  # Inaplicabilidade da Licitação — sem processo competitivo
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

    # STORY-220 AC4: Configurable format — JSON for production, text for development
    log_format = os.getenv("LOG_FORMAT", "").lower()
    if not log_format:
        log_format = "json" if is_production else "text"

    # STORY-202 SYS-M01: Add RequestIDFilter to inject request_id into all logs
    # Import here to avoid circular dependency. Must be added to handler BEFORE
    # any logs are emitted so startup logs don't crash on missing %(request_id)s.
    from middleware import RequestIDFilter
    request_id_filter = RequestIDFilter()

    if log_format == "json":
        # STORY-220 AC2/AC3: JSON structured logging with all required fields
        from pythonjsonlogger import jsonlogger
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d %(request_id)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger_name",
            },
        )
    else:
        # Human-readable pipe-delimited format for development
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(request_id_filter)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, effective_level))
    root_logger.addHandler(handler)
    root_logger.addFilter(request_id_filter)

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

# ============================================
# LLM Arbiter Configuration (STORY-179 AC6)
# ============================================
# GPT-4o-mini for false positive/negative elimination
# Cost: ~R$ 0.00003 per classification (~R$ 0.50/month for 10K contracts)

# Feature flag to enable/disable LLM arbiter (both FP and FN flows)
LLM_ARBITER_ENABLED: bool = str_to_bool(os.getenv("LLM_ARBITER_ENABLED", "true"))

# LLM model for contract classification
LLM_ARBITER_MODEL: str = os.getenv("LLM_ARBITER_MODEL", "gpt-4o-mini")

# Max tokens for LLM output (1 token forces "SIM" or "NAO" response)
LLM_ARBITER_MAX_TOKENS: int = int(os.getenv("LLM_ARBITER_MAX_TOKENS", "1"))

# Temperature (0 = deterministic, 1 = creative)
LLM_ARBITER_TEMPERATURE: float = float(os.getenv("LLM_ARBITER_TEMPERATURE", "0"))

# Term density thresholds (adjustable without code changes)
# HOTFIX 2026-02-10: Adjusted based on bug-investigation-squad findings
#
# ============================================
# STORY-248 Threshold Review (2026-02-14)
# ============================================
# Reviewed thresholds against 15-sector expansion (vestuario, alimentos,
# informatica, mobiliario, papelaria, engenharia, software, facilities,
# saude, vigilancia, transporte, manutencao_predial, engenharia_rodoviaria,
# materiais_eletricos, materiais_hidraulicos).
#
# Decision: KEEP all three thresholds unchanged.
#
# Density metric: matched_term_occurrences / total_words_in_objetoCompra.
# Typical PNCP descriptions are 10-40 words, so density values map to:
#   - 10-word desc + 1 match = 10.0% (auto-accept)
#   - 20-word desc + 1 match =  5.0% (boundary: exactly 5% goes to LLM)
#   - 30-word desc + 1 match =  3.3% (LLM standard prompt)
#   - 50-word desc + 1 match =  2.0% (boundary: exactly 2% goes to LLM standard)
#   - 100-word desc + 1 match = 1.0% (boundary: exactly 1% goes to LLM conservative)
#
# HIGH (5%) rationale:
#   For the typical 15-30 word PNCP description, >5% means the keyword
#   appears prominently (1-2 times in 15-20 words). Combined with the
#   multi-layer defense (exclusion keywords, context_required_keywords,
#   max_contract_value per sector, and RED_FLAGS), false positives at
#   >5% density are rare. Further lowering to 3% was considered but would
#   increase false auto-approvals for 30-word descriptions with 1 match.
#
# MEDIUM (2%) rationale:
#   The 2-5% zone captures genuinely ambiguous cases for LLM evaluation.
#   Contracts in this range have keyword presence but it may be tangential.
#   The dual prompt approach (standard for 2-5%, conservative for 1-2%)
#   correctly applies more scrutiny to lower-density matches.
#
# LOW (1%) rationale:
#   Below 1%, the keyword match is incidental in a long description (100+
#   words with 1 match). Auto-rejection is appropriate. For typical 10-30
#   word descriptions, any single match already yields >3% density, so this
#   threshold primarily filters out verbose multi-topic procurement packages.
#
# Per-sector thresholds considered and REJECTED:
#   While keyword specificity varies by sector (e.g., "uniforme" is
#   unambiguous vs. "LED" is broader), the multi-layer defense stack
#   (exclusions + context_required + value caps + red flags + LLM arbiter)
#   compensates adequately. Adding 15 x 3 = 45 per-sector threshold
#   parameters would increase maintenance burden without clear benefit.
#
# NOTE (out of scope): The conservative prompt in llm_arbiter.py (lines
#   115-137) has a hardcoded sector description for "Vestuario e Uniformes"
#   that is incorrectly applied to all 15 sectors. This should be addressed
#   in a separate story to use each sector's actual description.
# ============================================
#
# Decision flow:
#   density > 5%       -> Auto-ACCEPT (high confidence, no LLM)
#   2% < density <= 5% -> LLM with standard prompt
#   1% <= density <= 2% -> LLM with conservative prompt + examples
#   density < 1%       -> Auto-REJECT (low confidence, no LLM)
#
# High threshold: density > X% = auto-accept without LLM (high confidence)
TERM_DENSITY_HIGH_THRESHOLD: float = float(
    os.getenv("TERM_DENSITY_HIGH_THRESHOLD", "0.05")
)  # 5% — reviewed 2026-02-14, kept (see rationale above)

# Medium threshold: density between MEDIUM and HIGH = LLM with standard prompt
TERM_DENSITY_MEDIUM_THRESHOLD: float = float(
    os.getenv("TERM_DENSITY_MEDIUM_THRESHOLD", "0.02")
)  # 2% — reviewed 2026-02-14, kept (see rationale above)

# Low threshold: density < X% = auto-reject without LLM (low confidence)
TERM_DENSITY_LOW_THRESHOLD: float = float(
    os.getenv("TERM_DENSITY_LOW_THRESHOLD", "0.01")
)  # 1% — reviewed 2026-02-14, kept (see rationale above)

# ============================================
# Filter Debugging & QA (STORY-181 AC1.3, AC7)
# ============================================
# Debug mode: log ALL contracts including approved ones
FILTER_DEBUG_MODE: bool = str_to_bool(os.getenv("FILTER_DEBUG_MODE", "false"))

# Debug sample size: log only the first N contracts (0 = disabled)
FILTER_DEBUG_SAMPLE: int = int(os.getenv("FILTER_DEBUG_SAMPLE", "0"))

# QA audit sample rate: flag X% of LLM decisions for manual review
# STORY-248 AC8 Review (2026-02-14): Confirmed at 10%.
# At 10%, after ~100 LLM decisions we have ~10 audit samples — sufficient
# to detect systematic bias. With 15 sectors generating LLM calls, volume
# is adequate for statistical significance without overwhelming reviewers.
QA_AUDIT_SAMPLE_RATE: float = float(os.getenv("QA_AUDIT_SAMPLE_RATE", "0.10"))

# Synonym matching feature flag (STORY-179 AC12)
SYNONYM_MATCHING_ENABLED: bool = str_to_bool(os.getenv("SYNONYM_MATCHING_ENABLED", "true"))

# Zero results relaxation feature flag (STORY-179 AC14)
ZERO_RESULTS_RELAXATION_ENABLED: bool = str_to_bool(
    os.getenv("ZERO_RESULTS_RELAXATION_ENABLED", "true")
)

logger = logging.getLogger(__name__)


# ============================================
# Runtime-Reloadable Feature Flags (STORY-226 AC16)
# ============================================
# Cache dict: {flag_name: (value, timestamp)}
# TTL-based: re-reads from env after expiry.
# Use get_feature_flag() for runtime reads.
# Use reload_feature_flags() or POST /v1/admin/feature-flags/reload to clear cache.

_feature_flag_cache: dict[str, tuple[bool, float]] = {}
_FEATURE_FLAG_TTL: float = 60.0  # seconds

# Registry of known feature flags with their env var names and defaults
_FEATURE_FLAG_REGISTRY: dict[str, tuple[str, str]] = {
    "ENABLE_NEW_PRICING": ("ENABLE_NEW_PRICING", "true"),
    "LLM_ARBITER_ENABLED": ("LLM_ARBITER_ENABLED", "true"),
    "SYNONYM_MATCHING_ENABLED": ("SYNONYM_MATCHING_ENABLED", "true"),
    "ZERO_RESULTS_RELAXATION_ENABLED": ("ZERO_RESULTS_RELAXATION_ENABLED", "true"),
    "FILTER_DEBUG_MODE": ("FILTER_DEBUG_MODE", "false"),
}


def get_feature_flag(name: str, default: bool | None = None) -> bool:
    """Get a feature flag value, reading from environment at runtime with caching.

    Reads the environment variable on each call, but caches the result for
    _FEATURE_FLAG_TTL seconds to avoid excessive os.getenv() overhead.

    Args:
        name: Feature flag name (e.g., "ENABLE_NEW_PRICING").
        default: Override default value. If None, uses the registry default
                 or False if the flag is not in the registry.

    Returns:
        Boolean value of the feature flag.

    Examples:
        >>> get_feature_flag("ENABLE_NEW_PRICING")
        True
        >>> get_feature_flag("MY_NEW_FLAG", default=False)
        False
    """
    import time as _time

    now = _time.time()

    # Check cache
    if name in _feature_flag_cache:
        cached_value, cached_at = _feature_flag_cache[name]
        if (now - cached_at) < _FEATURE_FLAG_TTL:
            return cached_value

    # Cache miss or expired — read from env
    if name in _FEATURE_FLAG_REGISTRY:
        env_var, registry_default = _FEATURE_FLAG_REGISTRY[name]
    else:
        env_var = name
        registry_default = "true" if default is True else "false"

    effective_default = registry_default if default is None else ("true" if default else "false")
    value = str_to_bool(os.getenv(env_var, effective_default))

    _feature_flag_cache[name] = (value, now)
    return value


def reload_feature_flags() -> dict[str, bool]:
    """Clear the feature flag cache, forcing re-read from environment on next access.

    Returns:
        Dict of all registered flags with their current (freshly read) values.
    """
    _feature_flag_cache.clear()
    logger.info("Feature flag cache cleared — flags will be re-read from environment")

    # Re-read all registered flags
    current_values: dict[str, bool] = {}
    for name in _FEATURE_FLAG_REGISTRY:
        current_values[name] = get_feature_flag(name)

    return current_values


def log_feature_flags() -> None:
    """Log feature flag states. Call AFTER setup_logging() to ensure proper formatting.

    STORY-220 AC6: Moved from module-level to function to prevent logging
    before RequestIDFilter is installed.
    """
    logger.info(f"Feature Flag - ENABLE_NEW_PRICING: {ENABLE_NEW_PRICING}")
    logger.info(f"Feature Flag - LLM_ARBITER_ENABLED: {LLM_ARBITER_ENABLED}")
    logger.info(f"Feature Flag - SYNONYM_MATCHING_ENABLED: {SYNONYM_MATCHING_ENABLED}")
    logger.info(f"Feature Flag - ZERO_RESULTS_RELAXATION_ENABLED: {ZERO_RESULTS_RELAXATION_ENABLED}")


# ============================================
# CORS Configuration
# ============================================

# Default allowed origins for development
DEFAULT_CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Production allowed origins (always included when CORS_ORIGINS is set)
# STORY-210 AC14: Added smartlic.tech custom domain
PRODUCTION_ORIGINS: list[str] = [
    "https://bidiq-frontend-production.up.railway.app",
    "https://bidiq-uniformes-production.up.railway.app",
    "https://smartlic.tech",
    "https://www.smartlic.tech",
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


def validate_env_vars() -> None:
    """Validate required and recommended environment variables at startup.

    AC12: Check required vars: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET
    AC13: Warn on recommended vars: OPENAI_API_KEY, STRIPE_SECRET_KEY, SENTRY_DSN
    AC14: Raise RuntimeError if critical vars missing AND ENVIRONMENT=production
    """
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_JWT_SECRET"]
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
