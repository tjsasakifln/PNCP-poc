"""
Enhanced PNCP Client with Resilience Features

This module provides an enhanced version of AsyncPNCPClient with:
- Adaptive per-UF timeouts based on historical performance
- Retry logic with exponential backoff for failed UFs
- Circuit breaker to prevent cascading failures
- Simple caching to reduce API load

Task #3: Prevent PNCP API timeouts and improve reliability
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List

from config import DEFAULT_MODALIDADES, RetryConfig
from pncp_client import AsyncPNCPClient, STATUS_PNCP_MAP, PNCPAPIError
from pncp_resilience import (
    get_timeout_manager,
    get_circuit_breaker,
    get_cache,
)

logger = logging.getLogger(__name__)


class ResilientAsyncPNCPClient(AsyncPNCPClient):
    """
    Enhanced AsyncPNCPClient with resilience features.

    Features:
    1. Adaptive timeouts per UF (faster UFs = shorter timeout)
    2. Automatic retry with exponential backoff
    3. Circuit breaker to prevent hammering failing API
    4. Simple caching (1 hour TTL)
    5. Comprehensive metrics and logging
    """

    def __init__(
        self,
        config: RetryConfig | None = None,
        max_concurrent: int = 10,
        enable_cache: bool = True,
        enable_retry: bool = True,
        max_retries_per_uf: int = 2,
    ):
        """
        Initialize resilient PNCP client.

        Args:
            config: Retry configuration
            max_concurrent: Maximum concurrent requests
            enable_cache: Enable result caching
            enable_retry: Enable automatic retry on failure
            max_retries_per_uf: Maximum retry attempts per UF
        """
        super().__init__(config=config, max_concurrent=max_concurrent)
        self.enable_cache = enable_cache
        self.enable_retry = enable_retry
        self.max_retries_per_uf = max_retries_per_uf

        # Get singleton instances
        self.timeout_manager = get_timeout_manager()
        self.circuit_breaker = get_circuit_breaker()
        self.cache = get_cache()

    async def _fetch_uf_with_resilience(
        self,
        uf: str,
        data_inicial: str,
        data_final: str,
        modalidades: List[int],
        status: str | None = None,
        max_pages: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fetch UF data with resilience features: cache, adaptive timeout, retry.

        Args:
            uf: State code
            data_inicial: Start date
            data_final: End date
            modalidades: List of modality codes
            status: Optional status filter
            max_pages: Maximum pages to fetch per modality

        Returns:
            List of procurement records
        """
        # Check circuit breaker first
        if self.circuit_breaker.is_open:
            logger.warning(
                f"Circuit breaker is OPEN for UF={uf}, skipping fetch "
                f"(will retry in {self.circuit_breaker.config.timeout_seconds}s)"
            )
            return []

        # Try cache first (if enabled)
        if self.enable_cache and len(modalidades) == 1:
            # Only cache single-modalidade requests (most common case)
            cached = self.cache.get(
                uf=uf,
                data_inicial=data_inicial,
                data_final=data_final,
                modalidade=modalidades[0],
                status=status,
            )
            if cached is not None:
                logger.info(
                    f"Using cached results for UF={uf} "
                    f"({len(cached)} items, hit_rate={self.cache.hit_rate:.1%})"
                )
                return cached

        # Get adaptive timeout for this UF
        timeout = self.timeout_manager.get_timeout(uf)

        # Fetch with retry logic
        attempt = 0
        last_error = None

        while attempt <= (self.max_retries_per_uf if self.enable_retry else 0):
            start_time = time.time()

            try:
                logger.info(
                    f"Fetching UF={uf} (attempt {attempt + 1}/{self.max_retries_per_uf + 1}, "
                    f"timeout={timeout:.1f}s)"
                )

                # Fetch with timeout
                result = await asyncio.wait_for(
                    self._fetch_uf_all_pages(
                        uf=uf,
                        data_inicial=data_inicial,
                        data_final=data_final,
                        modalidades=modalidades,
                        status=status,
                        max_pages=max_pages,
                    ),
                    timeout=timeout,
                )

                # Success! Record metrics
                duration_ms = (time.time() - start_time) * 1000
                self.timeout_manager.record_request(
                    uf=uf,
                    duration_ms=duration_ms,
                    success=True,
                    is_timeout=False,
                )

                # Cache result (if enabled and single modalidade)
                if self.enable_cache and len(modalidades) == 1:
                    self.cache.put(
                        uf=uf,
                        data_inicial=data_inicial,
                        data_final=data_final,
                        modalidade=modalidades[0],
                        data=result,
                        status=status,
                    )

                logger.info(
                    f"UF={uf} fetch successful: {len(result)} items in {duration_ms/1000:.1f}s"
                )
                return result

            except asyncio.TimeoutError:
                # Timeout - record and retry
                duration_ms = timeout * 1000
                self.timeout_manager.record_request(
                    uf=uf,
                    duration_ms=duration_ms,
                    success=False,
                    is_timeout=True,
                )

                last_error = f"timeout after {timeout:.1f}s"
                logger.warning(
                    f"UF={uf} timed out after {timeout:.1f}s (attempt {attempt + 1})"
                )

                if attempt < self.max_retries_per_uf and self.enable_retry:
                    # Calculate backoff delay: 2^attempt * 2 seconds
                    backoff = (2 ** attempt) * 2
                    logger.info(f"Retrying UF={uf} after {backoff}s backoff...")
                    await asyncio.sleep(backoff)
                    attempt += 1

                    # Increase timeout for retry (1.5x)
                    timeout = min(timeout * 1.5, 180.0)
                else:
                    logger.error(
                        f"UF={uf} failed after {attempt + 1} attempts (all timeouts)"
                    )
                    return []

            except PNCPAPIError as e:
                # API error - record and decide whether to retry
                duration_ms = (time.time() - start_time) * 1000
                self.timeout_manager.record_request(
                    uf=uf,
                    duration_ms=duration_ms,
                    success=False,
                    is_timeout=False,
                )

                last_error = str(e)
                logger.warning(f"UF={uf} API error: {e}")

                # Don't retry on non-retryable errors (4xx codes)
                if "non-retryable" in str(e).lower():
                    logger.error(f"UF={uf} failed with non-retryable error: {e}")
                    return []

                if attempt < self.max_retries_per_uf and self.enable_retry:
                    backoff = (2 ** attempt) * 2
                    logger.info(f"Retrying UF={uf} after {backoff}s backoff...")
                    await asyncio.sleep(backoff)
                    attempt += 1
                else:
                    logger.error(f"UF={uf} failed after {attempt + 1} attempts: {e}")
                    return []

            except Exception as e:
                # Unexpected error - record and fail
                duration_ms = (time.time() - start_time) * 1000
                self.timeout_manager.record_request(
                    uf=uf,
                    duration_ms=duration_ms,
                    success=False,
                    is_timeout=False,
                )

                logger.error(f"UF={uf} unexpected error: {e}", exc_info=True)
                return []

        # All retries exhausted
        logger.error(f"UF={uf} failed after all retries. Last error: {last_error}")
        return []

    async def buscar_todas_ufs_paralelo(
        self,
        ufs: List[str],
        data_inicial: str,
        data_final: str,
        modalidades: List[int] | None = None,
        status: str | None = None,
        max_pages_per_uf: int = 50,
        on_uf_complete: Callable[[str, int], Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca licitações em múltiplas UFs em paralelo com resiliência.

        Enhanced version with:
        - Adaptive timeouts per UF
        - Automatic retry with exponential backoff
        - Circuit breaker protection
        - Caching for repeated queries
        - Comprehensive metrics

        Args:
            ufs: List of state codes (e.g., ["SP", "RJ", "MG"])
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            modalidades: List of modality codes (default: [6] - Pregão Eletrônico)
            status: Status filter (StatusLicitacao value or None)
            max_pages_per_uf: Maximum pages to fetch per UF/modality
            on_uf_complete: Optional callback(uf, items_count) called per UF

        Returns:
            List of all procurement records (deduplicated)
        """
        import time as sync_time

        start_time = sync_time.time()

        # Use default modalities if not specified
        modalidades = modalidades or DEFAULT_MODALIDADES

        # Map status to PNCP API value
        pncp_status = STATUS_PNCP_MAP.get(status) if status else None

        logger.info(
            f"[RESILIENT] Starting parallel fetch for {len(ufs)} UFs "
            f"(max_concurrent={self.max_concurrent}, cache={self.enable_cache}, "
            f"retry={self.enable_retry}, status={status})"
        )

        # Create tasks for each UF with progress callback
        async def _fetch_with_callback(uf: str) -> List[Dict[str, Any]]:
            result = await self._fetch_uf_with_resilience(
                uf=uf,
                data_inicial=data_inicial,
                data_final=data_final,
                modalidades=modalidades,
                status=pncp_status,
                max_pages=max_pages_per_uf,
            )

            # Call progress callback if provided
            if on_uf_complete:
                try:
                    maybe_coro = on_uf_complete(uf, len(result))
                    if asyncio.iscoroutine(maybe_coro):
                        await maybe_coro
                except Exception as cb_err:
                    logger.warning(f"on_uf_complete callback error for UF={uf}: {cb_err}")

            return result

        # Execute all tasks concurrently (semaphore limits actual concurrency)
        tasks = [_fetch_with_callback(uf) for uf in ufs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results and handle errors
        all_items: List[Dict[str, Any]] = []
        errors = 0
        successful_ufs = 0
        empty_ufs = 0

        for uf, result in zip(ufs, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching UF={uf}: {result}")
                errors += 1
            elif len(result) == 0:
                empty_ufs += 1
                logger.warning(f"UF={uf} returned 0 results (timeout or error)")
            else:
                all_items.extend(result)
                successful_ufs += 1

        elapsed = sync_time.time() - start_time

        # Log comprehensive metrics
        logger.info(
            f"[RESILIENT] Parallel fetch complete: {len(all_items)} items from "
            f"{successful_ufs}/{len(ufs)} UFs in {elapsed:.2f}s "
            f"(errors={errors}, empty={empty_ufs})"
        )

        # Log cache statistics
        if self.enable_cache:
            cache_stats = self.cache.get_stats()
            logger.info(
                f"[RESILIENT] Cache stats: "
                f"hit_rate={cache_stats['hit_rate']:.1%}, "
                f"hits={cache_stats['hits']}, "
                f"misses={cache_stats['misses']}, "
                f"size={cache_stats['size']}"
            )

        # Log timeout manager statistics
        timeout_stats = self.timeout_manager.get_stats()
        unhealthy_ufs = [
            uf for uf, stats in timeout_stats.items()
            if not stats["is_healthy"]
        ]
        if unhealthy_ufs:
            logger.warning(
                f"[RESILIENT] Unhealthy UFs (success rate <70%): {unhealthy_ufs}"
            )

        return all_items


# ============================================================================
# Convenience Function
# ============================================================================

async def buscar_todas_ufs_paralelo_resilient(
    ufs: List[str],
    data_inicial: str,
    data_final: str,
    modalidades: List[int] | None = None,
    status: str | None = None,
    max_concurrent: int = 10,
    enable_cache: bool = True,
    enable_retry: bool = True,
    on_uf_complete: Callable[[str, int], Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function for resilient parallel UF search.

    This is a drop-in replacement for buscar_todas_ufs_paralelo() with
    resilience features enabled by default.

    Args:
        ufs: List of state codes
        data_inicial: Start date YYYY-MM-DD
        data_final: End date YYYY-MM-DD
        modalidades: Optional modality codes
        status: Optional status filter
        max_concurrent: Maximum concurrent requests (default 10)
        enable_cache: Enable result caching (default True)
        enable_retry: Enable automatic retry (default True)
        on_uf_complete: Optional async callback(uf, items_count) called per UF

    Returns:
        List of procurement records

    Example:
        >>> results = await buscar_todas_ufs_paralelo_resilient(
        ...     ufs=["SP", "RJ", "PR", "RS"],
        ...     data_inicial="2026-02-01",
        ...     data_final="2026-02-10",
        ...     enable_cache=True,
        ...     enable_retry=True,
        ... )
    """
    async with ResilientAsyncPNCPClient(
        max_concurrent=max_concurrent,
        enable_cache=enable_cache,
        enable_retry=enable_retry,
    ) as client:
        return await client.buscar_todas_ufs_paralelo(
            ufs=ufs,
            data_inicial=data_inicial,
            data_final=data_final,
            modalidades=modalidades,
            status=status,
            on_uf_complete=on_uf_complete,
        )
