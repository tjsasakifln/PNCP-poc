# EPIC: Resolucao de Debito Tecnico — SmartLic v0.5

**Data de criacao:** 2026-03-04
**Owner:** @pm (Manager)
**Assessment base:** `docs/prd/technical-debt-assessment.md` v3.0 FINAL
**Commit base:** `4da1d98` (main)

---

## Objetivo

Resolver os 69 debitos tecnicos identificados no assessment v3.0, priorizados por risco ao negocio e complexidade. O trabalho esta dividido em 4 tiers, sendo que este epic cobre Tier 0 (quick wins) e Tier 1 (debitos estruturais) — os que impactam diretamente estabilidade, manutencao e velocidade de desenvolvimento.

**Por que agora:** O SmartLic esta em fase pre-revenue com trials beta. Debitos criticos (FK apontando para auth.users, mega-componentes bloqueando iteracao frontend, rotas legadas duplicadas) aumentam risco de regressao a cada feature nova e dificultam onboarding de desenvolvedores.

## Escopo

### Incluido (Tier 0 + Tier 1)

**Tier 0 — Quick Wins (2 stories, ~20h):**
- FK standardization em 6 tabelas (C-01, H-02, M-03)
- search_results_store hardening: retention pg_cron + composite index (H-03, L-06)
- RLS policies explicitas para health_checks/incidents (C-02)
- Trigger functions duplicadas consolidadas (H-01)
- Acessibilidade sidebar: aria-labels + aria-hidden (FE-12, FE-13)
- Branding cleanup: BidIQ -> SmartLic (TD-P03, TD-P04)
- SVGs inline -> lucide-react (FE-07)
- APP_NAME consolidacao (FE-24)

**Tier 1 — Estruturais (6 stories, ~140-190h):**
- RLS policy standardization: 8 tabelas auth.role() -> TO service_role (H-04/05/06, M-09, DA-01/02)
- Legacy routes removal (TD-A01)
- Design system foundation: Button via Shadcn/ui (FE-27) + prop grouping (FE-10)
- Hook test coverage + useSearch decomposition (FE-41, FE-03)
- SearchResults decomposition (FE-01)
- SWR adoption + pipeline refactor foundation (FE-08, TD-A02)

### Excluido (Tier 2 + 3 — epics futuros)
- Design system primitives alem de Button (Input, Card, Badge)
- conta/page.tsx decomposition
- Dual PNCP client elimination
- Feature flags admin UI
- i18n, Storybook, visual regression testing
- CSP hardening, CDN, load testing

## Criterios de Sucesso

### Tier 0 — Definition of Done
- [ ] Zero FK references to auth.users (all 6 tabelas -> profiles)
- [ ] search_results_store pg_cron cleanup running daily (4am UTC, 7d retention)
- [ ] All 32 tables have explicit RLS policies (no zero-policy tables)
- [ ] Zero duplicated trigger functions
- [ ] Axe accessibility audit passes for sidebar navigation
- [ ] No "BidIQ" string in production User-Agent or pyproject.toml

### Tier 1 — Definition of Done
- [ ] Zero legacy route mounts (only /v1/ prefixed)
- [ ] SearchResults.tsx < 300 linhas
- [ ] useSearch.ts < 300 linhas (orchestrator only)
- [ ] SWR integrated for all GET endpoints
- [ ] Shared Button component used across all pages
- [ ] All auth.role() RLS policies migrated to TO service_role
- [ ] Hook isolation tests for top 5 hooks (useSearch, useSearchFilters, usePipeline, useFetchWithBackoff, useTrialStatus)
- [ ] All 5774+ backend tests pass, 2681+ frontend tests pass (zero regressions)

## Timeline

| Fase | Stories | Estimativa | Sprint |
|------|---------|------------|--------|
| **Tier 0** | TD-001, TD-002 | ~20h | Sprint 1 (semana 1-2) |
| **Tier 1a** (DB + Backend) | TD-003, TD-004 | ~14h | Sprint 2 (semana 3-4) |
| **Tier 1b** (Frontend foundation) | TD-005, TD-006 | ~28-40h | Sprint 2-3 (semana 3-6) |
| **Tier 1c** (Frontend decomposition) | TD-007, TD-008 | ~48-78h | Sprint 3-4 (semana 5-8) |

**Total estimado:** 6-8 semanas para Tier 0 + Tier 1 completos.

**Sequencia obrigatoria frontend (validada por @qa):**
```
TD-005 (Button + prop grouping) -> TD-007 (SearchResults decomp)
TD-006 (hook tests + useSearch decomp) -> TD-008 (SWR adoption)
```

DB e Backend stories (TD-001 a TD-004) podem progredir em paralelo ao frontend.

## Budget

| Area | Horas (codigo) | Horas (testes) | Total |
|------|----------------|----------------|-------|
| Database | 12.5h | 3h | 15.5h |
| Backend | 5-9h | 3h | 8-12h |
| Frontend | 79-110h | 35h | 114-145h |
| **Total** | **96-132h** | **41h** | **137-172h** |

**Custo estimado:** ~R$27,400 - R$34,400 (considerando R$200/h dev senior)

## Stories

| ID | Titulo | Tier | Area | Horas | Status |
|----|--------|------|------|-------|--------|
| **STORY-TD-001** | FK Standardization + search_results_store Hardening | 0 | Database | 10.5h | To Do |
| **STORY-TD-002** | RLS + Trigger Cleanup + Accessibility + Branding | 0 | DB/FE/BE | 7.5h | To Do |
| **STORY-TD-003** | RLS Policy Standardization (8 tabelas auth.role()) | 1 | Database | 2h | To Do |
| **STORY-TD-004** | Remove Legacy Routes | 1 | Backend | 4-8h | To Do |
| **STORY-TD-005** | Frontend Design System Foundation (Button + Prop Grouping) | 1 | Frontend | 10-14h | To Do |
| **STORY-TD-006** | Hook Test Coverage + useSearch Decomposition | 1 | Frontend | 26-34h | To Do |
| **STORY-TD-007** | SearchResults Decomposition | 1 | Frontend | 14-18h | To Do |
| **STORY-TD-008** | SWR Adoption + Pipeline Refactor Foundation | 1 | Frontend/BE | 44-60h | To Do |

---

## Riscos

| Risco | Prob. | Impacto | Mitigacao |
|-------|-------|---------|-----------|
| FE-03 + FE-08 compound breakage (SSE integration) | HIGH | CRITICAL | Sequenciar: TD-006 -> TD-008. Nunca em paralelo. |
| C-01 FK re-pointing com usuarios beta ativos | MEDIUM | HIGH | NOT VALID + VALIDATE (zero downtime). Orphan query antes. Deploy 4am UTC. |
| FE-01 SearchResults decomp quebra 268 testes | HIGH | HIGH | Snapshot antes. Suite completa apos cada sub-componente. |
| TD-A01 legacy routes quebra consumidores | LOW | MEDIUM | Railway access logs antes. Deprecation counter metric. |
| FE-27 Shadcn/ui modifica tailwind.config | MEDIUM | MEDIUM | Build + visual check em todas 33 paginas apos setup. |

---

*Epic criado em 2026-03-04 pelo @pm (Manager).*
*Baseado no Technical Debt Assessment v3.0 FINAL, aprovado por @architect + @qa.*
