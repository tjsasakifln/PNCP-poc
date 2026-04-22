# SmartLic Components Map (para aiox-apex)

Mapa de componentes UI relevantes do SmartLic. Referência rápida para agentes APEX não precisarem escanear todo o frontend.

## Páginas (22 rotas App Router)

| Rota | Arquivo | Tipo | Descrição |
|---|---|---|---|
| `/` | `app/page.tsx` | Server | Landing page |
| `/login`, `/signup` | `app/login/`, `app/signup/` | Client | Auth Supabase |
| `/auth/callback` | `app/auth/callback/route.ts` | API | OAuth callback |
| `/recuperar-senha`, `/redefinir-senha` | `app/recuperar-senha/` etc | Client | Reset password |
| `/onboarding` | `app/onboarding/` | Client | 3-step wizard (Shepherd) |
| `/buscar` | `app/buscar/page.tsx` | Client | **Main search** — SSE + filtros + resultados |
| `/dashboard` | `app/dashboard/` | Client | Analytics (Recharts) |
| `/historico` | `app/historico/` | Client | Search history |
| `/pipeline` | `app/pipeline/` | Client | Kanban (@dnd-kit) |
| `/mensagens` | `app/mensagens/` | Client | Messaging |
| `/conta` | `app/conta/` | Client | Account settings |
| `/planos`, `/planos/obrigado` | `app/planos/` | Mixed | Pricing + thank you |
| `/pricing`, `/features` | `app/pricing/`, `/features/` | Server | Marketing |
| `/ajuda` | `app/ajuda/` | Server | Help center |
| `/admin`, `/admin/cache` | `app/admin/` | Client | Admin dashboards |
| `/termos`, `/privacidade` | `app/termos/`, `/privacidade/` | Server | Legal |

## Componentes `app/buscar/components/` (principais)

### Formulário e controle

- **`SearchForm`** — setor, CNPJ, UFs, modalidade, valor range, date range
- **`FilterPanel`** — filtros avançados (esfera, status, fonte)
- **`UfProgressGrid`** — visual de progresso por UF durante busca (SSE-driven)

### Resultados

- **`SearchResults`** — lista de licitações com cards
- **`LicitacaoCard`** — card individual de edital
- **`SearchResultsPagination`** — paginação client-side

### Resilience (degradação graciosa)

- **`CacheBanner`** — informa se resultado veio de cache
- **`DegradationBanner`** — avisa sobre fontes com falha parcial
- **`PartialResultsPrompt`** — oferece retry após timeout
- **`SourcesUnavailable`** — lista fontes indisponíveis
- **`ErrorDetail`** — modal de erro detalhado

### AI + Quality badges

- **`LlmSourceBadge`** — mostra origem da classificação (keyword/llm_standard/llm_conservative/llm_zero_match/pending_review)
- **`ViabilityBadge`** — score 0-100 com break-down 4-fator
- **`FeedbackButtons`** — 👍/👎 + comentário
- **`ReliabilityBadge`** — indicador de confiabilidade do resultado

### Billing

- **`PlanCard`** — card de plano (Free/Pro/Consultoria)
- **`PlanToggle`** — mensal/semestral/anual
- **`PaymentFailedBanner`** — alert de falha Stripe
- **`CancelSubscriptionModal`** — fluxo de cancelamento

### Loading

- **`EnhancedLoadingProgress`** — progress com fases (conectando, buscando, analisando)
- **`LoadingProgress`** — fallback simpler

## Componentes globais `components/`

- **`Header`** — nav bar (auth-aware)
- **`Sidebar`** — sidebar de app (/buscar, /dashboard, etc)
- **`Footer`** — footer público
- **`Toast`** — notificações (shadcn-like)
- **`Modal`** — primitive para modais

## API Proxies `app/api/`

Todos proxies para backend FastAPI (não expõem credenciais ao client):

- `/api/buscar` → proxy `POST /buscar`
- `/api/buscar-progress/[id]` → proxy SSE
- `/api/download/*` → Excel download signed URL
- `/api/analytics/*` → dashboards data
- `/api/admin/*` → admin endpoints (auth check)
- `/api/user/*`, `/api/plans`, `/api/pipeline`, etc

## Hooks customizados `hooks/` ou `lib/hooks/`

- `useSearchProgress` — gerencia EventSource + fallback polling
- `useAuth` — Supabase session
- `useFeatureFlag` — lê flags (se aplicável)
- `useAnalytics` — Mixpanel wrapper

## Utilitários `lib/`

- `supabase/client.ts`, `supabase/server.ts` — SSR split
- `api.ts` — fetch wrapper com error handling
- `formatters.ts` — BRL, datas, CNPJ masks

## Ao adicionar componente novo

1. Verificar se similar já existe (não duplicar)
2. Posicionar em `app/<rota>/components/` se específico, `components/` se global
3. Usar `shadcn/ui` primitives quando possível (pattern da codebase)
4. Tests em `__tests__/` mirror da estrutura
5. Se client component: `'use client'` no topo. Senão server.
6. Tailwind classes — não CSS modules novos
