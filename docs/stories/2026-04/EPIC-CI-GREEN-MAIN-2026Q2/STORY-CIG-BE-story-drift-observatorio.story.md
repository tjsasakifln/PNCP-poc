# STORY-CIG-BE-story-drift-observatorio — Endpoint retorna dados vazios (mock shape mismatch) — 4 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Done
**Priority:** P2 — Gate
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_observatorio.py` roda em `backend-tests.yml` e falha em **4 testes** do triage row #25/30. Causa raiz classificada como **mock-drift**: endpoint do observatório retorna dados vazios quando mocks têm shape antigo.

**Arquivos principais afetados:**
- `backend/tests/test_observatorio.py` (4 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Mock shape desatualizado pós-refactor do schema de Observatório (página frontend `/observatorio` — ver STORY-CIG-FE-17). Validar shape real.

---

## Acceptance Criteria

- [x] AC1: `pytest backend/tests/test_observatorio.py -v` retorna exit code 0 localmente. Validado 2026-04-19: 10/10 PASS.
- [x] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [x] AC3: Causa raiz documentada no commit `f81e5eed`: endpoint do Observatório consulta DUAS fontes (datalake `pncp_raw_bids` + historical `supplier_contracts`) pós-arquitetura DataLake (CLAUDE.md Layer 1/2). Mocks só cobriam datalake → endpoint retornava vazio porque o branch historical falhava silenciosamente. Fix: mockar AMBOS os paths. -25/+43 linhas.
- [x] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [x] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_observatorio.py -v` isolado.
- [ ] Validar shape do endpoint real em `backend/routes/` e Pydantic schema.
- [ ] Atualizar mocks para bater novo shape.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #25/30)

## Stories relacionadas no epic

- STORY-CIG-FE-17 `observatorio-page` (frontend counterpart)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #25/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. Validar shape contra Pydantic schema real; coordenar com STORY-CIG-FE-17 se endpoint path mudou.
- **2026-04-19** — @dev: Status Ready → InReview → Done. Mocks expandidos para cobrir AMBOS datalake + historical paths (commit `f81e5eed`). Validação local 2026-04-19: 10/10 PASS. AC1-5 atendidos.
