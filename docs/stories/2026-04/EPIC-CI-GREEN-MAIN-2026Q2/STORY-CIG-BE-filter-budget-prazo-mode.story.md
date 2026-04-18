# STORY-CIG-BE-filter-budget-prazo-mode — Time budget não marca pending review; prazo filter "modo abertas/publicacao" inativo — 10 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Duas suítes que cobrem filter budget e prazo filtering rodam em `backend-tests.yml` e falham em **10 testes** do triage row #19/30. Causa raiz classificada como **assertion-drift**:

1. **Time budget não marca pending review** (CRIT-057): quando o filter excede o time budget, deveria marcar itens como `PENDING_REVIEW` (para LLM processar depois). Atualmente marca como rejeitados.
2. **Prazo filter "modo abertas/publicacao" inativo**: o filtro de prazo tem dois modos (abertas = data de encerramento futura; publicacao = dateRange de publicação) e um dos modos deixou de funcionar.

**Arquivos principais afetados:**
- `backend/tests/test_crit057_filter_time_budget.py`
- `backend/tests/test_filtrar_prazo_aberto.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Possível **prod-bug duplo**: (1) CRIT-057 regrediu; (2) prazo filter mode switch foi removido/invertido. Ambos afetam UX visível. Validar com `git log -p backend/filter.py backend/filter/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_crit057_filter_time_budget.py backend/tests/test_filtrar_prazo_aberto.py -v` retorna exit code 0 localmente (10/10 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis". Distinguir os 2 sub-drifts. Se prod-bug, adicionar teste de regressão para cada.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 2 suítes isoladas.
- [ ] `git log -p backend/filter.py backend/filter/` — identificar commits que mexeram em CRIT-057 ou prazo mode.
- [ ] Se (b) prod-bug: coordenar com @po sobre P1 bugfix.
- [ ] Validar `LLM_FALLBACK_PENDING_ENABLED` flag está ligada em test environment.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #19/30)

## Stories relacionadas no epic

- STORY-CIG-BE-story-drift-pending-review-schema (#22 — mesma área pending review)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #19/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. **Atenção @po:** possível prod-bug duplo — investigação obrigatória.
