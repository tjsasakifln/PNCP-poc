# Epic: Resolucao de Debitos Tecnicos -- SmartLic
**ID:** EPIC-DEBT
**Data:** 2026-03-20
**Owner:** Engineering Team
**Status:** PLANNED

## Objetivo

Resolver sistematicamente os 81 debitos tecnicos identificados na Brownfield Discovery, eliminando riscos de seguranca (CORS wildcard, Stripe IDs hardcoded), desbloqueando velocidade do time (test pollution), e estabelecendo fundacao arquitetural (component library, async PNCP, API versioning) para escalar o SmartLic de beta para producao com clientes pagantes.

## Escopo
- 81 debitos tecnicos identificados (CRITICAL: 2, HIGH: 14, MEDIUM: 28, LOW: 37)
- ~280h de esforco estimado
- 4 sprints planejados (Sprint 0 + 1 + 2 + Backlog)
- 3 areas: Sistema (~102h), Database (~27h), Frontend (~151h)

## Criterios de Sucesso

| Metrica | Baseline (hoje) | Meta pos-remediacao |
|---------|-----------------|---------------------|
| Backend tests | 7332 pass / 0 fail | >= 7332 pass / 0 fail |
| Frontend tests | 5583 pass / 0 fail | >= 5583 pass / 0 fail |
| E2E tests | 60 pass | >= 60 pass |
| Backend coverage | 70%+ (CI gate) | >= 70% |
| Frontend coverage | 60%+ (CI gate) | >= 60% |
| `var(--` in frontend | ~1,754 | <50 |
| UI primitives | 6 | >= 11 |
| CORS unauthorized origins | `*` (all) | 0 (explicit allowlist) |
| Tables without retention | 3+ | 0 |
| a11y critical violations | 0 (axe-core) | 0 (manter) |

## Timeline

| Sprint | Foco | Duracao | Horas | Stories |
|--------|------|---------|-------|---------|
| 0 | Urgente/Security | 1 semana | ~19.5h | DEBT-S0.1, DEBT-S0.2, DEBT-S0.3 |
| 1 | Fundacao | 2 semanas | ~110.5h | DEBT-S1.1, DEBT-S1.2, DEBT-S1.3, DEBT-S1.4 |
| 2 | Otimizacao | 2 semanas | ~107h | DEBT-S2.1, DEBT-S2.2, DEBT-S2.3 |
| Backlog | Melhoria Continua | Ongoing | ~42.5h | DEBT-BL.1, DEBT-BL.2 |

## Stories

### Sprint 0 -- P0 (Imediato, ~19.5h)

| ID | Titulo | Horas | Debt Items |
|----|--------|-------|------------|
| DEBT-S0.1 | Fix main.py/app_factory dual-path + CORS | 4h | SYS-01, SYS-06, SYS-17, SYS-18 |
| DEBT-S0.2 | Security Hardening -- Stripe IDs + Dependencies | 3.5h | DB-01, FE-19 |
| DEBT-S0.3 | Test Infrastructure -- Eliminar Pollution | 12h | SYS-14 |

### Sprint 1 -- P1 (Fundacao, ~110.5h)

| ID | Titulo | Horas | Debt Items |
|----|--------|-------|------------|
| DEBT-S1.1 | PNCP Client Modernization -- Sync to Async | 16h | SYS-02 |
| DEBT-S1.2 | Database Integrity + Backend Hardening | 22.5h | DB-02, DB-06, SYS-05, SYS-08, SYS-09, SYS-10 |
| DEBT-S1.3 | Design System Foundation -- UI Primitives + Tokens | 60h | FE-01, FE-02, FE-07, FE-34 |
| DEBT-S1.4 | Observability e API Versioning | 16h | SYS-04, SYS-07 |

### Sprint 2 -- P2 (Otimizacao, ~107h)

| ID | Titulo | Horas | Debt Items |
|----|--------|-------|------------|
| DEBT-S2.1 | Frontend Architecture -- Components + Hooks | 65h | FE-03, FE-04, FE-06, FE-09, FE-12, FE-14, FE-16, FE-18, FE-20, FE-21, FE-26 |
| DEBT-S2.2 | Backend Cleanup -- Cache, Keywords, Pools | 26h | SYS-03, SYS-11, SYS-12, SYS-13, SYS-16 |
| DEBT-S2.3 | Database Performance + Schema | 16.5h | DB-03, DB-04, DB-08, DB-10, DB-11, DB-13, DB-17, DB-28, DB-30 |

### Backlog -- P3 (Melhoria Continua, ~42.5h)

| ID | Titulo | Horas | Debt Items |
|----|--------|-------|------------|
| DEBT-BL.1 | Code Quality -- Dead Code, Naming, Documentation | 28h | SYS-19, SYS-20, DB-05, DB-09, DB-12, DB-14, DB-15, DB-18, DB-19, DB-21, DB-22, DB-23, DB-24, DB-25, DB-26, DB-27, DB-29, DB-31, FE-05, FE-08, FE-10, FE-11, FE-15, FE-17, FE-23, FE-25, FE-27, FE-28, FE-29, FE-30, FE-32, FE-33 |
| DEBT-BL.2 | Accessibility + UX Polish | 14.5h | FE-24, FE-31, FE-35, FE-36 |

## Riscos

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| main.py/app_factory dual-path: producao roda com middleware incompleta | HIGH | CRITICAL | Investigar em 30min via Railway logs. Se confirmado, wiring app_factory resolve 4 items. |
| CORS fix quebra frontend proxy | MEDIUM | HIGH | Frontend proxy e same-origin, bypassa CORS. Testar com Origin headers via TestClient. |
| PNCP async migration quebra 7332 testes | LOW | CRITICAL | Migrar incrementalmente (1 metodo por vez em feature branch). |
| Component library quebra paginas existentes | MEDIUM | MEDIUM | Sem Storybook, validacao manual. Usar Playwright screenshot comparison. |
| Test pollution fixes quebram testes dependentes de estado poluido | MEDIUM | MEDIUM | Rodar full suite apos cada fix individual. Corrigir em cascata. |

## Dependencies

- **SYS-01** resolve SYS-06, SYS-17, SYS-18 (bundle)
- **FE-34** (Sprint 1) desbloqueia FE-09 e FE-26 (Sprint 2)
- **FE-02** (Sprint 1) desbloqueia FE-01 codemod e FE-03 refactor (Sprint 2)
- **DB-01** (Sprint 0) desbloqueia DB-18 (Backlog)
- **DB-02, DB-08, DB-19** podem ser agrupados em 1 migration

## Caminho Critico

```
SYS-01 (4h) --> SYS-14 (12h) --> FE-34 (2h) --> FE-02 (24h) --> FE-01 (32h) --> FE-03 (16h)
Total: ~90h (~6 semanas com 1 dev FE dedicado)
```

## Gaps Aceitos

8 gaps documentados na assessment e aceitos para o estagio atual (pre-revenue beta, <100 usuarios):
1. Sem consumer-driven contract tests (Pact)
2. LGPD compliance gaps (data retention PII)
3. Rate limiting fallback per-worker in-memory
4. Sem dead letter queue para ARQ jobs
5. Supply chain security nao auditado formalmente
6. OAuth token encryption app-layer only
7. Dependency supply chain nao verificado
8. DDoS resilience nao avaliada

---

*Gerado 2026-03-20 por @pm durante Brownfield Discovery Phase 10.*
*Baseado no Technical Debt Assessment FINAL v1.0.*
