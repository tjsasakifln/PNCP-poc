"""_PNCPParallelMixin — parallel fetching methods for AsyncPNCPClient.

Extracted from async_client.py to keep each file under 700 LOC.
AsyncPNCPClient inherits this mixin via MRO; self.* references resolve there.
"""

import asyncio
import logging
import sys
import time as sync_time
from typing import Any, Callable, Dict, List

import config as _config
from config import (
    PNCP_BATCH_SIZE,
    PNCP_BATCH_DELAY_S,
    DEFAULT_MODALIDADES,
    MODALIDADES_EXCLUIDAS,
)
from clients.pncp.circuit_breaker import _circuit_breaker
from clients.pncp.retry import (
    ModalityFetchState,
    ParallelFetchResult,
    UFS_BY_POPULATION,
)

logger = logging.getLogger(__name__)


def _pncp_timeout_per_modality() -> float:
    """Read at call-time so @patch('pncp_client.PNCP_TIMEOUT_PER_MODALITY', x) works in tests."""
    m = sys.modules.get("pncp_client")
    return getattr(m, "PNCP_TIMEOUT_PER_MODALITY", _config.PNCP_TIMEOUT_PER_MODALITY)


def _pncp_modality_retry_backoff() -> float:
    m = sys.modules.get("pncp_client")
    return getattr(m, "PNCP_MODALITY_RETRY_BACKOFF", _config.PNCP_MODALITY_RETRY_BACKOFF)


def _pncp_timeout_per_uf() -> float:
    m = sys.modules.get("pncp_client")
    return getattr(m, "PNCP_TIMEOUT_PER_UF", _config.PNCP_TIMEOUT_PER_UF)


def _pncp_timeout_per_uf_degraded() -> float:
    m = sys.modules.get("pncp_client")
    return getattr(m, "PNCP_TIMEOUT_PER_UF_DEGRADED", _config.PNCP_TIMEOUT_PER_UF_DEGRADED)


class _PNCPParallelMixin:
    """Mixin providing the three parallel-fetch methods for AsyncPNCPClient."""

    # These attributes are defined in AsyncPNCPClient and resolved at runtime.
    _semaphore: asyncio.Semaphore | None
    max_concurrent: int

    async def _fetch_modality_with_timeout(
        self,
        uf: str,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        status: str | None = None,
        max_pages: int | None = None,
    ) -> tuple[List[Dict[str, Any]], bool]:
        """Fetch a single modality with per-modality timeout and partial accumulation.

        Uses a shared ``ModalityFetchState`` so that items accumulated before a
        timeout cancellation are preserved instead of being discarded.

        When a timeout occurs and partial items exist, they are returned with
        ``was_truncated=True`` immediately (no retry needed — we already have
        useful data). If timeout fires with 0 items, a retry is attempted
        (STORY-252 AC9) since page 1 may have been transiently slow.

        Returns:
            Tuple of (items, was_truncated). Partial items + True if timed out
            with accumulated data; empty list + False only if both attempts
            yielded nothing.
        """
        per_modality_timeout = _pncp_timeout_per_modality()
        retry_backoff = _pncp_modality_retry_backoff()

        state = ModalityFetchState()

        for attempt in range(2):  # 0 = first try, 1 = retry
            try:
                result = await asyncio.wait_for(
                    self._fetch_single_modality(  # type: ignore[attr-defined]
                        uf=uf,
                        data_inicial=data_inicial,
                        data_final=data_final,
                        modalidade=modalidade,
                        status=status,
                        max_pages=max_pages,
                        state=state,
                    ),
                    timeout=per_modality_timeout,
                )
                return result
            except asyncio.TimeoutError:
                state.timed_out = True
                partial_count = len(state.items)
                await _circuit_breaker.record_failure()

                if partial_count > 0:
                    # Partial accumulation: return what we have instead of discarding
                    state.was_truncated = True
                    logger.warning(
                        f"UF={uf} modalidade={modalidade} timed out after "
                        f"{per_modality_timeout}s on attempt {attempt + 1} — "
                        f"returning {partial_count} partial items "
                        f"({state.pages_fetched} pages fetched)"
                    )
                    return state.items, True

                # Zero items: worth retrying (could be transient slowness on page 1)
                if attempt == 0:
                    logger.warning(
                        f"UF={uf} modalidade={modalidade} timed out after "
                        f"{per_modality_timeout}s with 0 items — "
                        f"retrying in {retry_backoff}s (attempt 1/1)"
                    )
                    await asyncio.sleep(retry_backoff)
                    # Reset state for retry attempt
                    state = ModalityFetchState()
                else:
                    logger.warning(
                        f"UF={uf} modalidade={modalidade} timed out after retry "
                        f"with 0 items — skipping this modality"
                    )
        return [], False

    async def _fetch_uf_all_pages(
        self,
        uf: str,
        data_inicial: str,
        data_final: str,
        modalidades: List[int],
        status: str | None = None,
        max_pages: int | None = None,  # STORY-282 AC2: Defaults to PNCP_MAX_PAGES (5)
    ) -> tuple[List[Dict[str, Any]], bool]:
        """Fetch all pages for a single UF across all modalities in parallel.

        STORY-252 AC6: Each modality runs with its own timeout so that one
        hanging modality does not block the others.

        Args:
            uf: State code.
            data_inicial: Start date.
            data_final: End date.
            modalidades: List of modality codes.
            status: Optional status filter.
            max_pages: Maximum pages to fetch per modality.

        Returns:
            Tuple of (items, was_truncated). was_truncated is True when any
            modality hit max_pages (GTM-FIX-004).
        """
        async with self._semaphore:  # type: ignore[attr-defined]
            # Launch all modalities in parallel with individual timeouts (AC6)
            modality_tasks = [
                self._fetch_modality_with_timeout(
                    uf=uf,
                    data_inicial=data_inicial,
                    data_final=data_final,
                    modalidade=mod,
                    status=status,
                    max_pages=max_pages,
                )
                for mod in modalidades
            ]

            modality_results = await asyncio.gather(
                *modality_tasks, return_exceptions=True
            )

            # Merge and deduplicate across modalities
            all_items: List[Dict[str, Any]] = []
            seen_ids: set[str] = set()
            uf_was_truncated = False

            for mod, result in zip(modalidades, modality_results):
                if isinstance(result, Exception):
                    logger.warning(
                        f"UF={uf} modalidade={mod} failed: {result}"
                    )
                    continue
                # GTM-FIX-004: result is now (items, was_truncated)
                items, was_truncated = result
                if was_truncated:
                    uf_was_truncated = True
                for item in items:
                    item_id = item.get("codigoCompra", "") or item.get(
                        "numeroControlePNCP", ""
                    )
                    if item_id and item_id not in seen_ids:
                        seen_ids.add(item_id)
                        all_items.append(item)

            logger.debug(f"Fetched {len(all_items)} items for UF={uf} (truncated={uf_was_truncated})")
            return all_items, uf_was_truncated

    async def buscar_todas_ufs_paralelo(
        self,
        ufs: List[str],
        data_inicial: str,
        data_final: str,
        modalidades: List[int] | None = None,
        status: str | None = None,
        max_pages_per_uf: int | None = None,  # STORY-282 AC2: Defaults to PNCP_MAX_PAGES (5)
        on_uf_complete: Callable[[str, int], Any] | None = None,
        on_uf_status: Callable[..., Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca licitações em múltiplas UFs em paralelo com limite de concorrência.

        This is the main method for parallel UF fetching. It creates one task
        per UF and executes them concurrently (up to max_concurrent).

        Args:
            ufs: List of state codes (e.g., ["SP", "RJ", "MG"])
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            modalidades: List of modality codes (default: [6] - Pregão Eletrônico)
            status: Status filter (StatusLicitacao value or None)
            max_pages_per_uf: Maximum pages to fetch per UF/modality

        Returns:
            List of all procurement records (deduplicated)

        Example:
            >>> async with AsyncPNCPClient(max_concurrent=10) as client:
            ...     results = await client.buscar_todas_ufs_paralelo(
            ...         ufs=["SP", "RJ", "MG", "BA", "RS"],
            ...         data_inicial="2026-01-01",
            ...         data_final="2026-01-15",
            ...         status="recebendo_proposta"
            ...     )
            >>> len(results)
            1523
        """
        from config import PNCP_MAX_PAGES
        from clients.pncp.async_client import STATUS_PNCP_MAP

        start_time = sync_time.time()

        # STORY-282 AC2: Resolve default page limit
        if max_pages_per_uf is None:
            max_pages_per_uf = PNCP_MAX_PAGES

        # Use default modalities if not specified; always filter out excluded
        modalidades = modalidades or DEFAULT_MODALIDADES
        modalidades = [m for m in modalidades if m not in MODALIDADES_EXCLUIDAS]

        # Map status to PNCP API value
        pncp_status = STATUS_PNCP_MAP.get(status) if status else None

        logger.info(
            f"Starting parallel fetch for {len(ufs)} UFs "
            f"(max_concurrent={self.max_concurrent}, status={status})"
        )

        # Try to recover before checking degraded state (STORY-257A AC4)
        await _circuit_breaker.try_recover()

        # STORY-257A AC1: Degraded mode tries with reduced concurrency
        if _circuit_breaker.is_degraded:
            logger.warning(
                "PNCP circuit breaker degraded — trying with reduced concurrency "
                f"(3 UFs, {_pncp_timeout_per_uf_degraded()}s timeout)"
            )
            # Reorder UFs by population priority
            ufs_ordered = sorted(ufs, key=lambda u: UFS_BY_POPULATION.index(u) if u in UFS_BY_POPULATION else 99)
            # Reduce concurrency
            self._semaphore = asyncio.Semaphore(3)  # type: ignore[attr-defined]
            # GTM-FIX-029 AC2: 120s in degraded mode (was 45s)
            PER_UF_TIMEOUT = _pncp_timeout_per_uf_degraded()
        else:
            # STORY-252 AC10: Health canary — lightweight probe before full search
            canary_ok = await self.health_canary()  # type: ignore[attr-defined]
            if not canary_ok:
                logger.warning(
                    "PNCP health canary failed — returning empty results"
                )
                return ParallelFetchResult(items=[], succeeded_ufs=[], failed_ufs=list(ufs))

            # Normal mode
            ufs_ordered = ufs
            # GTM-FIX-029 AC1/AC3: PER_UF_TIMEOUT raised from 30s to 90s
            # With tamanhoPagina=50, each modality needs ~10x more pages than before.
            # Calculation: 4 mods × ~15s/mod (with retry) = ~60s + 30s margin = 90s
            PER_UF_TIMEOUT = _pncp_timeout_per_uf()

        # Helper to safely call async/sync callbacks
        async def _safe_callback(cb, *args, **kwargs):
            if cb is None:
                return
            try:
                maybe_coro = cb(*args, **kwargs)
                if asyncio.iscoroutine(maybe_coro):
                    await maybe_coro
            except Exception as cb_err:
                logger.warning(f"Callback error: {cb_err}")

        # Create tasks for each UF with optional progress callback
        # GTM-FIX-004: returns (items, was_truncated) tuple
        async def _fetch_with_callback(uf: str) -> tuple[List[Dict[str, Any]], bool]:
            # STORY-257A AC6: Emit "fetching" status when UF starts
            await _safe_callback(on_uf_status, uf, "fetching")
            try:
                items, was_truncated = await asyncio.wait_for(
                    self._fetch_uf_all_pages(
                        uf=uf,
                        data_inicial=data_inicial,
                        data_final=data_final,
                        modalidades=modalidades,
                        status=pncp_status,
                        max_pages=max_pages_per_uf,
                    ),
                    timeout=PER_UF_TIMEOUT,
                )
            except asyncio.TimeoutError:
                await _circuit_breaker.record_failure()
                logger.warning(f"UF={uf} timed out after {PER_UF_TIMEOUT}s — skipping")
                # AC6: Emit "failed" status
                await _safe_callback(on_uf_status, uf, "failed", reason="timeout")
                items, was_truncated = [], False
            else:
                # AC6: Emit "success" status with count
                await _safe_callback(on_uf_status, uf, "success", count=len(items))
            if on_uf_complete:
                await _safe_callback(on_uf_complete, uf, len(items))
            return items, was_truncated

        # GTM-FIX-031: Phased UF batching — execute in batches of PNCP_BATCH_SIZE
        # with PNCP_BATCH_DELAY_S between batches to reduce API pressure
        batch_size = PNCP_BATCH_SIZE
        batch_delay = PNCP_BATCH_DELAY_S
        all_items: List[Dict[str, Any]] = []
        errors = 0
        succeeded_ufs = []
        failed_ufs = []
        truncated_ufs = []  # GTM-FIX-004
        total_batches = (len(ufs_ordered) + batch_size - 1) // batch_size

        for batch_idx in range(0, len(ufs_ordered), batch_size):
            batch = ufs_ordered[batch_idx:batch_idx + batch_size]
            batch_num = batch_idx // batch_size + 1

            logger.debug(
                f"Batch {batch_num}/{total_batches}: fetching {len(batch)} UFs: {batch}"
            )

            # Emit batch progress via SSE
            await _safe_callback(
                on_uf_status, batch[0], "batch_info",
                batch_num=batch_num, total_batches=total_batches,
                ufs_in_batch=batch,
            )

            batch_tasks = [_fetch_with_callback(uf) for uf in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for uf, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error fetching UF={uf}: {result}")
                    errors += 1
                    failed_ufs.append(uf)
                elif isinstance(result, tuple):
                    items, was_truncated = result
                    if was_truncated:
                        truncated_ufs.append(uf)
                    if len(items) == 0:
                        succeeded_ufs.append(uf)  # No data ≠ failure
                    else:
                        all_items.extend(items)
                        succeeded_ufs.append(uf)
                else:
                    # Backward compat: plain list (shouldn't happen with new code)
                    all_items.extend(result)
                    succeeded_ufs.append(uf)

            # Inter-batch delay (skip after last batch)
            if batch_idx + batch_size < len(ufs_ordered):
                logger.debug(f"Batch {batch_num} complete, waiting {batch_delay}s before next batch")
                await asyncio.sleep(batch_delay)

        # STORY-257A AC7: Auto-retry failed UFs (1 round, 5s delay)
        # GTM-FIX-029: Retry timeout matches degraded per-UF timeout (120s)
        if failed_ufs and succeeded_ufs:
            logger.debug(
                f"AC7: {len(failed_ufs)} UFs failed, {len(succeeded_ufs)} succeeded — "
                f"retrying failed UFs in 5s with {_pncp_timeout_per_uf_degraded()}s timeout"
            )
            await asyncio.sleep(5)

            RETRY_TIMEOUT = _pncp_timeout_per_uf_degraded()

            async def _retry_uf(uf: str) -> tuple[List[Dict[str, Any]], bool]:
                await _safe_callback(on_uf_status, uf, "retrying", attempt=2, max=2)
                try:
                    items, was_truncated = await asyncio.wait_for(
                        self._fetch_uf_all_pages(
                            uf=uf,
                            data_inicial=data_inicial,
                            data_final=data_final,
                            modalidades=modalidades,
                            status=pncp_status,
                            max_pages=max_pages_per_uf,
                        ),
                        timeout=RETRY_TIMEOUT,
                    )
                    return items, was_truncated
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"AC7: Retry for UF={uf} failed: {e}")
                    return [], False

            retry_tasks = [_retry_uf(uf) for uf in failed_ufs]
            retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)

            recovered_ufs = []
            for uf, result in zip(failed_ufs, retry_results):
                if isinstance(result, Exception):
                    await _safe_callback(on_uf_status, uf, "failed", reason="retry_failed")
                elif isinstance(result, tuple):
                    items, was_truncated = result
                    if not items:
                        await _safe_callback(on_uf_status, uf, "failed", reason="retry_failed")
                    else:
                        all_items.extend(items)
                        recovered_ufs.append(uf)
                        if was_truncated and uf not in truncated_ufs:
                            truncated_ufs.append(uf)
                        await _safe_callback(on_uf_status, uf, "recovered", count=len(items))
                        logger.debug(f"AC7: UF={uf} recovered with {len(items)} items")
                else:
                    await _safe_callback(on_uf_status, uf, "failed", reason="retry_failed")

            if recovered_ufs:
                # Move recovered UFs from failed to succeeded
                for uf in recovered_ufs:
                    failed_ufs.remove(uf)
                    succeeded_ufs.append(uf)
                logger.info(f"AC7: Recovered {len(recovered_ufs)} UFs: {recovered_ufs}")

        elapsed = sync_time.time() - start_time
        if truncated_ufs:
            logger.warning(
                f"GTM-FIX-004: Truncated UFs: {truncated_ufs}. "
                f"Results may be incomplete for these states."
            )
        logger.info(
            f"Parallel fetch complete: {len(all_items)} items from {len(ufs)} UFs "
            f"in {elapsed:.2f}s ({errors} errors, {len(truncated_ufs)} truncated)"
        )

        return ParallelFetchResult(
            items=all_items,
            succeeded_ufs=succeeded_ufs,
            failed_ufs=failed_ufs,
            truncated_ufs=truncated_ufs,
        )
