# STORY-CIG-BE-sse-last-event-id — Rotas `/v1/search/*` retornam 404 (prefix/montagem mudou) — 18 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_sse_last_event_id.py` roda em `backend-tests.yml` e falha em **18 testes** do triage row #3/30. Causa raiz classificada como **mock-drift / import / route-prefix drift**: as rotas `/v1/search/*` (incluindo `GET /v1/search/{id}/status`, `POST /v1/search/{id}/retry`) retornam HTTP 404 em TestClient. O endpoint de reconexão SSE com `Last-Event-ID` header é um dos contratos mais importantes para resiliência do progress chain.

**Arquivos principais afetados:**
- `backend/tests/test_sse_last_event_id.py` (18 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Refactor de `routes/search/` → package mudou prefix ou tirou o endpoint da montagem em `main.py`. Mesmo padrão de drift de STORY-CIG-BE-buscar-route-404 (#6). Validar com `grep -rn "/v1/search\\|@router" backend/routes/ backend/main.py`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_sse_last_event_id.py -v` retorna exit code 0 localmente (18/18 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift / import / route-prefix drift). Indicar se é mesmo fix de #6 ou independente.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_sse_last_event_id.py -v` isolado.
- [ ] `grep -rn "@router.get.*status\\|@router.post.*retry\\|/v1/search" backend/routes/ backend/main.py` — confirmar caminho real.
- [ ] Verificar se o fix de STORY-CIG-BE-buscar-route-404 (#6) já cobre este caso (se sim, esta story pode virar no-op e ser fechada como "resolved by #6").
- [ ] Se fix independente: corrigir prefix/montagem OU atualizar testes.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #3/30)

## Stories relacionadas no epic

- STORY-CIG-BE-buscar-route-404 (#6 — mesmo padrão de route drift)
- STORY-CIG-BE-sse-reconnect-api (#2 — mesmo módulo SSE)
- STORY-CIG-BE-sse-redis-pool-refactor (#1 — mesmo módulo SSE)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #3/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
