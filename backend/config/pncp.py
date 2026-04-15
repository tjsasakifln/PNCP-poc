"""PNCP, PCP, ComprasGov source configuration: modalities, retry, timeouts, bulkheads."""

import os
from dataclasses import dataclass, field
from typing import List, Tuple, Type

from config.base import str_to_bool

# DEBT-107: httpx exceptions replace requests.exceptions
import httpx


# PNCP Modality Codes (codigoModalidadeContratacao)
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

DEFAULT_MODALIDADES: List[int] = [4, 5, 6, 7]

MODALIDADES_EXCLUIDAS: List[int] = [9, 14]


@dataclass
class RetryConfig:
    """Configuration for HTTP retry logic.

    STORY-282 AC1: Defaults use PNCP-specific env vars.
    """
    max_retries: int = int(os.getenv("PNCP_MAX_RETRIES", "1"))
    base_delay: float = 1.5
    max_delay: float = 15.0
    exponential_base: int = 2
    jitter: bool = True
    timeout: int = int(os.getenv("PNCP_READ_TIMEOUT", "15"))
    connect_timeout: float = float(os.getenv("PNCP_CONNECT_TIMEOUT", "10"))
    read_timeout: float = float(os.getenv("PNCP_READ_TIMEOUT", "15"))

    retryable_status_codes: Tuple[int, ...] = field(
        default_factory=lambda: (408, 422, 429, 500, 502, 503, 504)
    )

    # DEBT-107: httpx exceptions replace requests.exceptions (CRIT-038 original note preserved)
    retryable_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=lambda: (
            ConnectionError,
            TimeoutError,
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadError,
        )
    )


# STORY-282: PNCP Timeout Resilience
PNCP_CONNECT_TIMEOUT: float = float(os.getenv("PNCP_CONNECT_TIMEOUT", "10"))
PNCP_READ_TIMEOUT: float = float(os.getenv("PNCP_READ_TIMEOUT", "15"))
PNCP_MAX_RETRIES: int = int(os.getenv("PNCP_MAX_RETRIES", "1"))
PNCP_MAX_PAGES: int = int(os.getenv("PNCP_MAX_PAGES", "20"))
# DEBT-102 AC6: PNCP API max page size (reduced from 500 to 50 by PNCP ~Feb 2026)
PNCP_MAX_PAGE_SIZE: int = 50
CACHE_FIRST_FRESH_TIMEOUT: int = int(os.getenv("CACHE_FIRST_FRESH_TIMEOUT", "60"))

# CRIT-052: Per-search PNCP canary adaptive timeout
PNCP_CANARY_TIMEOUT_S: float = float(os.getenv("PNCP_CANARY_TIMEOUT_S", "10"))
PNCP_CANARY_TIMEOUT_EXTENDED_S: float = float(os.getenv("PNCP_CANARY_TIMEOUT_EXTENDED_S", "15"))

# STORY-4.5 (TD-SYS-002): Breaking-change canary run cadence and escalation threshold.
# Set PNCP_CANARY_INTERVAL_S=0 to disable the background cron.
PNCP_CANARY_INTERVAL_S: int = int(os.getenv("PNCP_CANARY_INTERVAL_S", "600"))
PNCP_CANARY_FAIL_THRESHOLD: int = int(os.getenv("PNCP_CANARY_FAIL_THRESHOLD", "3"))

# STORY-296: Bulkhead Per Source
PNCP_BULKHEAD_CONCURRENCY: int = int(os.getenv("PNCP_BULKHEAD_CONCURRENCY", "5"))
PCP_BULKHEAD_CONCURRENCY: int = int(os.getenv("PCP_BULKHEAD_CONCURRENCY", "3"))
COMPRASGOV_BULKHEAD_CONCURRENCY: int = int(os.getenv("COMPRASGOV_BULKHEAD_CONCURRENCY", "3"))
PNCP_SOURCE_TIMEOUT: float = float(os.getenv("PNCP_SOURCE_TIMEOUT", "80"))
PCP_SOURCE_TIMEOUT: float = float(os.getenv("PCP_SOURCE_TIMEOUT", "30"))
COMPRASGOV_SOURCE_TIMEOUT: float = float(os.getenv("COMPRASGOV_SOURCE_TIMEOUT", "30"))

# CRIT-047: PCP v2 Timeout Resilience
PCP_MAX_PAGES_V2: int = int(os.getenv("PCP_MAX_PAGES_V2", "20"))
PCP_RATE_LIMIT_DELAY: float = float(os.getenv("PCP_RATE_LIMIT_DELAY", "0.5"))
PCP_SLOW_PAGE_THRESHOLD_S: float = float(os.getenv("PCP_SLOW_PAGE_THRESHOLD_S", "10.0"))

# STORY-305: ComprasGov circuit breaker
COMPRASGOV_CB_ENABLED: bool = os.getenv("COMPRASGOV_CB_ENABLED", "true").lower() in ("true", "1", "yes")

# HARDEN-010: ComprasGov v3 master flag (API down since 2026-03-03)
# W1-PR2: ComprasGov v3 has been offline since 2026-03-03 (confirmed via Playwright).
# Default is "false". Re-enable only after verifying https://dadosabertos.compras.gov.br is live.
COMPRASGOV_ENABLED: bool = str_to_bool(os.getenv("COMPRASGOV_ENABLED", "false"))

# GTM-STAB-003: Timeout Chain
PIPELINE_TIMEOUT: int = int(os.getenv("PIPELINE_TIMEOUT", "110"))
CONSOLIDATION_TIMEOUT: int = int(os.getenv("CONSOLIDATION_TIMEOUT", "100"))
PNCP_TIMEOUT_PER_SOURCE: int = int(os.getenv("PNCP_TIMEOUT_PER_SOURCE", "80"))
# Per-UF timeout (GTM-FIX-029 AC1/AC5) — configurable
# Calculation: 4 modalities × ~15s/mod (with retry) = ~60s + 30s margin = 90s
PNCP_TIMEOUT_PER_UF: int = int(os.getenv("PNCP_TIMEOUT_PER_UF", "30"))
PNCP_TIMEOUT_PER_UF_DEGRADED: int = int(os.getenv("PNCP_TIMEOUT_PER_UF_DEGRADED", "15"))
PIPELINE_SKIP_LLM_AFTER_S: int = int(os.getenv("PIPELINE_SKIP_LLM_AFTER_S", "90"))
PIPELINE_SKIP_VIABILITY_AFTER_S: int = int(os.getenv("PIPELINE_SKIP_VIABILITY_AFTER_S", "100"))

# GTM-STAB-003 AC3: Consolidation early return
# ISSUE-054: Lowered from 0.8 to 0.66 so 3-UF queries can early-return with 2/3 completed
EARLY_RETURN_THRESHOLD_PCT: float = float(os.getenv("EARLY_RETURN_THRESHOLD_PCT", "0.66"))
EARLY_RETURN_TIME_S: float = float(os.getenv("EARLY_RETURN_TIME_S", "80.0"))

# ============================================================================
# DEBT-118: Circuit breaker & batching config (moved from pncp_client.py)
# ============================================================================

# Configurable via environment variables (GTM-FIX-005)
PNCP_CIRCUIT_BREAKER_THRESHOLD: int = int(
    # GTM-INFRA-001 AC4: Reduced from 50 to 15 — trips in ~30s instead of ~3min
    os.getenv("PNCP_CIRCUIT_BREAKER_THRESHOLD", "15")
)
PNCP_CIRCUIT_BREAKER_COOLDOWN: int = int(
    # GTM-INFRA-001 AC5: Reduced proportionally from 120s to 60s
    os.getenv("PNCP_CIRCUIT_BREAKER_COOLDOWN", "60")
)
PCP_CIRCUIT_BREAKER_THRESHOLD: int = int(
    # STORY-305 AC5: Aligned with PNCP — same class of government API, no justification for 2x tolerance
    os.getenv("PCP_CIRCUIT_BREAKER_THRESHOLD", "15")
)
PCP_CIRCUIT_BREAKER_COOLDOWN: int = int(
    # STORY-305 AC5: Aligned with PNCP (was 120s)
    os.getenv("PCP_CIRCUIT_BREAKER_COOLDOWN", "60")
)

# STORY-305 AC2: ComprasGov circuit breaker — same class of government API
COMPRASGOV_CIRCUIT_BREAKER_THRESHOLD: int = int(
    os.getenv("COMPRASGOV_CIRCUIT_BREAKER_THRESHOLD", "15")
)
COMPRASGOV_CIRCUIT_BREAKER_COOLDOWN: int = int(
    os.getenv("COMPRASGOV_CIRCUIT_BREAKER_COOLDOWN", "60")
)

# Per-modality timeout (STORY-252 AC6, GTM-RESILIENCE-F03 AC1) — configurable
# PerModality=20s: GTM-STAB — tighter budget per modality under new PerUF=30s.
# Hierarchy: PerModality(20s) < PerUF(30s) — margin 10s.
PNCP_TIMEOUT_PER_MODALITY: float = float(
    os.getenv("PNCP_TIMEOUT_PER_MODALITY", "20")
)

# Modality retry on timeout (STORY-252 AC9)
PNCP_MODALITY_RETRY_BACKOFF: float = float(
    os.getenv("PNCP_MODALITY_RETRY_BACKOFF", "3.0")
)

# GTM-FIX-031: Phased UF batching — reduces PNCP API pressure
PNCP_BATCH_SIZE: int = int(os.getenv("PNCP_BATCH_SIZE", "5"))
PNCP_BATCH_DELAY_S: float = float(os.getenv("PNCP_BATCH_DELAY_S", "2.0"))

# B-06: Redis-backed circuit breaker toggle (rollback: set to "false")
USE_REDIS_CIRCUIT_BREAKER: bool = os.getenv(
    "USE_REDIS_CIRCUIT_BREAKER", "true"
).lower() == "true"
# B-06: Circuit breaker Redis key TTL — auto-expire safety net (AC12)
CB_REDIS_TTL: int = int(os.getenv("CB_REDIS_TTL", "300"))  # 5 minutes
