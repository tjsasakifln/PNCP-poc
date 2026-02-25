# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SmartLic** — Plataforma de inteligência em licitações públicas que automatiza a descoberta, análise e qualificação de oportunidades para empresas B2G (Business-to-Government). Produto da **CONFENGE Avaliações e Inteligência Artificial LTDA**.

**Estágio:** POC avançado (v0.5) em produção — beta com trials, pré-revenue.
**URL:** https://smartlic.tech
**Público-alvo:** Empresas B2G (todos os portes) + Consultorias/Assessorias de licitação.
**Diferenciais:** IA de classificação setorial (GPT-4.1-nano) + Análise de viabilidade 4 fatores.

### O que o SmartLic faz

1. **Busca multi-fonte** — Agrega PNCP + PCP v2 + ComprasGov v3 em uma busca consolidada com dedup
2. **Classificação IA** — LLM arbiter classifica relevância setorial (keyword + zero-match classification)
3. **Análise de viabilidade** — 4 fatores (modalidade 30%, timeline 25%, valor 25%, geografia 20%)
4. **Pipeline de oportunidades** — Kanban de editais com drag-and-drop
5. **Relatórios** — Excel estilizado + resumo executivo com IA
6. **Histórico** — Buscas salvas, sessões, analytics

### Tech Stack

**Backend (65+ módulos Python):**
- FastAPI 0.129.0, Python 3.12, Pydantic 2.12
- httpx 0.28 (resilient HTTP) + OpenAI SDK 1.109 (GPT-4.1-nano)
- Supabase (PostgreSQL + Auth + RLS) + Redis 5.3 (cache + circuit breaker)
- ARQ 0.26 (async job queue — LLM/Excel em background)
- Stripe 11.4 (billing) + Resend (transactional email)
- Prometheus (metrics) + OpenTelemetry (tracing) + Sentry (errors)
- openpyxl (Excel) + PyYAML (sector config)

**Frontend (22 páginas, 33 componentes):**
- Next.js 16, React 18, TypeScript 5.9
- Tailwind CSS 3.4 + Framer Motion + Recharts
- Supabase SSR (auth) + Sentry + Mixpanel
- @dnd-kit (pipeline drag-and-drop) + Shepherd.js (onboarding tours)

**Infraestrutura:**
- Railway (web + worker + frontend) — deploy via `railway up`
- Supabase Cloud (PostgreSQL + Auth + Storage)
- Redis (Upstash ou Railway addon)
- GitHub Actions (CI/CD — tests + e2e + deploy)

**Data Sources:**
- PNCP API: `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao` (priority 1)
- PCP v2 API: `https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` (priority 2, public, no auth)
- ComprasGov v3: `https://dadosabertos.compras.gov.br` (priority 3, dual-endpoint)
- OpenAI API: GPT-4.1-nano para classificação + resumos

### 15 Setores

| ID | Nome |
|----|------|
| vestuario | Vestuário e Uniformes |
| alimentos | Alimentos e Merenda |
| informatica | Hardware e Equipamentos de TI |
| mobiliario | Mobiliário |
| papelaria | Papelaria e Material de Escritório |
| engenharia | Engenharia, Projetos e Obras |
| software | Software e Sistemas |
| facilities | Facilities e Manutenção |
| saude | Saúde |
| vigilancia | Vigilância e Segurança Patrimonial |
| transporte | Transporte e Veículos |
| manutencao_predial | Manutenção e Conservação Predial |
| engenharia_rodoviaria | Engenharia Rodoviária e Infraestrutura Viária |
| materiais_eletricos | Materiais Elétricos e Instalações |
| materiais_hidraulicos | Materiais Hidráulicos e Saneamento |

Cada setor tem keywords, exclusões, e viability_value_range definidos em `backend/sectors_data.yaml`.

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

## CLI Tools Policy

**ALWAYS prefer CLI over web dashboards.** CLIs are faster, scriptable, and keep context in the terminal.

### Supabase CLI

```bash
# Load token from .env
export SUPABASE_ACCESS_TOKEN=$(grep SUPABASE_ACCESS_TOKEN .env | cut -d '=' -f2)

# Common commands
npx supabase projects list                    # List projects
npx supabase db push                          # Apply migrations
npx supabase db pull                          # Pull remote schema
npx supabase db diff                          # Show schema diff
npx supabase migration new <name>             # Create migration file

# Link project (first time)
npx supabase link --project-ref fqqyovlzdzimiwfofdjk
```

### Railway CLI

```bash
# Already authenticated as tiago.sasaki@gmail.com
railway status                                # Current project status
railway logs                                  # View logs
railway logs --tail                           # Stream logs
railway run <command>                         # Run command in Railway env
railway up                                    # Deploy current directory
railway variables                             # List env variables
railway variables set KEY=value               # Set env variable
```

### GitHub CLI

```bash
gh pr list                                    # List PRs
gh pr create                                  # Create PR
gh pr view <number>                           # View PR details
gh issue list                                 # List issues
gh issue create                               # Create issue
gh api repos/{owner}/{repo}/...               # Direct API access
```

## Development Commands

### SmartLic Development Acceleration

#### Option 1: Automatic Activation (Recommended)

System automatically detects context and suggests squad:

```bash
# Start working - system detects context
cd backend/
# 🐍 BidIQ Development Assistant
# 📍 Detected: Backend Development
# 💡 Recommended: team-bidiq-backend
# Type: /bidiq backend

# Or manually activate after detection:
/bidiq backend
```

**What's Detected Automatically:**
- Directory (backend/, frontend/, docs/stories/)
- Git branch (feature/*, fix/*, etc.)
- Modified files (backend vs frontend)
- Story status (in progress, pending)
- Test coverage and failures

**See Full Analysis:**
```bash
node .aios-core/development/scripts/bidiq-greeting-system.js
node .aios-core/development/scripts/bidiq-context-detector.js
```

#### Option 2: Manual Activation

Quick start with specialized agent squads:

```bash
# Access development hub
/bidiq

# 1. Backend development (FastAPI, PNCP client, database)
/bidiq backend
→ Squad: team-bidiq-backend (architect, dev, data-engineer, qa)

# 2. Frontend development (React, Next.js, UI)
/bidiq frontend
→ Squad: team-bidiq-frontend (ux-design-expert, dev, qa)

# 3. Complete features (backend + frontend)
/bidiq feature
→ Squad: team-bidiq-feature (pm, architect, dev, qa, devops)
```

**Resources:**
- **Auto-Activation Guide:** `docs/guides/bidiq-auto-activation-guide.md` (NEW!)
- **Development Guide:** `docs/guides/bidiq-development-guide.md`
- **Command Hub:** `/bidiq` (activation point)
- **Squad Configs:** `.aios-core/development/agent-teams/team-bidiq-*.yaml`
- **Config:** `.aios-core/development/configs/bidiq-activation-config.yaml`

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run dev server
uvicorn main:app --reload --port 8000

# Run tests
pytest                              # Run all tests
pytest --cov                        # With coverage report (threshold: 70%)
pytest --cov --cov-report=html      # Generate HTML coverage report
pytest -v                           # Verbose output
pytest -k "test_name"               # Run specific test
pytest --maxfail=1                  # Stop on first failure

# Linting (when configured)
ruff check .
mypy .
```

### Frontend

```bash
cd frontend
npm install

# Development
npm run dev      # Start dev server at http://localhost:3000

# Production
npm run build
npm start

# Testing
npm test                  # Run all tests
npm run test:coverage     # With coverage report (threshold: 60%)
npm run test:watch        # Watch mode for development
npm run test:ci           # CI mode (non-interactive)
npm run lint

# E2E Testing (Playwright)
npm run test:e2e          # Run E2E tests (headless)
npm run test:e2e:headed   # Run E2E tests (headed mode for debugging)
npm run test:e2e:debug    # Debug mode (step through tests)
npm run test:e2e:ui       # Playwright UI mode (interactive)
npm run test:e2e:report   # View last test report
```

### E2E Testing

**Framework:** Playwright 1.58+

**Configuration:** `frontend/playwright.config.ts`

**Test Location:** `frontend/e2e-tests/`

**Browsers Tested:**
- Chromium (Desktop Chrome)
- Mobile Safari (iPhone 13)

**Critical User Flows (60 tests):**
1. **Search Flow** - UF selection → Date range → Search → Results → Download
2. **Theme Switching** - Toggle theme → Verify persistence → Check CSS variables
3. **Saved Searches** - Execute search → Auto-save → Reload → Load saved
4. **Empty State** - No results → Empty state display → Adjust filters
5. **Error Handling** - Network errors → Timeout → User-friendly messages

Run with `npm run test:e2e` (headless) or `npm run test:e2e:headed` (debug). CI workflow: `.github/workflows/e2e.yml`.

### Manual Testing with Playwright MCP

When requested to test the production system, use **MCP Playwright** for browser automation. This enables rigorous, real-world testing beyond automated test suites.

**Production URL:** `https://smartlic.tech`

#### Test Credentials

| Role | Email | Password | Use Case |
|------|-------|----------|----------|
| **Admin** | `tiago.sasaki@gmail.com` | `B1lous234!` | Test admin features, user management, full functionality |
| **Master** | `marinalvabaron@gmail.com` | `mudar123` | Test master/superadmin features, global settings |

#### Testing Protocol

When asked to "test as admin" or "test as master":

1. **Navigate to production URL** using `mcp__playwright__browser_navigate`
2. **Take initial snapshot** using `mcp__playwright__browser_snapshot`
3. **Login with appropriate credentials** using `mcp__playwright__browser_type` and `mcp__playwright__browser_click`
4. **Systematically test ALL functionalities** - not just happy paths

### Environment Setup

1. Copy `.env.example` to `.env`
2. Add `OPENAI_API_KEY=sk-...`
3. Configure optional vars (see `.env.example` for comprehensive documentation)

## Architecture & Key Concepts

### High-Level Data Flow

```
User (Next.js 22 pages) → API Proxy (Next.js route handlers)
        ↓                           ↓
   Supabase Auth              Backend API (FastAPI)
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
                PNCP API      PCP v2 API     ComprasGov v3
                (priority 1)  (priority 2)   (priority 3)
                    └───────────────┼───────────────┘
                                    ↓
                         Consolidation + Dedup
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
               Filter (KW)    LLM Arbiter    Viability
               + Exclusion    (zero-match)   Assessment
                    └───────────────┼───────────────┘
                                    ↓
                         ┌──────────┼──────────┐
                         ↓          ↓          ↓
                    LLM Summary   Excel    Pipeline
                    (ARQ job)    (ARQ job)  (Supabase)
                         ↓
                    SSE Progress → User
```

### Backend Architecture (backend/)

**Core Modules (65+ files):**

| Category | Modules | Purpose |
|----------|---------|---------|
| **Entry** | `main.py`, `config.py`, `schemas.py` | App setup, env config, Pydantic models |
| **Search Pipeline** | `search_pipeline.py`, `consolidation.py`, `search_context.py`, `search_state_manager.py` | Multi-source orchestration, state machine |
| **Data Sources** | `pncp_client.py`, `portal_compras_client.py`, `compras_gov_client.py` + 4 others in `clients/` | PNCP, PCP v2, ComprasGov v3 |
| **Filtering** | `filter.py`, `filter_stats.py`, `term_parser.py`, `synonyms.py`, `status_inference.py` | Keyword matching, density scoring |
| **AI/LLM** | `llm.py`, `llm_arbiter.py`, `relevance.py`, `viability.py` | Classification, summaries, viability |
| **Cache** | `search_cache.py`, `cache.py`, `redis_client.py`, `redis_pool.py` | Two-level cache (InMemory + Supabase), SWR |
| **Auth** | `auth.py`, `authorization.py`, `oauth.py`, `quota.py` | Supabase auth, RLS, plan quotas |
| **Billing** | `services/billing.py`, `webhooks/stripe.py` | Stripe subscriptions, webhooks |
| **Jobs** | `job_queue.py`, `cron_jobs.py` | ARQ background processing |
| **Monitoring** | `metrics.py`, `telemetry.py`, `health.py`, `audit.py` | Prometheus, OpenTelemetry, Sentry |
| **Output** | `excel.py`, `google_sheets.py`, `report_generator.py` | Excel, Google Sheets export |
| **Feedback** | `feedback_analyzer.py` | User feedback patterns, bi-gram analysis |
| **Sectors** | `sectors.py`, `sectors_data.yaml` | 15 sector definitions + keywords |
| **Email** | `email_service.py`, `templates/emails/` | Transactional emails via Resend |
| **Progress** | `progress.py` | SSE progress tracking (asyncio.Queue) |
| **Routes** | 19 modules in `routes/` | All API endpoints |

**API Routes (49 endpoints across 19 modules):**

| Module | Key Endpoints |
|--------|--------------|
| `search.py` | `POST /buscar`, `GET /buscar-progress/{id}` (SSE), `GET /v1/search/{id}/status`, `POST /v1/search/{id}/retry` |
| `pipeline.py` | `POST/GET/PATCH/DELETE /pipeline`, `GET /pipeline/alerts` |
| `billing.py` | `GET /plans`, `POST /checkout`, `POST /billing-portal`, `GET /subscription/status` |
| `user.py` | `GET /me`, `POST /change-password`, `GET /trial-status`, `PUT/GET /profile/context` |
| `analytics.py` | `GET /summary`, `GET /searches-over-time`, `GET /top-dimensions`, `GET /trial-value` |
| `feedback.py` | `POST/DELETE /feedback`, `GET /admin/feedback/patterns` |
| `health.py` | `GET /health/cache` |
| `onboarding.py` | `POST /first-analysis` |
| `sessions.py` | `GET /sessions` |
| `messages.py` | `POST/GET /conversations`, `POST /{id}/reply`, `PATCH /{id}/status` |
| `auth_oauth.py` | `GET /google`, `GET /google/callback`, `DELETE /google` |
| `admin_trace.py` | `GET /search-trace/{search_id}` |
| Others | Plans, exports, features, subscriptions, emails |

### Frontend Architecture (frontend/app/)

**22 Pages:**

| Route | Purpose |
|-------|---------|
| `/` | Landing page |
| `/login`, `/signup` | Authentication |
| `/auth/callback` | OAuth callback |
| `/recuperar-senha`, `/redefinir-senha` | Password reset |
| `/onboarding` | 3-step wizard (CNAE → UFs → Confirmação) |
| `/buscar` | **Main search page** — filters, results, SSE progress |
| `/dashboard` | User dashboard with analytics |
| `/historico` | Search history |
| `/pipeline` | Opportunity pipeline (kanban) |
| `/mensagens` | Messaging system |
| `/conta` | Account settings |
| `/planos`, `/planos/obrigado` | Pricing + thank you |
| `/pricing`, `/features` | Marketing pages |
| `/ajuda` | Help center |
| `/admin`, `/admin/cache` | Admin dashboards |
| `/termos`, `/privacidade` | Legal pages |

**33 Components** in `app/buscar/components/` + `components/`:
- Search: `SearchForm`, `SearchResults`, `FilterPanel`, `UfProgressGrid`
- Resilience: `CacheBanner`, `DegradationBanner`, `PartialResultsPrompt`, `SourcesUnavailable`, `ErrorDetail`
- AI: `LlmSourceBadge`, `ViabilityBadge`, `FeedbackButtons`, `ReliabilityBadge`
- Billing: `PlanCard`, `PlanToggle`, `PaymentFailedBanner`, `CancelSubscriptionModal`
- Loading: `EnhancedLoadingProgress`, `LoadingProgress`

**API Proxies** (`app/api/`): buscar, download, analytics, admin, feedback, trial-status, user, plans, pipeline, sessions, etc.

### Key Architecture Patterns

**Multi-Source Pipeline:**
- 3 data sources with per-source circuit breakers
- Priority-based dedup (PNCP=1 wins over PCP=2)
- Fallback cascade: Live → Partial → Stale cache → Empty
- Timeout chain: FE(480s) > Pipeline(360s) > Consolidation(300s) > PerSource(180s) > PerUF(90s)

**Two-Level Cache (SWR):**
- L1: InMemoryCache (4h, proactive) — hot/warm/cold priority
- L2: Supabase (24h, failover) — persistent across restarts
- Stale-While-Revalidate: serves stale, refreshes in background
- Background revalidation: max 3 concurrent, 180s timeout

**LLM Classification:**
- Keywords match → "keyword" source (>5% density)
- Low density → "llm_standard" (2-5%), "llm_conservative" (1-2%)
- Zero match → "llm_zero_match" (GPT-4.1-nano YES/NO)
- Fallback = REJECT on LLM failure (zero noise philosophy)

**SSE Progress Tracking:**
- `search_id` links SSE stream to POST request
- Dual-connection: `GET /buscar-progress/{id}` (SSE) + `POST /buscar` (JSON)
- In-memory asyncio.Queue-based tracker
- Frontend graceful fallback: if SSE fails, uses time-based simulation

**ARQ Job Queue:**
- LLM summaries + Excel generation dispatched as background jobs
- Immediate response with fallback summary (`gerar_resumo_fallback()`)
- SSE events `llm_ready` / `excel_ready` update result in real-time
- Web + Worker separated via `PROCESS_TYPE` in `start.sh`

**PNCP API Critical Notes:**
- **Max tamanhoPagina = 50** (reduced from 500 in Feb 2026)
- tamanhoPagina > 50 → HTTP 400 (silent, no error message)
- Search period default: 10 days (frontend + backend)
- Phased UF batching: PNCP_BATCH_SIZE=5, PNCP_BATCH_DELAY_S=2.0
- Retry: exponential backoff, HTTP 422 is retryable (max 1 retry)
- Circuit breaker: 15 failures threshold (was 50), 60s cooldown (was 120s)

**Railway/Gunicorn Critical Notes (GTM-INFRA-001):**
- **Railway hard timeout: ~120s** — requests exceeding this are killed by Railway proxy
- Gunicorn timeout: 180s (above Railway's 120s but realistic for worker cleanup)
- Sync PNCPClient fallback wrapped in `asyncio.to_thread()` — never blocks event loop
- `start.sh` timeout default: 180s (env var `GUNICORN_TIMEOUT` overrides)

### AIOS Framework Integration

This project uses the AIOS Framework for AI-orchestrated development:

**Available Agents:**
- `@dev` - Development and implementation
- `@qa` - Quality assurance and testing
- `@architect` - Architectural decisions
- `@pm` - Story management
- `@devops` - Infrastructure and GitHub operations

**AIOS Commands:**
- `/AIOS/story` - Create new story
- `/AIOS/review` - Code review
- `/AIOS/docs` - Generate documentation
- See `.aios-core/user-guide.md` for complete command list

**MCP Usage Rules:**
- Native Claude Code tools (Read, Write, Edit, Bash, Glob, Grep) take priority
- Docker gateway (desktop-commander) only for Docker operations
- Playwright for browser automation only
- See `.claude/rules/mcp-usage.md` for detailed rules

### Proactive Agent & Script Invocation

**CRITICAL:** Claude should PROACTIVELY invoke appropriate agents, tasks, and scripts from `.aios-core/development/` based on the user's context and needs. Do NOT wait for explicit user requests.

#### When to Invoke Agents Proactively

| Situation | Agent(s) | Action |
|-----------|----------|--------|
| User describes new feature/requirement | `@pm` or `@po` | Create story with proper acceptance criteria |
| User asks architectural questions | `@architect` | Analyze design patterns, provide technical guidance |
| Code implementation needed | `@dev` | Implement features following project standards |
| Tests needed or test failures | `@qa` | Create test suites, debug failures |
| Docker/CI/CD/GitHub operations | `@devops` | Handle infrastructure tasks |
| Data modeling or database work | `@data-engineer` | Design schemas, migrations, queries |
| UX/UI design questions | `@ux-design-expert` | Design patterns, accessibility, user flows |
| Process/workflow questions | `@sm` | Scrum ceremonies, sprint planning |
| Business requirements analysis | `@analyst` | Requirements elicitation, feasibility |
| Complex multi-agent tasks | `@aios-master` | Orchestrate multiple agents |

**Invocation Method:** Use the `Skill` tool with the agent name:
```
Skill(skill: "dev", args: "implement PNCP client retry logic")
```

#### When to Invoke Tasks Proactively

| Situation | Task | Location |
|-----------|------|----------|
| Creating new story | `create-story.md` or `create-next-story.md` | `.aios-core/development/tasks/` |
| Brownfield analysis needed | `analyze-brownfield.md` | `.aios-core/development/tasks/` |
| Code review requested | `review-code.md` | Available via `/AIOS/review` |
| Component creation | `build-component.md` | `.aios-core/development/tasks/` |
| Database migration | `db-apply-migration.md` | `.aios-core/development/tasks/` |
| Performance analysis | `analyze-performance.md` | `.aios-core/development/tasks/` |
| Codebase audit | `audit-codebase.md` | `.aios-core/development/tasks/` |
| CI/CD setup | `ci-cd-configuration.md` | `.aios-core/development/tasks/` |
| Documentation needed | `create-doc.md` | `.aios-core/development/tasks/` |
| Architectural impact analysis | `architect-analyze-impact.md` | `.aios-core/development/tasks/` |

**Task Execution:** Load the task Markdown file and follow its workflow instructions:
```bash
node .aios-core/development/scripts/story-manager.js create-story --title "Feature X"
```

#### When to Invoke Scripts Proactively

| Situation | Script | Purpose |
|-----------|--------|---------|
| Loading agent configuration | `agent-config-loader.js` | Parse agent definitions |
| Story management operations | `story-manager.js` | Create, update, sync stories |
| Recording architectural decisions | `decision-recorder.js` | Log ADRs and decisions |
| Building agent greetings | `greeting-builder.js` | Context-aware agent initialization |
| Workflow navigation | `workflow-navigator.js` | Multi-step process guidance |
| Task validation | `validate-task-v2.js` | Validate story/task structure |
| Backlog management | `backlog-manager.js` | Prioritize and organize work |
| Squad operations | `squad/squad-generator.js` | Create multi-agent teams |

**Script Invocation:** Use Bash tool to execute Node.js scripts:
```bash
node .aios-core/development/scripts/story-manager.js --action create
```

#### When to Invoke Workflows Proactively

| Situation | Workflow | Location |
|-----------|----------|----------|
| New full-stack project | `greenfield-fullstack.yaml` | `.aios-core/development/workflows/` |
| New backend service | `greenfield-service.yaml` | `.aios-core/development/workflows/` |
| New frontend project | `greenfield-ui.yaml` | `.aios-core/development/workflows/` |
| Enhancing existing full-stack | `brownfield-fullstack.yaml` | `.aios-core/development/workflows/` |
| Enhancing existing backend | `brownfield-service.yaml` | `.aios-core/development/workflows/` |
| Enhancing existing frontend | `brownfield-ui.yaml` | `.aios-core/development/workflows/` |

**BidIQ-Specific Workflows (PREFER THESE for this project):**

| User Says / Context | Workflow | Agents |
|---------------------|----------|--------|
| "integrate X API" / "connect to external service" / new API client | `bidiq-api-integration.yaml` | architect → dev → qa |
| "add feature X" / full-stack feature / backend + frontend | `bidiq-feature-e2e.yaml` | pm → architect → dev → qa → devops |
| "bug in X" / "X is broken" / "fix X" / production issue | `bidiq-hotfix.yaml` | dev → qa → devops |
| "add filter" / "new report" / "Excel changes" / data pipeline | `bidiq-data-pipeline.yaml` | data-engineer → architect → dev → qa |
| "improve prompt" / "LLM output is wrong" / "add AI summary" | `bidiq-llm-prompt.yaml` | analyst → dev → qa |
| "deploy" / "release" / "push to production" | `bidiq-deploy-release.yaml` | qa → devops |
| "start sprint" / "what should we work on next" / "plan work" | `bidiq-sprint-kickoff.yaml` | pm → po → sm → architect → dev |
| "slow" / "performance" / "timeout" / "optimize" | `bidiq-performance-audit.yaml` | architect → dev → qa |
| "audit codebase" / "technical debt" / "migration" | `brownfield-discovery.yaml` | architect → data-engineer → ux → qa → analyst → pm |

**This project is BROWNFIELD** - use brownfield and BidIQ-specific workflows for enhancements.

**PROACTIVE RULE:** When the user describes a task, AUTOMATICALLY select and follow the matching BidIQ workflow without waiting for explicit invocation. Read the workflow YAML, then execute its sequence step by step using the appropriate agents.

#### Agent Team Configurations

For complex multi-agent operations, use pre-configured teams from `.aios-core/development/agent-teams/`:

| Team | Use Case | File |
|------|----------|------|
| Full Team | Complex features requiring all roles | `team-all.yaml` |
| Full-Stack | Backend + Frontend + QA + DevOps | `team-fullstack.yaml` |
| Backend Only | API/service development | `team-no-ui.yaml` |
| Quality Focus | Bug fixes, testing, refactoring | `team-qa-focused.yaml` |
| Minimal | Quick fixes, single-component work | `team-ide-minimal.yaml` |

#### Script Usage Patterns

**Story Management:**
```bash
# Create new story
node .aios-core/development/scripts/story-manager.js create --title "Add pagination"

# Update story status
node .aios-core/development/scripts/story-manager.js update --id STORY-001 --status completed
```

**Decision Recording:**
```bash
# Record architectural decision
node .aios-core/development/scripts/decision-recorder.js \
  --type architecture \
  --title "Use Redis for caching" \
  --rationale "Improve response time for frequently accessed data"
```

**Squad Management:**
```bash
# Create specialized squad
node .aios-core/development/scripts/squad/squad-generator.js \
  --agents dev,qa,architect \
  --task "Implement PNCP client resilience"
```

#### Key Principles

1. **Anticipate Needs:** Don't wait for explicit agent requests - invoke based on context
2. **Use Right Tool:** Choose agent/task/script based on specific need
3. **Chain Operations:** Multiple agents may be needed sequentially
4. **Document Decisions:** Use decision-recorder.js for architectural choices
5. **Follow Workflows:** Use brownfield workflows for this existing project
6. **Validate Work:** Always involve @qa for quality assurance
7. **Team Collaboration:** Use team configs for complex multi-role tasks

#### Task Categories Reference

**Story Management:** create-story, create-next-story, validate-story, sync-story
**Code Operations:** review-code, refactor, audit-codebase, cleanup-utilities
**Component Building:** build-component, compose-molecule, bootstrap-shadcn-library
**Database:** db-apply-migration, db-domain-modeling, db-schema-audit, db-rollback
**Testing:** apply-qa-fixes, create-suite, analyze-framework
**Documentation:** create-doc, update-readme, document-api
**Architecture:** architect-analyze-impact, analyze-brownfield, consolidate-patterns
**DevOps:** ci-cd-configuration, add-mcp, db-env-check
**Performance:** analyze-performance, db-analyze-hotpaths, db-explain
**Process:** correct-course, collaborative-edit, handoff, execute-checklist

See `.aios-core/development/tasks/` for complete list (115+ tasks available).

## Critical Implementation Notes

### 1. Data Source Resilience

**PNCP (Primary):**
- Max `tamanhoPagina` = 50 (API silently changed, >50 → HTTP 400)
- ALWAYS use retry with exponential backoff + circuit breaker
- Respect 429 rate limits (`Retry-After` header)
- HTTP 422 is retryable (max 1 retry, log body[:500])
- Phased UF batching: 5 UFs per batch, 2s delay between batches
- Health canary uses `tamanhoPagina=10` — doesn't detect page size limits

**PCP v2 (Secondary):**
- No auth required (fully public v2 API)
- Fixed 10/page pagination (`pageCount`/`nextPage`)
- Client-side UF filtering only (no server-side UF param)
- `valor_estimado=0.0` (v2 has no value data)

**ComprasGov v3 (Tertiary):**
- Dual-endpoint: legacy + Lei 14.133
- Base URL: `dadosabertos.compras.gov.br`

### 2. Filtering Pipeline

Order matters (fail-fast optimization):
1. UF check (fastest)
2. Value range check
3. Keyword matching (density scoring)
4. LLM zero-match classification (for 0% keyword density)
5. Status/date validation
6. Viability assessment (post-filter)

**Feature Flags:** `LLM_ZERO_MATCH_ENABLED`, `LLM_ARBITER_ENABLED`, `VIABILITY_ASSESSMENT_ENABLED`, `SYNONYM_MATCHING_ENABLED`

### 3. LLM Integration

- GPT-4.1-nano for classification + summaries
- Zero-match prompt: `_build_zero_match_prompt()` in `llm_arbiter.py`
- Fallback = REJECT on failure (zero noise philosophy)
- ARQ background jobs for summaries (immediate fallback response)
- ThreadPoolExecutor(max_workers=10) for parallel LLM calls

### 4. Cache Strategy

- L1 InMemoryCache: 4h TTL, hot/warm/cold priority
- L2 Supabase: 24h TTL, persistent
- Fresh (0-6h) → Stale (6-24h, served + background refresh) → Expired (>24h, not served)
- Patch `supabase_client.get_supabase` for cache tests (not `search_cache.get_supabase`)

### 5. Billing & Auth

- Stripe handles proration automatically — NO custom prorata code
- "Fail to last known plan": never fall back to free_trial on DB errors
- 3-day grace period for subscription gaps (`SUBSCRIPTION_GRACE_DAYS`)
- ALL Stripe webhook handlers sync `profiles.plan_type`
- Frontend localStorage plan cache (1hr TTL) prevents UI downgrades
- Tests mocking `/buscar` MUST also mock `check_and_increment_quota_atomic`

### 6. Type Safety

**Python:** Type hints on all functions, Pydantic for API contracts, pattern validation for dates
**TypeScript:** Interfaces over types, no `any`, strict null checks enabled

## Testing Strategy

### Backend Tests (backend/tests/)

**169 test files, 5131+ passing, 0 failures** (CRIT-036 baseline)

**Configuration:** `backend/pyproject.toml` (pytest + coverage settings, threshold: 70%)

**CI Gate:** `.github/workflows/backend-tests.yml` — pytest exit code 0 required for merge.

```bash
cd backend
pytest                           # Run all tests (must pass 100%)
pytest --cov                     # With coverage (enforces 70% threshold)
pytest -k "test_name"            # Run specific test
pytest tests/integration/        # Integration tests only
```

**Test Categories:**
- `tests/` — Unit tests (mock all external deps)
- `tests/integration/` — Integration tests (real pipeline, mock HTTP only)
- `tests/snapshots/` — OpenAPI schema drift detection

**Zero-Failure Policy:** 0 failures is the only acceptable baseline. If tests fail, fix them — never treat failures as "pre-existing".

**Key Testing Patterns:**
- Auth: Use `app.dependency_overrides[require_auth]` NOT `patch("routes.X.require_auth")`
- Cache: Patch `supabase_client.get_supabase` (not `search_cache.get_supabase`)
- Config: Use `@patch("config.FLAG_NAME", False)` not `os.environ`
- LLM: Mock at `@patch("llm_arbiter._get_client")` level
- Quota: Tests mocking `/buscar` MUST also mock `check_and_increment_quota_atomic`
- ARQ: Mock with `sys.modules["arq"]` (not installed locally)

### Frontend Tests (frontend/__tests__/)

**135 test files, 2681+ passing, 0 failures** (CRIT-037 baseline)

**Configuration:** `frontend/jest.config.js` + `frontend/jest.setup.js` (threshold: 60%)

**CI Gate:** `.github/workflows/frontend-tests.yml` — npm test exit code 0 required for merge.

```bash
cd frontend
npm test                  # Run all tests (must pass 100%)
npm run test:coverage     # With coverage
npm run test:ci           # CI mode (non-interactive)
```

**jest.setup.js polyfills:** `crypto.randomUUID` + `EventSource` (jsdom lacks both)

**Zero-Failure Policy:** 0 failures is the only acceptable baseline. If tests fail, fix them — never treat failures as "pre-existing".

### E2E Tests (Playwright)

**60 critical user flow tests** in `frontend/e2e-tests/`

```bash
npm run test:e2e          # Headless
npm run test:e2e:headed   # With browser
```

## Code Style & Standards

### Python

- Type hints required
- Docstrings for public functions (Google style)
- Use Pydantic for validation, not manual checks
- Structured logging (not print statements)
- f-strings for string formatting

**Example:**
```python
def filter_licitacao(
    licitacao: dict,
    ufs_selecionadas: set[str],
    valor_min: float = 50_000.0
) -> tuple[bool, str | None]:
    """
    Apply all filters to a bid.

    Returns:
        tuple: (approved: bool, rejection_reason: str | None)
    """
    ...
```

### TypeScript

- Explicit return types
- Interfaces over types
- React hooks with proper types
- JSDoc for exported functions

**Example:**
```typescript
interface Resumo {
  resumo_executivo: string;
  total_oportunidades: number;
  valor_total: number;
  destaques: string[];
}

async function buscarLicitacoes(
  ufs: string[],
  dataInicial: string,
  dataFinal: string
): Promise<BuscaResult> {
  ...
}
```

### Error Handling

**Backend:**
- Specific exception types (PNCPAPIError, PNCPRateLimitError)
- Log exceptions with context
- Return meaningful HTTP status codes

**Frontend:**
- Try-catch with user-friendly messages
- Loading states during async operations
- Error boundaries for component failures

## Common Development Tasks

### Adding a New Filter / Sector Keywords

1. Edit sector keywords in `backend/sectors_data.yaml` (not hardcoded in filter.py)
2. Update test_filter.py with new keyword coverage
3. Run `pytest -k test_filter` to verify no regressions
4. Run `node scripts/sync-setores-fallback.js --dry-run` if sector structure changed

### Modifying Excel Output

1. Update create_excel() in excel.py
2. Adjust column widths/styles as needed
3. Update example in PRD.md if structure changes
4. Test with various data sizes

### Changing LLM Prompt

1. Update system_prompt in llm.py
2. Adjust ResumoLicitacoes schema if output format changes
3. Update fallback logic to match new schema
4. Test with edge cases (0 bids, 100+ bids)

### Adding Environment Variables

1. Add to .env.example with documentation
2. Update config.py to load variable
3. Document in PRD.md section 10
4. Update README.md if user-facing

### Syncing Frontend Sector Fallback (STORY-170 AC15)

The frontend has a hardcoded fallback list of sectors that should be kept in sync with the backend's sector definitions.

**When to run:**
- Monthly (recommended)
- After adding new sectors to backend
- Before major releases

**How to run:**
```bash
# Dry run (preview changes without modifying files)
node scripts/sync-setores-fallback.js --dry-run

# Apply changes
node scripts/sync-setores-fallback.js

# Use custom backend URL
node scripts/sync-setores-fallback.js --backend-url https://api.smartlic.tech

# Test the script
bash scripts/test-sync-setores.sh
```

**What it does:**
1. Fetches sectors from backend `/setores` endpoint
2. Validates sector data structure (id, name, description)
3. Compares current frontend fallback vs new backend data
4. Updates `frontend/app/buscar/page.tsx` with new `SETORES_FALLBACK` list
5. Reports added, removed, and unchanged sectors

**Files involved:**
- `scripts/sync-setores-fallback.js` - Sync script
- `scripts/README-sync-setores.md` - Documentation
- `scripts/test-sync-setores.sh` - Test script
- `frontend/app/buscar/page.tsx` - Contains `SETORES_FALLBACK` constant
- `backend/sectors.py` - Source of truth for sector definitions

## Project Status & Roadmap

**Current State (v0.5 — POC Avançado):**
- Production at https://smartlic.tech (Railway)
- 65+ backend modules, 22 frontend pages, 49 API endpoints
- 15 setores com keywords e viability ranges
- Multi-source pipeline (PNCP + PCP v2 + ComprasGov v3)
- LLM classification + viability assessment
- Stripe billing (SmartLic Pro R$1.999 + trial 7 dias)
- Two-level cache with SWR + hot/warm/cold priority
- ARQ job queue for LLM + Excel background processing
- Prometheus metrics + OpenTelemetry tracing + Sentry errors
- 304+ test files (169 backend + 135 frontend + E2E)
- 42 database migrations (35 Supabase + 7 backend)

**Estágio comercial:** Beta com trials, pré-revenue.

**See `ROADMAP.md` for current backlog and priorities.**

**Development Process:**
1. Activate squad: `/bidiq backend`, `/bidiq frontend`, or `/bidiq feature`
2. Create/select story from `docs/stories/`
3. Use squad agents for design, implementation, testing
4. Automated quality gates enforce coverage thresholds
5. Deploy via Railway (`railway up`)

## Security Notes

- Supabase Auth with RLS (Row-Level Security) on all tables
- Input validation via Pydantic (backend) and form validation (frontend)
- CORS configurable via `CORS_ORIGINS` env var
- API keys in environment variables only (never commit)
- Log sanitization via `log_sanitizer.py`
- Redis token bucket rate limiting
- Stripe webhook signature verification
- Admin endpoints require `is_admin` or `is_master` role check

## Important Files

**Documentation:**
- `PRD.md` - Product requirements and technical specification
- `ROADMAP.md` - Project roadmap and current backlog
- `CHANGELOG.md` - Detailed changelog (accurate and comprehensive)
- `docs/framework/tech-stack.md` - Technology choices and versions
- `docs/framework/coding-standards.md` - Code style guide
- `docs/summaries/gtm-resilience-summary.md` - Resilience architecture reference (654 lines)
- `docs/summaries/gtm-fixes-summary.md` - Production fixes reference (667 lines)
- `.aios-core/user-guide.md` - AIOS framework documentation

**Configuration:**
- `.env.example` - Environment variable template (70+ vars documented)
- `backend/requirements.txt` - Python dependencies (32 production packages)
- `frontend/package.json` - Node.js dependencies (46 total packages)
- `backend/sectors_data.yaml` - 15 sector definitions (keywords, exclusions, value ranges)
- `backend/config.py` - All env var loading with defaults
- `.claude/rules/mcp-usage.md` - MCP server usage rules

**Database:**
- `supabase/migrations/` - 35 Supabase migrations
- `backend/migrations/` - 7 backend-specific migrations

**AIOS Development Resources:**
- `.aios-core/development/agents/` - 11 agent definitions (dev, qa, architect, etc.)
- `.aios-core/development/tasks/` - 115+ task definitions for workflows
- `.aios-core/development/scripts/` - 24 supporting scripts
- `.aios-core/development/workflows/` - 7 multi-step workflow definitions
- `.aios-core/development/agent-teams/` - 5 pre-configured team compositions

## Git Workflow

**Branches:**
- `main` - Production/stable
- `develop` - Development (not yet created)
- `feature/*` - New features
- `fix/*` - Bug fixes

**Commits:**
Use conventional commits:
- `feat(backend): add retry logic to PNCP client`
- `fix(frontend): correct UF selection validation`
- `docs: update CLAUDE.md with testing guidelines`
- `chore: update dependencies`

**Before Committing:**
- Run tests (pytest for backend, npm test for frontend)
- Check linting if configured
- Update relevant documentation
- Follow co-authoring convention from README if using AI assistance
- Migration CI guard (`migration-check.yml`) checks that all local migrations in `supabase/migrations/` are applied to production on every PR touching that path and before every deploy. Requires GitHub secrets: `SUPABASE_ACCESS_TOKEN` and `SUPABASE_PROJECT_REF`.

---

**Note:** SmartLic is a POC avançado (v0.5) in production at smartlic.tech. The codebase is extensive (65+ backend modules, 22 pages, 304+ tests). For detailed architecture references, see `docs/summaries/gtm-resilience-summary.md` and `docs/summaries/gtm-fixes-summary.md`.
