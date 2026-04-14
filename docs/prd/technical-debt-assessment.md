# Technical Debt Assessment — FINAL

**Project:** SmartLic (Inteligência em Licitações Públicas)
**Date:** 2026-04-14
**Author:** @architect (Aria), incorporando Phases 5 (DB), 6 (UX), 7 (QA)
**Workflow:** brownfield-discovery v3.1 — Phase 8
**Status:** ✅ APPROVED pela Phase 7 QA gate (com observações incorporadas)

---

## Executive Summary

| Métrica                          | Valor                       |
|----------------------------------|-----------------------------|
| **Total de débitos identificados** | 73                          |
| **Débitos já resolvidos (fixed)**  | 4 (DB CRITICAL hotfixes)    |
| **Débitos abertos**                | 69                          |
| **CRITICAL** abertos               | 9                           |
| **HIGH** abertos                   | 26                          |
| **MEDIUM** abertos                 | 22                          |
| **LOW** abertos                    | 12                          |
| **Esforço total estimado**         | **350-560 horas**           |
| **Custo estimado (R$150/h)**       | **R$ 52.500 — R$ 84.000**   |
| **Timeline recomendado**           | 12-18 semanas (3-4.5 meses) |

---

## 1. Inventário Completo de Débitos (Validado)

### 1.1 Sistema (20 débitos — validados por @architect)

#### CRITICAL

| ID         | Débito                                         | Severidade | Horas    | Prioridade |
|------------|------------------------------------------------|------------|----------|------------|
| TD-SYS-001 | CRIT-080 SIGSEGV em POST                       | CRITICAL   | 16-40h   | P0         |
| TD-SYS-002 | PNCP page size 50 (Feb 2026)                   | CRITICAL   | 4h       | P0         |
| TD-SYS-003 | Railway 120s hard timeout                      | CRITICAL   | 8-16h    | P0         |
| TD-SYS-004 | Migration CI (CRIT-050) — DEFENDED            | CRITICAL   | ✅ DONE  | -          |
| TD-SYS-005 | search.py monolítico                           | CRITICAL   | 24-40h   | P1         |

#### HIGH

| ID         | Débito                                         | Horas    | Prioridade |
|------------|------------------------------------------------|----------|------------|
| TD-SYS-010 | L1 cache não shared workers                    | 8h       | P2         |
| TD-SYS-011 | Feature flags em 3 lugares                     | 8-16h    | P2         |
| TD-SYS-012 | Setores duplicados sync manual                 | 4h       | P1         |
| TD-SYS-013 | Session dedup eventual consistency             | 16h      | P2         |
| TD-SYS-014 | LLM concurrency bottleneck                     | 16-24h   | P1         |
| TD-SYS-015 | FTS Português não otimizado                    | 8-16h    | P2         |
| TD-SYS-016 | search_results_cache growth (overlap TD-DB-013)| -        | P0         |
| TD-SYS-017 | Rate limit ausente endpoints públicos          | 4-8h     | P1         |
| TD-SYS-018 | LLM sem cap de custo mensal                    | 4-8h     | P1         |

#### MEDIUM

- TD-SYS-020 (sectors validate startup): 2h, P2
- TD-SYS-021 (feature flags docs): 4h, P2
- TD-SYS-022 (mock location consistency): 8h, P2
- TD-SYS-023 (integration tests flaky): 8-16h, P2
- TD-SYS-024 (schemas.py monolítico): 16h, P3
- TD-SYS-025 (logs JSON-vs-text): 4h, P3

#### LOW

- TD-SYS-030, 031, 032: 8-12h total, P3

**Subtotal Sistema (excluindo fixed): 19 débitos, ~140-220h**

### 1.2 Database (21 débitos — validados por @data-engineer)

#### CRITICAL

| ID         | Débito                                         | Horas    | Prioridade |
|------------|------------------------------------------------|----------|------------|
| TD-DB-001  | RLS bypass `search_sessions`                   | ✅ FIXED | -          |
| TD-DB-002  | Missing user_id indexes                        | ✅ FIXED | -          |
| TD-DB-003  | partner_referrals NOT NULL conflict            | ✅ FIXED | -          |
| TD-DB-004  | purge_old_bids cron NOT SCHEDULED              | 0.5h     | **P0**     |

#### HIGH

| ID         | Débito                                         | Horas | Prioridade |
|------------|------------------------------------------------|-------|------------|
| TD-DB-010  | stripe_webhook_events RLS admin                | 1h    | P1         |
| TD-DB-011  | profiles.email UNIQUE + dedup                  | 2-4h  | P1         |
| TD-DB-013  | search_results_cache cron cleanup              | 0.5h  | P0         |
| TD-DB-014  | search_results_store cron cleanup              | 0.5h  | P0         |
| TD-DB-022  | pncp_raw_bids.data_* nullable (HIGH ↑)         | 4-8h  | P1         |
| TD-DB-040  | pg_cron monitoring/alertas (NEW)               | 4-8h  | P1         |
| TD-DB-041  | Backup off-site (NEW)                          | 4-8h  | P2         |

#### MEDIUM

- TD-DB-012 (messages RLS comment): 4-6h, P2 (DOWNGRADED ↓)
- TD-DB-015 (alert digest index): 1h, P2 (DOWNGRADED ↓)
- TD-DB-020 (audit_events soft-delete): 1h, P2
- TD-DB-021 (classification_feedback docs): 2-4h, P2
- TD-DB-024 (stripe webhook PII archive): 4-8h, P2
- TD-DB-042 (connection pooler tune NEW): 2-4h, P2

#### LOW

- TD-DB-023 (health_checks cron): 0.5h, P3 (DOWNGRADED ↓)
- TD-DB-030 (down.sql templates): 4-8h, P3
- TD-DB-032 (soft FK comment): 0.5h, P3
- TD-DB-033 (search_results_store CASCADE): 1h, P3

**Subtotal Database (excluindo fixed): 17 débitos, ~42-70h**

### 1.3 Frontend (27 débitos — validados por @ux-design-expert)

#### CRITICAL

| ID         | Débito                                         | Horas    | Prioridade |
|------------|------------------------------------------------|----------|------------|
| TD-FE-001  | 296 `any` types                                | 24-40h   | P1         |
| TD-FE-002  | Shepherd.js hardcoded HTML a11y                | 16-24h   | P1         |
| TD-FE-006  | Kanban sem keyboard nav (UPGRADED ↑)           | 8-16h    | **P0**     |

#### HIGH

| ID         | Débito                                         | Horas    | Prioridade |
|------------|------------------------------------------------|----------|------------|
| TD-FE-003  | 139 inline styles (DOWNGRADED ↓)               | 16-24h   | P2         |
| TD-FE-004  | 194 inline hex colors                          | 8-16h    | P1         |
| TD-FE-005  | `<button>` codemod                             | 8h       | P1         |
| TD-FE-008  | Visual regression Percy                        | 8-16h    | P2         |
| TD-FE-013  | SSE reconnection feedback (UPGRADED ↑)         | 4-8h     | P1         |
| TD-FE-016  | Error messages humanizados (UPGRADED ↑)        | 4-8h     | P1         |
| TD-FE-050  | Disabled contrast WCAG (NEW)                   | 2-4h     | P1         |
| TD-FE-051  | Modal ARIA padronization (NEW)                 | 4-8h     | P1         |

#### MEDIUM

- TD-FE-007 (RSC opportunistic, DOWNGRADED ↓): 40-56h, P3
- TD-FE-010 (i18n deferred): TBD, P3
- TD-FE-011 (Storybook): 16-24h, P2
- TD-FE-012 (tree-shake): 4-8h, P2
- TD-FE-014 (image opt): 4-8h, P2
- TD-FE-015 (loading consistency): 4-8h, P2
- TD-FE-017 (tour dismiss): 2-4h, P2
- TD-FE-018 (bottom nav sticky): 2-4h, P2
- TD-FE-019 (cache freshness badge): 2-4h, P2
- TD-FE-020 (form validation prominence): 4-8h, P2
- TD-FE-021 (blog responsive): 2-4h, P2
- TD-FE-052 (SWR invalidation NEW): 4-8h, P2
- TD-FE-053 (skeleton CLS NEW): 2-4h, P2

#### LOW

- TD-FE-030, 031, 032: ~6-13h, P3

**Subtotal Frontend: 27 débitos, ~140-240h**

### 1.4 QA / Testing (5 débitos — adicionados por @qa)

| ID         | Débito                                         | Horas | Prioridade |
|------------|------------------------------------------------|-------|------------|
| TD-QA-060  | Load test baseline (k6/Locust + Grafana)       | 8-16h | P1         |
| TD-QA-061  | Chaos/failure injection (toxiproxy)            | 16-24h| P2         |
| TD-QA-062  | Contract tests PNCP/Stripe                     | 8-12h | P1         |
| TD-QA-063  | E2E billing/subscription flow                  | 8-16h | P1         |
| TD-QA-064  | Pydantic→TS type generation                    | 4-8h  | P1         |

**Subtotal QA: 5 débitos, ~44-76h**

---

## 2. Matriz de Priorização Final Consolidada

### P0 — IMEDIATO (sprint 0, ~12-30h, semana 1)

Bloqueios de produção e storage. Custo: R$ 1.800 — R$ 4.500.

| ID         | Débito                                         | Horas      | Owner            |
|------------|------------------------------------------------|------------|------------------|
| TD-DB-040  | pg_cron monitoring (PRECEDE crons)             | 4-8h       | @data-engineer   |
| TD-DB-004  | Schedule purge_old_bids cron                   | 0.5h       | @data-engineer   |
| TD-DB-013  | Schedule search_results_cache cleanup          | 0.5h       | @data-engineer   |
| TD-DB-014  | Schedule search_results_store cleanup          | 0.5h       | @data-engineer   |
| TD-FE-006  | Kanban keyboard nav (WCAG/legal)               | 8-16h      | @ux-design-expert + @dev |
| TD-SYS-001 | CRIT-080 SIGSEGV deep dive (kickoff)           | (ongoing)  | @architect + @dev |

### P1 — Critical Path (sprints 1-3, ~110-200h, semanas 2-7)

ROI alto, dependências + risk reduction. Custo: R$ 16.500 — R$ 30.000.

**Sprint 1 (foundations, ~40-60h):**
- TD-QA-064 — Pydantic→TS type gen (4-8h) — **PRECEDE TD-FE-001**
- TD-FE-005 — `<button>` codemod (8h)
- TD-FE-016 — Error messages humanizados (4-8h)
- TD-FE-013 — SSE reconnection feedback (4-8h)
- TD-FE-050 — Disabled contrast (2-4h)
- TD-FE-051 — Modal ARIA padronization (4-8h)
- TD-DB-010 — Stripe webhook admin RLS (1h)
- TD-DB-011 — profiles.email UNIQUE + dedup script (2-4h)
- TD-SYS-012 — Setores sync automatizado (4h)
- TD-SYS-017 — Rate limit público (4-8h)
- TD-SYS-018 — LLM cost cap (4-8h)
- TD-DB-022 — pncp_raw_bids.data_* nullability (4-8h)

**Sprint 2 (refactor + tests, ~40-70h):**
- TD-SYS-005 — search.py decomposition (24-40h) — **PRECEDE TD-SYS-014**
- TD-FE-001 — TypeScript strict + any progressive (24-40h, parallel)
- TD-QA-060 — Load test baseline (8-16h)
- TD-QA-062 — Contract tests PNCP/Stripe (8-12h)
- TD-QA-063 — E2E billing flow (8-16h)

**Sprint 3 (perf + a11y, ~30-70h):**
- TD-SYS-014 — LLM async + batching (16-24h)
- TD-FE-002 — Shepherd.js a11y replacement (16-24h)
- TD-FE-004 — ESLint hex enforcement + cleanup (8-16h)
- TD-SYS-003 — Railway 120s time budgets audit (8-16h)
- TD-SYS-002 — PNCP page size detect/alert (4h)

### P2 — Maintainability (sprints 4-6, ~80-140h, semanas 8-13)

Quality + DX. Custo: R$ 12.000 — R$ 21.000.

- TD-SYS-010 (L1 cache shared): 8h
- TD-SYS-011 (feature flags SoT): 8-16h
- TD-SYS-013 (session dedup): 16h
- TD-SYS-015 (FTS Português): 8-16h
- TD-SYS-020-025 (medium backend cleanup): 30-50h
- TD-DB-012, 015, 020, 021, 024, 041, 042: ~25-45h
- TD-FE-003, 008, 011, 012, 014, 015, 017, 018, 019, 020, 021, 052, 053: ~50-90h
- TD-QA-061 (chaos tests): 16-24h
- G-010 (axe-core E2E): 2-4h
- G-011 (Lighthouse CI): 4-8h

### P3 — Strategic (sprints 7+, ~80-150h, semanas 14-18+)

Polish + long-term. Custo: R$ 12.000 — R$ 22.500.

- TD-FE-007 (RSC opportunistic): 40-56h
- TD-FE-010 (i18n deferred): TBD
- TD-DB-023, 030, 032, 033: ~6-15h
- TD-SYS-030, 031, 032: ~8-12h
- TD-FE-030, 031, 032: ~6-13h
- G-012 (mutation testing): 8-16h
- G-013 (fuzz testing): 4-8h

---

## 3. Plano de Resolução

### Sequenciamento Crítico (NÃO REORDENAR)

```
Sprint 0 (semana 1):
  TD-DB-040 (cron monitoring)
       ↓
  TD-DB-004, 013, 014 (cron schedules) + smoke test
  TD-FE-006 (kanban a11y)
  TD-SYS-001 (SIGSEGV kickoff)

Sprint 1 (semanas 2-3):
  TD-QA-064 (Pydantic→TS) — PRECEDE TD-FE-001
       ↓
  Quick wins (TD-FE-005, 016, 050, 051; TD-DB-010, 011, 022;
              TD-SYS-012, 017, 018; TD-FE-013)

Sprint 2 (semanas 4-5):
  TD-SYS-005 (search.py decompose) [paralelo com:]
  TD-FE-001 (TS strict + any progressive)
  TD-QA-060, 062, 063 (test infra)

Sprint 3 (semanas 6-7):
  TD-SYS-014 (LLM async — DEPENDS on TD-SYS-005 done)
  TD-FE-002 (Shepherd a11y)
  TD-FE-004 (hex cleanup)
  TD-SYS-003 (Railway timeout)
  TD-SYS-002 (PNCP detect)
```

### Ondas de Resolução

| Onda | Foco                        | Sprints | Esforço     | Custo R$           |
|------|-----------------------------|---------|-------------|--------------------|
| 1    | P0 — Production Critical    | 0       | 12-30h      | 1.800 — 4.500     |
| 2    | P1 — Critical Path          | 1-3     | 110-200h    | 16.500 — 30.000   |
| 3    | P2 — Maintainability        | 4-6     | 80-140h     | 12.000 — 21.000   |
| 4    | P3 — Strategic              | 7+      | 80-150h     | 12.000 — 22.500   |
| **TOTAL** |                       | 12-18 sem | **282-520h**| **42.300 — 78.000** |

---

## 4. Riscos e Mitigações (do QA Review)

| Risco | Mitigação |
|-------|-----------|
| R-001: TD-SYS-005 + TD-SYS-014 simultâneo | Sequenciar: 005 primeiro, depois 014. |
| R-002: TD-DB-011 sem TD-DB-040 monitoring | Bundle ambos no mesmo PR ou monitoring antes. |
| R-003: TD-FE-001 sem TD-QA-064 type gen | TD-QA-064 precede TD-FE-001 (pode reduzir 30-50% esforço). |
| R-004: TD-SYS-001 + Sentry/OTEL change | Feature flag toggle + canary deploy + rollback ready. |
| R-005: TD-DB-004 sem monitoring | Smoke test pós-deploy + alerts. |
| R-006: A11y bundle requer screen reader real | Sprint A11y dedicada + parceria tester acessibilidade. |
| R-007: TD-SYS-002 PNCP externo | TD-QA-062 contract tests + alert response shape. |

---

## 5. Critérios de Sucesso (Definition of Done para Epic)

### Métricas Mensuráveis

| Métrica                       | Atual               | Meta                |
|-------------------------------|---------------------|---------------------|
| Backend test coverage         | ~70%                | 80%                 |
| Frontend test coverage        | ~60%                | 75%                 |
| TypeScript `any` count        | 296                 | <50                 |
| ARIA violations (axe-core)    | desconhecido        | 0 críticas          |
| Lighthouse Performance        | desconhecido        | >85                 |
| Lighthouse Accessibility      | desconhecido        | >95                 |
| Visual regression diff        | n/a                 | <1%                 |
| pg_cron job success rate      | desconhecido        | >99% (com alerts)   |
| Sentry POST error rate        | alto (CRIT-080)     | <0.1% requests      |
| LLM monthly cost              | uncapped            | budget definido     |
| pncp_raw_bids storage         | risco unbounded     | <300MB sustained    |

### Critérios Globais

1. ✅ Zero failures em backend pytest (mantém política existente)
2. ✅ Zero failures em frontend jest
3. ✅ All Playwright passing + novos E2E billing
4. ✅ Lighthouse CI verde (LCP <2.5s, FID <100ms, CLS <0.1)
5. ✅ Visual regression Percy <1% diff em rotas core
6. ✅ axe-core 0 violations em rotas core
7. ✅ pg_cron monitoring com Sentry alerts ativos

---

## 6. Estimativas Finais

### Esforço

- **Mínimo**: 282h (sweet spot)
- **Realista**: 400h
- **Máximo**: 520h

### Custo (a R$150/hora)

- **Mínimo**: R$ 42.300
- **Realista**: R$ 60.000
- **Máximo**: R$ 78.000

### Timeline (1 dev full-time, 30h/semana líquido)

- **Mínimo**: 10 semanas
- **Realista**: 13-14 semanas
- **Máximo**: 17-18 semanas

### Timeline com 2 devs (50h/semana líquido somando)

- **Realista**: 8-10 semanas

---

## 7. Recomendações Finais

1. **Tratar P0 imediatamente** (semana 1) — bloqueios de produção e storage. Custo <R$5K.
2. **Não deferir P1 além de 6 semanas** — dívida acumulada exponencializa risco.
3. **Definir budget LLM mensal** (TD-SYS-018) antes de ANY launch maior — proteger downside.
4. **WCAG 2.1 AA é compliance B2G** (TD-FE-006, 050, 051) — bloqueio de vendas enterprise.
5. **TypeScript strict (TD-FE-001)** é o ROI mais alto — destrava velocity.
6. **TD-QA-064 (Pydantic→TS)** PRECEDE TD-FE-001 — evita esforço duplicado.
7. **Bundle relacionados em PRs** (sprint a11y, sprint cleanup, sprint perf) — reduz overhead de review.
8. **Métricas antes/depois** — Phase 9 (relatório executivo) deve usar para narrativa ROI.

---

**Status**: ✅ FINAL — pronto para Phase 9 (executive report) e Phase 10 (Epic + Stories).
