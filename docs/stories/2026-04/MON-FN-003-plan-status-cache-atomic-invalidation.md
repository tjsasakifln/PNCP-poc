# MON-FN-003: Plan Status Cache Invalidação Atômica (Redis Pub/Sub)

**Priority:** P0
**Effort:** M (3 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 2 (06–12/mai)
**Sprint Window:** Sprint 2 (bloqueador para MON-FN-004)
**Dependências bloqueadoras:** MON-FN-002 (webhook DLQ confiável antes de Pub/Sub no commit)

---

## Contexto

`backend/quota/quota_core.py:28-71` mantém `_plan_status_cache: dict[str, tuple[str, float]]` com TTL puro `PLAN_STATUS_CACHE_TTL=300` (5 min). Função `invalidate_plan_status_cache(user_id)` (linha 59) é chamada localmente por handlers Stripe webhook em `webhooks/handlers/subscription.py` e `invoice.py`, mas **a invalidação é local-process-only**:

- Backend Railway tem 1 worker em Hobby (atualmente WEB_CONCURRENCY=1 pós-incident PR #529, mas está sendo elevado para 2-4 — memory `reference_railway_hobby_plan_actual`).
- Quando WEB_CONCURRENCY > 1 (ou multi-replica), webhook commit no worker A não invalida cache no worker B.
- Resultado: usuário paga checkout → webhook chega no worker A → `plan_type='paid'` em DB → cache invalidated no worker A. Mas próxima request do user pode rotear para worker B onde cache ainda diz `'free_trial'` → paywall_hit incorreto até TTL expirar (até 5s, podendo chegar a 5min).

Este é o **bug da race condition `/planos/obrigado`** que MON-FN-004 vai mitigar com polling client-side. Esta story (MON-FN-003) elimina a causa raiz: **invalidação atômica entre processes via Redis Pub/Sub**.

**Por que P0:** UX falso positivo pós-pagamento é o pior momento de churn. Benchmark Fortune-500: invalidação cross-process via Pub/Sub é mandatória em qualquer cache compartilhado de billing state. Sem isto, MON-FN-004 (polling) é band-aid.

**Paths críticos:**
- `backend/quota/quota_core.py` (L24-71: cache + invalidate)
- `backend/services/billing.py` (publica invalidação no commit)
- `backend/cache/redis.py` ou novo `backend/cache/pubsub.py` (subscriber init)
- `backend/main.py` (startup: subscribe loop)

---

## Acceptance Criteria

### AC1: Redis Pub/Sub channel `cache:invalidate:plan_status:{user_id}`

Given que webhook handler atualiza `profiles.plan_type`,
When o commit DB é confirmado,
Then publica em canal Redis `cache:invalidate:plan_status:{user_id}` o payload `{"user_id": ..., "plan_id": ..., "ts": iso8601}`.

- [ ] Em `backend/services/billing.py` (e/ou `webhooks/handlers/subscription.py`, `invoice.py`), após cada UPDATE de `plan_type`, chamar:
```python
async def publish_plan_invalidation(user_id: str, new_plan_id: str) -> None:
    """Atomic cross-process plan status cache invalidation via Redis Pub/Sub.

    MON-FN-003: Subscribers in quota_core.py invalidate _plan_status_cache locally.
    """
    from cache.redis import get_redis_client  # existing helper
    import json, time
    payload = {
        "user_id": user_id,
        "plan_id": new_plan_id,
        "published_at": time.time(),  # epoch seconds — used to compute lag metric
    }
    try:
        redis = await get_redis_client()
        await redis.publish(f"cache:invalidate:plan_status:{user_id}", json.dumps(payload))
        smartlic_plan_cache_invalidation_published_total.inc()
    except Exception as e:
        logger.warning(f"Pub/Sub publish failed: {e} — relying on TTL fallback")
        # Fail-open: TTL still kicks in within 5 min
```
- [ ] Channel pattern: `cache:invalidate:plan_status:{user_id}` (per-user) OR wildcard `cache:invalidate:plan_status:*` (broadcast). Decisão @architect: per-user (subscriber filtra por padrão `cache:invalidate:plan_status:*` via PSUBSCRIBE — escala se ficar caro com 10k users)
- [ ] Publish chamado APÓS commit SQL (não em transaction begin) — usar `try/finally` para garantir
- [ ] Counter `smartlic_plan_cache_invalidation_published_total` incrementa em sucesso

### AC2: Subscriber em quota_core.py invalida cache local

Given startup do backend,
When app inicializa,
Then um background task subscribe em `cache:invalidate:plan_status:*` e remove entry do `_plan_status_cache` ao receber mensagem.

- [ ] Em `backend/cache/pubsub.py` (NOVO):
```python
import asyncio
import json
import logging
from cache.redis import get_redis_client
from quota.quota_core import _plan_status_cache, _plan_status_cache_lock, invalidate_plan_status_cache_local
import time

logger = logging.getLogger(__name__)

async def plan_invalidation_subscriber(stop_event: asyncio.Event) -> None:
    """Subscribe to cache:invalidate:plan_status:* and invalidate local cache.

    Runs as a background asyncio.Task started in main.py:lifespan.
    """
    redis = await get_redis_client()
    pubsub = redis.pubsub()
    await pubsub.psubscribe("cache:invalidate:plan_status:*")
    logger.info("Plan invalidation subscriber started")
    try:
        async for message in pubsub.listen():
            if stop_event.is_set():
                break
            if message["type"] != "pmessage":
                continue
            try:
                payload = json.loads(message["data"])
                user_id = payload["user_id"]
                published_at = payload.get("published_at", time.time())
                lag = max(0, time.time() - published_at)
                smartlic_plan_cache_invalidation_lag_seconds.observe(lag)

                invalidate_plan_status_cache_local(user_id)
                smartlic_plan_cache_invalidation_received_total.inc()
            except Exception as e:
                logger.warning(f"Subscriber message handler error: {e}")
    finally:
        await pubsub.punsubscribe("cache:invalidate:plan_status:*")
        await pubsub.aclose()
```
- [ ] Renomear `quota_core.invalidate_plan_status_cache` → `invalidate_plan_status_cache_local` (clareza); criar wrapper `invalidate_plan_status_cache(user_id)` que faz BOTH local + publish (para callers existentes)
- [ ] Subscriber start em `backend/main.py:lifespan`:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    sub_task = asyncio.create_task(plan_invalidation_subscriber(stop_event))
    yield
    stop_event.set()
    await asyncio.wait_for(sub_task, timeout=5)
```
- [ ] Resilience: se subscriber crashar, lifespan reinicia (max 3 attempts, then log + continue without Pub/Sub — TTL fallback)

### AC3: Histograma `smartlic_plan_cache_invalidation_lag_seconds`

Given mensagem Pub/Sub recebida,
When subscriber processa,
Then registra histograma do delta entre `published_at` (publisher) e `received_at` (subscriber).

- [ ] Histograma `smartlic_plan_cache_invalidation_lag_seconds` com buckets `[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5]`
- [ ] Counter `smartlic_plan_cache_invalidation_received_total` (incrementa em cada mensagem processada)
- [ ] Counter `smartlic_plan_cache_invalidation_failed_total{reason}` (publish_error|subscribe_error|json_decode_error)
- [ ] Target: p99 lag < 500ms (validado em load test)

### AC4: TTL fallback mantido

Given que Pub/Sub falha (Redis indisponível),
When subscriber não recebe mensagem,
Then TTL 5min do `_plan_status_cache` ainda invalida eventualmente.

- [ ] Não remover `PLAN_STATUS_CACHE_TTL=300` (mantém belt-and-suspenders)
- [ ] Test: simular Redis down → publish falha (logged, counter incrementado) → TTL ainda funciona
- [ ] Documentar trade-off: invalidação atômica = best effort; TTL = guaranteed
- [ ] Métrica `smartlic_plan_cache_ttl_evictions_total` (entries removidas por TTL vs Pub/Sub) — alvo: <10% TTL (>90% atomic)

### AC5: Update todos os call sites de `invalidate_plan_status_cache`

Given funções existentes que chamam `invalidate_plan_status_cache(user_id)`,
When MON-FN-003 deploy,
Then todas chamadas passam a publicar Pub/Sub também.

- [ ] Grep por `invalidate_plan_status_cache(` em `backend/`:
  - `webhooks/handlers/subscription.py` (após UPDATE plan_type)
  - `webhooks/handlers/invoice.py` (após UPDATE em payment_failed/succeeded)
  - `services/billing.py` (após plan upgrade)
  - `routes/admin.py` (manual plan changes)
- [ ] Cada call passa pelo wrapper que faz local + publish
- [ ] Função `clear_plan_capabilities_cache` (linha 32 import em `webhooks/stripe.py`) — separada, NÃO mexer (esta é cache de plano definitions, não de user plan status)

### AC6: Feature flag rollback

Given que Pub/Sub introduz failure mode novo,
When emergência,
Then setar env var `PLAN_CACHE_PUBSUB_ENABLED=false` desliga publish; sistema cai para TTL puro (estado anterior).

- [ ] Env var `PLAN_CACHE_PUBSUB_ENABLED=true` default; `false` em rollback
- [ ] Em `publish_plan_invalidation`: early return if flag false
- [ ] Subscriber: se flag false em startup, não inicializa task (evita conexão Redis desnecessária)
- [ ] Documentar em `docs/operations/feature-flags.md`

### AC7: Testes

- [ ] Unit `backend/tests/quota/test_plan_cache_invalidation_pubsub.py`:
  - [ ] Publish chamado após webhook handler success (mock subscription.updated)
  - [ ] Publish payload contém `user_id`, `plan_id`, `published_at`
  - [ ] Subscriber recebe message → cache local removido
  - [ ] Lag histograma incrementado com valor correto
  - [ ] Redis down → publish loga warning + counter `failed_total{reason=publish_error}` incrementado
  - [ ] Subscriber crash → lifespan reinicia (max 3x)
  - [ ] Feature flag false → publish noop, subscriber não inicia
- [ ] Integration: 2 workers simulados (process A faz webhook, process B serve user request) — validar que process B vê cache invalidado em <500ms
- [ ] Load test: 100 webhooks/sec → p99 lag < 500ms (Locust + Redis local)
- [ ] Cobertura ≥85%

---

## Scope

**IN:**
- Redis Pub/Sub publish em todos call sites de `invalidate_plan_status_cache`
- Subscriber background task em `quota_core` (lifespan-managed)
- Histograma de lag + counters
- Feature flag rollback
- Refactor mínimo de `invalidate_plan_status_cache` para wrapper (local+publish)

**OUT:**
- Migrar para Redis Streams (over-engineering pre-revenue)
- Cache de capabilities (separado, não relacionado)
- Cache L2 Supabase (search_results_cache — fora de escopo desta story)
- Distributed lock para invalidação (não necessário; idempotente)
- Multi-region replication (Hobby não suporta)

---

## Definition of Done

- [ ] Publish disparado após cada webhook commit (validar via log + counter)
- [ ] Subscriber rodando como background task em `lifespan` (verificar via `/health` que reporta task status)
- [ ] Histograma `smartlic_plan_cache_invalidation_lag_seconds` p99 < 500ms em staging
- [ ] Counter `smartlic_plan_cache_ttl_evictions_total / smartlic_plan_cache_invalidation_received_total` < 0.1 (>90% atomic)
- [ ] Feature flag `PLAN_CACHE_PUBSUB_ENABLED` documentada e testada
- [ ] Load test: 100 webhooks/sec sem degradar p99
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] CodeRabbit clean
- [ ] Smoke test em staging: trigger Stripe checkout test mode → assert cache invalidated em <500ms (medir via timestamps)
- [ ] Rollback runbook documentado
- [ ] Memory existente atualizada com nota sobre Pub/Sub (cache não é mais TTL puro)

---

## Dev Notes

### Padrões existentes a reutilizar

- **Redis client:** `backend/cache/redis.py::get_redis_client()` (existente, conexão pool)
- **Lifespan management:** `backend/main.py::lifespan` (FastAPI app contextmanager)
- **Logger:** `from log_sanitizer import get_sanitized_logger` (mascara user_id)
- **Sentry:** capture exception em subscriber crash, mas não em publish failure (publish é fail-open — TTL cobre)

### Funções afetadas

- `backend/quota/quota_core.py` (renomear `invalidate_plan_status_cache` → `_invalidate_plan_status_cache_local`; criar wrapper público)
- `backend/cache/pubsub.py` (NOVO)
- `backend/services/billing.py` (call sites)
- `backend/webhooks/handlers/{subscription,invoice}.py` (já chama invalidate; passa pelo wrapper)
- `backend/main.py` (lifespan: start/stop subscriber)
- `backend/metrics.py` (histograma + counters)
- `backend/config.py` (env var `PLAN_CACHE_PUBSUB_ENABLED`)

### Pattern: per-user vs broadcast channel

Decisão: **PSUBSCRIBE wildcard** `cache:invalidate:plan_status:*` no subscriber. Vantagens:
- Subscriber não precisa saber quais users existem
- Single subscription suporta arbitrary user count
- Trade-off: cada worker recebe TODAS as invalidações (não só dos seus users)

Alternativa (não escolhida): single channel `cache:invalidate:plan_status` com payload incluindo user_id — equivalente em prática, mas menos legível em monitoring (Redis stats por canal).

### Testing Standards

- Test file: `backend/tests/quota/test_plan_cache_invalidation_pubsub.py`
- Mock Redis via `fakeredis` (já em requirements-dev) — `@pytest.fixture async def fake_redis()`
- 2 subscriber instances simulando 2 workers; publish em A, assert invalidação em B
- `freezegun` para validar lag observation
- Anti-hang: pytest-timeout 30s; subscriber tests usam `asyncio.wait_for(timeout=5)` para evitar deadlock
- E2E real Redis em CI: opcional (evita Redis fixture em CI; mock cobre)

---

## Risk & Rollback

### Triggers de rollback
- Lag p99 > 1s sustained (Pub/Sub gargalo — Redis under-provisioned)
- Subscriber crash rate >1/dia (bug em handler)
- Counter `smartlic_plan_cache_invalidation_failed_total{reason=publish_error}` rate > 1/min sustained (Redis flaky)
- User reports paywall pós-pagamento aumentam pós-deploy (sinal pior, não melhor)

### Ações de rollback
1. **Imediato:** Railway env var `PLAN_CACHE_PUBSUB_ENABLED=false` (deploy zero-downtime via reload)
2. **Verificação:** após flag, publish e subscriber viram noop; cache cai para TTL puro (estado pré-MON-FN-003)
3. **Diagnóstico:** Sentry breadcrumb + Prometheus dashboard mostram causa raiz (Redis, network, code)
4. **Re-enable:** após fix, flip flag de volta; smoke test em staging primeiro

### Compliance
- Pub/Sub payload contém `user_id` (UUID) — não PII direta. Audit: incluir em `analytics_events` retention 90d se admin desejar (não obrigatório)
- LGPD export (MON-FN-010): cache state não é persistido — não precisa exportar

---

## Dependencies

### Entrada
- **MON-FN-002** (DLQ): garante webhook commit confiável antes de publish — sem DLQ, falha de webhook = stale cache silently
- Redis disponível em prod (já existe; Upstash/Railway)
- `cache/redis.py` helper (existente)

### Saída
- **MON-FN-004** (`/planos/obrigado` polling): polling client-side complementa Pub/Sub server-side; juntas resolvem race condition end-to-end
- **MON-FN-008** (free tier downsell): downgrade trial→free também precisa invalidar atomicamente

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "Plan Status Cache Invalidação Atômica (Redis Pub/Sub)" — solução + protocolo |
| 2 | Complete description | Y | Cita memory `reference_railway_hobby_plan_actual` + linhas código (quota_core.py:28) |
| 3 | Testable acceptance criteria | Y | 7 ACs incluindo load test 100 webhooks/sec + 2 worker simulation |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui Streams/L2 cache (não reescopar) |
| 5 | Dependencies mapped | Y | Entrada MON-FN-002 (DLQ); Saída MON-FN-004 (polling) e MON-FN-008 |
| 6 | Complexity estimate | Y | M (3 dias) coerente — Pub/Sub + subscriber + lifespan + tests |
| 7 | Business value | Y | UX falso positivo pós-pagamento = pior momento de churn |
| 8 | Risks documented | Y | Triggers + feature flag rollback + TTL fallback explícito (belt-and-suspenders) |
| 9 | Criteria of Done | Y | p99 lag <500ms, smoke test, rollback runbook |
| 10 | Alignment with PRD/Epic | Y | EPIC gap #3; explicita relação MON-FN-002 → 003 → 004 sequence |

### Observations
- Decisão arquitetural PSUBSCRIBE wildcard (vs per-user) bem documentada com trade-offs
- TTL fallback mantido (não removido) é insight de resilience
- Histograma `smartlic_plan_cache_invalidation_lag_seconds` com buckets corretos (sub-second focus)
- Feature flag `PLAN_CACHE_PUBSUB_ENABLED` permite rollback zero-downtime

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — invalidação atômica cross-process via Redis Pub/Sub | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). P0 race condition root-cause fix; Status Draft → Ready. | @po (Pax) |
