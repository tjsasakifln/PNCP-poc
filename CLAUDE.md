# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SmartLic** — Plataforma de inteligencia em licitacoes publicas que automatiza a descoberta, analise e qualificacao de oportunidades para empresas B2G (Business-to-Government). Produto da **CONFENGE Avaliacoes e Inteligencia Artificial LTDA**.

**Estagio:** POC avancado (v0.5) em producao — beta com trials, pre-revenue.
**URL:** https://smartlic.tech
**Publico-alvo:** Empresas B2G (todos os portes) + Consultorias/Assessorias de licitacao.
**Diferenciais:** IA de classificacao setorial (GPT-4.1-nano) + Analise de viabilidade 4 fatores.

### O que o SmartLic faz

1. **Busca multi-fonte** — Agrega PNCP + PCP v2 + ComprasGov v3 em uma busca consolidada com dedup
2. **Classificacao IA** — LLM arbiter classifica relevancia setorial (keyword + zero-match classification)
3. **Analise de viabilidade** — 4 fatores (modalidade 30%, timeline 25%, valor 25%, geografia 20%)
4. **Pipeline de oportunidades** — Kanban de editais com drag-and-drop
5. **Relatorios** — Excel estilizado + resumo executivo com IA
6. **Historico** — Buscas salvas, sessoes, analytics

### Tech Stack

**Backend:** FastAPI 0.129, Python 3.12, Pydantic v2, httpx, OpenAI SDK (GPT-4.1-nano), Supabase (PostgreSQL 17 + Auth + RLS), Redis (cache + circuit breaker + state), ARQ (async job queue), Stripe (billing), Resend (email), Prometheus + OpenTelemetry + Sentry, openpyxl, PyYAML

**Frontend:** Next.js 16, React 18, TypeScript 5.9, Tailwind CSS 3, Framer Motion, Recharts, Supabase SSR (auth), Sentry, Mixpanel, @dnd-kit (pipeline), Shepherd.js (onboarding)

**Infra:** Railway (web + worker + frontend), Supabase Cloud, Redis (Upstash/Railway), GitHub Actions (CI/CD)

**Data Sources:**
- PNCP API: `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao` (priority 1)
- PCP v2 API: `https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` (priority 2, public, no auth)
- ComprasGov v3: `https://dadosabertos.compras.gov.br` (priority 3, dual-endpoint)
- OpenAI API: GPT-4.1-nano para classificacao + resumos

**15 Setores:** Definidos em `backend/sectors_data.yaml` — cada setor tem keywords, exclusoes, e viability_value_range.

## Smart Routing — Auto-Invocação de Skills

**REGRA OBRIGATÓRIA:** Quando o usuário envia uma mensagem sem invocar um `/comando` explícito, analise o conteúdo e invoque o skill correspondente via `Skill` tool antes de responder. Use a tabela abaixo como mapa de decisão.

**Pule o roteamento apenas se:**
- O usuário já digitou `/comando` explicitamente
- É conversa casual sem tarefa acionável (agradecimento, pergunta factual simples)
- O usuário disse "responda diretamente" ou equivalente

**NUNCA pule o roteamento por:**
- Continuação implícita de sessão anterior (ex: "sim", "pode fazer", "continue") — **a tarefa ainda precisa ser roteada**
- O agente "já saber" o que fazer pelo contexto — o Skill tool deve ser invocado mesmo assim

### Tabela de Roteamento

| Sinais na mensagem do usuário | Skill a invocar |
|-------------------------------|----------------|
| **Inteligência B2G** | |
| CNPJ + analisar / pesquisar / editais / histórico / oportunidades | `intel-busca` |
| mapear concorrentes / fornecedores / players / quem ganha / market share | `intel-b2g` |
| qualificar leads / scoring / tier / priorizar prospects | `qualify-b2g` |
| cadência / prospecção / sequência de abordagem / follow-up sistemático | `cadencia-b2g` |
| pipeline comercial / funil / forecast / MRR / estágios de venda | `pipeline-b2g` |
| preço / benchmark / valor estimado / quanto custa / margem / P50/P90 | `pricing-b2g` |
| participar edital / go-no-go / dossiê / checklist habilitação / decisão edital | `war-room-b2g` |
| proposta comercial / apresentação / deck / documento de proposta | `proposta-b2g` |
| reter cliente / upsell / churn / health score / renovação | `retention-b2g` |
| monitorar editais / alertas / novos editais do dia / radar | `radar-b2g` |
| relatório executivo / análise profunda CNPJ + editais + mercado | `report-b2g` |
| **Advisory Boards** | |
| copy / texto / mensagem / landing page / email marketing / UX writing | `copymasters` |
| marketing / crescimento / GTM / SEO / conteúdo / CAC / aquisição orgânica | `marketing` |
| cold email / cold outreach / LinkedIn / SDR / abordagem inicial | `outreach` |
| revenue / monetização / pricing / modelo de negócio / unit economics | `turbocash` |
| decisão técnica / arquitetura / trade-off / estratégia produto/tech | `conselho` |
| estratégia empresa / escala / moat / outlier / solo founder / pivot / categoria / obsolescência | `manage` |
| **Desenvolvimento** | |
| bug / erro / quebrou / problema / fix / não funciona | `squad-creator` (args: "bidiq-hotfix") |
| nova feature / implementar / desenvolver / adicionar funcionalidade | `squad-creator` (args: "bidiq-feature-e2e") |
| integrar API / novo cliente / fonte de dados | `squad-creator` (args: "bidiq-api-integration") |
| performance / lento / timeout / otimizar | `squad-creator` (args: "bidiq-performance-audit") |
| próxima issue / o que fazer agora / próximo passo técnico / prioridade | `pick-next-issue` |
| revisar PR / fazer merge / validar PR / governance PR | `review-pr` |
| roadmap / status geral / audit / o que está atrasado / sincronizar | `audit-roadmap` |
| banco de dados / schema / migration / RLS / query / supabase estrutura | `data-engineer` |
| testes / cobertura / QA / suite / validação qualidade | `qa` |
| arquitetura / impacto da mudança / ADR / design sistema | `architect` |
| **Squads aiox (SynkraAI/aiox-squads)** | |
| Lei 14.133 / jurisprudência licitação / impugnação / habilitação edital / acórdão TCU-TCE | `aiox-legal-analyst` |
| componente frontend buscar / SSE / EventSource / Shepherd onboarding / animação buscar-pipeline | `aiox-apex` |
| supplier_contracts / SEO orgânico / blog observatório / sitemap / programmatic SEO | `aiox-seo` |
| pesquisa multi-fonte / deep research / análise setorial B2G / síntese de evidência / PICO | `aiox-deep-research` |
| paralelizar UF/batch/agentes / dispatch agentes / decompor story / wave execução | `aiox-dispatch` |
| memória ecossistema/sessão / aprendizado contínuo / daily sensing / kaizen / Ebbinghaus | `aiox-kaizen-v2` |
| **Meta / Sessão** | |
| beta / usuários reais / feedback / testar com usuário / sessão beta | `beta-team` |
| squad / equipe / time / coordenar agentes / orquestrar | `squad-creator` |
| aios-master / orquestrar tudo / tarefa complexa multi-agente | `aios-master` |
| **Story Lifecycle** | |
| criar story / nova story / story faltante / issue → story / story de bug/incidente | `sm` |
| validar story / story draft review / po review / aprovar story / GO ou NO-GO | `po` |
| **DevOps** | |
| push / subir código / publicar / deploy / enviar para remote / git push | `devops` |

### Exemplos de roteamento automático

- *"preciso analisar o CNPJ 12345 para ver seus editais"* → invoca `intel-busca`
- *"como faço para abordar esse lead?"* → invoca `cadencia-b2g`
- *"qual o preço médio dos contratos de limpeza em SC?"* → invoca `pricing-b2g`
- *"o login está quebrado"* → invoca `squad-creator` com args `bidiq-hotfix`
- *"qual a próxima coisa para fazer no produto?"* → invoca `pick-next-issue`
- *"preciso escrever o email de trial expiring"* → invoca `copymasters`

---

## Behavioral Rules

### NEVER

- Implement without showing options first (always 1, 2, 3 format)
- Delete/remove content without asking first
- Delete anything created in the last 7 days without explicit approval
- Change something that was already working
- Pretend work is done when it isn't
- Process batch without validating one first
- Add features that weren't requested
- Use mock data when real data exists in database
- Explain/justify when receiving criticism (just fix)
- Trust AI/subagent output without verification
- Create from scratch when similar exists in squads/

### ALWAYS

- Present options as "1. X, 2. Y, 3. Z" format
- Use AskUserQuestion tool for clarifications
- Check squads/ and existing components before creating new
- Read COMPLETE schema before proposing database changes
- Investigate root cause when error persists
- Commit before moving to next task
- Create handoff in `docs/sessions/YYYY-MM/` at end of session
- **Use CLI tools (Supabase, Railway, gh) instead of web dashboards when possible**
- **Before writing any `.story.md` file: invoke `Skill(skill: "sm")` first** — mesmo em continuação de sessão
- **Before running any story GO/NO-GO verdict: invoke `Skill(skill: "po")` first**
- **Before any `git push` or `gh pr`: invoke `Skill(skill: "devops")` first**

## Web Search & Industry Validation

**IMPORTANT:** Proactively use web search (WebSearch tool) to validate decisions against industry best practices. This applies to:

### When to Search

- **Before architectural decisions** — Search for current best practices (e.g., "FastAPI circuit breaker pattern 2026", "Next.js SSE best practices")
- **Before adding dependencies** — Verify the package is actively maintained, check for security advisories, compare alternatives
- **When debugging unfamiliar errors** — Search for the specific error message + stack trace patterns
- **Before implementing complex patterns** — Validate approach against industry standards (e.g., "SWR cache invalidation patterns", "Stripe webhook idempotency")
- **When user asks about industry trends** — Search for current state-of-the-art
- **Before database schema changes** — Search for established patterns (e.g., "PostgreSQL RLS best practices", "Supabase migration patterns")
- **When writing prompts for LLMs** — Search for prompt engineering best practices specific to the task

### How to Search Effectively

- Include the current year (2026) in queries for up-to-date results
- Use specific technology names + the pattern being implemented
- Cross-reference at least 2 sources before recommending an approach
- Prefer official docs > well-known blogs > Stack Overflow
- If a searched best practice contradicts this CLAUDE.md, flag it to the user

### When NOT to Search

- For project-specific conventions already documented here
- For trivial changes (typo fixes, variable renames)
- When the user has given explicit, detailed instructions

## CLI Tools Policy

**ALWAYS prefer CLI over web dashboards.** CLIs are faster, scriptable, and keep context in the terminal.

### Supabase CLI

```bash
export SUPABASE_ACCESS_TOKEN=$(grep SUPABASE_ACCESS_TOKEN .env | cut -d '=' -f2)
npx supabase projects list                    # List projects
npx supabase db push                          # Apply migrations
npx supabase db pull                          # Pull remote schema
npx supabase db diff                          # Show schema diff
npx supabase migration new <name>             # Create migration file
npx supabase link --project-ref fqqyovlzdzimiwfofdjk  # Link project
```

### Railway CLI

```bash
# Already authenticated as tiago.sasaki@gmail.com
railway status                                # Current project status
railway logs --tail                           # Stream logs
railway run <command>                         # Run command in Railway env
railway up                                    # Deploy current directory
railway variables                             # List env variables
railway variables set KEY=value               # Set env variable
```

**CRITICAL — Railway Deploy Rules:**
- **NEVER run `railway up` from inside `backend/` or `frontend/`** — always from project root. Running from a subdirectory uploads wrong structure → `Could not find root directory` build failure.
- **Prefer GitHub auto-deploy over `railway up`** — push to `main` triggers deploys automatically with correct monorepo structure.
- **If deploy is stuck SKIPPED:** Commits that don't touch files inside `backend/` or `frontend/` are skipped by Railway watch patterns. To force a rebuild, bump the cache bust in `backend/Dockerfile` (`LABEL build.timestamp` + `ARG CACHEBUST`).
- **`railway up` from root may fail with 413 Payload Too Large** if repo exceeds ~300MB. Use `.railwayignore` to exclude `docs/`, `data/`, `scripts/`, `frontend/` (for backend deploy) or just rely on GitHub auto-deploy.
- **Monorepo config:** `RAILWAY_SERVICE_ROOT_DIRECTORY=backend` (backend), `=frontend` (frontend). Each service has its own `railway.toml` + `Dockerfile`.

### Troubleshooting: Deploy Falha Silenciosamente (CRIT-080)

**PRIMEIRO PASSO:** Verificar GitHub Actions billing **antes de qualquer outra investigação**.

```bash
gh api /repos/{owner}/{repo}/actions/runs --jq '.workflow_runs[:5] | .[] | {status, conclusion, name}'
# Se status="queued" e conclusion=null em múltiplos runs → billing issue
```

- **Sintoma:** Commits em `main` não triggeram deploy; Railway roda versão antiga.
- **Causa:** GitHub Actions com pagamento pendente ou spending limit excedido.
- **Fix:** GitHub Settings > Billing & plans > Actions > resolver pagamento.
- **Deploy de emergência:** `railway redeploy --service bidiq-backend -y` (bypassa Actions).
- **Lição CRIT-080:** `jemalloc LD_PRELOAD` + `Sentry StarletteIntegration` + `cryptography>=46` causam SIGSEGV em POST requests (auth → TLS handshake). GET requests funcionam; POST crasham.

### GitHub CLI

```bash
gh pr list / gh pr create / gh pr view <number>
gh issue list / gh issue create
gh api repos/{owner}/{repo}/...               # Direct API access
```

## Development Commands

### BidIQ Development Squads

```bash
/bidiq                  # Development hub
/bidiq backend          # Squad: team-bidiq-backend (architect, dev, data-engineer, qa)
/bidiq frontend         # Squad: team-bidiq-frontend (ux-design-expert, dev, qa)
/bidiq feature          # Squad: team-bidiq-feature (pm, architect, dev, qa, devops)
```

Resources: `docs/guides/bidiq-development-guide.md`, `.aios-core/development/agent-teams/team-bidiq-*.yaml`

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000            # Dev server

# Tests (IMPORTANT: see Anti-Hang Rules in Testing Strategy)
pytest -k "test_name"               # Specific test (fast, preferred)
pytest tests/test_foo.py            # Single file (safe)
python scripts/run_tests_safe.py    # Full suite — Windows safe (subprocess isolation per file)
python scripts/run_tests_safe.py --parallel 4  # Full suite parallel (4 workers)
pytest --timeout=30                 # Full suite direct (Linux CI — use signal method)
pytest --cov                        # Coverage (threshold: 70%)
pytest tests/integration/           # Integration only
ruff check . && mypy .              # Linting
```

### Frontend

```bash
cd frontend && npm install
npm run dev                         # Dev server at localhost:3000
npm run build && npm start          # Production

# Tests
npm test                            # Run all (must pass 100%)
npm run test:coverage               # Coverage (threshold: 60%)
npm run test:ci                     # CI mode
npm run lint

# E2E (Playwright)
npm run test:e2e                    # Headless
npm run test:e2e:headed             # Debug mode
```

### Pydantic -> TypeScript Type Sync (STORY-2.1 EPIC-TD-2026Q2)

Whenever you change `backend/schemas/*.py` or add/modify `response_model=` on a route, regenerate the frontend types:

```bash
# Terminal 1: run backend locally
cd backend && uvicorn main:app --port 8000

# Terminal 2: regenerate and commit
npm --prefix frontend run generate:api-types
git add frontend/app/api-types.generated.ts
```

- **Source of truth:** `frontend/app/api-types.generated.ts` (auto-generated by `openapi-typescript`, DO NOT edit by hand).
- **Re-export surface:** `frontend/app/types.ts` maps generated schemas to UI-facing names (e.g. `BuscaResult`, `LicitacaoItem`, `Resumo`). Always prefer importing from here; drop down to `components["schemas"]["X"]` only for types that aren't re-exported yet.
- **CI gate:** `.github/workflows/api-types-check.yml` extracts the OpenAPI schema directly from FastAPI (no running backend needed in CI) and fails the PR if the committed generated file drifts from what the backend would produce.
- **Coverage:** every endpoint exposed to the frontend MUST declare `response_model=` on its route decorator so the schema ends up in the OpenAPI output — otherwise CI passes but the frontend stays loosely typed (`{[k: string]: unknown}`).

### Manual Testing (Playwright MCP)

**Production URL:** `https://smartlic.tech`

| Role | Email | Password Source |
|------|-------|----------------|
| Admin | `tiago.sasaki@gmail.com` | env var `SEED_ADMIN_PASSWORD` |
| Master | `marinalvabaron@gmail.com` | env var `SEED_MASTER_PASSWORD` |

### Environment Setup

1. Copy `.env.example` to `.env`
2. Add `OPENAI_API_KEY=sk-...`
3. Configure optional vars (see `.env.example`)

## Key Architecture Patterns

### Data Architecture (3 Layers)

**Layer 1: Periodic Ingestion (ETL → Supabase)**
- ARQ cron jobs: full daily (2am BRT), incremental 3x/day (8am/2pm/8pm BRT), purge daily (4am BRT)
- Table `pncp_raw_bids` (~50K+ rows): open bids — content_hash dedup, GIN full-text index (Portuguese), 12-day retention
- Table `supplier_contracts` (~2M+ rows): historical contracts feeding SEO organic inbound — 3x/week full crawl, incremental same days
- Config: `backend/ingestion/` (config, crawler, transformer, loader, checkpoint, scheduler)
- Checkpoint tracking: `ingestion_checkpoints` + `ingestion_runs` tables for resumable crawls
- Feature flag: `DATALAKE_ENABLED` (default true)

**Layer 2: Search Pipeline (queries local DB, NOT live APIs)**
- `DATALAKE_QUERY_ENABLED=true` (default): `execute.py` → `query_datalake()` → `search_datalake` RPC
- PostgreSQL full-text search (tsquery Portuguese) with UF/date/modality/value/esfera filters, returns <100ms at p95
- Fallback: if datalake returns 0 results, falls through to live multi-source API fetch
- Async-first (CRIT-072): POST /buscar → 202 in <2s, results via SSE + polling
- SSE chain: bodyTimeout(0) + heartbeat(15s) > Railway idle(60s) | SSE inactivity timeout(120s)

**Layer 3: Search Results Cache (passive, per-request)**
- L1: InMemoryCache (4h, hot/warm/cold priority)
- L2: Supabase `search_results_cache` (24h, persistent)
- SWR (per-request reactive): when a request touches a stale entry (6-24h), serve stale + trigger background revalidation in `cache/swr.py::trigger_background_revalidation` (max 3 concurrent, 180s timeout)
- **No proactive warming.** Cache warming jobs (startup/cron/coverage-check) were deprecated 2026-04-18 (STORY-CIG-BE-cache-warming-deprecate). DataLake query latency <100ms made pre-population overhead pure waste. Cache populates on-demand from real user requests.

**Legacy Fallback: Live API Fetch (only when datalake returns 0 or DATALAKE_QUERY_ENABLED=false)**
- `pncp_client.py` (PNCP), `portal_compras_client.py` (PCP v2), `compras_gov_client.py` (ComprasGov v3)
- Per-source circuit breakers, priority-based dedup (PNCP=1 > PCP=2), phased UF batching
- Timeout chain: ARQ Job(300s) > Pipeline(110s) > Consolidation(100s) > PerSource(80s) > PerUF(30s)

### LLM Classification
- Keywords match -> "keyword" source (>5% density)
- Low density -> "llm_standard" (2-5%), "llm_conservative" (1-2%)
- Zero match -> "llm_zero_match" (GPT-4.1-nano YES/NO)
- Fallback = PENDING_REVIEW on LLM failure when `LLM_FALLBACK_PENDING_ENABLED=true` (gray zone + zero-match); hard REJECT when disabled
- Classification SLA: precision >= 85%, recall >= 70% (benchmark-validated, 15 samples/sector). NOT zero FN/FP — impossible with ambiguous government text.
- Observability: `smartlic_filter_decisions_by_setor_total`, `smartlic_llm_fallback_rejects_total`, `smartlic_feedback_negative_total` Prometheus counters

### SSE Progress Tracking
- `search_id` links SSE stream to POST request
- Dual-connection: `GET /buscar-progress/{id}` (SSE) + `POST /buscar` (JSON)
- In-memory asyncio.Queue-based tracker
- Frontend graceful fallback: if SSE fails, uses time-based simulation

### ARQ Job Queue
- LLM summaries + Excel generation dispatched as background jobs
- Immediate response with fallback summary (`gerar_resumo_fallback()`)
- SSE events `llm_ready` / `excel_ready` update result in real-time
- Web + Worker separated via `PROCESS_TYPE` in `start.sh`

For detailed module tables and route maps, see `.claude/rules/architecture-detail.md` (auto-loaded).

## Critical Implementation Notes

### Ingestion Pipeline (Layer 1)
- **Schedule:** Full crawl daily 5 UTC (2am BRT), incremental 11/17/23 UTC, purge 7 UTC
- **Scope:** 27 UFs × 6 modalidades (4,5,6,7,8,12), 10-day window (full), 3-day (incremental)
- **Concurrency:** 5 UFs parallel, 2s delay between batches, max 50 pages per (UF, modalidade)
- **Upsert:** 500 rows/batch via `upsert_pncp_raw_bids` RPC with content_hash dedup
- **Retention:** 12 days (purge sets `is_active=false`, soft-delete)
- **Tables:** `pncp_raw_bids` (data), `ingestion_checkpoints` (progress), `ingestion_runs` (audit)
- **Worker:** `PROCESS_TYPE=worker` → `arq job_queue.WorkerSettings`
- **pg_cron backup (STORY-1.2):** `purge-old-bids` scheduled via `cron.schedule('purge-old-bids', '0 7 * * *', ...)` — runs server-side even if Railway worker is offline. Monitored by STORY-1.1.

### pg_cron Monitoring (STORY-1.1 EPIC-TD-2026Q2)

All scheduled pg_cron jobs (purge-old-bids, cleanup-search-cache, cleanup-search-store, and any future additions) are monitored end-to-end:

- **View:** `public.cron_job_health` joins `cron.job` + `cron.job_run_details` over a 7-day window.
- **RPC:** `public.get_cron_health()` (SECURITY DEFINER) — invoked by backend only.
- **Endpoint:** `GET /v1/admin/cron-status` (admin-only) returns JSON snapshot — shape `{status, count, jobs: [{jobname, last_status, last_run_at, runs_24h, failures_24h, latency_avg_ms}]}`.
- **Alerting:** hourly ARQ cron `cron_monitoring_job` (in `backend/jobs/cron/cron_monitor.py`) emits a Sentry `capture_message(level="error")` for any job that is `failed` or stale (>25h since last run). Fingerprint `["cron_job", jobname, reason]` dedups across runs.

**To add a new scheduled cron:**
1. Create a migration `supabase/migrations/YYYYMMDDHHMMSS_schedule_<name>.sql` calling `cron.schedule(...)`.
2. That's it — the existing monitor will start checking the new job on the next hourly tick. No code changes required unless you want custom thresholds.

### PNCP API (used by ingestion + legacy fallback)
- **Max tamanhoPagina = 50** (reduced from 500 in Feb 2026, >50 -> HTTP 400 silent)
- Search period default: 10 days (frontend + backend)
- Phased UF batching: PNCP_BATCH_SIZE=5, PNCP_BATCH_DELAY_S=2.0
- Retry: exponential backoff, HTTP 422 is retryable (max 1 retry)
- Circuit breaker: 15 failures threshold, 60s cooldown
- Fast health canary (`backend/health.py`) validates `tamanhoPagina=50` succeeds (production value) + delegates to `pncp_canary.validate_page_size_limit` to probe `tamanhoPagina=51` on every health cycle.

### PNCP Breaking Change Canary (STORY-4.5)

Background ARQ cron in `backend/jobs/cron/pncp_canary.py` runs every `PNCP_CANARY_INTERVAL_S` seconds (default 600s = 10 min) and triggers Sentry fatal alerts when:

| Reason | Probe | Sentry gate |
|--------|-------|-------------|
| `max_page_size_changed` | `tamanhoPagina=51` accepted (HTTP < 400) | immediate (1 occurrence) |
| `canary_3x_failed` | `tamanhoPagina=50` fails or returns non-JSON for 3 consecutive runs | threshold gated |
| `shape_drift` | `tamanhoPagina=50` payload fails `backend/contracts/schemas/pncp_search_response.schema.json` | immediate |

Dedup: each reason uses a Redis flag with 6h TTL so operators get one Sentry event per incident, not 36/day. Tags: `pncp_breaking_change={reason}`, `source=pncp`. Fingerprint: `["pncp_canary", reason]`.

Metrics (Prometheus): `smartlic_pncp_max_page_size_changed_total`, `smartlic_pncp_canary_consecutive_failures`, `smartlic_pncp_canary_shape_drift_total`. Disable the cron with `PNCP_CANARY_INTERVAL_S=0`; raise/lower the threshold via `PNCP_CANARY_FAIL_THRESHOLD` (default 3).

### PCP v2 (Secondary)
- No auth required (fully public v2 API)
- Fixed 10/page pagination (`pageCount`/`nextPage`)
- Client-side UF filtering only (no server-side UF param)
- `valor_estimado=0.0` (v2 has no value data)

### ComprasGov v3 (Tertiary)
- Dual-endpoint: legacy + Lei 14.133
- Base URL: `dadosabertos.compras.gov.br`

### Filtering Pipeline (order matters — fail-fast)
1. UF check (fastest)
2. Value range check
3. Keyword matching (density scoring)
4. LLM zero-match classification (for 0% keyword density)
5. Status/date validation
6. Viability assessment (post-filter)

**Feature Flags:** `DATALAKE_ENABLED`, `DATALAKE_QUERY_ENABLED`, `LLM_ZERO_MATCH_ENABLED`, `LLM_ARBITER_ENABLED`, `VIABILITY_ASSESSMENT_ENABLED`, `SYNONYM_MATCHING_ENABLED`

### LLM Integration
- GPT-4.1-nano for classification + summaries
- Zero-match prompt: `_build_zero_match_prompt()` in `llm_arbiter.py`
- Fallback = PENDING_REVIEW on failure (gray zone + zero-match) when `LLM_FALLBACK_PENDING_ENABLED=true`; REJECT when disabled
- ARQ background jobs for summaries (immediate fallback response)
- ThreadPoolExecutor(max_workers=10) for parallel LLM calls

### Cache Strategy (Layer 3 — caches search results, NOT raw bids)
- L1 InMemoryCache: 4h TTL, hot/warm/cold priority
- L2 Supabase `search_results_cache`: 24h TTL, persistent
- Fresh (0-6h) -> Stale (6-24h, served + background refresh) -> Expired (>24h, not served)
- Patch `supabase_client.get_supabase` for cache tests (not `search_cache.get_supabase`)

### Billing & Auth
- **Pricing (STORY-277/360):** SmartLic Pro R$397/mes (mensal), R$357/mes (semestral, 10% off), R$297/mes (anual, 25% off). Consultoria R$997/mes, R$897/sem (10%), R$797/anual (20%). Source of truth: `plan_billing_periods` table (synced from Stripe)
- **Trial:** 14 dias gratis (STORY-264/277/319), sem cartao
- Stripe handles proration automatically — NO custom prorata code
- "Fail to last known plan": never fall back to free_trial on DB errors
- 3-day grace period for subscription gaps (`SUBSCRIPTION_GRACE_DAYS`)
- ALL Stripe webhook handlers sync `profiles.plan_type`
- Frontend localStorage plan cache (1hr TTL) prevents UI downgrades
- Tests mocking `/buscar` MUST also mock `check_and_increment_quota_atomic`

### Railway/Gunicorn Critical Notes
- **Railway hard timeout: ~120s** — requests exceeding this are killed by Railway proxy
- Gunicorn timeout: 180s (env var `GUNICORN_TIMEOUT` overrides)
- Sync PNCPClient fallback wrapped in `asyncio.to_thread()` — never blocks event loop
- Gunicorn keep-alive: 75s (> Railway proxy 60s) prevents intermittent 502s

### Time Budget Waterfall (STORY-4.4 TD-SYS-003)

Defaults tightened in `backend/config/pncp.py` so the inner timeout always expires before Railway kills the request — leaving ~20s headroom for response serialization:

```
Railway proxy     [========================== 120s ==========================]
Gunicorn worker   [======================= 110s ========================]
Pipeline budget   [==================== 100s ====================]
  Consolidation   [================== 90s ===================]
    PerSource     [============= 70s =============]
      PerUF       [===== 25s =====]
        httpx r/w [10c+15r]
```

Invariant (enforced by `backend/tests/test_timeout_invariants.py`): `pipeline(100) > consolidation(90) > per_source(70) > per_uf(25) > (per_modality 20 + httpx 15)`.

Both knobs (`config/pncp.py` and `source_config/sources.ConsolidationConfig`) now share defaults — the "divergência 300s vs 100s" documented pre-STORY-4.4 is resolved.

Pipeline call sites go through `backend/pipeline/budget.py::_run_with_budget` so every TimeoutError increments `smartlic_pipeline_budget_exceeded_total{phase,source}`. Query `histogram_quantile(0.95, rate(smartlic_pipeline_duration_seconds_bucket[5m]))` for the current p95; alert `rate(smartlic_pipeline_budget_exceeded_total[5m]) > 0`.

To unblock a specific deploy (emergency), override via Railway vars: `PIPELINE_TIMEOUT=110`, `CONSOLIDATION_TIMEOUT=100`, `PNCP_TIMEOUT_PER_SOURCE=80`, etc. — no code change needed.

### Type Safety
- **Python:** Type hints on all functions, Pydantic for API contracts, pattern validation for dates
- **TypeScript:** Interfaces over types, no `any`, strict null checks enabled

## Testing Strategy

### Backend (backend/tests/)

**169 test files, 5131+ passing, 0 failures** — CI gate: `.github/workflows/backend-tests.yml`

**Zero-Failure Policy:** 0 failures is the only acceptable baseline. Fix them, never treat as "pre-existing".

**Key Testing Patterns (IMPORTANT — wrong mocks cause hard-to-debug failures):**
- Auth: Use `app.dependency_overrides[require_auth]` NOT `patch("routes.X.require_auth")`
- Cache: Patch `supabase_client.get_supabase` (not `search_cache.get_supabase`)
- Config: Use `@patch("config.FLAG_NAME", False)` not `os.environ`
- LLM: Mock at `@patch("llm_arbiter._get_client")` level
- Quota: Tests mocking `/buscar` MUST also mock `check_and_increment_quota_atomic`
- ARQ: Mock with `sys.modules["arq"]` (not installed locally). Conftest autouse fixture `_isolate_arq_module` handles cleanup automatically — do NOT do raw `sys.modules["arq"] = ...` without cleanup

**Anti-Hang Rules (CRITICAL — violations cause full-suite freezes):**
- **pytest-timeout**: Every test has a 30s timeout (`pyproject.toml`). Override with `@pytest.mark.timeout(60)` for slow integration tests
- **NEVER use `asyncio.get_event_loop().run_until_complete()`** in tests — use `async def` + `@pytest.mark.asyncio` instead
- **NEVER use `sys.modules["arq"] = MagicMock()`** without cleanup — the conftest fixture handles isolation automatically
- **Fire-and-forget tasks**: Conftest `_cleanup_pending_async_tasks` cancels lingering `asyncio.create_task()` after each test
- **subprocess in tests**: Always use `timeout` parameter in `Popen.communicate()` and clean up with `proc.kill()`
- **Full-suite validation**: Run `pytest --timeout=30 -q` periodically to catch hanging tests early
- **timeout_method = "thread"**: Required for Windows compatibility (signal method is Unix-only)

### Frontend (frontend/__tests__/)

**135 test files, 2681+ passing, 0 failures** — CI gate: `.github/workflows/frontend-tests.yml`

**jest.setup.js polyfills:** `crypto.randomUUID` + `EventSource` (jsdom lacks both)

### E2E (Playwright)

**60 critical user flow tests** in `frontend/e2e-tests/`. CI: `.github/workflows/e2e.yml`

## AIOS Framework & Agents

This project uses the AIOS Framework for AI-orchestrated development. Full agent, task, workflow, and script documentation is in `.claude/rules/aios-framework.md` (auto-loaded).

**Quick Reference:**
- Agents: `@dev`, `@qa`, `@architect`, `@pm`, `@devops`, `@data-engineer`, `@ux-design-expert`, `@analyst`, `@sm`, `@po`, `@aios-master`
- Invoke via `Skill` tool: `Skill(skill: "dev", args: "implement X")`
- **PROACTIVE RULE:** When the user describes a task, AUTOMATICALLY select and follow the matching BidIQ workflow without waiting for explicit invocation
- **This project is BROWNFIELD** — use brownfield and BidIQ-specific workflows

## Common Development Recipes

For step-by-step procedures (adding filters, modifying Excel, changing LLM prompts, syncing sectors), see `.claude/rules/dev-recipes.md` (auto-loaded).

## Security Notes

Supabase Auth with RLS on all tables. Input validation via Pydantic (backend) and form validation (frontend). CORS configurable via `CORS_ORIGINS`. API keys in env vars only (never commit). Log sanitization via `log_sanitizer.py`. Redis token bucket rate limiting. Stripe webhook signature verification. Admin endpoints require `is_admin` or `is_master` role check.

## Important Files

| Category | Files |
|----------|-------|
| **Docs** | `PRD.md`, `ROADMAP.md`, `CHANGELOG.md`, `docs/summaries/gtm-resilience-summary.md`, `docs/summaries/gtm-fixes-summary.md` |
| **Config** | `.env.example`, `backend/requirements.txt`, `frontend/package.json`, `backend/sectors_data.yaml`, `backend/config.py` |
| **Database** | `supabase/migrations/` (35), `backend/migrations/` (7+) |
| **Ingestion** | `backend/ingestion/` (config, crawler, transformer, loader, checkpoint, scheduler), `backend/datalake_query.py` |
| **AIOS** | `.aios-core/development/agents/` (11), `.aios-core/development/tasks/` (115+), `.aios-core/development/workflows/` (7) |

## Git Workflow

**Branches:** `main` (production), `feature/*`, `fix/*`

**Commits:** Use conventional commits: `feat(backend):`, `fix(frontend):`, `docs:`, `chore:`

**Before Committing:** Run tests (pytest / npm test), check linting, update docs.

### Migration Policy (STORY-6.3 EPIC-TD-2026Q2)

| Directory | Role | Policy |
|-----------|------|--------|
| `supabase/migrations/` | **Source of truth** for all SQL schema (tables, indexes, RLS, pg_cron schedules) | New migrations go here. Applied via `npx supabase db push` and CI auto-apply (CRIT-050). Every new `.sql` must have a paired `.down.sql` rollback script (STORY-6.2). |
| `backend/migrations/` | **Legacy** Python/Alembic scripts | Historical audit trail only. Do NOT add new migrations here. Kept for reference; not executed by CI. |

**Rule for devs:** All schema changes → `supabase/migrations/YYYYMMDDHHMMSS_description.sql` + paired `YYYYMMDDHHMMSS_description.down.sql`. See `supabase/migrations/README.md` for templates and conventions.

### Migration CI Flow (CRIT-050)

Three-layer defense against unapplied migrations (prevents CRIT-039/CRIT-045 recurrence):

1. **PR Warning** (`migration-gate.yml`) — Runs on PRs touching `supabase/migrations/`. Lists pending migrations and posts a WARNING comment. Also enforces down.sql pairing (STORY-6.2 — blocks if missing). Does NOT block merge for pending-migration warnings.
2. **Push Alert** (`migration-check.yml`) — Runs on push to main + daily schedule. Blocks (exit 1) if unapplied migrations detected.
3. **Auto-Apply on Deploy** (`deploy.yml`) — After backend deploys, runs `supabase db push --include-all` automatically. Sends `NOTIFY pgrst, 'reload schema'` for immediate PostgREST cache refresh. Verifies no PGRST205 errors via smoke test. If push fails, marks deploy as DEGRADED (does not rollback).

**Required Secrets:** `SUPABASE_ACCESS_TOKEN`, `SUPABASE_PROJECT_REF`, `SUPABASE_DB_URL` (for NOTIFY pgrst)
