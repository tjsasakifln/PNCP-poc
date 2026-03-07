# HARDEN-019: Last-Event-ID Fallback para DB State

**Severidade:** MEDIA
**Esforço:** 20 min
**Quick Win:** Nao
**Origem:** Conselho CTO — Auditoria de Fragilidades (2026-03-06)

## Contexto

Client reconecta SSE com last_event_id, mas stream Redis já expirou (_STREAM_EXPIRE_TTL=300s). Replay retorna vazio e client nunca recebe terminal event — progress bar fica stuck em 90%.

## Critérios de Aceitação

- [x] AC1: `is_search_terminal()` faz fallback a DB state machine quando Redis vazio
- [x] AC2: DB states "completed"/"failed"/"degraded" mapeados para SSE terminal events
- [x] AC3: Client recebe terminal event sintético com dados do DB
- [x] AC4: Teste com cenário de Redis expirado + DB complete
- [x] AC5: Zero regressions nos testes de replay (STORY-297)

## Arquivos Afetados

- `backend/progress.py` — is_search_terminal()
- `backend/search_state_manager.py` — get_current_state()
- `backend/tests/test_progress.py`
