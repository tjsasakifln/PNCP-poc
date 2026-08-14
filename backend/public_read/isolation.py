"""Consumer isolation budgets — #2116.

If SmartLic saturates, SmartLic degrades. extra-cli does not.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass

_DEFAULTS = {
    "PUBLIC_READ_POOL_LIMIT": 4,
    "PUBLIC_READ_MAX_CONCURRENCY": 8,
    "PUBLIC_READ_STATEMENT_TIMEOUT_MS": 2000,
    "PUBLIC_READ_LOCK_TIMEOUT_MS": 500,
    "PUBLIC_READ_QUERY_BUDGET_PER_MIN": 120,
    "PUBLIC_READ_CONNECT_TIMEOUT_S": 2,
}


@dataclass(frozen=True)
class IsolationBudgets:
    pool_limit: int
    max_concurrency: int
    statement_timeout_ms: int
    lock_timeout_ms: int
    query_budget_per_min: int
    connect_timeout_s: float


def load_budgets() -> IsolationBudgets:
    return IsolationBudgets(
        pool_limit=int(os.getenv("PUBLIC_READ_POOL_LIMIT", _DEFAULTS["PUBLIC_READ_POOL_LIMIT"])),
        max_concurrency=int(
            os.getenv("PUBLIC_READ_MAX_CONCURRENCY", _DEFAULTS["PUBLIC_READ_MAX_CONCURRENCY"])
        ),
        statement_timeout_ms=int(
            os.getenv(
                "PUBLIC_READ_STATEMENT_TIMEOUT_MS",
                _DEFAULTS["PUBLIC_READ_STATEMENT_TIMEOUT_MS"],
            )
        ),
        lock_timeout_ms=int(
            os.getenv("PUBLIC_READ_LOCK_TIMEOUT_MS", _DEFAULTS["PUBLIC_READ_LOCK_TIMEOUT_MS"])
        ),
        query_budget_per_min=int(
            os.getenv(
                "PUBLIC_READ_QUERY_BUDGET_PER_MIN",
                _DEFAULTS["PUBLIC_READ_QUERY_BUDGET_PER_MIN"],
            )
        ),
        connect_timeout_s=float(
            os.getenv(
                "PUBLIC_READ_CONNECT_TIMEOUT_S",
                _DEFAULTS["PUBLIC_READ_CONNECT_TIMEOUT_S"],
            )
        ),
    )


class Backpressure:
    """Process-local token window + concurrency gate."""

    def __init__(self, budgets: IsolationBudgets | None = None) -> None:
        self.budgets = budgets or load_budgets()
        self._lock = threading.Lock()
        self._in_flight = 0
        self._window_start = time.monotonic()
        self._window_count = 0

    def acquire(self) -> str | None:
        """Return a reason code if the call must degrade, else None."""
        with self._lock:
            now = time.monotonic()
            if now - self._window_start >= 60:
                self._window_start = now
                self._window_count = 0
            if self._in_flight >= self.budgets.max_concurrency:
                return "concurrency_budget_exceeded"
            if self._window_count >= self.budgets.query_budget_per_min:
                return "query_budget_exceeded"
            self._in_flight += 1
            self._window_count += 1
            return None

    def release(self) -> None:
        with self._lock:
            self._in_flight = max(0, self._in_flight - 1)

    def snapshot(self) -> dict[str, int | float]:
        with self._lock:
            return {
                "in_flight": self._in_flight,
                "window_count": self._window_count,
                "pool_limit": self.budgets.pool_limit,
                "max_concurrency": self.budgets.max_concurrency,
                "query_budget_per_min": self.budgets.query_budget_per_min,
            }


_BACKPRESSURE = Backpressure()


def get_backpressure() -> Backpressure:
    return _BACKPRESSURE
