# Technical Debt Assessment — FINAL v3.0

**Projeto:** SmartLic v0.5
**Data:** 2026-03-04
**Autor:** @architect (Atlas) — Fase 8 Brownfield Discovery v2
**Status:** FINAL — Aprovado pelo QA com 4 condicoes (todas incorporadas)
**Revisores:** @data-engineer (Fase 5), @ux-design-expert (Fase 6), @qa (Fase 7)
**Commit base:** `4da1d98` (main)
**Supersedes:** v2.0 FINAL (2026-02-25)

---

## Executive Summary

| Metrica | Valor |
|---------|-------|
| **Total de debitos** | **69** (24 backend, 26 database, 41 frontend, 6 testing — deduplicated, net of removals) |
| Criticos | 1 (C-01) |
| Altos | 12 |
| Medios | 28 |
| Baixos | 28 |
| **Esforco total (codigo)** | **~269-374h** |
| **Esforco total (testes)** | **~59.5h** |
| **Grand total** | **~328-434h** |

### Destaques

- **1 debito critico:** FK para auth.users em 6 tabelas (risco de integridade em disaster recovery)
- **Top 3 frontend:** SearchResults.tsx (1,581 linhas), useSearch.ts (1,510 linhas), conta/page.tsx (1,420 linhas) — mega-componentes que bloqueiam manutencao
- **Correcao importante:** FE-18 (Blog CSR) **removido** — verificado que paginas SEO ja sao Server Components
- **Correcao importante:** TD-S05 (time.sleep) **removido** — ja corrigido (asyncio.sleep em quota.py)
- **i18n adiado:** Downgraded para LOW (pre-revenue, mercado 100% BR)
- **Design system:** Shadcn/ui recomendado pelo @ux-design-expert como base

---

## 1. Inventario Completo de Debitos

### 1.1 Sistema (validado por @architect) — 23 debitos

| ID | Debito | Severidade | Horas | Tier |
|----|--------|-----------|-------|------|
| TD-A01 | Rotas montadas 2x (/v1/ + legacy root) — 61 include_router, 120+ endpoints | HIGH | 4-8h | 1 |
| TD-A02 | search_pipeline.py god module — 800+ linhas | HIGH | 24-32h | 1 |
| TD-A03 | Progress tracker in-memory nao escala — blocker para horizontal scaling | HIGH | 8-16h | 1 |
| TD-A04 | 10 background tasks no lifespan sem task manager | MEDIUM | 8h | 3 |
| TD-A05 | Dual HTTP client PNCP (sync + async) — logica duplicada | MEDIUM | 12-16h | 2 |
| TD-A06 | Lead prospecting modules desconectados — possivel dead code | LOW | 2h | 3 |
| TD-P01 | Migration naming inconsistente (sequencial + timestamped) | MEDIUM | 4h | 3 |
| TD-P02 | Feature flags somente em env vars — sem UI toggle | MEDIUM | 8-12h | 2 |
| TD-P03 | User-Agent hardcoded "BidIQ" | LOW | 0.5h | 0 |
| TD-P04 | pyproject.toml referencia "bidiq-uniformes-backend" | LOW | 0.5h | 0 |
| TD-P05 | Arquivos de teste na raiz do backend | LOW | 1h | 3 |
| TD-M01 | Sem lifecycle manager para background tasks | MEDIUM | 8h | 3 |
| TD-M02 | Sem validacao de contrato API no CI | MEDIUM | 4-8h | 2 |
| TD-M03 | Sem pre-commit hooks | LOW | 2h | 3 |
| TD-M04 | Sem lint enforcement no CI backend | LOW | 2h | 3 |
| TD-S01 | Railway 1GB com 2 workers — OOM historico | HIGH | 4-8h | 1 |
| TD-S02 | PNCP page size 50 — requer 10x mais API calls | HIGH | N/A (API limit) | 3 |
| TD-S03 | Auth token cache nao compartilhado entre workers | MEDIUM | 4h | 3 |
| TD-S04 | Sem CDN para assets estaticos | MEDIUM | 4-8h | 3 |
| TD-SEC01 | unsafe-inline/eval no CSP | MEDIUM | 8h | 3 |
| TD-SEC02 | Service role key para todas ops backend | LOW | N/A | 3 |
| TD-SEC03 | Sem timeout em webhook handler | LOW | 2h | 3 |
| TD-SEC04 | Temp files Excel no frontend proxy | LOW | 2h | 3 |

> **Removido:** TD-S05 (time.sleep sincrono) — ja corrigido, verificado por @qa (asyncio.sleep em quota.py linhas 1467, 1557, 1624)

### 1.2 Database (validado por @data-engineer) — 26 debitos

| ID | Debito | Severidade | Horas | Tier |
|----|--------|-----------|-------|------|
| **C-01** | **FK para auth.users em vez de profiles (6 tabelas)** — search_results_store, mfa_recovery_codes, mfa_recovery_attempts, organizations, org_members, partner_referrals | **CRITICAL** | 6-8h | 0 |
| C-02 | health_checks + incidents: RLS sem policies (service_role only) | HIGH | 2h | 0 |
| H-01 | 3 trigger functions updated_at duplicadas | HIGH | 2h | 0 |
| H-02 | search_results_store FK sem CASCADE (subsumed by C-01) | HIGH | — | 0 |
| H-03 | Sem retention para search_results_store (expires_at decorativo) | HIGH | 2h | 0 |
| H-04 | alert_preferences service_role usa auth.role() | MEDIUM | 0.5h | 1 |
| H-05 | reconciliation_log service_role usa auth.role() | MEDIUM | 0.5h | 1 |
| H-06 | organizations + org_members service_role usa auth.role() | MEDIUM | 0.5h | 1 |
| DA-01 | partners + partner_referrals service_role usa auth.role() (**novo**) | MEDIUM | 0.5h | 1 |
| DA-02 | search_results_store service_role usa auth.role() (**novo**) | MEDIUM | — | 1 |
| DA-03 | health_checks + incidents sem retention pg_cron (**novo**) | MEDIUM | 1h | 2 |
| M-01 | Sem updated_at em 3 tabelas (monthly_quota, mfa_recovery_codes, partner_referrals) | MEDIUM | 1.5h | 2 |
| M-02 | Sem indice standalone search_state_transitions(created_at) | MEDIUM | 0.5h | 2 |
| M-03 | partner_referrals FK sem ON DELETE (subsumed by C-01) | MEDIUM | — | 0 |
| M-04 | Sem retention mfa_recovery_attempts (30d) | MEDIUM | 1h | 2 |
| M-05 | Sem retention alert_runs (90d) | MEDIUM | 1h | 2 |
| M-06 | Sem retention alert_sent_items (180d) | MEDIUM | 1h | 2 |
| M-07 | handle_new_user() trigger modificado 7x — regression risk | MEDIUM | 3h | 2 |
| M-08 | CHECK constraint naming inconsistente | LOW | 1h | 3 |
| M-09 | classification_feedback admin policy usa auth.role() | MEDIUM | 0.5h | 1 |
| L-01 | Indice redundante alert_preferences.user_id | LOW | 0.5h | 3 |
| L-02 | Indice redundante alert_sent_items.alert_id | LOW | 0.5h | 3 |
| L-03 | Sem COMMENT em tabelas novas | LOW | 1h | 3 |
| L-04 | plan_type CHECK reconstruido 6x | LOW | 2h | 3 |
| L-05 | Stripe Price IDs hardcoded em migrations | LOW | 2h | 3 |
| L-06 | Sem indice composto (user_id, expires_at) search_results_store | LOW | 0.5h | 0 |

> **Nota @data-engineer:** auth.role() pattern afeta 8 tabelas no total (nao 5 como no DRAFT). M-01 reduzido de 11 para 3 tabelas (somente as que recebem UPDATE). H-02 e M-03 subsumidos por C-01.

### 1.3 Frontend/UX (validado por @ux-design-expert) — 41 debitos

| ID | Debito | Severidade | Horas | Tier | UX Impact |
|----|--------|-----------|-------|------|-----------|
| FE-01 | SearchResults.tsx mega-componente (1,581 linhas, ~55 props) | HIGH | 14-18h | 1 | High |
| FE-02 | conta/page.tsx mega-componente (1,420 linhas) | MEDIUM | 8-12h | 2 | Medium |
| FE-03 | useSearch.ts mega-hook (1,510 linhas) | HIGH | 14-18h | 1 | High |
| FE-04 | buscar/page.tsx (1,019 linhas) | MEDIUM | 6-8h | 2 | Medium |
| FE-05 | 3 diretorios componentes sem convencao | MEDIUM | 4-6h | 2 | Low |
| FE-06 | Sem Button component (= FE-27) | HIGH | 6-8h | 1 | High |
| FE-07 | SVGs inline Sidebar (75 linhas) | LOW | 2h | 0 | Low |
| FE-08 | Sem data fetching library (SWR recomendado) | HIGH | 20-28h | 1 | High |
| FE-09 | 13+ localStorage keys sem abstracao | LOW | 4-6h | 3 | Low |
| FE-10 | Prop drilling SearchResults (55 props) | HIGH | 6-8h | 1 | High |
| FE-11 | Ref-based circular dependency workaround | LOW | 2-3h | 3 | Low |
| FE-12 | Missing aria-labels botoes icon-only sidebar | HIGH | 1.5h | 0 | Critical |
| FE-13 | SVG icons sem aria-hidden (Sidebar) | MEDIUM | 0.5h | 0 | Medium |
| FE-14 | Viability scores cor sem texto alternativo | MEDIUM | 2h | 1 | Medium |
| FE-15 | Inputs com placeholder em vez de label | MEDIUM | 2h | 1 | Medium |
| FE-16 | Sem hierarquia headings auditada | LOW | 2h | 3 | Low |
| FE-17 | Sem ARIA live regions para progresso busca | MEDIUM | 2h | 2 | Medium |
| FE-19 | Sem dynamic imports (Recharts, Shepherd, dnd-kit) | MEDIUM | 3-4h | 2 | Medium |
| FE-20 | useIsMobile() hydration mismatch | LOW | 1h | 3 | Low |
| FE-21 | Sem Lighthouse CI gated | MEDIUM | 3h | 2 | Medium |
| FE-22 | Hardcoded Portuguese (44 paginas) | LOW | 24-40h | 3 | Low |
| FE-23 | eslint-disable exhaustive-deps (3+ locais) | LOW | 1h | 3 | Low |
| FE-24 | APP_NAME redeclarado 5+ arquivos | LOW | 0.5h | 0 | Low |
| FE-25 | Import patterns mistos | LOW | 1h | 3 | Low |
| FE-26 | Sem TypeScript paths | LOW | 1h | 3 | Low |
| FE-27 | Sem Button compartilhado (Shadcn/ui) | HIGH | 4-6h | 1 | High |
| FE-28 | Sem Input compartilhado | MEDIUM | 3-4h | 2 | Medium |
| FE-29 | Sem Card compartilhado | MEDIUM | 2-3h | 2 | Medium |
| FE-30 | Sem Badge compartilhado | MEDIUM | 2-3h | 2 | Low |
| FE-31 | Sem Storybook | LOW | 8-12h | 3 | Low |
| FE-32 | Design tokens parcialmente adotados | MEDIUM | 3-4h | 2 | Medium |
| FE-33 | Search page navigation vs NavigationShell | MEDIUM | 4-6h | 2 | Medium |
| FE-34 | 2 padroes empty state | LOW | 1h | 3 | Low |
| FE-35 | Toast vs inline banners sem criterio | LOW | 2h | 3 | Low |
| FE-36 | Loading spinner size/style varia | LOW | 1h | 3 | Low |
| FE-37 | Date formatting inconsistente | LOW | 2h | 3 | Low |
| FE-38 | Currency formatting inconsistente | LOW | 1h | 3 | Low |
| FE-39 | Dashboard charts sem mobile layout (**novo**) | MEDIUM | 4-6h | 2 | Medium |
| FE-40 | Missing dynamic imports alem de TotpVerification (**novo**) | MEDIUM | 2h | 2 | Medium |
| FE-41 | Sem hook isolation tests — 19 hooks, 0 testes isolados (**novo**) | MEDIUM | 12-16h | 1 | Medium |
| FE-42 | Alert creation form sem mobile optimization (**novo**) | LOW | 3h | 3 | Low |

> **Removido:** FE-18 (Blog/SEO pages CSR) — Verificado por @ux + @qa: todas as paginas blog/SEO ja sao Server Components.

### 1.4 Testing (novos, identificados por @qa) — 6 debitos

| ID | Debito | Severidade | Horas | Tier |
|----|--------|-----------|-------|------|
| TD-T01 | Sem E2E para MFA, organizations, alerts, partners | MEDIUM | 12-16h | 2 |
| TD-T02 | Backend test pollution patterns (sys.modules, singleton leak) | MEDIUM | 8-12h | 2 |
| TD-T03 | Sem hook isolation tests (= FE-41) | MEDIUM | — | — |
| TD-T04 | Sem visual regression testing (Chromatic/Percy) | LOW | 8h | 3 |
| TD-T05 | Sem dependency security scanning no CI | MEDIUM | 2h | 2 |
| TD-T06 | Sem load testing baseline automatizado | LOW | 4h | 3 |

---

## 2. Plano de Resolucao por Tier

### Tier 0 — Quick Wins (~14h codigo + 6h testes = 20h)

**Timeline:** 1 sprint (1-2 semanas)

| # | IDs | Descricao | Area | Horas |
|---|-----|-----------|------|-------|
| 1 | C-01 + H-02 + M-03 | Migration 1: FK standardization (6 tabelas → profiles, NOT VALID + VALIDATE) | DB | 6-8h |
| 2 | H-03 + L-06 | Migration 2: search_results_store retention (pg_cron 4am UTC, 7d retention, 2MB CHECK, composite index) | DB | 2.5h |
| 3 | C-02 | Add explicit service_role policies to health_checks + incidents | DB | 1h |
| 4 | H-01 | Consolidar 3 trigger functions duplicadas | DB | 1h |
| 5 | FE-12 + FE-13 | aria-labels em botoes icon-only + aria-hidden em SVGs sidebar | Frontend | 2h |
| 6 | TD-P03 + TD-P04 | Branding BidIQ → SmartLic (User-Agent + pyproject.toml) | Backend | 1h |
| 7 | FE-07 | Replace inline SVGs com lucide-react | Frontend | 1.5h |
| 8 | FE-24 | APP_NAME consolidar em lib/constants | Frontend | 0.5h |

### Tier 1 — Debitos Estruturais (~105-155h codigo + 35h testes = 140-190h)

**Timeline:** 2-3 sprints

**Sequencia obrigatoria frontend (validada por @qa):**
```
FE-27 (Button) → FE-10 (prop grouping) → FE-41 (hook tests) → FE-01 (SearchResults decomp)
FE-41 (hook tests) → FE-03 (useSearch decomp) → FE-08 (SWR adoption)
```

| # | ID | Descricao | Horas |
|---|-----|-----------|-------|
| 1 | H-04/05/06 + M-09 + DA-01/02 | Migration 3: RLS policy standardization (8 tabelas auth.role() → TO service_role) | 2h |
| 2 | TD-A01 | Remover legacy routes (manter /v1/ only) — verificar Railway logs antes | 4-8h |
| 3 | FE-27 (= FE-06) | Button component via Shadcn/ui (prerequisito FE-01) | 4-6h |
| 4 | FE-10 | Prop grouping em SearchResults (55 → 6-8 typed objects) | 6-8h |
| 5 | FE-14 + FE-15 | Viability text alternatives + form labels | 4h |
| 6 | FE-41 | Hook isolation tests para useSearch + hooks criticos (prerequisito FE-03) | 12-16h |
| 7 | FE-01 | Decomposicao SearchResults.tsx (ResultCard, ResultsList, ResultsToolbar, etc.) | 14-18h |
| 8 | FE-03 | Decomposicao useSearch.ts (useSearchExecution, useSearchSSE, useSearchRetry, useSearchExport, useSearchPersistence) | 14-18h |
| 9 | FE-08 | Adotar SWR — migrar endpoints GET primeiro (/me, /plans, /analytics, /pipeline), depois mutations | 20-28h |
| 10 | TD-A02 | Refatorar search_pipeline.py (800+ linhas → stages modulares) | 24-32h |
| 11 | TD-A03 | Migrar progress tracker para Redis Streams (primary, in-memory fallback) | 8-16h |
| 12 | TD-S01 | Otimizar memoria Railway (shared caches cross-worker via Redis) | 4-8h |

### Tier 2 — Melhorias de Qualidade (~85-120h codigo + 18.5h testes = 103-139h)

**Timeline:** 2-4 sprints

| # | ID | Descricao | Horas |
|---|-----|-----------|-------|
| 1 | FE-28/29/30 | Design system primitives (Input, Card, Badge) | 7-10h |
| 2 | FE-02 | Decomposicao conta/page.tsx (sub-routes: /perfil, /seguranca, /plano) | 8-12h |
| 3 | FE-32 + FE-33 | Design token consolidation + navigation unification | 7-10h |
| 4 | TD-A05 | Eliminar dual HTTP client PNCP | 12-16h |
| 5 | TD-P02 | Feature flags admin UI | 8-12h |
| 6 | FE-19 + FE-40 | Dynamic imports (Recharts, Shepherd, dnd-kit, etc.) | 5-6h |
| 7 | FE-04 | Decomposicao buscar/page.tsx | 6-8h |
| 8 | FE-05 | Convencao de diretorios componentes | 4-6h |
| 9 | DA-03 + M-04/05/06 | Migration 4: Retention pg_cron (health_checks 30d, mfa 30d, alert_runs 90d, alert_sent 180d) | 3h |
| 10 | M-01 + M-02 | Migration 5: updated_at (3 tabelas) + index created_at | 2h |
| 11 | M-07 | Integration test handle_new_user() + CI guard | 3h |
| 12 | TD-M02 | API contract CI validation | 4-8h |
| 13 | FE-17 + FE-21 | ARIA live regions + Lighthouse CI | 5h |
| 14 | TD-T01 | E2E coverage: MFA, organizations, alerts, partners | 12-16h |
| 15 | TD-T02 | Backend test pollution cleanup | 8-12h |
| 16 | TD-T05 | Dependency security scanning (pip-audit + npm audit) | 2h |
| 17 | FE-39 | Dashboard charts mobile layout | 4-6h |

### Tier 3 — Backlog (~65-85h)

IDs: TD-A04, TD-A06, TD-P01, TD-P05, TD-M01, TD-M03, TD-M04, TD-S02, TD-S03, TD-S04, TD-SEC01-04, M-08, L-01 a L-05, FE-09, FE-11, FE-16, FE-20, FE-22, FE-23, FE-25, FE-26, FE-31, FE-34-38, FE-42, TD-T04, TD-T06

---

## 3. Grafo de Dependencias (Corrigido)

```
DATABASE:
  C-01 (FK padronizacao) ──→ H-02, M-03 (subsumidos)
  L-06 (composite index) ──→ H-03 (retention job)
  M-02 (created_at index) ──→ M-04/05/06 (retention jobs)

BACKEND:
  TD-A01 (remover legacy routes) ──→ TD-M02 (API contract CI)
  TD-A02 (pipeline refactor) ╎╎ TD-A03 (progress tracker) — INDEPENDENTES (decoupled per @qa)

FRONTEND (sequencia obrigatoria):
  FE-27 (Button) ──→ FE-01 (SearchResults decomp)
  FE-10 (prop grouping) ──→ FE-01 (SearchResults decomp)
  FE-41 (hook tests) ──→ FE-03 (useSearch decomp) ──→ FE-08 (SWR adoption)

CROSS-AREA:
  Nenhuma dependencia — DB, Backend, e Frontend podem progredir em paralelo
```

> **Correcao @qa:** DRAFT original tinha FE-03 requerendo FE-08. Ordem correta e INVERSA: decompor useSearch primeiro, depois adotar SWR nos hooks decompostos. Tambem: TD-A02 e TD-A03 sao independentes (pipeline refactor nao requer mudar progress tracking).

---

## 4. Riscos e Mitigacoes

| Risco | Areas | Prob. | Impacto | Mitigacao |
|-------|-------|-------|---------|-----------|
| FE-03 + FE-08 compound breakage da integracao SSE | Frontend + Backend | HIGH | CRITICAL | Sequenciar: FE-41 → FE-03 → estabilizar → FE-08. Nunca em paralelo. |
| TD-A02 + TD-A03 mudancas simultaneas no core | Backend + SSE | MEDIUM | CRITICAL | Tratar como independentes. Pipeline refactor nao exige mudar progress tracking. |
| C-01 FK re-pointing com usuarios beta ativos | Database | MEDIUM | HIGH | NOT VALID + VALIDATE (zero downtime). Orphan detection query antes. Deploy 4am UTC. |
| FE-01 SearchResults decomp quebra 268 testes frontend | Frontend | HIGH | HIGH | Snapshot tests antes da decomposicao. Rodar suite completa apos cada sub-componente extraido. |
| TD-A01 remover legacy routes quebra consumidores desconhecidos | Backend | LOW | MEDIUM | Verificar Railway access logs para chamadas non-/v1/. Deprecation metric counter antes. |
| FE-27 Shadcn/ui modifica tailwind.config | Frontend build | MEDIUM | MEDIUM | Testar build + visual regression em todas 33 paginas apos setup. |

---

## 5. Criterios de Sucesso

### Tier 0 (definicao de "done")
- [ ] Zero FK references to auth.users (all 6 → profiles)
- [ ] search_results_store pg_cron cleanup running daily
- [ ] All 32 tables have explicit RLS policies (no zero-policy tables)
- [ ] Zero duplicated trigger functions
- [ ] Axe accessibility audit passes for sidebar navigation
- [ ] No "BidIQ" string in production User-Agent

### Tier 1 (definicao de "done")
- [ ] Zero legacy route mounts (only /v1/)
- [ ] SearchResults.tsx < 300 linhas
- [ ] useSearch.ts < 300 linhas (orchestrator)
- [ ] SWR integrated for all GET endpoints
- [ ] Shared Button component used across all pages
- [ ] All auth.role() policies → TO service_role
- [ ] Hook isolation tests for top 5 hooks
- [ ] All 5774+ backend tests pass, 2681+ frontend tests pass

### Tier 2 (definicao de "done")
- [ ] Design system primitives (Button, Input, Card, Badge) documented
- [ ] conta/page.tsx decomposed into sub-routes
- [ ] Single PNCP client (async only)
- [ ] Retention jobs running for 4+ tables
- [ ] E2E coverage for MFA, organizations, alerts
- [ ] Dependency security scanning in CI

---

## 6. Esforco por Area e Tier

| Area | Tier 0 | Tier 1 | Tier 2 | Tier 3 | Total |
|------|--------|--------|--------|--------|-------|
| **Database** | 10.5h | 2h | 9h | 7.5h | **29h** |
| **Backend** | 1h | 36-56h | 24-36h | 22-30h | **83-123h** |
| **Frontend** | 4h | 75-106h | 50-72h | 35-55h | **164-237h** |
| **Testing** | 6h | 35h | 18.5h | 12h | **71.5h** |
| **Total por Tier** | **21.5h** | **148-199h** | **101.5-135.5h** | **76.5-104.5h** | **347-460h** |

---

## Anexos

- `docs/architecture/system-architecture.md` — Arquitetura completa (Fase 1)
- `supabase/docs/SCHEMA.md` — Schema de 32 tabelas (Fase 2)
- `supabase/docs/DB-AUDIT.md` — Audit de database (Fase 2)
- `docs/frontend/frontend-spec.md` — Especificacao frontend (Fase 3)
- `docs/prd/technical-debt-DRAFT.md` — DRAFT consolidado (Fase 4)
- `docs/reviews/db-specialist-review.md` — Revisao @data-engineer (Fase 5)
- `docs/reviews/ux-specialist-review.md` — Revisao @ux-design-expert (Fase 6)
- `docs/reviews/qa-review.md` — QA review (Fase 7)

---

*Assessment FINAL v3.0 gerado em 2026-03-04 pelo @architect (Atlas).*
*Aprovado pelo @qa (Guardian) com todas as 4 condicoes incorporadas.*
*Pronto para: Fase 9 (Relatorio Executivo) e Fase 10 (Planning).*
