"""STORY-2.10 (EPIC-TD-2026Q2 P0): Rate limit para endpoints públicos sem auth.

Factory que retorna FastAPI Depends callable com limite configurável.
Identifica caller por último IP de X-Forwarded-For (atrás do Railway proxy) ou
``user_id`` (quando houver auth opcional). Retorna 429 com header Retry-After
quando o limite é excedido.

Uso::

    from public_rate_limit import rate_limit_public

    router = APIRouter(
        dependencies=[Depends(rate_limit_public(limit_unauth=60, endpoint_name="stats_public"))],
    )

Métricas:
    - ``smartlic_rate_limit_hits_total{endpoint, caller_type}`` — counter

Alertas:
    - Sentry ``rate_limit_burst`` quando um mesmo caller excede >100 hits/min
      (deduplicado por TTL de 60s).
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable, Optional

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# In-memory dedup / burst tracker (per-process). Graceful no-op fallback
# quando Redis/Sentry estão indisponíveis.
_burst_counters: dict[str, list[float]] = defaultdict(list)
_last_sentry_alert: dict[str, float] = {}

# Thresholds
_BURST_WINDOW_S = 60.0  # janela rolante de 1 min
_BURST_ALERT_THRESHOLD = 100  # >100 hits/min dispara Sentry
_SENTRY_DEDUP_TTL_S = 60.0  # dedup por 60s


def _extract_ip(request: Request) -> str:
    """Extrai IP do caller respeitando X-Forwarded-For do Railway proxy.

    Preferimos o *último* IP do XFF (o proxy da borda é o mais confiável).
    Falls back para ``request.client.host`` e por fim ``"unknown"``.
    """
    xff = request.headers.get("X-Forwarded-For") or request.headers.get("x-forwarded-for")
    if xff:
        ips = [ip.strip() for ip in xff.split(",") if ip.strip()]
        if ips:
            return ips[-1]
    if request.client and getattr(request.client, "host", None):
        return request.client.host
    return "unknown"


def _track_burst_and_alert(key: str, caller_type: str, caller_id: str, endpoint: str) -> None:
    """Conta hits em janela rolante e dispara alerta Sentry se >100/min.

    Usa dedup in-memory (TTL 60s) para não spammar Sentry.
    Sentry é importado lazily para nunca quebrar a request em dev/tests sem SDK.
    """
    now = time.monotonic()
    bucket = _burst_counters[key]
    # Purga entries antigas da janela
    cutoff = now - _BURST_WINDOW_S
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    bucket.append(now)

    if len(bucket) <= _BURST_ALERT_THRESHOLD:
        return

    last = _last_sentry_alert.get(key, 0.0)
    if now - last < _SENTRY_DEDUP_TTL_S:
        return
    _last_sentry_alert[key] = now

    try:
        import sentry_sdk

        sentry_sdk.capture_message(
            f"rate_limit_burst endpoint={endpoint} "
            f"{caller_type}={caller_id} hits_per_min={len(bucket)}",
            level="warning",
        )
    except Exception as e:
        logger.debug("public_rate_limit: sentry alert failed: %s", e)


def rate_limit_public(
    *,
    limit_unauth: int = 60,
    limit_auth: int = 600,
    endpoint_name: Optional[str] = None,
) -> Callable:
    """Factory que retorna uma FastAPI dependency de rate limit público.

    Args:
        limit_unauth: requests/min permitidos para caller não autenticado (por IP).
        limit_auth: requests/min permitidos para caller autenticado (por user_id).
        endpoint_name: label para métricas. Se ``None`` usa ``request.url.path``.

    Returns:
        Async callable pronto para ``Depends(...)``. Levanta ``HTTPException(429)``
        com ``Retry-After: 60`` quando o limite é excedido.

    A chave de rate limit reusa a infra existente em ``rate_limiter.RateLimiter``
    (token-bucket per-minute com fallback in-memory quando Redis está fora).
    """

    async def _check(request: Request):
        # Descobrir caller. Aceitamos user_id em request.state (auth opcional)
        # ou via JWT sub claim (se middleware adicionou).
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            key = f"rl_pub:user:{user_id}"
            limit = limit_auth
            caller_type = "user"
            caller_id = str(user_id)
        else:
            ip = _extract_ip(request)
            key = f"rl_pub:ip:{ip}"
            limit = limit_unauth
            caller_type = "ip"
            caller_id = ip

        # Reusa RateLimiter existente (Redis + in-memory fallback, por-minuto).
        try:
            from rate_limiter import rate_limiter as _rl

            allowed, retry_after = await _rl.check_rate_limit(key, limit)
        except Exception as e:
            # Nunca quebrar a request por erro de rate limiter — fail-open.
            logger.warning("public_rate_limit: check failed (fail-open): %s", e)
            return None

        ep = endpoint_name or request.url.path

        # Sempre rastreia burst (mesmo requests permitidas contam pro alerta).
        _track_burst_and_alert(key, caller_type, caller_id, ep)

        if not allowed:
            try:
                from metrics import RATE_LIMIT_HITS

                RATE_LIMIT_HITS.labels(endpoint=ep, caller_type=caller_type).inc()
            except Exception:
                pass

            retry_sec = int(retry_after) if retry_after else 60
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "retry_after_sec": retry_sec,
                    "endpoint": ep,
                },
                headers={"Retry-After": str(retry_sec)},
            )
        return None

    return _check
