"""SELECT-only adapter client for extra-cli public_read_v1.

No browser credentials. No writes. No access to public schema.
DSN must live in server env PUBLIC_READ_V1_DSN.
Supports psycopg3 first, then psycopg2.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator

from public_read.flags import is_kill_switch_on, should_read_public
from public_read.isolation import IsolationBudgets, get_backpressure, load_budgets

logger = logging.getLogger(__name__)

_LAST_KNOWN_GOOD: dict[str, Any] = {}


def public_read_dsn() -> str | None:
    return os.getenv("PUBLIC_READ_V1_DSN") or None


def last_known_good(family: str) -> Any | None:
    return _LAST_KNOWN_GOOD.get(family)


def store_last_known_good(family: str, payload: Any) -> None:
    _LAST_KNOWN_GOOD[family] = payload


def clear_last_known_good() -> None:
    _LAST_KNOWN_GOOD.clear()


def session_options(budgets: IsolationBudgets | None = None) -> list[str]:
    cfg = budgets or load_budgets()
    return [
        "SET default_transaction_read_only = on",
        f"SET statement_timeout = '{cfg.statement_timeout_ms}ms'",
        f"SET lock_timeout = '{cfg.lock_timeout_ms}ms'",
        "SET idle_in_transaction_session_timeout = '5000ms'",
        "SET search_path TO public_read_v1, pg_temp",
    ]


class PublicReadUnavailable(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _connect(dsn: str, connect_timeout: float) -> Any:
    timeout = max(int(connect_timeout), 1)
    try:
        import psycopg

        return psycopg.connect(dsn, connect_timeout=timeout, autocommit=True)
    except ImportError:
        pass
    try:
        import psycopg2
    except ImportError as exc:
        raise PublicReadUnavailable("psycopg_missing") from exc
    conn = psycopg2.connect(dsn, connect_timeout=timeout)
    conn.autocommit = True
    return conn


@contextmanager
def public_read_connection() -> Iterator[Any]:
    """Yield a read-only connection or raise PublicReadUnavailable."""
    if is_kill_switch_on():
        raise PublicReadUnavailable("kill_switch")
    if not should_read_public():
        raise PublicReadUnavailable("mode_off")
    dsn = public_read_dsn()
    if not dsn:
        raise PublicReadUnavailable("dsn_missing")

    pressure = get_backpressure()
    reason = pressure.acquire()
    if reason:
        raise PublicReadUnavailable(reason)

    conn = None
    try:
        budgets = load_budgets()
        try:
            conn = _connect(dsn, budgets.connect_timeout_s)
        except PublicReadUnavailable:
            raise
        except Exception as exc:
            raise PublicReadUnavailable("connect_failed") from exc
        try:
            with conn.cursor() as cur:
                for stmt in session_options(budgets):
                    cur.execute(stmt)
            yield conn
        finally:
            conn.close()
    finally:
        pressure.release()


def fetchall(sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    """Bounded read. Callers must pass parameterized SQL with LIMIT. No retry."""
    with public_read_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            description = cur.description or []
            columns = []
            for desc in description:
                name = getattr(desc, "name", None)
                columns.append(name if name is not None else desc[0])
            rows = cur.fetchall()
    return [dict(zip(columns, row, strict=True)) for row in rows]
