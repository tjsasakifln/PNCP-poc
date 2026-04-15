"""STORY-4.5 (TD-SYS-002) — PNCP API Breaking Change Detection Canary.

Extends the light page-size probe in ``health.py`` with:

- Explicit ``tamanhoPagina=51`` probe that asserts the PNCP rejection persists.
- ``tamanhoPagina=50`` probe validated against a frozen JSON schema so we
  detect response-shape drift (field renames, type flips).
- Consecutive-failure counter persisted in Redis with TTL so that transient
  network blips don't page on-call; Sentry fires only after ``threshold`` runs.
- Fingerprint-based Sentry dedup so operators get ONE alert per breaking
  change, not one every ``PNCP_CANARY_INTERVAL_S`` seconds.

Historical context: PNCP silently reduced ``tamanhoPagina`` from 500 to 50 in
February 2026 and the existing ``tamanhoPagina=10`` health canary did not
detect it. This module is the first line of defence against a recurrence.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


PNCP_ENDPOINT = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

# Redis keys — keep short, prefix with smartlic namespace
REDIS_KEY_FAILURES = "smartlic:pncp_canary:consecutive_failures"
REDIS_KEY_LAST_SUCCESS = "smartlic:pncp_canary:last_success_ts"
REDIS_KEY_ALERTED = "smartlic:pncp_canary:alerted:{reason}"

_FAILURES_TTL_S = 3600  # 1h — auto-reset if the canary itself stops running
_ALERTED_TTL_S = 21600  # 6h — re-alert if the issue persists across windows


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class CanaryResult:
    """Outcome of a single canary run — useful for tests and logs."""

    healthy: bool
    reason: Optional[str] = None
    details: Optional[dict] = None
    consecutive_failures: int = 0
    alerted: bool = False


# ---------------------------------------------------------------------------
# Schema loading (cached)
# ---------------------------------------------------------------------------


_SCHEMA_PATH = Path(__file__).parent / "contracts" / "schemas" / "pncp_search_response.schema.json"
_schema_cache: Optional[dict] = None


def _load_schema() -> Optional[dict]:
    """Load and cache the PNCP response schema. Returns None if unavailable."""

    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache
    try:
        with _SCHEMA_PATH.open("r", encoding="utf-8") as fh:
            _schema_cache = json.load(fh)
        return _schema_cache
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("STORY-4.5: PNCP schema unavailable at %s: %s", _SCHEMA_PATH, exc)
        return None


def _validate_shape(sample: Any, schema: dict) -> tuple[bool, list[str]]:
    """Validate sample against schema. Reuses contract_validator when possible."""

    try:
        from tests.contracts.contract_validator import validate_shape  # type: ignore

        result = validate_shape(sample, schema)
        return bool(result.valid), list(result.errors)
    except ImportError:
        # Production deploy may not ship tests/ — fall back to raw jsonschema.
        try:
            from jsonschema import Draft202012Validator

            errors = [
                f"{list(e.absolute_path)}: {e.message}"
                for e in Draft202012Validator(schema).iter_errors(sample)
            ]
            return (not errors), errors
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("STORY-4.5: jsonschema unavailable (%s); skipping shape check", exc)
            return True, []


# ---------------------------------------------------------------------------
# Redis-backed state helpers (graceful when Redis is unavailable)
# ---------------------------------------------------------------------------


async def _get_redis():
    try:
        from redis_pool import get_redis_pool

        return await get_redis_pool()
    except Exception as exc:
        logger.debug("STORY-4.5: Redis pool unavailable: %s", exc)
        return None


async def _increment_failures(redis) -> int:
    if redis is None:
        return 0
    try:
        count = await redis.incr(REDIS_KEY_FAILURES)
        await redis.expire(REDIS_KEY_FAILURES, _FAILURES_TTL_S)
        return int(count)
    except Exception as exc:
        logger.debug("STORY-4.5: Failure counter increment failed: %s", exc)
        return 0


async def _reset_failures(redis) -> None:
    if redis is None:
        return
    try:
        await redis.set(REDIS_KEY_FAILURES, 0, ex=_FAILURES_TTL_S)
        await redis.set(REDIS_KEY_LAST_SUCCESS, int(time.time()), ex=_FAILURES_TTL_S * 24)
    except Exception as exc:
        logger.debug("STORY-4.5: Failure counter reset failed: %s", exc)


async def _should_alert(redis, reason: str) -> bool:
    """Return True iff we have NOT alerted for this reason within the dedup window."""

    if redis is None:
        return True
    try:
        key = REDIS_KEY_ALERTED.format(reason=reason)
        # set-if-not-exists; if we set, we should alert.
        was_set = await redis.set(key, int(time.time()), nx=True, ex=_ALERTED_TTL_S)
        return bool(was_set)
    except Exception as exc:
        logger.debug("STORY-4.5: Alert-dedup check failed: %s", exc)
        return True


# ---------------------------------------------------------------------------
# Sentry escalation (silent no-op if Sentry not configured)
# ---------------------------------------------------------------------------


def _escalate_to_sentry(reason: str, details: dict) -> None:
    """Fire a Sentry ``capture_message`` with the canonical fingerprint + tags."""

    try:
        import sentry_sdk
    except ImportError:  # pragma: no cover - prod always has sentry_sdk
        logger.warning("STORY-4.5: sentry_sdk not installed; skipping escalation")
        return

    try:
        with sentry_sdk.push_scope() as scope:
            scope.level = "fatal"
            scope.set_tag("pncp_breaking_change", reason)
            scope.set_tag("source", "pncp")
            scope.fingerprint = ["pncp_canary", reason]
            scope.set_context("canary", details)
            sentry_sdk.capture_message(
                f"PNCP breaking change detected: {reason}", level="fatal"
            )
        logger.critical("STORY-4.5: PNCP breaking change escalated to Sentry: %s", reason)
    except Exception as exc:
        logger.error("STORY-4.5: Failed to escalate to Sentry: %s", exc, exc_info=True)


# ---------------------------------------------------------------------------
# Canary entry point
# ---------------------------------------------------------------------------


async def run_pncp_canary(
    *,
    client: Optional[httpx.AsyncClient] = None,
    fail_threshold: int = 3,
) -> CanaryResult:
    """Execute one canary sweep. Safe to call from cron or ad-hoc from tests.

    Parameters
    ----------
    client:
        Optional ``httpx.AsyncClient``. When ``None``, a fresh client is built
        with a 10s timeout. Tests pass a mocked client.
    fail_threshold:
        Number of consecutive failed runs before Sentry is paged. Defaults to
        ``PNCP_CANARY_FAIL_THRESHOLD`` from config.
    """

    from config import PNCP_CANARY_FAIL_THRESHOLD, PNCP_CANARY_TIMEOUT_S

    if fail_threshold == 3:  # still the caller default — take from config
        fail_threshold = PNCP_CANARY_FAIL_THRESHOLD

    try:
        from metrics import (
            PNCP_CANARY_CONSECUTIVE_FAILURES,
            PNCP_CANARY_SHAPE_DRIFT,
            PNCP_MAX_PAGE_SIZE_CHANGED,
        )
    except Exception:  # pragma: no cover
        PNCP_MAX_PAGE_SIZE_CHANGED = None  # type: ignore[assignment]
        PNCP_CANARY_CONSECUTIVE_FAILURES = None  # type: ignore[assignment]
        PNCP_CANARY_SHAPE_DRIFT = None  # type: ignore[assignment]

    redis = await _get_redis()
    owned_client = client is None
    if owned_client:
        client = httpx.AsyncClient(timeout=PNCP_CANARY_TIMEOUT_S)

    common_params = {
        "dataInicial": "20260101",
        "dataFinal": "20260101",
        "codigoModalidadeContratacao": 6,
        "pagina": 1,
    }

    try:
        # ----------------------------------------------------------------
        # Probe A — tamanhoPagina=51 MUST be rejected
        # ----------------------------------------------------------------
        try:
            r51 = await client.get(PNCP_ENDPOINT, params={**common_params, "tamanhoPagina": 51})
        except httpx.HTTPError as exc:
            logger.warning("STORY-4.5: Probe A (tamanhoPagina=51) network error: %s", exc)
            r51 = None

        if r51 is not None and r51.status_code < 400:
            reason = "max_page_size_changed"
            details = {
                "reason": reason,
                "probe": "tamanhoPagina=51",
                "status_code": r51.status_code,
                "known_limit": 50,
                "note": "PNCP accepted tamanhoPagina=51 — the historical limit may have risen.",
            }
            if PNCP_MAX_PAGE_SIZE_CHANGED is not None:
                try:
                    PNCP_MAX_PAGE_SIZE_CHANGED.inc()
                except Exception:
                    pass
            alerted = False
            if await _should_alert(redis, reason):
                _escalate_to_sentry(reason, details)
                alerted = True
            return CanaryResult(healthy=False, reason=reason, details=details, alerted=alerted)

        # ----------------------------------------------------------------
        # Probe B — tamanhoPagina=50 MUST succeed AND match schema
        # ----------------------------------------------------------------
        try:
            r50 = await client.get(PNCP_ENDPOINT, params={**common_params, "tamanhoPagina": 50})
            status = r50.status_code
            payload = r50.json() if status < 400 else None
        except httpx.HTTPError as exc:
            logger.warning("STORY-4.5: Probe B (tamanhoPagina=50) network error: %s", exc)
            status = 0
            payload = None
        except (ValueError, json.JSONDecodeError) as exc:
            logger.warning("STORY-4.5: Probe B JSON parse failure: %s", exc)
            status = -1
            payload = None

        if status >= 400 or payload is None:
            count = await _increment_failures(redis)
            if PNCP_CANARY_CONSECUTIVE_FAILURES is not None:
                try:
                    PNCP_CANARY_CONSECUTIVE_FAILURES.set(count)
                except Exception:
                    pass
            alerted = False
            reason = "canary_3x_failed"
            details = {
                "reason": reason,
                "probe": "tamanhoPagina=50",
                "status_code": status,
                "consecutive_failures": count,
                "threshold": fail_threshold,
            }
            if count >= fail_threshold:
                if await _should_alert(redis, reason):
                    _escalate_to_sentry(reason, details)
                    alerted = True
            return CanaryResult(
                healthy=False,
                reason=reason,
                details=details,
                consecutive_failures=count,
                alerted=alerted,
            )

        # ----------------------------------------------------------------
        # Probe B — shape validation (optional — schema may not be shipped)
        # ----------------------------------------------------------------
        schema = _load_schema()
        if schema is not None:
            valid, errors = _validate_shape(payload, schema)
            if not valid:
                reason = "shape_drift"
                details = {
                    "reason": reason,
                    "probe": "tamanhoPagina=50",
                    "status_code": status,
                    "schema_errors": errors[:10],  # cap to keep Sentry payload sane
                }
                if PNCP_CANARY_SHAPE_DRIFT is not None:
                    try:
                        PNCP_CANARY_SHAPE_DRIFT.inc()
                    except Exception:
                        pass
                alerted = False
                if await _should_alert(redis, reason):
                    _escalate_to_sentry(reason, details)
                    alerted = True
                # Shape drift ALSO counts as a failure run to bias towards
                # recovery detection — but we alert immediately (not on 3x).
                count = await _increment_failures(redis)
                return CanaryResult(
                    healthy=False,
                    reason=reason,
                    details=details,
                    consecutive_failures=count,
                    alerted=alerted,
                )

        # ----------------------------------------------------------------
        # Healthy run — reset counters, clear alert dedup on recovery
        # ----------------------------------------------------------------
        await _reset_failures(redis)
        if PNCP_CANARY_CONSECUTIVE_FAILURES is not None:
            try:
                PNCP_CANARY_CONSECUTIVE_FAILURES.set(0)
            except Exception:
                pass
        if redis is not None:
            try:
                await redis.delete(
                    REDIS_KEY_ALERTED.format(reason="max_page_size_changed"),
                    REDIS_KEY_ALERTED.format(reason="canary_3x_failed"),
                    REDIS_KEY_ALERTED.format(reason="shape_drift"),
                )
            except Exception:
                pass
        return CanaryResult(healthy=True, details={"status_code": status})
    finally:
        if owned_client and client is not None:
            try:
                await client.aclose()
            except Exception:
                pass


async def validate_page_size_limit(
    client: httpx.AsyncClient,
    *,
    expected_limit: int = 50,
) -> dict:
    """Lightweight probe reused by ``health.check_source_health``.

    Kept as a separate entrypoint so the fast health check can hit ONLY the
    page-size probe without paying for the full canary (Redis, Sentry, etc.).
    """

    params = {
        "dataInicial": "20260101",
        "dataFinal": "20260101",
        "codigoModalidadeContratacao": 6,
        "pagina": 1,
        "tamanhoPagina": expected_limit + 1,
    }
    try:
        response = await client.get(PNCP_ENDPOINT, params=params)
        drifted = response.status_code < 400
        return {
            "drifted": drifted,
            "probe_status": response.status_code,
            "expected_limit": expected_limit,
        }
    except httpx.HTTPError as exc:
        return {
            "drifted": False,
            "probe_status": None,
            "expected_limit": expected_limit,
            "error": str(exc)[:120],
        }


__all__ = [
    "CanaryResult",
    "PNCP_ENDPOINT",
    "REDIS_KEY_ALERTED",
    "REDIS_KEY_FAILURES",
    "REDIS_KEY_LAST_SUCCESS",
    "run_pncp_canary",
    "validate_page_size_limit",
]
