"""STORY-4.1 (TD-SYS-014) — Async runtime for LLM arbiter.

Provides:

- ``_get_async_client()`` — lazy-initialised ``openai.AsyncOpenAI`` with the
  same timeout/retry config as the existing sync client.
- ``_get_semaphore()`` — loop-scoped ``asyncio.Semaphore`` whose bound comes
  from ``LLM_MAX_CONCURRENT``. Loop-scoped so that re-binding across
  ``asyncio.run()`` calls (tests, cron tasks) never produces the classic
  "Future attached to different loop" error.
- ``_bounded(call_type)`` — async context manager combining the semaphore
  with a Prometheus gauge (``smartlic_llm_concurrent_calls{call_type}``).
- ``run_bounded_in_thread(func, *args, call_type)`` — convenience helper for
  call sites that keep a sync inner function (``filter/pipeline.py``): runs
  ``func`` inside ``asyncio.to_thread`` while honouring the semaphore and
  gauge. Lets us swap ``ThreadPoolExecutor(max_workers=10)`` for
  ``asyncio.gather`` with configurable concurrency in one step.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from typing import Any, AsyncIterator, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


_async_client: Any = None  # openai.AsyncOpenAI — typed loose to avoid hard import


def _get_async_client() -> Any:
    """Return a process-wide ``openai.AsyncOpenAI`` instance.

    Mirrors ``_get_client`` semantics: same ``OPENAI_API_KEY``, same timeout
    (``LLM_TIMEOUT_S`` env / config override), single retry.
    """

    global _async_client
    if _async_client is None:
        from openai import AsyncOpenAI  # local import keeps module lightweight

        from config.features import LLM_TIMEOUT_S

        _async_client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=LLM_TIMEOUT_S,
            max_retries=1,
        )
    return _async_client


# ---------------------------------------------------------------------------
# Loop-scoped semaphore (prevents "Future attached to different loop")
# ---------------------------------------------------------------------------


_sem: Optional[asyncio.Semaphore] = None
_sem_loop: Optional[asyncio.AbstractEventLoop] = None


def _get_semaphore() -> asyncio.Semaphore:
    """Return an ``asyncio.Semaphore`` bound to the current running loop."""

    global _sem, _sem_loop
    loop = asyncio.get_running_loop()
    if _sem is None or _sem_loop is not loop:
        # Late import so config changes via monkeypatching tests are respected.
        from llm_arbiter.async_runtime import get_max_concurrent

        _sem = asyncio.Semaphore(get_max_concurrent())
        _sem_loop = loop
    return _sem


def get_max_concurrent() -> int:
    """Resolve ``LLM_MAX_CONCURRENT`` at call time (not import time)."""

    try:
        from config import LLM_MAX_CONCURRENT

        return int(LLM_MAX_CONCURRENT)
    except Exception:
        return int(os.getenv("LLM_MAX_CONCURRENT", "50"))


def reset_semaphore() -> None:
    """Test helper — forces ``_get_semaphore`` to rebuild on next call."""

    global _sem, _sem_loop
    _sem = None
    _sem_loop = None


# ---------------------------------------------------------------------------
# Bounded execution + Prometheus observability
# ---------------------------------------------------------------------------


@contextlib.asynccontextmanager
async def _bounded(call_type: str) -> AsyncIterator[None]:
    """Acquire the semaphore and tick the concurrency gauge while inside."""

    semaphore = _get_semaphore()
    try:
        from metrics import LLM_CONCURRENT_CALLS
    except Exception:
        LLM_CONCURRENT_CALLS = None  # type: ignore[assignment]

    async with semaphore:
        if LLM_CONCURRENT_CALLS is not None:
            try:
                LLM_CONCURRENT_CALLS.labels(call_type=call_type).inc()
            except Exception:
                pass
        try:
            yield
        finally:
            if LLM_CONCURRENT_CALLS is not None:
                try:
                    LLM_CONCURRENT_CALLS.labels(call_type=call_type).dec()
                except Exception:
                    pass


async def run_bounded_in_thread(
    func: Callable[..., Any],
    /,
    *args,
    call_type: str,
    **kwargs,
) -> Any:
    """Run ``func(*args, **kwargs)`` in a worker thread under the semaphore.

    Designed for call sites whose inner function is still synchronous (e.g.
    ``classify_contract_primary_match``). Provides the ``LLM_MAX_CONCURRENT``
    bound + the concurrency gauge without rewriting the inner function.
    """

    async with _bounded(call_type):
        return await asyncio.to_thread(func, *args, **kwargs)


async def gather_classifications(
    func: Callable[..., Any],
    items: list,
    *,
    call_type: str,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> list:
    """Run ``func(item)`` concurrently for every item, returning results in order.

    Preserves the incremental ``on_progress(done, total, phase)`` contract of
    the previous ``ThreadPoolExecutor + as_completed`` pattern. When the inner
    function raises, the exception is stored as the result so the caller can
    re-raise on ``.result()`` — matching the legacy ``future.result()``
    behaviour exactly.
    """

    total = len(items)
    results: list = [None] * total
    done = 0

    async def _one(idx: int, item: Any) -> None:
        nonlocal done
        try:
            results[idx] = await run_bounded_in_thread(func, item, call_type=call_type)
        except BaseException as exc:  # noqa: BLE001 — mirrors future.result() re-raise contract
            results[idx] = _FailedResult(exc)
        done += 1
        if on_progress:
            try:
                on_progress(done, total, "llm_classify")
            except Exception:
                logger.debug("STORY-4.1: on_progress callback raised — ignoring")

    await asyncio.gather(*[_one(i, it) for i, it in enumerate(items)])
    return results


class _FailedResult:
    """Sentinel holding an exception so the legacy ``future.result()`` loop re-raises."""

    __slots__ = ("_exc",)

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def __iter__(self):  # pragma: no cover - not used
        raise self._exc

    @property
    def exc(self) -> BaseException:
        return self._exc


def unwrap_result(result: Any) -> Any:
    """Re-raise exceptions stored by ``gather_classifications`` or return the value."""

    if isinstance(result, _FailedResult):
        raise result.exc
    return result


__all__ = [
    "_FailedResult",
    "_bounded",
    "_get_async_client",
    "_get_semaphore",
    "gather_classifications",
    "get_max_concurrent",
    "reset_semaphore",
    "run_bounded_in_thread",
    "unwrap_result",
]
