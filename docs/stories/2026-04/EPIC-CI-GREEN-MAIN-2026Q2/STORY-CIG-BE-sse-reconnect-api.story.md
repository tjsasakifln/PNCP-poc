# STORY-CIG-BE-sse-reconnect-api — `routes.search.acquire_sse_connection` sumiu após refactor `routes/search/` → package — 3 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P2 — Gate
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_sse_reconnect_rate_limit.py` roda em `backend-tests.yml` e falha em **3 testes** do triage row #2/30. Causa raiz classificada como **mock-drift**: `routes.search` não expõe mais `acquire_sse_connection` após o refactor que transformou `routes/search.py` em package `routes/search/`.

**Arquivos principais afetados:**
- `backend/tests/test_sse_reconnect_rate_limit.py` (3 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** `acquire_sse_connection` migrou para `routes/search/sse.py` ou `routes/search_sse.py`. Validar com `grep -rn "def acquire_sse_connection" backend/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_sse_reconnect_rate_limit.py -v` retorna exit code 0 localmente (3/3 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift). Path antes→depois.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_sse_reconnect_rate_limit.py -v` isolado.
- [ ] `grep -rn "def acquire_sse_connection" backend/`.
- [ ] Atualizar mock path para nova localização.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #2/30)

## Stories relacionadas no epic

- STORY-CIG-BE-sse-redis-pool-refactor (#1 — mesmo módulo)
- STORY-CIG-BE-sse-last-event-id (#3 — mesmo módulo)
- STORY-CIG-BE-buscar-route-404 (#6 — mesmo refactor `routes/search/` → package)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #2/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (8/10)** — Draft → Ready. Mock-path trivial; low-risk Implement.
