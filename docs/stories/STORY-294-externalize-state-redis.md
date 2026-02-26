# STORY-294: Externalize State to Redis

**Sprint:** 1 — Make It Reliable
**Size:** L (8-16h)
**Root Cause:** RC-3
**Depends on:** STORY-292
**Industry Standard:** [State Externalization Pattern](https://12factor.net/processes), [Microsoft — External Configuration Store](https://learn.microsoft.com/en-us/azure/architecture/patterns/external-configuration-store)

## Contexto

O backend roda com `WEB_CONCURRENCY=2` (2 workers Gunicorn). Três estruturas in-memory são compartilhadas APENAS dentro de um worker:

1. `_active_trackers: dict[str, ProgressTracker]` em `progress.py` — SSE streams
2. `_background_results: dict[str, BuscaResponse]` em `routes/search.py` — resultados async
3. `_arbiter_cache: dict[str, LLMClassification]` em `llm_arbiter.py` — cache LLM

Se o POST /buscar roda no worker 1 e o GET /buscar-progress/{id} cai no worker 2, o tracker não existe. Resultado: SSE fica em espera infinita ou retorna 404.

## Acceptance Criteria

- [ ] AC1: `_active_trackers` substituído por Redis pub/sub — tracker publica eventos, SSE consome
- [ ] AC2: `_background_results` substituído por Redis hash com TTL 30min (`search_result:{id}`)
- [ ] AC3: `_arbiter_cache` substituído por Redis hash com TTL 1h (`arbiter:{sector}:{hash}`)
- [ ] AC4: SSE endpoint funciona independente de qual worker recebe o request
- [ ] AC5: Resultado disponível via `/v1/search/{id}/results` independente de worker
- [ ] AC6: Graceful fallback: se Redis indisponível, in-memory como fallback (não crash)
- [ ] AC7: Prometheus metric: `smartlic_state_store_errors_total` (labels: store, operation)
- [ ] AC8: TTL cleanup: Redis EXPIRE em todas as chaves temporárias
- [ ] AC9: Testes existentes continuam passando
- [ ] AC10: Load test: 10 buscas simultâneas com WEB_CONCURRENCY=2 — 100% entregam resultado

## Technical Design

```python
# Redis pub/sub for progress events
class RedisProgressTracker:
    def __init__(self, search_id: str, redis: Redis):
        self._channel = f"progress:{search_id}"
        self._redis = redis

    async def emit(self, event: dict):
        await self._redis.publish(self._channel, json.dumps(event))

    async def subscribe(self) -> AsyncIterator[dict]:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self._channel)
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
```

## Files to Change

- `backend/progress.py` — RedisProgressTracker (pub/sub)
- `backend/routes/search.py` — Redis hash para background results
- `backend/llm_arbiter.py` — Redis hash para arbiter cache
- `backend/redis_client.py` — helper functions para state operations
- `backend/config.py` — `STATE_STORE_REDIS_PREFIX` config

## Definition of Done

- [ ] SSE funciona com WEB_CONCURRENCY=2 em 100% dos casos
- [ ] Zero "tracker not found" errors com multiple workers
- [ ] Todos os testes passando
- [ ] PR merged
