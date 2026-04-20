# Tech Stack — SmartLic

Versões exatas e características operacionais. Atualize se uma story mudar versão principal.

## Backend

| Componente | Versão | Uso |
|---|---|---|
| Python | 3.12 | Runtime |
| FastAPI | 0.129 | Framework web |
| Pydantic | v2 | Validação + schemas |
| httpx | latest | HTTP assíncrono |
| OpenAI SDK | latest | GPT-4.1-nano (classificação + resumos) |
| Supabase Python | latest | Client PostgreSQL + Auth + RLS |
| Redis | latest | Cache + circuit breaker + state |
| ARQ | latest | Async job queue |
| Stripe | latest | Billing |
| Resend | latest | Email transacional |
| Prometheus client | latest | Métricas |
| OpenTelemetry | latest | Tracing |
| Sentry SDK | latest | Error tracking |
| openpyxl | latest | Excel export |
| PyYAML | latest | Config loading |

## Frontend

| Componente | Versão | Uso |
|---|---|---|
| Next.js | 16 | App Router |
| React | 18 | UI |
| TypeScript | 5.9 | Type safety |
| Tailwind CSS | 3 | Styling |
| Framer Motion | latest | Animação |
| Recharts | latest | Gráficos |
| `@supabase/ssr` | latest | Auth SSR |
| Sentry | latest | Error tracking |
| Mixpanel | latest | Product analytics |
| `@dnd-kit` | latest | Drag-and-drop (pipeline) |
| Shepherd.js | latest | Onboarding tours |
| Jest + jsdom | latest | Unit tests |
| Playwright | latest | E2E tests |

## Database

| Componente | Versão/Config |
|---|---|
| PostgreSQL (Supabase) | 17 |
| pg_cron | habilitado (purge-old-bids, cleanup-search-cache, cleanup-search-store) |
| RLS | habilitado em TODAS as tabelas |

## Infra

| Componente | Notas |
|---|---|
| Railway (web + worker + frontend) | Proxy hard timeout ~120s. NÃO `railway up` de subdir — só raiz. Monorepo via `RAILWAY_SERVICE_ROOT_DIRECTORY`. Gunicorn timeout 180s. Keep-alive 75s. |
| Supabase Cloud | Auth + Postgres + Storage. Project ref em `.env` |
| Redis (Upstash/Railway) | Cache L1/L2, circuit breaker, token bucket rate limit |
| GitHub Actions | CI/CD. `backend-tests.yml`, `frontend-tests.yml`, `e2e.yml`, `migration-*.yml`, `api-types-check.yml`, `deploy.yml` |

## Thresholds CI

- Backend pytest coverage: **70%**
- Frontend jest coverage: **60%**
- Backend tests: **5131+ passing, 0 failures** (Zero-Failure Policy)
- Frontend tests: **2681+ passing, 0 failures**
- E2E: **60 critical flows**
- pytest timeout: **30s por test** (override com `@pytest.mark.timeout(60)`)
- pytest `timeout_method = "thread"` (Windows compat)

## Comandos úteis

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn main:app --reload --port 8000
pytest -k "test_name"                  # Safe: specific test
python scripts/run_tests_safe.py       # Full suite (Windows-safe, subprocess isolation)
pytest --timeout=30                    # Full suite direct (Linux CI)
pytest --cov

# Frontend
cd frontend && npm install
npm run dev
npm test
npm run test:e2e

# Type sync Pydantic → TypeScript
npm --prefix frontend run generate:api-types
```
