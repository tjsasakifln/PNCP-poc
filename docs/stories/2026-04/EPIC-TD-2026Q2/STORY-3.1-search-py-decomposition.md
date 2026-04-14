# STORY-3.1: search.py Decomposition (TD-SYS-005)

**Priority:** P1 (manutenibilidade — bloqueia LLM async refactor)
**Effort:** L (24-40h)
**Squad:** @architect (lead) + @dev (executor) + @qa
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 2 (precede STORY-4.1)

---

## Story

**As a** dev SmartLic,
**I want** `routes/search.py` decomposto em módulos coesos (POST handler, SSE, state, status, retry),
**so that** mudanças não cascateiem, testes sejam isolados, e novo dev consiga onboard em <2 dias.

---

## Acceptance Criteria

### AC1: Módulos finais

- [ ] `backend/routes/search/__init__.py` — re-export para backward compat
- [ ] `backend/routes/search/post_handler.py` — `POST /buscar`
- [ ] `backend/routes/search/sse.py` — `GET /buscar-progress/{id}` (já parcial)
- [ ] `backend/routes/search/state.py` — state machine queries
- [ ] `backend/routes/search/status.py` — `/v1/search/{id}/status`
- [ ] `backend/routes/search/retry.py` — `/v1/search/{id}/retry`

### AC2: Backward compat

- [ ] All imports `from routes.search import X` continuam funcionando
- [ ] Existing 5131+ pytest pass sem mudança

### AC3: Cobertura testes

- [ ] Cada novo módulo tem test file dedicado (`test_search_post.py`, `test_search_sse.py`, etc.)
- [ ] Cobertura backend mantém 70%+

### AC4: Documentation

- [ ] Atualizar CLAUDE.md "Routes" e "Source Tree"
- [ ] Atualizar `docs/architecture/system-architecture.md` removendo TD-SYS-005

---

## Tasks / Subtasks

- [ ] Task 1: Audit `routes/search.py` — mapear funções, dependências, state
- [ ] Task 2: Definir module boundaries
- [ ] Task 3: Refactor incremental:
  - [ ] Move SSE logic → `sse.py`
  - [ ] Move state queries → `state.py`
  - [ ] Move status endpoint → `status.py`
  - [ ] Move retry endpoint → `retry.py`
  - [ ] Move POST handler → `post_handler.py`
- [ ] Task 4: Update `__init__.py` re-exports
- [ ] Task 5: Run pytest após cada move (incremental safety)
- [ ] Task 6: Split tests por módulo
- [ ] Task 7: Documentation update

## Dev Notes

- `routes/search.py` ~1000 LOC; já parcialmente decomposto em `search_sse.py`, `search_state.py`, `search_status.py`
- Pattern: `routes/<feature>/<sub>.py` ao invés de `<feature>_<sub>.py`
- Dependências: `search_pipeline.py`, `search_state_manager.py`, `search_context.py`, `progress.py`

## Testing

- Existing pytest must pass durante refactor (run after each step)
- Add unit tests para each new module
- E2E `/buscar` smoke test final

## Definition of Done

- [ ] All AC met
- [ ] PR review por @architect + @qa
- [ ] No regression em production canary
- [ ] Story TD-SYS-005 closed em backlog

## Risks

- **R1**: Hidden coupling não detectado — mitigation: incremental + test-after-each-step
- **R2**: Esforço excede 40h — mitigation: timebox + escalate

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
