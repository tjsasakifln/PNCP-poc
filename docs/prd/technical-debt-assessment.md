# Technical Debt Assessment - FINAL

**Data:** 2026-03-23
**Autores:** @architect (consolidacao), @data-engineer (DB review), @ux-design-expert (UX review), @qa (validacao)
**Versao:** 1.0 -- Pos-revisao dos especialistas (Phases 5-7 complete)

---

## 1. Resumo Executivo

| Metrica | Valor |
|---------|-------|
| **Total de debitos abertos** | 54 |
| **CRITICAL** | 1 |
| **HIGH** | 9 |
| **MEDIUM** | 27 |
| **LOW** | 17 |
| **Esforco total estimado** | ~196h |
| **Distribuicao** | Sistema: ~82h / Database: ~2.3h / Frontend: ~74h / Cross-cutting: ~38h |
| **Items removidos (ja resolvidos)** | 6 |
| **Items adicionados por especialistas** | 7 |

### Nota de Processo

O DRAFT original (Phase 4) continha 56 items com ~246h de esforco estimado. A revisao por especialistas (Phases 5-7) identificou uma taxa de erro de **18%** (10 de 56 items imprecisos). Os erros mais significativos foram 3 items de banco de dados listados como abertos que ja tinham sido resolvidos por migracoes aplicadas 2-3 semanas antes, e 3 items frontend com severidade superestimada. O processo de revisao multi-fase validou seu valor ao corrigir ~50h de estimativas incorretas.

**Licao aprendida:** Futuras avaliacoes devem incluir verificacao contra `supabase migration list` e inspecao de codigo vivo, nao apenas documentacao estatica.

### Top 10 Items Mais Urgentes

| # | ID | Debito | Sev. | Area | Horas |
|---|-----|--------|------|------|-------|
| 1 | DEBT-324 | Dual Stripe webhook router (audit + fix) | HIGH | Backend | 3 |
| 2 | DEBT-323 | `_plan_status_cache` unbounded dict (memory leak) | CRIT | Backend | 1 |
| 3 | TD-M07 | Landing 13 child components all "use client" | HIGH | Frontend | 10 |
| 4 | DB-H04 | Missing NOT NULL em created_at/updated_at (3 cols) | HIGH | Database | 0.25 |
| 5 | TD-H04 | Pipeline kanban sem screen reader announcements | MED | Frontend | 4 |
| 6 | DEBT-307 | Stripe webhooks monolitico (1192 LOC) | HIGH | Backend | 6 |
| 7 | TD-NEW-01 | Duplicate `id="main-content"` (WCAG 2.4.1) | MED | Frontend | 1 |
| 8 | TD-NEW-02 | Color-only viability indicators (WCAG 1.4.1) | MED | Frontend | 3 |
| 9 | DA-01 | Cache cleanup regressed priority-aware eviction | MED | Database | 0.5 |
| 10 | DEBT-301 | filter/core.py 3871 LOC monolith | HIGH | Backend | 8 |

---

## 2. Inventario Completo de Debitos

### 2.1 Sistema (validado por @architect, spot-checked por @qa)

#### CRITICAL

| ID | Debito | Horas | Impacto | Descricao |
|----|--------|-------|---------|-----------|
| DEBT-323 | `_plan_status_cache` unbounded | 1h | Seguranca/Memoria | `quota.py:44` -- dict cresce sem limite. Diferente de `_token_cache` (LRU 1000) e `_arbiter_cache` (LRU 5000). Pode causar OOM sob alto volume de usuarios. Fix: converter para `functools.lru_cache` ou `cachetools.TTLCache`. |

#### HIGH

| ID | Debito | Horas | Impacto | Descricao |
|----|--------|-------|---------|-----------|
| DEBT-301 | filter/core.py monolitico (3871 LOC) | 8h | Manutencao | Package facade (`filter/`) criado mas `core.py` contem toda a logica. Core matching deveria ser decomposto em submodulos. **Maior risco de regressao** -- 14 test files, 3704 LOC de testes. |
| DEBT-302 | schemas.py monolitico (2121 LOC) | 6h | Manutencao | Todos os Pydantic models de 49 endpoints em um arquivo. Import path changes cascade a todas as routes. |
| DEBT-304 | 68 top-level .py files | 12h | Onboarding | Faltam packages para filtering (11), search (4), PNCP (3). Meta-change -- fazer incrementalmente. |
| DEBT-305 | job_queue.py (2152) + cron_jobs.py (2218) | 6h | Manutencao | Monolitos de jobs/crons. Error handling patterns nao avaliados (gap do QA review). |
| DEBT-307 | Stripe webhooks monolitico (1192 LOC) | 6h | Seguranca | 10+ event types em uma handler function. Dificil auditar logica de billing. Decompor APOS audit do DEBT-324. |
| DEBT-324 | Dual Stripe webhook router registration | 3h | Seguranca | `startup/routes.py` linhas 46 e 70 -- registra router em `/v1/` E root. **Elevado a Batch 0 por recomendacao do QA:** requer audit de 2h para verificar se double-processing ocorreu + 1h fix. Verificar URL configurada no Stripe Dashboard, idempotency keys, e logs de producao. |

#### MEDIUM

| ID | Debito | Horas | Impacto | Descricao |
|----|--------|-------|---------|-----------|
| DEBT-303 | pncp_client.py sync + async dual | 4h | Performance | Importa `requests` junto com `httpx`. Fallback via `asyncio.to_thread()`. |
| DEBT-306 | search_cache.py (2512 LOC) | 4h | Manutencao | L1, L2, SWR, key gen, serialization em um arquivo. |
| DEBT-309 | quota.py (1622 LOC) mixed concerns | 4h | Manutencao | Plan definition + quota + rate limiting + trial em um modulo. |
| DEBT-310 | main.py backward-compat re-exports | 3h | Manutencao | ~75 linhas de proxy classes para testes. |
| DEBT-312 | filter_*.py naming ambiguity | 3h | Manutencao | 11 filter files + filter.py com docstring enganosa. |
| DEBT-313 | ComprasGov v3 dead source | 2h | Performance | Fonte fora do ar desde marco 2026. Timeout budget desperdicado. |
| DEBT-314 | 16 feature flags, possiveis dead flags | 1h | Manutencao | `config/features.py` -- 16 flags (nao 40+ como estimado no DRAFT). Inventariar uso antes de remover. |
| DEBT-315 | 58 API proxies, nem todos usam factory | 4h | Manutencao | `create-proxy-route.ts` existe mas nao e universal. Security header forwarding nao avaliada (gap do QA). |
| DEBT-316 | Onboarding (783) + signup (703) LOC | 4h | Manutencao | Paginas grandes sem decomposicao de componentes. |
| DEBT-317 | clients/ inconsistente | 4h | Manutencao | 5 clients com estrutura variada apesar de `base.py` existir. |
| DEBT-322 | CB configs mislocated | 1h | Manutencao | PCP/ComprasGov circuit breaker configs em `pncp_client.py:56-71`. |
| DEBT-325 | Hardcoded USD_TO_BRL = 5.0 | 0.5h | Manutencao | `llm_arbiter.py:73` -- cost tracking impreciso. Tornar configuravel via env var. |

#### LOW

| ID | Debito | Horas | Impacto | Descricao |
|----|--------|-------|---------|-----------|
| DEBT-308 | api-types.generated.ts (5177 LOC) | 2h | Performance | Verificar tree-shaking. |
| DEBT-311 | Test LOC 1.8x source | 0h (aceito) | Manutencao | Ratio 1.87x e normal para sistemas com billing + multi-source + resilience. QA validou como aceitavel. |
| DEBT-318 | docs/ content currency unknown | 2h audit | Manutencao | Documentacao potencialmente stale. |
| DEBT-319 | scripts/ fora do CI | 1h | Qualidade | Apenas 2-3 scripts operacionais precisam smoke tests (run_tests_safe.py, sync-setores-fallback.js). Reducao de 2h para 1h por recomendacao do QA. |
| DEBT-320 | startup/ compat shim | 1h | Manutencao | `main.py:82-102` track_legacy_routes() duplica logica. |
| DEBT-321 | blog.ts hardcoded (785 LOC) | N/A | Design choice | Conteudo do blog estatico no codigo. Decisao intencional. |

---

### 2.2 Database (validado por @data-engineer)

**Saude geral: 7/10.** Sprints DEBT anteriores resolveram os maiores problemas (FK standardization, RLS auth.role(), trigger consolidation). O que resta e integrity hardening e uma regressao de cache eviction.

**Esforco total: ~2.3h**

#### HIGH

| ID | Debito | Horas | Impacto | Descricao |
|----|--------|-------|---------|-----------|
| DB-H04 + DA-02 | Missing NOT NULL em created_at/updated_at | 0.25h | Integridade | `classification_feedback.created_at`, `user_oauth_tokens.created_at`, `user_oauth_tokens.updated_at` -- todos `DEFAULT now()` sem NOT NULL. INSERT com NULL quebraria ORDER BY, pg_cron retention, e analytics. Backfill + ADD NOT NULL em single migration. |

#### MEDIUM

| ID | Debito | Horas | Impacto | Descricao |
|----|--------|-------|---------|-----------|
| DB-H02 | health/incidents sem user RLS | 0.25h | Seguranca | So `service_role` pode ler. Futuro status page ficaria bloqueado. Downgraded de HIGH -- dados operacionais, sem frontend consumer atual. Ship com feature de status page. |
| DB-M04 | Sem CHECK em response_state | 0.17h | Integridade | `search_sessions.response_state` aceita qualquer string. Valores validos: live, cached, degraded, empty_failure. |
| DB-M05 | Sem CHECK em pipeline_stage | 0.17h | Integridade | `search_sessions.pipeline_stage` aceita qualquer string. COMMENT documenta valores mas nao enforces. |
| DA-01 + DB-L05 | Cache cleanup regressed priority-aware eviction | 0.5h | Performance | Migration 032 introduziu eviction por prioridade (hot/warm/cold). DEBT-017 substituiu por FIFO simples com limite 5. Hot entries podem ser evictadas prematuramente. Fix: restaurar priority ordering + limit 10 + short-circuit do DEBT-017. |

#### LOW

| ID | Debito | Horas | Impacto | Descricao |
|----|--------|-------|---------|-----------|
| DB-M02 | organizations.owner_id FK documentation | 0h (doc only) | Manutencao | FK ja aponta para profiles(id) ON DELETE RESTRICT. RESTRICT e intencional. Apenas documentar decisao. |
| DB-M03 | partner_referrals FK verification | 0.17h | Integridade | SET NULL e correto (preserva revenue data apos churn). Verificar estado producao + adicionar COMMENT no FK. |
| DB-M07 | subscription_status enum mapping | 0.17h | Manutencao | Trigger existe e funciona. Adicionar COMMENT documentando mapping para futuros devs. |
| DB-L01 | Migration naming + .bak file | 0.08h | Manutencao | Dois padroes coexistem. Arquivo `008_rollback.sql.bak` ainda presente. |
| DB-L03 + DA-03 | Missing COMMENTs + SCHEMA.md stale | 0.33h | Manutencao | Tabelas antigas sem COMMENT. `organization_members.user_id` documentado como auth.users mas ja aponta para profiles. |
| DA-04 | partners sem updated_at column | 0.17h | Manutencao | Tabela nao tem `updated_at`. Baixa prioridade -- dados mudam raramente (admin-only). |

---

### 2.3 Frontend/UX (validado por @ux-design-expert)

**Saude geral: 7/10.** Patterns de UX core (loading states, error handling, resilience banners, onboarding) sao solidos. A maior divida e a landing page client-rendered e missing screen reader announcements no pipeline.

**Esforco total: ~74h** (68h itens originais ajustados + 6h novos items)

#### HIGH

| ID | Debito | Horas | Impacto UX | Descricao |
|----|--------|-------|------------|-----------|
| TD-M07 | Landing 13 child components all "use client" | 10h | **Major** | **Upgraded de MEDIUM.** Landing page.tsx e Server Component, mas todos 13 filhos usam "use client". Apenas 3 precisam de Framer Motion. Os outros 10 usam "use client" apenas para useState/useEffect/useInView. Maior ROI de performance -- acquisition funnel entry point. Fix: islands pattern (RSC wrapper + client animation children). |
| TD-H02 | Dual header/auth pattern | 4h | Minor | `/buscar` bypassa `(protected)/layout.tsx`. Logica duplicada, UI inconsistente. Resolver junto com TD-NEW-01. |

#### MEDIUM

| ID | Debito | Horas | Impacto UX | Descricao |
|----|--------|-------|------------|-----------|
| TD-H01 | Protected pages RSC data fetching | 10h | Moderate | **Downgraded de HIGH.** Landing, blog, legal, pricing, features, sobre JA sao Server Components. O DRAFT "zero RSC" era falso. Debito real: 26 protected pages poderiam beneficiar de RSC data fetching. Esforco reduzido de 16h para 10h. |
| TD-H04 | Pipeline kanban sem screen reader announcements | 4h | Moderate | **Downgraded de HIGH.** Keyboard DnD JA funciona (`KeyboardSensor` + `sortableKeyboardCoordinates`). Falta apenas `accessibility` prop no `DndContext` com custom announcements + `aria-roledescription="sortable"` nos cards. Esforco reduzido de 8h para 4h. |
| TD-M01 | 22 `any` types em 15 arquivos | 4h | None (DX) | SavedSearchesDropdown, OrgaoFilter, MunicipioFilter, AnalyticsProvider, LoginForm, ErrorDetail. |
| TD-M02 | ValorFilter.tsx (478 LOC) | 3h | None (DX) | Mixing currency formatting + dual-slider + presets. |
| TD-M03 | EnhancedLoadingProgress (391 LOC) | 3h | None (DX) | Multi-phase loading + UF grid + fallback em um componente. |
| TD-M04 | useFeatureFlags custom cache | 2h | None (DX) | Implementa cache proprio ao inves de usar SWR (ja disponivel). |
| TD-M05 | Raw CSS var usage (~40 instancias) | 3h | None (DX) | `bg-[var(--surface-0)]` ao inves de `bg-surface-0`. Quebra Tailwind intellisense. |
| TD-M06 | 87 localStorage sem registry | 2h | None (DX) | Sem constantes centralizadas. Risco de colisao. |
| TD-M08 | ProfileCompletionPrompt (638 LOC) | 3h | None (DX) | Componente grande precisa decomposicao. |
| TD-NEW-01 | Duplicate `id="main-content"` | 1h | Moderate | 3 arquivos definem `<main id="main-content">`. Viola HTML spec e quebra skip navigation (WCAG 2.4.1). Quick fix com alto impacto a11y. |
| TD-NEW-02 | Color-only viability indicators | 3h | Moderate | Viability badges usam cor como unico diferenciador. WCAG 1.4.1 exige texto/icones alem de cor. Afeta ~8% dos usuarios masculinos (daltonismo). |

#### LOW

| ID | Debito | Horas | Impacto UX | Descricao |
|----|--------|-------|------------|-----------|
| TD-H03 | Remaining aria-live gaps (granular SSE) | 2h | Minor | **Downgraded de HIGH.** O DRAFT dizia "sem aria-live para SSE" -- FALSO. 16 aria-live regions ja existem no modulo de busca. Gap restante: anuncios granulares de progresso SSE (ex: quando cada UF completa) e "novos resultados disponiveis". |
| TD-L01 | Sem a11y unit tests (jest-axe) | 4h | Minor | Apenas 2 Playwright axe-core E2E specs. Instalar jest-axe ANTES de Batch 3. |
| TD-L02 | Skeleton coverage gaps | 4h | Minor | Admin sub-pages, alertas, mensagens sem skeletons. |
| TD-L03 | useOnboarding.tsx extension | 0.5h | None | Hook sem JSX deveria ser `.ts`. |
| TD-L04 | Missing error.tsx (3 pages) | 2h | Minor | Onboarding, signup, login sem error boundaries. 9 error.tsx ja existem (reduzido de 3h para 2h). |
| TD-L05 | TourInviteBanner inline | 0.5h | None | Definido dentro de SearchResults.tsx. |
| TD-L06 | Blog TODO placeholders | 4h | None (conteudo) | 60+ TODOs de internal linking em 30 artigos. |
| TD-L07 | Search hooks complexity | 4h (docs) | None (DX) | 3287 LOC em 9 hooks. Falta dependency graph documentado. |
| TD-NEW-03 | Shepherd.js loaded eagerly | 2h | Minor | ~15KB importado em todas as protected pages mesmo apos tour completo. Usar `next/dynamic` para lazy load. |

---

### 2.4 Cross-Cutting (atualizado com correcoes)

| ID | Debito | Areas | Impacto | Descricao |
|----|--------|-------|---------|-----------|
| XC-02 | Monolith decomposition | Backend + Tests | Manutencao | DEBT-301/302/305/306/307/309 sao todos >1500 LOC. Decomposicao afeta 143K LOC de testes. Usar facade preservation pattern. |
| XC-03 | Server Components migration | Frontend | Performance | TD-H01 + TD-M07 sao INDEPENDENTES (correcao do QA). TD-M07 (landing) nao depende de TD-H01 (protected). |
| XC-04 | Feature flags cleanup | Backend + Frontend | Manutencao | DEBT-314 (16 flags) -- inventariar uso em FE e BE antes de remover qualquer flag. |
| XC-05 | API proxy standardization | Frontend + Backend | Manutencao | DEBT-315 (58 proxies). Security header forwarding e um gap nao avaliado. |
| XC-06 | A11y compliance | Frontend + Legal | Acessibilidade | TD-H04 + TD-NEW-01 + TD-NEW-02 + TD-H03. SmartLic e B2B privado (Lei 13.146/2015 nao obriga diretamente), mas expansao para governo exigiria WCAG 2.1 AA. |
| XC-07 | Dead source cleanup | Backend + Frontend | Performance | DEBT-313 (ComprasGov down). Frontend source indicators, backend timeouts, health dashboard. |

**Removido:** XC-01 (FK standardization) -- FKs ja estao padronizadas para profiles. Migration `20260304100000` + verification `20260311100000` confirmam resolucao.

---

## 3. Matriz de Priorizacao Final

Classificacao: Impacto (1-5) x Urgencia (1-5) / Esforco normalizado. Incorpora todas as correcoes dos especialistas.

### Quick Wins (Alto impacto, baixo esforco)

| Rank | ID | Debito | Sev. | Horas | ROI |
|------|-----|--------|------|-------|-----|
| 1 | DEBT-323 | Unbounded plan cache -> LRU | CRIT | 1 | 5/5 |
| 2 | DB-H04+DA-02 | NOT NULL em 3 timestamp columns | HIGH | 0.25 | 5/5 |
| 3 | DA-01+DB-L05 | Restore priority-aware cache eviction | MED | 0.5 | 4/5 |
| 4 | DB-M04+M05 | CHECK constraints em response_state + pipeline_stage | MED | 0.34 | 4/5 |
| 5 | DEBT-322 | Mover CB configs para local correto | MED | 1 | 4/5 |
| 6 | DEBT-325 | USD_TO_BRL configuravel via env | MED | 0.5 | 4/5 |
| 7 | TD-NEW-01 | Fix duplicate id="main-content" | MED | 1 | 4/5 |

### Valor Estrategico (Alto impacto, esforco moderado)

| Rank | ID | Debito | Sev. | Horas | ROI |
|------|-----|--------|------|-------|-----|
| 8 | TD-M07 | Landing page RSC islands | HIGH | 10 | 5/5 |
| 9 | DEBT-307 | Decomp Stripe webhooks | HIGH | 6 | 4/5 |
| 10 | TD-H04 | Pipeline screen reader announcements | MED | 4 | 4/5 |
| 11 | TD-NEW-02 | Viability badge text alternatives | MED | 3 | 4/5 |
| 12 | TD-H02 | Unificar /buscar auth pattern | HIGH | 4 | 3/5 |
| 13 | DEBT-301 | Decomp filter/core.py | HIGH | 8 | 3/5 |
| 14 | DEBT-304 | Backend packaging | HIGH | 12 | 3/5 |

### Melhoria Continua (Medio impacto)

| Rank | ID(s) | Debito | Sev. | Horas |
|------|-------|--------|------|-------|
| 15 | DEBT-302 | Decomp schemas.py | HIGH | 6 |
| 16 | DEBT-305 | Decomp job_queue + cron_jobs | HIGH | 6 |
| 17 | DEBT-309 | Decomp quota.py | MED | 4 |
| 18 | TD-H01 | Protected pages RSC data fetching | MED | 10 |
| 19 | TD-M01 | Eliminar `any` types | MED | 4 |
| 20 | TD-M05 | Tailwind tokens padronizar | MED | 3 |
| 21 | TD-M04 | useFeatureFlags -> SWR | MED | 2 |
| 22 | DEBT-313 | ComprasGov dead source cleanup | MED | 2 |
| 23 | DEBT-314 | Feature flag audit (16 flags) | MED | 1 |

### Backlog (Baixa urgencia)

Todos os items LOW ficam no backlog para serem priorizados oportunisticamente ou como parte de feature work.

---

## 4. Dependencias entre Debitos

```
DEBT-324 audit ──> DEBT-307 (webhook decomp)
     (audit antes de decompor)

TD-M07 (landing RSC) ──> independente (NAO depende de TD-H01)

TD-H01 (protected RSC) ──> XC-03 (data fetching redesign)

DEBT-304 (packaging) ──> DEBT-301 (filter decomp)
DEBT-304 ──> DEBT-302 (schemas decomp)
DEBT-304 ──> DEBT-305 (job/cron decomp)

DEBT-314 (flag audit) ──> XC-04 (FE/BE flag sync)

DEBT-315 (proxy factory) ──> XC-05 (API standardization)

TD-L01 (jest-axe) ──> previne regressao de TD-H04, TD-NEW-01, TD-NEW-02

TD-H02 (unify /buscar) ──> resolve TD-NEW-01 (duplicate IDs) simultaneamente
```

**Correcao vs DRAFT:** TD-M07 (landing RSC) e TD-H01 (protected RSC) sao INDEPENDENTES. O DRAFT incorretamente encadeava TD-H01 -> TD-M07.

---

## 5. Plano de Resolucao

### Batch 0: Audit (DEBT-324 webhook) -- 3h

**Objetivo:** Verificar se double-processing de Stripe webhooks ocorreu em producao.

| Task | Esforco | Descricao |
|------|---------|-----------|
| Verificar Stripe Dashboard webhook URL(s) | 0.5h | Qual URL esta configurada? Se apenas uma, risco e menor. |
| Analisar logs de producao | 1h | Buscar duplicatas de webhook events (mesmo event_id processado 2x). |
| Verificar idempotency keys | 0.5h | O handler verifica `event.id` contra processamento anterior? |
| Fix: remover registro duplicado | 1h | Remover uma das duas registracoes em `startup/routes.py`. |

**Teste:** Enviar webhook de teste, verificar handler executa exatamente 1x (contar log entries).

### Batch 1: Quick Wins -- ~5h

| ID | Debito | Horas | Teste Requerido |
|----|--------|-------|-----------------|
| DEBT-323 | Plan cache -> LRU/TTLCache | 1h | Unit test: inserir 1001 entries, verificar eviction. Test concurrency com threading. |
| DB-H04+DA-02 | NOT NULL em 3 timestamp columns | 0.25h | Migration: backfill NULLs + ADD NOT NULL. Verificar `COUNT(*) WHERE created_at IS NULL = 0`. |
| DB-M04+M05 | CHECK constraints | 0.34h | Negative test: INSERT com valor invalido deve falhar com CHECK violation. |
| DA-01+DB-L05 | Cache eviction priority + limit 10 | 0.5h | Inserir 11 entries com mixed priorities. Cold evicted first. Hot sobrevive. |
| DEBT-322 | Mover CB configs | 1h | Regression test: CB behavior inalterado. |
| DEBT-325 | USD_TO_BRL env var | 0.5h | Config test: env var override + fallback 5.0. |
| TD-NEW-01 | Fix duplicate main-content ID | 1h | DOM validation: nenhum duplicate ID. jest-axe ou Playwright `page.$$eval('[id]')`. |
| DB extras | COMMENTs + FK docs + .bak cleanup | 0.5h | Doc-only changes. |

**Migration file:** `supabase/migrations/YYYYMMDD100000_debt_db_integrity_phase5.sql` (idempotent, zero downtime).

### Batch 2: Landing Performance -- 10h

| ID | Debito | Horas | Teste Requerido |
|----|--------|-------|-----------------|
| TD-M07 | Landing RSC islands (10 of 13 components) | 10h | Lighthouse CI: LCP < 2.5s, TTFB < 800ms. Visual regression: Playwright screenshots 3 breakpoints (375px, 768px, 1440px), diff < 1%. Bundle size: -40-60KB gzipped client JS. Build: `npm run build` must succeed (RSC import errors caught at build time). |

**Abordagem (validada por UX specialist):**
1. Converter componentes sem hooks primeiro (zero risk)
2. Substituir `useInView` por CSS `animation-timeline: view()` ou lightweight IntersectionObserver
3. Manter 3 client islands para Framer Motion (HeroSection, SectorsGrid, AnalysisExamplesCarousel)
4. Validar com Lighthouse entre cada conversao

### Batch 3: Security/A11y -- 17h

| ID | Debito | Horas | Teste Requerido |
|----|--------|-------|-----------------|
| DEBT-307 | Decomp Stripe webhooks | 6h | Cada event type com handler test proprio. Replay todos os testes existentes de webhook. |
| TD-H04 | Pipeline screen reader announcements | 4h | Playwright a11y: Tab -> Space -> Arrow -> Space. Verificar aria-live announcement text. |
| TD-NEW-02 | Viability badge text alternatives | 3h | Visual test: badges renderizam texto alem de cor (Alta/Media/Baixa). |
| TD-H02 | Unificar /buscar auth | 4h | Verificar header consistente em todas as protected pages. |

**Pre-requisito:** Instalar jest-axe (TD-L01, 4h) antes de iniciar a11y fixes para prevenir regressao.

### Batch 4: Architecture -- 32h

| ID | Debito | Horas | Teste Requerido |
|----|--------|-------|-----------------|
| DEBT-301 | Decomp filter/core.py | 8h | **CRITICAL:** Full test suite antes E depois. `from filter import X` via `__init__.py` DEVE continuar funcionando. 14 test files (3704 LOC). |
| DEBT-304 | Backend packaging (68 files) | 12h | Incremental. `python -c "from <package> import <key_function>"` apos cada move. OpenAPI schema snapshot test. |
| DEBT-302 | Decomp schemas.py | 6h | Verificar todas 49 routes importam corretamente. |
| DEBT-305 | Decomp job_queue + cron_jobs | 6h | Verificar ARQ job discovery. |

**Estrategia:** Facade preservation pattern -- criar nova estrutura, mover codigo, manter re-export `__init__.py`. Cada file move = commit separado + full test suite run. Verificar cobertura >80% nos files alvo antes de comecar (`pytest --cov=filter --cov-report=term-missing`).

### Batch 5: Continued Improvement -- ~46h

| ID(s) | Debito | Horas |
|-------|--------|-------|
| DEBT-309 | Decomp quota.py | 4h |
| DEBT-306 | Decomp search_cache.py | 4h |
| TD-H01 | Protected pages RSC data fetching | 10h |
| TD-M01 | Eliminar `any` types | 4h |
| TD-M05 | Tailwind token standardization | 3h |
| DEBT-303 | pncp_client dual sync/async cleanup | 4h |
| DEBT-315 | API proxy standardization | 4h |
| DEBT-316 | Onboarding + signup decomposition | 4h |
| DEBT-317 | clients/ standardization | 4h |
| DEBT-313 | ComprasGov dead source cleanup | 2h |
| DEBT-314 | Feature flag audit | 1h |
| DEBT-310 | main.py re-exports cleanup | 3h |

### Batch 6: Polish -- ~27h (backlog)

Todos os items LOW, priorizados oportunisticamente:

| ID | Debito | Horas |
|----|--------|-------|
| TD-L01 | jest-axe setup | 4h |
| TD-L02 | Skeleton coverage gaps | 4h |
| TD-L04 | Missing error.tsx (3 pages) | 2h |
| TD-L06 | Blog TODO placeholders | 4h |
| TD-L07 | Search hooks docs | 4h |
| TD-H03 | Remaining aria-live gaps | 2h |
| TD-NEW-03 | Shepherd.js lazy load | 2h |
| DEBT-308 | api-types tree-shaking | 2h |
| DEBT-319 | CI smoke tests (2-3 scripts) | 1h |
| DEBT-320 | startup compat shim | 1h |
| TD-L03, TD-L05 | Extension fix, banner extract | 1h |

---

## 6. Riscos e Mitigacoes

| Risco | Severidade | Mitigacao |
|-------|------------|-----------|
| **Monolith decomposition breaks test imports** | HIGH | Decompor um arquivo de cada vez. Full test suite (7656 tests) apos cada move. Usar facade `__init__.py` para preservar imports. |
| **Dual webhook double-processing corrupted data** | HIGH | Batch 0 audit primeiro. Verificar logs, Stripe Dashboard URL, idempotency. |
| **filter/core.py decomposition regression** | HIGH | Maior risco: 3871 LOC + 14 test files. Preservar `from filter import X`. Verificar cobertura >80% antes. |
| **Landing RSC migration breaks Framer Motion** | MEDIUM | Islands pattern: RSC wrapper + client animation children. Build-time error detection (Next.js fails build if RSC imports client module). Visual regression tests. |
| **Feature flag cleanup removes active flags** | MEDIUM | Grep usage em FE + BE antes de remover. Cross-reference ambos codebases. |
| **Cache eviction fix (DA-01) data loss** | MEDIUM | Testar com volumes de producao. Priority ordering preserva hot entries. |
| **Redis failure modes nao avaliadas** | MEDIUM (gap) | Nao coberto neste assessment. Verificar: CB fail open/closed? Rate limit fail open/closed? Reconexao automatica? Avaliar durante proximo incident review. |

---

## 7. Criterios de Sucesso

### Per-Batch Metrics

| Batch | Criterio | Medicao |
|-------|----------|---------|
| 0 | Zero evidence of double-processing | Log audit: 0 duplicate event_ids processed |
| 1 | All quick wins deployed, zero regressions | 7656 backend tests pass, 5733 frontend tests pass |
| 2 | Landing LCP < 2.5s | Lighthouse CI automated check |
| 2 | Client JS bundle reduced -40KB+ | `npm run build` + `next/bundle-analyzer` comparison |
| 3 | Zero WCAG violations in axe-core scan | Playwright axe-core on /pipeline, /buscar |
| 3 | Webhook handler has per-event-type tests | pytest coverage report shows >90% on webhook handlers |
| 4 | All imports unchanged (facade test) | `python -c "from filter import classificar_resultado"` succeeds |
| 4 | OpenAPI schema unchanged | Snapshot diff test: `openapi_schema.diff.json` |
| 4 | Test suite green after decomposition | 7656 tests, 0 new failures |

### Overall Success Metrics

| Metrica | Antes | Depois (target) |
|---------|-------|-----------------|
| Backend monolith files >1500 LOC | 6 | 0 |
| Frontend HIGH debt items | 2 | 0 |
| CRITICAL items | 1 | 0 |
| WCAG a11y violations (axe-core) | Unknown | 0 (on primary pages) |
| Landing page LCP | >3s (estimated) | <2.5s |
| Open DB integrity items | 4 | 0 |

---

## 8. Items Resolvidos (Nao Incluidos no Inventario)

Os seguintes items foram listados no DRAFT original mas confirmados como ja resolvidos pelos especialistas. Documentados aqui para audit trail e para demonstrar eficacia dos sprints DEBT anteriores.

| ID Original | Debito | Sev. Original | Resolvido Por | Verificado Por |
|-------------|--------|---------------|---------------|----------------|
| DB-C01 | 3 tabelas FK para auth.users ao inves de profiles | CRITICAL | Migration `20260304100000_fk_standardization_to_profiles.sql` + verification `20260311100000` (DEBT-113) | @data-engineer |
| DB-H01 | auth.role() em 6+ RLS policies (pattern deprecated) | HIGH | Migrations `20260304200000` + `20260308300000` (DEBT-009) + verification `20260311100000` | @data-engineer |
| DB-H03 | 3 duplicate updated_at trigger functions | HIGH | Migration `20260304120000_rls_policies_trigger_consolidation.sql` | @data-engineer |
| DB-L02 | Redundant update_updated_at() function | LOW | Migration `20260304120000` (drops duplicates, re-points to set_updated_at()) | @data-engineer |
| TD-M09 | Feature-gated pages routable (/alertas, /mensagens) | MEDIUM | `<ComingSoonPage>` component + `isFeatureGated()` check implemented | @ux-design-expert |
| XC-01 | FK standardization cross-cutting concern | N/A | All FKs standardized to profiles(id) | @data-engineer |

**Impacto da resolucao:** Estes 6 items representavam ~3.3h de trabalho e incluiam o unico item CRITICAL de database (DB-C01). Sua resolucao previa confirma que os sprints DEBT-001 a DEBT-113 foram eficazes.

---

## 9. Gaps Conhecidos (Nao Avaliados)

Os seguintes areas foram identificadas pelo QA review como nao cobertas por este assessment. Devem ser investigadas em futuras avaliacoes ou durante feature work.

| Gap | Area | Descricao | Recomendacao |
|-----|------|-----------|--------------|
| Redis connection resilience | Backend | Nao avaliado: CB fail open/closed? Rate limit fail open/closed? Reconexao automatica? | Avaliar durante proximo incident review ou como parte de reliability story. |
| Error handling em background jobs | Backend | job_queue.py e cron_jobs.py avaliados por tamanho mas nao por patterns de error handling. ARQ nao tem runtime reconnection. | Incluir na decomposicao (DEBT-305). |
| API proxy security headers | Frontend | 58 proxies: forwarding consistente de security headers? Content type validation? Rate limits? | Incluir na padronizacao (DEBT-315). |
| Migration rollback strategy | Database | DB specialist forneceu plano forward sem rollback. Pre-check queries recomendados. | Incluir pre-check `SELECT COUNT(*) WHERE col IS NULL` em migration DB-H04. |

---

*Este documento e o resultado definitivo do workflow Brownfield Discovery (Phases 1-8). Sera usado como input para Phase 9 (executive report por @analyst) e Phase 10 (epic + story creation por @pm).*
