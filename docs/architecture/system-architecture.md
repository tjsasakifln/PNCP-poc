# SmartLic Brownfield Architecture Document

## Introduction

Este documento captura o **ESTADO ATUAL** do codebase SmartLic — uma plataforma SaaS B2G (Business-to-Government) de inteligência em licitações públicas — incluindo dívida técnica, workarounds conhecidos, padrões inconsistentes e restrições de integração. Serve como referência para agentes AI trabalhando em aprimoramentos e para a fase de Planning (Epic/Stories) do workflow brownfield-discovery.

**NÃO é um documento arquitetural aspiracional.** É um retrato honesto do sistema em produção em https://smartlic.tech.

### Document Scope

Auditoria compreensiva do sistema inteiro (sem filtro de PRD). Cobertura:

- Backend (FastAPI 0.129 + Python 3.12, 65+ módulos)
- Frontend (Next.js 16 + React 18 + TypeScript 5.9, 22 páginas, 243 componentes)
- Database (Supabase PostgreSQL 17, 23 tabelas, 35+ migrations)
- Infraestrutura (Railway, Supabase Cloud, Redis, GitHub Actions)
- Integrações externas (PNCP, PCP v2, ComprasGov v3, OpenAI, Stripe, Resend, Sentry, Mixpanel)

### Change Log

| Date       | Version | Description                                                   | Author       |
|------------|---------|---------------------------------------------------------------|--------------|
| 2026-02-23 | 1.0     | Análise inicial de arquitetura                                | @architect   |
| 2026-04-08 | 1.5     | Atualização pós-GTM-resilience                                | @architect   |
| 2026-04-14 | 2.0     | Rewrite completo via workflow brownfield-discovery (YOLO)     | @architect   |

---

## Quick Reference — Key Files and Entry Points

### Critical Files for Understanding the System

- **Backend Entry**: `backend/main.py` (FastAPI app setup, middleware stack, route registration, SSE endpoints, Sentry init)
- **Frontend Entry**: `frontend/app/layout.tsx` (Next.js App Router root layout, provider hierarchy)
- **Configuration**: `backend/config.py` (feature flags, timeouts, cache TTLs, LLM params), `.env.example` (env vars reference)
- **Core Business Logic**:
  - `backend/search_pipeline.py` — orquestração multi-fonte (PNCP + PCP v2 + ComprasGov v3)
  - `backend/consolidation.py` — dedup priority-based (PNCP=1 > PCP=2 > ComprasGov=3)
  - `backend/filter.py` — density scoring + UF/value/keyword filtering
  - `backend/llm_arbiter.py` — classificação LLM (zero-match + gray zone + arbiter)
  - `backend/viability.py` — análise de 4 fatores (modalidade 30%, timeline 25%, valor 25%, geografia 20%)
- **Ingestion Pipeline (Layer 1)**: `backend/ingestion/` (config, crawler, transformer, loader, checkpoint, scheduler)
- **Datalake Query (Layer 2)**: `backend/datalake_query.py` → `search_datalake` RPC
- **Cache (Layer 3)**: `backend/search_cache.py`, `backend/cache.py`, `backend/redis_client.py`
- **API Routes**: `backend/routes/` (19 módulos, 49 endpoints públicos)
- **Database**: `supabase/migrations/` (35+ SQL files), `backend/migrations/` (7+ Python migrations)
- **Background Jobs**: `backend/job_queue.py` (ARQ WorkerSettings), `backend/cron_jobs.py`
- **Billing**: `backend/services/billing.py`, `backend/webhooks/stripe.py`
- **Observability**: `backend/metrics.py` (Prometheus), `backend/telemetry.py` (OpenTelemetry), Sentry initialized in `main.py`
- **Sectors**: `backend/sectors.py` + `backend/sectors_data.yaml` (15 setores com keywords + exclusões)

### Key Algorithms

- **Density Scoring**: `backend/filter.py` — keyword >5% = "keyword"; 2-5% = "llm_standard"; 1-2% = "llm_conservative"; 0% = "llm_zero_match"
- **LLM Zero-Match Prompt**: `backend/llm_arbiter.py` → `_build_zero_match_prompt()`
- **Content-Hash Dedup**: `backend/ingestion/transformer.py` + `upsert_pncp_raw_bids` RPC
- **Checkpoint Resume**: `backend/ingestion/checkpoint.py`
- **SSE Progress Tracking**: `backend/progress.py` (asyncio.Queue por search_id)
- **SWR Cache Strategy**: `backend/search_cache.py` (fresh 0-6h → stale 6-24h → expired >24h)
- **Phased UF Batching**: `backend/search_pipeline.py` (PNCP_BATCH_SIZE=5, 2s delay)

---

## High Level Architecture

### Technical Summary

SmartLic é uma aplicação web monorepo com separação clara entre **backend (FastAPI/Python)** e **frontend (Next.js/TypeScript)**. O backend segue arquitetura em **3 camadas de dados**: ingestão periódica (ETL → datalake), query pipeline (busca local com fallback live), e cache SWR. Classificação de relevância usa **LLM (GPT-4.1-nano)** como arbiter em 3 modos (standard, conservative, zero-match). Deploy em **Railway** (serviços web + worker + frontend separados) com auto-deploy via GitHub Actions. **Supabase** hospeda PostgreSQL + Auth + RLS. **Redis** serve como cache L1, circuit breaker state e token bucket para rate limiting.

### Actual Tech Stack

| Category         | Technology         | Version     | Notes                                                        |
|------------------|--------------------|-------------|--------------------------------------------------------------|
| **Backend**      |                    |             |                                                              |
| Runtime          | Python             | 3.12        | Railway + Gunicorn + Uvicorn workers                         |
| Framework        | FastAPI            | 0.129       | Async-first, Pydantic v2 contracts                           |
| HTTP Client      | httpx              | 0.28+       | async, connection pooling                                    |
| Job Queue        | ARQ                | 0.26+       | Redis-backed, web+worker via PROCESS_TYPE                    |
| DB Access        | supabase-py        | 2.x         | Service-role para backend; auth.uid() RLS para users         |
| LLM              | openai             | 1.x         | GPT-4.1-nano, ThreadPoolExecutor(max_workers=10)             |
| Billing          | stripe             | 11.x        | Webhooks com signature verification                          |
| Email            | Resend SDK         | custom      | Templates em `backend/templates/emails/`                     |
| Excel            | openpyxl           | 3.x         | Estilização + ARQ background job                             |
| Observability    | prometheus-client  | 0.20+       | `/metrics` endpoint                                          |
|                  | opentelemetry-api  | 1.30+       | HTTP-only (limitado por CRIT-080 SIGSEGV)                    |
|                  | sentry-sdk         | 2.x         | StarletteIntegration desabilitado (CRIT-080)                 |
| **Frontend**     |                    |             |                                                              |
| Framework        | Next.js            | 16.1.6      | App Router, mix RSC com ~88% "use client"                    |
| UI Runtime       | React              | 18.3.1      |                                                              |
| Types            | TypeScript         | 5.9.3       | strict NÃO habilitado (296 `any` types)                      |
| Styling          | Tailwind CSS       | 3.4.19      | 50+ tokens; ~70% adoção (194 hex hardcoded)                  |
| Animations       | Framer Motion      | 12.33       | Não tree-shakeable                                           |
| Charts           | Recharts           | 3.7         | 10-color palette                                             |
| Drag-Drop        | @dnd-kit/core      | 6.3.1       | /pipeline kanban; SEM keyboard nav                           |
| Onboarding       | Shepherd.js        | 14.5.1      | HTML hardcoded (screen reader issue)                         |
| Forms            | react-hook-form    | 7.71.2      | + Zod 4.3.6                                                  |
| Auth             | @supabase/ssr      | 0.8.0       | Server Components compatible                                 |
| Data Fetching    | SWR                | 2.4.1       |                                                              |
| Toasts           | Sonner             | 2.0.7       |                                                              |
| Analytics        | Mixpanel/Sentry/GA4| 2.74/10.38  |                                                              |
| Icons            | lucide-react       | 0.563.0     |                                                              |
| **Database**     |                    |             |                                                              |
| Engine           | PostgreSQL         | 17          | Supabase Cloud (project ref `fqqyovlzdzimiwfofdjk`)          |
| Auth             | Supabase Auth      | -           | JWT, RLS em todas tabelas user-data                          |
| FTS              | tsvector           | Portuguese  | GIN index em `pncp_raw_bids.tsv`                             |
| Extensions       | pg_cron, pg_trgm   | -           | Cron para purge/retention                                    |
| **Cache/Queue**  |                    |             |                                                              |
| Cache/Broker     | Redis              | 7.x         | Upstash/Railway; L1 + circuit breaker + ARQ                  |
| **Infra**        |                    |             |                                                              |
| Hosting          | Railway            | -           | Web + Worker + Frontend (serviços separados)                 |
| CI/CD            | GitHub Actions     | -           | migration-gate.yml, deploy.yml, test workflows               |
| Container        | Docker             | -           | `backend/Dockerfile`, `frontend/Dockerfile`                  |

### Repository Structure Reality Check

- **Type**: Monorepo (backend + frontend + supabase + docs)
- **Package Managers**: `npm` (frontend), `pip`/`requirements.txt` (backend)
- **Notable Decisions**:
  - Não usa Turborepo/Nx — separação por Railway service roots (`RAILWAY_SERVICE_ROOT_DIRECTORY=backend|frontend`)
  - `.railwayignore` exclui docs/data/scripts para reduzir upload
  - Cada serviço Railway tem seu próprio `railway.toml` + `Dockerfile`

---

## Source Tree and Module Organization

### Project Structure (Actual)

```text
PNCP-poc/
├── backend/                   # FastAPI app (Python 3.12)
│   ├── main.py                # Entry: middleware, routes, SSE, lifespan
│   ├── config.py              # Feature flags + env parsing
│   ├── schemas.py             # Pydantic contracts (API I/O)
│   ├── search_pipeline.py     # Orquestração multi-fonte
│   ├── consolidation.py       # Dedup priority-based
│   ├── search_context.py      # Context holder (request-scoped)
│   ├── search_state_manager.py# State machine (pending/running/done/failed)
│   ├── filter.py              # Keyword density + UF/value filter
│   ├── filter_stats.py        # Agregação de stats de filtragem
│   ├── term_parser.py         # Parse de termos (AND/OR/quotes)
│   ├── synonyms.py            # Expansão de sinônimos
│   ├── status_inference.py    # Inferência de status (aberto/encerrado)
│   ├── llm.py                 # OpenAI wrapper + resumos
│   ├── llm_arbiter.py         # Zero-match + gray zone classification
│   ├── relevance.py           # Score de relevância final
│   ├── viability.py           # 4-fator viability assessment
│   ├── search_cache.py        # L1+L2 cache SWR
│   ├── cache.py               # InMemoryCache primitive
│   ├── redis_client.py        # Redis async wrapper
│   ├── redis_pool.py          # Connection pool
│   ├── pncp_client.py         # Cliente PNCP (prioridade 1)
│   ├── portal_compras_client.py # Cliente PCP v2 (prioridade 2)
│   ├── compras_gov_client.py  # Cliente ComprasGov v3 (prioridade 3)
│   ├── clients/               # 4+ clients auxiliares
│   ├── datalake_query.py      # RPC wrapper search_datalake
│   ├── ingestion/             # ETL Layer 1
│   ├── auth.py, authorization.py, oauth.py, quota.py
│   ├── routes/                # 19 modules, 49 endpoints
│   ├── services/billing.py    # Stripe service layer
│   ├── webhooks/stripe.py     # Signature-verified handlers
│   ├── job_queue.py           # ARQ WorkerSettings
│   ├── cron_jobs.py           # Cron handlers
│   ├── metrics.py, telemetry.py, health.py, audit.py, progress.py
│   ├── email_service.py       # Resend wrapper
│   ├── feedback_analyzer.py   # Bi-gram pattern analysis
│   ├── excel.py, google_sheets.py, report_generator.py
│   ├── sectors.py, sectors_data.yaml # 15 setores
│   ├── log_sanitizer.py       # PII redaction
│   ├── templates/emails/      # HTML email templates
│   ├── migrations/            # Python-based migrations (7+)
│   ├── tests/                 # 169 test files, 5131+ passing
│   └── requirements.txt
├── frontend/                  # Next.js 16 (App Router)
│   ├── app/
│   │   ├── layout.tsx, globals.css
│   │   ├── (pages 22)/
│   │   ├── buscar/            # Main search page + 20+ components
│   │   ├── pipeline/          # Kanban com @dnd-kit
│   │   ├── admin/             # is_admin/is_master gated
│   │   └── api/               # Route handlers (proxy to backend)
│   ├── components/            # Shared (68)
│   ├── lib/, hooks/
│   ├── __tests__/             # Jest+RTL (135 files, 2681+)
│   ├── e2e-tests/             # Playwright (60 tests)
│   ├── jest.setup.js          # Polyfills (crypto.randomUUID, EventSource)
│   ├── tailwind.config.ts     # 50+ design tokens
│   ├── next.config.js, package.json, tsconfig.json
├── supabase/
│   ├── migrations/            # 35+ SQL (source of truth)
│   └── docs/                  # SCHEMA.md, DB-AUDIT.md
├── docs/
│   ├── architecture/          # ADRs + this document
│   ├── frontend/              # frontend-spec.md
│   ├── prd/                   # technical-debt-DRAFT + assessment
│   ├── reviews/               # Specialist reviews
│   ├── reports/               # TECHNICAL-DEBT-REPORT.md + audits anteriores
│   ├── stories/               # Epics + stories numeradas
│   ├── sessions/, guides/, summaries/
├── .aios-core/, .aiox-core/   # Framework (L1/L2)
├── .claude/                   # CLAUDE.md, rules, commands, settings
├── .github/workflows/         # CI/CD
├── scripts/                   # sync-setores-fallback, etc.
└── CLAUDE.md                  # Project instructions (source of truth)
```

### Key Modules

- **`backend/main.py`**: FastAPI app, CORS, middleware (rate limit, request ID), Sentry init, lifespan (Redis pool, HTTP client, Supabase client), route registration, SSE endpoints.
- **`backend/search_pipeline.py`**: Pipeline de busca com gates por fonte, phased UF batching, timeout chain ARQ Job(300s) > Pipeline(110s) > PerSource(80s) > PerUF(30s).
- **`backend/consolidation.py`**: Dedup baseado em `numeroControlePNCP` + hash de objeto; merge priority-based (PNCP=1 > PCP=2 > ComprasGov=3).
- **`backend/filter.py`**: Density scoring — keyword/llm_standard/llm_conservative/llm_zero_match.
- **`backend/llm_arbiter.py`**: Monta prompts, chama OpenAI, classifica YES/NO com fallback `PENDING_REVIEW` quando `LLM_FALLBACK_PENDING_ENABLED=true`.
- **`backend/ingestion/`**: ARQ cron — full daily 5 UTC (2am BRT), incremental 11/17/23 UTC, purge 7 UTC. Escopo: 27 UFs × 6 modalidades, 10-day window full, 3-day incremental. Concurrency 5 UFs paralelas, 2s delay, max 50 pages/UF/modalidade.
- **`backend/search_cache.py`**: L1 InMemoryCache (4h, hot/warm/cold) + L2 Supabase `search_results_cache` (24h). SWR: serve stale + revalidate background (max 3 concurrent, 180s timeout).
- **`backend/job_queue.py`**: ARQ WorkerSettings — LLM summaries + Excel generation como background jobs; resposta imediata com fallback summary.
- **`frontend/app/buscar/`**: Página principal — filtros, SSE progress, resultados paginados, degradation banners.
- **`frontend/hooks/useSearchOrchestration`**: Gerencia POST /buscar → SSE + polling fallback → render results.

---

## Data Architecture (3 Layers)

### Layer 1 — Periodic Ingestion (ETL → `pncp_raw_bids`)

- **Cron jobs (ARQ)**: full daily 5 UTC, incremental 11/17/23 UTC, purge 7 UTC.
- **Tabela**: `pncp_raw_bids` (~40K-100K rows), GIN FTS em `tsv` (pre-computed, DEBT-210), content_hash dedup, 12-day retention (soft-delete `is_active=false`).
- **Config**: `backend/ingestion/config.py`.
- **Checkpoints**: `ingestion_checkpoints` (resumable) + `ingestion_runs` (audit).
- **Feature flag**: `DATALAKE_ENABLED` (default `true`).
- **Loader**: `upsert_pncp_raw_bids(p_records JSONB)` RPC — batch 500 rows, DISTINCT ON dedup intra-batch, INSERT ON CONFLICT com WHERE por content_hash.

### Layer 2 — Search Pipeline (queries local DB, fallback live)

- **Default**: `DATALAKE_QUERY_ENABLED=true` → `datalake_query.py` chama `search_datalake` RPC (tsquery Portuguese + filtros UF/data/modalidade/valor/esfera).
- **Fallback**: Se datalake 0 results, live multi-source fetch (PNCP + PCP v2 + ComprasGov v3).
- **Async-first (CRIT-072)**: `POST /buscar` → 202 em <2s → resultados via SSE + polling.
- **SSE chain**: `bodyTimeout(0)` + heartbeat 15s > Railway idle 60s | SSE inactivity timeout 120s.

### Layer 3 — Search Results Cache (SWR)

- **L1 — InMemoryCache**: 4h TTL, hot/warm/cold priority, por processo Gunicorn (NÃO shared — TD-SYS-010).
- **L2 — Supabase `search_results_cache`**: 24h TTL, persistente, cleanup trigger max 5/user.
- **SWR states**: fresh (0-6h) → stale (6-24h, served + background refresh) → expired (>24h, não served).

### Legacy Fallback — Live API Fetch

Apenas quando `DATALAKE_QUERY_ENABLED=false` ou datalake 0:

- `pncp_client.py` / `portal_compras_client.py` / `compras_gov_client.py`
- Per-source circuit breakers (15 failures threshold, 60s cooldown)
- Priority-based dedup, phased UF batching
- Timeout chain: ARQ Job(300s) > Pipeline(110s) > Consolidation(100s) > PerSource(80s) > PerUF(30s)

---

## Data Models and APIs

### Core Data Models

Schemas Pydantic em `backend/schemas.py`:

- **`SearchRequest`** — filtros de entrada (sectors, ufs, date range, custom_keywords, valor_min/max)
- **`SearchResponse`** — payload SSE/JSON (search_id, status, progress, items, sources_status)
- **`LicitacaoItem`** — representação unificada de um edital (cross-source)
- **`ViabilityAssessment`** — 4 fatores + score final
- **`ClassificationResult`** — source, confidence, reasoning

Tabelas DB (ver `supabase/docs/SCHEMA.md` para detalhes): `profiles`, `plans`, `user_subscriptions`, `search_sessions`, `monthly_quota`, `stripe_webhook_events`, `conversations`, `messages`, `alert_preferences`, `alerts`, `alert_sent_items`, `health_checks`, `incidents`, `organizations`, `organization_members`, `pipeline_items`, `search_results_cache`, `search_results_store`, `pncp_raw_bids`, `ingestion_checkpoints`, `ingestion_runs`, `audit_events`, `partner_referrals`, `classification_feedback`.

### API Specifications

49 endpoints públicos em 19 módulos de `backend/routes/`:

| Module            | Key Endpoints                                                                                      |
|-------------------|----------------------------------------------------------------------------------------------------|
| `search.py`       | `POST /buscar`, `GET /buscar-progress/{id}` (SSE), `GET /v1/search/{id}/status`, `POST /v1/search/{id}/retry` |
| `pipeline.py`     | `POST/GET/PATCH/DELETE /pipeline`, `GET /pipeline/alerts`                                          |
| `billing.py`      | `GET /plans`, `POST /checkout`, `POST /billing-portal`, `GET /subscription/status`                 |
| `user.py`         | `GET /me`, `POST /change-password`, `GET /trial-status`, `PUT/GET /profile/context`                |
| `analytics.py`    | `GET /summary`, `GET /searches-over-time`, `GET /top-dimensions`, `GET /trial-value`               |
| `feedback.py`     | `POST/DELETE /feedback`, `GET /admin/feedback/patterns`                                            |
| `messages.py`     | `POST/GET /conversations`, `POST /{id}/reply`, `PATCH /{id}/status`                                |
| `auth_oauth.py`   | `GET /google`, `GET /google/callback`, `DELETE /google`                                            |
| `admin_trace.py`  | `GET /search-trace/{search_id}`                                                                    |
| Outros            | plans, exports, features, subscriptions, emails, onboarding, sessions, health, stats_public        |

---

## Technical Debt and Known Issues

### CRITICAL

#### TD-SYS-001 — CRIT-080 SIGSEGV em POST requests

- **Location**: `backend/Dockerfile` (jemalloc LD_PRELOAD), `backend/requirements.txt` (cryptography>=46), `backend/main.py` (Sentry StarletteIntegration)
- **Impact**: POST `/buscar`, `/checkout`, `/feedback` crasham com segfault em TLS handshake. GET requests funcionam.
- **Root cause**: `jemalloc LD_PRELOAD` + `Sentry StarletteIntegration` + `cryptography>=46` interagem mal em worker forking Gunicorn.
- **Current mitigation**: StarletteIntegration desabilitado; uvloop desabilitado; OTEL HTTP-only; Sentry graceful degradation.
- **Emergency deploy**: `railway redeploy --service bidiq-backend -y`.

#### TD-SYS-002 — PNCP API page size limit drop (Feb 2026)

- **Location**: `backend/pncp_client.py`, `backend/ingestion/crawler.py`
- **Impact**: `tamanhoPagina` reduzido de 500 → 50 (>50 retorna HTTP 400 silencioso). 10x mais chamadas.
- **Detection**: Health canary usa `tamanhoPagina=10`, não detecta o limite.
- **Retry**: exponential backoff; HTTP 422 retryable (max 1); circuit breaker 15 fails / 60s cooldown.
- **Mitigation**: Phased UF batching (`PNCP_BATCH_SIZE=5`, `PNCP_BATCH_DELAY_S=2.0`).

#### TD-SYS-003 — Railway hard timeout 120s < Gunicorn 180s

- **Location**: `backend/start.sh`, `backend/gunicorn_conf.py`, CLAUDE.md
- **Impact**: Requests >120s são killed pelo proxy Railway, ignorando Gunicorn timeout.
- **Mitigation**: Time budgets stage-wise (80s execute, 20s filter, 30s LLM); `asyncio.to_thread()` para wraps sync; Gunicorn keep-alive 75s (>Railway 60s) previne 502s intermitentes.

#### TD-SYS-004 — Migrations não aplicadas bloqueiam features (CRIT-039/045/050)

- **Location**: `.github/workflows/migration-gate.yml`, `migration-check.yml`, `deploy.yml`
- **Impact**: Incidentes históricos (ES256 JWT, multipart CVE, PGRST205); features flag habilitadas mas schema ausente.
- **Mitigation (CRIT-050)**: 3 camadas — PR warning, push alert, auto-apply on deploy com `NOTIFY pgrst`.

#### TD-SYS-005 — `search.py` monolítico (1000+ LOC), state distribuído

- **Location**: `backend/routes/search.py`
- **Impact**: Debug difícil, mudanças cascateiam, fragilidade de testes, backward compat constraints.
- **Partial fix**: Decomposição iniciada (`search_sse.py`, `search_state.py`, `search_status.py`), re-exportadas via `search.py`.

### HIGH

#### TD-SYS-010 — In-memory cache não shared entre Gunicorn workers

- **Impact**: Hit ratio L1 baixo em multi-worker. Redis L2 compensa parcialmente.
- **Fix**: Migrar L1 para Redis-backed ou `gunicorn --preload`.

#### TD-SYS-011 — Feature flags em 3 lugares (env vars + Redis + código)

- **Impact**: Valores conflitantes; ordem de avaliação pouco clara.
- **Fix**: Single source of truth (Redis ou DB table) com admin UI.

#### TD-SYS-012 — Setores duplicados (backend YAML + frontend hardcoded)

- **Location**: `backend/sectors_data.yaml` + `frontend/app/buscar/page.tsx` (`SETORES_FALLBACK`)
- **Mitigation**: Script `node scripts/sync-setores-fallback.js` (mensal, manual).
- **Fix**: Expor `/setores` endpoint + consumir em runtime.

#### TD-SYS-013 — Session dedup eventual consistency 6-24h

- **Impact**: Duplicatas na UI; confusão usuário.

#### TD-SYS-014 — LLM concurrency bottleneck

- **Location**: `backend/llm_arbiter.py`
- **Impact**: `ThreadPoolExecutor(max_workers=10)`; max 3 searches concurrent por user; latência 30s+.
- **Fix**: Async OpenAI; Batch API (50% custo); ARQ summaries (parcial).

#### TD-SYS-015 — FTS não otimizado para Português

- **Location**: `backend/datalake_query.py`
- **Fix**: Dicionário customizado `public.portuguese_smartlic`; synonyms agressivos.

#### TD-SYS-016 — `search_results_cache` growth unbounded

- **Location**: `supabase/migrations/026_*`
- **Fix**: pg_cron `DELETE WHERE created_at < now() - interval '24 hours'`.

#### TD-SYS-017 — Rate limit ausente em endpoints públicos

- **Location**: `backend/routes/stats_public.py`, `/setores`, `/planos`
- **Fix**: Token bucket Redis.

#### TD-SYS-018 — LLM sem cap de custo mensal

- **Impact**: Runaway cost se trigger loop.
- **Fix**: Counter Prometheus + budget alert + hard cap.

### MEDIUM

- **TD-SYS-020**: `sectors_data.yaml` sem validação em startup (`backend/sectors.py`)
- **TD-SYS-021**: Feature flags docs inconsistentes (`backend/FEATURE_FLAGS.md`)
- **TD-SYS-022**: Mock location inconsistente em testes (`conftest.py`)
- **TD-SYS-023**: Integration tests flaky (shared state)
- **TD-SYS-024**: `backend/schemas.py` 1500+ LOC monolítico
- **TD-SYS-025**: Logs JSON-vs-text inconsistentes

### LOW

- **TD-SYS-030**: `backend/migrations/` (Python) + `supabase/migrations/` (SQL) coexistem sem doc
- **TD-SYS-031**: Dead code (`backend/legacy/`, ADR-TD004 fragments)
- **TD-SYS-032**: Telemetria spans incompletos (OTEL HTTP-only)

### Workarounds and Gotchas

- **PNCP `tamanhoPagina` max 50** (TD-SYS-002). Health canary não detecta.
- **Railway hard timeout 120s** (TD-SYS-003). Gunicorn 180s ineffective.
- **`LLM_FALLBACK_PENDING_ENABLED`**: true → PENDING_REVIEW, false → REJECT.
- **Deploy Railway**: NUNCA `railway up` de dentro de `backend/` ou `frontend/` — sempre do root; prefira GitHub auto-deploy.
- **Force rebuild**: bump `LABEL build.timestamp` + `ARG CACHEBUST` em `backend/Dockerfile` se skipped.
- **413 Payload Too Large**: use `.railwayignore` ou GitHub auto-deploy.
- **Sync `NOTIFY pgrst, 'reload schema'`**: após `supabase db push --include-all`.
- **Quota tests**: testes mockando `/buscar` DEVEM mockar `check_and_increment_quota_atomic`.
- **ARQ mock**: use conftest `_isolate_arq_module` fixture; nunca raw assignment.
- **pytest-timeout**: 30s default; `@pytest.mark.timeout(60)` para slow integration.
- **Stripe webhooks**: ALL handlers syncam `profiles.plan_type`; "fail to last known plan"; 3-day grace `SUBSCRIPTION_GRACE_DAYS`.
- **CRIT-080 billing diagnose**: `gh api /repos/.../actions/runs` — se status queued & conclusion null → billing issue.

---

## Integration Points and External Dependencies

### External Services

| Service        | Purpose                              | Integration Type           | Key Files                           |
|----------------|--------------------------------------|----------------------------|-------------------------------------|
| PNCP           | Fonte primária (priority 1)          | REST (GET, no auth)        | `backend/pncp_client.py`            |
| PCP v2         | Fonte secundária (priority 2)        | REST (GET, no auth, v2)    | `backend/portal_compras_client.py`  |
| ComprasGov v3  | Fonte terciária (priority 3)         | REST dual-endpoint         | `backend/compras_gov_client.py`     |
| OpenAI         | GPT-4.1-nano classificação + resumos | SDK (openai)               | `backend/llm.py`, `llm_arbiter.py`  |
| Supabase       | DB + Auth + Storage + RLS            | PostgreSQL + REST + JWT    | `backend/supabase_client.py`        |
| Stripe         | Billing, webhooks, portal            | SDK + webhooks             | `backend/services/billing.py`       |
| Resend         | Transactional emails                 | SDK + HTML templates       | `backend/email_service.py`          |
| Sentry         | Error tracking                       | SDK (backend + frontend)   | `backend/main.py`, `frontend/` init |
| Mixpanel       | Analytics frontend                   | JS SDK                     | `frontend/` provider                |
| Google OAuth   | Social login                         | OAuth 2.0 flow             | `backend/oauth.py`                  |

### Internal Integration Points

- **SSE chain**: `POST /buscar` (search_id) → `GET /buscar-progress/{id}` (SSE) → asyncio.Queue tracker → emit events (`progress`, `source_done`, `llm_ready`, `excel_ready`, `done`).
- **ARQ worker/web split**: `PROCESS_TYPE=web` → FastAPI Uvicorn; `PROCESS_TYPE=worker` → `arq backend.job_queue.WorkerSettings`.
- **Supabase RLS**: Todas tabelas user-data; policies `USING (auth.uid() = user_id)` + `WITH CHECK`; service_role bypass para backend writes.
- **Redis circuit breaker**: State distribuído entre workers via Redis key `cb:{source_name}:state`.
- **Ingestion checkpoints**: `ingestion_checkpoints` — resumable crawl; `crawl_batch_id` soft-FK.

---

## Development and Deployment

### Local Development Setup

```bash
# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env  # edit OPENAI_API_KEY, SUPABASE_URL
uvicorn main:app --reload --port 8000

# Frontend
cd ../frontend && npm install && npm run dev  # localhost:3000
```

### Build and Deployment Process

- **Monorepo Railway**: `RAILWAY_SERVICE_ROOT_DIRECTORY=backend|frontend`; `railway.toml` + `Dockerfile` por serviço.
- **Auto-deploy**: Push em `main` → GitHub Actions → Railway webhook.
- **Migration CI (CRIT-050)**: `migration-gate.yml` (PR) + `migration-check.yml` (push/daily) + `deploy.yml` auto-apply.
- **Required secrets**: `SUPABASE_ACCESS_TOKEN`, `SUPABASE_PROJECT_REF`, `SUPABASE_DB_URL`.
- **Force rebuild**: `LABEL build.timestamp` + `ARG CACHEBUST`.
- **Emergency deploy**: `railway redeploy --service bidiq-backend -y`.

---

## Testing Reality

- **Backend**: 169 test files, 5131+ passing, 0 failures. Coverage threshold 70%.
- **Frontend**: 135 test files, 2681+ passing, 0 failures. Coverage threshold 60%.
- **E2E**: 60 Playwright specs.

### Testing Gaps

- Visual regression (Percy/Chromatic) — não configurado.
- Load testing (k6/Locust) — sem baseline.
- Chaos tests — sem failure injection.
- Contract tests (PNCP, Stripe) — snapshots manuais.

### Running Tests

```bash
# Backend
pytest -k "test_name"
python scripts/run_tests_safe.py --parallel 4
pytest --timeout=30 --cov

# Frontend
npm test
npm run test:coverage
npm run test:e2e
```

---

## Risk Register (Forward-Looking)

### CRITICAL (Security, Data Loss, Downtime)

| ID           | Description                                                   | File/Path                                    |
|--------------|---------------------------------------------------------------|----------------------------------------------|
| TD-SYS-001   | CRIT-080 SIGSEGV em POST                                      | Dockerfile, requirements.txt, main.py        |
| TD-SYS-002   | PNCP max 50/page (Feb 2026)                                   | pncp_client.py                               |
| TD-SYS-003   | Railway 120s hard timeout                                     | start.sh, gunicorn_conf.py                   |
| TD-SYS-004   | Migrations não aplicadas (CRIT-039/045/050)                   | .github/workflows/*                          |
| TD-SYS-005   | `search.py` monolítico                                        | routes/search.py                             |

### HIGH

| ID           | Description                                                   | File/Path                                    |
|--------------|---------------------------------------------------------------|----------------------------------------------|
| TD-SYS-010   | L1 cache não shared                                           | cache.py, gunicorn_conf.py                   |
| TD-SYS-011   | Feature flags em 3 lugares                                    | config.py, feature_flags.py, .env            |
| TD-SYS-012   | Setores duplicados                                            | sectors_data.yaml, buscar/page.tsx           |
| TD-SYS-013   | Session dedup 6-24h window                                    | consolidation.py                             |
| TD-SYS-014   | LLM concurrency bottleneck                                    | llm_arbiter.py                               |
| TD-SYS-015   | FTS não otimizado Português                                   | datalake_query.py                            |
| TD-SYS-016   | search_results_cache growth unbounded                         | migrations/026_*                             |
| TD-SYS-017   | Rate limit ausente público                                    | routes/stats_public.py                       |
| TD-SYS-018   | LLM sem cap custo mensal                                      | llm_arbiter.py                               |

### MEDIUM

| ID           | Description                                                   | File/Path                                    |
|--------------|---------------------------------------------------------------|----------------------------------------------|
| TD-SYS-020   | sectors_data.yaml sem validação startup                       | sectors.py                                   |
| TD-SYS-021   | Feature flags docs inconsistentes                             | FEATURE_FLAGS.md                             |
| TD-SYS-022   | Mock location inconsistente                                   | tests/conftest.py                            |
| TD-SYS-023   | Integration tests flaky                                       | tests/integration/                           |
| TD-SYS-024   | schemas.py 1500+ LOC                                          | schemas.py                                   |
| TD-SYS-025   | Logs JSON-vs-text inconsistentes                              | config.py                                    |

### LOW

| ID           | Description                                                   | File/Path                                    |
|--------------|---------------------------------------------------------------|----------------------------------------------|
| TD-SYS-030   | Python + SQL migrations coexistem sem doc                     | migrations/                                  |
| TD-SYS-031   | Dead code legacy                                              | backend/legacy/                              |
| TD-SYS-032   | OTEL spans incompletos                                        | telemetry.py                                 |

**Total sistema**: 20 debits. Complementado por DB-AUDIT.md e frontend-spec.md.

---

## Questions for Specialists (Phase 4+)

### For @data-engineer (Phase 5)

1. `purge_old_bids()` cron configurado em prod? (TD-DB-retention)
2. `pncp_raw_bids.is_active=false` soft-delete vs hard delete — audit trail requirement?
3. `partner_referrals` table — feature shipped ou WIP?
4. `classification_feedback` table — shipped ou optional?
5. RLS `messages` (triple nested EXISTS) — refactor ou accept?
6. `profiles.email` UNIQUE constraint — adicionar?
7. PII em `stripe_webhook_events.payload` — mask ou archive?
8. Owner deletion em `organizations` — soft-delete vs RESTRICT?

### For @ux-design-expert (Phase 6)

1. Server Components strategy — atualmente 88% client-side, plan de migração?
2. TypeScript strict mode — bloqueador para 296 `any` types?
3. Storybook implementation — quando?
4. i18n roadmap — retrofit ou deferir?
5. Design token enforcement — ESLint ou code review?
6. `<Button>` migration (62% ainda `<button>` nativo)?
7. Kanban keyboard nav (@dnd-kit) — WCAG 2.1 AA gap?
8. Performance budgets (LCP/FID targets)?
9. Mobile-first vs desktop-first?
10. Visual regression tool (Percy/Chromatic/Loki)?

---

## Appendix — Useful Commands

```bash
# Supabase CLI
export SUPABASE_ACCESS_TOKEN=$(grep SUPABASE_ACCESS_TOKEN .env | cut -d '=' -f2)
npx supabase db push
npx supabase db diff
npx supabase migration new <name>

# Railway CLI
railway status / logs --tail / variables
railway redeploy --service bidiq-backend -y

# GitHub CLI
gh pr list / create / view <n>
gh api repos/{owner}/{repo}/actions/runs --jq '.workflow_runs[:5]'

# Backend dev
cd backend && uvicorn main:app --reload --port 8000
pytest -k "test_name" / --cov
ruff check . && mypy .

# Frontend dev
cd frontend && npm run dev
npm test / run test:e2e

# AIOS story management
node .aios-core/development/scripts/story-manager.js create --title "..."

# Sector fallback sync
node scripts/sync-setores-fallback.js --dry-run
```

---

**Document Status**: 2.0 (2026-04-14) — Phase 1 of brownfield-discovery workflow complete. Handoff to Phase 2 (@data-engineer) and Phase 3 (@ux-design-expert).
