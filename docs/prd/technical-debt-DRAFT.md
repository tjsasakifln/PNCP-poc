# Technical Debt Assessment - DRAFT v2.0

**Projeto:** SmartLic v0.5
**Data:** 2026-03-04
**Autor:** @architect (Atlas) — Consolidacao Fase 4 (Brownfield Discovery v2)
**Status:** DRAFT — Pendente revisao dos especialistas
**Fontes:** system-architecture.md v4.0 (Fase 1), SCHEMA.md + DB-AUDIT.md (Fase 2), frontend-spec.md (Fase 3)
**Delta desde v1 (2026-02-25):** +30 stories shipped, +1208 files changed, 190K insertions

---

## Para Revisao dos Especialistas

Este documento consolida TODOS os debitos tecnicos identificados nas Fases 1-3 do Brownfield Discovery v2. Cada secao precisa de validacao do especialista responsavel antes de se tornar FINAL.

---

## 1. Debitos de Sistema (@architect)

Fonte: `docs/architecture/system-architecture.md` v4.0 — 17 debitos identificados em 5 categorias

### 1.1 Arquitetura (6 debitos)

| ID | Debito | Severidade | Impacto | Esforco Est. |
|----|--------|-----------|---------|-------------|
| TD-A01 | **Rotas montadas 2x** (versioned `/v1/` + legacy root) — 61 `include_router` calls, dobra a tabela de rotas para 120+ endpoints. Sunset 2026-06-01 sem plano de migracao. Frontend ja usa versioned endpoints. | HIGH | Performance + manutencao | 4-8h |
| TD-A02 | **search_pipeline.py god module** — 800+ linhas com helpers inline, cache logic, quota email, item conversion. Cada "stage" tem 50-100+ linhas com try/catch aninhado. | HIGH | Manutencao + testabilidade | 16-24h |
| TD-A03 | **Progress tracker in-memory nao escala horizontalmente** — `_active_trackers` usa asyncio.Queue local. Redis Streams existe mas e fallback. Duas instancias Railway teriam estado dividido. | HIGH | Escalabilidade (blocker para scale-out) | 8-16h |
| TD-A04 | **10 background tasks no lifespan** sem task manager — Cada task tem seu proprio pattern cancel/await. Sem abstracao `TaskRegistry`. | MEDIUM | Manutencao | 8h |
| TD-A05 | **Dual HTTP client PNCP** (sync requests + async httpx) — 1500+ linhas de logica duplicada de retry, circuit breaker, error handling. Sync client usado apenas como fallback via `asyncio.to_thread()`. | MEDIUM | Manutencao | 12-16h |
| TD-A06 | **Lead prospecting modules desconectados** — 5 modulos (lead_prospecting, lead_scorer, lead_deduplicator, contact_searcher, cli_acha_leads) aparentemente dead code. | LOW | Limpeza | 2h |

### 1.2 Inconsistencias de Padrao (5 debitos)

| ID | Debito | Severidade | Esforco |
|----|--------|-----------|---------|
| TD-P01 | **Nomenclatura de migrations inconsistente** — Mix de `001_*.sql` (sequencial) + `20260220120000_*` (timestamped). 73 migrations totais. | MEDIUM | 4h |
| TD-P02 | **Feature flags somente em env vars** — 25+ flags com cache 60s. Sem UI para toggle runtime. Requer restart ou endpoint admin reload. | MEDIUM | 8-12h |
| TD-P03 | **User-Agent hardcoded "BidIQ"** em pncp_client.py — misleading para API providers. | LOW | 0.5h |
| TD-P04 | **pyproject.toml referencia "bidiq-uniformes-backend"** — branding antigo. | LOW | 0.5h |
| TD-P05 | **Arquivos de teste na raiz do backend** — test_pncp_homologados_discovery.py etc. fora de `tests/`. | LOW | 1h |

### 1.3 Abstracoes Faltantes (4 debitos)

| ID | Debito | Severidade | Esforco |
|----|--------|-----------|---------|
| TD-M01 | **Sem lifecycle manager para background tasks** — 10 tasks com create/cancel/await manual. | MEDIUM | 8h |
| TD-M02 | **Sem validacao de contrato API no CI** — openapi-typescript gera types mas sem CI step de drift detection. | MEDIUM | 4-8h |
| TD-M03 | **Sem pre-commit hooks** — Sem `.pre-commit-config.yaml`. Devs podem commitar codigo failing lint/type checks. | LOW | 2h |
| TD-M04 | **Sem lint enforcement no CI backend** — ruff e mypy configurados mas nao no CI. | LOW | 2h |

### 1.4 Escalabilidade (5 debitos)

| ID | Debito | Severidade | Impacto |
|----|--------|-----------|---------|
| TD-S01 | **Railway 1GB com 2 workers** — Cada worker mantem caches in-memory proprios. OOM kills historicos (WEB_CONCURRENCY reduzido de 4 para 2). | HIGH | Estabilidade producao |
| TD-S02 | **PNCP page size reduzido para 50** — API limit change requer 10x mais API calls. Health canary (tamanhoPagina=10) nao detecta este limite. | HIGH | Cobertura de dados |
| TD-S03 | **Auth token cache in-memory nao compartilhado** entre Gunicorn workers — Desperdicio de memoria. | MEDIUM | Eficiencia |
| TD-S04 | **Sem CDN para assets estaticos** — Frontend servido direto do Railway sem edge caching. | MEDIUM | Performance usuario |
| TD-S05 | **`time.sleep(0.3)` sincrono em quota.py** — Bloqueia event loop async. Deveria usar `asyncio.sleep()`. | MEDIUM | Estabilidade |

### 1.5 Seguranca (4 debitos)

| ID | Debito | Severidade | Impacto |
|----|--------|-----------|---------|
| TD-SEC01 | **`unsafe-inline` e `unsafe-eval` no CSP** — Requerido por Next.js + Stripe.js mas enfraquece CSP. Avaliar nonce-based approach. | MEDIUM | Seguranca |
| TD-SEC02 | **Service role key para todas as ops backend** — Bypass RLS intencional para server-to-server mas qualquer vuln backend expoe todos os dados. | LOW | Seguranca |
| TD-SEC03 | **Sem timeout em webhook handler** — Operacoes DB longas no Stripe webhook handler podem bloquear indefinidamente. | LOW | Resiliencia |
| TD-SEC04 | **Temp files Excel no frontend proxy** — Escritos em tmpdir() como fallback, nao limpos em crash. Potencial disk exhaustion. | LOW | Operacional |

---

## 2. Debitos de Database (@data-engineer)

Fonte: `supabase/docs/DB-AUDIT.md` — 23 debitos em 4 severidades

> :warning: **PENDENTE: Revisao do @data-engineer (Fase 5)**

### 2.1 Criticos (2)

| ID | Debito | Tabelas Afetadas | Impacto |
|----|--------|------------------|---------|
| C-01 | **FK para auth.users em vez de profiles** em 6 tabelas novas — Inconsistente com padronizacao (migrations 018, 20260225120000). ON DELETE CASCADE para auth.users bypassa cascades de profile. | search_results_store, mfa_recovery_codes, mfa_recovery_attempts, organizations (owner_id), organization_members, partner_referrals | Integridade de dados, orfaos em disaster recovery |
| C-02 | **health_checks e incidents com RLS habilitado mas ZERO policies** — Somente service_role funciona. Se backend usar anon/authenticated client, operacoes falham silenciosamente. | health_checks, incidents | Seguranca fragil |

### 2.2 Altos (6)

| ID | Debito | Tabelas | Impacto |
|----|--------|---------|---------|
| H-01 | **3 funcoes trigger updated_at duplicadas** — Copias identicas de `update_updated_at()` | pipeline_items, alert_preferences, alerts | Manutencao |
| H-02 | **search_results_store FK nao padronizado** — user_id ref auth.users sem ON DELETE CASCADE | search_results_store | Integridade dados |
| H-03 | **Sem retention para search_results_store** — Coluna `expires_at` existe mas sem pg_cron cleanup. Rows expiradas acumulam indefinidamente. | search_results_store | Storage crescente |
| H-04 | **alert_preferences service_role policy usa auth.role()** em vez de `TO service_role` | alert_preferences | Inconsistencia seguranca |
| H-05 | **reconciliation_log service_role policy usa auth.role()** em vez de padrao `TO service_role` | reconciliation_log | Inconsistencia seguranca |
| H-06 | **organizations e org_members service_role policies usam auth.role()** | organizations, organization_members | Inconsistencia seguranca |

### 2.3 Medios (9)

| ID | Debito | Esforco |
|----|--------|---------|
| M-01 | Sem `updated_at` em 11 tabelas (monthly_quota, search_state_transitions, stripe_webhook_events, classification_feedback, trial_email_log, alert_sent_items, alert_runs, reconciliation_log, health_checks, incidents, mfa_recovery_codes, mfa_recovery_attempts, partner_referrals) | 4h |
| M-02 | Sem indice standalone em `search_state_transitions(created_at)` para retention cleanup | 0.5h |
| M-03 | `partner_referrals` FK sem ON DELETE explicito — defaults to RESTRICT em ambas FKs | 1h |
| M-04 | Sem retention para `mfa_recovery_attempts` — brute force tracking acumula forever | 1h |
| M-05 | Sem retention para `alert_runs` — historico de execucao acumula indefinidamente | 1h |
| M-06 | Sem retention para `alert_sent_items` — dedup tracking cresce ilimitadamente | 1h |
| M-07 | `handle_new_user()` trigger modificado 7x em migrations — alto risco de regressao | 2h |
| M-08 | Nomenclatura inconsistente de CHECK constraints — 4 padroes diferentes | 2h (padronizar future) |
| M-09 | `classification_feedback` admin policy usa `auth.role()` em vez de `TO service_role` | 0.5h |

### 2.4 Baixos (6)

| ID | Debito |
|----|--------|
| L-01 | Indice redundante em alert_preferences.user_id (coberto por UNIQUE constraint) |
| L-02 | Indice redundante em alert_sent_items.alert_id (prefixo de indice UNIQUE composto) |
| L-03 | Sem COMMENT em tabelas novas (organizations, org_members, health_checks, incidents) |
| L-04 | plan_type CHECK constraint reconstruido 6x — considerar reference table |
| L-05 | Stripe Price IDs hardcoded em migrations SQL — nao funciona para staging/dev |
| L-06 | Sem indice composto (user_id, expires_at) em search_results_store |

**Pontos Positivos Database:**
- 100% RLS coverage (32/32 tabelas)
- N+1 patterns ja fixados com RPC functions
- JSONB governance com 2MB limits em cache
- PII hashing para LGPD compliance em audit_events
- Strong index coverage em tabelas de alto trafego

---

## 3. Debitos de Frontend/UX (@ux-design-expert)

Fonte: `docs/frontend/frontend-spec.md` — 38 debitos em 7 categorias

> :warning: **PENDENTE: Revisao do @ux-design-expert (Fase 6)**

### 3.1 Arquitetura de Componentes (7)

| ID | Debito | Severidade | Impacto |
|----|--------|-----------|---------|
| FE-01 | **Mega-componente SearchResults.tsx** (1,581 linhas, 50+ props) — Impossivel manter, testar, revisar | HIGH | Manutencao critica |
| FE-02 | **Mega-componente conta/page.tsx** (1,420 linhas) — Perfil, senha, plano, MFA, cancelamento tudo junto | HIGH | Violacao SRP |
| FE-03 | **Mega-hook useSearch.ts** (1,510 linhas) — Execucao, SSE, retry, error, save, download, Excel, partial, polling | HIGH | Manutencao critica |
| FE-04 | **buscar/page.tsx** (1,019 linhas) — Tours, trials, auto-search, keyboard shortcuts, queuing | MEDIUM | Complexidade |
| FE-05 | **3 diretorios de componentes** sem convencao (`app/components/`, `components/`, `buscar/components/`). Nomes duplicados: EmptyState, LoadingProgress existem em multiplos | MEDIUM | Confusao dev |
| FE-06 | **Sem componente Button compartilhado** — ~15 variantes de estilo inline | MEDIUM | Inconsistencia visual |
| FE-07 | **SVGs inline no Sidebar** (75 linhas) em vez de lucide-react | LOW | Inconsistencia |

### 3.2 State Management (4)

| ID | Debito | Severidade | Impacto |
|----|--------|-----------|---------|
| FE-08 | **Sem data fetching library** — useState + useEffect + fetch manual everywhere. Sem dedup, cache, revalidacao automatica. ~500 linhas de boilerplate eliminavel. | HIGH | Produtividade, confiabilidade |
| FE-09 | **13+ localStorage keys** sem abstracao — Chamadas diretas em 20+ arquivos. Sem migration strategy, sem quota awareness. | MEDIUM | Fragilidade |
| FE-10 | **Prop drilling em SearchResults** — 50+ props de buscar/page.tsx. Sinal claro para context ou composicao. | HIGH | Acoplamento extremo |
| FE-11 | **Ref-based circular dependency workaround** — `clearResultRef` para quebrar dependencia useSearchFilters ↔ useSearch | MEDIUM | Code smell |

### 3.3 Acessibilidade (6)

| ID | Debito | WCAG | Severidade |
|----|--------|------|-----------|
| FE-12 | Missing aria-labels em botoes icon-only do sidebar | 1.1.1 | HIGH |
| FE-13 | SVG icons sem `aria-hidden="true"` (75+ no Sidebar) | 1.1.1 | MEDIUM |
| FE-14 | Viability scores usam cor sem alternativa textual | 1.4.1 | MEDIUM |
| FE-15 | Inputs com placeholder em vez de label (onboarding CNAE) | 1.3.1 | MEDIUM |
| FE-16 | Sem hierarquia de headings auditada — paginas comecam em h3 | 1.3.1 | LOW |
| FE-17 | Sem ARIA live regions para progresso de busca dinamico | 4.1.3 | MEDIUM |

### 3.4 Performance (4)

| ID | Debito | Severidade | Impacto |
|----|--------|-----------|---------|
| FE-18 | **Blog/SEO pages sao CSR** — Todas paginas programaticas usam `"use client"` apesar de conteudo estatico. Derrota proposito de SEO. | HIGH | SEO, Core Web Vitals |
| FE-19 | **Sem dynamic imports** para Recharts (~50KB), Shepherd.js (~25KB), @dnd-kit (~15KB) | MEDIUM | Bundle size |
| FE-20 | **useIsMobile() hydration mismatch risk** — JS check roda apos hydration | LOW | Layout shift |
| FE-21 | **Sem Lighthouse CI** — @lhci/cli configurado mas nao gated no CI | MEDIUM | Performance regressions |

### 3.5 Qualidade de Codigo (5)

| ID | Debito | Severidade |
|----|--------|-----------|
| FE-22 | **Hardcoded Portuguese strings** em 44 paginas — sem i18n | HIGH |
| FE-23 | **eslint-disable react-hooks/exhaustive-deps** em 3+ locais | MEDIUM |
| FE-24 | **APP_NAME redeclarado** em 5+ arquivos | LOW |
| FE-25 | **Import patterns mistos** para constantes (inline vs centralizado) | LOW |
| FE-26 | **Sem TypeScript paths** — imports relativos 3+ niveis `../../../hooks/` | LOW |

### 3.6 Design System Ausente (6)

| ID | Gap | Impacto |
|----|-----|---------|
| FE-27 | Sem Button component compartilhado | 15+ variantes inline |
| FE-28 | Sem Input component compartilhado | Cada form estilo proprio |
| FE-29 | Sem Card component compartilhado | Padroes variam |
| FE-30 | Sem Badge component compartilhado | Multiplas implementacoes |
| FE-31 | Sem Storybook / documentacao visual | Descoberta de componentes |
| FE-32 | **Design tokens parcialmente adotados** — Mix de var(--brand-blue), text-brand-blue, hex raw | Inconsistencia |

### 3.7 UX Inconsistencies (6)

| ID | Debito | Severidade |
|----|--------|-----------|
| FE-33 | Search page header/footer proprio vs NavigationShell das demais | MEDIUM |
| FE-34 | 2 padroes empty state (componente vs JSX inline) | LOW |
| FE-35 | Toast (sonner) vs inline banners sem criterio | LOW |
| FE-36 | Loading spinner size/style varia (h-8, h-6, w-5) | LOW |
| FE-37 | Date formatting: date-fns vs Intl.DateTimeFormat vs toLocaleDateString | LOW |
| FE-38 | Currency formatting: utility existe mas alguns formatam inline | LOW |

**Pontos Positivos Frontend:**
- WCAG contrast ratios documentados e verificados
- Error recovery patterns abrangentes (auto-retry, SSE fallback, search queuing)
- Dark mode com anti-flash script
- 2,681 testes unitarios + 22 E2E passando com 0 falhas
- Educational loading carousel (UX-411) para tempo percebido
- Security headers no middleware
- 44px touch targets enforced globalmente

---

## 4. Matriz de Priorizacao Preliminar

### Tier 0 — Quick Wins de Seguranca/Estabilidade (imediato, <1 sprint)

| # | ID | Debito | Area | Esforco | Justificativa |
|---|-----|--------|------|---------|--------------|
| 1 | C-01 | FK auth.users → profiles (6 tabelas) | DB | 4h | Integridade dados |
| 2 | C-02 | RLS sem policies (2 tabelas) | DB | 2h | Seguranca |
| 3 | TD-S05 | time.sleep() bloqueando event loop | Backend | 1h | Estabilidade |
| 4 | H-03 | Retention search_results_store | DB | 2h | Storage |
| 5 | H-01 | Consolidar trigger functions duplicadas | DB | 2h | Limpeza |
| 6 | H-04/05/06 | Padronizar service_role policies (4 tabelas) | DB | 2h | Seguranca |
| 7 | FE-12 | aria-labels em botoes icon-only | Frontend | 2h | Acessibilidade |
| 8 | TD-P03/04 | Branding BidIQ → SmartLic | Backend | 1h | Profissionalismo |
| **Total Tier 0** | | | | **~16h** | |

### Tier 1 — Debitos Estruturais (proximo sprint)

| # | ID | Debito | Area | Esforco |
|---|-----|--------|------|---------|
| 9 | TD-A01 | Remover legacy routes (manter so /v1/) | Backend | 4-8h |
| 10 | FE-01 | Decompor SearchResults.tsx | Frontend | 12-16h |
| 11 | FE-03 | Decompor useSearch.ts | Frontend | 12-16h |
| 12 | FE-08 | Adotar data fetching library (SWR/TanStack) | Frontend | 16-24h |
| 13 | FE-10 | Eliminar prop drilling SearchResults (context) | Frontend | 8h |
| 14 | FE-18 | Converter SEO pages para SSG/ISR | Frontend | 8-12h |
| 15 | FE-02 | Decompor conta/page.tsx | Frontend | 8-12h |
| 16 | TD-A02 | Refatorar search_pipeline.py | Backend | 16-24h |
| 17 | TD-A03 | Migrar progress tracker para Redis Streams | Backend | 8-16h |
| 18 | TD-S01 | Otimizar memoria Railway (shared caches) | Backend | 4-8h |
| **Total Tier 1** | | | | **~97-146h** |

### Tier 2 — Melhorias de Qualidade (2-3 sprints)

| # | ID | Debito | Area | Esforco |
|---|-----|--------|------|---------|
| 19 | FE-27-32 | Design system primitives (Button, Input, Card, Badge) | Frontend | 16-24h |
| 20 | FE-22 | Iniciar i18n abstraction | Frontend | 24-40h |
| 21 | TD-A05 | Eliminar dual HTTP client PNCP | Backend | 12-16h |
| 22 | TD-P02 | Feature flags admin UI | Backend | 8-12h |
| 23 | M-01 | updated_at em 11 tabelas | DB | 4h |
| 24 | M-04/05/06 | Retention pg_cron (3 tabelas) | DB | 3h |
| 25 | FE-13/14/15/17 | Acessibilidade restante (4 itens) | Frontend | 8h |
| 26 | FE-19 | Dynamic imports heavy deps | Frontend | 4h |
| 27 | TD-M02 | API contract CI validation | Backend | 4-8h |
| 28 | FE-33 | Unificar navigation pattern | Frontend | 4h |
| **Total Tier 2** | | | | **~87-125h** |

### Tier 3 — Backlog (baixa prioridade)

IDs: TD-A04, TD-A06, TD-P01, TD-P05, TD-M01, TD-M03, TD-M04, TD-S02, TD-S03, TD-S04, TD-SEC01-04, M-02, M-03, M-07, M-08, M-09, L-01 a L-06, FE-04, FE-05, FE-06, FE-07, FE-09, FE-11, FE-16, FE-20, FE-21, FE-23-26, FE-34-38

**Total Tier 3:** ~65-85h

---

## 5. Perguntas para Especialistas

### Para @data-engineer (Fase 5):

1. **C-01:** A migracao das 6 FKs pode ser feita em uma unica migration ou precisa ser faseada? Impacto em dados existentes? Downtime esperado?
2. **C-02:** health_checks e incidents sao acessados SOMENTE via service_role hoje? Existe plano para status page client-side?
3. **H-03:** Qual o volume esperado de search_results_store? Retention de 24h ou 7 dias? Row count atual?
4. **M-07:** O trigger handle_new_user() deve ser migrado para application layer (backend Python) para reduzir risco de regressao?
5. **L-04:** Vale migrar CHECK constraint para reference table (plan_types) dado que estamos pre-revenue com mudancas frequentes?
6. **M-04/05/06:** Qual retention adequada para mfa_recovery_attempts (30d?), alert_runs (90d?), alert_sent_items (90d?)?
7. **Performance:** search_results_store.results nao tem CHECK de tamanho como search_results_cache (2MB). Deve ter?

### Para @ux-design-expert (Fase 6):

1. **FE-01/02/03:** Estrategia de decomposicao preferida? Context API vs prop reduction vs sub-routes vs composition?
2. **FE-08:** SWR vs TanStack Query — dado que temos SSE patterns customizados, qual se integra melhor?
3. **FE-18:** Converter SEO pages para Server Components — quais dependencias bloqueiam SSR? Quais precisam de `"use client"` boundary?
4. **FE-22:** Para o momento (pre-revenue, mercado 100% BR), vale iniciar i18n ou esperar validacao de mercado internacional?
5. **FE-27-32:** Design system — Shadcn/ui vs Radix vs build from scratch com Tailwind primitives? Considerando que ja temos tokens CSS.
6. **FE-33:** Unificar search page dentro do NavigationShell ou manter layout separado? Quais UX tradeoffs?
7. **FE-10:** Para eliminar prop drilling no SearchResults — Context vs Zustand slice vs composition pattern?

---

## 6. Resumo Quantitativo

| Metrica | Valor |
|---------|-------|
| **Total de debitos identificados** | **63** |
| Criticos (C) | 2 |
| Altos (H/HIGH) | 16 |
| Medios (M/MEDIUM) | 23 |
| Baixos (L/LOW) | 22 |
| | |
| **Por area** | |
| Backend/Infra | 24 debitos (~100-140h) |
| Database | 23 debitos (~25-35h) |
| Frontend/UX | 38 debitos (~155-205h) |
| | |
| **Esforco total estimado** | **~280-380 horas** |
| Tier 0 (imediato) | ~16h |
| Tier 1 (proximo sprint) | ~97-146h |
| Tier 2 (2-3 sprints) | ~87-125h |
| Tier 3 (backlog) | ~65-85h |

---

## 7. Dependencias entre Debitos

```
C-01 (FK padronizacao) ─── bloqueia ──→ H-02 (search_results_store FK)
                                    └──→ M-03 (partner_referrals FK)

TD-A01 (remover legacy routes) ─── habilita ──→ TD-M02 (API contract validation)

FE-01 (SearchResults decomp) ──── requer ────→ FE-10 (eliminar prop drilling)
                              └── requer ────→ FE-06 (Button component)
                              └── requer ────→ FE-27-30 (design primitives)

FE-03 (useSearch decomp) ──── requer ────→ FE-08 (data fetching library)

FE-18 (SSG/ISR) ──── independente (pode iniciar paralelo)

TD-A02 (pipeline refactor) ──── requer ────→ TD-A03 (progress tracker Redis)
```

---

*DRAFT v2.0 gerado em 2026-03-04 pelo @architect (Atlas). Pendente validacao das Fases 5, 6 e 7.*
