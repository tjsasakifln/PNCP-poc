# HARDEN-020: SSE Reconnect Rate Limit (10/min)

**Severidade:** MEDIA
**Esforço:** 10 min
**Quick Win:** Nao
**Origem:** Conselho CTO — Auditoria de Fragilidades (2026-03-06)

## Contexto

GET `/buscar-progress/{search_id}` não tem rate limit explícito. Já tem `acquire_sse_connection` (3 conexões simultâneas por user) mas não limita reconexões rápidas que forçam replay de eventos do Redis.

## Critérios de Aceitação

- [x] AC1: Max 10 reconnections por user em 60s
- [x] AC2: 429 com Retry-After se limite excedido
- [x] AC3: Reutilizar infra de rate_limiter.py existente
- [x] AC4: Teste unitário

## Arquivos Afetados

- `backend/routes/search.py` — buscar_progress_stream()
- `backend/rate_limiter.py` — novo rate limit
