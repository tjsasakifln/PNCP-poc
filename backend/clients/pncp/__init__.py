"""PNCP client subpackage — re-export facade.

All public names from the original pncp_client module are re-exported here
so that ``from clients.pncp import AsyncPNCPClient`` works alongside the
existing ``from pncp_client import AsyncPNCPClient`` import path.
"""

from clients.pncp.circuit_breaker import (
    PNCPCircuitBreaker,
    RedisCircuitBreaker,
    get_circuit_breaker,
)
from clients.pncp.retry import (
    ParallelFetchResult,
    ModalityFetchState,
    DateFormat,
    validate_timeout_chain,
    calculate_delay,
    format_date,
)
from clients.pncp.sync_client import PNCPClient, PNCPDegradedError
from clients.pncp.async_client import AsyncPNCPClient
from clients.pncp.adapter import PNCPLegacyAdapter, buscar_todas_ufs_paralelo

__all__ = [
    "PNCPCircuitBreaker",
    "RedisCircuitBreaker",
    "get_circuit_breaker",
    "ParallelFetchResult",
    "ModalityFetchState",
    "DateFormat",
    "validate_timeout_chain",
    "calculate_delay",
    "format_date",
    "PNCPClient",
    "PNCPDegradedError",
    "AsyncPNCPClient",
    "PNCPLegacyAdapter",
    "buscar_todas_ufs_paralelo",
]
