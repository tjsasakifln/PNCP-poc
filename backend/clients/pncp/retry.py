"""Retry/timeout utilities, dataclasses, and date formatting helpers for PNCP.

Contains:
- validate_timeout_chain() — startup validation of timeout hierarchy
- UFS_BY_POPULATION — UF priority list for degraded mode
- ParallelFetchResult / ModalityFetchState — structured return types
- DateFormat — date format constants + cache helpers
- _validate_date_params / _handle_422_response — 422 handling
- calculate_delay — exponential backoff
- format_date — date string conversion
"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config import (
    RetryConfig,
    PNCP_TIMEOUT_PER_MODALITY as _CFG_TIMEOUT_PER_MODALITY,
    PNCP_TIMEOUT_PER_UF as _CFG_TIMEOUT_PER_UF,
    PNCP_MODALITY_RETRY_BACKOFF,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Startup Timeout Chain Validation (GTM-RESILIENCE-F03 AC7-AC12)
# ============================================================================

_SAFE_PER_MODALITY = 20.0
_SAFE_PER_UF = 30.0

# Mutable module-level vars (validate_timeout_chain may override)
PNCP_TIMEOUT_PER_MODALITY: float = _CFG_TIMEOUT_PER_MODALITY
PNCP_TIMEOUT_PER_UF: float = _CFG_TIMEOUT_PER_UF


def validate_timeout_chain() -> None:
    """Validate timeout hierarchy at startup. Prevents misconfigurations.

    If PerModality >= PerUF, logs critical and forces safe defaults.
    If PerModality > 80% of PerUF, logs warning.
    Never raises — always falls back to safe values on misconfiguration.
    """
    global PNCP_TIMEOUT_PER_MODALITY, PNCP_TIMEOUT_PER_UF

    if PNCP_TIMEOUT_PER_MODALITY >= PNCP_TIMEOUT_PER_UF:
        logger.critical(
            "TIMEOUT MISCONFIGURATION: PerModality(%.0fs) >= PerUF(%.0fs). "
            "Modality timeout must be strictly less than UF timeout. "
            "Falling back to safe defaults: PerModality=%.0fs, PerUF=%.0fs.",
            PNCP_TIMEOUT_PER_MODALITY, PNCP_TIMEOUT_PER_UF,
            _SAFE_PER_MODALITY, _SAFE_PER_UF,
        )
        PNCP_TIMEOUT_PER_MODALITY = _SAFE_PER_MODALITY
        PNCP_TIMEOUT_PER_UF = _SAFE_PER_UF
        return

    threshold_80 = PNCP_TIMEOUT_PER_UF * 0.8
    if PNCP_TIMEOUT_PER_MODALITY > threshold_80:
        recommended = PNCP_TIMEOUT_PER_UF * 0.67
        logger.warning(
            "TIMEOUT NEAR-INVERSION: PerModality(%.0fs) > 80%% of PerUF(%.0fs). "
            "Recommend PerModality <= %.0fs for safe margin.",
            PNCP_TIMEOUT_PER_MODALITY, PNCP_TIMEOUT_PER_UF, recommended,
        )


# UFs ordered by population for degraded priority (STORY-257A AC1)
UFS_BY_POPULATION = ["SP", "RJ", "MG", "BA", "PR", "RS", "PE", "CE", "SC", "GO",
                      "PA", "MA", "AM", "ES", "PB", "RN", "MT", "AL", "PI", "DF",
                      "MS", "SE", "RO", "TO", "AC", "AP", "RR"]


@dataclass
class ParallelFetchResult:
    """Structured return from buscar_todas_ufs_paralelo with per-UF metadata."""
    items: List[Dict[str, Any]]
    succeeded_ufs: List[str]
    failed_ufs: List[str]
    truncated_ufs: List[str] = field(default_factory=list)  # GTM-FIX-004: UFs that hit max_pages limit


@dataclass
class ModalityFetchState:
    """Shared mutable state for partial accumulation during modality fetch.

    Passed into _fetch_single_modality so that items accumulated before a
    timeout cancellation are preserved. Thread-safe in asyncio (single-threaded
    event loop — no locks needed).
    """
    items: List[Dict[str, Any]] = field(default_factory=list)
    seen_ids: set = field(default_factory=set)
    pages_fetched: int = 0
    was_truncated: bool = False
    timed_out: bool = False


# ============================================================================
# UX-336: Multi-format date handling for PNCP 422 recovery
# ============================================================================

class DateFormat:
    """Supported PNCP date formats for 422 retry rotation."""
    YYYYMMDD = "YYYYMMDD"       # 20260218 (only format accepted by PNCP)
    ISO_DASH = "YYYY-MM-DD"     # 2026-02-18 (NOT accepted by PNCP)
    BR_SLASH = "DD/MM/YYYY"     # 18/02/2026 (NOT accepted by PNCP)
    BR_DASH = "DD-MM-YYYY"      # 18-02-2026 (NOT accepted by PNCP)

    # PNCP API only accepts yyyyMMdd. Format rotation to other formats
    # wastes retries and guarantees failure. Confirmed in production
    # 2026-02-25: rotating to ISO_DASH/BR_SLASH/BR_DASH always returns
    # "Data Inicial inválida". Keep only the correct format.
    ALL = [YYYYMMDD]


# UX-336 AC3: In-memory cache of accepted date format (TTL 24h)
_accepted_date_format: Optional[str] = None
_accepted_date_format_ts: float = 0.0
_DATE_FORMAT_CACHE_TTL = 86400.0  # 24 hours


def _get_cached_date_format() -> Optional[str]:
    """Return cached accepted format if still valid, else None."""
    global _accepted_date_format, _accepted_date_format_ts
    if _accepted_date_format and (time.time() - _accepted_date_format_ts) < _DATE_FORMAT_CACHE_TTL:
        return _accepted_date_format
    return None


def _set_cached_date_format(fmt: str) -> None:
    """Cache the accepted date format."""
    global _accepted_date_format, _accepted_date_format_ts
    _accepted_date_format = fmt
    _accepted_date_format_ts = time.time()
    logger.debug(f"pncp_date_format_cached format={fmt}")


def format_date(iso_date: str, fmt: str) -> str:
    """Convert YYYY-MM-DD date string to the specified format.

    Args:
        iso_date: Date in YYYY-MM-DD format
        fmt: Target format from DateFormat constants

    Returns:
        Formatted date string
    """
    parts = iso_date.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid ISO date: '{iso_date}'")
    yyyy, mm, dd = parts

    if fmt == DateFormat.YYYYMMDD:
        return f"{yyyy}{mm}{dd}"
    elif fmt == DateFormat.ISO_DASH:
        return iso_date  # Already in this format
    elif fmt == DateFormat.BR_SLASH:
        return f"{dd}/{mm}/{yyyy}"
    elif fmt == DateFormat.BR_DASH:
        return f"{dd}-{mm}-{yyyy}"
    else:
        raise ValueError(f"Unknown date format: '{fmt}'")


def _get_format_rotation() -> List[str]:
    """Return date formats to try, with cached format first if available."""
    cached = _get_cached_date_format()
    if cached:
        # Put cached format first, then the rest
        return [cached] + [f for f in DateFormat.ALL if f != cached]
    return list(DateFormat.ALL)


def _validate_date_params(
    data_inicial: str, data_inicial_fmt: str,
    data_final: str, data_final_fmt: str,
) -> None:
    """GTM-FIX-032 AC2: Pre-flight date validation before sending to PNCP."""
    if len(data_inicial_fmt) != 8 or not data_inicial_fmt.isdigit():
        raise ValueError(f"Malformed data_inicial: '{data_inicial}' → '{data_inicial_fmt}'")
    if len(data_final_fmt) != 8 or not data_final_fmt.isdigit():
        raise ValueError(f"Malformed data_final: '{data_final}' → '{data_final_fmt}'")


def _handle_422_response(
    response_text: str,
    params: dict,
    data_inicial: str,
    data_final: str,
    attempt: int,
    max_retries: int = 1,
) -> "str | dict":
    """GTM-FIX-032 AC1+AC4+AC6: Shared 422 handling for sync and async clients.

    Returns:
        "retry" — caller should retry (same format)
        "retry_format" — caller should retry with next date format (UX-336)
        dict — empty result (graceful skip for date-related 422s)
        "raise" — caller should raise PNCPAPIError
    """
    body_preview = response_text[:500] if response_text else "(empty)"
    uf_param = params.get("uf", "?")
    mod_param = params.get("codigoModalidadeContratacao", "?")
    pagina = params.get("pagina", 1)

    # UX-336 AC4: Detailed logging of each attempt
    logger.warning(
        f"PNCP 422 for UF={uf_param} mod={mod_param} "
        f"(attempt {attempt + 1}/{max_retries + 1}). Body: {body_preview}. "
        f"Params: {params}. Raw dates: {data_inicial} → {data_final}."
    )

    # UX-336: Always signal format rotation — the outer loop tracks format exhaustion
    if attempt < max_retries:
        return "retry_format"

    # Retry exhausted — categorize (called explicitly when formats are exhausted)
    logger.warning(
        f"PNCP 422 persisted for UF={uf_param} mod={mod_param} "
        f"after {max_retries} retry. Body: {body_preview}. "
        f"Params: {params}. Raw dates: {data_inicial} → {data_final}"
    )

    # AC4.1: NO circuit breaker for 422 (transient validation, not API down)
    # AC4.2: Categorize and handle gracefully
    _422_type = "unknown"
    if "Data Inicial" in body_preview:
        _422_type = "date_swap"
    elif "365 dias" in body_preview:
        _422_type = "date_range"

    # AC4.4 + UX-336 AC5: Sentry-style metric tag with format info
    logger.debug(
        f"pncp_422_count uf={uf_param} modality={mod_param} type={_422_type}"
    )

    if _422_type != "unknown":
        # AC4.3: Return empty instead of crashing
        logger.debug(
            f"pncp_422_date_skip uf={uf_param} modality={mod_param} type={_422_type}"
        )
        return {
            "data": [],
            "totalRegistros": 0,
            "totalPaginas": 0,
            "paginaAtual": pagina,
            "temProximaPagina": False,
        }

    return "raise"


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: Current retry attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds

    Example:
        With base_delay=2, exponential_base=2, max_delay=60:
        - Attempt 0: 2s
        - Attempt 1: 4s
        - Attempt 2: 8s
        - Attempt 3: 16s
        - Attempt 4: 32s
        - Attempt 5: 60s (capped)
    """
    delay = min(
        config.base_delay * (config.exponential_base**attempt), config.max_delay
    )

    if config.jitter:
        # Add ±50% jitter to prevent thundering herd
        delay *= random.uniform(0.5, 1.5)

    return delay
