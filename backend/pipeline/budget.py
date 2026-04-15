"""STORY-4.4 (TD-SYS-003) — Railway 120s time budgets.

``_run_with_budget`` wraps an awaitable with ``asyncio.wait_for`` and records a
Prometheus counter when the coroutine exceeds its budget. The existing
pipeline already uses ``asyncio.wait_for`` in many places; wiring those call
sites through this helper adds observability without changing behaviour
(``fallback=None`` preserves the raised ``TimeoutError``).

Invariant (enforced by tests/test_timeout_invariants.py):

    pipeline(100s) > consolidation(90s) > per_source(70s) > per_uf(25s)

Background: Railway's proxy kills requests at ~120s. The defaults in
``config/pncp.py`` leave ~20s headroom for response serialization.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def _run_with_budget(
    coro: Awaitable[T],
    *,
    budget: float,
    phase: str,
    source: Optional[str] = None,
    fallback: Optional[Any] = None,
) -> T:
    """Await ``coro`` with a timeout, recording a counter when it expires.

    Parameters
    ----------
    coro:
        The awaitable to run.
    budget:
        Seconds before timing out.
    phase:
        Prometheus label — one of ``pipeline``, ``consolidation``,
        ``per_source``, ``per_uf``.
    source:
        Optional source identifier (e.g. ``pncp``) — used as a Prometheus label.
    fallback:
        Optional value to return on timeout. When ``None``, the
        ``asyncio.TimeoutError`` is re-raised so existing recovery paths keep
        working. Existing call sites SHOULD pass ``fallback=None`` unless
        they can tolerate a silent default.

    Returns
    -------
    The coroutine result, or ``fallback`` when supplied and the budget is
    exceeded.
    """

    try:
        return await asyncio.wait_for(coro, timeout=budget)
    except asyncio.TimeoutError:
        _record_exceeded(phase=phase, source=source, budget=budget)
        if fallback is not None:
            logger.warning(
                "STORY-4.4: budget exceeded phase=%s source=%s budget=%.1fs — using fallback",
                phase,
                source or "",
                budget,
            )
            return fallback  # type: ignore[return-value]
        raise


def _record_exceeded(*, phase: str, source: Optional[str], budget: float) -> None:
    """Record Prometheus counter and a structured log line."""

    try:
        from metrics import PIPELINE_BUDGET_EXCEEDED_TOTAL

        PIPELINE_BUDGET_EXCEEDED_TOTAL.labels(phase=phase, source=source or "").inc()
    except Exception:  # pragma: no cover - metrics unavailable in some envs
        pass
    logger.warning(
        "STORY-4.4: budget exceeded phase=%s source=%s budget=%.1fs",
        phase,
        source or "",
        budget,
    )


__all__ = ["_run_with_budget"]
