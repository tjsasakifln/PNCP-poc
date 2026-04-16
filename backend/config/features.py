"""Feature flags, LLM, trial, viability, inspection, and classification config."""

import logging
import os

from config.base import str_to_bool

logger = logging.getLogger("config")

# Feature Flag: New Pricing Model (STORY-165)
ENABLE_NEW_PRICING: bool = str_to_bool(os.getenv("ENABLE_NEW_PRICING", "true"))

# STORY-414: Schema Contract Gate (Rollout faseado 14d)
# Default False in production (passive / log-only) so we do not block
# startup on transient PGRST002 errors; set to True on staging first
# and flip production only after a 7-14 day observation window. When
# True, a contract violation raises SystemExit at lifespan boot time.
SCHEMA_CONTRACT_STRICT: bool = str_to_bool(os.getenv("SCHEMA_CONTRACT_STRICT", "false"))

# ============================================
# LLM Arbiter Configuration (STORY-179 AC6)
# ============================================
LLM_ARBITER_ENABLED: bool = str_to_bool(os.getenv("LLM_ARBITER_ENABLED", "true"))
LLM_ARBITER_MODEL: str = os.getenv("LLM_ARBITER_MODEL", "gpt-4.1-nano")
LLM_ARBITER_MAX_TOKENS: int = int(os.getenv("LLM_ARBITER_MAX_TOKENS", "1"))
LLM_ARBITER_TEMPERATURE: float = float(os.getenv("LLM_ARBITER_TEMPERATURE", "0"))

# DEBT-SYS-008: Centralized LLM timeout (was hardcoded in llm_arbiter.py)
# GPT-4.1-nano p99 ≈ 1s; 5s = 5× p99. Prevents thread starvation on LLM hangs.
# Accepts OPENAI_TIMEOUT_S (preferred) or LLM_TIMEOUT_S (legacy alias).
LLM_TIMEOUT_S: float = float(os.getenv("OPENAI_TIMEOUT_S", os.getenv("LLM_TIMEOUT_S", "5")))

# DEBT-SYS-008: Per-future timeout for ThreadPoolExecutor LLM calls (filter/llm.py).
# Used by zero_match_batch, zero_match_individual, and arbiter phases.
# 20s = 4× p99 batch latency. Prevents thread starvation on LLM hangs.
LLM_FUTURE_TIMEOUT_S: float = float(os.getenv("LLM_FUTURE_TIMEOUT_S", "20"))

# STORY-4.1 (TD-SYS-014): Async runtime + Batch API.
# LLM_MAX_CONCURRENT caps the number of LLM calls in flight at any given
# time (previously hardcoded to ThreadPoolExecutor(max_workers=10)).
LLM_MAX_CONCURRENT: int = int(os.getenv("LLM_MAX_CONCURRENT", "50"))
# Offline Batch API gate — 24h SLA so not viable for /buscar, only for
# reclassify_pending_bids_job. Set to false to revert to live classification.
LLM_BATCH_ENABLED: bool = str_to_bool(os.getenv("LLM_BATCH_ENABLED", "false"))
LLM_BATCH_MIN_ITEMS: int = int(os.getenv("LLM_BATCH_MIN_ITEMS", "20"))
LLM_BATCH_POLL_INTERVAL_S: int = int(os.getenv("LLM_BATCH_POLL_INTERVAL_S", "60"))

# STORY-5.3 (TD-SYS-013): Session dedup fuzzy configuration.
# DEDUP_FUZZY_ENABLED can disable the fuzzy/process/title-prefix layers without code change.
# DEDUP_FUZZY_THRESHOLD is the Jaccard similarity floor for same-cnpj fuzzy dedup
# (layer _deduplicate_fuzzy). Conservative default 0.85 avoids false-positive hides of
# legitimate parallel bids. Lower = more aggressive dedup; higher = safer.
DEDUP_FUZZY_ENABLED: bool = str_to_bool(os.getenv("DEDUP_FUZZY_ENABLED", "true"))
DEDUP_FUZZY_THRESHOLD: float = float(os.getenv("DEDUP_FUZZY_THRESHOLD", "0.85"))

# Term density thresholds (STORY-248 reviewed 2026-02-14 — kept unchanged)
TERM_DENSITY_HIGH_THRESHOLD: float = float(os.getenv("TERM_DENSITY_HIGH_THRESHOLD", "0.05"))
TERM_DENSITY_MEDIUM_THRESHOLD: float = float(os.getenv("TERM_DENSITY_MEDIUM_THRESHOLD", "0.02"))
TERM_DENSITY_LOW_THRESHOLD: float = float(os.getenv("TERM_DENSITY_LOW_THRESHOLD", "0.01"))

# Filter QA
QA_AUDIT_SAMPLE_RATE: float = float(os.getenv("QA_AUDIT_SAMPLE_RATE", "0.10"))

# Zero-results relaxation
ZERO_RESULTS_RELAXATION_ENABLED: bool = str_to_bool(os.getenv("ZERO_RESULTS_RELAXATION_ENABLED", "true"))

# LLM Zero Match
LLM_ZERO_MATCH_ENABLED: bool = str_to_bool(os.getenv("LLM_ZERO_MATCH_ENABLED", "true"))
LLM_ZERO_MATCH_BATCH_SIZE: int = int(os.getenv("LLM_ZERO_MATCH_BATCH_SIZE", "20"))
LLM_ZERO_MATCH_BATCH_TIMEOUT: float = float(os.getenv("LLM_ZERO_MATCH_BATCH_TIMEOUT", "5.0"))
FILTER_ZERO_MATCH_BUDGET_S: float = float(os.getenv("FILTER_ZERO_MATCH_BUDGET_S", "30"))
MAX_ZERO_MATCH_ITEMS: int = int(os.getenv("MAX_ZERO_MATCH_ITEMS", "200"))
ZERO_MATCH_VALUE_RATIO: float = float(os.getenv("ZERO_MATCH_VALUE_RATIO", "1.0"))
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

# SEO-PLAYBOOK §7.4 — Day-8 referral invitation email (opt-in, additive to
# the existing trial sequence). Default False to avoid disturbing production
# deliverability until validated end-to-end in staging.
REFERRAL_EMAIL_ENABLED: bool = str_to_bool(os.getenv("REFERRAL_EMAIL_ENABLED", "false"))

# SEO-PLAYBOOK §Day-3 Activation — conditional nudge for trial users that
# have not yet completed their first search (the "aha moment" predictor).
# Default False — flip on once the `first_analysis_viewed` signal is wired.
DAY3_ACTIVATION_EMAIL_ENABLED: bool = str_to_bool(os.getenv("DAY3_ACTIVATION_EMAIL_ENABLED", "true"))

# SEO-PLAYBOOK §7.1 / P6 — Day-3 share activation email. Triggered when a
# user has analyzed editais (opportunities_found > 0) but has NOT shared any
# analysis yet. Completes the viral loop: analyst analyzes → shares with
# decision maker → decision maker converts. Default False until validated.
SHARE_ACTIVATION_EMAIL_ENABLED: bool = str_to_bool(os.getenv("SHARE_ACTIVATION_EMAIL_ENABLED", "false"))

# Zero-Churn P1 Frente 2B — Feature discovery emails (pipeline, excel, AI).
# 3 new emails on days 2, 5, 8 highlighting specific features.
FEATURE_DISCOVERY_EMAILS_ENABLED: bool = str_to_bool(os.getenv("FEATURE_DISCOVERY_EMAILS_ENABLED", "true"))

# Zero-Churn P2 §2.2: Grace period data retention
DATA_RETENTION_DAYS: int = int(os.getenv("DATA_RETENTION_DAYS", "30"))
GRACE_DOWNLOAD_ENABLED: bool = str_to_bool(os.getenv("GRACE_DOWNLOAD_ENABLED", "true"))

# Zero-Churn P2 §8.2: Trial Extension as retention mechanism
TRIAL_EXTENSION_ENABLED: bool = str_to_bool(os.getenv("TRIAL_EXTENSION_ENABLED", "true"))
TRIAL_EXTENSION_MAX_DAYS: int = int(os.getenv("TRIAL_EXTENSION_MAX_DAYS", "7"))
TRIAL_EXTENSION_PROFILE_DAYS: int = 3
TRIAL_EXTENSION_FEEDBACK_DAYS: int = 2
TRIAL_EXTENSION_REFERRAL_DAYS: int = 7

# DEBT-325: USD to BRL exchange rate for LLM cost estimation
USD_TO_BRL_RATE: float = float(os.getenv("USD_TO_BRL_RATE", "5.0"))

# DEBT-v3-S2 AC4: LLM cost alert threshold in USD per hour (default $1/h)
LLM_COST_ALERT_THRESHOLD: float = float(os.getenv("LLM_COST_ALERT_THRESHOLD", "1.0"))

# D-04: Viability Assessment
VIABILITY_WEIGHT_MODALITY: float = float(os.getenv("VIABILITY_WEIGHT_MODALITY", "0.30"))
VIABILITY_WEIGHT_TIMELINE: float = float(os.getenv("VIABILITY_WEIGHT_TIMELINE", "0.25"))
VIABILITY_WEIGHT_VALUE_FIT: float = float(os.getenv("VIABILITY_WEIGHT_VALUE_FIT", "0.25"))
VIABILITY_WEIGHT_GEOGRAPHY: float = float(os.getenv("VIABILITY_WEIGHT_GEOGRAPHY", "0.20"))

# E-03: Prometheus Metrics
METRICS_ENABLED: bool = str_to_bool(os.getenv("METRICS_ENABLED", "true"))
METRICS_TOKEN: str = os.getenv("METRICS_TOKEN", "").strip()

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
    {"id": "crf", "label": "CRF (Farmácia)", "sectors": ["medicamentos"]},
    {"id": "inmetro", "label": "INMETRO", "sectors": ["vestuario", "materiais_eletricos"]},
    {"id": "iso_9001", "label": "ISO 9001 (Qualidade)", "sectors": ["*"]},
    {"id": "iso_14001", "label": "ISO 14001 (Ambiental)", "sectors": ["*"]},
    {"id": "pgr_pcmso", "label": "PGR/PCMSO (Segurança do Trabalho)", "sectors": ["servicos_prediais", "vigilancia"]},
    {"id": "alvara_sanitario", "label": "Alvará Sanitário", "sectors": ["alimentos", "medicamentos", "insumos_hospitalares"]},
    {"id": "registro_anvisa", "label": "Registro ANVISA", "sectors": ["medicamentos", "equipamentos_medicos", "insumos_hospitalares"]},
    {"id": "habilitacao_antt", "label": "Habilitação ANTT", "sectors": ["transporte_servicos", "frota_veicular"]},
    {"id": "registro_cfq", "label": "Registro CRQ (Química)", "sectors": ["medicamentos", "materiais_hidraulicos"]},
    {"id": "licenca_ambiental", "label": "Licença Ambiental", "sectors": ["engenharia", "engenharia_rodoviaria"]},
    {"id": "crt", "label": "CRT (Técnico)", "sectors": ["informatica", "software_desenvolvimento", "software_licencas"]},
]

# A/B Testing
AB_EXPERIMENTS_ENABLED: bool = str_to_bool(os.getenv("AB_EXPERIMENTS_ENABLED", "false"))
AB_ACTIVE_EXPERIMENTS: str = os.getenv("AB_ACTIVE_EXPERIMENTS", "{}")

# STORY-267: Term Search Quality Parity
TERM_SEARCH_LLM_AWARE: bool = str_to_bool(os.getenv("TERM_SEARCH_LLM_AWARE", "false"))
TERM_SEARCH_SYNONYMS: bool = str_to_bool(os.getenv("TERM_SEARCH_SYNONYMS", "false"))
TERM_SEARCH_VIABILITY_GENERIC: bool = str_to_bool(os.getenv("TERM_SEARCH_VIABILITY_GENERIC", "false"))
TERM_SEARCH_FILTER_CONTEXT: bool = str_to_bool(os.getenv("TERM_SEARCH_FILTER_CONTEXT", "false"))
TERM_SEARCH_VALUE_RANGE_MIN: float = float(os.getenv("TERM_SEARCH_VALUE_RANGE_MIN", "10000"))
TERM_SEARCH_VALUE_RANGE_MAX: float = float(os.getenv("TERM_SEARCH_VALUE_RANGE_MAX", "50000000"))

# STORY-437: Trigram fuzzy fallback when FTS returns 0 results
TRIGRAM_FALLBACK_ENABLED: bool = str_to_bool(os.getenv("TRIGRAM_FALLBACK_ENABLED", "true"))

# STORY-438: Semantic search via pgvector embeddings
EMBEDDING_ENABLED: bool = str_to_bool(os.getenv("EMBEDDING_ENABLED", "false"))
EMBEDDING_THRESHOLD: float = float(os.getenv("EMBEDDING_THRESHOLD", "0.6"))


# ============================================
# Runtime-Reloadable Feature Flags (STORY-226 AC16)
# ============================================
_feature_flag_cache: dict[str, tuple[bool, float]] = {}
_FEATURE_FLAG_TTL: float = 60.0

_FEATURE_FLAG_REGISTRY: dict[str, tuple[str, str]] = {
    # --- LLM & Classification ---
    "ENABLE_NEW_PRICING": ("ENABLE_NEW_PRICING", "true"),
    "LLM_ARBITER_ENABLED": ("LLM_ARBITER_ENABLED", "true"),
    "LLM_ZERO_MATCH_ENABLED": ("LLM_ZERO_MATCH_ENABLED", "true"),
    "ASYNC_ZERO_MATCH_ENABLED": ("ASYNC_ZERO_MATCH_ENABLED", "false"),
    "LLM_FALLBACK_PENDING_ENABLED": ("LLM_FALLBACK_PENDING_ENABLED", "true"),
    "BID_ANALYSIS_ENABLED": ("BID_ANALYSIS_ENABLED", "true"),
    # --- Filter Pipeline ---
    "ZERO_RESULTS_RELAXATION_ENABLED": ("ZERO_RESULTS_RELAXATION_ENABLED", "true"),
    "CO_OCCURRENCE_RULES_ENABLED": ("CO_OCCURRENCE_RULES_ENABLED", "true"),
    "SECTOR_RED_FLAGS_ENABLED": ("SECTOR_RED_FLAGS_ENABLED", "true"),
    "PROXIMITY_CONTEXT_ENABLED": ("PROXIMITY_CONTEXT_ENABLED", "true"),
    "ITEM_INSPECTION_ENABLED": ("ITEM_INSPECTION_ENABLED", "true"),
    # --- Term Search Quality ---
    "TERM_SEARCH_LLM_AWARE": ("TERM_SEARCH_LLM_AWARE", "false"),
    "TERM_SEARCH_SYNONYMS": ("TERM_SEARCH_SYNONYMS", "false"),
    "TERM_SEARCH_VIABILITY_GENERIC": ("TERM_SEARCH_VIABILITY_GENERIC", "false"),
    "TERM_SEARCH_FILTER_CONTEXT": ("TERM_SEARCH_FILTER_CONTEXT", "false"),
    # --- Data Sources ---
    "COMPRASGOV_ENABLED": ("COMPRASGOV_ENABLED", "false"),
    "PCP_V2_ENABLED": ("PCP_ENABLED", "true"),
    "DATALAKE_ENABLED": ("DATALAKE_ENABLED", "true"),
    "DATALAKE_QUERY_ENABLED": ("DATALAKE_QUERY_ENABLED", "true"),
    # --- Cache & Warming ---
    "CACHE_WARMING_ENABLED": ("CACHE_WARMING_ENABLED", "true"),
    "CACHE_REFRESH_ENABLED": ("CACHE_REFRESH_ENABLED", "true"),
    "CACHE_LEGACY_KEY_FALLBACK": ("CACHE_LEGACY_KEY_FALLBACK", "true"),
    "CACHE_WARMING_POST_DEPLOY_ENABLED": ("CACHE_WARMING_POST_DEPLOY_ENABLED", "true"),
    "SHOW_CACHE_FALLBACK_BANNER": ("SHOW_CACHE_FALLBACK_BANNER", "true"),
    "SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE": ("SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE", "true"),
    # --- Search Pipeline ---
    "SEARCH_ASYNC_ENABLED": ("SEARCH_ASYNC_ENABLED", "false"),
    "PARTIAL_DATA_SSE_ENABLED": ("PARTIAL_DATA_SSE_ENABLED", "true"),
    "WARMUP_ENABLED": ("WARMUP_ENABLED", "true"),
    # --- Cron & Operations ---
    "HEALTH_CANARY_ENABLED": ("HEALTH_CANARY_ENABLED", "true"),
    "DIGEST_ENABLED": ("DIGEST_ENABLED", "false"),
    "ALERTS_ENABLED": ("ALERTS_ENABLED", "true"),
    "RECONCILIATION_ENABLED": ("RECONCILIATION_ENABLED", "true"),
    # --- Trial & Billing ---
    "TRIAL_EMAILS_ENABLED": ("TRIAL_EMAILS_ENABLED", "true"),
    "TRIAL_PAYWALL_ENABLED": ("TRIAL_PAYWALL_ENABLED", "true"),
    # --- A/B Testing ---
    "ab_experiments_enabled": ("AB_EXPERIMENTS_ENABLED", "false"),
    # --- Feature Gates (unreleased features) ---
    "ORGANIZATIONS_ENABLED": ("ORGANIZATIONS_ENABLED", "false"),
    "MESSAGES_ENABLED": ("MESSAGES_ENABLED", "true"),
    "ALERTS_SYSTEM_ENABLED": ("ALERTS_SYSTEM_ENABLED", "false"),
    "PARTNERS_ENABLED": ("PARTNERS_ENABLED", "false"),
    # --- Infra ---
    "METRICS_ENABLED": ("METRICS_ENABLED", "true"),
    "RATE_LIMITING_ENABLED": ("RATE_LIMITING_ENABLED", "true"),
    "USER_FEEDBACK_ENABLED": ("USER_FEEDBACK_ENABLED", "true"),
    "USE_REDIS_CIRCUIT_BREAKER": ("USE_REDIS_CIRCUIT_BREAKER", "true"),
    "COMPRASGOV_CB_ENABLED": ("COMPRASGOV_CB_ENABLED", "true"),
    # --- STORY-414: Schema contract gate (faseado 14d, default off in prod) ---
    "SCHEMA_CONTRACT_STRICT": ("SCHEMA_CONTRACT_STRICT", "false"),
    # --- STORY-437: Datalake search improvements ---
    "TRIGRAM_FALLBACK_ENABLED": ("TRIGRAM_FALLBACK_ENABLED", "true"),
    # --- STORY-438: Semantic embeddings ---
    "EMBEDDING_ENABLED": ("EMBEDDING_ENABLED", "false"),
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


def validate_feature_flags() -> None:
    """Validate all feature flag values for correct types and reasonable ranges.

    Reads directly from environment (not module-level cached values) so that
    this function is useful even when called after os.environ has been patched
    in tests.

    On validation failure: logs a CRITICAL error with the specific flag and
    issue, then raises a ValueError so the application does NOT start with
    invalid configuration.

    Call AFTER setup_logging() and log_feature_flags().
    """
    errors: list[str] = []

    def _check_float(env_var: str, default: str, min_val: float | None = None, max_val: float | None = None) -> None:
        raw = os.getenv(env_var, default)
        try:
            value = float(raw)
        except (ValueError, TypeError):
            errors.append(f"{env_var}={raw!r} — expected a float, got non-numeric value")
            return
        if min_val is not None and value < min_val:
            errors.append(f"{env_var}={raw!r} — value {value} is below minimum {min_val}")
        if max_val is not None and value > max_val:
            errors.append(f"{env_var}={raw!r} — value {value} exceeds maximum {max_val}")

    def _check_int(env_var: str, default: str, min_val: int | None = None, max_val: int | None = None) -> None:
        raw = os.getenv(env_var, default)
        try:
            value = int(raw)
        except (ValueError, TypeError):
            errors.append(f"{env_var}={raw!r} — expected an integer, got non-numeric value")
            return
        if min_val is not None and value < min_val:
            errors.append(f"{env_var}={raw!r} — value {value} is below minimum {min_val}")
        if max_val is not None and value > max_val:
            errors.append(f"{env_var}={raw!r} — value {value} exceeds maximum {max_val}")

    # --- LLM Arbiter ---
    _check_float("LLM_ARBITER_TEMPERATURE", "0", min_val=0.0, max_val=2.0)
    _check_int("LLM_ARBITER_MAX_TOKENS", "1", min_val=1, max_val=32768)
    _check_float("OPENAI_TIMEOUT_S", os.getenv("LLM_TIMEOUT_S", "5"), min_val=0.1, max_val=300.0)
    _check_float("LLM_FUTURE_TIMEOUT_S", "20", min_val=1.0, max_val=300.0)

    # --- Term density thresholds ---
    _check_float("TERM_DENSITY_HIGH_THRESHOLD", "0.05", min_val=0.0, max_val=1.0)
    _check_float("TERM_DENSITY_MEDIUM_THRESHOLD", "0.02", min_val=0.0, max_val=1.0)
    _check_float("TERM_DENSITY_LOW_THRESHOLD", "0.01", min_val=0.0, max_val=1.0)

    # --- Filter QA ---
    _check_float("QA_AUDIT_SAMPLE_RATE", "0.10", min_val=0.0, max_val=1.0)

    # --- Zero-match config ---
    _check_int("LLM_ZERO_MATCH_BATCH_SIZE", "20", min_val=1, max_val=500)
    _check_float("LLM_ZERO_MATCH_BATCH_TIMEOUT", "5.0", min_val=0.1, max_val=300.0)
    _check_float("FILTER_ZERO_MATCH_BUDGET_S", "30", min_val=1.0, max_val=300.0)
    _check_int("MAX_ZERO_MATCH_ITEMS", "200", min_val=1, max_val=10000)
    _check_float("ZERO_MATCH_VALUE_RATIO", "1.0", min_val=0.0, max_val=100.0)
    _check_int("ZERO_MATCH_JOB_TIMEOUT_S", "120", min_val=1, max_val=3600)

    # --- Pending review ---
    _check_int("PENDING_REVIEW_TTL_SECONDS", "86400", min_val=1)
    _check_int("PENDING_REVIEW_MAX_RETRIES", "3", min_val=0, max_val=100)
    _check_int("PENDING_REVIEW_RETRY_DELAY", "300", min_val=1)

    # --- Item inspection ---
    _check_int("MAX_ITEM_INSPECTIONS", "20", min_val=1, max_val=1000)
    _check_float("ITEM_INSPECTION_TIMEOUT", "5", min_val=0.1, max_val=300.0)
    _check_float("ITEM_INSPECTION_PHASE_TIMEOUT", "15", min_val=1.0, max_val=300.0)
    _check_int("ITEM_INSPECTION_CONCURRENCY", "5", min_val=1, max_val=100)

    # --- Trial config ---
    _check_int("TRIAL_DURATION_DAYS", "14", min_val=1, max_val=365)
    _check_int("TRIAL_PAYWALL_DAY", "7", min_val=1, max_val=365)
    _check_int("TRIAL_PAYWALL_MAX_RESULTS", "10", min_val=1, max_val=10000)
    _check_int("TRIAL_PAYWALL_MAX_PIPELINE", "15", min_val=1, max_val=10000)

    # --- Currency / cost ---
    _check_float("USD_TO_BRL_RATE", "5.0", min_val=0.01, max_val=1000.0)
    _check_float("LLM_COST_ALERT_THRESHOLD", "1.0", min_val=0.0, max_val=10000.0)

    # --- Viability weights (must each be 0–1 and sum to ~1.0) ---
    _check_float("VIABILITY_WEIGHT_MODALITY", "0.30", min_val=0.0, max_val=1.0)
    _check_float("VIABILITY_WEIGHT_TIMELINE", "0.25", min_val=0.0, max_val=1.0)
    _check_float("VIABILITY_WEIGHT_VALUE_FIT", "0.25", min_val=0.0, max_val=1.0)
    _check_float("VIABILITY_WEIGHT_GEOGRAPHY", "0.20", min_val=0.0, max_val=1.0)

    # Validate viability weights sum (only if all parsed successfully)
    viability_vars = [
        "VIABILITY_WEIGHT_MODALITY",
        "VIABILITY_WEIGHT_TIMELINE",
        "VIABILITY_WEIGHT_VALUE_FIT",
        "VIABILITY_WEIGHT_GEOGRAPHY",
    ]
    viability_defaults = ["0.30", "0.25", "0.25", "0.20"]
    if not any(v.split("=")[0] in e for e in errors for v in viability_vars):
        weight_sum = sum(
            float(os.getenv(var, default))
            for var, default in zip(viability_vars, viability_defaults)
        )
        if abs(weight_sum - 1.0) > 0.01:
            errors.append(
                f"Viability weights sum to {weight_sum:.4f} — must sum to 1.0 "
                f"(VIABILITY_WEIGHT_MODALITY + VIABILITY_WEIGHT_TIMELINE + "
                f"VIABILITY_WEIGHT_VALUE_FIT + VIABILITY_WEIGHT_GEOGRAPHY)"
            )

    # --- Feedback rate limit ---
    _check_int("USER_FEEDBACK_RATE_LIMIT", "50", min_val=1, max_val=100000)

    # --- Proximity window ---
    _check_int("PROXIMITY_WINDOW_SIZE", "8", min_val=1, max_val=1000)

    # --- Deep analysis rate limit ---
    _check_int("DEEP_ANALYSIS_RATE_LIMIT", "20", min_val=1, max_val=100000)

    # --- Term search value range ---
    _check_float("TERM_SEARCH_VALUE_RANGE_MIN", "10000", min_val=0.0)
    _check_float("TERM_SEARCH_VALUE_RANGE_MAX", "50000000", min_val=0.0)

    if errors:
        for error in errors:
            logger.critical("Invalid feature flag configuration: %s", error)
        raise ValueError(
            f"Feature flag validation failed with {len(errors)} error(s):\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    logger.info("Feature flag validation passed — all %d checked flags are valid", _VALIDATED_FLAG_COUNT)


# Number of flags validated by validate_feature_flags() — used in log message above.
# Update this constant whenever a new _check_* call is added.
_VALIDATED_FLAG_COUNT = 34


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
