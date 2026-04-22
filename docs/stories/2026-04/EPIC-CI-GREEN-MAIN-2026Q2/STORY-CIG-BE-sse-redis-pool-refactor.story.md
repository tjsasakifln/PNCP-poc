# STORY-CIG-BE-sse-redis-pool-refactor — `routes.search_sse.get_redis_pool` perdido após refactor — 17 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Done
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

- [x] AC1: `pytest backend/tests/test_sse_heartbeat.py backend/tests/test_progress_streams.py -v` retorna exit code 0 — **11/11 + 22/22 = 33/33 PASS** (evidência no commit Wave #386 sub-commit "CIG Wave 1 — sessions/paywall/buscar/sse mock paths post-package refactors").
- [x] AC2: Última run de `backend-tests.yml` pós-merge PR #386 na main mostra as 2 suítes com 0 failed / 0 errored.
- [x] AC3: Causa raiz em "Root Cause Analysis" abaixo — **mock-drift** (símbolo renomeado no refactor redis_pool).
- [x] AC4: Cobertura backend não regrediu. Threshold 70% mantido. Sem mudanças de produção.
- [x] AC5 (NEGATIVO): Zero novos skip/xfail markers. Apenas mocks de teste atualizados.

---

## Investigation Checklist (para @dev, fase Implement)

- [x] Rodar as 2 suítes isoladas e capturar AttributeError real.
- [x] `grep -rn "def get_redis_pool\|def _get_redis_pool\|redis_pool" backend/routes/ backend/` — mapeamento: função renomeada para `get_sse_redis_pool` no módulo `backend/redis_pool.py`, reexportada via `routes.search_sse.get_sse_redis_pool`.
- [x] Decisão: **(b) atualizar mocks** — consumers do símbolo público são apenas testes internos.
- [x] Aplicado: 11 occurrências de `patch("routes.search_sse.get_redis_pool")` → `patch("routes.search_sse.get_sse_redis_pool")`.
- [x] Cobertura não regrediu.
- [x] Grep de skip markers vazio.

---

## Root Cause Analysis

**Causa raiz:** Mock-drift após refactor que renomeou `get_redis_pool` → `get_sse_redis_pool` para segregar pool dedicado a SSE streaming (do pool generalista).

**Antes→Depois (símbolos):**

| Antes | Depois |
|-------|--------|
| `routes.search_sse.get_redis_pool` | `routes.search_sse.get_sse_redis_pool` |
| `backend/redis_pool.py::get_redis_pool` | `backend/redis_pool.py::get_sse_redis_pool` (SSE-scoped) + `get_redis_pool` (generalista) |

**Por que renomeou:** HARDEN-017 AC1 introduziu pool SSE-scoped para isolar replay buffers (200 eventos/stream, bounded Redis memory) do pool de quota/cache generalista. Pools separados permitem tunar eviction/keepalive independentemente.

**Fix (commit Wave #386):** Testes `test_sse_heartbeat.py` e `test_progress_streams.py` atualizaram todos os `patch()` para o novo símbolo. Nenhuma mudança de produção. 11/11 + 22/22 = 33/33 PASS.

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
- **2026-04-19** — @dev: Implementação resolvida via PR #386 (Wave 1 Foundation). Decisão (b) aplicada: mocks atualizados `get_redis_pool` → `get_sse_redis_pool`. Zero mudanças de código de produção. 33/33 PASS (11 heartbeat + 22 progress streams). Status: Ready → InProgress → InReview.
- **2026-04-19** — @qa (Quinn): QA Gate **PASS**. Evidência: commit Wave #386 sub-commit "CIG Wave 1". RCA claro com tabela antes→depois. AC1-5 atendidos.
- **2026-04-19** — @devops (Gage): PR #386 merged em main (commit 45e4f70b). Status: InReview → Done.
