# Technical Debt Assessment - FINAL

**Projeto:** SmartLic
**Data:** 2026-03-20
**Versao:** 1.0
**Status:** FINAL -- Validado por @architect, @data-engineer, @ux-design-expert, @qa

---

## Executive Summary

- **Total de debitos:** 81 (79 originais - 6 removidos + 8 adicionados)
- **Por severidade:** CRITICAL: 2 | HIGH: 14 | MEDIUM: 28 | LOW: 37
- **Esforco total estimado:** ~280h
- **Por area:** Sistema ~102h | Database ~27h | Frontend ~151h
- **Achado mais critico:** Dual-path `main.py` / `app_factory.py` -- producao pode rodar com CORS `*` e middleware stack incompleta. Investigacao imediata necessaria.

### Mudancas em Relacao ao DRAFT

| Fase | Acao | Quantidade |
|------|------|-----------|
| Phase 5 (@data-engineer) | Removidos (falsos positivos) | 3 (DB-07, DB-16, DB-20) |
| Phase 5 (@data-engineer) | Adicionados | 4 (DB-28 a DB-31) |
| Phase 5 (@data-engineer) | Severidade ajustada | 8 items |
| Phase 6 (@ux-design-expert) | Removidos (falsos positivos) | 2 (FE-13, FE-22) |
| Phase 6 (@ux-design-expert) | Adicionados | 4 (FE-33 a FE-36) |
| Phase 6 (@ux-design-expert) | Severidade ajustada | 11 items |
| Phase 7 (@qa) | Duplicata removida | 1 (SYS-15 = FE-03) |
| Phase 7 (@qa) | Prioridade elevada | SYS-14 para P0 |
| Phase 7 (@qa) | Escopo alterado | SYS-01 (CORS) requer investigacao dual-path |
| Phase 7 (@qa) | Gaps documentados | 5 areas nao cobertas |

---

## Inventario Completo de Debitos

### Sistema (validado por @architect + @qa)

| # | ID | Debito | Severidade | Horas | Prioridade | Status |
|---|------|--------|------------|-------|------------|--------|
| 1 | SYS-01 | **CORS permite todas origens (`*`) + dual-path main.py/app_factory.** `main.py` tem `allow_origins=["*"]`, `app_factory.py` tem CORS correto via `get_cors_origins()`. Producao roda `main:app` (o stub). Investigar se `app_factory` e dead code. Se sim, wiring `app_factory` como entry point resolve SYS-01, SYS-06, SYS-17, SYS-18 simultaneamente. | CRITICAL | 4h | P0 | Escopo alterado por @qa -- requer investigacao antes de fix |
| 2 | SYS-02 | **PNCP client usa `requests` sincrona.** Confirmado: `pncp_client.py` linha 8 ainda tem `import requests` apesar do commit DEBT-107. Mitigado por `asyncio.to_thread()`. Adequado para escala atual (2 workers). | HIGH | 16h | P1 | Rebaixado de CRITICAL por @qa -- mitigacao existente adequada |
| 3 | SYS-03 | **ComprasGov v3 offline sem monitoramento.** Fora do ar desde 2026-03-03 (17 dias). Health check para API que pode nao voltar e low ROI. | MEDIUM | 2h | P2 | Rebaixado de CRITICAL por @qa -- cron check de 15min suficiente |
| 4 | SYS-04 | **Metricas Prometheus efemeras.** Resetam a cada deploy (in-memory). Sem SLO tracking persistente. `reconciliation_log` tabela ja persiste dados de reconciliacao no DB. | HIGH | 8h | P1 | Mantido |
| 5 | SYS-05 | **Health canary nao detecta PNCP page size limit.** Canary usa `tamanhoPagina=10`, passa mesmo quando max mudou de 500 para 50. | HIGH | 4h | P1 | Mantido |
| 6 | SYS-06 | **Route registration nao visivel em main.py.** `main.py` mostra apenas root + health. 38 modulos de rotas registrados via pattern nao visivel do entry point. | HIGH | 0h | P0 | Bundled com SYS-01 (resolver via app_factory) |
| 7 | SYS-07 | **Versionamento de API inconsistente.** Algumas rotas usam `/v1/`, maioria nao. Sem negociacao de versao. | HIGH | 8h | P1 | Mantido |
| 8 | SYS-08 | **Sem request timeout no nivel da aplicacao.** Gunicorn 180s, Railway ~300s, mas sem middleware de timeout por request. | HIGH | 4h | P1 | Mantido |
| 9 | SYS-09 | **Worker liveness depende do Redis.** `_worker_alive_cache` verifica via Redis. Fallback inline funciona, mas sem alerta para ausencia prolongada. | HIGH | 4h | P1 | Mantido |
| 10 | SYS-10 | **Search decomposition backward-compat re-exports.** DEBT-115 decompos `routes/search.py` em 4 sub-modulos com re-exports frageis. | HIGH | 4h | P1 | Mantido |
| 11 | SYS-11 | **`filter.py` keyword sets hardcoded.** `KEYWORDS_UNIFORMES` default hardcoded ao lado de keywords setoriais do YAML. | MEDIUM | 4h | P2 | Mantido |
| 12 | SYS-12 | **Multiplas implementacoes de cache.** `search_cache.py`, `cache.py`, `redis_pool.py`, `auth.py`, `llm_arbiter.py`, `quota.py` -- cada um com logica propria. | MEDIUM | 8h | P2 | Mantido |
| 13 | SYS-13 | **Sem version tracking de migrations em runtime.** CI cobre (`migration-check.yml`), mas sem assertion de schema version no startup do backend. | MEDIUM | 4h | P2 | Mantido |
| 14 | SYS-14 | **Test pollution documentada mas nao eliminada.** 8+ padroes (sys.modules, importlib.reload, MagicMock leakage, global singletons). `run_tests_safe.py --parallel` mitiga cross-file, mas intra-file persiste. 4 quota tests flaky. | MEDIUM | 12h | **P0** | Elevado a P0 por @qa -- bloqueia velocidade de todo o time |
| 15 | SYS-16 | **Dual connection pool management.** Supabase (25 conn, CB) e Redis (50 conn) sem budget unificado ou backpressure. | MEDIUM | 8h | P2 | Mantido |
| 16 | SYS-17 | **Titulo do app "BidIQ Uniformes".** `main.py` referencia nome do POC original. | LOW | 0h | P0 | Bundled com SYS-01 (app_factory ja tem titulo correto) |
| 17 | SYS-18 | **Versao FastAPI 0.2.0.** Deveria ser v0.5. | LOW | 0h | P0 | Bundled com SYS-01 (app_factory ja tem APP_VERSION) |
| 18 | SYS-19 | **Comentarios com Issue numbers sem links.** Muitos refs a Issues sem URLs. | LOW | 4h | P3 | Mantido |
| 19 | SYS-20 | **SEO pages hardcoded.** Rotas estaticas, nao CMS-driven. | LOW | 8h | P3 | Mantido |

**Subtotal Sistema:** 19 items | CRITICAL: 1 | HIGH: 8 | MEDIUM: 6 | LOW: 4 | **~102h**

> **Nota:** SYS-15 (Frontend sem state management global) foi **REMOVIDO** -- duplicata de FE-03 (buscar complexity), conforme identificado no DRAFT e confirmado por @qa.

---

### Database (validado por @data-engineer)

| # | ID | Debito | Severidade | Horas | Prioridade | Status |
|---|------|--------|------------|-------|------------|--------|
| 1 | DB-01 | **Stripe price IDs hardcoded em migrations.** 5 migration files com `price_1*` IDs de producao. Staging pode cobrar precos reais. Fix: config table + seed via env vars (nova migration). NAO editar migrations existentes. | CRITICAL | 3h | P0 | Confirmado CRITICAL. Estimativa 2h->3h (inclui seed script) |
| 2 | DB-02 | **`handle_new_user()` omite `trial_expires_at`.** Trigger insere 10 colunas sem `trial_expires_at`. App layer compensa via `created_at + TRIAL_DURATION_DAYS`. | HIGH | 1.5h | P1 | Estimativa reduzida. ALTER FUNCTION simples |
| 3 | DB-03 | **`get_conversations_with_unread_count()` COUNT(*) OVER().** Window function antes de LIMIT/OFFSET. <500 rows em producao. | **MEDIUM** | 3h | P2 | Rebaixado de HIGH -- volume negligenciavel no estagio atual |
| 4 | DB-04 | **`profiles.plan_type` sem metrica de drift.** Reconciliacao JA existe via `stripe_reconciliation.py` (roda diariamente). Falta metrica granular por tipo de divergencia. | **MEDIUM** | 1h | P2 | Rebaixado de HIGH -- reconciliacao ja funciona |
| 5 | DB-05 | **`partner_referrals` orfaos acumulam.** <50 rows em producao, 1-2 orfaos/mes. | **LOW** | 0.5h | P3 | Rebaixado de HIGH -- volume minimo |
| 6 | DB-06 | **`user_subscriptions` sem retention.** Cada mudanca cria nova row (is_active=false). Dunning retries acumulam 5-10 rows/user/mes. | HIGH | 1h | P1 | Mantido HIGH -- crescimento real com dunning |
| 7 | DB-08 | **`search_state_transitions.user_id` nullable.** Adicionado nullable para backfill. Requer verificacao em producao antes de NOT NULL. | MEDIUM | 1h | P2 | Mantido |
| 8 | DB-09 | **`classification_feedback` FK ordering.** DEBT-002 cria com `auth.users(id)`, DEBT-113 re-aponta para `profiles(id)`. | **LOW** | 0.5h | P3 | Rebaixado de MEDIUM -- funciona, falha rara e detectavel via CI |
| 9 | DB-10 | **System cache warmer em `auth.users`.** Conta sentinela aparece em listings admin. | MEDIUM | 0.5h | P2 | Mantido. Estimativa reduzida |
| 10 | DB-11 | **OAuth tokens no public schema.** AES-256 na app layer. Padrao industria. | MEDIUM | 2h | P2 | Mantido |
| 11 | DB-12 | **Tres convencoes de nomes em migrations.** Squash NAO recomendado (custo-beneficio negativo). | **LOW** | 0h | P3 | Rebaixado de MEDIUM, 0h -- aceitar como esta, apenas README |
| 12 | DB-13 | **Sem down migrations.** Criar rollback apenas para billing e RLS. | MEDIUM | 2h | P2 | Mantido |
| 13 | DB-14 | **Cache cleanup trigger COUNT a cada INSERT.** Short-circuit (<=5) e index scan <1ms. | **LOW** | 0h | P3 | Rebaixado de MEDIUM, 0h -- overhead negligenciavel |
| 14 | DB-15 | **`alert_sent_items` retention scan.** Index `idx_alert_sent_items_sent_at` cobre adequadamente. Nao e full scan. | **LOW** | 0h | P3 | Rebaixado de MEDIUM, 0h -- falso alarme no DRAFT |
| 15 | DB-17 | **`organizations.plan_type` CHECK permissivo.** 13 valores incluindo legacy. | MEDIUM | 0.5h | P2 | Mantido |
| 16 | DB-18 | **`stripe_price_id` deprecated em `plans`.** Coluna nao mais usada como fallback (DEBT-114 removeu). Pode dropar. | LOW | 1h | P3 | Mantido |
| 17 | DB-19 | **`created_at` nullable inconsistente.** `user_oauth_tokens` e `plan_billing_periods`. | LOW | 0.5h | P3 | Estimativa reduzida |
| 18 | DB-21 | **`trial_email_log` sem policy explicita.** `service_role` bypassa RLS. Apenas documentacao. | LOW | 0.5h | P3 | Mantido |
| 19 | DB-22 | **Org admins sem UPDATE.** Backend handles writes via service role. | LOW | 0.5h | P3 | Mantido |
| 20 | DB-23 | **Migration 027b superseded.** IF NOT EXISTS garante idempotencia. | LOW | 0h | P3 | Mantido, 0h -- aceitar como esta |
| 21 | DB-24 | **Legacy `backend/migrations/`.** 7 arquivos redundantes. Adicionar DEPRECATED.md. | LOW | 0.5h | P3 | Mantido |
| 22 | DB-25 | **Constraint names inconsistentes.** 5+ padroes. Cosmetico. | LOW | 0h | P3 | Mantido, 0h -- enforce going forward |
| 23 | DB-26 | **Trigger names inconsistentes.** 4 padroes. Cosmetico. | LOW | 0h | P3 | Mantido, 0h -- enforce going forward |
| 24 | DB-27 | **`pipeline_items.search_id` TEXT vs UUID.** Auto-casts para TEXT. FK nao necessaria. | LOW | 0.5h | P3 | Mantido |
| 25 | DB-28 | **`conversations` correlated subquery per row.** `unread_count` via subquery correlacionada (50 subqueries por page). Mais impactante que DB-03. Resolver junto com DB-03. | MEDIUM | 2h | P2 | **NOVO** -- descoberto por @data-engineer |
| 26 | DB-29 | **`monthly_quota` sem retention.** 1 row/user/mes. 24,000 rows em 2 anos com 1000 users. | LOW | 0.5h | P3 | **NOVO** -- descoberto por @data-engineer |
| 27 | DB-30 | **`search_results_store`/`search_results_cache` JSONB sem versionamento.** Sem schema_version. Dados antigos e novos coexistem sem distincao. | MEDIUM | 4h | P2 | **NOVO** -- descoberto por @data-engineer |
| 28 | DB-31 | **`profiles.plan_type` CHECK nao escala.** Novo plano requer migration para alterar CHECK. Documentar como armadilha. | MEDIUM | 0.5h | P3 | **NOVO** -- descoberto por @data-engineer |

**Subtotal Database:** 28 items | CRITICAL: 1 | HIGH: 2 | MEDIUM: 10 | LOW: 15 | **~27h**

---

### Frontend/UX (validado por @ux-design-expert)

| # | ID | Debito | Severidade | Horas | Prioridade | Status |
|---|------|--------|------------|-------|------------|--------|
| 1 | FE-01 | **Inline `var()` ao inves de Tailwind tokens.** ~1,754 ocorrencias (nao 1,417). Comportamento visual identico. E debt de DX/consistencia, nao UX. Codemod regex cobre ~80%. | **HIGH** | 32h | P1 | Rebaixado de CRITICAL por @ux-design-expert |
| 2 | FE-02 | **Component library UI ausente (6 primitivos).** Faltam Card, Badge, Modal, Dialog, Select, Tabs, Tooltip. Recomendado Radix UI + CVA (Shadcn pattern). | HIGH | 24h | P1 | Mantido |
| 3 | FE-03 | **Complexidade da pagina Buscar.** 39 componentes em `app/buscar/components/` + 9 hooks. Debt de engenharia/manutencao, nao UX. | HIGH | 16h | P2 | Mantido (absorve SYS-15 eliminado) |
| 4 | FE-04 | **Error pages inconsistentes entre si.** TODOS 9 error.tsx reportam ao Sentry. Diferenca real: root usa inline var(), per-route usa Tailwind tokens. Cosmetica. | **MEDIUM** | 3h | P2 | Rebaixado de HIGH por @ux-design-expert |
| 5 | FE-05 | **Cores hex raw em global-error.tsx.** Usa inline styles BY DESIGN (root layout failed = sem acesso a Tailwind/CSS vars). Ja suporta dark mode via `prefers-color-scheme`. | **LOW** | 0.5h | P3 | Rebaixado de HIGH por @ux-design-expert |
| 6 | FE-06 | **Dual footer.** Buscar footer tem funcionalidades contextuais uteis. Unificar visualmente com variantes, nao eliminar. | **MEDIUM** | 4h | P2 | Rebaixado de HIGH por @ux-design-expert |
| 7 | FE-07 | **useIsMobile initial false flash.** `useState(false)` causa layout shift em mobile. Fix: usar `matchMedia` sincrono no initializer. | HIGH | 2h | P1 | Mantido |
| 8 | FE-08 | **Image optimization.** Apenas 4 imagens em `/public`. ZERO `<img>` tags em JSX. HeroSection ja usa `next/image` com WebP. Codebase e predominantemente data/text UI. | **LOW** | 2h | P3 | Rebaixado de HIGH por @ux-design-expert |
| 9 | FE-09 | **Localizacao inconsistente de componentes.** `components/`, `app/components/`, `app/buscar/components/` -- sem fronteira clara. AuthProvider em `app/components/` importado por 7 arquivos em `components/`. | MEDIUM | 8h | P2 | Mantido |
| 10 | FE-10 | **Blog/SEO pages sem loading states.** Server Components com static/ISR -- loading states menos criticos. | **LOW** | 2h | P3 | Rebaixado de MEDIUM por @ux-design-expert |
| 11 | FE-11 | **Animacoes duplicadas (CSS + Tailwind).** fadeInUp, shimmer, float definidos em ambos. Funciona -- redundancia, nao conflito. | **LOW** | 2h | P3 | Rebaixado de MEDIUM por @ux-design-expert |
| 12 | FE-12 | **Pages sem PageErrorBoundary sub-page.** 9 error.tsx cobrem rotas principais. Faltam boundaries sub-page em componentes internos. | MEDIUM | 3h | P2 | Mantido |
| 13 | FE-14 | **Feature-gated pages roteáveis.** `/alertas` e `/mensagens` sao FUNCIONAIS (nao stubs). Ocultas da nav mas acessiveis via URL direta. | MEDIUM | 2h | P2 | Mantido. Descricao ajustada |
| 14 | FE-15 | **Admin pages sem responsive.** Admin page principal ja tem `overflow-x-auto`. <5 usuarios internos, todos desktop. Paliativo de 1h suficiente. | **LOW** | 1h | P3 | Rebaixado de MEDIUM por @ux-design-expert |
| 15 | FE-16 | **Sem Storybook.** ROI baixo com apenas 6 primitivos. Cresce quando FE-02 for resolvido. | MEDIUM | 16h | P2 | Mantido |
| 16 | FE-17 | **Pull-to-refresh desktop hack CSS.** Usa `@media (pointer: fine)` -- abordagem padrao, nao fragil. | **LOW** | 1h | P3 | Rebaixado de MEDIUM por @ux-design-expert |
| 17 | FE-18 | **Shepherd.js usa Tailwind raw.** 15+ usos de `bg-white`, `text-gray-700`, `bg-blue-600` que NAO respeitam design tokens. Dark mode inconsistente. | MEDIUM | 2h | P2 | Mantido |
| 18 | FE-19 | **react-hook-form em devDependencies.** Usado em producao (signup, onboarding). Funciona porque Next.js bundla tudo, mas semanticamente incorreto. | MEDIUM | 0.5h | P0 | Mantido. Quick fix |
| 19 | FE-20 | **SVGs sem `aria-hidden`.** 396 usos de `aria-hidden` ja existem. Lacuna em SVGs inline menores espalhados. | MEDIUM | 3h | P2 | Mantido |
| 20 | FE-21 | **Focus nao retorna apos modal close.** BottomNav tem focus trap. BuscarModals, InviteMemberModal, CancelSubscriptionModal -- sem evidencia de focus return. | MEDIUM | 4h | P2 | Mantido |
| 21 | FE-23 | **59 API route files.** Standalone output nao cria serverless functions individuais. Impacto em cold start e teorico. | **LOW** | 0h | P3 | Rebaixado de MEDIUM, 0h -- nao e problema real |
| 22 | FE-24 | **a11y no CI.** `@axe-core/playwright` integrado em `accessibility-audit.spec.ts` (DEBT-109). Gate: 0 critical violations. Funciona em CI. | LOW | 4h | P3 | Mantido. @qa confirmou integracao existente |
| 23 | FE-25 | **Tailwind content paths com `pages/`.** Diretorio nao existe. Tailwind ignora paths inexistentes. Zero impacto. | LOW | 0.5h | P3 | Mantido |
| 24 | FE-26 | **Imports circulares potenciais.** 7 arquivos em `components/` importam de `app/components/AuthProvider`. Viola arquitetura shared -> page-specific. | **MEDIUM** | 4h | P2 | Elevado de LOW por @ux-design-expert |
| 25 | FE-27 | **NProgress vs built-in Next.js.** Funciona bem. Next.js nao tem equivalente robusto para App Router. | LOW | 0h | P3 | Mantido, 0h -- nao e debt real |
| 26 | FE-28 | **Formatacao de datas inconsistente.** 25 arquivos com padroes mistos. | LOW | 3h | P3 | Mantido |
| 27 | FE-29 | **Toast vs banner inconsistente.** Estrategia atual e razoavel. Falta documentacao da convencao. | LOW | 4h | P3 | Mantido |
| 28 | FE-30 | **Shepherd arrow hidden.** Remove conexao visual com target element. | LOW | 1h | P3 | Mantido |
| 29 | FE-31 | **Dashboard icon errado no BottomNav.** Usa `icons.search` ao inves de `icons.dashboard`. | LOW | 0.5h | P3 | Mantido |
| 30 | FE-32 | **Framer Motion bundle.** Isolado em landing pages. Tree-shaking funciona. | LOW | 0h | P3 | Mantido, 0h -- nao e debt real |
| 31 | FE-33 | **Error pages usam tokens inconsistentes.** Root error.tsx usa inline var(), per-route usa Tailwind tokens. Deveria unificar. | LOW | 2h | P3 | **NOVO** -- descoberto por @ux-design-expert |
| 32 | FE-34 | **AuthProvider em localizacao incorreta.** `app/components/AuthProvider.tsx` importado por `components/`. Deveria estar em `contexts/` ou `components/`. Root cause de FE-26. | MEDIUM | 2h | P1 | **NOVO** -- descoberto por @ux-design-expert |
| 33 | FE-35 | **BottomNav label "Dash" confuso.** Considerar "Painel" (PT-BR nativo). `ariaLabel: "Dashboard"` esta correto. | LOW | 0.5h | P3 | **NOVO** -- descoberto por @ux-design-expert |
| 34 | FE-36 | **Shepherd.js tour arrow hidden remove affordance.** Sem arrow, usuario pode nao associar tooltip ao elemento. | LOW | 1h | P3 | **NOVO** -- descoberto por @ux-design-expert |

**Subtotal Frontend:** 34 items | CRITICAL: 0 | HIGH: 4 | MEDIUM: 12 | LOW: 18 | **~151h**

> **Nota:** Nenhum CRITICAL restante no frontend. O item mais impactante para UX real e FE-07 (useIsMobile flash, 2h). O mais impactante para DX e FE-02 (component library, 24h).

---

## Itens Removidos (Falsos Positivos)

| ID | Motivo | Removido por |
|----|--------|-------------|
| DB-07 | **Ja corrigido.** Migration TD-003 (`20260304200000`) corrigiu `auth.role()` para `TO service_role`. DEBT-113 inclui runtime assertion verificada em producao. | @data-engineer |
| DB-16 | **Decisao arquitetural, nao debito.** `search_state_transitions.search_id` sem FK e correto: `search_sessions.search_id` e nullable e nao-unico (retries compartilham IDs). FK requer UNIQUE. Tabela e audit trail com retention 30 dias. | @data-engineer |
| DB-20 | **Ja resolvido.** Migration `20260309200000` (DEBT-100 AC10) tem block `DO $$ ... END $$` que verifica `pg_stat_user_indexes.idx_scan` e dropa indexes redundantes. Mecanismo de cleanup in place. | @data-engineer |
| FE-13 | **Ja implementado.** `Sidebar.tsx` linha 86: `aria-current={active ? "page" : undefined}`. Tanto Sidebar quanto BottomNav implementam corretamente. | @ux-design-expert |
| FE-22 | **Ja implementado.** `PlanToggle.tsx` linha 67: `focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2`. Focus ring funciona via teclado. | @ux-design-expert |
| SYS-15 | **Duplicata de FE-03.** Mesmo problema (buscar complexity / state management) visto de angulos diferentes. FE-03 absorve o escopo. | @qa |

---

## Itens Adicionados (Descobertos na Revisao)

| ID | Debito | Area | Severidade | Horas | Descoberto por |
|----|--------|------|------------|-------|---------------|
| DB-28 | `conversations` correlated subquery per row (50 subqueries por page) | Performance | MEDIUM | 2h | @data-engineer |
| DB-29 | `monthly_quota` sem retention (acumula 1 row/user/mes) | Integridade | LOW | 0.5h | @data-engineer |
| DB-30 | `search_results_store`/`search_results_cache` JSONB sem versionamento | Schema | MEDIUM | 4h | @data-engineer |
| DB-31 | `profiles.plan_type` CHECK nao escala para novos planos | Schema | MEDIUM | 0.5h | @data-engineer |
| FE-33 | Error pages usam tokens inconsistentes (inline var vs Tailwind) | Design System | LOW | 2h | @ux-design-expert |
| FE-34 | AuthProvider em localizacao incorreta (causa circular imports FE-26) | DX | MEDIUM | 2h | @ux-design-expert |
| FE-35 | BottomNav label "Dash" confuso (deveria ser "Painel") | UX | LOW | 0.5h | @ux-design-expert |
| FE-36 | Shepherd.js tour arrow hidden remove affordance visual | UX | LOW | 1h | @ux-design-expert |

---

## Matriz de Priorizacao Final

| Prioridade | IDs | Criterio | Horas |
|-----------|-----|----------|-------|
| **P0 (Imediato)** | SYS-01+SYS-06+SYS-17+SYS-18 (bundle), DB-01, SYS-14, FE-19 | Seguranca + producao + velocity blocker | ~19.5h |
| **P1 (Sprint 1)** | SYS-02, SYS-04, SYS-05, SYS-07, SYS-08, SYS-09, SYS-10, DB-02, DB-06, FE-01, FE-02, FE-07, FE-34 | Alto impacto, habilita outros | ~110.5h |
| **P2 (Sprint 2-3)** | SYS-03, SYS-11, SYS-12, SYS-13, SYS-16, DB-03, DB-04, DB-08, DB-10, DB-11, DB-13, DB-17, DB-28, DB-30, FE-03, FE-04, FE-06, FE-09, FE-12, FE-14, FE-16, FE-18, FE-20, FE-21, FE-26 | Impacto medio, melhorias incrementais | ~107h |
| **P3 (Backlog)** | SYS-19, SYS-20, DB-05, DB-09, DB-12, DB-14, DB-15, DB-18, DB-19, DB-21, DB-22, DB-23, DB-24, DB-25, DB-26, DB-27, DB-29, DB-31, FE-05, FE-08, FE-10, FE-11, FE-15, FE-17, FE-23, FE-24, FE-25, FE-27, FE-28, FE-29, FE-30, FE-31, FE-32, FE-33, FE-35, FE-36 | Baixo risco, pode esperar | ~42.5h |

---

## Plano de Resolucao

### Sprint 0: Pre-requisitos (1 semana, ~19.5h)

**Objetivo:** Eliminar riscos de seguranca e desbloquear velocidade do time.

| # | IDs | Acao | Horas | Responsavel |
|---|-----|------|-------|-------------|
| 1 | SYS-01 | **Investigar dual-path main.py/app_factory.** Verificar em Railway qual entry point e usado. Se `main:app`, wiring `app_factory:create_app` resolve CORS + route registration + titulo + versao (SYS-06, SYS-17, SYS-18). | 4h | @architect + @devops |
| 2 | DB-01 | **Mover Stripe price IDs para config table.** Nova migration que popula `plan_billing_periods` via `current_setting()`. Seed script para staging/dev. NAO editar migrations existentes. | 3h | @data-engineer |
| 3 | SYS-14 | **Eliminar test pollution.** Remover `sys.modules["arq"]` raw (usar conftest fixture). Eliminar `importlib.reload()` patterns. Reset global singletons. Meta: `run_tests_safe.py --parallel 1` sem flakes. | 12h | @qa + @dev |
| 4 | FE-19 | **Mover react-hook-form para dependencies.** | 0.5h | @dev |

### Sprint 1: Fundacao (2 semanas, ~110.5h)

**Objetivo:** Estabilizar arquitetura e criar fundacao para frontend.

**Track Backend (~52h):**

| # | IDs | Acao | Horas |
|---|-----|------|-------|
| 1 | SYS-08 | Request timeout middleware | 4h |
| 2 | SYS-04 | Metricas Prometheus persistentes (push para DB) | 8h |
| 3 | SYS-05 | Health canary com page size validation | 4h |
| 4 | SYS-07 | Versionamento de API consistente | 8h |
| 5 | SYS-09 | Worker liveness alerta para ausencia prolongada | 4h |
| 6 | SYS-10 | Search decomposition: remover backward-compat re-exports | 4h |
| 7 | SYS-02 | PNCP async migration (incremental, por metodo) | 16h |
| 8 | DB-02 | `handle_new_user()` + `trial_expires_at` | 1.5h |
| 9 | DB-06 | pg_cron retention para `user_subscriptions` (24 meses) | 1h |

> **Nota sobre SYS-02:** Migrar incrementalmente (1 metodo por vez em feature branch). Todos `@patch("pncp_client.requests.Session")` mocks precisam ser atualizados. Risco de regressao: MEDIUM.

**Track Frontend (~62h):**

| # | IDs | Acao | Horas |
|---|-----|------|-------|
| 1 | FE-34 | Mover AuthProvider para `contexts/` (pre-requisito de FE-09 e FE-26) | 2h |
| 2 | FE-07 | Fix useIsMobile layout shift (matchMedia sincrono) | 2h |
| 3 | FE-02 | Component library: Card, Modal, Badge, Select, Tabs (Radix + CVA) | 24h |
| 4 | FE-01 | Inline var() codemod migration (~1,754 occurrences) | 32h |

> **Nota sobre FE-01:** Depende de FE-02 (componentes novos ja usam tokens certos). Iniciar codemod apos primeiros 3 primitivos estarem prontos. 32h = 2h codemod script + 20h validacao + 10h edge cases manuais. Tokens sem mapeamento Tailwind (`--gradient-*`, `--glass-*`, `--text-hero`) ficam como `var()`.

### Sprint 2: Otimizacao (2 semanas, ~107h)

**Track Backend (~26h):**

| # | IDs | Acao | Horas |
|---|-----|------|-------|
| 1 | SYS-03 | ComprasGov health check cron (15min) | 2h |
| 2 | SYS-11 | Migrar keywords hardcoded para YAML | 4h |
| 3 | SYS-12 | Unificar cache patterns (interface comum) | 8h |
| 4 | SYS-13 | Runtime schema version assertion no startup | 4h |
| 5 | SYS-16 | Pool budget unificado + backpressure | 8h |

**Track Database (~14.5h):**

| # | IDs | Acao | Horas |
|---|-----|------|-------|
| 1 | DB-03 + DB-28 | Rewrite `get_conversations_with_unread_count()` (LEFT JOIN + separar count) | 5h |
| 2 | DB-04 | Metrica de drift granular no Prometheus (label `divergence_type`) | 1h |
| 3 | DB-30 | Adicionar `schema_version INTEGER DEFAULT 1` em JSONB tables | 4h |
| 4 | DB-08 | `search_state_transitions.user_id` NOT NULL (apos verificacao producao) | 1h |
| 5 | DB-10, DB-11, DB-13, DB-17 | Batch: cache warmer filter, OAuth docs, down migrations billing/RLS, CHECK tighten | 5.5h |

**Track Frontend (~74h):**

| # | IDs | Acao | Horas |
|---|-----|------|-------|
| 1 | FE-03 | Refactor buscar (com component library pronta) | 16h |
| 2 | FE-09 | Unificar component locations | 8h |
| 3 | FE-26 | Resolver circular imports (depende de FE-34 feito em Sprint 1) | 4h |
| 4 | FE-04, FE-06, FE-12 | Error pages unificacao, dual footer, PageErrorBoundary | 10h |
| 5 | FE-14, FE-16, FE-18, FE-20, FE-21 | Feature gates, Storybook, Shepherd tokens, SVG a11y, modal focus | 27h |

### Backlog (~42.5h)

Items de baixo risco que podem ser resolvidos oportunisticamente:

**Quick wins (<1h cada):** FE-05 (0.5h), FE-25 (0.5h), FE-31 (0.5h), FE-35 (0.5h), DB-05 (0.5h), DB-19 (0.5h), DB-21 (0.5h), DB-22 (0.5h), DB-24 (0.5h), DB-27 (0.5h), DB-29 (0.5h), DB-31 (0.5h)

**Small items (1-4h):** FE-08 (2h), FE-10 (2h), FE-11 (2h), FE-15 (1h), FE-17 (1h), FE-24 (4h), FE-28 (3h), FE-29 (4h), FE-30 (1h), FE-33 (2h), FE-36 (1h), SYS-19 (4h), DB-09 (0.5h), DB-18 (1h)

**Larger items (>4h):** SYS-20 (8h)

**Zero-effort (accepted as-is):** DB-12 (0h), DB-14 (0h), DB-15 (0h), DB-23 (0h), DB-25 (0h), DB-26 (0h), FE-23 (0h), FE-27 (0h), FE-32 (0h)

---

## Dependencias e Ordem de Execucao

### Grafo de Dependencias Criticas

```
[P0 - Sprint 0]
  SYS-01 (main.py/app_factory investigation)
    |---> Resolve SYS-06 (route registration)
    |---> Resolve SYS-17 (titulo)
    |---> Resolve SYS-18 (versao)
    |
  DB-01 (Stripe IDs) -- independente, paralelo
    |
  SYS-14 (test pollution) -- desbloqueia velocidade
    |
  FE-19 (react-hook-form dep) -- independente, paralelo

[P1 - Sprint 1]
  FE-34 (AuthProvider move)
    |---> FE-09 (component locations) [Sprint 2]
    |---> FE-26 (circular imports) [Sprint 2]
    |
  FE-02 (component library: Card, Modal, Badge, Select, Tabs)
    |---> FE-01 (inline var codemod -- beneficia de componentes prontos)
    |       |---> FE-03 (buscar refactor -- com primitivos estaveis) [Sprint 2]
    |
  DB-02 (handle_new_user) -- pode agrupar com DB-08, DB-19 em 1 migration
    |
  DB-06 (retention) -- independente
    |
  SYS-02 (PNCP async) -- incremental por metodo
    |---> SYS-12 (cache unification, mesmo async pattern) [Sprint 2]

[P2 - Sprint 2]
  DB-03 + DB-28 -- resolver juntos (rewrite de get_conversations)
    |
  DB-30 (JSONB versioning) -- independente
    |
  FE-16 (Storybook) -- ROI cresce apos FE-02
```

### Cadeia de Dependencias DB (via @data-engineer)

```
Cadeia 1: Billing Integrity
  DB-01 (Stripe IDs) -- independente, P0
    --> DB-18 (drop deprecated stripe_price_id)
    --> DB-31 (plan_type CHECK escalabilidade) -- futuro

Cadeia 2: Retention Jobs (paralelos)
  DB-06 (user_subscriptions, 24 meses)
  DB-05 (partner_referrals, 12 meses)
  DB-29 (monthly_quota, 24 meses)

Cadeia 3: Schema Integrity (mesma migration)
  DB-02 (handle_new_user + trial_expires_at)
  DB-08 (search_state_transitions NOT NULL)
  DB-19 (created_at NOT NULL fixes)

Cadeia 4: Performance (rewrite unica)
  DB-03 (COUNT(*) OVER()) + DB-28 (correlated subquery)
```

### Caminho Critico

O caminho critico para desbloqueio maximo e:

1. **SYS-01 investigation** (4h) -- determina escopo real de fix
2. **SYS-14 test pollution** (12h) -- desbloqueia velocidade de PRs
3. **FE-34 AuthProvider** (2h) --> **FE-02 component library** (24h) --> **FE-01 codemod** (32h) --> **FE-03 buscar refactor** (16h)

Total do caminho critico: ~90h (~6 semanas com 1 dev FE dedicado).

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| **main.py/app_factory dual-path: producao roda com middleware incompleta** | HIGH | CRITICAL | Investigar em 30min via Railway logs (`railway logs --tail`). Se confirmado, wiring `app_factory` resolve 4 items de uma vez. |
| **CORS fix quebra frontend proxy** | MEDIUM | HIGH | Frontend proxy (`/api/*`) e same-origin, bypassa CORS. Testar com `Origin` headers via TestClient. E2E nao detecta issues de CORS. |
| **PNCP async migration quebra 7332 testes** | LOW | CRITICAL | Todos `@patch("pncp_client.requests.Session")` mocks quebram. Migrar incrementalmente (1 metodo por vez em feature branch). |
| **Component library quebra paginas existentes** | MEDIUM | MEDIUM | Sem Storybook (FE-16), validacao visual e manual. Usar Playwright screenshot comparison como gate. |
| **Retention jobs deletam dados validos** | LOW | HIGH | Adicionar dry-run mode. WHERE conditions com `is_active = false` e `created_at <` threshold. Testar com volumes de producao. |
| **Test pollution fixes quebram testes dependentes do estado poluido** | MEDIUM | MEDIUM | Rodar full suite apos cada fix individual. Corrigir em cascata. |
| **Webhook idempotency: Stripe entrega duplicada durante deploy** | LOW | MEDIUM | Verificar se `stripe_webhook_events` e usada para dedup. Se nao, adicionar check. |
| **ARQ job perdido se Redis morre mid-execution** | LOW | LOW | Fallback inline existe. Jobs resultam em atraso, nao perda de dados. |

---

## Gaps Aceitos (Documentados)

Riscos identificados por @qa que sao aceitos para o estagio atual (pre-revenue beta, <100 usuarios):

| # | Gap | Justificativa | Revisitar quando |
|---|-----|---------------|-----------------|
| 1 | **Sem consumer-driven contract tests (Pact).** Frontend proxy tightly coupled a backend response shapes. | Time pequeno, unico frontend consumer. Snapshot tests em `backend/tests/snapshots/api_contracts/` fornecem cobertura basica. | Adicionar mobile clients ou API externa |
| 2 | **LGPD compliance gaps.** Data retention PII, right-to-deletion, data export nao implementados. | Pre-revenue beta com <100 usuarios. | Antes de escalar para clientes pagantes |
| 3 | **Rate limiting fallback per-worker in-memory.** Com Redis down, limite efetivo dobra (2 workers). SSE endpoint sem rate limit dedicado. | Redis Upstash uptime >99.9%. Volume baixo. search_id e UUID opaco. | Escalar para >1000 usuarios simultaneos |
| 4 | **Sem dead letter queue para ARQ jobs.** Jobs falhos usam fallback inline (execucao sincrona). | Resultado e atraso, nao perda de dados. `gerar_resumo_fallback()` garante resposta. | Volume de jobs > 100/hora |
| 5 | **Supply chain security nao auditado formalmente.** CI roda `pip-audit`. Dependabot ativo. | Nenhuma vulnerabilidade critica conhecida. | Antes de certificacao SOC2/ISO |
| 6 | **OAuth token encryption app-layer only.** AES-256 padrao industria. Sem rotation procedure documentada para OAUTH_ENCRYPTION_KEY, Stripe keys, SUPABASE_SERVICE_ROLE_KEY. | Risco aceito. Time pequeno, acesso restrito. | Antes de adicionar mais devs ou compliance enterprise |
| 7 | **Dependency supply chain nao verificado.** `pip-audit` e `npm audit` rodam em CI mas resultados nao sao revisados formalmente. Lock file integrity nao verificada. | Dependabot auto-merge para minor. | Antes de compliance formal |
| 8 | **DDoS resilience nao avaliada.** Railway proxy e unica barreira. Sem WAF ou CDN. | Volume muito baixo. Railway absorve requests. | Antes de marketing push ou >1000 DAU |

---

## Criterios de Sucesso

### Per-Item

| Item | Teste de Validacao |
|------|-------------------|
| SYS-01 (CORS) | Request com `Origin: https://evil.com` retorna SEM header `Access-Control-Allow-Origin`. Request com `Origin: https://smartlic.tech` retorna header correto. Teste em `test_cors.py` com TestClient. |
| SYS-14 (test pollution) | `python scripts/run_tests_safe.py --parallel 1` (sequential, sem isolamento subprocess) passa todos testes sem flakes. Baseline de flaky tests: 0. |
| DB-01 (Stripe IDs) | Fresh install via `seed.sql` popula price IDs de env vars. `grep -r 'price_1' supabase/migrations/` retorna apenas migrations historicas (ja aplicadas). Staging usa test-mode IDs. |
| FE-01 (inline var) | `grep -r 'var(--' frontend/app/ | wc -l` retorna <50 (excecoes: gradient, glass, text-hero). Visual regression screenshots identicos pre/pos. |
| FE-02 (component library) | `grep -r 'from.*components/ui' | sort -u` mostra Card, Modal, Badge, Select, Tabs em uso. Cada primitivo tem testes unitarios. |
| FE-07 (useIsMobile) | Lighthouse CLS < 0.1 em viewport mobile (375px). Sem layout shift perceptivel no primeiro paint. |

### Pre-Remediacao (escrever ANTES de corrigir)

| Debito | Teste Pre-Remediacao |
|--------|---------------------|
| SYS-01 | Test com TestClient + `Origin` header que documenta comportamento atual |
| SYS-02 | Characterization tests para metodos publicos de `pncp_client.py` |
| FE-01 | Visual regression screenshots de 5 paginas-chave via Playwright |
| FE-02 | Inventario script que lista todas implementacoes ad-hoc de Card/Modal/Badge |
| SYS-14 | `run_tests_safe.py --parallel 1` -- documenta quais testes falham (pollution baseline) |

### Metricas Globais

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

---

## Changelog do Assessment

| Versao | Data | Mudanca |
|--------|------|---------|
| DRAFT | 2026-03-20 | 79 itens consolidados de 3 fontes (system-architecture, DB-AUDIT, frontend-spec) por @architect |
| Phase 5 | 2026-03-20 | @data-engineer: 3 removidos (DB-07, DB-16, DB-20), 4 adicionados (DB-28-31), 8 severidades ajustadas, esforco DB 40h->27h |
| Phase 6 | 2026-03-20 | @ux-design-expert: 2 removidos (FE-13, FE-22), 4 adicionados (FE-33-36), 11 severidades ajustadas, FE-01 CRITICAL->HIGH, esforco FE 180h->~140h |
| Phase 7 | 2026-03-20 | @qa: APPROVED WITH CONDITIONS. SYS-15 removido (duplicata FE-03). SYS-14 elevado a P0. SYS-01 escopo alterado (dual-path discovery). 5 gaps documentados. Cross-cutting risks mapeados. |
| **FINAL (1.0)** | **2026-03-20** | **@architect: Todas revisoes incorporadas. 81 items finais (CRIT:2, HIGH:14, MED:28, LOW:37). ~280h estimados. Priorizacao e plano de 4 sprints consolidados. 3 condicoes QA MUST atendidas. 8 gaps aceitos documentados.** |

---

### Condicoes QA Atendidas

1. **MUST: main.py/app_factory ambiguidade** -- Documentada como achado mais critico no Executive Summary. Sprint 0 Item 1, P0 com 4h dedicadas a investigacao e resolucao. Riscos mapeados na tabela. SYS-01 escopo expandido para cobrir o dual-path. SYS-06, SYS-17, SYS-18 bundled como resolucao conjunta.

2. **MUST: SYS-15 removido do plano** -- Removido como duplicata de FE-03. Nota explicitamente documentada na secao Sistema. Horas de FE-03 (16h) absorvem o escopo completo. Nao ha double-counting.

3. **MUST: SYS-02 verificado como valido** -- Confirmado que `pncp_client.py` ainda usa `import requests` (apesar de DEBT-107). Rebaixado de CRITICAL para HIGH com justificativa documentada (`asyncio.to_thread()` mitiga para escala atual de 2 workers). Incluido em Sprint 1 Track Backend com recomendacao de migracao incremental.

---

*Gerado 2026-03-20 por @architect (Atlas) durante Brownfield Discovery Phase 8.*
*Incorpora revisoes de @data-engineer (Phase 5), @ux-design-expert (Phase 6), @qa (Phase 7).*
*Todas as 3 condicoes QA MUST foram atendidas. 8 gaps aceitos documentados.*
