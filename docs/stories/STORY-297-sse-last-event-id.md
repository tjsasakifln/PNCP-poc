# STORY-297: SSE Last-Event-ID Resumption

**Sprint:** 1 — Make It Reliable
**Size:** M (4-8h)
**Root Cause:** Track B (UX Audit)
**Depends on:** STORY-294
**Industry Standard:** [WHATWG — Server-Sent Events Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html#the-last-event-id-header)

## Contexto

SSE connections drop por vários motivos: mobile network switch, laptop sleep, Railway proxy reset (60s idle). Hoje quando SSE desconecta, o frontend perde todo o contexto e não tem como reconectar sem perder eventos.

A spec WHATWG define `Last-Event-ID`: cada evento SSE tem um `id:` field, e quando o browser reconecta, envia `Last-Event-ID` header. O servidor reenvia apenas os eventos após aquele ID.

## Acceptance Criteria

### Backend
- [ ] AC1: Cada evento SSE inclui `id:` field (monotonic counter por search_id)
- [ ] AC2: Eventos armazenados em Redis list com TTL 10min: `sse_events:{search_id}`
- [ ] AC3: Endpoint SSE lê `Last-Event-ID` header e reenvia eventos após esse ID
- [ ] AC4: Se `Last-Event-ID` presente e search já completou, envia evento `completed` imediatamente
- [ ] AC5: Máximo 1000 eventos por search_id (ring buffer)

### Frontend
- [ ] AC6: EventSource reconecta automaticamente (browser nativo)
- [ ] AC7: Se reconexão falha 3x, fallback para polling `/v1/search/{id}/status`
- [ ] AC8: UI não reseta estado durante reconexão — mantém resultados parciais
- [ ] AC9: Indicador visual: "Reconectando..." durante gap

### Quality
- [ ] AC10: Teste: desconexão simulada → reconexão → eventos não perdidos
- [ ] AC11: Teste: reconnect após search completo → recebe `completed` imediatamente
- [ ] AC12: Testes existentes passando

## Technical Notes

```
SSE Event Format (com id):
  id: 42
  event: partial_results
  data: {"source": "pncp", "uf": "SP", "items": [...]}

Reconnect Request:
  GET /buscar-progress/{id}
  Last-Event-ID: 42

Server Response:
  → replay events 43, 44, 45, ...
```

## Files to Change

- `backend/progress.py` — add event ID tracking + Redis storage
- `backend/routes/search.py` — read Last-Event-ID header, replay events
- `frontend/hooks/useSearch.ts` — handle reconnection state
- `frontend/app/buscar/page.tsx` — reconnection UI indicator

## Definition of Done

- [ ] SSE reconnect após 5s disconnect: zero eventos perdidos
- [ ] Mobile network switch: busca continua sem restart
- [ ] Todos os testes passando
- [ ] PR merged
