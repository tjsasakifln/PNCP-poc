# Tech Stack — SmartLic v0.5

## Backend (Python 3.12)

### Core Framework

| Componente | Tecnologia | Versao | Justificativa |
|------------|------------|--------|---------------|
| Framework | FastAPI | 0.129.0 | Performance, async, validacao automatica |
| Runtime | Python | 3.12 | Ecosystem rico, type hints avanados |
| Server (dev) | Uvicorn | 0.40.0 | ASGI server, hot-reload |
| Server (prod) | Gunicorn | 23.0.0 | Process management, graceful restart |
| Validacao | Pydantic | 2.12.5 | Type safety, structured outputs |
| Config | pydantic-settings | 2.10.1 | .env loading com validacao |

### HTTP & Data Sources

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| HTTP Client | httpx | 0.28.1 | Resilient HTTP, async support |
| HTTP Client (legacy) | requests | 2.32.3 | Backward compat |
| YAML Parser | PyYAML | >=6.0 | Sector config (sectors_data.yaml) |
| Excel | openpyxl | 3.1.5 | Planilhas formatadas |

### AI / LLM

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| OpenAI SDK | openai | 1.109.1 | GPT-4.1-nano classificacao + resumos |

### Database & Cache

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Database | Supabase | 2.13.0 | PostgreSQL + Auth + RLS + Storage |
| Cache/Queue | Redis | 5.3.1 | Cache L1, circuit breaker, job queue |
| Auth tokens | PyJWT | 2.9.0 | JWT validation |

### Billing & Payments

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Payments | Stripe | 11.4.1 | Subscriptions, webhooks, billing portal |

### Background Jobs

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Job Queue | ARQ | >=0.26 | LLM + Excel async processing |

### Monitoring & Observability

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Error tracking | Sentry | >=2.0.0 | FastAPI integration |
| Metrics | prometheus_client | >=0.20.0 | /metrics endpoint |
| Tracing (API) | opentelemetry-api | >=1.25 | Distributed tracing |
| Tracing (SDK) | opentelemetry-sdk | >=1.25 | Spans, exporters |
| Tracing (OTLP) | opentelemetry-exporter-otlp-proto-grpc | >=1.25 | OTLP export |
| Tracing (FastAPI) | opentelemetry-instrumentation-fastapi | >=0.46b0 | Auto-instrumentation |
| Tracing (httpx) | opentelemetry-instrumentation-httpx | >=0.46b0 | HTTP client tracing |
| Logging | python-json-logger | >=2.0.4 | Structured JSON logs |

### Google Integration

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Google API | google-api-python-client | 2.150.0 | Sheets export |
| Google Auth | google-auth + oauthlib | 2.35.0 | OAuth 2.0 |
| Crypto | cryptography | 43.0.3 | Token encryption |

### Email

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Transactional | Resend | >=2.0.0 | Welcome, quota, billing emails |

---

## Frontend (Node.js 18+)

### Core Framework

| Componente | Tecnologia | Versao | Justificativa |
|------------|------------|--------|---------------|
| Framework | Next.js | ^16.1.6 | App Router, SSR, API routes |
| Runtime | React | ^18.3.1 | Component model, hooks |
| Language | TypeScript | ^5.9.3 | Type safety |
| Styling | Tailwind CSS | ^3.4.19 | Utility-first, responsive |

### UI Libraries

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Icons | lucide-react | ^0.563.0 | Icon system |
| Animation | framer-motion | ^12.33.0 | Transitions, motion |
| Toast | sonner | ^2.0.7 | Notifications |
| Onboarding | shepherd.js | ^14.5.1 | Product tours |
| Progress bar | nprogress | ^0.2.0 | Navigation indicator |
| Charts | recharts | ^3.7.0 | Analytics dashboards |

### Date & DnD

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Dates | date-fns | ^4.1.0 | Date formatting |
| Date picker | react-day-picker | ^9.13.0 | Calendar UI |
| Drag & Drop | @dnd-kit/core + sortable | ^6.3.1 | Pipeline kanban |

### Auth & Data

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Auth (SSR) | @supabase/ssr | ^0.8.0 | Server-side auth |
| Supabase JS | @supabase/supabase-js | ^2.95.3 | Database client |
| UUID | uuid | ^13.0.0 | ID generation |
| Debounce | use-debounce | ^10.1.0 | Input debouncing |

### Monitoring

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Error tracking | @sentry/nextjs | ^10.38.0 | Frontend errors |
| Analytics | mixpanel-browser | ^2.74.0 | User analytics |

### Testing

| Componente | Tecnologia | Versao | Uso |
|------------|------------|--------|-----|
| Unit tests | Jest | ^29.7.0 | Component + hook tests |
| DOM testing | @testing-library/react | ^14.1.2 | React component testing |
| E2E tests | @playwright/test | ^1.58.2 | Browser automation |
| Accessibility | @axe-core/playwright | ^4.11.1 | a11y testing |
| Transpiler | @swc/jest | ^0.2.29 | Fast TypeScript compilation |
| Lighthouse | @lhci/cli | ^0.15.0 | Performance auditing |

---

## Infrastructure

| Componente | Servico | Uso |
|------------|---------|-----|
| Backend (web) | Railway | FastAPI server (PROCESS_TYPE=web) |
| Backend (worker) | Railway | ARQ job processor (PROCESS_TYPE=worker) |
| Frontend | Railway | Next.js SSR |
| Database | Supabase Cloud | PostgreSQL + Auth + RLS + Storage |
| Cache / Queue | Redis (Upstash/Railway) | InMemory L1, circuit breaker, ARQ |
| CI/CD | GitHub Actions | Tests + E2E + deploy |
| DNS | Cloudflare (or similar) | smartlic.tech domain |
| Payments | Stripe | Subscriptions, invoices, webhooks |
| Email | Resend | Transactional email delivery |
| Error tracking | Sentry | Backend + Frontend error monitoring |
| Metrics | Prometheus + Grafana | /metrics endpoint, dashboards |
| Tracing | OpenTelemetry (OTLP) | Distributed tracing |

## External APIs

| Servico | Endpoint | Prioridade | Auth |
|---------|----------|------------|------|
| PNCP | `pncp.gov.br/api/consulta/v1/contratacoes/publicacao` | 1 (primary) | None |
| PCP v2 | `compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` | 2 | None (public) |
| ComprasGov v3 | `dadosabertos.compras.gov.br` | 3 | None |
| OpenAI | `api.openai.com` | N/A | API Key |
| Stripe | `api.stripe.com` | N/A | Secret Key |
| Resend | `api.resend.com` | N/A | API Key |
| Google OAuth | `accounts.google.com` | N/A | Client ID/Secret |
