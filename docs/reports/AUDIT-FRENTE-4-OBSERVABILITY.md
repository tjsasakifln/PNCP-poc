# FRENTE 4 -- OBSERVABILITY & OPERABILITY AUDIT REPORT

**Audit Date:** 2026-02-12
**Auditor:** Claude Opus 4.6 (deep codebase audit)
**Scope:** Backend (FastAPI), Frontend (Next.js), Infrastructure (Railway, Supabase, Stripe)
**Method:** Exhaustive grep/read of all logging, metrics, alerting, health check, error tracking, tracing, and audit patterns across the entire codebase.

---

## Executive Summary

**Can we operate this system at 3 AM? NO.**

If Google login breaks at 03:17 AM, the customer discovers it first. The system has foundational observability building blocks -- structured log formatting, correlation IDs, health checks, log sanitization, and Mixpanel analytics -- but critical operational gaps remain. There is **no error tracking service** (Sentry is mentioned in 20+ documents but never installed), **no automated alerting** (all monitoring is manual/aspirational), **no JSON-structured logs** (Railway log aggregation is limited to plain text grep), and the **frontend has zero server-side observability** (errors go to `console.error` only). The monitoring runbook describes an elaborate 48-hour manual monitoring protocol, but none of it is automated. A payment webhook failure or auth token validation crash would produce log lines that nobody is watching.

**Overall Observability Maturity: BASIC (2/5)**

| Dimension | Score | GTM Blocker? |
|-----------|-------|--------------|
| Structured Logging | BASIC | No (functional but not machine-parseable) |
| Application Metrics | ABSENT | No (Railway provides basic infra metrics) |
| Alerting | ABSENT | **YES** |
| Health Checks | ADEQUATE | No |
| Error Tracking | ABSENT | **YES** |
| Distributed Tracing | BASIC | No |
| Audit Logging | BASIC | No |
| Documentation | ADEQUATE | No |

**GTM-blocking gaps:** 2 (alerting, error tracking)

---

## 1. Structured Logging

### Current State: BASIC

### Findings

**Logging Library:** Standard Python `logging` module (no structlog, loguru, or python-json-logger).

**Log Format (`backend/config.py` line 98-101):**
```
%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s
```
Example output:
```
2026-02-12 03:17:42 | ERROR    | a3f5b2c8-... | backend.auth | JWT token expired
```

**Positives:**

1. **Consistent format across all modules.** 47+ backend files use `logger = logging.getLogger(__name__)` pattern uniformly. Not a single module deviates from this pattern.

2. **Request ID injected into all log records** via `RequestIDFilter` (`backend/middleware.py` lines 16-26) added to root logger (`config.py` lines 106-116). The filter uses a `ContextVar` (line 13) with default `"-"` so startup logs outside request context do not crash.

3. **Comprehensive log sanitization infrastructure** (`backend/log_sanitizer.py`, 606 lines):
   - `mask_email()` -- `u***@example.com`
   - `mask_api_key()` -- `sk-***cdef`
   - `mask_token()` -- `eyJ***[JWT]`
   - `mask_user_id()` -- `550e8400-***`
   - `mask_password()` -- `[PASSWORD_REDACTED]`
   - `mask_ip_address()` -- `192.168.x.x`
   - `mask_phone()` -- `***-1234`
   - `SanitizedLogAdapter` class for automatic sanitization
   - `sanitize_dict()`, `sanitize_string()` for deep sanitization
   - `SENSITIVE_PATTERNS` regex auto-detection for API keys, JWT tokens, Bearer tokens
   - `SENSITIVE_FIELDS` set for field-name-based masking
   - `log_auth_event()`, `log_admin_action()`, `log_user_action()` structured helpers

4. **Sanitization actually used in production code:**
   - `backend/auth.py` -- `log_auth_event()` for token verification failures (line 131)
   - `backend/admin.py` -- `log_admin_action()` for 7+ admin operations (lines 350, 385, 428, 461, 508, 571, 608)
   - `backend/routes/billing.py` -- `log_user_action()` for plan activation (line 114)
   - `backend/routes/user.py` -- `log_user_action()` for password changes (lines 37, 40)
   - `backend/routes/analytics.py`, `quota.py`, `authorization.py`, `routes/search.py`, `routes/features.py`, `routes/subscriptions.py` -- use `mask_user_id()`
   - Total: 11 production files actively use sanitization functions.

5. **Production DEBUG suppression** (`config.py` lines 87-96) -- DEBUG level elevated to INFO in production environments, preventing accidental sensitive data exposure.

6. **Third-party library noise suppressed** (`config.py` lines 125-126) -- urllib3 and httpx set to WARNING level.

7. **247 error/warning/critical log calls** across 47 backend Python files -- substantial logging coverage. Error logging includes context in most cases.

**Frontend Logging:**
- Uses `console.log`, `console.error`, `console.warn` throughout (~70+ calls across TypeScript files).
- `frontend/app/error.tsx` (line 13) -- Next.js error boundary catches component errors with `console.error("Application error:", error)`.
- API route handlers (`buscar/route.ts`, `download/route.ts`, `me/route.ts`, etc.) log errors with `console.error`.
- OAuth callback (`frontend/app/auth/callback/page.tsx`) has 30+ console statements for debugging.

### Gaps

1. **NOT JSON-structured.** Logs are pipe-delimited plain text. Railway's log viewer provides basic filtering, but there is no way to run structured queries (e.g., "show all ERROR logs where request_id=X and duration > 5000ms"). Machine parsing requires regex. No `python-json-logger`, `structlog`, or equivalent is installed.

2. **Import-time logging race condition.** `config.py` lines 222-227 call `logger.info()` to log feature flag state at module import time. These fire during `import config` in `main.py` line 30, which triggers before `setup_logging()` on line 53. The `RequestIDFilter` is installed inside `setup_logging()`, creating a window where early logs may not have the filter. Currently mitigated by the filter defaulting to `"-"`, but fragile.

3. **Frontend OAuth callback leaks token prefix.** `frontend/app/auth/callback/page.tsx` line 125:
   ```typescript
   console.log("[OAuth Callback] Access Token (first 20 chars):",
     session.access_token.substring(0, 20) + "...");
   ```
   This is logged in the browser console in production. Not gated behind `NODE_ENV === 'development'`.

4. **No log rotation or retention policy.** Railway retains logs for a limited period (varies by plan). There is no configuration for log forwarding to a durable store (e.g., Datadog, CloudWatch, Elastic).

5. **`SanitizedLogAdapter` is available but underutilized.** Only `log_auth_event` is used in production code (`auth.py`). Most modules use the raw `logger` directly. The `SanitizedLogAdapter` and `get_sanitized_logger()` helper exist but are called in zero production modules as wrappers.

---

## 2. Application & Business Metrics

### Current State: ABSENT

### Findings

**No application-level metrics library.** There is no `prometheus_client`, `statsd`, `opentelemetry`, `datadog`, or any metrics collection library in `backend/requirements.txt` or `frontend/package.json`.

**In-memory operational metrics exist in two modules (not exported):**

1. **`backend/pncp_resilience.py`** (lines 31-183) -- `UFPerformanceMetrics` dataclass tracks per-UF:
   - `total_requests`, `successful_requests`, `failed_requests`, `timeout_count`
   - `success_rate`, `avg_duration_ms`, `p95_duration_ms`
   - `is_healthy` boolean (based on success rate threshold)
   - **In-memory only, lost on restart, not exported to any monitoring system.**

2. **`backend/consolidation.py`** (line 21) -- `SourceFetchMetrics` tracks per-source results.
   - Also in-memory, used for response construction only.

**Business metrics via Mixpanel (frontend only):**

1. **`frontend/app/components/AnalyticsProvider.tsx`** -- Initializes Mixpanel with `NEXT_PUBLIC_MIXPANEL_TOKEN`, tracks:
   - `page_load` (with path, referrer, user_agent, timestamp)
   - `page_exit` (with session_duration_ms)
   - Route change tracking via `usePathname()`

2. **`frontend/hooks/useAnalytics.ts`** -- `trackEvent()` wrapper for Mixpanel:
   - Used in search flow, download flow, upgrade modal
   - Events tracked: `search_started`, `search_completed`, `search_failed`, `download_started`, `download_completed`, `upgrade_modal_opened`, `plan_clicked`, `page_view`
   - All events include timestamp and environment

3. **Mixpanel is client-side only.** Server-side business events (search execution time, PNCP API latency, filter precision, Excel generation timing, webhook processing) are NOT tracked in Mixpanel or any analytics platform.

**Locust load testing exists** (`backend/locustfile.py`, 140+ lines) but is manual and not integrated into CI/CD.

### Gaps

1. **Zero Prometheus/StatsD/OTEL metrics.** Cannot create dashboards, cannot set up metric-based alerts, cannot track SLOs/SLIs.
2. **In-memory metrics are volatile.** `UFPerformanceMetrics` disappears on every Railway deployment or restart.
3. **No backend-to-analytics integration.** Server-side business events are invisible to Mixpanel.
4. **No SLI/SLO definitions.** No target latency, availability, or error rate budgets formally defined.
5. **No request latency histograms.** The middleware logs duration per request but does not aggregate into percentiles.

---

## 3. Alerting

### Current State: ABSENT

### Findings

**No automated alerting is configured anywhere in the codebase or infrastructure-as-code.**

The monitoring runbook (`docs/runbooks/monitoring-alerting-setup.md`, 817 lines) describes:
- Railway dashboard alerts (CPU >80%, memory >90%, health check failures)
- Vercel build failure alerts
- Mixpanel manual monitoring every 30 minutes
- 48-hour on-call rotation schedule
- Incident response playbook (Critical/Warning/Information severity)
- Slack alert format templates

However, this is **entirely aspirational documentation**:
- All alert configurations are "Access: Railway Dashboard -> Settings -> Alerts -> Add Alert" -- manual dashboard steps never confirmed as executed.
- Slack webhook URL is placeholder: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
- Contact information is blank: `@devops | ____________ | 24/7 (48h window)`
- No `.github/workflows` for monitoring automation
- No Railway alert configuration files in the repo
- No PagerDuty, OpsGenie, or incident management integration
- No cron-based health check scripts

**Railway restart policy IS configured** (`backend/railway.toml` lines 18-19):
```toml
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```
This provides **automatic restart on failure** (up to 3 retries) but **no notification**. The service could crash-loop 3 times and stop, with nobody knowing.

### Gaps

1. **Zero automated alerts configured.** No email, Slack, PagerDuty, or webhook notifications for any failure condition.
2. **No alerting on auth failures.** If `SUPABASE_JWT_SECRET` is rotated and JWT validation fails for all users, no alert fires.
3. **No alerting on payment failures.** If `STRIPE_WEBHOOK_SECRET` expires and all webhooks are rejected, no alert fires. Revenue impact would be invisible.
4. **No alerting on PNCP API degradation.** If the primary data source returns 500s for all states, only end users notice.
5. **No alerting on error rate spikes.** 100% of requests could return 500s with no notification.
6. **No alerting on Railway crash-loop.** After 3 restart failures, the backend stops and nobody is notified.
7. **Runbook exists but is 100% unimplemented.** The gap between documented procedures and actual implementation is total.

---

## 4. Health Checks

### Current State: ADEQUATE

### Findings

**Backend `/health` endpoint** (`backend/main.py` lines 193-266):
- Returns `healthy`, `degraded`, or `unhealthy` status
- Checks critical dependencies:
  - **Supabase**: Verifies client initialization; returns HTTP 503 if client creation fails
  - **OpenAI**: Checks API key presence (`configured` vs `missing_api_key`)
  - **Redis**: Tests connectivity via `is_redis_available()` (optional; degrades gracefully if unconfigured)
- Returns HTTP 503 for unhealthy (Supabase down), 200 for healthy/degraded
- Includes `timestamp`, `version`, `dependencies` in response
- **Used by Railway** (`railway.toml` line 16: `healthcheckPath = "/health"`, timeout 120s)

**Backend `/sources/health` endpoint** (`backend/main.py` lines 269-356):
- Checks health of all procurement data sources (PNCP, Portal, ComprasGov)
- Runs health checks in parallel via `ConsolidationService.health_check_all()`
- Reports per-source status, response time (ms), priority, enabled state
- Returns totals: `total_enabled`, `total_available`

**Dedicated health module** (`backend/health.py`, 360 lines):
- `HealthStatus` enum: HEALTHY, DEGRADED, UNHEALTHY
- `SourceHealthResult` and `SystemHealth` dataclasses with JSON serialization
- `check_source_health()` -- HTTP probe per source (HEAD preferred, GET fallback, 10s timeout)
- `check_all_sources_health()` -- Parallel checks via `asyncio.gather()`
- `calculate_overall_status()` -- Composite logic (PNCP is critical; if PNCP down, system UNHEALTHY)
- `get_health_status()` and `get_detailed_health()` for comprehensive diagnostics
- Uptime tracking via `initialize_health_tracking()` / `get_uptime_seconds()`
- Diagnostics include Python version, hostname, port

**Frontend `/api/health` endpoint** (`frontend/app/api/health/route.ts`, 5 lines):
```typescript
export async function GET() {
  return NextResponse.json({ status: "ok" }, { status: 200 });
}
```
- **Minimal stub.** Returns `{"status":"ok"}` with no dependency checks.
- Used by Railway (`frontend/railway.toml` line 14: `healthcheckPath = "/api/health"`)

### Gaps

1. **Frontend health check is trivial.** Does not verify backend connectivity, Supabase auth service, or critical environment variables.

2. **Backend `/health` does NOT check PNCP API.** The primary data source is only checked via `/sources/health`, which Railway does NOT poll. A PNCP outage shows backend as "healthy."

3. **No deep database health check.** Supabase check only verifies client initialization (in-memory), not actual query capability. Connection pool exhaustion or permission issues would pass.

4. **No Stripe connectivity check** in `/health`. If `STRIPE_SECRET_KEY` is invalid, the health check says "healthy."

5. **Health check timeout is 120 seconds** -- very generous. If the check hangs for 119s, Railway considers it healthy.

---

## 5. Error Tracking

### Current State: ABSENT

### Findings

**No error tracking service is installed or configured.**

- `SENTRY_DSN=` appears in `.env.example` (line 111) as an empty placeholder.
- `@sentry/nextjs` is NOT in `frontend/package.json` dependencies or devDependencies.
- `sentry-sdk` or `sentry-sdk[fastapi]` is NOT in `backend/requirements.txt`.
- `@sentry/*` packages exist in `frontend/package-lock.json` as transitive dependencies of Next.js, but are **never imported or initialized** in application code.
- Grep for `import sentry` or `@sentry` or `Sentry.init` or `sentry_sdk.init` in all backend `.py` and frontend `.ts`/`.tsx`/`.js` files: **zero results**.

**What happens when errors occur:**

| Error Source | Capture Method | Persistence | Searchable? | User Impact Visible? |
|---|---|---|---|---|
| Backend Python exceptions | `logger.error()` to stdout | Railway logs (~7 days) | Text grep only | No alert |
| Backend unhandled exceptions | FastAPI default 500 handler + stdout | Railway logs | Text grep | No alert |
| Frontend component errors | `error.tsx` boundary + `console.error` | Browser console only | NO | User sees error page |
| Frontend API route errors | `console.error` in route handlers | Railway logs | Text grep | No alert |
| Frontend browser JS errors | No capture mechanism | Lost forever | NO | User sees blank/broken UI |
| Unhandled promise rejections (FE) | No capture mechanism | Lost forever | NO | Silent failure |

**Next.js error boundary** (`frontend/app/error.tsx`, 65 lines):
- Catches React component rendering errors within the app router
- Displays user-friendly Portuguese error message with retry button
- Logs to `console.error("Application error:", error)` only
- Does NOT report to any external service

**No `global-error.tsx`** exists. This Next.js convention catches errors in the root layout itself. Without it, root layout errors produce the default Next.js error page with no custom handling.

### Gaps

1. **Frontend JavaScript errors are completely invisible.** No `window.onerror`, no `window.addEventListener('error')`, no `window.addEventListener('unhandledrejection')`. If a user encounters a JS error, it exists only in their browser console and is lost when they close the tab.

2. **No `global-error.tsx`.** Root layout errors crash the entire page with no recovery UI and no error reporting.

3. **No error deduplication, grouping, or trending.** Backend logs errors, but there is no way to see "this error occurred 47 times in the last hour" without manually parsing Railway logs.

4. **No source maps for production error traces.** Frontend is built with `output: 'standalone'` but no source map upload. Production stack traces show minified/bundled code.

5. **No user context on errors.** When an error occurs, there is no automatic capture of which user, which session, which browser, or what actions preceded the error.

6. **Inconsistent exception logging in backend.** Some use `exc_info=True` (e.g., `webhooks/stripe.py` line 140: `logger.error(f"Error processing webhook: {e}", exc_info=True)`), others only log the message string without stack trace. No enforced pattern.

---

## 6. Distributed Tracing

### Current State: BASIC

### Findings

**Correlation ID middleware implemented** (`backend/middleware.py`, 71 lines):

1. **`CorrelationIDMiddleware`** (lines 29-70):
   - Accepts incoming `X-Request-ID` header from frontend or generates new UUID
   - Stores in `request_id_var: ContextVar[str]` for async context propagation
   - Logs consolidated request summary: `{method} {path} -> {status} ({duration}ms) [req_id={id}]`
   - Returns `X-Request-ID` in response headers for client-side correlation
   - Logs errors with exception type and message

2. **`RequestIDFilter`** (lines 16-26):
   - Logging filter injects `request_id` into ALL log records across ALL modules
   - Falls back to `"-"` outside request context (startup, background tasks)

3. **Frontend generates correlation IDs:**
   - `frontend/app/api/buscar/route.ts` line 67: `"X-Request-ID": randomUUID()`
   - `frontend/app/api/download/route.ts` lines 16-17: forwards incoming `X-Request-ID`

4. **CORS allows `X-Request-ID`** (`backend/main.py` line 79: `allow_headers` includes `"X-Request-ID"`).

5. **Filter-level tracing** (`backend/filter.py` lines 2001-2140):
   - Generates per-contract `trace_id` (8-char UUID prefix)
   - Logs filter decisions at each layer (Camada 2A, 3A) with trace_id
   - Stored in `lic["_trace_id"]` for downstream correlation

### Gaps

1. **No trace propagation to external APIs.** When backend calls PNCP API, OpenAI API, Supabase, or Stripe, `X-Request-ID` is NOT forwarded in outgoing requests. A slow PNCP response cannot be correlated to the user request that triggered it.

2. **No OpenTelemetry or W3C TraceContext.** The correlation ID is custom and limited to frontend-to-backend only. No standard trace context propagation.

3. **No trace visualization.** No Jaeger, Zipkin, or Sentry Performance tracing. Debugging requires manual log grep with `req_id=X` across Railway log viewer.

4. **Background tasks lack correlation.** Async operations outside the middleware chain (webhook processing, cache invalidation) have `request_id="-"`. Stripe webhooks generate their own request_id via the middleware, but there is no link to the original user action.

5. **Frontend does not log generated correlation IDs.** The `randomUUID()` is sent as a header but never logged client-side. If the frontend request times out, the correlation ID is effectively lost.

---

## 7. Audit Logging

### Current State: BASIC

### Findings

**Auth events partially logged:**
- JWT validation failures: `log_auth_event(logger, event="token_verification", success=False, reason=type(e).__name__)` (`auth.py` line 131-135)
- JWT validation success: `logger.info(f"JWT validation SUCCESS for user {user_id[:8]} ({email})")` (`auth.py` line 121)
- JWT expiration: `logger.warning("JWT token expired")` (`auth.py` line 97)
- Invalid JWT: `logger.warning(f"Invalid JWT token: {type(e).__name__}")` (`auth.py` line 100)
- Auth cache operations: logged at DEBUG level (suppressed in production)

**Admin actions well-logged:**
- `backend/admin.py` uses `log_admin_action()` for all admin operations:
  - User listing, user detail viewing, plan assignment, force plan change, subscription management
  - Each call includes `admin_id` (masked), `action` name, `target_user_id` (masked), and sanitized details
  - 7+ distinct `log_admin_action()` calls with full context

**Payment events logged with audit trail:**
- Stripe webhook receipt: `logger.info(f"Received Stripe webhook: event_id={event.id}, type={event.type}")` (line 100)
- Idempotency check: duplicate detection logged (line 115)
- Subscription changes: subscription_id, interval, billing_period logged (line 164)
- Subscription deletions: logged with subscription_id (line 221)
- Invoice payments: logged with subscription_id (line 270)
- **Database audit trail:** `stripe_webhook_events` table stores event id, type, processed_at, payload (lines 129-134)

**User actions partially logged:**
- Plan activation: `log_user_action(logger, "plan-activated", user_id, details={"plan_id": plan_id})` (`billing.py` line 114)
- Password changes: `log_user_action(logger, "password-changed/failed", user["id"])` (`user.py` lines 37, 40)
- Search sessions: logged with session_id prefix and masked user_id (`search.py` lines 927, 1074)

**OAuth operations logged:**
- Google OAuth initiation: `logger.info(f"Initiating Google OAuth for user {user['id'][:8]}")` (`auth_oauth.py` line 89)
- OAuth completion: `logger.info(f"Google OAuth completed successfully for user {user_id[:8]}")` (line 172)
- OAuth errors: logged at WARNING/ERROR level with type information (lines 132, 139, 150, 181, 187)
- Token revocation: logged (lines 221, 227, 237)
- Token storage: `logger.info(f"Saved {provider} OAuth tokens for user {user_id[:8]}")` (`oauth.py` line 319)

### Gaps

1. **No centralized audit log table.** Auth events, admin actions, and user actions go to stdout logs only. Only Stripe webhook events have a database audit trail. If Railway logs rotate, the audit trail is gone.

2. **Supabase Auth login/logout events not captured.** The backend only validates JWTs -- it does not know when a user logs in or logs out. Supabase Auth handles these events but there is no webhook configured to forward them to the backend.

3. **Failed login attempts not distinguishable.** The backend sees token validation failures but cannot distinguish "wrong password" from "expired token" from "no account" -- these all happen at Supabase Auth before reaching the backend.

4. **No audit log for data access/download.** When a user downloads Excel results or views procurement data, there is no dedicated audit record. Search sessions are logged, but download events are not persisted.

5. **No IP address logging for security events.** Auth failures and admin actions are logged with user_id but NOT with client IP address. The `mask_ip_address()` function exists in `log_sanitizer.py` but is never called in production code.

---

## 8. Documentation Quality

### Current State: ADEQUATE

### Swagger/OpenAPI
- **Enabled and accessible:** `/docs` (Swagger UI), `/redoc` (ReDoc), `/openapi.json`
- FastAPI auto-generates schema from Pydantic models and route decorators
- Response models defined for analytics endpoints (`SummaryResponse`, `TimeSeriesDataPoint`, etc.)
- OpenAPI schema snapshot exists (`backend/tests/snapshots/openapi_schema.json`) with automated diff testing (`test_openapi_schema.py`)
- **Gap:** Not all endpoints have explicit response models. Some return raw dicts. Query parameter descriptions are inconsistent across endpoints.

### READMEs
- **`CLAUDE.md`** (~2000 lines) -- Comprehensive development guide covering architecture, commands, testing strategy, troubleshooting, AIOS integration. Very detailed and current.
- **Gap:** No standalone user-facing README with quick-start instructions.

### Architecture Documentation
- Data flow documented in `CLAUDE.md` (High-Level Data Flow section)
- Backend module descriptions with critical implementation details
- Multi-source architecture documented in `docs/architecture/multi-source-technical-considerations.md`
- **Gap:** No deployment architecture diagram showing Railway service topology, Supabase connections, DNS/CDN flow, or Stripe webhook path.

### Troubleshooting Guide
- Present in `CLAUDE.md` (Troubleshooting section): PNCP timeouts, LLM errors, frontend connection issues, Excel download failures
- Dedicated `docs/runbooks/PNCP-TIMEOUT-RUNBOOK.md`
- Dedicated `docs/runbooks/rollback-procedure.md`
- Monitoring runbook (817 lines, aspirational but comprehensive)
- **Gap:** No troubleshooting guide for auth failures, Stripe webhook issues, or database connection problems.

### Auth Flow Documentation
- OAuth callback flow heavily commented inline (`frontend/app/auth/callback/page.tsx`)
- JWT validation documented in `auth.py` docstrings
- Supabase Auth middleware documented in comments
- **Gap:** No standalone auth flow diagram. Flow spans frontend middleware (`middleware.ts`), Supabase client, backend JWT validation (`auth.py`), role checking (`authorization.py`), and Google OAuth (`oauth.py`, `auth_oauth.py`) across 6+ files.

### Billing/Quota Flow Documentation
- Stripe webhook handler documented (`webhooks/stripe.py` docstring: 28 lines)
- Quota system documented (`quota.py` docstring: 18 lines)
- Stripe integration guide: `docs/stripe/STRIPE_INTEGRATION.md`
- **Gap:** No visual diagram of billing lifecycle (signup -> plan selection -> checkout -> webhook -> quota enforcement -> upgrade/downgrade/cancellation).

---

## 9. Operability Risk Matrix

| # | Area | Current State | Risk Level | GTM Blocker? | Effort to Fix |
|---|------|---------------|-----------|--------------|---------------|
| 1 | Error Tracking (Sentry) | ABSENT -- no SDK installed | **CRITICAL** | **YES** | 1-2 days |
| 2 | Automated Alerting | ABSENT -- runbook exists, nothing implemented | **CRITICAL** | **YES** | 1 day |
| 3 | JSON Structured Logging | ABSENT -- plain text pipe-delimited | HIGH | No | 0.5 day |
| 4 | Frontend Global Error Handler | ABSENT -- no `global-error.tsx`, no window.onerror | HIGH | No | 0.5 day |
| 5 | Application Metrics Export | ABSENT -- no Prometheus/StatsD/OTEL | HIGH | No | 2-3 days |
| 6 | Frontend Health Check (deep) | TRIVIAL -- returns `{"status":"ok"}` | MEDIUM | No | 0.5 day |
| 7 | Audit Log Persistence | ABSENT -- stdout only, no DB table | MEDIUM | No | 1-2 days |
| 8 | External API Trace Propagation | ABSENT -- X-Request-ID not forwarded | MEDIUM | No | 1 day |
| 9 | Log Forwarding/Retention | ABSENT -- relies on Railway retention | MEDIUM | No | 1 day |
| 10 | Backend Metrics Export | ABSENT -- in-memory only | LOW | No | 2 days |
| 11 | Login/Logout Event Capture | ABSENT -- Supabase handles, no webhook | LOW | No | 1 day |
| 12 | SLI/SLO Definitions | ABSENT -- no formal targets | LOW | No | 0.5 day |
| 13 | OAuth token prefix in console | PRESENT -- line 125 of callback | LOW (security) | No | 5 min |

---

## 10. Critical Gaps for GTM

### Must-Fix Before Launch (GTM Blockers)

1. **INSTALL ERROR TRACKING (Sentry recommended) for both backend and frontend.**
   - Backend: `pip install sentry-sdk[fastapi]`, add `sentry_sdk.init()` in `main.py` before app creation
   - Frontend: `npx @sentry/wizard@latest -i nextjs` (generates config files automatically)
   - Configure `SENTRY_DSN` environment variable on Railway (already placeholder in `.env.example`)
   - Captures: unhandled exceptions, 500 errors, JS errors, unhandled promise rejections
   - Free tier: 5,000 events/month -- sufficient for early GTM
   - **This is the single highest-ROI observability investment.**

2. **CONFIGURE AUTOMATED ALERTING for critical failure conditions.**
   - Minimum viable setup (zero-code option):
     - **UptimeRobot free tier**: Monitor `https://bidiq-backend-production.up.railway.app/health` and `https://smartlic.tech/api/health` every 5 min, email alert on failure
     - **Sentry alert rules**: Error rate > 5% in 5 minutes -> email notification
   - Must alert real email addresses, not placeholder `devops@example.com`
   - Total setup time: ~1 hour

### Should-Fix Before Launch (High Priority)

3. **Add `global-error.tsx` to frontend** for root layout error recovery.

4. **Switch to JSON-structured logging.** Install `python-json-logger`, change one line in `config.py` formatter. Enables Railway structured log search and future log forwarding.

5. **Remove token prefix logging from production OAuth callback.** Gate `console.log` statements in `app/auth/callback/page.tsx` behind `process.env.NODE_ENV === 'development'`.

---

## 11. Recommended Monitoring Stack

### Phase 1: GTM (1-2 days, $0/month)

| Tool | Purpose | Cost | Priority |
|------|---------|------|----------|
| **Sentry** (free tier) | Error tracking -- backend + frontend | Free (5K errors/mo) | P0 |
| **UptimeRobot** (free tier) | Uptime monitoring + email alerts | Free (50 monitors) | P0 |
| **python-json-logger** | JSON-structured backend logs | Free (OSS) | P1 |

**Sentry Backend Integration (`backend/main.py`):**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration(), StarletteIntegration()],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        environment=os.getenv("ENVIRONMENT", "production"),
        release=app.version,
    )
```

**Sentry Frontend Integration:**
```bash
npx @sentry/wizard@latest -i nextjs
# Generates: sentry.client.config.ts, sentry.server.config.ts, sentry.edge.config.ts
# Add SENTRY_DSN and SENTRY_AUTH_TOKEN to Railway env vars
```

**UptimeRobot Monitors:**
- `GET /health` on backend (every 5 min, email on 2 consecutive failures)
- `GET /api/health` on frontend (every 5 min, email on 2 consecutive failures)

### Phase 2: First Month (3-5 days)

| Tool | Purpose | Cost |
|------|---------|------|
| **Sentry Performance** | Transaction tracing, slow query detection | Free tier included |
| **Supabase Auth Hooks** | Capture login/logout events to audit table | Free (Supabase included) |
| **`audit_events` DB table** | Persistent audit trail for auth + admin + billing events | Free (Supabase included) |
| **JSON logs + Railway log drains** | Forward logs to durable storage | Varies by destination |

### Phase 3: At Scale (when needed)

| Tool | Purpose | Cost |
|------|---------|------|
| **Grafana Cloud** or **Datadog** | Unified metrics dashboards, custom alerts | $15-50/mo |
| **OpenTelemetry SDK** | W3C standard distributed tracing | Free (OSS) |
| **PagerDuty** or **OpsGenie** | On-call rotation, escalation policies | $20-50/mo |
| **prometheus_client** | Application metrics export (counters, histograms) | Free (OSS) |

---

## Appendix: Key File References

| File | Relevant Lines | What It Contains |
|------|---------------|------------------|
| `backend/config.py` | 63-127 | `setup_logging()`: format, RequestIDFilter, level enforcement |
| `backend/config.py` | 222-227 | Import-time feature flag logging (race condition risk) |
| `backend/middleware.py` | 1-71 | `CorrelationIDMiddleware`, `RequestIDFilter`, `request_id_var` |
| `backend/log_sanitizer.py` | 1-606 | Full PII masking suite, `SanitizedLogAdapter`, audit log helpers |
| `backend/health.py` | 1-360 | Health check module with source probing, uptime tracking |
| `backend/main.py` | 193-266 | `/health` endpoint: Supabase + OpenAI + Redis checks |
| `backend/main.py` | 269-356 | `/sources/health` endpoint: multi-source health |
| `backend/railway.toml` | 16-19 | Health check path, timeout, restart policy |
| `backend/requirements.txt` | 1-36 | No sentry-sdk, no prometheus, no structlog |
| `backend/webhooks/stripe.py` | 80-141 | Webhook processing with DB audit trail |
| `backend/auth.py` | 42-137 | JWT validation with sanitized auth event logging |
| `backend/admin.py` | 350-608 | Admin operations with `log_admin_action()` calls |
| `backend/pncp_resilience.py` | 31-183 | In-memory UF performance metrics (not exported) |
| `frontend/app/error.tsx` | 1-65 | Error boundary: `console.error` only, no Sentry |
| `frontend/app/api/health/route.ts` | 1-5 | Trivial `{"status":"ok"}` health check |
| `frontend/middleware.ts` | 1-173 | Auth middleware: `console.error` on failure |
| `frontend/app/components/AnalyticsProvider.tsx` | 1-81 | Mixpanel initialization and page tracking |
| `frontend/hooks/useAnalytics.ts` | 1-66 | `trackEvent()` wrapper for business events |
| `frontend/app/auth/callback/page.tsx` | 125 | Token prefix leaked to console in production |
| `frontend/package.json` | 1-69 | No @sentry/nextjs in dependencies |
| `frontend/railway.toml` | 14 | Frontend health check path |
| `.env.example` | 110-111 | `SENTRY_DSN=` empty placeholder |
| `docs/runbooks/monitoring-alerting-setup.md` | 1-817 | Comprehensive but unimplemented monitoring plan |

---

**Bottom Line:** SmartLic has a surprisingly solid *foundation* for observability -- correlation IDs, log sanitization, health checks, and audit logging helpers are all well-implemented in code. The critical gap is the "last mile": these building blocks are not connected to any external service that would **wake someone up** when things go wrong. Installing Sentry (~2 hours) and configuring UptimeRobot (~30 minutes) would close the two GTM-blocking gaps and transform the system from "invisible failures" to "we know before the customer does."
