# D10+D11: Security & Infrastructure Assessment

## Score: D10 (Security & LGPD): 7/10
## Score: D11 (Infrastructure Resilience): 6/10

---

## D10: Security & LGPD

### Security Checklist

| Item | Status | Evidence |
|------|--------|----------|
| **Authentication** | PASS | Supabase JWT with local validation, ES256+JWKS+HS256 fallback (`auth.py` L106-153). 60s token cache with SHA256 full-token hashing (`auth.py` L245-246). |
| **Authorization** | PASS (partial) | `require_auth` dependency (`auth.py` L327-336), `require_admin` guard (`admin.py`), RLS on Supabase tables. BUT: RLS policy gaps documented (see `BACKEND-DEBUG-REPORT-2026-02-10.md` -- `search_sessions` table had missing service role RLS policy). |
| **CORS configuration** | PASS | Not wildcard. Explicit allowlist in `config.py` L411-511. Wildcard "*" explicitly rejected with warning (L489-494). Production origins hardcoded: Railway URLs + smartlic.tech (L418-423). |
| **API docs in production** | PASS | Disabled when `ENVIRONMENT=production` (`main.py` L73-76, L211-213): `docs_url=None`, `redoc_url=None`, `openapi_url=None`. |
| **Webhook signature validation** | PASS | `stripe.Webhook.construct_event()` validates every webhook (`webhooks/stripe.py` L90-99). Missing signature header rejected with 400 (L85-87). |
| **Input validation (Pydantic)** | PASS | All endpoints use Pydantic models (`schemas.py`, 1000+ lines). `BuscaRequest` has field validators for UF codes, date patterns, and sector IDs. `validate_password()` enforces password policy. |
| **Security headers (Backend)** | PASS | `SecurityHeadersMiddleware` (`middleware.py` L133-152): X-Content-Type-Options, X-Frame-Options DENY, X-XSS-Protection, Referrer-Policy, Permissions-Policy. |
| **Security headers (Frontend)** | PASS | `next.config.js` L23-69: All same headers PLUS `Strict-Transport-Security` (HSTS 1yr) and `Content-Security-Policy` with restrictive directives. |
| **PII masking in logs** | PASS | Comprehensive `log_sanitizer.py` (606 lines): masks emails, tokens, API keys, user IDs, IPs, passwords, phone numbers. `SanitizedLogAdapter` auto-sanitizes. Sentry `scrub_pii` callback (`main.py` L81-122). |
| **Debug logs suppressed in prod** | PASS | `config.py` L98-103: DEBUG elevated to INFO in production. `log_sanitizer.py` L455-457: DEBUG calls skipped entirely in production. |
| **Secrets in frontend code** | PASS | Grep for `sk-`, `api_key`, `password`, `secret` in frontend TS/TSX found ZERO hardcoded secrets. Only UI form password fields and test fixtures with dummy values. |
| **Secrets in `.gitignore`** | PASS | `.env`, `.env.*`, `.env.local`, `backend/.env*`, `frontend/.env*` all gitignored (`.gitignore` L101-108, L360-367). |
| **Secret scanning (CI)** | PASS | TruffleHog runs on PRs (`codeql.yml` L63-81). GitHub dependency-review blocks high-severity CVEs (L83-96). |
| **Rate limiting on password change** | PASS | 5 attempts per 15 minutes per user (`routes/user.py` L44-70). In-memory tracking with pruning. |
| **Rate limiting on search** | PASS | Per-user per-minute rate limiting via `rate_limiter.py` (Redis + in-memory fallback). Enforced in `routes/search.py` L176. |
| **Rate limiting on checkout** | FAIL | No rate limiting on `POST /checkout` (`routes/billing.py` L33-79). Anyone authenticated can spam Stripe Checkout session creation. |
| **Rate limiting on auth endpoints** | N/A | Auth handled by Supabase Auth (external service). Supabase has its own rate limits. |
| **Env var validation at startup** | PASS | `validate_env_vars()` (`config.py` L514-538): checks SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET. Raises `RuntimeError` in production if missing. Warns on missing OPENAI_API_KEY, STRIPE_SECRET_KEY, SENTRY_DSN. |
| **Token cache collision prevention** | PASS | Fixed CVSS 9.1 vulnerability (STORY-210 AC3). Now hashes full JWT with SHA256 (`auth.py` L243-245), not just first 16 chars. |
| **Correlation IDs** | PASS | `CorrelationIDMiddleware` (`middleware.py` L29-70): generates UUID per request, propagates via `X-Request-ID` header and context variable. |
| **Structured logging** | PASS | JSON structured logging in production (`config.py` L118-129) via `python-json-logger`. Includes timestamp, level, module, funcName, lineno, request_id. |
| **CSP (Content-Security-Policy)** | PARTIAL | Frontend has CSP (`next.config.js` L53-64), but uses `'unsafe-inline'` and `'unsafe-eval'` in script-src. Necessary for Next.js hydration, but weakens XSS protection. Mixpanel connect-src NOT whitelisted -- analytics calls may be blocked by CSP. |

### LGPD Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **Cookie consent banner** | PASS | `CookieConsentBanner.tsx` (119 lines): binary accept-all/reject-non-essential. Uses localStorage key `bidiq_cookie_consent`. Dispatches `cookie-consent-changed` CustomEvent for AnalyticsProvider to listen to. |
| **Cookie consent granularity** | PARTIAL | Only binary toggle (analytics yes/no). Does not offer per-cookie granular control. Sufficient for current scope (only Mixpanel analytics cookies). |
| **Privacy policy page** | PASS | `privacidade/page.tsx` (223 lines): 12 comprehensive sections covering data collection, usage, sharing, security, LGPD rights, cookies, retention, international transfers, minors, DPO contact. Last updated 2026-02-13. |
| **DPO contact** | PASS | Listed as `privacidade@smartlic.tech` (L198). ANPD reference included (L202-205). |
| **LGPD rights (Art. 18)** | PASS | All 7 rights listed (access, correction, anonymization, deletion, portability, consent revocation, opposition) in section 6 (L120-129). |
| **Data deletion capability** | PASS | `DELETE /me` endpoint exists (`routes/user.py` STORY-213). Account deletion route documented in privacy policy (L131-135). |
| **Data export/portability** | PASS | `GET /me/export` endpoint exists (`routes/user.py` STORY-213). |
| **Consent at signup** | PASS | `signup/page.tsx` includes terms/consent checkbox (confirmed by E2E tests `signup-consent.spec.ts`). |
| **Terms of service page** | PASS | `termos/page.tsx` exists (found via glob). |
| **Analytics consent-gated** | PASS | `AnalyticsProvider.tsx` respects cookie consent before initializing Mixpanel. Verified by cookie consent event listener pattern. |
| **"Manage Cookies" link** | PASS | Footer includes "Gerenciar Cookies" link that dispatches `manage-cookies` event, re-showing consent banner (`CookieConsentBanner.tsx` L55-61). |
| **Data retention policy** | PASS | Privacy policy states 24-month inactivity threshold for anonymization/deletion (section 8, L157-160). |

### Critical Security Gaps

| # | Gap | Severity | Fix | Effort |
|---|-----|----------|-----|--------|
| S1 | **`checkout.session.completed` webhook NOT handled** | P0 CRITICAL | After Stripe Checkout, no webhook creates the local subscription. `_activate_plan()` exists (`billing.py` L82-113) but is NEVER CALLED. Users pay but don't get activated. | 2h |
| S2 | **`invoice.payment_failed` webhook NOT handled** | P1 HIGH | Failed renewal payments are invisible. Subscription stays active even when payment fails. Users get free service after card expiry. | 2h |
| S3 | **No rate limiting on `/checkout`** | P2 MEDIUM | Authenticated user can spam Stripe Checkout sessions. Stripe has its own limits, but this wastes API calls and could generate costs. | 1h |
| S4 | **CSP allows `unsafe-eval` + `unsafe-inline`** | P3 LOW | Required by Next.js runtime. Acceptable tradeoff for current stage. Could be tightened with nonce-based CSP in future. | 4h |
| S5 | **CSP missing Mixpanel connect-src** | P2 MEDIUM | `api-js.mixpanel.com` not in CSP connect-src. Analytics calls may be silently blocked by browser. | 15min |
| S6 | **Backend missing HSTS header** | P3 LOW | Frontend has HSTS via `next.config.js`, but backend API responses lack `Strict-Transport-Security`. Railway handles TLS termination, so impact is low. | 15min |
| S7 | **Backend missing CSP header** | P3 LOW | `SecurityHeadersMiddleware` does not include CSP. API-only backend with no HTML rendering, so risk is minimal. | 30min |

---

## D11: Infrastructure Resilience

### Infrastructure Profile

| Dimension | Value |
|-----------|-------|
| **Hosting** | Railway (backend + frontend, separate services) |
| **Database** | Supabase (PostgreSQL, managed) |
| **Cache** | Redis (Railway or external, optional -- graceful fallback if unavailable) |
| **CDN** | None explicitly configured. Railway provides edge routing. |
| **Domain** | `smartlic.tech` (custom domain) |
| **TLS** | Railway auto-managed (Let's Encrypt) |
| **Container Runtime** | Docker (Python 3.11-slim for backend, Node 20-alpine for frontend) |
| **Expected concurrent users** | Low -- POC/early-stage. Estimated 10-50 concurrent during launch. |
| **Known bottlenecks** | PNCP API rate limiting (10 req/s), circuit breaker cascade, 500-page pagination cap |
| **Cold start time** | ~10-15s (Python image, dependency loading, Supabase/Redis init, JWKS fetch) |
| **Auto-scaling** | NO. Railway Hobby plan does NOT auto-scale. Single instance per service. |

### Infrastructure Checklist

| Item | Status | Evidence |
|------|--------|----------|
| **Health check endpoint** | PASS | `GET /health` (`main.py` L327-412): checks Supabase, OpenAI, Redis, circuit breaker, per-source health. Returns 200 always (to prevent Railway startup block). Status in body. |
| **Health check integration** | PASS | `railway.toml` backend: `healthcheckPath = "/health"`, `healthcheckTimeout = 120` (L16-17). Frontend: `healthcheckPath = "/api/health"` (L14). |
| **Restart policy** | PASS | `restartPolicyType = "ON_FAILURE"`, `restartPolicyMaxRetries = 3` in both `railway.toml` files. |
| **Non-root container** | PARTIAL | Frontend Dockerfile creates `nextjs` user (UID 1001) and switches to it (L87-97). Backend Dockerfile runs as root (no USER directive in `backend/Dockerfile`). |
| **Multi-stage builds** | PARTIAL | Frontend uses 3-stage build (deps, builder, runner) for minimal image. Backend is single-stage (includes gcc build tools in production image). |
| **Dependency pinning** | PASS | `backend/requirements.txt` pins all major deps (fastapi==0.129.0, httpx==0.28.1, etc.). Some use ranges (resend>=2.0.0,<3.0.0). Frontend uses `package-lock.json` with `npm ci`. |
| **Vulnerability scanning** | PASS | Backend CI runs `safety check` for Python CVEs (`backend-ci.yml` L38-42). Frontend CI runs `npm audit` (`tests.yml` L122-130). CodeQL weekly scan for Python+JS (`codeql.yml`). |
| **CI/CD pipeline** | PASS | Multiple workflows: `deploy.yml` (production deploy with health checks and smoke tests), `backend-ci.yml` (lint, type check, safety, tests), `tests.yml` (backend + frontend + integration + E2E), `codeql.yml` (security), `e2e.yml`. |
| **Deploy health verification** | PASS | `deploy.yml` includes post-deploy health checks (5 attempts, 15s apart) and smoke tests (root, health, buscar endpoints). |
| **Error tracking** | PARTIAL | Sentry SDK integrated in both backend (`main.py` L77-137) and frontend (`next.config.js` L73-94). BUT: SENTRY_DSN not configured in production (per MEMORY.md assessment: "Sentry DSN not configured"). Code 9/10, deployment 5/10. |
| **Analytics/observability** | PARTIAL | Mixpanel integrated (`AnalyticsProvider.tsx`) BUT token not set in production (per MEMORY.md: "Mixpanel token not set -- zero analytics data"). JSON structured logging is well-implemented. |
| **Redis graceful fallback** | PASS | `rate_limiter.py` falls back to in-memory dict if Redis unavailable. `progress.py` supports both Redis pub/sub and in-memory queues. `redis_pool.py` uses connection pooling with graceful degradation. |
| **Database connection pooling** | PASS | Supabase handles connection pooling server-side (PgBouncer built into Supabase). Backend uses `supabase-py` client which reuses HTTP connections. |
| **PNCP circuit breaker** | PASS | Circuit breaker pattern implemented (`pncp_client.py`). Health endpoint reports circuit breaker status (`main.py` L386-387). |
| **Concurrent request handling** | PARTIAL | Uvicorn single-worker (`CMD uvicorn main:app`, Dockerfile L41). No `--workers` flag. Single-threaded async. Adequate for POC load but will bottleneck under concurrent heavy searches. |
| **Graceful shutdown** | PASS | Lifespan context manager (`main.py` L170-199): startup initializes Redis, shutdown closes Redis pool. |
| **Environment documentation** | PASS | `.env.example` (175 lines) documents all env vars with descriptions and defaults. `validate_env_vars()` checks critical vars at startup. |
| **Secrets management** | PASS | All secrets via env vars (Railway dashboard). No secrets in code or Docker images. `.gitignore` covers all `.env` variants. |
| **Backup/DR** | DELEGATED | Supabase handles database backups (daily point-in-time recovery on Pro plan). No additional backup strategy documented for Railway services (stateless by design). |

### CI/CD Workflow Summary

| Workflow | Trigger | Purpose | Quality Gates |
|----------|---------|---------|---------------|
| `tests.yml` | Push/PR to main | Backend tests (3.11+3.12), frontend tests, integration, E2E | Coverage >= 70% backend, TypeScript check, API types committed |
| `backend-ci.yml` | Push/PR to main, backend changes | Linting, type checking, security scan, tests | ruff, mypy, safety, pytest --cov-fail-under=70 |
| `deploy.yml` | Push to main (backend/frontend changes) | Railway deployment | Health checks (5 retries), smoke tests (health, root, buscar) |
| `codeql.yml` | Push/PR to main, weekly schedule | Security analysis | CodeQL (Python+JS), TruffleHog secret scanning, dependency review |
| `e2e.yml` | Push/PR | Playwright E2E tests | Chromium + Mobile Safari, 60 critical flow tests |
| `lighthouse.yml` | Exists | Performance auditing | Not investigated in detail |
| `pr-validation.yml` | PRs | PR validation | Not investigated in detail |

### Critical Infrastructure Gaps

| # | Gap | Severity | Fix | Effort |
|---|-----|----------|-----|--------|
| I1 | **Sentry DSN not configured in production** | P1 HIGH | Set `SENTRY_DSN` env var in Railway. Code is ready, just needs the DSN value from sentry.io project. Zero error visibility in production without this. | 15min |
| I2 | **Mixpanel token not set in production** | P1 HIGH | Set `NEXT_PUBLIC_MIXPANEL_TOKEN` in Railway frontend build args. Zero product analytics data without this. | 15min |
| I3 | **Single Uvicorn worker** | P2 MEDIUM | Backend runs single async worker. Under concurrent heavy search requests (PNCP calls take 10-30s), the event loop may saturate. Add `--workers 2-4` or use gunicorn with uvicorn workers. | 30min |
| I4 | **Backend container runs as root** | P2 MEDIUM | `backend/Dockerfile` lacks USER directive. Container compromise gives root access. Frontend properly uses non-root user. | 15min |
| I5 | **No auto-scaling** | P2 MEDIUM | Railway Hobby plan is single-instance. No horizontal scaling. Acceptable for POC launch but will need Pro plan for growth. | Upgrade plan |
| I6 | **Backend Dockerfile single-stage** | P3 LOW | Includes gcc build tools in production image. Multi-stage build would reduce image size and attack surface. | 1h |
| I7 | **No CDN for static assets** | P3 LOW | Frontend static assets served directly from Railway. No Cloudflare/CloudFront CDN. Acceptable for Brazil-focused audience. | 2h |
| I8 | **deploy.yml smoke test checks /docs** | P3 LOW | Smoke test at L208 checks `curl "${BACKEND_URL}/docs"` expecting 200, but production disables docs (returns 404/None). This smoke test will fail in production. | 15min |

---

## Combined Risk Matrix

### P0 -- Must Fix Before Launch

| ID | Area | Issue | Impact |
|----|------|-------|--------|
| S1 | Security | `checkout.session.completed` webhook not handled | **Users pay but never get activated.** `_activate_plan()` function exists at `billing.py:82` but is dead code. |
| S2 | Security | `invoice.payment_failed` webhook not handled | Failed payments are invisible. Subscriptions remain active indefinitely after card failure. |

### P1 -- Fix Within 48h of Launch

| ID | Area | Issue | Impact |
|----|------|-------|--------|
| I1 | Infra | Sentry DSN not configured | Zero error visibility in production. Bugs will go unnoticed. |
| I2 | Infra | Mixpanel token not set | Zero product analytics. Cannot measure funnel, retention, feature usage. |

### P2 -- Fix Within 1 Week

| ID | Area | Issue | Impact |
|----|------|-------|--------|
| S3 | Security | No rate limit on `/checkout` | Abuse vector for Stripe API cost inflation. |
| S5 | Security | CSP missing Mixpanel domain | Analytics may be silently blocked by browsers. |
| I3 | Infra | Single Uvicorn worker | Event loop saturation under concurrent searches. |
| I4 | Infra | Backend runs as root | Container security best practice violation. |
| I5 | Infra | No auto-scaling | Single instance bottleneck under load. |

### P3 -- Backlog

| ID | Area | Issue | Impact |
|----|------|-------|--------|
| S4 | Security | CSP allows unsafe-eval/unsafe-inline | Required by Next.js. Low practical risk. |
| S6 | Security | Backend missing HSTS | TLS termination at Railway edge. Low risk. |
| S7 | Security | Backend missing CSP | API-only, no HTML. Minimal risk. |
| I6 | Infra | Backend single-stage Docker build | Larger image size, but functional. |
| I7 | Infra | No CDN | Acceptable for Brazil-focused audience. |
| I8 | Infra | Smoke test checks disabled `/docs` | Will cause false-negative in CI. |

---

## Evidence References

### Security

- **Auth module**: `backend/auth.py` (350 lines) -- JWT validation with ES256+JWKS+HS256, token cache, full-token SHA256 hashing
- **Log sanitizer**: `backend/log_sanitizer.py` (606 lines) -- PII masking for emails, tokens, IDs, IPs, passwords, phones
- **Middleware**: `backend/middleware.py` (153 lines) -- CorrelationID, SecurityHeaders, Deprecation middleware
- **Webhook handler**: `backend/webhooks/stripe.py` (440 lines) -- Signature validation, idempotency, audit trail
- **CORS config**: `backend/config.py` L411-511 -- Explicit allowlist, wildcard rejection
- **Rate limiter**: `backend/rate_limiter.py` (96 lines) -- Redis + in-memory fallback, per-user per-minute
- **Password rate limit**: `backend/routes/user.py` L44-70 -- 5 attempts per 15 minutes
- **Frontend security headers**: `frontend/next.config.js` L23-69 -- CSP, HSTS, X-Frame-Options, Permissions-Policy

### LGPD

- **Cookie consent**: `frontend/app/components/CookieConsentBanner.tsx` (119 lines)
- **Privacy policy**: `frontend/app/privacidade/page.tsx` (223 lines)
- **Terms of service**: `frontend/app/termos/page.tsx` (exists)
- **Account deletion**: `DELETE /me` in `routes/user.py` (STORY-213)
- **Data export**: `GET /me/export` in `routes/user.py` (STORY-213)

### Infrastructure

- **Backend Dockerfile**: `backend/Dockerfile` (42 lines) -- Python 3.11-slim, single-stage
- **Frontend Dockerfile**: `frontend/Dockerfile` (111 lines) -- Node 20-alpine, 3-stage, non-root user
- **Backend Railway config**: `backend/railway.toml` -- healthcheck, restart policy
- **Frontend Railway config**: `frontend/railway.toml` -- healthcheck, restart policy
- **Deploy workflow**: `.github/workflows/deploy.yml` (254 lines) -- Railway CLI deploy with health checks
- **CI workflow**: `.github/workflows/tests.yml` (412 lines) -- Backend, frontend, integration, E2E
- **Security workflow**: `.github/workflows/codeql.yml` (97 lines) -- CodeQL, TruffleHog, dependency review
- **Health endpoint**: `main.py` L327-412 -- Supabase, OpenAI, Redis, circuit breaker, source health
- **Sentry integration**: `main.py` L77-137 -- PII scrubbing callback, FastAPI+Starlette integrations

---

## Scoring Rationale

### D10: Security & LGPD -- 7/10

**Strengths (drives score up):**
- Excellent PII masking in logs (606-line log_sanitizer with SanitizedLogAdapter)
- Proper JWT validation with modern ES256+JWKS support and HS256 fallback
- Comprehensive security headers on both backend and frontend
- LGPD compliance is thorough: privacy policy, cookie consent, data deletion, data export, DPO contact
- Webhook signature validation prevents forged Stripe events
- Secret scanning in CI (TruffleHog + CodeQL)
- No hardcoded secrets in codebase

**Weaknesses (drives score down):**
- **P0 gap**: `checkout.session.completed` webhook not handled means paying customers never get activated (-2 points)
- **P0 gap**: `invoice.payment_failed` not handled means failed renewals are invisible (-1 point)
- Missing rate limit on checkout endpoint
- CSP has `unsafe-eval` (necessary evil for Next.js but still a weakness)

### D11: Infrastructure Resilience -- 6/10

**Strengths (drives score up):**
- Solid CI/CD pipeline with deploy health checks and smoke tests
- Health endpoint is comprehensive (Supabase, Redis, sources, circuit breaker)
- Graceful fallbacks everywhere (Redis, analytics, PNCP circuit breaker)
- Proper restart policies and health check configuration
- Multi-stage frontend Docker build with non-root user
- JSON structured logging ready for observability platforms

**Weaknesses (drives score down):**
- **Sentry not configured**: Zero error tracking in production despite code being ready (-2 points)
- **Mixpanel not configured**: Zero analytics despite code being ready (-1 point)
- Single Uvicorn worker (no concurrency headroom)
- Backend container runs as root
- No auto-scaling on Railway Hobby plan
- Single-stage backend Docker image includes build tools
