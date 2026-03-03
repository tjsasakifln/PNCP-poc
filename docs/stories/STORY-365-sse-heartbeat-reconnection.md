# STORY-365 — SSE Heartbeat & Auto-Reconnection

**Status:** pending
**Priority:** P2 — Production (resiliencia de conexao SSE)
**Origem:** Conselho CTO Advisory — Analise de exports quebrados (2026-03-03)
**Componentes:** backend/routes/search.py, backend/progress.py, frontend/app/api/buscar-progress/route.ts, frontend/app/buscar/hooks/useUfProgress.ts
**Depende de:** STORY-363 (Async Pipeline)
**Bloqueia:** nenhuma
**Estimativa:** ~4h

---

## Contexto

Apos STORY-363 (pipeline async no Worker), o SSE (`GET /buscar-progress/{id}`) torna-se apenas um reporter de progresso, nao mais uma lifeline. Porem, o SSE ainda pode desconectar por timeout de proxies intermediarios (Railway, Cloudflare). Quando desconecta:

1. Frontend perde atualizacoes de progresso (barra de progresso congela)
2. Se CRIT-012 ja implementou heartbeat a cada 15s, ainda pode desconectar apos 5 min (Railway hard cap)
3. Apos desconexao, nao ha reconnect automatico — usuario ve progresso parado

### Diferenca de CRIT-012

CRIT-012 (ja completo) adicionou heartbeats a cada 15s e `bodyTimeout: 0` no proxy undici. Porem:
- **CRIT-012 foca em manter a conexao viva** (heartbeats)
- **STORY-365 foca em reconectar quando a conexao morre** (reconnection)
- **CRIT-012 usa `asyncio.Queue` in-memory** para progress state — nao sobrevive a reconnect
- **STORY-365 persiste progress no Redis** — reconnect recebe estado atual

### Evidencia no Codigo

| Arquivo | Linha | Problema |
|---------|-------|----------|
| `backend/progress.py` | — | Progress state em `asyncio.Queue` in-memory — perdido em reconnect |
| `backend/routes/search.py` | 284+ | SSE generator nao suporta `Last-Event-ID` para replay |
| `frontend/app/buscar/hooks/useUfProgress.ts` | — | `EventSource` sem reconnect automatico |

## Acceptance Criteria

### Backend — Progress Persistence

- [ ] **AC1:** Progress state persistido no Redis (key: `smartlic:progress:{search_id}`, TTL: 1h) alem de `asyncio.Queue`
- [ ] **AC2:** Cada progress event inclui `id` field no SSE (`id: {event_counter}\n`) para `Last-Event-ID` support
- [ ] **AC3:** SSE endpoint aceita header `Last-Event-ID` e replay events posteriores ao ID informado (lidos do Redis)

### Backend — Heartbeat Enhancement

- [ ] **AC4:** SSE response headers incluem `X-Accel-Buffering: no` e `Cache-Control: no-cache, no-store` para evitar buffering em proxies
- [ ] **AC5:** Heartbeat interval configuravel via env var `SSE_HEARTBEAT_INTERVAL_S` (default: 15s, ja implementado por CRIT-012)

### Frontend — Auto-Reconnection

- [ ] **AC6:** Hook `useUfProgress` (ou equivalente) implementa reconnect automatico quando `EventSource` emite `error` event
- [ ] **AC7:** Reconnect usa exponential backoff: 1s → 2s → 4s (max 3 tentativas)
- [ ] **AC8:** Apos reconnect bem-sucedido, progresso exibido corretamente (nao reseta para 0%)
- [ ] **AC9:** Apos 3 falhas de reconnect, fallback para polling `GET /v1/search/{id}/status` a cada 5s

### Frontend Proxy — Resilience

- [ ] **AC10:** Proxy SSE (`buscar-progress/route.ts`) forward `Last-Event-ID` header ao backend

### Testes

- [ ] **AC11:** Teste backend: SSE endpoint com `Last-Event-ID` retorna apenas events posteriores
- [ ] **AC12:** Teste backend: Progress state no Redis sobrevive a restart do SSE connection
- [ ] **AC13:** Teste frontend: EventSource reconnect apos desconexao simulada
- [ ] **AC14:** Zero regressoes nos testes existentes

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/progress.py` | Dual-write: Queue + Redis. Metodo `get_events_since(search_id, last_event_id)` |
| `backend/routes/search.py` | SSE generator: `id:` field, `Last-Event-ID` support, response headers |
| `frontend/app/buscar/hooks/useUfProgress.ts` | Auto-reconnect com exponential backoff |
| `frontend/app/api/buscar-progress/route.ts` | Forward `Last-Event-ID` header |
| `backend/config.py` | `SSE_HEARTBEAT_INTERVAL_S` env var |

## Notas Tecnicas

- Redis progress data structure: usar Redis Stream (`XADD/XREAD`) ou sorted set com event_id como score
  - **Recomendacao:** Redis List com JSON events — simples, suporta replay com `LRANGE`
- O `asyncio.Queue` deve ser mantido como fast path (mesma instancia/worker), Redis como fallback para cross-worker e reconnect
- `Last-Event-ID` e parte da spec SSE — o browser envia automaticamente no reconnect
- O `EventSource` nativo do browser JA tem reconnect automatico, mas com intervalo fixo de 3s. O hook customizado permite exponential backoff e fallback para polling
- Considerar usar `@microsoft/fetch-event-source` no frontend para maior controle sobre reconnect (ja usado em alguns testes)
