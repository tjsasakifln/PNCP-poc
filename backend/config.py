"""Configuration models for PNCP client."""

from dataclasses import dataclass, field
from typing import Tuple, Type, List
import logging
import os
import sys

# CRIT-038: Import requests exceptions for retryable_exceptions.
# requests.exceptions.ConnectionError inherits from IOError, NOT builtins.ConnectionError.
# Without these, fetch_page's except clause silently misses requests errors → Sentry.
try:
    import requests.exceptions as _req_exc
except ImportError:
    _req_exc = None  # type: ignore[assignment]


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
    """Configuration for HTTP retry logic.

    STORY-282 AC1: Defaults updated to use PNCP-specific env vars when available.
    """

    max_retries: int = int(os.getenv("PNCP_MAX_RETRIES", "1"))  # STORY-282: was 3, now 1
    base_delay: float = 1.5  # seconds
    max_delay: float = 15.0  # seconds
    exponential_base: int = 2
    jitter: bool = True
    timeout: int = int(os.getenv("PNCP_READ_TIMEOUT", "15"))  # STORY-282: was 30, now 15
    connect_timeout: float = float(os.getenv("PNCP_CONNECT_TIMEOUT", "10"))  # STORY-282: was 30, now 10
    read_timeout: float = float(os.getenv("PNCP_READ_TIMEOUT", "15"))  # STORY-282: was 30, now 15

    # HTTP status codes that should trigger retry
    # GTM-FIX-029 AC12: 422 added — PNCP returns 422 for certain UF+modality combos
    retryable_status_codes: Tuple[int, ...] = field(
        default_factory=lambda: (408, 422, 429, 500, 502, 503, 504)
    )

    # Exception types that should trigger retry
    # CRIT-038: Added requests.exceptions.* — requests raises its OWN ConnectionError
    # and Timeout classes that inherit from IOError, NOT from builtins.ConnectionError.
    # Without these, fetch_page's except clause never catches requests timeout/connection
    # errors, allowing them to bubble up unhandled to Sentry.
    retryable_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=lambda: (
            ConnectionError,    # builtins.ConnectionError (OSError subclass)
            TimeoutError,       # builtins.TimeoutError (OSError subclass)
            *(
                (
                    _req_exc.ConnectionError,  # requests — IOError subclass, NOT builtins.ConnectionError
                    _req_exc.Timeout,          # requests — inherits from requests.ConnectionError
                    _req_exc.ReadTimeout,      # requests — specific read timeout
                )
                if _req_exc is not None
                else ()
            ),
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
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d %(request_id)s %(search_id)s %(correlation_id)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger_name",
            },
        )
    else:
        # Human-readable pipe-delimited format for development
        # CRIT-004 AC9: Include search_id in log format
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | req=%(request_id)s | search=%(search_id)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(request_id_filter)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, effective_level))

    # STORY-330 AC1: Remove pre-existing stdout/stderr handlers to prevent duplicates.
    # Gunicorn's logconfig_dict adds a "stdout" handler to root before workers
    # call setup_logging() → without clearing, each log line is emitted 2x.
    # Only remove handlers targeting stdout/stderr (preserves test framework handlers).
    for existing in root_logger.handlers[:]:
        if isinstance(existing, logging.StreamHandler):
            stream = getattr(existing, "stream", None)
            if stream in (sys.stdout, sys.stderr):
                root_logger.removeHandler(existing)
                existing.close()

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
# GTM-FIX-028 AC5: Migrated from gpt-4o-mini to gpt-4.1-nano (33% cheaper, same quality for binary)
LLM_ARBITER_MODEL: str = os.getenv("LLM_ARBITER_MODEL", "gpt-4.1-nano")

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
# NOTE: Resolved by STORY-251 — conservative prompt now uses dynamic sector
#   lookup via get_sector(setor_id) in llm_arbiter.py:45-109.
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

# GTM-FIX-028: LLM Zero Match — classify bids with 0 keyword matches via LLM
# When enabled, bids that fail keyword matching are sent to LLM for sector-aware
# classification instead of being auto-rejected. Disables FLUXO 2 to avoid
# double-classification.
LLM_ZERO_MATCH_ENABLED: bool = str_to_bool(
    os.getenv("LLM_ZERO_MATCH_ENABLED", "true")
)

# UX-402: LLM Zero Match Batch — classify up to 20 bids per LLM call
# When enabled, sends numbered list of objects in a single prompt instead of
# individual calls. Reduces ~50 calls to ~3, cutting zero-match latency from ~8s to ~1.5s.
LLM_ZERO_MATCH_BATCH_ENABLED: bool = str_to_bool(
    os.getenv("LLM_ZERO_MATCH_BATCH_ENABLED", "true")
)

# UX-402 AC1: Max items per batch call (GPT-4.1-nano handles 20 easily within token limits)
LLM_ZERO_MATCH_BATCH_SIZE: int = int(os.getenv("LLM_ZERO_MATCH_BATCH_SIZE", "20"))

# UX-402 AC7: Timeout per batch call in seconds
LLM_ZERO_MATCH_BATCH_TIMEOUT: float = float(os.getenv("LLM_ZERO_MATCH_BATCH_TIMEOUT", "5.0"))

# STORY-354 AC8: LLM fallback to PENDING_REVIEW instead of REJECT for zero-match bids
# When enabled, bids with 0% keyword density that fail LLM classification are marked
# PENDING_REVIEW instead of silently discarded. Allows reclassification when LLM returns.
# CRIT-057: Time budget for zero-match LLM classification inside filter
FILTER_ZERO_MATCH_BUDGET_S: float = float(os.getenv("FILTER_ZERO_MATCH_BUDGET_S", "30"))

# CRIT-058: Cap + sampling for zero-match LLM classification
MAX_ZERO_MATCH_ITEMS: int = int(os.getenv("MAX_ZERO_MATCH_ITEMS", "200"))
ZERO_MATCH_VALUE_RATIO: float = float(os.getenv("ZERO_MATCH_VALUE_RATIO", "0.7"))

# CRIT-059: Async zero-match — move LLM zero-match classification to ARQ background job
ASYNC_ZERO_MATCH_ENABLED: bool = str_to_bool(
    os.getenv("ASYNC_ZERO_MATCH_ENABLED", "false")
)
# CRIT-059 AC7: Global timeout for the background zero-match job
ZERO_MATCH_JOB_TIMEOUT_S: int = int(os.getenv("ZERO_MATCH_JOB_TIMEOUT_S", "120"))

LLM_FALLBACK_PENDING_ENABLED: bool = str_to_bool(
    os.getenv("LLM_FALLBACK_PENDING_ENABLED", "true")
)

# STORY-354 AC7: Pending review bids expire after 24h
PENDING_REVIEW_TTL_SECONDS: int = int(os.getenv("PENDING_REVIEW_TTL_SECONDS", "86400"))

# STORY-354 AC4: Max retries for reclassification ARQ job
PENDING_REVIEW_MAX_RETRIES: int = int(os.getenv("PENDING_REVIEW_MAX_RETRIES", "3"))

# STORY-354 AC4: Delay between reclassification attempts (seconds)
PENDING_REVIEW_RETRY_DELAY: int = int(os.getenv("PENDING_REVIEW_RETRY_DELAY", "300"))

# ============================================
# D-02: LLM Structured Output with Evidence
# ============================================
# When enabled, LLM arbiter returns JSON with confidence, evidence, rejection reason
# instead of binary SIM/NAO. Allows re-ranking by confidence and audit trail.
LLM_STRUCTURED_OUTPUT_ENABLED: bool = str_to_bool(
    os.getenv("LLM_STRUCTURED_OUTPUT_ENABLED", "true")
)

# ============================================
# D-01: Item Inspection (Gray Zone Enhancement)
# ============================================
# Feature flag: enable/disable item-level inspection for gray zone bids (0-5% density)
ITEM_INSPECTION_ENABLED: bool = str_to_bool(
    os.getenv("ITEM_INSPECTION_ENABLED", "true")
)

# Max item-fetch calls per search (budget). Env var can increase but not below 5.
_MAX_ITEM_RAW = int(os.getenv("MAX_ITEM_INSPECTIONS", "20"))
MAX_ITEM_INSPECTIONS: int = max(5, _MAX_ITEM_RAW)

# Timeout per individual item-fetch request (seconds)
ITEM_INSPECTION_TIMEOUT: float = float(os.getenv("ITEM_INSPECTION_TIMEOUT", "5"))

# Global timeout for the entire item inspection phase (seconds)
ITEM_INSPECTION_PHASE_TIMEOUT: float = float(
    os.getenv("ITEM_INSPECTION_PHASE_TIMEOUT", "15")
)

# Max concurrent item-fetch requests (semaphore limit)
ITEM_INSPECTION_CONCURRENCY: int = int(os.getenv("ITEM_INSPECTION_CONCURRENCY", "5"))

# ============================================
# STORY-264: Trial Duration
# ============================================
TRIAL_DURATION_DAYS: int = int(os.getenv("TRIAL_DURATION_DAYS", "14"))  # STORY-319: 14-day trial (was 30)

# STORY-319 AC6: Feature flag for gradual rollout of 14-day trial
TRIAL_14_DAYS_ENABLED: bool = str_to_bool(os.getenv("TRIAL_14_DAYS_ENABLED", "true"))

# STORY-266: Trial Reminder Emails
TRIAL_EMAILS_ENABLED: bool = str_to_bool(os.getenv("TRIAL_EMAILS_ENABLED", "true"))

# STORY-320: Trial Paywall — soft paywall from day 7 of trial
TRIAL_PAYWALL_ENABLED: bool = str_to_bool(os.getenv("TRIAL_PAYWALL_ENABLED", "true"))
TRIAL_PAYWALL_DAY: int = int(os.getenv("TRIAL_PAYWALL_DAY", "7"))
TRIAL_PAYWALL_MAX_RESULTS: int = int(os.getenv("TRIAL_PAYWALL_MAX_RESULTS", "10"))
TRIAL_PAYWALL_MAX_PIPELINE: int = int(os.getenv("TRIAL_PAYWALL_MAX_PIPELINE", "5"))

# ============================================
# D-04: Viability Assessment
# ============================================
VIABILITY_WEIGHT_MODALITY: float = float(os.getenv("VIABILITY_WEIGHT_MODALITY", "0.30"))
VIABILITY_WEIGHT_TIMELINE: float = float(os.getenv("VIABILITY_WEIGHT_TIMELINE", "0.25"))
VIABILITY_WEIGHT_VALUE_FIT: float = float(os.getenv("VIABILITY_WEIGHT_VALUE_FIT", "0.25"))
VIABILITY_WEIGHT_GEOGRAPHY: float = float(os.getenv("VIABILITY_WEIGHT_GEOGRAPHY", "0.20"))

# ============================================
# E-03: Prometheus Metrics
# ============================================
METRICS_ENABLED: bool = str_to_bool(os.getenv("METRICS_ENABLED", "true"))
METRICS_TOKEN: str = os.getenv("METRICS_TOKEN", "")

# ============================================
# B-01: Background Revalidation
# ============================================
# Timeout for background revalidation tasks (seconds). Does not affect active requests.
REVALIDATION_TIMEOUT: int = int(os.getenv("REVALIDATION_TIMEOUT", "180"))

# Maximum concurrent background revalidations per worker process.
MAX_CONCURRENT_REVALIDATIONS: int = int(os.getenv("MAX_CONCURRENT_REVALIDATIONS", "3"))

# Minimum interval between revalidations of the same cache key (seconds). 10 minutes default.
REVALIDATION_COOLDOWN_S: int = int(os.getenv("REVALIDATION_COOLDOWN_S", "600"))

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
    "LLM_ZERO_MATCH_ENABLED": ("LLM_ZERO_MATCH_ENABLED", "true"),
    "LLM_ZERO_MATCH_BATCH_ENABLED": ("LLM_ZERO_MATCH_BATCH_ENABLED", "true"),
    "ASYNC_ZERO_MATCH_ENABLED": ("ASYNC_ZERO_MATCH_ENABLED", "false"),
    "CO_OCCURRENCE_RULES_ENABLED": ("CO_OCCURRENCE_RULES_ENABLED", "true"),
    "FILTER_DEBUG_MODE": ("FILTER_DEBUG_MODE", "false"),
    "ITEM_INSPECTION_ENABLED": ("ITEM_INSPECTION_ENABLED", "true"),
    "LLM_STRUCTURED_OUTPUT_ENABLED": ("LLM_STRUCTURED_OUTPUT_ENABLED", "true"),
    "VIABILITY_ASSESSMENT_ENABLED": ("VIABILITY_ASSESSMENT_ENABLED", "true"),
    "USER_FEEDBACK_ENABLED": ("USER_FEEDBACK_ENABLED", "true"),
    "PROXIMITY_CONTEXT_ENABLED": ("PROXIMITY_CONTEXT_ENABLED", "true"),
    "RATE_LIMITING_ENABLED": ("RATE_LIMITING_ENABLED", "true"),
    "SECTOR_RED_FLAGS_ENABLED": ("SECTOR_RED_FLAGS_ENABLED", "true"),
    "TRIAL_EMAILS_ENABLED": ("TRIAL_EMAILS_ENABLED", "true"),
    "TRIAL_PAYWALL_ENABLED": ("TRIAL_PAYWALL_ENABLED", "true"),
    "CACHE_REFRESH_ENABLED": ("CACHE_REFRESH_ENABLED", "false"),
    "SEARCH_ASYNC_ENABLED": ("SEARCH_ASYNC_ENABLED", "false"),
    "BID_ANALYSIS_ENABLED": ("BID_ANALYSIS_ENABLED", "true"),
    # STORY-267: Term search quality parity flags (gradual opt-in)
    "TERM_SEARCH_LLM_AWARE": ("TERM_SEARCH_LLM_AWARE", "false"),
    "TERM_SEARCH_SYNONYMS": ("TERM_SEARCH_SYNONYMS", "false"),
    "TERM_SEARCH_VIABILITY_GENERIC": ("TERM_SEARCH_VIABILITY_GENERIC", "false"),
    "TERM_SEARCH_FILTER_CONTEXT": ("TERM_SEARCH_FILTER_CONTEXT", "false"),
    "CACHE_WARMING_ENABLED": ("CACHE_WARMING_ENABLED", "false"),
    # STORY-306: Cache correctness — dual-read for thundering herd mitigation
    "CACHE_LEGACY_KEY_FALLBACK": ("CACHE_LEGACY_KEY_FALLBACK", "true"),
    "SHOW_CACHE_FALLBACK_BANNER": ("SHOW_CACHE_FALLBACK_BANNER", "true"),
    "HEALTH_CANARY_ENABLED": ("HEALTH_CANARY_ENABLED", "true"),
    # CRIT-047 AC6: PCP v2 disable flag (reads PCP_ENABLED env var, default true)
    "PCP_V2_ENABLED": ("PCP_ENABLED", "true"),
    # STORY-354 AC8: LLM fallback to PENDING_REVIEW instead of REJECT
    "LLM_FALLBACK_PENDING_ENABLED": ("LLM_FALLBACK_PENDING_ENABLED", "true"),
}

# ============================================
# STORY-267: Term Search Quality Parity
# ============================================
TERM_SEARCH_LLM_AWARE: bool = str_to_bool(os.getenv("TERM_SEARCH_LLM_AWARE", "false"))
TERM_SEARCH_SYNONYMS: bool = str_to_bool(os.getenv("TERM_SEARCH_SYNONYMS", "false"))
TERM_SEARCH_VIABILITY_GENERIC: bool = str_to_bool(os.getenv("TERM_SEARCH_VIABILITY_GENERIC", "false"))
TERM_SEARCH_FILTER_CONTEXT: bool = str_to_bool(os.getenv("TERM_SEARCH_FILTER_CONTEXT", "false"))

# Generic value range for term-based searches without sector context
TERM_SEARCH_VALUE_RANGE_MIN: float = float(os.getenv("TERM_SEARCH_VALUE_RANGE_MIN", "10000"))
TERM_SEARCH_VALUE_RANGE_MAX: float = float(os.getenv("TERM_SEARCH_VALUE_RANGE_MAX", "50000000"))

# ============================================
# GTM-STAB-003: Timeout Chain (Railway 300s hard limit, conservative for pre-async mode)
# ============================================
PIPELINE_TIMEOUT: int = int(os.getenv("PIPELINE_TIMEOUT", "110"))
CONSOLIDATION_TIMEOUT: int = int(os.getenv("CONSOLIDATION_TIMEOUT", "100"))
PNCP_TIMEOUT_PER_SOURCE: int = int(os.getenv("PNCP_TIMEOUT_PER_SOURCE", "80"))
PNCP_TIMEOUT_PER_UF: int = int(os.getenv("PNCP_TIMEOUT_PER_UF", "30"))
PNCP_TIMEOUT_PER_UF_DEGRADED: int = int(os.getenv("PNCP_TIMEOUT_PER_UF_DEGRADED", "15"))
PIPELINE_SKIP_LLM_AFTER_S: int = int(os.getenv("PIPELINE_SKIP_LLM_AFTER_S", "90"))
PIPELINE_SKIP_VIABILITY_AFTER_S: int = int(os.getenv("PIPELINE_SKIP_VIABILITY_AFTER_S", "100"))

# ============================================
# STORY-282: PNCP Timeout Resilience
# ============================================
# AC1: Aggressive PNCP timeouts — fail fast, don't waste time retrying slow API
PNCP_CONNECT_TIMEOUT: float = float(os.getenv("PNCP_CONNECT_TIMEOUT", "10"))  # was 30
PNCP_READ_TIMEOUT: float = float(os.getenv("PNCP_READ_TIMEOUT", "15"))  # was 30
PNCP_MAX_RETRIES: int = int(os.getenv("PNCP_MAX_RETRIES", "1"))  # was 3
# AC2: Page limit per modality — SP/mod6 has 30 pages, cap at 5 (250 items max)
PNCP_MAX_PAGES: int = int(os.getenv("PNCP_MAX_PAGES", "5"))
# AC3: Cache-first user search timeout — max seconds for fresh fetch before serving cache
CACHE_FIRST_FRESH_TIMEOUT: int = int(os.getenv("CACHE_FIRST_FRESH_TIMEOUT", "60"))

# GTM-STAB-003 AC3: Consolidation early return — return partial results when most UFs responded
EARLY_RETURN_THRESHOLD_PCT: float = float(os.getenv("EARLY_RETURN_THRESHOLD_PCT", "0.8"))  # 80% of UFs
EARLY_RETURN_TIME_S: float = float(os.getenv("EARLY_RETURN_TIME_S", "80.0"))  # seconds elapsed

# ============================================
# P1.2: Startup Cache Warm-up (Top Sector+UF Combos)
# ============================================
# Enable startup warm-up for top sector+UF combinations (default: true)
WARMUP_ENABLED: bool = str_to_bool(os.getenv("WARMUP_ENABLED", "true"))

# CRIT-055: All 27 Brazilian UFs (used as default warmup coverage)
ALL_BRAZILIAN_UFS: list[str] = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]

# CRIT-055 AC1: Default UF order when no history (popular states first)
DEFAULT_UF_PRIORITY: list[str] = [
    "SP", "RJ", "MG", "BA", "PR", "RS", "SC", "PE", "CE", "GO",
    "DF", "PA", "MA", "AM", "ES", "PB", "RN", "MT", "MS", "AL",
    "PI", "SE", "RO", "TO", "AC", "AP", "RR",
]

# Comma-separated list of UFs to pre-warm on startup (default: all 27 UFs)
WARMUP_UFS: list[str] = [
    uf.strip() for uf in os.getenv("WARMUP_UFS", ",".join(ALL_BRAZILIAN_UFS)).split(",") if uf.strip()
]

# Comma-separated list of sector IDs to pre-warm on startup (default: top 5 sectors)
WARMUP_SECTORS: list[str] = [
    s.strip()
    for s in os.getenv("WARMUP_SECTORS", "software,informatica,engenharia,saude,facilities").split(",")
    if s.strip()
]

# Seconds to wait after startup before starting warm-up (default: 120s — lets app stabilize)
WARMUP_STARTUP_DELAY_SECONDS: int = int(os.getenv("WARMUP_STARTUP_DELAY_SECONDS", "120"))

# Seconds to sleep between consecutive warm-up dispatches (rate-limiting, default: 2s)
WARMUP_BATCH_DELAY_SECONDS: float = float(os.getenv("WARMUP_BATCH_DELAY_SECONDS", "2"))

# CRIT-055 AC3: Periodic warmup interval (hours) — re-warms top combinations
WARMUP_PERIODIC_INTERVAL_HOURS: int = int(os.getenv("WARMUP_PERIODIC_INTERVAL_HOURS", "3"))

# CRIT-055 AC4: Max requests/second to PNCP during warmup
WARMUP_RATE_LIMIT_RPS: float = float(os.getenv("WARMUP_RATE_LIMIT_RPS", "2.0"))

# CRIT-055 AC4: Pause duration (seconds) when PNCP canary reports degraded
WARMUP_PNCP_DEGRADED_PAUSE_S: float = float(os.getenv("WARMUP_PNCP_DEGRADED_PAUSE_S", "300.0"))

# CRIT-055 AC1: UFs per batch in startup warmup
WARMUP_UF_BATCH_SIZE: int = int(os.getenv("WARMUP_UF_BATCH_SIZE", "5"))

# ============================================
# GTM-STAB-007: Cache Warming
# ============================================
CACHE_WARMING_ENABLED: bool = str_to_bool(os.getenv("CACHE_WARMING_ENABLED", "false"))
CACHE_WARMING_INTERVAL_HOURS: int = int(os.getenv("CACHE_WARMING_INTERVAL_HOURS", "4"))
CACHE_WARMING_CONCURRENCY: int = int(os.getenv("CACHE_WARMING_CONCURRENCY", "2"))
CACHE_WARMING_BUDGET_MINUTES: int = int(os.getenv("CACHE_WARMING_BUDGET_MINUTES", "30"))

# STAB-007 AC4: Cache warming non-interference with user searches
WARMING_BATCH_DELAY_S: float = float(os.getenv("WARMING_BATCH_DELAY_S", "3.0"))
WARMING_BUDGET_TIMEOUT_S: float = float(os.getenv("WARMING_BUDGET_TIMEOUT_S", "1800"))
WARMING_PAUSE_ON_ACTIVE_S: float = float(os.getenv("WARMING_PAUSE_ON_ACTIVE_S", "10.0"))
WARMING_MAX_PAUSE_CYCLES: int = int(os.getenv("WARMING_MAX_PAUSE_CYCLES", "3"))
WARMING_USER_ID: str = "00000000-0000-0000-0000-000000000000"
WARMING_RATE_LIMIT_BACKOFF_S: float = float(os.getenv("WARMING_RATE_LIMIT_BACKOFF_S", "60.0"))

# ============================================
# CRIT-032: Periodic Cache Refresh (ARQ Cron)
# ============================================
CACHE_REFRESH_ENABLED: bool = str_to_bool(os.getenv("CACHE_REFRESH_ENABLED", "false"))
CACHE_REFRESH_INTERVAL_HOURS: int = int(os.getenv("CACHE_REFRESH_INTERVAL_HOURS", "12"))
CACHE_REFRESH_BATCH_SIZE: int = int(os.getenv("CACHE_REFRESH_BATCH_SIZE", "25"))
CACHE_REFRESH_STAGGER_SECONDS: int = int(os.getenv("CACHE_REFRESH_STAGGER_SECONDS", "5"))

# ============================================
# STORY-306: Cache Correctness & Data Integrity
# ============================================
# AC12: Dual-read for thundering herd mitigation on deploy — try new key (with dates)
# first, fall back to legacy key (without dates) if miss. Disable manually after 24h.
CACHE_LEGACY_KEY_FALLBACK: bool = str_to_bool(os.getenv("CACHE_LEGACY_KEY_FALLBACK", "true"))
# AC6: Frontend banner visibility when cache_fallback is true
SHOW_CACHE_FALLBACK_BANNER: bool = str_to_bool(os.getenv("SHOW_CACHE_FALLBACK_BANNER", "true"))
# AC13: Cache warming post-deploy — revalidate top queries in first 5min after startup
CACHE_WARMING_POST_DEPLOY_ENABLED: bool = str_to_bool(os.getenv("CACHE_WARMING_POST_DEPLOY_ENABLED", "true"))
CACHE_WARMING_POST_DEPLOY_TOP_N: int = int(os.getenv("CACHE_WARMING_POST_DEPLOY_TOP_N", "10"))
CACHE_WARMING_POST_DEPLOY_DELAY_S: int = int(os.getenv("CACHE_WARMING_POST_DEPLOY_DELAY_S", "30"))

# ============================================
# STORY-292: Async Search via asyncio.create_task (no ARQ dependency)
# ============================================
SEARCH_ASYNC_ENABLED: bool = str_to_bool(os.getenv("SEARCH_ASYNC_ENABLED", "false"))

# STORY-363: Async search pipeline via ARQ Worker
SEARCH_JOB_TIMEOUT: int = int(os.getenv("SEARCH_JOB_TIMEOUT", "300"))  # AC5: max pipeline duration in worker
MAX_CONCURRENT_SEARCHES: int = int(os.getenv("MAX_CONCURRENT_SEARCHES", "3"))  # AC14: per-user concurrent limit

# ============================================
# D-05: User Feedback Loop
# ============================================
USER_FEEDBACK_ENABLED: bool = str_to_bool(os.getenv("USER_FEEDBACK_ENABLED", "true"))
USER_FEEDBACK_RATE_LIMIT: int = int(os.getenv("USER_FEEDBACK_RATE_LIMIT", "50"))  # per user per hour

# ============================================
# SECTOR-PROX: Proximity Context Filter
# ============================================
PROXIMITY_CONTEXT_ENABLED: bool = str_to_bool(os.getenv("PROXIMITY_CONTEXT_ENABLED", "true"))
PROXIMITY_WINDOW_SIZE: int = int(os.getenv("PROXIMITY_WINDOW_SIZE", "8"))

# ============================================
# STORY-259: Bid Analysis
# ============================================
DEEP_ANALYSIS_RATE_LIMIT: int = int(os.getenv("DEEP_ANALYSIS_RATE_LIMIT", "20"))  # per user per hour
BID_ANALYSIS_ENABLED: bool = str_to_bool(os.getenv("BID_ANALYSIS_ENABLED", "true"))

# ============================================
# STORY-260: Atestados/Certificações Catalog
# ============================================
ATESTADOS_DISPONIVEIS: list[dict] = [
    {"id": "crea", "label": "CREA (Engenharia)", "sectors": ["engenharia", "manutencao_predial", "engenharia_rodoviaria"]},
    {"id": "crf", "label": "CRF (Farmácia)", "sectors": ["saude"]},
    {"id": "inmetro", "label": "INMETRO", "sectors": ["vestuario", "materiais_eletricos"]},
    {"id": "iso_9001", "label": "ISO 9001 (Qualidade)", "sectors": ["*"]},
    {"id": "iso_14001", "label": "ISO 14001 (Ambiental)", "sectors": ["*"]},
    {"id": "pgr_pcmso", "label": "PGR/PCMSO (Segurança do Trabalho)", "sectors": ["facilities", "vigilancia"]},
    {"id": "alvara_sanitario", "label": "Alvará Sanitário", "sectors": ["alimentos", "saude"]},
    {"id": "registro_anvisa", "label": "Registro ANVISA", "sectors": ["saude"]},
    {"id": "habilitacao_antt", "label": "Habilitação ANTT", "sectors": ["transporte"]},
    {"id": "registro_cfq", "label": "Registro CRQ (Química)", "sectors": ["saude", "materiais_hidraulicos"]},
    {"id": "licenca_ambiental", "label": "Licença Ambiental", "sectors": ["engenharia", "engenharia_rodoviaria"]},
    {"id": "crt", "label": "CRT (Técnico)", "sectors": ["informatica", "software"]},
]


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
# STORY-266: Legacy Railway hostnames kept for backward compat until Railway service rename
PRODUCTION_ORIGINS: list[str] = [
    "https://smartlic.tech",
    "https://www.smartlic.tech",
    "https://smartlic-frontend-production.up.railway.app",
    "https://smartlic-backend-production.up.railway.app",
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
         'https://smartlic.tech', 'https://www.smartlic.tech',
         'https://smartlic-frontend-production.up.railway.app',
         'https://smartlic-backend-production.up.railway.app']

        # Production (env var set):
        >>> # CORS_ORIGINS=https://myapp.com,https://api.myapp.com
        >>> get_cors_origins()
        ['https://myapp.com', 'https://api.myapp.com',
         'https://smartlic.tech', 'https://www.smartlic.tech',
         'https://smartlic-frontend-production.up.railway.app',
         'https://smartlic-backend-production.up.railway.app']

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


# ============================================================================
# STORY-296: Bulkhead Per Source — concurrency & timeout isolation
# ============================================================================
PNCP_BULKHEAD_CONCURRENCY: int = int(os.getenv("PNCP_BULKHEAD_CONCURRENCY", "5"))
PCP_BULKHEAD_CONCURRENCY: int = int(os.getenv("PCP_BULKHEAD_CONCURRENCY", "3"))
COMPRASGOV_BULKHEAD_CONCURRENCY: int = int(os.getenv("COMPRASGOV_BULKHEAD_CONCURRENCY", "3"))
PNCP_SOURCE_TIMEOUT: float = float(os.getenv("PNCP_SOURCE_TIMEOUT", "80"))
PCP_SOURCE_TIMEOUT: float = float(os.getenv("PCP_SOURCE_TIMEOUT", "30"))
COMPRASGOV_SOURCE_TIMEOUT: float = float(os.getenv("COMPRASGOV_SOURCE_TIMEOUT", "30"))

# ============================================================================
# CRIT-047: PCP v2 Timeout Resilience
# ============================================================================
# AC4: Max pages to paginate (PCP v2 = 10 items/page, 206 pages for 10-day range).
# Cap at 20 pages (200 items) to avoid 200s+ pagination that triggers source timeout.
PCP_MAX_PAGES_V2: int = int(os.getenv("PCP_MAX_PAGES_V2", "20"))
# AC5: Rate limit delay between PCP requests (seconds). 0.5s = 2 req/s (was 0.2s = 5 req/s).
PCP_RATE_LIMIT_DELAY: float = float(os.getenv("PCP_RATE_LIMIT_DELAY", "0.5"))
# AC4: Per-page slow threshold (seconds). Pages slower than this trigger early-return
# after 3 consecutive slow pages.
PCP_SLOW_PAGE_THRESHOLD_S: float = float(os.getenv("PCP_SLOW_PAGE_THRESHOLD_S", "10.0"))

# STORY-305 AC2/AC6: ComprasGov circuit breaker (rollback: COMPRASGOV_CB_ENABLED=false)
# All 3 HTTP API sources (PNCP, PCP, ComprasGov) share the same CB class and aligned
# thresholds (15 failures / 60s cooldown). If different thresholds are needed in the future,
# document the reason as a comment next to the env var in pncp_client.py.
# Note: SupabaseCircuitBreaker (supabase_client.py) is intentionally SEPARATE —
# databases have different failure semantics than HTTP APIs (sliding window with
# fail-rate percentage is correct for DB; consecutive-failure count for HTTP APIs).
COMPRASGOV_CB_ENABLED: bool = os.getenv("COMPRASGOV_CB_ENABLED", "true").lower() in ("true", "1", "yes")

# ============================================================================
# STORY-294: State Externalization to Redis
# ============================================================================
# TTLs for externalized state stores (seconds)
RESULTS_REDIS_TTL: int = int(os.getenv("RESULTS_REDIS_TTL", "14400"))  # 4 hours — STORY-362 AC2
RESULTS_SUPABASE_TTL_HOURS: int = int(os.getenv("RESULTS_SUPABASE_TTL_HOURS", "24"))  # 24h — STORY-362 AC4
ARBITER_REDIS_TTL: int = int(os.getenv("ARBITER_REDIS_TTL", "3600"))  # 1 hour
STATE_STORE_REDIS_PREFIX: str = os.getenv("STATE_STORE_REDIS_PREFIX", "smartlic:")

# ============================================================================
# STORY-278: Daily Digest Configuration
# ============================================================================

DIGEST_ENABLED: bool = str_to_bool(os.getenv("DIGEST_ENABLED", "false"))
DIGEST_HOUR_UTC: int = int(os.getenv("DIGEST_HOUR_UTC", "10"))  # 10:00 UTC = 7:00 BRT
DIGEST_MAX_PER_EMAIL: int = int(os.getenv("DIGEST_MAX_PER_EMAIL", "10"))
DIGEST_BATCH_SIZE: int = 100  # Resend API limit per batch call

# ============================================================================
# STORY-301: Email Alert System Configuration
# ============================================================================

ALERTS_ENABLED: bool = str_to_bool(os.getenv("ALERTS_ENABLED", "true"))
ALERTS_HOUR_UTC: int = int(os.getenv("ALERTS_HOUR_UTC", "11"))  # 11:00 UTC = 8:00 BRT
ALERTS_MAX_PER_EMAIL: int = int(os.getenv("ALERTS_MAX_PER_EMAIL", "10"))

# ============================================================================
# STORY-314: Stripe ⇄ DB Reconciliation
# ============================================================================
RECONCILIATION_ENABLED: bool = str_to_bool(os.getenv("RECONCILIATION_ENABLED", "true"))
RECONCILIATION_HOUR_UTC: int = int(os.getenv("RECONCILIATION_HOUR_UTC", "6"))  # 06:00 UTC = 03:00 BRT

# ============================================================================
# STORY-316: Health Canary + Status Page
# ============================================================================
HEALTH_CANARY_ENABLED: bool = str_to_bool(os.getenv("HEALTH_CANARY_ENABLED", "true"))
HEALTH_CANARY_INTERVAL_SECONDS: int = int(os.getenv("HEALTH_CANARY_INTERVAL_SECONDS", "300"))  # 5 minutes
HEALTH_CHECKS_RETENTION_DAYS: int = int(os.getenv("HEALTH_CHECKS_RETENTION_DAYS", "30"))

# CRIT-052: Per-search PNCP canary adaptive timeout
PNCP_CANARY_TIMEOUT_S: float = float(os.getenv("PNCP_CANARY_TIMEOUT_S", "10"))
PNCP_CANARY_TIMEOUT_EXTENDED_S: float = float(os.getenv("PNCP_CANARY_TIMEOUT_EXTENDED_S", "15"))

# ============================================================================
# SHIP-002: Feature gates for incomplete features (organizations, messages, alerts, partners)
# All False by default — these features have no frontend and generate Sentry noise.
# Set env var to "true" to re-enable when ready for users.
# ============================================================================
ORGANIZATIONS_ENABLED: bool = str_to_bool(os.getenv("ORGANIZATIONS_ENABLED", "false"))
MESSAGES_ENABLED: bool = str_to_bool(os.getenv("MESSAGES_ENABLED", "false"))
ALERTS_SYSTEM_ENABLED: bool = str_to_bool(os.getenv("ALERTS_SYSTEM_ENABLED", "false"))
PARTNERS_ENABLED: bool = str_to_bool(os.getenv("PARTNERS_ENABLED", "false"))

# ============================================================================
# STORY-353: Support SLA Business Hours
# ============================================================================
BUSINESS_HOURS_START: int = int(os.getenv("BUSINESS_HOURS_START", "8"))   # 08:00 BRT
BUSINESS_HOURS_END: int = int(os.getenv("BUSINESS_HOURS_END", "18"))     # 18:00 BRT
SUPPORT_SLA_CHECK_INTERVAL_SECONDS: int = 4 * 60 * 60  # every 4 hours
SUPPORT_SLA_ALERT_THRESHOLD_HOURS: int = 20  # alert after 20 business hours
