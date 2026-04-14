# QA Review — Technical Debt Assessment

**Reviewer:** @qa (Quinn)
**Date:** 2026-04-14
**Workflow:** brownfield-discovery v3.1 — Phase 7
**Inputs:**
- `docs/prd/technical-debt-DRAFT.md` (Phase 4)
- `docs/reviews/db-specialist-review.md` (Phase 5)
- `docs/reviews/ux-specialist-review.md` (Phase 6)

---

## Gate Status: ✅ **APPROVED** com observações

O assessment está **completo o suficiente** para prosseguir à Phase 8 (Final Assessment) e Phase 10 (Planning). Existem 5 observações críticas e 7 gaps menores documentados abaixo.

---

## Gaps Identificados

### Gaps Críticos (devem ser endereçados na Phase 8 antes do Planning)

#### G-001: Sem teste de carga (load testing) baseline

- **Área**: Performance / Reliability
- **Risco**: TD-SYS-014 (LLM concurrency bottleneck) e TD-SYS-003 (Railway 120s) são "narrativos" sem k6/Locust baseline. Não dá pra medir melhoria objetivamente.
- **Recomendação**: Adicionar TD-QA-060 — Estabelecer baseline k6/Locust + dashboard Grafana antes de implementar fixes de perf. Effort: 8-16h. Priority: P1.

#### G-002: Sem chaos/failure injection tests

- **Área**: Resilience
- **Risco**: TD-SYS-001 (SIGSEGV) + circuit breakers + SSE fallback nunca testados sob falhas controladas.
- **Recomendação**: Adicionar TD-QA-061 — toxiproxy ou similar para PNCP/PCP/ComprasGov/OpenAI failure injection em E2E. Effort: 16-24h. Priority: P2.

#### G-003: Sem contract tests para PNCP/Stripe

- **Área**: Integration / Regression
- **Risco**: TD-SYS-002 (PNCP page size 50 breaking) reapareceria sem detection. Stripe webhook payload changes silenciosos.
- **Recomendação**: Adicionar TD-QA-062 — Pact ou snapshot tests contra responses real (gravadas) + alerts on diff. Effort: 8-12h. Priority: P1.

#### G-004: Cobertura E2E para subscription/billing limitada

- **Área**: Critical user flow
- **Risco**: 60 Playwright tests cobrem search/pipeline; mas billing/checkout/cancel/upgrade não exercitados E2E.
- **Recomendação**: Adicionar TD-QA-063 — E2E specs para upgrade flow, downgrade, trial→paid, cancel. Effort: 8-16h. Priority: P1.

#### G-005: Sem audit de TypeScript types em backend Pydantic ↔ frontend

- **Área**: Cross-stack contract
- **Risco**: Backend Pydantic schema muda → frontend não pega em compile (schema duplicado em TS sem geração).
- **Recomendação**: Adicionar TD-QA-064 — `openapi-typescript-codegen` ou `pydantic-to-typescript` em CI. Effort: 4-8h. Priority: P1.

### Gaps Menores

- **G-010**: Sem accessibility test automation (axe-core integration parcial). Add `@axe-core/playwright` em E2E. Effort: 2-4h. Priority: P2.
- **G-011**: Sem performance budgets em CI (Lighthouse). Effort: 4-8h. Priority: P2.
- **G-012**: Sem mutation testing (Stryker) para backend critical paths. Effort: 8-16h. Priority: P3.
- **G-013**: Sem fuzz testing para search filter parser (`term_parser.py`). Effort: 4-8h. Priority: P2.
- **G-014**: Sem snapshot testing de Excel output (openpyxl). Effort: 2-4h. Priority: P3.
- **G-015**: Sem teste de race condition em quota atomic increment. Effort: 4-8h. Priority: P2.
- **G-016**: Sem teste para schema migrations rollback (depende de TD-DB-030 down.sql). Effort: bloqueado por TD-DB-030.

---

## Riscos Cruzados

| Risco                                                                       | Áreas Afetadas              | Mitigação                                                  |
|-----------------------------------------------------------------------------|------------------------------|------------------------------------------------------------|
| **R-001**: TD-SYS-005 (search.py decompose) + TD-SYS-014 (LLM async) — refactor simultâneo é arriscado | Backend (search/llm)         | Sequenciar: TD-SYS-005 primeiro, depois TD-SYS-014.        |
| **R-002**: TD-DB-011 (UNIQUE email) + TD-DB-040 (cron monitoring) — sem monitoring, dedup script pode falhar silenciosamente | DB                          | TD-DB-040 deve preceder TD-DB-011 ou ambos no mesmo PR.    |
| **R-003**: TD-FE-001 (any types) + TD-QA-064 (Pydantic→TS gen) — gerar types antes de remover any reduz scope drasticamente | FE/Backend contract         | TD-QA-064 antes de TD-FE-001 — pode reduzir 30-50% do esforço. |
| **R-004**: TD-SYS-001 (SIGSEGV) + qualquer Sentry/OTEL change — risco de regressão | Backend                     | Feature flag toggle + canary deploy + rollback ready.      |
| **R-005**: TD-DB-004 (purge cron) + TD-DB-040 (monitoring) — purge silently fail = downtime imediato | DB ops                      | Bundle ambos no mesmo PR + smoke test pós-deploy.          |
| **R-006**: TD-FE-006 (kanban a11y) + TD-FE-051 (modal ARIA) + WCAG audit — esforço somado >24h, mas testes manuais com screen reader essenciais | FE accessibility            | Bundle em "Sprint A11y" + parceria com tester acessibilidade. |
| **R-007**: TD-SYS-002 (PNCP 50/page) é externo — nada garante que não mude novamente | Integration                  | TD-QA-062 (contract tests) + alert se response shape muda. |

---

## Dependências Validadas

### Sequência crítica (DO NOT REORDER)

```
TD-DB-040 (cron monitoring)
    ↓
TD-DB-004, 013, 014 (cron schedules)
    ↓ (smoke test pós-deploy)
[clear P0 blockers]

TD-QA-064 (Pydantic→TS)
    ↓
TD-FE-001 (any types)

TD-SYS-005 (search.py decompose)
    ↓
TD-SYS-014 (LLM async/batching)

TD-DB-011 dedup script DRY-RUN
    ↓
TD-DB-011 ALTER ADD UNIQUE
```

### Parallelizable (independentes)

- TD-FE-005 (`<Button>` codemod) — independente
- TD-FE-006 (kanban keyboard) — independente
- TD-DB-010 (stripe RLS admin) — independente
- TD-SYS-012 (setores sync) — independente
- TD-SYS-017 (rate limit público) — independente

---

## Testes Requeridos (pós-resolução)

### Por categoria de débito

#### CRITICAL — necessitam regression suite robusto

- **TD-SYS-001 (SIGSEGV)**: Test POST endpoints sob load (k6); monitor segfault em Sentry; canary deploy.
- **TD-SYS-005 (search.py decomp)**: Backwards-compat test (re-export shapes); existing 5131+ pytest suite full pass; E2E `/buscar` golden path.
- **TD-DB-004 (purge cron)**: Smoke test query `SELECT cron.schedule WHERE jobname='purge-old-bids'`; row count antes/depois.
- **TD-FE-001 (any types)**: `tsc --noEmit` strict pass; existing 2681+ jest pass.
- **TD-FE-002 (Shepherd a11y)**: axe-core scan; manual screen reader (NVDA/VoiceOver); E2E onboarding flow.
- **TD-FE-006 (Kanban keyboard)**: axe-core; manual keyboard nav; Playwright keyboard event tests.

#### HIGH — adicionar test cases

- **TD-DB-010, 011**: RLS test (anon/auth/service contexts); dedup script test.
- **TD-FE-005 (`<Button>` codemod)**: visual regression Percy; existing tests pass.
- **TD-FE-013 (SSE feedback)**: E2E + simulate dropped connection.
- **TD-SYS-014 (LLM async)**: Load test 10/50/100 concurrent; cost dashboard.

### Critérios de aceite globais

1. **Zero failures** em backend pytest (regra existente CLAUDE.md).
2. **Zero failures** em frontend jest.
3. **All 60 Playwright** continuam passando + novos E2E para gaps G-004.
4. **Lighthouse CI** (G-011) — LCP <2.5s, FID <100ms, CLS <0.1.
5. **Visual regression** (TD-FE-008) — Percy diff <1% em rotas críticas.
6. **Accessibility** (TD-FE-006, 050, 051) — `@axe-core/playwright` 0 violations em rotas core.
7. **Cron monitoring** (TD-DB-040) — Sentry alert configurado e testado.

---

## Métricas de Qualidade Sugeridas

| Métrica                       | Valor Atual         | Meta Pós-Resolução  |
|-------------------------------|---------------------|---------------------|
| Backend test coverage         | ~70% (threshold)    | 80%                 |
| Frontend test coverage        | ~60% (threshold)    | 75%                 |
| TypeScript `any` count        | 296                 | <50                 |
| ARIA violations (axe)         | desconhecido        | 0 críticas          |
| Lighthouse Performance        | desconhecido        | >85                 |
| Lighthouse Accessibility      | desconhecido        | >95                 |
| Visual regression diff        | n/a                 | <1%                 |
| pg_cron job success rate      | desconhecido        | >99% (com alerts)   |
| Sentry error rate (POST)      | alto (CRIT-080)     | <0.1% requests      |
| LLM cost monthly cap          | uncapped            | budget definido     |

---

## Parecer Final

### ✅ APPROVED com condições

O assessment **está aprovado** para prosseguir, mas a Phase 8 (Final Assessment) DEVE incluir:

1. **5 novos débitos QA** (TD-QA-060 a TD-QA-064) descritos acima nos gaps críticos.
2. **Sequenciamento explícito** das dependências R-001 a R-007 documentadas.
3. **Critérios de aceite globais** (1-7 acima) como Definition of Done para o Epic.
4. **Métricas mensuráveis** antes/depois (tabela acima) — sem isso, ROI fica narrativo.

### Recomendações para Phase 8

- @architect deve **explicitamente sequenciar** as 4 dependências críticas no plano de resolução.
- @architect deve **incluir os 5 débitos QA novos** na matriz consolidada.
- @analyst (Phase 9) deve usar as **métricas mensuráveis** como base do ROI no relatório executivo.
- @pm (Phase 10) deve criar **stories separadas para cada débito** mas **bundle relacionados em PRs** (ex: P0 cron schedules em 1 PR, kanban a11y bundle).

### Riscos de Não-Resolução

| Categoria | Se não resolver em 6 meses                                                               |
|-----------|-------------------------------------------------------------------------------------------|
| TD-DB-004 (purge cron)        | **Storage 500MB exceeded** → table locks → downtime → emergency cleanup downtime adicional |
| TD-SYS-001 (SIGSEGV)          | **5-15% POST failures** persistentes; usuários percebem flakiness; Sentry overflow         |
| TD-FE-006 (kanban a11y)       | **B2G enterprise sales bloqueadas** por compliance LBI 13.146/2015                         |
| TD-FE-001 (any types)         | **Velocity drop**; novos bugs não pegos em compile time; refactoring confiança baixa       |
| TD-DB-011 (email UNIQUE)      | **Account confusion + Stripe billing chaos** com customers reportando duplicates           |
| TD-SYS-018 (LLM cost cap)     | **Runaway spending risk** se prompt loop inadvertido; potencial $1000s/mês unexpected      |

---

## Total de Débitos Pós-Review

- **Sistema**: 20 (Phase 1)
- **Database**: 18 + 3 novos = 21 (Phase 2 + Phase 5)
- **Frontend**: 23 + 4 novos = 27 (Phase 3 + Phase 6)
- **QA / Testing**: 5 novos = 5 (Phase 7)
- **TOTAL**: **73 débitos** (4 já FIXED) → **69 abertos**

---

**Status**: ✅ APPROVED. Handoff para Phase 8 (@architect — final assessment).
