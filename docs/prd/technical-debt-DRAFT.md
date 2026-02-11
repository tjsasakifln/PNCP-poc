# Technical Debt Assessment - DRAFT
## Para Revisao dos Especialistas

**Projeto:** SmartLic/BidIQ
**Data:** 2026-02-11
**Status:** DRAFT - Pendente validacao dos especialistas
**Commit:** `808cd05` (branch `main`)
**Fontes:**
1. `docs/architecture/system-architecture.md` -- @architect (Aria)
2. `supabase/docs/SCHEMA.md` -- @data-engineer (Dara)
3. `supabase/docs/DB-AUDIT.md` -- @data-engineer (Dara)
4. `docs/frontend/frontend-spec.md` -- @ux-design-expert (Uma)

---

### 1. Resumo Executivo

O SmartLic/BidIQ e um SaaS em producao (POC v0.3) para descoberta automatizada de oportunidades de contratacao publica no PNCP. O sistema esta funcional com usuarios reais, porem carrega debito tecnico significativo acumulado durante o crescimento rapido de features.

**Avaliacao Geral de Saude:**
- **Backend/Arquitetura:** MEDIO (funcional, mas com riscos de escalabilidade)
- **Database:** 6.5/10 (funcional para POC, gaps de seguranca e consistencia)
- **Frontend/UX:** MEDIO-ALTO (rico em features, mas com monolitos e duplicacoes)

**Contagem Total de Debitos:**

| Severidade | Sistema | Database | Frontend | Cross-Cutting | Total |
|-----------|---------|----------|----------|---------------|-------|
| CRITICAL | 4 | 3 | 3 | 2 | **12** |
| HIGH | 5 | 5 | 6 | 1 | **17** |
| MEDIUM | 8 | 7 | 9 | 2 | **26** |
| LOW | 6 | 4 | 7 | 0 | **17** |
| **Total** | **23** | **19** | **25** | **5** | **72** |

**Esforco Total Estimado:** 280-380 horas

---

### 2. Debitos de Sistema/Arquitetura

Extraido de: `docs/architecture/system-architecture.md` -- @architect (Aria)

#### 2.1 CRITICAL

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| SYS-C01 | In-memory state impede escalabilidade horizontal | `_active_trackers` dict em `progress.py:98` armazena estado SSE em memoria. Se mais de 1 instancia for deployada, progresso de busca quebra. Estado perdido em restart. | `backend/progress.py:98` | 16-24h (requer Redis pub/sub) |
| SYS-C02 | Monolito main.py (1.959 linhas) | Contem 20+ endpoints, logica de negocio, funcoes helper, handlers de billing. Dificil de manter e testar isoladamente. | `backend/main.py` | 12-16h |
| SYS-C03 | Dual ORM/DB access pattern | Dois mecanismos de acesso ao banco coexistem: Supabase Python Client (95% do codigo) e SQLAlchemy (Stripe webhooks). Risco de drift de schema. | `backend/supabase_client.py`, `backend/database.py` | 8-12h |
| SYS-C04 | Falhas pre-existentes de testes | Backend: 21 falhas; Frontend: 70 falhas. Pipeline de CI falha, mascarando novas regressoes. Quality gate nao funcional. | Backend tests, Frontend tests | 8-16h |

#### 2.2 HIGH

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| SYS-H01 | Cliente PNCP sincrono em contexto async | `PNCPClient` usa `requests` (bloqueante) como fallback. Bloqueia event loop quando utilizado. Apenas `AsyncPNCPClient` e non-blocking. | `backend/pncp_client.py:67-557` | 4-6h |
| SYS-H02 | Excel armazenado em filesystem temporario | Arquivos temp nao sao compartilhados entre instancias. TTL de 60 min via `setTimeout` nao e confiavel. Arquivos sobrevivem restart. | `frontend/app/api/buscar/route.ts:180-204` | 6-8h |
| SYS-H03 | Sem migrations de banco trackeadas no repo | Nenhum diretorio `migrations/` padrao encontrado. Mudancas de schema dependem de operacoes manuais no dashboard Supabase. | N/A | 4-6h |
| SYS-H04 | Logica de negocio em funcoes helper do main.py | Logica de autorizacao core (`_check_user_roles`, `_is_admin`, `_has_master_access`) co-localizada com route handlers. Nao pode ser testada unitariamente. | `backend/main.py:392-523` | 4-6h |
| SYS-H05 | Dependencias de desenvolvimento em requirements de producao | pytest, ruff, mypy, locust, faker instalados em producao. Aumenta superficie de ataque e tamanho da imagem. | `backend/requirements.txt:37-50` | 2-3h |

#### 2.3 MEDIUM

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| SYS-M01 | Sem request ID / correlation ID | Impossivel rastrear um request entre entradas de log ou entre proxy frontend e backend. Dificil debugar em producao. | Todo backend | 3-4h |
| SYS-M02 | Token cache usa `hash()` do prefixo do token | `hash()` do Python nao e criptograficamente seguro e varia entre execucoes. Potencial para colisoes em instancias de longa duracao. | `backend/auth.py:45` | 2-3h |
| SYS-M03 | Rate limiter in-memory sem tamanho maximo | Memoria cresce sem limite com user IDs unicos no fallback in-memory. Garbage collection so remove entradas > 60s. | `backend/rate_limiter.py:84-89` | 2-3h |
| SYS-M04 | Capacidades de plano hardcoded | Definicoes de plano estao no codigo Python, nao no banco. Adicionar novo plano requer deploy de codigo. | `backend/quota.py:62-95` | 4-6h |
| SYS-M05 | Google API credentials handling | Integracao Google Sheets adiciona 4 dependencias pesadas. Mecanismo de armazenamento de token OAuth nao visivel. | `backend/requirements.txt:29-33` | 2-3h |
| SYS-M06 | `datetime.utcnow()` deprecated | Python 3.12 depreca `datetime.utcnow()`. Deve usar `datetime.now(timezone.utc)` consistentemente. | Multiplos arquivos | 2-3h |
| SYS-M07 | Cobertura frontend abaixo do threshold | 49.46% vs alvo de 60%. Gate de cobertura CI falha. Gap principalmente em LoadingProgress, RegionSelector, SavedSearchesDropdown, AnalyticsProvider. | `frontend/` | 8-12h |
| SYS-M08 | Sem versionamento de API | Todos endpoints sem versao. Breaking changes requerem deploy coordenado frontend/backend. | `backend/main.py` | 4-6h |

#### 2.4 LOW

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| SYS-L01 | Sem validacao de OpenAPI schema em testes | Drift de contrato API entre backend e frontend pode passar despercebido. | Backend tests | 4-6h |
| SYS-L02 | Uso de emoji em logs de producao | Agregadores de log podem nao renderizar emojis corretamente. | `backend/pncp_client.py:525,533` | 1h |
| SYS-L03 | CSS inline em layout.tsx | Script de inicializacao de tema usa inline styles. Deveria usar CSS variables exclusivamente. | `frontend/app/layout.tsx:62-77` | 1-2h |
| SYS-L04 | Sem middleware de logging de request/response | Sem logging centralizado de requests (duracao, status code, path). Cada endpoint loga individualmente. | Backend | 3-4h |
| SYS-L05 | Imports nao utilizados em main.py | `from filter import match_keywords, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO` importado dentro de loop diagnostico. | `backend/main.py:1694` | 0.5h |
| SYS-L06 | Sem health check para Redis | Endpoint de health checa Supabase e OpenAI mas nao Redis. Rate limiting degrada silenciosamente. | `backend/main.py:162-229` | 2h |

**Subtotal Sistema:** 23 debitos | Esforco: ~105-155h

---

### 3. Debitos de Database

Extraido de: `supabase/docs/SCHEMA.md` e `supabase/docs/DB-AUDIT.md` -- @data-engineer (Dara)

> PENDENTE: Revisao do @data-engineer

#### 3.1 CRITICAL

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| DB-C01 | `database.py` deriva URL PostgreSQL incorretamente de SUPABASE_URL | O motor SQLAlchemy constroi URL PostgreSQL substituindo `https://` em `SUPABASE_URL`, que e uma URL HTTPS (nao PostgreSQL). Conexao provavelmente falha silenciosamente ou usa fallback localhost. | `backend/database.py:33` | 2-3h |
| DB-C02 | `user_subscriptions` sem policy RLS de service role para writes | Backend usa `SUPABASE_SERVICE_ROLE_KEY` para INSERT/UPDATE subscriptions. Se comportamento de bypass RLS mudar, toda gestao de subscriptions quebra silenciosamente. Inconsistente com pattern de `monthly_quota` e `search_sessions`. | `supabase/migrations/001_profiles_and_sessions.sql:119-121` | 1-2h |
| DB-C03 | `stripe_webhook_events` admin check usa `plan_type = 'master'` em vez de `is_admin` | Policy SELECT verifica `plan_type = 'master'` mas flag real de admin e `is_admin`. Admin com `plan_type != 'master'` nao pode ver webhook events. Non-admin master user PODE ver. | `supabase/migrations/010_stripe_webhook_events.sql:61-68` | 1h |

#### 3.2 HIGH

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| DB-H01 | Dual ORM Architecture (Supabase Client + SQLAlchemy) | Dois mecanismos de acesso DB completamente separados. Diferentes estrategias de transacao, pools de conexao, risco de drift de schema. | `backend/supabase_client.py`, `backend/database.py`, `backend/models/` | 8-12h |
| DB-H02 | Migration 006 duplicada (3 arquivos) | Tres arquivos com prefixo `006_`. `006_APPLY_ME.sql` contem instrucoes para aplicar manualmente via Supabase dashboard. Ambiguidade sobre quais migrations foram aplicadas. | `supabase/migrations/006_*` | 2-3h |
| DB-H03 | Index faltando em `user_subscriptions.stripe_subscription_id` | Stripe webhook handler consulta por `stripe_subscription_id`. SQLAlchemy model define `unique=True` mas SQL migration NAO cria constraint. Index pode nao existir. | `backend/webhooks/stripe.py:187-189`, `backend/main.py:795` | 1h |
| DB-H04 | Policies RLS overly permissive (`USING (true)` sem restricao de role) | `monthly_quota` e `search_sessions` tem policies `FOR ALL USING (true)` sem clausula `TO service_role`. Permite qualquer usuario autenticado realizar qualquer operacao. | Migrations 002, 006 | 1-2h |
| DB-H05 | `profiles` sem INSERT policy para trigger de auth | `handle_new_user()` roda como `SECURITY DEFINER`, mas `_ensure_profile_exists()` em `quota.py:623-655` insere via service_role key. Policy INSERT explicita tornaria modelo de seguranca explicito. | `supabase/migrations/001_profiles_and_sessions.sql:110-113` | 1h |

#### 3.3 MEDIUM

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| DB-M01 | Foreign Keys inconsistentes (auth.users vs profiles) | `monthly_quota`, `user_oauth_tokens`, `google_sheets_exports` referenciam `auth.users(id)` diretamente; outros referenciam `profiles(id)`. Pattern inconsistente. | Migrations 002, 013, 014 | 3-4h |
| DB-M02 | CHECK constraint `plan_type` inclui valores legacy | Constraint permite 10 valores incluindo 4 legacy (`'free'`, `'avulso'`, `'pack'`, `'monthly'`, `'annual'`) que nao correspondem a planos ativos. Nada impede novos usuarios de receberem tipos deprecated. | `supabase/migrations/006_update_profiles_plan_type_constraint.sql` | 2-3h |
| DB-M03 | Coluna `updated_at` faltando em migration para `user_subscriptions` | Migration 001 NAO inclui `updated_at`, mas migration 008 e codigo aplicacao escrevem nessa coluna. Pode ter sido adicionada manualmente. | `001_profiles_and_sessions.sql`, `backend/models/user_subscription.py:83` | 1-2h |
| DB-M04 | `profiles.plan_type` e `user_subscriptions.plan_id` podem divergir | Duas fontes de verdade para plano do usuario. Fallback de 4 camadas bem desenhado, mas modelo de dados permite divergencia indefinida sem reconciliacao. | `backend/quota.py:413-504` | 4-6h |
| DB-M05 | Stripe price IDs hardcoded em migration 015 | Migration contem IDs de preco Stripe de producao. Se aplicada em outro ambiente (staging, dev), configura precos incorretos. | `supabase/migrations/015_add_stripe_price_ids_monthly_annual.sql` | 2-3h |
| DB-M06 | N+1 query em endpoint de lista de conversas | Para cada conversa, query separada conta mensagens nao lidas. Com 50 conversas, produz 51 queries. | `backend/routes/messages.py:114-121` | 3-4h |
| DB-M07 | Endpoints de analytics buscam TODAS as sessions | `get_analytics_summary()` busca TODAS search sessions de um usuario. Power users com 1000+ sessions transferem dados significativos. | `backend/routes/analytics.py:78-83` | 3-4h |

#### 3.4 LOW

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| DB-L01 | Tabela `plans` sem coluna `updated_at` | Sem audit trail de quando atributos do plano mudaram. | Migrations 001, 005 | 1h |
| DB-L02 | Sem retencao/cleanup para `monthly_quota` historico | Linhas historicas acumulam indefinidamente. | N/A | 3-4h |
| DB-L03 | Sem retencao/cleanup para `stripe_webhook_events` | Migration 010 menciona retencao de 90 dias, mas nao implementada. | Migration 010 | 3-4h |
| DB-L04 | Index redundante `idx_user_oauth_tokens_provider` | Tabela com poucas centenas de linhas. UNIQUE constraint em `(user_id, provider)` ja cobre lookups. Index standalone em `provider` (3 valores possiveis) tem selectividade muito baixa. | Migration 013 | 0.5h |

**Subtotal Database:** 19 debitos | Esforco: ~43-62h

---

### 4. Debitos de Frontend/UX

Extraido de: `docs/frontend/frontend-spec.md` -- @ux-design-expert (Uma)

> PENDENTE: Revisao do @ux-design-expert

#### 4.1 CRITICAL

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| FE-C01 | Pagina de busca monolitica (~1100 linhas) | `buscar/page.tsx` contem 30+ useState hooks, toda logica de negocio inline. Componente unico concentrando toda complexidade da aplicacao. | `frontend/app/buscar/page.tsx` | 16-24h |
| FE-C02 | Fallback localhost em rota de analytics | `http://localhost:8000` como fallback para `BACKEND_URL` em rota de analytics. Inconsistente com outras rotas que retornam 503 quando nao configurado. Potencial issue de seguranca. | `frontend/app/api/analytics/route.ts:4` | 1h |
| FE-C03 | Padroes mistos de API | Algumas paginas usam proxy `/api/*`, outras chamam `NEXT_PUBLIC_BACKEND_URL` diretamente do browser. Dois padroes diferentes de forwarding de auth, expoe URL do backend ao cliente. | `historico/page.tsx`, `conta/page.tsx`, `admin/page.tsx` | 8-12h |

#### 4.2 HIGH

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| FE-H01 | Componentes de filtro duplicados | EsferaFilter e MunicipioFilter existem em dois diretorios (`app/components/` e `components/`). | `app/components/EsferaFilter.tsx`, `components/EsferaFilter.tsx`, etc. | 3-4h |
| FE-H02 | Manipulacao direta de DOM em restauracao de estado de busca | `document.createElement` usado para restaurar estado de busca. Anti-pattern em React. | `app/buscar/page.tsx:285-293` | 2-3h |
| FE-H03 | Error boundary ignora design system | Cores Tailwind hardcoded (`bg-gray-50`, `text-red-500`, `bg-green-600`) em vez de tokens de design. Quebra dark mode. | `frontend/app/error.tsx` | 1-2h |
| FE-H04 | `alert()` nativo para feedback de usuario | Usa `window.alert()` em vez do sistema de toast sonner ja instalado. | `app/buscar/page.tsx:1080` | 1h |
| FE-H05 | UF_NAMES duplicado em multiplos arquivos | Mapeamento duplicado entre buscar e dashboard. | `buscar/page.tsx`, `dashboard/page.tsx` | 1-2h |
| FE-H06 | Excel storage em tmpdir() | Perdido em restart, nao escala horizontalmente. TTL via setTimeout nao confiavel. | `app/api/buscar/route.ts`, `app/api/download/route.ts` | 6-8h |

#### 4.3 MEDIUM

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| FE-M01 | Sem app shell compartilhado para paginas protegidas | Cada pagina protegida gerencia seu proprio header independentemente. Sem sidebar ou top-nav comum. | Todas paginas protegidas | 6-8h |
| FE-M02 | Sistema de feature flags subutilizado | Feature flags definidos em `lib/config.ts` mas nao amplamente adotados. | `frontend/lib/config.ts` | 2-3h |
| FE-M03 | Sem biblioteca de validacao de formularios | Validacao ad-hoc por formulario com useState. Sem react-hook-form ou zod. | Login, signup, search pages | 8-12h |
| FE-M04 | Lista STOPWORDS_PT duplicada do backend | Lista de stopwords em portugues duplicada no frontend. | `app/buscar/page.tsx:70-82` | 1-2h |
| FE-M05 | SETORES_FALLBACK requer sync manual | Lista de setores fallback deve ser sincronizada manualmente com backend. | `app/buscar/page.tsx:429-442` | 1h (script existe) |
| FE-M06 | Arquivos stale: `dashboard-old.tsx` | Codigo morto no repositorio. | `app/dashboard-old.tsx` | 0.5h |
| FE-M07 | Arquivos stale: `landing-layout-backup.tsx` | Codigo morto no repositorio. | `app/landing-layout-backup.tsx` | 0.5h |
| FE-M08 | Sem middleware de auth guards (flash de conteudo desprotegido) | Paginas protegidas checam auth client-side. Flash de conteudo possivel. | Todas paginas protegidas | 4-6h |
| FE-M09 | `performance.timing` deprecated | API deprecated usada em AnalyticsProvider. | `app/components/AnalyticsProvider.tsx:53` | 1h |

#### 4.4 LOW

| ID | Debito | Descricao | Arquivo(s) | Esforco Est. |
|----|--------|-----------|------------|-------------|
| FE-L01 | SVG icons nao componentizados (aria-label generico "Icone") | Muitos SVGs com `aria-label="Icone"` generico, nao descritivo. | Multiplas paginas | 3-4h |
| FE-L02 | useEffect com dependencia Set serializada | Set serializado como string de dependencia em useEffect. | `app/buscar/page.tsx:426` | 1h |
| FE-L03 | Precos de planos divergentes entre paginas | Valores 149/349/997 vs 297/597/1497 em diferentes paginas. | `pricing/page.tsx`, `lib/plans.ts` | 2h |
| FE-L04 | Barrel file nao utilizado `components/filters/index.ts` | Export barrel file vazio/nao utilizado. | `components/filters/index.ts` | 0.5h |
| FE-L05 | Sem robots.txt ou sitemap | SEO basico faltando. | N/A | 2-3h |
| FE-L06 | Sem OpenGraph images configuradas | Compartilhamento social sem preview de imagem. | `app/layout.tsx` | 2-3h |
| FE-L07 | Cobertura de testes ~49.46% vs threshold 60% (70 falhas pre-existentes) | CI coverage gate falha. | `__tests__/` | 12-16h |

**Acessibilidade (observacoes adicionais do audit):**
- `aria-live` regions faltando para atualizacoes dinamicas (resultados de busca, progresso)
- `aria-expanded` faltando em paineis de filtro colapsaveis
- `aria-describedby` faltando ligando campos de formulario a mensagens de erro de validacao
- Sem roving tabindex para grid de 27 estados UF
- Custom dropdowns podem nao implementar pattern ARIA listbox completo
- Framer-motion pode nao respeitar `prefers-reduced-motion`
- Sem `next/dynamic` para componentes pesados (EnhancedLoadingProgress, UpgradeModal, secoes framer-motion)

**Subtotal Frontend:** 25 debitos | Esforco: ~85-120h

---

### 5. Debitos Cross-Cutting (Afetam multiplas areas)

| ID | Debito | Areas | Severidade | Descricao | Esforco Est. |
|----|--------|-------|-----------|-----------|-------------|
| CROSS-C01 | Dual ORM afetando DB + Backend | Database, Backend | CRITICAL | O `database.py` constroi URL PostgreSQL incorretamente a partir de `SUPABASE_URL` (HTTPS), afetando o handler de Stripe webhooks que usa SQLAlchemy. O restante do codigo usa Supabase client. Duas estrategias de transacao, dois pools de conexao, schema drift entre SQL migrations e SQLAlchemy models. **Debito mais impactante do sistema.** | 12-16h |
| CROSS-C02 | Excel storage em filesystem temporario | Backend, Frontend | CRITICAL | Backend gera Excel (base64 em resposta JSON). Frontend proxy salva em `tmpdir()` com setTimeout cleanup. Nao compartilhado entre instancias. Nao persiste em restart. Afeta tanto a rota de API proxy (`/api/buscar/route.ts`) quanto a rota de download (`/api/download/route.ts`). | 8-12h |
| CROSS-H01 | Padroes de API inconsistentes entre frontend e backend | Frontend, Backend | HIGH | Frontend mistura proxy routes (`/api/*`) com chamadas diretas a `NEXT_PUBLIC_BACKEND_URL`. Dois padroes de forwarding de auth. URL do backend exposta ao client. Afeta: `historico`, `conta`, `admin`, `mensagens`. | 8-12h |
| CROSS-M01 | Dados de plano hardcoded em multiplos lugares | Database, Backend, Frontend | MEDIUM | Capacidades de plano em `quota.py:62-95` (Python), precos em `plans` table (DB), precos em `pricing/page.tsx` e `lib/plans.ts` (frontend). Valores divergentes (149/349/997 vs 297/597/1497). Sem single source of truth acessivel a todos. | 6-8h |
| CROSS-M02 | Falhas de testes pre-existentes mascaram regressoes | Backend, Frontend, CI/CD | MEDIUM | Backend: 21 falhas pre-existentes (billing, stripe, feature flags, prorata). Frontend: 70 falhas pre-existentes. CI pipeline nao e verde, quality gates nao funcionais. Novas regressoes ficam invisíveis. | 16-24h |

**Subtotal Cross-Cutting:** 5 debitos | Esforco: ~50-72h

---

### 6. Matriz Preliminar de Priorizacao

| ID | Debito | Area | Severidade | Impacto | Esforco Est. | Prioridade |
|----|--------|------|-----------|---------|-------------|-----------|
| DB-C01 | `database.py` URL PostgreSQL incorreta | DB | CRITICAL | Stripe webhooks podem falhar silenciosamente | 2-3h | **P0** |
| DB-C02 | `user_subscriptions` sem policy RLS service role | DB | CRITICAL | Gestao de subscriptions pode quebrar | 1-2h | **P0** |
| DB-C03 | `stripe_webhook_events` admin check incorreto | DB | CRITICAL | Controle de acesso incorreto | 1h | **P0** |
| FE-C02 | Fallback localhost em analytics route | FE | CRITICAL | Leak de dados em producao | 1h | **P0** |
| CROSS-C01 | Dual ORM (Supabase + SQLAlchemy) | Cross | CRITICAL | Schema drift, transacoes inconsistentes | 12-16h | **P0** |
| SYS-C04 | Falhas pre-existentes de testes | SYS | CRITICAL | CI nao funcional | 8-16h | **P1** |
| SYS-C02 | Monolito main.py (1.959 linhas) | SYS | CRITICAL | Manutencao e testes dificeis | 12-16h | **P1** |
| FE-C01 | Pagina buscar monolitica (~1100 linhas) | FE | CRITICAL | Manutencao e testes dificeis | 16-24h | **P1** |
| SYS-C01 | In-memory state (SSE progress) | SYS | CRITICAL | Impede escalabilidade | 16-24h | **P1** |
| CROSS-C02 | Excel em filesystem temporario | Cross | CRITICAL | Impede escalabilidade, dados perdidos | 8-12h | **P1** |
| FE-C03 | Padroes mistos de API | FE | CRITICAL | Seguranca e manutencao | 8-12h | **P1** |
| DB-H01 | Dual ORM architecture | DB | HIGH | Complexidade operacional | 8-12h | **P1** |
| DB-H02 | Migration 006 duplicada | DB | HIGH | Ambiguidade de estado | 2-3h | **P1** |
| DB-H03 | Index faltando stripe_subscription_id | DB | HIGH | Performance de webhook | 1h | **P1** |
| DB-H04 | Policies RLS overly permissive | DB | HIGH | Seguranca | 1-2h | **P1** |
| DB-H05 | profiles sem INSERT policy | DB | HIGH | Modelo de seguranca incompleto | 1h | **P1** |
| SYS-H01 | Cliente PNCP sincrono em async | SYS | HIGH | Bloqueia event loop | 4-6h | **P1** |
| SYS-H04 | Logica de negocio em helpers main.py | SYS | HIGH | Testabilidade | 4-6h | **P1** |
| SYS-H05 | Dev deps em producao requirements | SYS | HIGH | Seguranca, tamanho imagem | 2-3h | **P1** |
| FE-H01 | Componentes de filtro duplicados | FE | HIGH | Manutencao | 3-4h | **P1** |
| FE-H03 | Error boundary sem design system | FE | HIGH | Dark mode quebrado | 1-2h | **P1** |
| FE-H04 | alert() nativo em vez de toast | FE | HIGH | UX inconsistente | 1h | **P1** |
| CROSS-H01 | Padroes API inconsistentes | Cross | HIGH | Seguranca e manutencao | 8-12h | **P1** |
| SYS-H02 | Excel em filesystem temp | SYS | HIGH | Escalabilidade | 6-8h | **P2** |
| SYS-H03 | Migrations nao trackeadas | SYS | HIGH | Drift de ambiente | 4-6h | **P2** |
| FE-H02 | DOM manipulation direta | FE | HIGH | Anti-pattern React | 2-3h | **P2** |
| FE-H05 | UF_NAMES duplicado | FE | HIGH | Manutencao | 1-2h | **P2** |
| FE-H06 | Excel tmpdir() | FE | HIGH | Escalabilidade | 6-8h | **P2** |
| DB-M01 | FKs inconsistentes | DB | MEDIUM | Integridade | 3-4h | **P2** |
| DB-M02 | Legacy plan types em CHECK | DB | MEDIUM | Integridade dados | 2-3h | **P2** |
| DB-M03 | updated_at faltando em migration | DB | MEDIUM | Schema inconsistente | 1-2h | **P2** |
| DB-M04 | plan_type drift | DB | MEDIUM | Dados inconsistentes | 4-6h | **P2** |
| DB-M05 | Stripe IDs hardcoded em migration | DB | MEDIUM | DevOps | 2-3h | **P2** |
| DB-M06 | N+1 query conversas | DB | MEDIUM | Performance | 3-4h | **P2** |
| DB-M07 | Analytics fetch all | DB | MEDIUM | Performance | 3-4h | **P2** |
| SYS-M01 | Sem correlation ID | SYS | MEDIUM | Observabilidade | 3-4h | **P2** |
| SYS-M02 | Token cache hash inseguro | SYS | MEDIUM | Seguranca | 2-3h | **P2** |
| SYS-M03 | Rate limiter sem max size | SYS | MEDIUM | Memory leak | 2-3h | **P2** |
| SYS-M04 | Plan capabilities hardcoded | SYS | MEDIUM | Flexibilidade | 4-6h | **P2** |
| SYS-M06 | datetime.utcnow() deprecated | SYS | MEDIUM | Deprecacao | 2-3h | **P2** |
| SYS-M07 | Frontend coverage < 60% | SYS | MEDIUM | Qualidade | 8-12h | **P2** |
| SYS-M08 | Sem versionamento API | SYS | MEDIUM | Evolucao | 4-6h | **P2** |
| FE-M01 | Sem app shell compartilhado | FE | MEDIUM | UX consistencia | 6-8h | **P2** |
| FE-M03 | Sem form validation library | FE | MEDIUM | DX e UX | 8-12h | **P2** |
| FE-M08 | Sem middleware auth guards | FE | MEDIUM | Flash de conteudo | 4-6h | **P2** |
| CROSS-M01 | Dados de plano hardcoded everywhere | Cross | MEDIUM | Consistencia | 6-8h | **P2** |
| CROSS-M02 | Falhas de teste mascaram regressoes | Cross | MEDIUM | Qualidade | 16-24h | **P2** |
| SYS-M05 | Google API credentials | SYS | MEDIUM | Seguranca | 2-3h | **P3** |
| FE-M02 | Feature flags subutilizados | FE | MEDIUM | Flexibilidade | 2-3h | **P3** |
| FE-M04 | STOPWORDS_PT duplicada | FE | MEDIUM | Manutencao | 1-2h | **P3** |
| FE-M05 | SETORES_FALLBACK sync manual | FE | MEDIUM | Manutencao | 1h | **P3** |
| FE-M06 | Arquivo stale dashboard-old | FE | MEDIUM | Limpeza | 0.5h | **P3** |
| FE-M07 | Arquivo stale landing-layout-backup | FE | MEDIUM | Limpeza | 0.5h | **P3** |
| FE-M09 | performance.timing deprecated | FE | MEDIUM | Deprecacao | 1h | **P3** |
| DB-L01 | plans sem updated_at | DB | LOW | Auditoria | 1h | **P3** |
| DB-L02 | Sem cleanup monthly_quota | DB | LOW | Manutencao | 3-4h | **P3** |
| DB-L03 | Sem cleanup webhook_events | DB | LOW | Manutencao | 3-4h | **P3** |
| DB-L04 | Index redundante oauth provider | DB | LOW | Performance | 0.5h | **P3** |
| SYS-L01 | Sem OpenAPI schema validation | SYS | LOW | Contratos | 4-6h | **P3** |
| SYS-L02 | Emoji em logs | SYS | LOW | Operacoes | 1h | **P3** |
| SYS-L03 | CSS inline layout.tsx | SYS | LOW | Padrao | 1-2h | **P3** |
| SYS-L04 | Sem request logging middleware | SYS | LOW | Observabilidade | 3-4h | **P3** |
| SYS-L05 | Imports nao utilizados | SYS | LOW | Limpeza | 0.5h | **P3** |
| SYS-L06 | Sem health check Redis | SYS | LOW | Operacoes | 2h | **P3** |
| FE-L01 | SVGs sem aria-label descritivo | FE | LOW | Acessibilidade | 3-4h | **P3** |
| FE-L02 | useEffect com Set serializado | FE | LOW | Correctness | 1h | **P3** |
| FE-L03 | Precos divergentes entre paginas | FE | LOW | Consistencia | 2h | **P3** |
| FE-L04 | Barrel file nao utilizado | FE | LOW | Limpeza | 0.5h | **P3** |
| FE-L05 | Sem robots.txt/sitemap | FE | LOW | SEO | 2-3h | **P3** |
| FE-L06 | Sem OpenGraph images | FE | LOW | Marketing | 2-3h | **P3** |
| FE-L07 | Cobertura testes < threshold | FE | LOW | Qualidade | 12-16h | **P3** |

---

### 7. Dependencias Entre Debitos

```
Cadeia 1: Consolidacao ORM (Pre-requisito para tudo de DB)
  CROSS-C01 (Dual ORM) --must-precede-->
    DB-C01 (database.py URL incorreta) --must-precede-->
      DB-H01 (Consolidar ORM) --must-precede-->
        DB-H03 (Index stripe_subscription_id)

Cadeia 2: Decomposicao de Monolitos (Melhoria de manutencao)
  SYS-C02 (main.py 1959 linhas) --must-precede-->
    SYS-H04 (Logica de negocio em helpers)
    SYS-M01 (Correlation IDs -- mais facil apos decomposicao)
    SYS-L04 (Request logging middleware)
  FE-C01 (buscar 1100 linhas) --must-precede-->
    FE-H01 (Componentes duplicados -- consolidar durante decomposicao)
    FE-H02 (DOM manipulation -- refatorar durante decomposicao)
    FE-H05 (UF_NAMES duplicado -- extrair durante decomposicao)
    FE-M03 (Form validation library -- integrar durante decomposicao)

Cadeia 3: Escalabilidade Horizontal (Pre-requisito para multi-instance)
  SYS-C01 (In-memory SSE state) --must-precede-->
    CROSS-C02 (Excel em tmpdir) --must-precede-->
      SYS-H02 (Object storage para Excel)

Cadeia 4: CI/CD Verde (Pre-requisito para deploys seguros)
  SYS-C04 (Fix pre-existing test failures) --must-precede-->
    SYS-M07 (Frontend coverage < 60%) --must-precede-->
      SYS-L01 (OpenAPI schema validation)

Cadeia 5: Seguranca RLS (Pode ser feita em paralelo)
  DB-C02 (user_subscriptions RLS) --parallel-->
  DB-C03 (stripe_webhook_events admin check) --parallel-->
  DB-H04 (Overly permissive policies) --parallel-->
  DB-H05 (profiles INSERT policy)

Cadeia 6: API Pattern Unification
  FE-C03 (Mixed API patterns) --must-precede-->
    FE-C02 (localhost fallback) -- fix during unification
    CROSS-H01 (Inconsistent patterns) -- resolved by unification
    FE-M01 (Shared app shell) -- easier after unified patterns
    FE-M08 (Middleware auth guards) -- natural companion
```

---

### 8. Perguntas para Especialistas

#### Para @data-engineer (Dara):

1. **DB-C01 (database.py URL):** Confirmacao -- a conexao SQLAlchemy esta realmente falhando em producao, ou existe um `DATABASE_URL` env var nao documentado que a resolve? Se esta falhando, como os Stripe webhooks estao processando pagamentos?

2. **DB-C02 (user_subscriptions RLS):** O service role key do Supabase realmente bypassa RLS por default. Voce considera que a policy explicita e necessaria agora, ou e apenas uma medida preventiva para caso o comportamento mude?

3. **DB-M01 (FK inconsistentes):** Qual seria o esforco real de migrar as 3 tabelas (`monthly_quota`, `user_oauth_tokens`, `google_sheets_exports`) para FK em `profiles(id)` sem downtime? Ha risco de dados orfaos?

4. **DB-H02 (Migration 006 duplicada):** Voce pode verificar no dashboard Supabase qual versao da migration 006 esta realmente aplicada em producao? Isso determinaria se precisamos de uma migration corretiva.

5. **DB-M04 (plan_type drift):** O fallback de 4 camadas em `quota.py` e robusto o suficiente, ou deveriamos implementar um trigger PostgreSQL que sincroniza `profiles.plan_type` automaticamente quando `user_subscriptions` muda?

6. **DB-M06/M07 (N+1 e analytics):** Voce tem dados de producao sobre o tamanho tipico dessas queries? Quantas conversas e sessions o usuario medio tem? Isso ajudaria a priorizar.

7. **Retencao (DB-L02, DB-L03):** Qual seria a estrategia de retencao recomendada? pg_cron job? Supabase Edge Function agendada? Application-level cleanup?

#### Para @ux-design-expert (Uma):

1. **FE-C01 (buscar monolito):** Na sua analise, voce sugeriu decomposicao em SearchForm, FilterPanel, SearchResults, useSearch, useSearchFilters. Essa decomposicao manteria a UX atual intacta, ou voce prevê mudancas na experiencia do usuario durante a refatoracao?

2. **FE-C03 (Mixed API patterns):** Qual e o impacto perceptivel ao usuario de unificar os padroes de API? Haveria ganho de performance perceptivel ou e apenas uma melhoria de manutencao?

3. **FE-H01 (Componentes duplicados):** Qual versao dos componentes duplicados (EsferaFilter, MunicipioFilter) e a "correta" -- a de `app/components/` ou `components/`? Ha diferencas de funcionalidade entre elas?

4. **Acessibilidade ARIA:** Das 6 issues de acessibilidade identificadas (aria-live, aria-expanded, aria-describedby, roving tabindex, ARIA listbox, prefers-reduced-motion), quais voce priorizaria para a proxima sprint?

5. **FE-M01 (Shared app shell):** Voce tem um wireframe ou spec para como o app shell compartilhado deveria parecer? Sidebar + top nav? Apenas top nav consistente?

6. **FE-L03 (Precos divergentes):** Quais sao os precos CORRETOS? 297/597/1497 (da tabela de planos do backend) ou 149/349/997 (da pagina de pricing)? Isso precisa ser reconciliado com o time de produto.

7. **FE-M03 (Form validation):** Voce recomenda zod + react-hook-form como a combinacao padrao? Ou ha uma alternativa que se integre melhor com o design system existente?

8. **Performance:** O `framer-motion` (40KB gzipped) e usado apenas no landing page. Vale a pena implementar dynamic import para ele, ou o impacto e aceitavel dado que o landing nao e a pagina principal dos usuarios logados?

#### Para @qa:

1. **Testes pre-existentes (SYS-C04):** Das 21 falhas backend e 70 falhas frontend, qual proporcao sao testes que precisam ser corrigidos vs testes que devem ser removidos/reescritos?

2. **Coverage gaps:** A cobertura frontend esta em 49.46% (vs threshold 60%). Quais componentes deveriam ser priorizados para testes -- os mencionados (LoadingProgress, RegionSelector, SavedSearchesDropdown, AnalyticsProvider) ou ha outros mais criticos?

3. **Risk assessment:** Dado que o sistema esta em producao com usuarios reais e processando pagamentos via Stripe, quais areas do codigo voce considera de maior risco para regressoes?

4. **E2E testing:** Os 60 testes E2E Playwright cobrem os fluxos criticos. Ha gaps nos cenarios de billing/Stripe checkout que deveriam ser cobertos?

5. **Performance testing:** O Locust esta nas dependencias mas nao ha testes configurados. Deveriamos priorizar load testing dado que o backend tem rate limiting e retries para a PNCP API?

6. **Security testing:** Considerando os gaps de RLS identificados (DB-C02, DB-C03, DB-H04), voce recomenda testes automatizados de seguranca (SQL injection, privilege escalation) como parte do CI?

7. **Migration testing:** Com a situacao das migrations duplicadas (DB-H02) e migrations manuais, como podemos garantir que o schema esta consistente entre ambientes?

---

### 9. Observacoes Positivas (Preservar)

Estas qualidades foram destacadas pelos especialistas e devem ser preservadas durante a resolucao de debitos:

**Arquitetura/Backend:**
1. Retry com exponential backoff e jitter no cliente PNCP
2. Parallel UF fetching com asyncio.Semaphore (10 concurrent)
3. Fail-fast sequential filtering (cheapest filters first)
4. LLM Arbiter pattern (auto-accept/reject + LLM for medium confidence)
5. Feature flags runtime-configurables via env vars
6. Multi-layer subscription fallback (4 camadas, "fail to last known plan")
7. Log sanitization completa (PII masking)
8. Stripe webhook idempotency

**Database:**
9. Atomic quota increment functions (race condition prevention)
10. RLS habilitado em 100% das tabelas
11. Partial indexes para queries comuns (`is_active`, `is_admin`, unread messages)
12. GIN index para JSONB queries
13. Token encryption at rest (AES-256 Fernet)
14. Migrations com blocos de validacao e documentacao inline

**Frontend:**
15. Design system completo com CSS custom properties (WCAG contrast documented)
16. Dark mode full com flash prevention
17. EmptyState component informativo e acionavel
18. SSE progress tracking com fallback de simulacao
19. Keyboard shortcuts (Ctrl+K, Ctrl+A, Escape)
20. Skip navigation link (WCAG 2.4.1)
21. Focus-visible outlines (WCAG 2.2 Level AAA)
22. Error message translation (technical -> user-friendly Portuguese)
23. Pull-to-refresh mobile

---

### 10. Sequencia Recomendada de Resolucao

#### Sprint 1: Fundacao (Quick wins de seguranca + CI verde)

**Objetivo:** Corrigir issues de seguranca criticas e restaurar CI pipeline funcional.
**Esforco:** ~20-30h

1. DB-C01: Fix database.py URL (2-3h)
2. DB-C02: Add service role policy user_subscriptions (1-2h)
3. DB-C03: Fix stripe_webhook_events admin check (1h)
4. DB-H04: Tighten overly permissive RLS policies (1-2h)
5. DB-H05: Add profiles INSERT policy (1h)
6. FE-C02: Remove localhost fallback analytics (1h)
7. DB-H02: Consolidate migration 006 (2-3h)
8. DB-H03: Add index stripe_subscription_id (1h)
9. SYS-H05: Split requirements prod/dev (2-3h)
10. FE-H03: Fix error boundary design system (1-2h)
11. FE-H04: Replace alert() with sonner toast (1h)

#### Sprint 2: Consolidacao (Padroes unificados)

**Objetivo:** Eliminar dual ORM, unificar padroes de API.
**Esforco:** ~30-40h

1. CROSS-C01/DB-H01: Consolidar ORM (migrar Stripe webhook para Supabase client) (12-16h)
2. FE-C03/CROSS-H01: Unificar padroes de API (todas chamadas via proxy /api/*) (8-12h)
3. FE-H01: Consolidar componentes duplicados (3-4h)
4. FE-H05: Extrair UF_NAMES para modulo compartilhado (1-2h)
5. SYS-C04: Fix/skip pre-existing test failures (8-16h)

#### Sprint 3: Decomposicao (Monolitos -> modulos)

**Objetivo:** Melhorar manutencao decomondo os dois maiores arquivos.
**Esforco:** ~30-45h

1. SYS-C02: Extrair main.py em router modules (search, auth, billing, sessions, authorization) (12-16h)
2. FE-C01: Decompor buscar/page.tsx (SearchForm, FilterPanel, SearchResults, useSearch, useSearchFilters) (16-24h)
3. SYS-H04: Extrair logica de autorizacao para authorization.py (incluso no item 1)
4. SYS-M01: Adicionar correlation IDs (3-4h)

#### Sprint 4: Escalabilidade (Pre-requisitos para multi-instance)

**Objetivo:** Remover barreiras para escalabilidade horizontal.
**Esforco:** ~30-40h

1. SYS-C01: Migrar SSE state para Redis pub/sub (16-24h)
2. CROSS-C02/SYS-H02/FE-H06: Object storage para Excel (Supabase Storage ou S3) (8-12h)
3. SYS-H01: Remover/refatorar PNCPClient sincrono (4-6h)

#### Backlog: Melhorias Continuas

- DB-M01 a DB-M07: Database cleanup e performance
- SYS-M02 a SYS-M08: Backend quality improvements
- FE-M01 a FE-M09: Frontend architecture e UX
- Todos items LOW: Polish e operacoes

---

### 11. Status do DRAFT

**Completude:** 95%

- Documentado: System architecture (23 debitos)
- Documentado: Database schema + audit (19 debitos)
- Documentado: Frontend/UX spec (25 debitos)
- Documentado: Cross-cutting concerns (5 debitos)
- Documentado: Dependencias entre debitos
- Documentado: Priorizacao (72 items)
- Documentado: Sequencia de resolucao (4 sprints + backlog)
- Documentado: Perguntas para especialistas

**PENDENTE REVISAO:**
- @data-engineer (Dara): Validar Secao 3, responder perguntas Secao 8
- @ux-design-expert (Uma): Validar Secao 4, responder perguntas Secao 8
- @qa: Responder perguntas de risk assessment Secao 8
- @architect: Revisao final e priorizacao apos feedback dos especialistas

---

*Documento consolidado por @architect (Aria) em 2026-02-11 a partir de analises dos especialistas @architect, @data-engineer, @ux-design-expert. Todos os caminhos de arquivo e numeros de linha referenciam o estado do codigo no commit `808cd05` da branch `main`.*
