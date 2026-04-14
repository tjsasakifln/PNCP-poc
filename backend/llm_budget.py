"""STORY-2.11 (EPIC-TD-2026Q2 P0): LLM monthly cost cap with progressive alerts.

Centralizes tracking and rejection logic for LLM spend. All OpenAI calls in
``llm.py`` and ``llm_arbiter`` should flow through ``track_llm_cost()`` and
check ``is_budget_exceeded()`` before making expensive calls.

Storage:
    - Redis counter (monthly key ``llm_cost_month_YYYY_MM``, TTL 32 days)
    - Sentry alerts at 50% / 80% / 100% of the monthly budget (deduped 1h)
    - Hard-reject flag set at 100% (TTL 32d) — cleared on month rollover

Budget source: ``LLM_MONTHLY_BUDGET_USD`` env var (default $100).

Graceful degradation: tudo está try/except. Redis down → tracking é no-op,
budget never exceeded (fail-open). Never blocks a request on infra failure.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def _get_budget_usd() -> float:
    """Lê budget USD do env a cada chamada (permite override em runtime/tests)."""
    try:
        return float(os.getenv("LLM_MONTHLY_BUDGET_USD", "100"))
    except (ValueError, TypeError):
        return 100.0


def _month_key() -> str:
    now = datetime.now(timezone.utc)
    return f"llm_cost_month_{now.year}_{now.month:02d}"


def _budget_exceeded_key() -> str:
    now = datetime.now(timezone.utc)
    return f"llm_budget_exceeded_{now.year}_{now.month:02d}"


def _alert_key(threshold: int) -> str:
    now = datetime.now(timezone.utc)
    return f"llm_budget_alert_{now.year}_{now.month:02d}_{threshold}"


_MONTH_TTL_SECONDS = 32 * 86400  # 32d para cobrir rollover do mês
_ALERT_DEDUP_TTL = 3600  # 1h entre alertas do mesmo threshold


async def track_llm_cost(cost_usd: float) -> float:
    """Incrementa contador mensal em Redis e dispara alertas progressivos.

    Args:
        cost_usd: custo incremental desta chamada (>=0).

    Returns:
        Total acumulado no mês (USD), ou 0.0 se Redis indisponível ou erro.

    Fire-and-forget safe: qualquer exceção é logada e retorna 0.0.
    """
    if cost_usd <= 0:
        return 0.0
    try:
        from redis_pool import get_redis_pool

        redis = await get_redis_pool()
        if redis is None:
            return 0.0

        key = _month_key()
        # incrbyfloat é atômico (único worker incrementando por vez é OK,
        # múltiplos workers ficam consistentes no server-side).
        total = await redis.incrbyfloat(key, cost_usd)
        # Garante TTL de 32d (no-op se já tiver TTL).
        try:
            ttl = await redis.ttl(key)
            if ttl is None or ttl < 0:
                await redis.expire(key, _MONTH_TTL_SECONDS)
        except Exception:
            # Se ttl falhar, seta direto — expire é idempotente
            await redis.expire(key, _MONTH_TTL_SECONDS)

        total_f = float(total)
        budget = _get_budget_usd()
        pct = (total_f / budget * 100.0) if budget > 0 else 0.0

        # Atualiza gauge Prometheus
        try:
            from metrics import LLM_BUDGET_USD_MTD

            LLM_BUDGET_USD_MTD.set(total_f)
        except Exception:
            pass

        await _fire_alerts_if_crossed(pct, total_f, budget, redis)
        return total_f
    except Exception as e:
        logger.warning("llm_budget.track_llm_cost failed: %s", e)
        return 0.0


async def _fire_alerts_if_crossed(
    pct: float, total: float, budget: float, redis
) -> None:
    """Emite Sentry capture_message em 50/80/100% com dedup via Redis SETNX."""
    thresholds = [(50, "warning"), (80, "error"), (100, "fatal")]
    for threshold, level in thresholds:
        if pct < threshold:
            continue
        alert_k = _alert_key(threshold)
        try:
            # SET ... NX EX=3600 — só seta se ainda não existe, TTL 1h
            set_ok = await redis.set(alert_k, "1", nx=True, ex=_ALERT_DEDUP_TTL)
        except Exception as e:
            logger.debug("llm_budget: alert dedup SET failed: %s", e)
            set_ok = False

        if set_ok:
            try:
                import sentry_sdk

                sentry_sdk.capture_message(
                    f"LLM budget {threshold}% reached: ${total:.2f}/${budget:.2f}",
                    level=level,
                    tags={
                        "llm_budget_threshold_pct": str(threshold),
                        "llm_budget_month": _month_key(),
                    },
                )
            except Exception as e:
                logger.debug("llm_budget: sentry capture failed: %s", e)

        # Hard-reject flag é setado em 100% independente do Sentry
        if threshold == 100:
            try:
                await redis.set(
                    _budget_exceeded_key(), "1", ex=_MONTH_TTL_SECONDS
                )
            except Exception as e:
                logger.debug("llm_budget: failed to set exceeded flag: %s", e)


async def is_budget_exceeded() -> bool:
    """Retorna True se o budget mensal já atingiu 100% neste mês.

    Graceful: Redis down → False (fail-open, nunca bloqueia sem dado).
    """
    try:
        from redis_pool import get_redis_pool

        redis = await get_redis_pool()
        if redis is None:
            return False
        flag = await redis.get(_budget_exceeded_key())
        return bool(flag)
    except Exception as e:
        logger.debug("llm_budget.is_budget_exceeded failed: %s", e)
        return False


def is_budget_exceeded_sync() -> bool:
    """Versão sync para uso em ``asyncio.to_thread`` (LLM arbiter).

    Usa ``get_sync_redis`` do redis_pool. Fail-open em qualquer erro.
    """
    try:
        from redis_pool import get_sync_redis

        redis = get_sync_redis()
        if redis is None:
            return False
        flag = redis.get(_budget_exceeded_key())
        return bool(flag)
    except Exception as e:
        logger.debug("llm_budget.is_budget_exceeded_sync failed: %s", e)
        return False


async def get_cost_snapshot() -> dict:
    """Snapshot para o endpoint ``GET /v1/admin/llm-cost`` (AC4).

    Returns:
        dict com: month_to_date_usd, budget_usd, pct_used,
        projected_end_of_month_usd, month, exceeded (bool).
    """
    mtd = 0.0
    exceeded = False
    try:
        from redis_pool import get_redis_pool

        redis = await get_redis_pool()
        if redis is not None:
            try:
                raw = await redis.get(_month_key())
                mtd = float(raw) if raw else 0.0
            except Exception as e:
                logger.debug("llm_budget.snapshot read mtd failed: %s", e)
            try:
                flag = await redis.get(_budget_exceeded_key())
                exceeded = bool(flag)
            except Exception:
                pass
    except Exception as e:
        logger.debug("llm_budget.snapshot redis init failed: %s", e)

    budget = _get_budget_usd()
    now = datetime.now(timezone.utc)
    # Dias no mês (aprox via 28..31, mais simples: dia 1 do mês seguinte - 1)
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    days_in_month = (next_month - now.replace(day=1)).days
    day_of_month = now.day
    projected = (
        (mtd / day_of_month) * days_in_month if day_of_month > 0 else mtd
    )

    pct = round((mtd / budget * 100.0), 2) if budget > 0 else 0.0
    return {
        "month_to_date_usd": round(mtd, 4),
        "budget_usd": round(budget, 2),
        "pct_used": pct,
        "projected_end_of_month_usd": round(projected, 2),
        "month": _month_key(),
        "exceeded": exceeded,
    }
