"""Resilient HTTP client for PNCP API — re-export facade.

# TIMEOUT CHAIN (strict decreasing, validated at startup):
# FE Proxy(480s) > Pipeline(360s) > Consolidation(300s) > PerSource(180s)
#   > PerUF(30s) > PerModality(20s) > HTTP(10s)
# Invariants:
#   - Each level must be strictly greater than the next
#   - PerUF - PerModality >= 10s (margin for parallel modality completion)
#   - PerSource > 2 * PerUF (margin for multi-UF batches)

DEBT-204 Track 1: This module is now a thin facade over clients/pncp/.
All implementation lives in the subpackage. Import from either location:
    from pncp_client import AsyncPNCPClient        # legacy — still works
    from clients.pncp import AsyncPNCPClient       # new preferred path
"""

# These module-level imports keep test patches (e.g. @patch("pncp_client.requests.Session.get"))
# working after the facade refactor — patching the class attribute is global regardless of caller.
import requests  # noqa: F401
import httpx  # noqa: F401
import asyncio  # noqa: F401

# Re-export everything from the subpackage so existing callers continue to work.
from clients.pncp.circuit_breaker import (  # noqa: F401
    PNCPCircuitBreaker,
    RedisCircuitBreaker,
    get_circuit_breaker,
    _circuit_breaker,
    _pcp_circuit_breaker,
    _comprasgov_circuit_breaker,
    PNCP_CIRCUIT_BREAKER_THRESHOLD,
    PNCP_CIRCUIT_BREAKER_COOLDOWN,
    PCP_CIRCUIT_BREAKER_THRESHOLD,
    PCP_CIRCUIT_BREAKER_COOLDOWN,
)
from config.pncp import (  # noqa: F401
    PNCP_BATCH_SIZE,
    PNCP_BATCH_DELAY_S,
    USE_REDIS_CIRCUIT_BREAKER,
    CB_REDIS_TTL,
)
from clients.pncp.retry import (  # noqa: F401
    ParallelFetchResult,
    ModalityFetchState,
    DateFormat,
    UFS_BY_POPULATION,
    validate_timeout_chain,
    calculate_delay,
    format_date,
    _get_format_rotation,
    _validate_date_params,
    _handle_422_response,
    _get_cached_date_format,
    _set_cached_date_format,
    PNCP_TIMEOUT_PER_MODALITY,
    PNCP_TIMEOUT_PER_UF,
    PNCP_MODALITY_RETRY_BACKOFF,
)
from clients.pncp.sync_client import (  # noqa: F401
    PNCPClient,
    PNCPDegradedError,
    STATUS_PNCP_MAP,
)
from clients.pncp.async_client import AsyncPNCPClient  # noqa: F401
from clients.pncp.adapter import (  # noqa: F401
    PNCPLegacyAdapter,
    buscar_todas_ufs_paralelo,
)

# Run validation at import time (preserves original behaviour — AC8)
validate_timeout_chain()
