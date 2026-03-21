# Technical Debt Assessment - DRAFT

**Projeto:** SmartLic
**Data:** 2026-03-20
**Status:** DRAFT -- Pendente revisao dos especialistas
**Fontes:** system-architecture.md (Phase 1), DB-AUDIT.md (Phase 2), frontend-spec.md (Phase 3)

---

## 1. Debitos de Sistema (fonte: system-architecture.md)

### CRITICAL

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| SYS-01 | **CORS permite todas as origens (`*`)**. Qualquer website pode fazer chamadas autenticadas a API. Em producao com usuarios reais, risco significativo de seguranca. | CRITICAL | Seguranca | 2h |
| SYS-02 | **PNCP client usa biblioteca sincrona `requests`**. Bloqueia a thread do event loop (mitigado via `asyncio.to_thread()`, mas adiciona complexidade e limita concorrencia). Todos os outros clients usam async httpx. | CRITICAL | Arquitetura | 16h |
| SYS-03 | **ComprasGov v3 offline sem monitoramento**. Terceira fonte de dados completamente indisponivel desde 2026-03-03 sem health check automatizado ou alerta para detectar recuperacao. Prioridade hardcoded para 99. | CRITICAL | Integracao | 4h |

### HIGH

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| SYS-04 | **Metricas Prometheus sao efemeras**. Todas as metricas resetam ao reiniciar container (in-memory only). Sem SLO tracking persistente. Railway reinicia containers a cada deploy. | HIGH | Observabilidade | 8h |
| SYS-05 | **Health canary nao detecta limite de page size do PNCP**. Canary usa `tamanhoPagina=10`, entao passa mesmo quando PNCP mudou max de 500 para 50. Regressao no limite de page size passaria despercebida. | HIGH | Integracao | 4h |
| SYS-06 | **main.py e minimo, registro de rotas acontece em outro lugar**. main.py mostra apenas root + health. Registro real (38 modulos) nao e visivel do entry point -- feito via pattern nao visivel em main.py. Prejudica discoverability. | HIGH | DX | 4h |
| SYS-07 | **Versionamento de API inconsistente**. Algumas rotas usam prefixo `/v1/` (search status, first-analysis), maioria nao. Sem negociacao de versao. Breaking changes futuras serao dificeis. | HIGH | Arquitetura | 8h |
| SYS-08 | **Sem request timeout no nivel da aplicacao**. Gunicorn timeout e 120s, Railway ~300s, mas nao ha middleware de timeout a nivel de aplicacao. Chamada downstream lenta pode segurar worker pelo timeout total do Gunicorn. | HIGH | Resiliencia | 4h |
| SYS-09 | **Deteccao de liveness do worker depende do Redis**. `_worker_alive_cache` verifica via chave Redis. Se Redis cair, liveness nao pode ser determinada. Path de fallback inline ativa (correto), mas nao ha alerta para ausencia prolongada do worker. | HIGH | Resiliencia | 4h |
| SYS-10 | **Decomposicao de search tem re-exports de backward-compat**. DEBT-115 decompos `routes/search.py` em 4 sub-modulos, mas o modulo original re-exporta todos simbolos. Cria grafo de imports fragil. | HIGH | DX | 4h |

### MEDIUM

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| SYS-11 | **`filter.py` tem keyword sets hardcoded**. Conjunto `KEYWORDS_UNIFORMES` default esta hardcoded ao lado de keywords setoriais do YAML. Deveria estar totalmente migrado para `sectors_data.yaml`. | MEDIUM | Arquitetura | 4h |
| SYS-12 | **Multiplas implementacoes de cache**. `search_cache.py`, `cache.py`, `redis_pool.py`, `auth.py`, `llm_arbiter.py`, `quota.py` -- cada um com logica propria de eviction/TTL. | MEDIUM | Arquitetura | 8h |
| SYS-13 | **Sem version tracking de migrations no codigo**. 35 Supabase migrations + 7 backend migrations, mas nenhuma assertion de schema version em runtime. Migration-check CI cobre, mas sem verificacao runtime. | MEDIUM | Infra | 4h |
| SYS-14 | **Padroes de test pollution documentados mas nao eliminados**. MEMORY.md documenta 8+ padroes (sys.modules, importlib.reload, MagicMock leakage, global singletons). Mitigados por conftest fixtures mas causas raiz permanecem. | MEDIUM | Testes | 12h |
| SYS-15 | **Frontend sem state management global**. Todo estado esta em hooks custom. A decomposicao de 9 hooks de search (`useSearchOrchestration` -> 8 sub-hooks) e complexa. Sincronizacao de estado depende de prop drilling e callback chains. | MEDIUM | Frontend | 16h |
| SYS-16 | **Gerenciamento dual de connection pool**. `supabase_client.py` gerencia pool httpx (25 conexoes, circuit breaker) enquanto `redis_pool.py` gerencia pool Redis (50 conexoes). Sem budget unificado de pool ou backpressure entre ambos. | MEDIUM | Resiliencia | 8h |

### LOW

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| SYS-17 | **Titulo do app ainda diz "BidIQ Uniformes"**. `main.py` titulo e descricoes referenciam nome original do POC, nao "SmartLic". | LOW | DX | 1h |
| SYS-18 | **Versao FastAPI declarada como 0.2.0**. `main.py` declara `version="0.2.0"` mas produto esta na v0.5. | LOW | DX | 0.5h |
| SYS-19 | **Comentarios referenciam numeros de Issue**. Muitos comentarios referenciam numeros de GitHub Issues sem links. Densa anotacao ajuda arqueologia mas prejudica legibilidade. | LOW | DX | 4h |
| SYS-20 | **Paginas SEO do frontend sao hardcoded**. Paginas de conteudo SEO sao rotas Next.js estaticas, nao CMS-driven. Novas paginas requerem deploy de codigo. | LOW | Frontend | 8h |

---

## 2. Debitos de Database (fonte: DB-AUDIT.md)

> :warning: PENDENTE: Revisao do @data-engineer

### CRITICAL

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| DB-01 | **Stripe price IDs hardcoded em migrations**. Migrations 015, 029, 20260226120000, 20260301300000 contem IDs de producao Stripe (ex: `price_1T54vN9FhmvPslGYgfTGIAzV`). Visiveis no git, staging pode cobrar precos de producao. | CRITICAL | Seguranca | 2h |

### HIGH

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| DB-02 | **`handle_new_user()` omite `trial_expires_at`**. Trigger insere 10 colunas mas omite `trial_expires_at` -- NULL para novos usuarios. App layer compensa via `created_at + TRIAL_DURATION_DAYS`, mas deveria estar no trigger. | HIGH | Schema | 2h |
| DB-03 | **`get_conversations_with_unread_count()` usa COUNT(*) OVER()**. Window function conta TODAS rows antes de paginacao, causando full scan. Para admins (que veem TODAS conversas), e O(N) a cada page load. | HIGH | Performance | 4h |
| DB-04 | **`profiles.plan_type` denormalizado sem reconciliacao**. Cache do plano atual. Sincronizado por webhooks Stripe, mas se processamento falhar, `plan_type` pode divergir. Nao ha reconciliacao automatizada. | HIGH | Integridade | 4h |
| DB-05 | **`partner_referrals` orfaos acumulam**. `referred_user_id` nullable apos mudanca de FK. Records orfaos acumulam sem cleanup job. | HIGH | Integridade | 1h |
| DB-06 | **`user_subscriptions` sem retention**. Subscricoes inativas acumulam indefinidamente. Cada mudanca cria nova row (is_active=false na anterior). | HIGH | Integridade | 1h |

### MEDIUM

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| DB-07 | **Verificar policy `reconciliation_log` em producao**. Migration usou `auth.role() = 'service_role'` que deveria ser `TO service_role`. TD-003 provavelmente corrigiu, mas necessita verificacao. | MEDIUM | RLS | 0.5h |
| DB-08 | **`search_state_transitions.user_id` deveria ser NOT NULL**. Adicionado nullable para backfill. Apos estabilizacao, deve ser NOT NULL. | MEDIUM | Schema | 1h |
| DB-09 | **`classification_feedback` FK ordering em fresh install**. DEBT-002 cria com `REFERENCES auth.users(id)`, DEBT-113 re-aponta para `profiles(id)`. Funciona mas e fragil. | MEDIUM | Schema | 1h |
| DB-10 | **System cache warmer em `auth.users`**. Conta sentinela (UUID nulo) com senha vazia. Banida ate 2099, mas aparece em listings. | MEDIUM | Seguranca | 1h |
| DB-11 | **OAuth tokens no public schema**. Tokens criptografados AES-256 na camada de aplicacao. Se `OAUTH_ENCRYPTION_KEY` e DB forem comprometidos juntos, tokens ficam expostos. | MEDIUM | Seguranca | 2h |
| DB-12 | **Tres convencoes de nomes para migrations**. Numbered prefix (001-033), timestamped (20260...), lettered suffix (006a, 006b, 027b). Funciona mas confuso. | MEDIUM | DX | 4h |
| DB-13 | **Sem down migrations**. Nenhum dos 86 arquivos tem rollback. Padrao Supabase, mas arriscado para migrations criticas. | MEDIUM | Infra | 2h |
| DB-14 | **`cleanup_search_cache_per_user()` trigger fires COUNT a cada INSERT**. Short-circuit se <= 5, mas COUNT roda toda vez. | MEDIUM | Performance | 1h |
| DB-15 | **`alert_sent_items` scan pattern para retention**. DELETE sem filtro por alert_id leva a full scan de rows antigas. | MEDIUM | Performance | 0.5h |
| DB-16 | **`search_state_transitions.search_id` sem FK constraint**. Por design (search_id nullable e nao-unico), mas orfaos possiveis. Retention cleanup cobre. | MEDIUM | Integridade | 1h |
| DB-17 | **`organizations.plan_type` CHECK permissivo demais**. Permite 13 valores incluindo tipos legacy que nao tem integracao de billing. | MEDIUM | Integridade | 0.5h |

### LOW

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| DB-18 | **Coluna `stripe_price_id` deprecated ainda presente**. `billing.py` usa como fallback. Deveria ser removida apos confirmacao. | LOW | Schema | 1h |
| DB-19 | **`created_at` nullable inconsistente**. `user_oauth_tokens` e `plan_billing_periods` tem DEFAULT NOW() sem NOT NULL. | LOW | Schema | 1h |
| DB-20 | **Indexes sobrepostos em `search_sessions`**. 3 indexes cobrem `user_id`. Compostos subsumem o simples. Desperdicio de storage/writes. | LOW | Performance | 1h |
| DB-21 | **`trial_email_log` sem policy explicita de service_role**. RLS habilitado mas nenhuma policy. service_role bypassa, mas nao documentado explicitamente. | LOW | RLS | 0.5h |
| DB-22 | **Organization admins nao podem UPDATE org**. Apenas owner pode UPDATE via Supabase client. Backend handles writes, mas inconsistente. | LOW | RLS | 0.5h |
| DB-23 | **Migration 027b superseded ainda presente**. `IF NOT EXISTS` torna seguro, mas e dead code confuso. | LOW | DX | 0.5h |
| DB-24 | **Legacy `backend/migrations/` ainda presente**. 7 arquivos redundantes desde DEBT-002. Confuso para novos devs. | LOW | DX | 0.5h |
| DB-25 | **Nomes de constraints inconsistentes**. 5+ padroes: `table_column_check`, `chk_table_column`, `descriptive`, `table_column_fkey`, `fk_table_column`. | LOW | DX | 2h |
| DB-26 | **Nomes de triggers inconsistentes**. 4 padroes: `table_purpose`, `tr_table_purpose`, `trg_purpose`, `trigger_purpose`. | LOW | DX | 0.5h |
| DB-27 | **`pipeline_items.search_id` e TEXT, nao UUID**. Tipo incompativel com `search_sessions.search_id` UUID. Sem FK possivel. | LOW | Schema | 0.5h |

---

## 3. Debitos de Frontend/UX (fonte: frontend-spec.md)

> :warning: PENDENTE: Revisao do @ux-design-expert

### CRITICAL

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| FE-01 | **Inline `var()` ao inves de classes Tailwind semanticas**. 1,417+ ocorrencias de `bg-[var(--*)]` e `text-[var(--*)]` em 100+ arquivos. Deveria usar tokens mapeados (ex: `bg-canvas` ao inves de `bg-[var(--canvas)]`). DEBT-012 abordou parcialmente mas adocao incompleta. | CRITICAL | Design System | 40h |

### HIGH

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| FE-02 | **Component library UI ausente**. Apenas 6 primitivos (Button, Input, Label, Pagination, CurrencyInput, Slot). Faltam Card, Badge, Tabs, Select, Modal, Dropdown, Toast wrapper, Dialog, Tooltip. Componentes reconstruidos per page. | HIGH | Design System | 24h |
| FE-03 | **Complexidade da pagina Buscar**. 41 componentes + 9 hooks + orchestration pattern. `useSearchOrchestration` compoe 8+ hooks. Prop drilling por SearchForm (30+ props). | HIGH | Manutencao | 16h |
| FE-04 | **Padrao inconsistente de error pages**. Root error.tsx tem UI completa com Sentry. Per-route error.tsx variam em qualidade. Alguns nao reportam ao Sentry. | HIGH | Resiliencia | 4h |
| FE-05 | **Cores hex raw em global-error.tsx e ThemeProvider**. 5 ocorrencias de hex raw (#116dff, #0a1e3f) fora do sistema de design tokens. | HIGH | Design System | 1h |
| FE-06 | **Padrao de dual footer**. Buscar page tem footer proprio E NavigationShell tem footer minimo. Intencional (SAB-013/DEBT-105) mas confuso para usuarios. | HIGH | UX | 4h |
| FE-07 | **useIsMobile initial false flash**. useState(false) significa que SSR/render inicial assume desktop. Causa layout shift quando client hidrata em mobile. | HIGH | UX | 2h |
| FE-08 | **Sem estrategia de image optimization**. Apenas 1 uso de `next/image` no codebase inteiro (HeroSection). Paginas marketing, blog, about com imagens nao otimizadas. | HIGH | Performance | 8h |

### MEDIUM

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| FE-09 | **Localizacao inconsistente de componentes**. `app/components/` vs `components/` -- dois diretorios sem fronteira clara. Imports usam paths relativos mistos. | MEDIUM | DX | 8h |
| FE-10 | **Blog/SEO pages sem loading states**. Server components sem loading.tsx para streaming fallback. | MEDIUM | UX | 2h |
| FE-11 | **Definicoes de animacao duplicadas**. fadeInUp/fadeIn em globals.css E tailwind.config.ts. Shimmer, float tambem duplicados. | MEDIUM | DX | 2h |
| FE-12 | **Algumas pages sem PageErrorBoundary**. Nem todas protected pages envolvem conteudo em PageErrorBoundary. | MEDIUM | Resiliencia | 3h |
| FE-13 | **Falta aria-current no Sidebar**. BottomNav usa `aria-current="page"` mas Sidebar nao seta em links ativos. | MEDIUM | Acessibilidade | 1h |
| FE-14 | **Feature-gated pages ainda roteáveis**. `/alertas`, `/mensagens` ocultas da navegacao (SHIP-002 AC9) mas rotas existem e renderizam. Deveria mostrar "em breve" ou redirecionar. | MEDIUM | UX | 2h |
| FE-15 | **Admin pages sem responsive design**. Admin metrics, SLO, partners com tabelas complexas que overflow em mobile. | MEDIUM | UX | 8h |
| FE-16 | **Sem Storybook ou component playground**. Sem forma de navegar, testar ou demonstrar componentes em isolamento. | MEDIUM | DX | 16h |
| FE-17 | **Pull-to-refresh desktop desabilitado via pointer-events**. Abordagem CSS fragil. Melhor condicionar render do componente. | MEDIUM | DX | 1h |
| FE-18 | **Shepherd.js custom theme usa Tailwind raw**. `bg-white`, `text-gray-700` nao usam CSS variables do design token. Errado em custom themes. | MEDIUM | Design System | 2h |
| FE-19 | **react-hook-form em devDependencies**. Listado em devDependencies mas usado em production pages (signup, onboarding). Deveria ser dependency. | MEDIUM | Build | 0.5h |
| FE-20 | **Inline SVGs sem `aria-hidden="true"`**. SVGs decorativos em alguns componentes podem ser anunciados por screen readers. | MEDIUM | Acessibilidade | 3h |
| FE-21 | **Focus management apos modal close**. Nem todos modals retornam foco ao trigger (BottomNav faz, BuscarModals incerto). | MEDIUM | Acessibilidade | 4h |
| FE-22 | **PlanToggle radio buttons sem focus visible**. Radio group customizado pode nao ter focus ring visivel via teclado. | MEDIUM | Acessibilidade | 2h |
| FE-23 | **59 API route files**. Cada cria serverless function. A maioria usa factory `createProxyRoute`, mas volume pode aumentar cold start times. | MEDIUM | Performance | 4h |

### LOW

| ID | Descricao | Severidade | Area | Estimativa |
|----|-----------|-----------|------|------------|
| FE-24 | **Sem testes automatizados de acessibilidade no CI**. @axe-core/playwright instalado mas integracao com CI incerta. | LOW | Acessibilidade | 4h |
| FE-25 | **Tailwind content paths incluem `pages/`**. Diretorio `pages/` nao existe (App Router), scan desnecessario. | LOW | Build | 0.5h |
| FE-26 | **Imports circulares potenciais**. Hooks em `components/` importam de `app/components/AuthProvider`. | LOW | DX | 4h |
| FE-27 | **NProgress para transicoes de pagina**. Leve mas poderia usar loading indicators built-in do Next.js. | LOW | DX | 2h |
| FE-28 | **Multiplos padroes de formatacao de datas**. `timeAgo()`, `formatDate()`, `toLocaleDateString()` inline. Deveria consolidar. | LOW | DX | 3h |
| FE-29 | **Sonner toast + custom error banners**. Alguns erros via toast, outros via banners inline. Sem estrategia consistente. | LOW | UX | 4h |
| FE-30 | **Shepherd arrow hidden**. `.shepherd-arrow { display: none }` remove conexao visual com target. | LOW | UX | 1h |
| FE-31 | **Dashboard icon duplicado no BottomNav**. Dashboard usa Search icon ao inves de LayoutDashboard no mobile nav. | LOW | UX | 0.5h |
| FE-32 | **Framer Motion bundle**. ~32KB gzipped. Apenas landing/marketing. Poderia ser code-split mais. | LOW | Performance | 2h |

---

## 4. Matriz Preliminar de Priorizacao

| # | ID | Debito | Area | Severidade | Impacto | Esforco (h) | Prioridade |
|---|------|--------|------|------------|---------|-------------|------------|
| 1 | SYS-01 | CORS permite todas origens (`*`) | Seguranca | CRITICAL | Users em risco de ataques cross-origin | 2h | P0 |
| 2 | SYS-02 | PNCP client sincrono (`requests`) | Arquitetura | CRITICAL | Limita concorrencia, complexidade desnecessaria | 16h | P0 |
| 3 | SYS-03 | ComprasGov v3 offline sem monitoramento | Integracao | CRITICAL | Fonte de dados silenciosamente indisponivel | 4h | P0 |
| 4 | DB-01 | Stripe price IDs hardcoded em migrations | Seguranca | CRITICAL | Staging pode cobrar precos producao | 2h | P0 |
| 5 | FE-01 | 1,417+ inline var() ao inves de Tailwind tokens | Design System | CRITICAL | Debt composto: cada novo componente herda pattern ruim | 40h | P0 |
| 6 | SYS-04 | Metricas Prometheus efemeras | Observabilidade | HIGH | Sem historico de SLO apos deploys | 8h | P1 |
| 7 | SYS-05 | Health canary nao detecta PNCP page size limit | Integracao | HIGH | Regressao silenciosa de data source | 4h | P1 |
| 8 | SYS-06 | Route registration nao visivel em main.py | DX | HIGH | Onboarding lento de novos devs | 4h | P1 |
| 9 | SYS-07 | Versionamento de API inconsistente | Arquitetura | HIGH | Breaking changes futuras dificeis | 8h | P1 |
| 10 | SYS-08 | Sem request timeout na aplicacao | Resiliencia | HIGH | Worker preso por downstream lento | 4h | P1 |
| 11 | SYS-09 | Worker liveness depende do Redis | Resiliencia | HIGH | Sem alerta para ausencia prolongada | 4h | P1 |
| 12 | SYS-10 | Search decomposition backward-compat re-exports | DX | HIGH | Import graph fragil, tests quebram | 4h | P1 |
| 13 | DB-02 | handle_new_user() omite trial_expires_at | Schema | HIGH | Trial expiration nao setada no signup | 2h | P1 |
| 14 | DB-03 | COUNT(*) OVER() em conversations | Performance | HIGH | O(N) scan a cada page load admin | 4h | P1 |
| 15 | DB-04 | profiles.plan_type sem reconciliacao | Integridade | HIGH | Drift de plano nao detectado | 4h | P1 |
| 16 | DB-05 | partner_referrals orfaos acumulam | Integridade | HIGH | Tabela cresce sem bound | 1h | P1 |
| 17 | DB-06 | user_subscriptions sem retention | Integridade | HIGH | Tabela cresce sem bound | 1h | P1 |
| 18 | FE-02 | Component library UI ausente (6 primitivos) | Design System | HIGH | Componentes reconstruidos ad-hoc | 24h | P1 |
| 19 | FE-03 | Buscar page complexidade (41 components, 30+ props) | Manutencao | HIGH | Alto custo de manutencao | 16h | P1 |
| 20 | FE-04 | Error pages inconsistentes | Resiliencia | HIGH | Errors nao reportados ao Sentry | 4h | P1 |
| 21 | FE-05 | Cores hex raw fora do design system | Design System | HIGH | Tema inconsistente | 1h | P1 |
| 22 | FE-06 | Dual footer confuso | UX | HIGH | Experiencia de usuario confusa | 4h | P1 |
| 23 | FE-07 | useIsMobile layout shift em mobile | UX | HIGH | Layout flickering na hidracao | 2h | P1 |
| 24 | FE-08 | Sem image optimization (1 uso de next/image) | Performance | HIGH | Paginas lentas, sem WebP/AVIF | 8h | P1 |
| 25 | SYS-11 | filter.py keyword sets hardcoded | Arquitetura | MEDIUM | Config duplicada | 4h | P2 |
| 26 | SYS-12 | Multiplas implementacoes de cache | Arquitetura | MEDIUM | Logica de eviction inconsistente | 8h | P2 |
| 27 | SYS-13 | Sem version tracking de migrations | Infra | MEDIUM | Sem verificacao runtime | 4h | P2 |
| 28 | SYS-14 | Test pollution nao eliminada | Testes | MEDIUM | Flaky tests em full suite | 12h | P2 |
| 29 | SYS-15 | Frontend sem state management global | Frontend | MEDIUM | Prop drilling complexo | 16h | P2 |
| 30 | SYS-16 | Dual connection pool management | Resiliencia | MEDIUM | Sem backpressure cross-pool | 8h | P2 |
| 31 | DB-07 | Verificar reconciliation_log policy | RLS | MEDIUM | Policy potencialmente ineficiente | 0.5h | P2 |
| 32 | DB-08 | search_state_transitions.user_id nullable | Schema | MEDIUM | Dados inconsistentes | 1h | P2 |
| 33 | DB-09 | classification_feedback FK ordering | Schema | MEDIUM | Fragil em fresh install | 1h | P2 |
| 34 | DB-10 | System cache warmer em auth.users | Seguranca | MEDIUM | Confunde admin dashboards | 1h | P2 |
| 35 | DB-11 | OAuth tokens no public schema | Seguranca | MEDIUM | Risco se DB + key comprometidos | 2h | P2 |
| 36 | DB-12 | Tres convencoes de nomes em migrations | DX | MEDIUM | Confuso para novos devs | 4h | P2 |
| 37 | DB-13 | Sem down migrations | Infra | MEDIUM | Rollback manual em producao | 2h | P2 |
| 38 | DB-14 | Cache cleanup trigger COUNT a cada INSERT | Performance | MEDIUM | Overhead por cache write | 1h | P2 |
| 39 | DB-15 | alert_sent_items retention scan pattern | Performance | MEDIUM | Full scan diario | 0.5h | P2 |
| 40 | DB-16 | search_state_transitions sem FK (by design) | Integridade | MEDIUM | Orfaos possiveis | 1h | P2 |
| 41 | DB-17 | organizations.plan_type CHECK permissivo | Integridade | MEDIUM | Tipos legacy aceitos | 0.5h | P2 |
| 42 | FE-09 | Component locations inconsistentes | DX | MEDIUM | Imports confusos | 8h | P2 |
| 43 | FE-10 | Blog/SEO pages sem loading states | UX | MEDIUM | Streaming fallback ausente | 2h | P2 |
| 44 | FE-11 | Animacoes duplicadas (CSS + Tailwind) | DX | MEDIUM | Definicoes divergentes | 2h | P2 |
| 45 | FE-12 | Pages sem PageErrorBoundary | Resiliencia | MEDIUM | Erros nao capturados | 3h | P2 |
| 46 | FE-13 | Falta aria-current no Sidebar | Acessibilidade | MEDIUM | Screen readers nao indicam pagina ativa | 1h | P2 |
| 47 | FE-14 | Feature-gated pages ainda roteáveis | UX | MEDIUM | Usuario chega em pagina vazia | 2h | P2 |
| 48 | FE-15 | Admin pages sem responsive | UX | MEDIUM | Tabelas overflow em mobile | 8h | P2 |
| 49 | FE-16 | Sem Storybook | DX | MEDIUM | Nao se testa componentes isolados | 16h | P2 |
| 50 | FE-17 | Pull-to-refresh desktop hack CSS | DX | MEDIUM | Abordagem fragil | 1h | P2 |
| 51 | FE-18 | Shepherd.js Tailwind raw | Design System | MEDIUM | Tema errado em dark mode | 2h | P2 |
| 52 | FE-19 | react-hook-form em devDependencies | Build | MEDIUM | Pode quebrar em producao se tree-shaked | 0.5h | P2 |
| 53 | FE-20 | SVGs sem aria-hidden | Acessibilidade | MEDIUM | Screen readers anunciam decorativos | 3h | P2 |
| 54 | FE-21 | Focus nao retorna apos modal close | Acessibilidade | MEDIUM | Foco perde contexto | 4h | P2 |
| 55 | FE-22 | PlanToggle sem focus visible | Acessibilidade | MEDIUM | Navegacao teclado prejudicada | 2h | P2 |
| 56 | FE-23 | 59 API route files (cold start) | Performance | MEDIUM | Cold start potencialmente lento | 4h | P2 |
| 57 | SYS-17 | Titulo app "BidIQ Uniformes" | DX | LOW | Confuso | 1h | P3 |
| 58 | SYS-18 | Versao FastAPI 0.2.0 | DX | LOW | Metadata incorreta | 0.5h | P3 |
| 59 | SYS-19 | Comentarios com Issue numbers sem links | DX | LOW | Legibilidade | 4h | P3 |
| 60 | SYS-20 | SEO pages hardcoded | Frontend | LOW | Deploy pra novo conteudo | 8h | P3 |
| 61 | DB-18 | stripe_price_id deprecated presente | Schema | LOW | Confusao de schema | 1h | P3 |
| 62 | DB-19 | created_at nullable inconsistente | Schema | LOW | Queries inesperadas | 1h | P3 |
| 63 | DB-20 | Indexes sobrepostos search_sessions | Performance | LOW | Desperdicio storage | 1h | P3 |
| 64 | DB-21 | trial_email_log sem policy explicita | RLS | LOW | Documentacao | 0.5h | P3 |
| 65 | DB-22 | Org admins sem UPDATE | RLS | LOW | Backend cobre | 0.5h | P3 |
| 66 | DB-23 | Migration 027b superseded | DX | LOW | Dead code | 0.5h | P3 |
| 67 | DB-24 | Legacy backend/migrations presente | DX | LOW | Confusao | 0.5h | P3 |
| 68 | DB-25 | Constraint names inconsistentes | DX | LOW | Cosmetico | 2h | P3 |
| 69 | DB-26 | Trigger names inconsistentes | DX | LOW | Cosmetico | 0.5h | P3 |
| 70 | DB-27 | pipeline_items.search_id TEXT vs UUID | Schema | LOW | Sem FK possivel | 0.5h | P3 |
| 71 | FE-24 | Sem a11y tests no CI | Acessibilidade | LOW | Regressoes nao detectadas | 4h | P3 |
| 72 | FE-25 | Tailwind content paths com pages/ | Build | LOW | Scan desnecessario | 0.5h | P3 |
| 73 | FE-26 | Imports circulares potenciais | DX | LOW | Risco de ciclo | 4h | P3 |
| 74 | FE-27 | NProgress vs built-in Next.js | DX | LOW | Dependencia extra | 2h | P3 |
| 75 | FE-28 | Formatacao de datas inconsistente | DX | LOW | 3 padroes diferentes | 3h | P3 |
| 76 | FE-29 | Toast vs banner inconsistente | UX | LOW | Sem estrategia unica | 4h | P3 |
| 77 | FE-30 | Shepherd arrow hidden | UX | LOW | Visual tour degradado | 1h | P3 |
| 78 | FE-31 | Dashboard icon errado no BottomNav | UX | LOW | Icone inconsistente | 0.5h | P3 |
| 79 | FE-32 | Framer Motion bundle size | Performance | LOW | 32KB extra | 2h | P3 |

---

## 5. Analise de Dependencias

### Chains de Dependencia

```
FE-01 (inline var) --> FE-02 (component library)
  Se criar component library PRIMEIRO, novos componentes ja usam tokens certos.
  Migrar 1,417 ocorrencias fica mais facil com componentes que encapsulam tokens.

FE-02 (component library) --> FE-03 (buscar complexity)
  Componentes compartilhados (Card, Badge, Modal) reduzem duplicacao em buscar.
  Refactoring de buscar para context depende de primitivos estaveis.

FE-09 (component locations) --> FE-02 (component library)
  Unificar localizacao ANTES de criar novos primitivos evita mais dispersao.

SYS-01 (CORS *) --> Independente, deve ser corrigido IMEDIATAMENTE (P0)

SYS-02 (PNCP sync) --> SYS-12 (cache implementations)
  Migrar PNCP para httpx async simplifica a camada de cache (mesmo pattern).

DB-01 (Stripe IDs) --> Independente, deve ser corrigido IMEDIATAMENTE (P0)

DB-02 (handle_new_user) --> DB-08 (search_state_transitions NOT NULL)
  Ambos sao mudancas no trigger/schema. Podem ser agrupados em 1 migration.

DB-04 (plan_type reconciliacao) --> DB-06 (user_subscriptions retention)
  Reconciliacao precisa de user_subscriptions limpo para nao detectar falsos positivos.

DB-05 + DB-06 (retention jobs) --> Independentes entre si, podem ser paralelos

SYS-14 (test pollution) --> Bloqueia velocidade de TODOS os outros items
  Test pollution causa flaky tests que atrasam PRs. Resolver cedo multiplica produtividade.

SYS-15 (state management) ~= FE-03 (buscar complexity)
  Mesmo problema visto de angulos diferentes. Resolver juntos.
```

### Ordem Recomendada de Execucao

**Sprint 0 (Quick Wins -- 1 semana):**
1. SYS-01 (CORS) -- 2h, risco de seguranca imediato
2. DB-01 (Stripe IDs) -- 2h, risco de seguranca
3. FE-05 (hex raw) -- 1h, quick fix
4. FE-19 (react-hook-form dep) -- 0.5h, quick fix
5. SYS-17 + SYS-18 (titulo + versao) -- 1.5h, quick fix
6. DB-02 (handle_new_user trigger) -- 2h, data integrity

**Sprint 1 (Foundation -- 2 semanas):**
7. SYS-08 (request timeout middleware) -- 4h, resiliencia critica
8. DB-05 + DB-06 (retention jobs) -- 2h, crescimento descontrolado
9. FE-09 (unificar component locations) -- 8h, pre-requisito de FE-02
10. SYS-14 (test pollution) -- 12h, desbloqueia velocidade do time

**Sprint 2 (Core Improvements -- 2 semanas):**
11. FE-02 (component library) -- 24h, fundacao para FE-01
12. SYS-02 (PNCP async) -- 16h, debloqueio de performance
13. DB-04 (plan_type reconciliacao) -- 4h, integridade billing

**Sprint 3 (Polish -- 2 semanas):**
14. FE-01 (inline var migration) -- 40h, com componentes prontos vai mais rapido
15. FE-03 (buscar refactor) -- 16h, com component library pronta

---

## 6. Resumo Quantitativo

### Totais Gerais

| Metrica | Valor |
|---------|-------|
| **Total de debitos** | **79** |
| CRITICAL | 5 |
| HIGH | 19 |
| MEDIUM | 32 |
| LOW | 23 |

### Por Area de Origem

| Fonte | Debitos | CRIT | HIGH | MED | LOW | Horas |
|-------|---------|------|------|-----|-----|-------|
| Sistema (system-architecture.md) | 20 | 3 | 7 | 6 | 4 | 148.5h |
| Database (DB-AUDIT.md) | 27 | 1 | 5 | 11 | 10 | 40h |
| Frontend/UX (frontend-spec.md) | 32 | 1 | 7 | 15 | 9 | 180h |
| **Total** | **79** | **5** | **19** | **32** | **23** | **368.5h** |

> **Nota sobre sobreposicao:** SYS-15 (state management, 16h) e FE-03 (buscar complexity, 16h) descrevem o mesmo problema de angulos diferentes. O esforco real e ~20h combinados, nao 32h. A estimativa consolidada ajustada e **~372.5h** (soma bruta 368.5h ajustada para duplicatas).

### Por Prioridade

| Prioridade | Debitos | Horas |
|------------|---------|-------|
| P0 (Imediato) | 5 | 64h |
| P1 (Proximo sprint) | 19 | 107h |
| P2 (Medio prazo) | 32 | 148h |
| P3 (Backlog) | 23 | 53.5h |

### Por Categoria Funcional

| Categoria | Debitos | Horas |
|-----------|---------|-------|
| Seguranca | 5 | 9h |
| Design System | 6 | 69h |
| DX (Developer Experience) | 16 | 42.5h |
| Resiliencia | 6 | 27h |
| Performance | 8 | 23h |
| Integridade de Dados | 6 | 12h |
| Acessibilidade | 6 | 17h |
| Arquitetura | 5 | 44h |
| Observabilidade | 1 | 8h |
| UX | 7 | 23h |
| Testes | 1 | 12h |
| Infra / Build | 5 | 11h |
| Schema | 7 | 8.5h |
| RLS | 3 | 1.5h |
| Integracao | 2 | 8h |
| Manutencao | 1 | 16h |
| Frontend (misc) | 2 | 24h |

---

## 7. Perguntas para Especialistas

### Para @data-engineer:

1. **SEC-01 (DB-01) -- Stripe price IDs:** A estrategia recomendada e mover para env vars, config table, ou ambos? Ha risco de break em rollback se removermos os IDs das migrations existentes (migrations ja aplicadas nao re-executam, mas fresh installs sim)?

2. **D-01 (DB-04) -- plan_type drift:** Qual e a frequencia observada de drift entre `profiles.plan_type` e `user_subscriptions`? O reconciliation job existente ja roda periodicamente? Temos metricas de quantas vezes o fallback "last known plan" foi ativado em producao?

3. **P-01 (DB-03) -- COUNT(*) OVER():** A tabela `conversations` tem quantas rows em producao atualmente? Para admins, qual o volume medio de conversas? Seria melhor um count query separado com cache, ou migrar para uma materialized view que atualiza via pg_cron?

4. **D-05/D-06 (DB-05/06) -- Retention:** Os pg_cron jobs existentes de retention cobrem quantas tabelas atualmente? Ha um padrao padronizado (template SQL de retention) que deveriamos seguir para `partner_referrals` e `user_subscriptions`? Qual intervalo de retention e seguro para subscriptions inativas (12 meses? 24 meses?)?

5. **M-01 (DB-12) -- Migration squash:** Qual o risco de fazer migration squash agora? Temos ambientes (staging, dev local) que dependem de replay incremental das 86 migrations? O Supabase CLI suporta squash nativo ou teriamos que fazer manual?

### Para @ux-design-expert:

1. **FE-01 -- inline var() migration:** Qual a estrategia de adocao recomendada? Migrar por pagina (top-down), por componente (bottom-up), ou por token (horizontal)? Devemos criar um codemod automatico para converter `bg-[var(--canvas)]` -> `bg-canvas`?

2. **FE-02 -- Component library:** Quais 5 primitivos sao mais urgentes para construir primeiro? Devemos adotar Radix UI (headless) como base ou construir do zero usando nossa CVA pattern existente? Ha design system de referencia (ex: Shadcn/UI) que deveriamos seguir?

3. **FE-06 -- Dual footer:** O footer da buscar page tem funcionalidades especificas (ex: atalhos, metricas) que justificam sua existencia separada? Podemos unificar em um unico footer com variantes contextuais, ou sao realmente dois footers distintos por necessidade de UX?

4. **FE-07 -- useIsMobile flash:** Qual a melhor abordagem para SSR-safe responsive? CSS-only com media queries, `useMediaQuery` com SSR-safe default via cookies/headers, ou `matchMedia` sync no primeiro client render? Ha impacto mensuravel no CLS (Cumulative Layout Shift) em producao?

5. **FE-08 -- Image optimization:** Quantas imagens nao-otimizadas existem no codebase atualmente? Ha imagens em `/public` que nunca passam pelo `next/image` pipeline? Qual o saving estimado em LCP se migrarmos todas para WebP/AVIF via `next/image`?

6. **FE-15 -- Admin responsive:** Dado que admin pages sao usadas por <5 usuarios internos, vale o investimento de 8h em responsive completo ou devemos apenas adicionar `overflow-x-auto` como paliativo (1h) e mover para P3?

### Para @qa:

1. **SYS-14 -- Test pollution:** Dos 8+ padroes documentados em MEMORY.md, quais causam mais flakes na pratica? O `run_tests_safe.py --parallel` com subprocess isolation elimina todos os problemas, ou restam padroes que falham mesmo com isolamento?

2. **Cobertura de testes dos debitos CRITICAL:** Temos testes que validam o comportamento atual de CORS (`SYS-01`)? Se corrigirmos para origens especificas, quais testes de integracao quebram? Ha testes E2E que dependem do CORS `*`?

3. **FE-04 -- Error pages:** Quais rotas protegidas NAO tem error.tsx atualmente? Podemos criar um script automatizado que verifique cobertura de error boundaries (ex: lint rule ou test que lista rotas sem error.tsx)?

4. **Regressao em migration squash (DB-12):** Se fizermos squash de migrations, qual a estrategia de teste para garantir equivalencia? Temos CI que roda fresh install com todas migrations aplicadas? O `supabase db push` em clean database valida integridade completa?

5. **FE-24 -- a11y testing:** O @axe-core/playwright esta configurado nos E2E existentes ou apenas instalado? Quantas violacoes WCAG AA existem atualmente (baseline)? Qual seria o threshold aceitavel para gate no CI (0 critical + N warnings)?

---

*Gerado 2026-03-20 por @architect (Atlas) durante Brownfield Discovery Phase 4.*
*Fontes: system-architecture.md (Phase 1), SCHEMA.md + DB-AUDIT.md (Phase 2), frontend-spec.md (Phase 3).*
