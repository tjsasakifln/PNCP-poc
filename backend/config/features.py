"""Feature flags, LLM, trial, viability, inspection, and classification config."""

import logging
import os

from config.base import str_to_bool

logger = logging.getLogger("config")

# Feature Flag: New Pricing Model (STORY-165)
ENABLE_NEW_PRICING: bool = str_to_bool(os.getenv("ENABLE_NEW_PRICING", "true"))

# ============================================
# LLM Arbiter Configuration (STORY-179 AC6)
# ============================================
LLM_ARBITER_ENABLED: bool = str_to_bool(os.getenv("LLM_ARBITER_ENABLED", "true"))
LLM_ARBITER_MODEL: str = os.getenv("LLM_ARBITER_MODEL", "gpt-4.1-nano")
LLM_ARBITER_MAX_TOKENS: int = int(os.getenv("LLM_ARBITER_MAX_TOKENS", "1"))
LLM_ARBITER_TEMPERATURE: float = float(os.getenv("LLM_ARBITER_TEMPERATURE", "0"))

# Term density thresholds (STORY-248 reviewed 2026-02-14 — kept unchanged)
TERM_DENSITY_HIGH_THRESHOLD: float = float(os.getenv("TERM_DENSITY_HIGH_THRESHOLD", "0.05"))
TERM_DENSITY_MEDIUM_THRESHOLD: float = float(os.getenv("TERM_DENSITY_MEDIUM_THRESHOLD", "0.02"))
TERM_DENSITY_LOW_THRESHOLD: float = float(os.getenv("TERM_DENSITY_LOW_THRESHOLD", "0.01"))

# Filter Debugging & QA
FILTER_DEBUG_MODE: bool = str_to_bool(os.getenv("FILTER_DEBUG_MODE", "false"))
FILTER_DEBUG_SAMPLE: int = int(os.getenv("FILTER_DEBUG_SAMPLE", "0"))
QA_AUDIT_SAMPLE_RATE: float = float(os.getenv("QA_AUDIT_SAMPLE_RATE", "0.10"))

# Zero-results relaxation
ZERO_RESULTS_RELAXATION_ENABLED: bool = str_to_bool(os.getenv("ZERO_RESULTS_RELAXATION_ENABLED", "true"))

# LLM Zero Match
LLM_ZERO_MATCH_ENABLED: bool = str_to_bool(os.getenv("LLM_ZERO_MATCH_ENABLED", "true"))
LLM_ZERO_MATCH_BATCH_SIZE: int = int(os.getenv("LLM_ZERO_MATCH_BATCH_SIZE", "20"))
LLM_ZERO_MATCH_BATCH_TIMEOUT: float = float(os.getenv("LLM_ZERO_MATCH_BATCH_TIMEOUT", "5.0"))
FILTER_ZERO_MATCH_BUDGET_S: float = float(os.getenv("FILTER_ZERO_MATCH_BUDGET_S", "30"))
MAX_ZERO_MATCH_ITEMS: int = int(os.getenv("MAX_ZERO_MATCH_ITEMS", "200"))
ZERO_MATCH_VALUE_RATIO: float = float(os.getenv("ZERO_MATCH_VALUE_RATIO", "0.7"))
ASYNC_ZERO_MATCH_ENABLED: bool = str_to_bool(os.getenv("ASYNC_ZERO_MATCH_ENABLED", "false"))
ZERO_MATCH_JOB_TIMEOUT_S: int = int(os.getenv("ZERO_MATCH_JOB_TIMEOUT_S", "120"))
LLM_FALLBACK_PENDING_ENABLED: bool = str_to_bool(os.getenv("LLM_FALLBACK_PENDING_ENABLED", "true"))
PARTIAL_DATA_SSE_ENABLED: bool = str_to_bool(os.getenv("PARTIAL_DATA_SSE_ENABLED", "true"))
PENDING_REVIEW_TTL_SECONDS: int = int(os.getenv("PENDING_REVIEW_TTL_SECONDS", "86400"))
PENDING_REVIEW_MAX_RETRIES: int = int(os.getenv("PENDING_REVIEW_MAX_RETRIES", "3"))
PENDING_REVIEW_RETRY_DELAY: int = int(os.getenv("PENDING_REVIEW_RETRY_DELAY", "300"))

# D-01: Item Inspection (Gray Zone)
ITEM_INSPECTION_ENABLED: bool = str_to_bool(os.getenv("ITEM_INSPECTION_ENABLED", "true"))
_MAX_ITEM_RAW = int(os.getenv("MAX_ITEM_INSPECTIONS", "20"))
MAX_ITEM_INSPECTIONS: int = max(5, _MAX_ITEM_RAW)
ITEM_INSPECTION_TIMEOUT: float = float(os.getenv("ITEM_INSPECTION_TIMEOUT", "5"))
ITEM_INSPECTION_PHASE_TIMEOUT: float = float(os.getenv("ITEM_INSPECTION_PHASE_TIMEOUT", "15"))
ITEM_INSPECTION_CONCURRENCY: int = int(os.getenv("ITEM_INSPECTION_CONCURRENCY", "5"))

# STORY-264: Trial Duration
TRIAL_DURATION_DAYS: int = int(os.getenv("TRIAL_DURATION_DAYS", "14"))
TRIAL_EMAILS_ENABLED: bool = str_to_bool(os.getenv("TRIAL_EMAILS_ENABLED", "true"))
TRIAL_PAYWALL_ENABLED: bool = str_to_bool(os.getenv("TRIAL_PAYWALL_ENABLED", "true"))
TRIAL_PAYWALL_DAY: int = int(os.getenv("TRIAL_PAYWALL_DAY", "7"))
TRIAL_PAYWALL_MAX_RESULTS: int = int(os.getenv("TRIAL_PAYWALL_MAX_RESULTS", "10"))
TRIAL_PAYWALL_MAX_PIPELINE: int = int(os.getenv("TRIAL_PAYWALL_MAX_PIPELINE", "5"))

# DEBT-325: USD to BRL exchange rate for LLM cost estimation
USD_TO_BRL_RATE: float = float(os.getenv("USD_TO_BRL_RATE", "5.0"))

# D-04: Viability Assessment
VIABILITY_WEIGHT_MODALITY: float = float(os.getenv("VIABILITY_WEIGHT_MODALITY", "0.30"))
VIABILITY_WEIGHT_TIMELINE: float = float(os.getenv("VIABILITY_WEIGHT_TIMELINE", "0.25"))
VIABILITY_WEIGHT_VALUE_FIT: float = float(os.getenv("VIABILITY_WEIGHT_VALUE_FIT", "0.25"))
VIABILITY_WEIGHT_GEOGRAPHY: float = float(os.getenv("VIABILITY_WEIGHT_GEOGRAPHY", "0.20"))

# E-03: Prometheus Metrics
METRICS_ENABLED: bool = str_to_bool(os.getenv("METRICS_ENABLED", "true"))
METRICS_TOKEN: str = os.getenv("METRICS_TOKEN", "")

# D-05: User Feedback Loop
USER_FEEDBACK_ENABLED: bool = str_to_bool(os.getenv("USER_FEEDBACK_ENABLED", "true"))
USER_FEEDBACK_RATE_LIMIT: int = int(os.getenv("USER_FEEDBACK_RATE_LIMIT", "50"))

# SECTOR-PROX: Proximity Context
PROXIMITY_CONTEXT_ENABLED: bool = str_to_bool(os.getenv("PROXIMITY_CONTEXT_ENABLED", "true"))
PROXIMITY_WINDOW_SIZE: int = int(os.getenv("PROXIMITY_WINDOW_SIZE", "8"))

# STORY-259: Bid Analysis
DEEP_ANALYSIS_RATE_LIMIT: int = int(os.getenv("DEEP_ANALYSIS_RATE_LIMIT", "20"))
BID_ANALYSIS_ENABLED: bool = str_to_bool(os.getenv("BID_ANALYSIS_ENABLED", "true"))

# STORY-260: Certifications Catalog
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

# STORY-267: Term Search Quality Parity
TERM_SEARCH_LLM_AWARE: bool = str_to_bool(os.getenv("TERM_SEARCH_LLM_AWARE", "false"))
TERM_SEARCH_SYNONYMS: bool = str_to_bool(os.getenv("TERM_SEARCH_SYNONYMS", "false"))
TERM_SEARCH_VIABILITY_GENERIC: bool = str_to_bool(os.getenv("TERM_SEARCH_VIABILITY_GENERIC", "false"))
TERM_SEARCH_FILTER_CONTEXT: bool = str_to_bool(os.getenv("TERM_SEARCH_FILTER_CONTEXT", "false"))
TERM_SEARCH_VALUE_RANGE_MIN: float = float(os.getenv("TERM_SEARCH_VALUE_RANGE_MIN", "10000"))
TERM_SEARCH_VALUE_RANGE_MAX: float = float(os.getenv("TERM_SEARCH_VALUE_RANGE_MAX", "50000000"))


# ============================================
# Runtime-Reloadable Feature Flags (STORY-226 AC16)
# ============================================
_feature_flag_cache: dict[str, tuple[bool, float]] = {}
_FEATURE_FLAG_TTL: float = 60.0

_FEATURE_FLAG_REGISTRY: dict[str, tuple[str, str]] = {
    "ENABLE_NEW_PRICING": ("ENABLE_NEW_PRICING", "true"),
    "LLM_ARBITER_ENABLED": ("LLM_ARBITER_ENABLED", "true"),
    "ZERO_RESULTS_RELAXATION_ENABLED": ("ZERO_RESULTS_RELAXATION_ENABLED", "true"),
    "LLM_ZERO_MATCH_ENABLED": ("LLM_ZERO_MATCH_ENABLED", "true"),
    "ASYNC_ZERO_MATCH_ENABLED": ("ASYNC_ZERO_MATCH_ENABLED", "false"),
    "CO_OCCURRENCE_RULES_ENABLED": ("CO_OCCURRENCE_RULES_ENABLED", "true"),
    "FILTER_DEBUG_MODE": ("FILTER_DEBUG_MODE", "false"),
    "ITEM_INSPECTION_ENABLED": ("ITEM_INSPECTION_ENABLED", "true"),
    "USER_FEEDBACK_ENABLED": ("USER_FEEDBACK_ENABLED", "true"),
    "PROXIMITY_CONTEXT_ENABLED": ("PROXIMITY_CONTEXT_ENABLED", "true"),
    "RATE_LIMITING_ENABLED": ("RATE_LIMITING_ENABLED", "true"),
    "SECTOR_RED_FLAGS_ENABLED": ("SECTOR_RED_FLAGS_ENABLED", "true"),
    "TRIAL_EMAILS_ENABLED": ("TRIAL_EMAILS_ENABLED", "true"),
    "TRIAL_PAYWALL_ENABLED": ("TRIAL_PAYWALL_ENABLED", "true"),
    "CACHE_REFRESH_ENABLED": ("CACHE_REFRESH_ENABLED", "true"),
    "SEARCH_ASYNC_ENABLED": ("SEARCH_ASYNC_ENABLED", "false"),
    "BID_ANALYSIS_ENABLED": ("BID_ANALYSIS_ENABLED", "true"),
    "TERM_SEARCH_LLM_AWARE": ("TERM_SEARCH_LLM_AWARE", "false"),
    "TERM_SEARCH_SYNONYMS": ("TERM_SEARCH_SYNONYMS", "false"),
    "TERM_SEARCH_VIABILITY_GENERIC": ("TERM_SEARCH_VIABILITY_GENERIC", "false"),
    "TERM_SEARCH_FILTER_CONTEXT": ("TERM_SEARCH_FILTER_CONTEXT", "false"),
    "CACHE_WARMING_ENABLED": ("CACHE_WARMING_ENABLED", "false"),
    "CACHE_LEGACY_KEY_FALLBACK": ("CACHE_LEGACY_KEY_FALLBACK", "true"),
    "SHOW_CACHE_FALLBACK_BANNER": ("SHOW_CACHE_FALLBACK_BANNER", "true"),
    "HEALTH_CANARY_ENABLED": ("HEALTH_CANARY_ENABLED", "true"),
    "PCP_V2_ENABLED": ("PCP_ENABLED", "true"),
    "LLM_FALLBACK_PENDING_ENABLED": ("LLM_FALLBACK_PENDING_ENABLED", "true"),
    "PARTIAL_DATA_SSE_ENABLED": ("PARTIAL_DATA_SSE_ENABLED", "true"),
    "COMPRASGOV_ENABLED": ("COMPRASGOV_ENABLED", "false"),
}


def get_feature_flag(name: str, default: bool | None = None) -> bool:
    """Get a feature flag value with TTL-based caching (60s)."""
    import time as _time

    now = _time.time()

    if name in _feature_flag_cache:
        cached_value, cached_at = _feature_flag_cache[name]
        if (now - cached_at) < _FEATURE_FLAG_TTL:
            return cached_value

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
    """Clear the feature flag cache, forcing re-read from environment."""
    _feature_flag_cache.clear()
    logger.info("Feature flag cache cleared — flags will be re-read from environment")
    current_values: dict[str, bool] = {}
    for name in _FEATURE_FLAG_REGISTRY:
        current_values[name] = get_feature_flag(name)
    return current_values


def log_feature_flags() -> None:
    """Log feature flag states. Call AFTER setup_logging()."""
    from config.pncp import COMPRASGOV_ENABLED as _cg_enabled

    logger.info(f"Feature Flag - ENABLE_NEW_PRICING: {ENABLE_NEW_PRICING}")
    logger.info(f"Feature Flag - LLM_ARBITER_ENABLED: {LLM_ARBITER_ENABLED}")
    logger.info(f"Feature Flag - ZERO_RESULTS_RELAXATION_ENABLED: {ZERO_RESULTS_RELAXATION_ENABLED}")
    if not _cg_enabled:
        logger.warning(
            "ComprasGov v3 source is DISABLED (COMPRASGOV_ENABLED=false). "
            "Set COMPRASGOV_ENABLED=true to re-enable when API is back online."
        )
