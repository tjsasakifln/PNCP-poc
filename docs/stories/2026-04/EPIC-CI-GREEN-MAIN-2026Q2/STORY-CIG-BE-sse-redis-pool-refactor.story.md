# STORY-CIG-BE-sse-redis-pool-refactor — `routes.search_sse.get_redis_pool` perdido após refactor — 17 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate Blocker
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suítes `test_sse_heartbeat.py` e `test_progress_streams.py` rodam em `backend-tests.yml` e falham em **17 testes** do triage row #1/30. Causa raiz classificada como **mock-drift**: `routes.search_sse` não expõe mais `get_redis_pool` (atributo virou `_get_redis_pool` ou moveu para o módulo `redis_pool`). Os testes fazem `patch("routes.search_sse.get_redis_pool")` contra o símbolo antigo e recebem `AttributeError`.

O SSE é crítico para UX (progress chain: bodyTimeout(0) + heartbeat(15s), Railway idle 60s, SSE inactivity 120s — CLAUDE.md). Corrigir o mock-drift é gate blocker porque dezenas de testes de SSE dependem do mesmo path.

**Arquivos principais afetados:**
- `backend/tests/test_sse_heartbeat.py`
- `backend/tests/test_progress_streams.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** `routes/search_sse.py` sofreu refactor privatizando `get_redis_pool` → `_get_redis_pool` OU movendo para `backend/redis_pool.py`. Validar com `grep -rn "def get_redis_pool\\|def _get_redis_pool" backend/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_sse_heartbeat.py backend/tests/test_progress_streams.py -v` retorna exit code 0 localmente (17/17 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift). Tabela antes→depois dos símbolos renomeados.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 2 suítes isoladas e capturar AttributeError real.
- [ ] `grep -rn "def get_redis_pool\\|def _get_redis_pool\\|redis_pool" backend/routes/ backend/` — mapear nome atual e localização.
- [ ] Decidir entre (a) reexpor `get_redis_pool` como atributo público em `routes.search_sse` (backward-compat) ou (b) atualizar mocks dos testes para o novo path.
- [ ] Preferir (b) — acoplamento menor. Usar (a) só se houver consumers externos.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #1/30)

## Stories relacionadas no epic

- STORY-CIG-BE-sse-reconnect-api (#2 — mesmo módulo routes/search)
- STORY-CIG-BE-sse-last-event-id (#3 — mesmo módulo routes/search)
- STORY-CIG-BE-buscar-route-404 (#6 — mesmo módulo routes/search)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #1/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (8/10)** — Draft → Ready. 17 testes mock-drift; preferir decisão (b) atualizar mocks (menor acoplamento) vs (a) reexpor backward-compat — consumers externos improváveis em rota interna.
