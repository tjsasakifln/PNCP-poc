# STORY-276: Migrar Progress Tracking de Redis Pub/Sub para Redis Streams

**Priority:** P0 BLOCKER
**Effort:** 2-3 days
**Squad:** @dev + @architect + @qa
**Replaces:** STORY-268 (progress bar fix) — abordagem anterior falhava por tratar sintoma

## Fundamentacao (Web Research Validada)

### Por que Redis Pub/Sub causa "barra travada em 10%"

Redis Pub/Sub e **at-most-once delivery** (fire-and-forget):
- Mensagens publicadas ANTES do subscriber conectar sao **permanentemente perdidas**
- Nao ha replay, acknowledgment, nem retry
- Fonte: [Redis Pub/Sub docs](https://redis.io/docs/latest/develop/pubsub/)

Com Gunicorn `WEB_CONCURRENCY=2`:
1. POST /buscar cria tracker no worker A, emite eventos
2. GET /buscar-progress/{id} (SSE) pode cair no worker B
3. Worker B recria tracker via Redis metadata, faz subscribe no canal
4. Eventos emitidos entre criacao e subscribe sao **PERDIDOS**
5. Progress bar fica em 10% ate o proximo evento chegar (se chegar)

### Por que Redis Streams resolve

| Feature | Pub/Sub | Streams |
|---------|---------|---------|
| Persistencia | Nenhuma | Append-only log |
| Mensagens perdidas | Perdidas para sempre | Replay de qualquer ponto |
| Consumer groups | Nao | Sim |
| Delivery guarantee | At-most-once | At-least-once |

Fonte: [Redis Streams vs Pub/Sub (Jan 2026)](https://oneuptime.com/blog/post/2026-01-21-redis-streams-vs-pubsub/view)

Pattern recomendado pela comunidade:
```
Producer (qualquer worker): XADD progress:{search_id} * stage "fetching" progress "25"
SSE endpoint (qualquer worker): XREAD BLOCK 5000 STREAMS progress:{search_id} $last_id
Cleanup: EXPIRE progress:{search_id} 300
```
Fonte: [ITNEXT: Scalable Real-Time Apps](https://itnext.io/scalable-real-time-apps-with-python-and-redis-exploring-asyncio-fastapi-and-pub-sub-79b56a9d2b94)

### ARQ esta em maintenance-only mode

ARQ nao tera novos fixes ([Issue #437](https://github.com/python-arq/arq/issues/437)):
- PR #492 (Redis Streams PoC) nunca foi mergeado
- Successor oficial: [streaq](https://github.com/tastyware/streaq)
- Health check key compartilhada e deletada por qualquer worker ao fechar ([Issue #291](https://github.com/python-arq/arq/issues/291))
- Job status e "entirely unreliable" ([Issue #342](https://github.com/samuelcolvin/arq/issues/342))

**Decisao:** Nao migrar ARQ agora (risco alto), mas substituir o pub/sub do ProgressTracker por Streams.

## Acceptance Criteria

### AC1: ProgressTracker usa Redis Streams (nao Pub/Sub)
- [x] `progress.py`: `_publish_to_redis()` usa `XADD` em vez de `PUBLISH`
- [x] Channel format: `smartlic:progress:{search_id}:stream`
- [x] Cada evento = um entry no stream com campos: `stage`, `progress`, `message`, `detail_json`
- [x] `EXPIRE` no stream key com TTL de 5 minutos apos `complete`/`error`/`degraded`

### AC2: SSE Consumer usa XREAD BLOCK (nao subscribe)
- [x] `routes/search.py`: SSE endpoint usa `XREAD BLOCK 15000` em vez de `pubsub.get_message()`
- [x] Primeiro XREAD com `id=0` (le TODO o historico desde o inicio)
- [x] Subsequent XREADs com `id=$last_received_id`
- [x] Se subscriber conecta tarde, recebe TODOS os eventos acumulados (replay)
- [x] Heartbeat: se XREAD retorna vazio (timeout), yield `: heartbeat\n\n`

### AC3: Fallback in-memory preservado
- [x] Se Redis indisponivel, continua usando asyncio.Queue (comportamento atual)
- [x] `use_redis` flag decide entre Streams e Queue
- [x] Sem regressao para deploy single-worker sem Redis

### AC4: Eliminado `subscribe_to_events()` e toda logica pub/sub
- [x] Remover `subscribe_to_events()` de progress.py
- [x] Remover bloco `if pubsub:` do SSE endpoint
- [x] Simplificar para: "try Streams first, fallback to queue"

### AC5: Teste end-to-end cross-worker
- [x] Teste simula: tracker created in "worker A", SSE reads from "worker B"
- [x] Verifica que TODOS os eventos sao recebidos (zero perda)
- [x] Verifica que subscriber tardio recebe historico completo
- [x] Verifica cleanup: stream key removido apos TTL

## Impacto Esperado

- Progress bar avanca de 10% → 15% → 25% → ... → 100% sem gaps
- Subscriber tardio recebe historico (nao mais "stuck at 10%")
- Elimina race condition pub/sub que causava 11+ tentativas de fix sem resultado

## Files to Modify

| File | Change |
|------|--------|
| `backend/progress.py` | XADD em vez de PUBLISH, remover subscribe_to_events |
| `backend/routes/search.py` | XREAD BLOCK em vez de pubsub.get_message |
| `backend/tests/test_progress_streams.py` | **NEW** — testes de Streams |
| `backend/tests/test_progress.py` | Atualizar mocks |

## Riscos Mitigados

| Risco | Mitigacao |
|-------|----------|
| Redis nao suporta Streams | Redis 5.0+ (Upstash/Railway suportam). Verificar com `redis.execute_command("XINFO", "HELP")` |
| Performance de XADD vs PUBLISH | XADD e ~10% mais lento que PUBLISH, mas a persistencia compensa. Em volumes SmartLic (<1000 eventos/busca), irrelevante |
| Fallback quebra | AC3 garante asyncio.Queue como fallback |
