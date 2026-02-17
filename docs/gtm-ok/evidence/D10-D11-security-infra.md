# D10: Security & LGPD | D11: Infrastructure Resilience

**Assessment Date:** 2026-02-17
**Assessor:** @architect (Phase 6 - GTM-OK v2.0)
**Method:** Fresh codebase analysis (no prior D10/D11 evidence file existed)

---

## D10: Security & LGPD

### Score: 7/10 (Production-ready)

---

### 10.1 Authentication

**Mechanism:** Supabase Auth with local JWT verification (`backend/auth.py`)

| Aspect | Status | Evidence |
|--------|--------|----------|
| JWT verification | STRONG | Local decode via `jwt.decode()` with audience verification (`audience="authenticated"`) -- no remote API call needed (auth.py:267-273) |
| Algorithm support | STRONG | ES256 (JWKS) + HS256 (symmetric) with automatic fallback during rotation (auth.py:106-221) |
| JWKS key rotation | STRONG | PyJWKClient with 5-min cache TTL, lazy initialization (auth.py:58-98) |
| Token cache | STRONG | SHA-256 full-token hash with 60s TTL -- prevents identity collision (auth.py:244-245, CVSS 9.1 fix documented in AC3) |
| Token expiry handling | STRONG | Explicit `ExpiredSignatureError` catch with proper 401 response (auth.py:279-281) |
| Error sanitization | STRONG | Only exception *type* logged, never token content (auth.py:318-323) |
| `require_auth` dependency | GOOD | Clean Depends-based guard for protected endpoints (auth.py:327-336) |

**Frontend middleware** (`frontend/middleware.ts`):
- Uses `supabase.auth.getUser()` (server-validated) instead of `getSession()` (client-only) -- line 126
- Proper protected/public route distinction with redirect-on-fail
- Session expiry detection via cookie presence heuristic (lines 135-145)

**Finding (MINOR):** The middleware falls through silently if Supabase env vars are missing (line 81-82: `return NextResponse.next()`). This means protected routes become accessible without auth if env vars are misconfigured. Low risk in production since Railway always has these set, but a defensive `redirect("/login")` would be safer.

---

### 10.2 Authorization & RBAC

**Mechanism:** Three-tier role system (`backend/authorization.py`)

| Role | Source | Capabilities |
|------|--------|-------------|
| Admin | `profiles.is_admin = true` OR `ADMIN_USER_IDS` env var | Full access, user management, webhook events, audit logs |
| Master | `profiles.plan_type = 'master'` | All features, unlimited quota |
| Regular | Plan-based (free_trial, smartlic_pro, legacy) | Quota-limited, plan-gated features |

- Retry logic on role check: 2 attempts with 0.3s delay (authorization.py:44-93)
- Fail-safe: on error, user treated as regular (non-admin/non-master) -- never escalates

---

### 10.3 Row Level Security (RLS)

**All tables have RLS enabled.** Analysis of 30 migration files:

| Table | RLS Policies | Assessment |
|-------|-------------|------------|
| `profiles` | Select/update own only (`auth.uid() = id`) | STRONG |
| `plans` | Public read (catalog) | CORRECT |
| `user_subscriptions` | Select own + service_role full (migration 016) | STRONG |
| `search_sessions` | Select/insert own + service_role full (migration 016) | STRONG |
| `monthly_quota` | Service_role only (migration 016) | STRONG |
| `stripe_webhook_events` | Admin-only select (uses `is_admin`, fixed from `plan_type` in 016) | STRONG |
| `audit_events` | Service_role full + admin read (migration 023) | STRONG |
| `pipeline_items` | Select/insert/update own (migration 025) | STRONG |

**Prior vulnerability fixed:** Migration 016 replaced overly-permissive `FOR ALL USING (true)` (without role restriction) with proper `TO service_role` scoping on `monthly_quota` and `search_sessions`.

---

### 10.4 LGPD Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Privacy policy page | COMPLETE | `/privacidade` -- 12 sections, LGPD rights enumerated, DPO contact, ANPD reference (frontend/app/privacidade/page.tsx) |
| Cookie consent banner | COMPLETE | Accept all / Reject non-essential, links to privacy policy, re-manageable via footer "Gerenciar Cookies" event (frontend/app/components/CookieConsentBanner.tsx) |
| Analytics gating | COMPLETE | Mixpanel only initialized after explicit `analytics: true` consent; `opt_out_tracking()` called on revocation (AnalyticsProvider.tsx) |
| LGPD test suite | COMPLETE | 17 tests covering banner visibility, accept/reject, revocation, consent persistence (frontend/__tests__/lgpd.test.tsx) |
| PII masking in logs | COMPLETE | `log_sanitizer.py` -- 6 masking functions (email, API key, token, user ID, IP, phone, password) + `SanitizedLogAdapter` + auto-detection patterns |
| PII masking in Sentry | COMPLETE | `scrub_pii()` callback strips emails, user IDs, IPs, tokens from error events before transmission (main.py:82-123) |
| Audit trail PII | COMPLETE | Audit events store SHA-256 hashes (truncated to 16 hex chars) for actor_id, target_id, IP -- never raw PII (migration 023) |
| Data retention | COMPLETE | pg_cron jobs: monthly_quota 24 months, webhook_events 90 days, audit_events 12 months |
| Data deletion right | PARTIAL | Privacy policy references "Minha Conta" for elimination and portability, but no automated "delete my data" button was found in `/conta` |
| DPO contact | COMPLETE | `privacidade@smartlic.tech` documented in privacy page |
| Terms of service | PRESENT | `/termos` page exists |

**Finding (MODERATE):** LGPD Art. 18 requires a mechanism for data subjects to request elimination. The privacy page directs to `/conta` and to the DPO email, but there is no automated "delete my account and data" workflow. This is acceptable for soft launch with manual DPO handling, but should be automated before scale.

---

### 10.5 API Key Security

| Check | Result |
|-------|--------|
| Hardcoded secrets in frontend source (`app/`, `lib/`) | NONE FOUND |
| Hardcoded secrets in backend source (*.py) | NONE FOUND -- only test doubles (`whsec_test`, `sk-123...` in test files) |
| `.env` files tracked in git | NO -- both `.env` and `backend/.env` confirmed untracked (`git ls-files --error-unmatch`) |
| `.gitignore` coverage | COMPREHENSIVE -- `.env`, `.env.*`, `.env.local`, `backend/.env*`, `frontend/.env*` all excluded |
| `NEXT_PUBLIC_*` exposure | SAFE -- only Supabase anon key (by design public), Stripe publishable key (public), Sentry DSN (public), app URL/name |
| Backend secrets via env | CORRECT -- `STRIPE_WEBHOOK_SECRET`, `OPENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` all loaded from `os.getenv()` |

---

### 10.6 CORS Configuration

**Implementation:** `backend/config.py:get_cors_origins()` (lines 426-511)

| Aspect | Status |
|--------|--------|
| Wildcard `*` rejection | YES -- explicitly caught and replaced with production defaults (line 489-494) |
| Production origins hardcoded | YES -- `smartlic.tech`, `www.smartlic.tech`, Railway URLs (lines 418-423) |
| Development defaults | `localhost:3000` and `127.0.0.1:3000` only |
| Allowed methods | GET, POST, PUT, DELETE, OPTIONS (line 226) |
| Allowed headers | Limited to Authorization, Content-Type, Accept, Origin, X-Requested-With, X-Request-ID (line 227) |
| Credentials | Enabled (`allow_credentials=True`) |

**Assessment:** STRONG. No wildcard, explicit origin list, proper credential handling.

---

### 10.7 Security Headers

**Backend** (`backend/middleware.py:SecurityHeadersMiddleware`, lines 133-152):
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

**Frontend** (`frontend/next.config.js`, lines 23-69):
All of the above PLUS:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy` with explicit `default-src 'self'`, `object-src 'none'`, `base-uri 'self'`, domain-restricted `connect-src` and `frame-src`

**Finding (MINOR):** CSP includes `'unsafe-inline'` and `'unsafe-eval'` for `script-src`. This is common for Next.js/React apps due to inline scripts and HMR, but weakens XSS protection. Nonce-based CSP would be stronger but is complex with Next.js SSR.

---

### 10.8 Rate Limiting

| Layer | Mechanism | Evidence |
|-------|-----------|----------|
| API user rate limit | `RateLimiter` class: Redis token bucket + in-memory fallback, per-user per-minute (backend/rate_limiter.py) |
| Search endpoint | Plan-based `max_requests_per_min` from quota capabilities (search_pipeline.py:329-337) |
| Password change | 5 attempts per 15 minutes, per-user (routes/user.py:44-65) |
| Email resend | 60s cooldown per email (routes/auth_email.py:22-51) |
| PNCP API | 100ms minimum between requests, 10 req/s (pncp_client.py) |
| PCP API | 200ms delay, 5 req/s (portal_compras_client.py:111) |
| ComprasGov API | 500ms delay, 2 req/s (compras_gov_client.py:55) |
| Sanctions API | 667ms delay, ~90 req/min (clients/sanctions.py:120) |

**Finding (MODERATE):** No global IP-based rate limiting exists at the reverse proxy / load balancer level. The per-user rate limiter only works for authenticated users. Unauthenticated endpoints (`/health`, `/`, `/v1/auth/*`) have no rate limiting protection against DDoS. Railway does not provide built-in WAF/DDoS protection at the free tier.

---

### 10.9 Input Validation

| Aspect | Status | Evidence |
|--------|--------|----------|
| Pydantic request models | STRONG | `BuscaRequest` with field validators, pattern matching, type safety (schemas.py) |
| UUID validation | STRONG | UUID v4 regex pattern with format enforcement (schemas.py:74-114) |
| Plan ID validation | STRONG | Alphanumeric + underscore pattern, max 50 chars (schemas.py:152-179) |
| Search query sanitization | STRONG | Character whitelist, max 100 chars, SQL pattern escaping (schemas.py:182-213) |
| Password validation | STRONG | Min 8 chars, 1 uppercase, 1 digit (schemas.py:117-149) |
| API docs disabled in production | YES | `docs_url=None`, `redoc_url=None`, `openapi_url=None` when `ENVIRONMENT=production` (main.py:212-214) |

---

### 10.10 Error Tracking & Observability

| Aspect | Status |
|--------|--------|
| Sentry backend | CONFIGURED -- `sentry_sdk.init()` with `FastApiIntegration`, `traces_sample_rate=0.1`, PII scrubbing via `before_send` callback (main.py:128-135) |
| Sentry frontend | CONFIGURED -- `@sentry/nextjs` with source map upload, `/monitoring` tunnel route to bypass ad blockers, `hideSourceMaps: true` (next.config.js:73-94) |
| Structured logging | JSON format in production via `python-json-logger`, text in dev (config.py:118-135) |
| Request correlation | CorrelationIDMiddleware adds/propagates `X-Request-ID` (middleware.py:29-70) |
| Log level enforcement | DEBUG suppressed in production (config.py:96-103) |

---

### D10 Summary

**Strengths:**
1. JWT auth with local verification, full-token hashing, JWKS support
2. Comprehensive RLS across all tables, prior vulnerabilities fixed
3. Full LGPD stack: consent banner, analytics gating, privacy policy, PII masking, audit trail
4. No secrets in source code, proper .gitignore coverage
5. Strong input validation with Pydantic and regex patterns
6. Solid security headers including CSP on frontend

**Weaknesses:**
1. No IP-based rate limiting for unauthenticated endpoints (DDoS risk)
2. No automated "delete my data" workflow for LGPD Art. 18 compliance
3. CSP allows `unsafe-inline` and `unsafe-eval` (common for React, but weaker)
4. Middleware falls through without auth if Supabase env vars missing
5. Backend Docker container runs as root (no `USER` directive in backend Dockerfile)

---

## D11: Infrastructure Resilience

### Score: 6/10 (Conditional -- adequate for soft launch, not for scale)

---

### 11.1 Hosting Platform

**Provider:** Railway (PaaS)
**Architecture:** 2 services in monorepo

| Service | Runtime | Container | Config |
|---------|---------|-----------|--------|
| Backend (FastAPI) | Python 3.11-slim | Single Dockerfile | `backend/railway.toml` |
| Frontend (Next.js) | Node 20.11-alpine | Multi-stage Dockerfile (standalone output) | `frontend/railway.toml` |

**Deployment model:**
- Docker-based (`builder = "DOCKERFILE"`)
- GitHub auto-deploy on push to main
- `restartPolicyType = "ON_FAILURE"` with `restartPolicyMaxRetries = 3`

---

### 11.2 Health Checks

**Backend (`/health`):**
- Comprehensive dependency checks: Supabase, OpenAI, Redis (main.py:330-417)
- Per-source health: PNCP, PCP, ComprasGov circuit breaker status
- Degraded state detection (Redis down but Supabase up = "degraded")
- Always returns 200 (Railway health checks fail if non-200, preventing startup)
- Health status communicated via response body `"status"` field
- Railway health check timeout: 120s

**Frontend (`/api/health`):**
- Simple API route health check
- Railway health check timeout: 120s

**Assessment:** GOOD health check implementation with dependency-aware status.

---

### 11.3 Database

**Provider:** Supabase (managed PostgreSQL)

| Aspect | Status | Evidence |
|--------|--------|----------|
| Connection method | Supabase client SDK (not raw psycopg2) | `supabase_client.py` -- singleton pattern via `create_client()` |
| Connection pooling | IMPLICIT -- Supabase Python SDK uses HTTP/REST API, not direct Postgres connections | No pgBouncer config needed |
| RLS enforcement | ALL tables | 30 migrations reviewed, every table has `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` |
| Index coverage | GOOD | 15+ custom indexes for common query patterns (user lookups, Stripe IDs, trigram email search) |
| Data retention | AUTOMATED | pg_cron jobs for monthly_quota (24mo), webhook_events (90d), audit_events (12mo) |
| Migrations | MANAGED | 31 SQL files in `supabase/migrations/` |

**Finding (MODERATE):** The Supabase client is a singleton but uses the REST API (PostgREST), which has connection limits on the Supabase side. Under heavy concurrent load, this could become a bottleneck. Supabase Free tier allows max 50 concurrent connections; Pro tier allows 100+. The current architecture does not use direct Postgres connections or pgBouncer pooling.

---

### 11.4 Caching Layer

| Layer | Implementation | Status |
|-------|---------------|--------|
| Redis (primary) | `redis_pool.py` -- async pool, 20 max connections, 5s timeout | Optional -- graceful fallback |
| InMemoryCache (fallback) | LRU with TTL, max 10K entries | Always available |
| Token cache | SHA-256 keyed, 60s TTL (auth.py) | In-memory dict |
| Feature flag cache | 60s TTL, runtime-reloadable (config.py) | In-memory dict |
| Search results cache | Two-level: InMemoryCache (4h) + Supabase table (24h) | SWR pattern |
| Redis features cache | User capabilities cached in Redis (cache.py) | Invalidated on webhook events |

**Assessment:** STRONG caching architecture with proper fallback chain. Redis unavailability does not break the application.

---

### 11.5 Concurrent User Capacity

**Bottleneck analysis:**

| Component | Capacity | Limiting Factor |
|-----------|----------|----------------|
| Railway backend | Single container, single uvicorn process | No auto-scaling on Railway starter plan |
| Uvicorn workers | 1 (default `CMD uvicorn main:app`) -- no `--workers N` | Single process handles all requests |
| PNCP API | 10 req/s rate limit | Hard external constraint |
| PCP API | 5 req/s rate limit | Hard external constraint |
| Supabase REST API | 50-100 concurrent connections (plan-dependent) | Shared with frontend |
| Redis pool | 20 max connections | Configurable |

**Critical Finding (HIGH):** The backend runs a single uvicorn worker (`CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`). This means:
- All requests are handled by a single Python process
- CPU-bound operations (Excel generation, keyword filtering) block the entire server
- Under moderate load (10+ concurrent searches), response times will degrade significantly
- No horizontal scaling configured

**Estimated safe capacity:** 5-10 concurrent active searches, 50-100 concurrent idle/browsing users.

---

### 11.6 Auto-Scaling

**Status:** NOT CONFIGURED

Railway supports horizontal scaling (multiple replicas) on paid plans, but:
- No `railway.toml` `numReplicas` setting
- No autoscaling configuration
- Single container per service

**Assessment:** Acceptable for soft launch with <100 users. Must be addressed before any marketing push.

---

### 11.7 Cold Start Time

| Service | Estimated Cold Start | Notes |
|---------|---------------------|-------|
| Backend | ~10-15s | Python dependency loading, Sentry init, Redis connect, env validation |
| Frontend | ~3-5s | Node.js standalone server, minimal startup |

Railway keeps containers warm for active services. Cold starts occur after:
- Deployment (new container)
- Service restart (crash recovery)
- Idle shutdown (Free tier: 5 min inactivity; Hobby: no idle shutdown)

**Finding:** The `healthcheckTimeout = 120` is generous enough to handle cold starts without false failures.

---

### 11.8 Container Security

**Frontend container:**
- Non-root user: YES (`adduser --system --uid 1001 nextjs`, `USER nextjs`) -- line 121-131
- Minimal base image: `node:20.11-alpine3.19`
- Multi-stage build: 3 stages (deps -> builder -> runner)

**Backend container:**
- Non-root user: NO -- runs as root (no `USER` directive in Dockerfile)
- Base image: `python:3.11-slim` (reasonable)
- Single-stage build

**Finding (MODERATE):** Backend container runs as root. While Railway provides container isolation, running as non-root is a defense-in-depth best practice. The frontend container correctly uses a non-root user.

---

### 11.9 Circuit Breaker & Resilience

| Pattern | Implementation | Evidence |
|---------|---------------|----------|
| Circuit breaker | Per-source: PNCP, PCP -- `get_circuit_breaker()` (main.py:389-392) | Independent breakers prevent cascade |
| Retry with backoff | Exponential backoff + jitter on all HTTP clients | pncp_client.py, portal_compras_client.py, compras_gov_client.py |
| Rate limit respect | Honors 429 `Retry-After` header | All clients check response status |
| Graceful degradation | SWR cache fallback on source failure | search_cache.py -- AllSourcesFailedError handler queries cache |
| Redis failure | Transparent fallback to InMemoryCache | redis_pool.py, rate_limiter.py |
| Supabase failure | Partial -- health check reports "unhealthy" | No request-level retry on Supabase |

**Assessment:** STRONG resilience for external API sources. ADEQUATE for internal dependencies.

---

### 11.10 Observability (Deployed)

| Component | Configured | Deployed/Active |
|-----------|-----------|----------------|
| Sentry (backend) | YES | UNKNOWN -- depends on `SENTRY_DSN` env var being set in Railway |
| Sentry (frontend) | YES | UNKNOWN -- depends on `NEXT_PUBLIC_SENTRY_DSN` build arg |
| Mixpanel (analytics) | YES | YES (consent-gated) |
| Structured JSON logging | YES | YES (LOG_FORMAT=json in production) |
| Request ID correlation | YES | YES (CorrelationIDMiddleware) |
| Health endpoint | YES | YES (`/health` with dependency checks) |
| Grafana/Datadog/etc. | NO | NO -- Railway provides basic metrics only |

**Finding (MODERATE):** While the code has excellent observability instrumentation (Sentry, structured logging, correlation IDs), the previous GTM-OK assessment noted that deployed observability scored 3/10. The issue is not the code but the operational configuration -- whether Sentry DSN is actually set, whether alerts are configured, whether anyone monitors the dashboards.

---

### D11 Summary

**Strengths:**
1. Comprehensive health check with dependency awareness
2. Multi-layer caching with graceful Redis fallback
3. Per-source circuit breakers prevent cascade failures
4. Docker-based deployment with auto-restart policy
5. Frontend container follows security best practices (non-root, multi-stage)

**Weaknesses:**
1. **Single uvicorn worker** -- no multi-process or async worker scaling (CRITICAL for load)
2. **No auto-scaling** -- single container per service
3. **Backend runs as root** in Docker
4. No WAF/DDoS protection at the network edge
5. No external monitoring/alerting platform (depends on Sentry being configured)
6. Supabase REST API connection limits under heavy concurrent load
7. No CDN for frontend static assets (Railway serves directly)

---

## Consolidated Scores

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **D10: Security & LGPD** | **7/10** | Production-ready. Strong auth, RLS, LGPD compliance, input validation, security headers. Gaps: no IP rate limiting, no automated data deletion, CSP allows unsafe-inline. |
| **D11: Infrastructure** | **6/10** | Conditional. Adequate for soft launch with <100 users. Single-worker uvicorn and no auto-scaling are the critical blockers for growth. Health checks, caching, and circuit breakers are solid. |

### Path to 8/10 (D10)
1. Add IP-based rate limiting (Cloudflare or nginx reverse proxy) -- 2h
2. Implement automated "delete my account" workflow -- 4h
3. Add non-root user to backend Dockerfile -- 15min

### Path to 8/10 (D11)
1. Add `--workers 4` (or `gunicorn -w 4 -k uvicorn.workers.UvicornWorker`) to backend CMD -- 15min
2. Configure Railway horizontal scaling (2+ replicas) -- 30min
3. Add Cloudflare CDN/WAF in front of Railway -- 2h
4. Verify Sentry DSN is configured and alerts are set up -- 1h

---

## Files Analyzed

**Backend:**
- `backend/main.py` (lines 1-500)
- `backend/auth.py` (350 lines)
- `backend/authorization.py` (168 lines)
- `backend/config.py` (539 lines)
- `backend/middleware.py` (153 lines)
- `backend/log_sanitizer.py` (606 lines)
- `backend/schemas.py` (lines 1-220)
- `backend/rate_limiter.py` (96 lines)
- `backend/redis_pool.py` (203 lines)
- `backend/supabase_client.py` (50 lines)
- `backend/webhooks/stripe.py` (lines 1-148)
- `backend/Dockerfile` (42 lines)
- `backend/railway.toml` (33 lines)

**Frontend:**
- `frontend/middleware.ts` (184 lines)
- `frontend/next.config.js` (95 lines)
- `frontend/app/components/CookieConsentBanner.tsx` (120 lines)
- `frontend/app/privacidade/page.tsx` (224 lines)
- `frontend/__tests__/lgpd.test.tsx` (656 lines)
- `frontend/Dockerfile` (145 lines)
- `frontend/railway.toml` (26 lines)

**Database:**
- `supabase/migrations/001_profiles_and_sessions.sql`
- `supabase/migrations/016_security_and_index_fixes.sql`
- `supabase/migrations/022_retention_cleanup.sql`
- `supabase/migrations/023_audit_events.sql`
- 27 additional migration files (RLS verification)

**Git:**
- `.gitignore` (390+ lines) -- verified .env exclusion
- `git ls-files --error-unmatch` -- confirmed .env files untracked
