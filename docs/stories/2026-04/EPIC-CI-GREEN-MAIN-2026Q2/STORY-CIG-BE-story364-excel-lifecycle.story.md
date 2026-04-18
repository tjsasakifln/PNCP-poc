# STORY-CIG-BE-story364-excel-lifecycle — Endpoints de Excel lifecycle 404 (rota renomeada/re-hosted) — 17 testes route-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_story364_excel_resilience.py` roda em `backend-tests.yml` e falha em **17 testes** do triage row #4/30. Causa raiz classificada como **import / route-prefix drift**: endpoints do lifecycle de Excel (geração, download, status de job ARQ, expiração) retornam 404. STORY-364 introduziu esse lifecycle resiliente; refactor recente moveu/renomeou rotas.

**Arquivos principais afetados:**
- `backend/tests/test_story364_excel_resilience.py` (17 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Endpoints podem ter migrado de `/download/excel` → `/v1/exports/excel` ou similar, ou de `routes/download.py` → `routes/exports/` package. Validar com `grep -rn "excel\\|@router.*download" backend/routes/ backend/main.py` + `git log --follow backend/routes/download.py`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_story364_excel_resilience.py -v` retorna exit code 0 localmente (17/17 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (import / route-drift). Tabela antes→depois dos paths.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_story364_excel_resilience.py -v` isolado.
- [ ] Mapear paths de Excel endpoints antes vs depois do refactor.
- [ ] Decidir entre (a) atualizar testes para novo path ou (b) reexpor path antigo (backward-compat) se frontend ainda usar.
- [ ] Validar integração ARQ ainda funciona (`llm_ready`/`excel_ready` SSE events — CLAUDE.md).
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #4/30)

## Stories relacionadas no epic

- STORY-CIG-BE-buscar-route-404 (#6 — mesmo padrão de route drift)
- STORY-CIG-BE-alerts-endpoint-404 (#5 — mesmo padrão de route drift)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #4/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
