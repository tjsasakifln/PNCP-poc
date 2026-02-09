"""
PNCP Platform Statistics Module

Computes real-time statistics about the PNCP procurement platform for
display on the landing page hero section.

Features:
- Queries PNCP API for last 30 days of data (all 27 Brazilian states)
- Filters to modalidade=6 (Dispensa) only for focused statistics
- Calculates annualized projections (multiply by 365/30)
- Aggregates total estimated value (valor_total_estimado)
- Returns structured PNCPStatsResponse

Performance:
- Typical execution: 30-60 seconds (27 UFs in parallel with max_concurrent=10)
- Cached for 24 hours to minimize API load
- Fallback data provided on timeout/errors

Usage:
    from pncp_stats import compute_pncp_stats

    stats = await compute_pncp_stats()
    print(f"Annual bids: {stats.annualized_total}")
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from schemas import PNCPStatsResponse
from pncp_client import buscar_todas_ufs_paralelo
from sectors import list_sectors
from exceptions import PNCPAPIError

logger = logging.getLogger(__name__)

# All 27 Brazilian state codes (26 states + DF)
ALL_UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]

# Fallback data for when PNCP API is unavailable
# Based on historical averages (updated 2026-01-30)
FALLBACK_STATS = PNCPStatsResponse(
    total_bids_30d=12000,
    annualized_total=146000,
    total_value_30d=42000000.00,
    annualized_value=511000000.00,
    total_sectors=9,
    last_updated=datetime.utcnow().isoformat() + "Z"
)


async def compute_pncp_stats(timeout_seconds: int = 90) -> PNCPStatsResponse:
    """
    Compute PNCP platform-wide statistics for landing page.

    Queries PNCP API for:
    - Last 30 days of procurement data
    - All 27 Brazilian states (UFs)
    - Modalidade 6 (Dispensa) only

    Calculates:
    - Total bids published in 30 days
    - Annualized bid count (total * 365/30)
    - Total estimated value (sum of valor_total_estimado)
    - Annualized value projection
    - Total available sectors

    Args:
        timeout_seconds: Maximum time to wait for API response (default 90s)

    Returns:
        PNCPStatsResponse with computed statistics

    Raises:
        PNCPAPIError: If API fails after retries (caller should catch and use fallback)

    Example:
        >>> stats = await compute_pncp_stats()
        >>> print(f"Annual bids: {stats.annualized_total:,}")
        Annual bids: 152,083
    """
    try:
        # Calculate date range (last 30 days)
        data_final = datetime.utcnow().date()
        data_inicial = data_final - timedelta(days=30)

        logger.info(
            f"Computing PNCP stats: {data_inicial} to {data_final} "
            f"(modalidade=6, all 27 UFs)"
        )

        # Fetch data with timeout
        results: List[Dict[str, Any]] = await asyncio.wait_for(
            buscar_todas_ufs_paralelo(
                ufs=ALL_UFS,
                data_inicial=data_inicial.isoformat(),
                data_final=data_final.isoformat(),
                modalidades=[6],  # Dispensa only
                status=None,  # All statuses
                max_concurrent=10,  # Parallel requests
            ),
            timeout=timeout_seconds
        )

        # Aggregate statistics
        total_bids_30d = len(results)

        total_value_30d = sum(
            float(item.get("valorTotalEstimado", 0) or 0)
            for item in results
        )

        # Annualize (30 days -> 365 days)
        annualized_total = int(total_bids_30d * 365 / 30)
        annualized_value = total_value_30d * 365 / 30

        # Get sector count
        total_sectors = len(list_sectors())

        logger.info(
            f"PNCP stats computed: {total_bids_30d:,} bids (30d), "
            f"R$ {total_value_30d:,.2f} (30d), {total_sectors} sectors"
        )

        return PNCPStatsResponse(
            total_bids_30d=total_bids_30d,
            annualized_total=annualized_total,
            total_value_30d=total_value_30d,
            annualized_value=annualized_value,
            total_sectors=total_sectors,
            last_updated=datetime.utcnow().isoformat() + "Z"
        )

    except asyncio.TimeoutError:
        logger.warning(
            f"PNCP stats computation timed out after {timeout_seconds}s. "
            "Using fallback data."
        )
        raise PNCPAPIError("PNCP API timeout during stats computation")

    except Exception as e:
        logger.error(f"Error computing PNCP stats: {e}", exc_info=True)
        raise PNCPAPIError(f"Failed to compute PNCP stats: {e}") from e


def get_fallback_stats() -> PNCPStatsResponse:
    """
    Get fallback statistics when PNCP API is unavailable.

    Returns hardcoded statistics based on historical averages.
    Updated timestamp shows current time to indicate freshness of fallback.

    Returns:
        PNCPStatsResponse with fallback data
    """
    # Update timestamp to current time
    fallback = FALLBACK_STATS.model_copy()
    fallback.last_updated = datetime.utcnow().isoformat() + "Z"

    logger.info("Using fallback PNCP stats (API unavailable)")
    return fallback
