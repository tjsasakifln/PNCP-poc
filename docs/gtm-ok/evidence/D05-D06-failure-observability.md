# D05+D06: Failure Transparency & Observability

**Assessed by:** Claude Opus 4.6 (Phase 5, GTM-OK workflow)
**Date:** 2026-02-16
**Files Reviewed:** 28 source files across backend and frontend

---

## Score: D05 (Failure Transparency): 7/10
## Score: D06 (Observability): 5/10

---

## D05: Failure Transparency Matrix

### Summary

The frontend has an exceptionally mature error handling system with user-friendly Portuguese messages, retry mechanisms, degradation banners, and multiple fallback states. The backend maps every PNCP failure to an appropriate HTTP code with a human-readable `detail`. The gap lies in **Stripe checkout completion** (P0 webhook gap) and **network disconnection** handling (no offline detection).

### Detailed Scenario Analysis

| # | Scenario | User Message | Next Steps Provided | Backend Log | Grade |
|---|----------|-------------|---------------------|-------------|-------|
| 1 | PNCP API down (5xx) | "Nossas fontes de dados estao temporariamente indisponiveis. Tente novamente em alguns instantes ou reduza o numero de estados selecionados." | Retry button (30s cooldown), reduce states suggestion | `logger.error("PNCP API error: {e}", exc_info=True)` with req_id correlation | **9/10** |
| 2 | PNCP rate limit (429) | "As fontes de dados estao temporariamente limitando consultas. Aguarde {retry_after} segundos e tente novamente." | Retry-After header, timed retry | `logger.error("PNCP rate limit exceeded: {e}")` + Retry-After propagated | **9/10** |
| 3 | Stripe checkout fails (API error) | `getUserFriendlyError(err)` via toast.error | User stays on /planos page, can retry | `trackEvent("checkout_failed")` in frontend; backend logs HTTPException | **7/10** |
| 4 | Stripe checkout.session.completed | **NO HANDLER** -- `_activate_plan()` exists but is NEVER called because `checkout.session.completed` is NOT in the webhook handler's event type switch | User sees success_url redirect but plan may NOT activate | Webhook logs "Unhandled event type: checkout.session.completed" at INFO level only | **2/10 -- P0 GAP** |
| 5 | Auth token expires mid-session | Frontend: `window.location.href = "/login"` with search state saved to localStorage. Backend: HTTPException 401 "Token expirado" | Redirects to login, restores search state after re-auth | `logger.warning("JWT token expired")` + `log_auth_event(success=False)` | **8/10** |
| 6 | Auth token invalid | Backend: HTTPException 401 "Token invalido". Login page: translated Supabase errors | Login page with clear error messages | Sanitized log: only exception type, never token content | **8/10** |
| 7 | Quota exceeded (monthly) | "Limite de {N} buscas mensais atingido. Renovacao em {date} ou faca upgrade." | "Ver Planos" button links to /planos | `logger.info()` with masked user_id and quota details | **9/10** |
| 8 | Trial expired | "Seu trial expirou. Veja o valor que voce analisou e continue tendo vantagem." | TrialConversionScreen with personalized value metrics + CTA to /planos | Logged via quota.py check | **9/10** |
| 9 | Paid plan expired (beyond grace) | "Sua assinatura {plan_name} expirou. Renove para continuar com acesso completo." | Implicit redirect to plans | Logged with grace period details | **7/10** |
| 10 | Server error (500) | "Erro interno do servidor. Tente novamente em alguns instantes." | Retry button with 30s cooldown | `logger.exception("Internal server error during procurement search")` with full traceback | **8/10** |
| 11 | Network disconnection | `getUserFriendlyError` maps "fetch failed" / "Failed to fetch" to "Erro de conexao. Verifique sua internet." | Retry button available, but NO proactive offline detection | No backend log (request never arrives) | **6/10** |
| 12 | Partial source failure (some UFs) | DegradationBanner (yellow) + FailedUfsBanner (blue info) with per-source detail | "Consultar estados restantes" retry button | `is_partial` flag in response + per-source status | **10/10** |
| 13 | All sources down (0 results, partial) | SourcesUnavailable full-screen: "Nossas fontes de dados governamentais estao temporariamente indisponiveis" | Retry with 30s cooldown + "Ver ultima busca salva" | Source health logged per-source | **9/10** |
| 14 | Zero results (legitimate, not API failure) | EmptyState with filter rejection breakdown (keyword/value/UF counts) + actionable suggestions | "Ajustar criterios de busca" button + 3 specific suggestions | Session saved with total_raw/total_filtered for diagnostics | **10/10** |
| 15 | Download file expired (404) | "Arquivo expirado. Faca uma nova busca para gerar o Excel." | Implicit: search again | Frontend-only error, no specific backend log | **7/10** |
| 16 | Date range exceeds plan limit | Full message passed through: "O periodo de busca nao pode exceder {N} dias (seu plano: {plan_name}). Voce tentou buscar {M} dias." | User knows exact limit and how to fix | Logged as 403 with error_code DATE_RANGE_EXCEEDED | **9/10** |
| 17 | Rate limit (2/min client) | "Limite de requisicoes excedido (2/min). Aguarde {N} segundos e tente novamente." | Wait timer shown | error_code RATE_LIMIT logged | **8/10** |
| 18 | invoice.payment_failed | **NO HANDLER** -- webhook only handles `invoice.payment_succeeded`, not `invoice.payment_failed` | User receives NO notification of failed payment | Webhook logs "Unhandled event type" at INFO | **1/10 -- P0 GAP** |
| 19 | Unhandled JS exception (any page) | error.tsx: "Ops! Algo deu errado" + error.message displayed + "Tentar novamente" button + support links | Retry button + support link (/mensagens) + help link (/ajuda) | Sentry.captureException(error) + analytics tracking | **8/10** |
| 20 | Root layout crash | global-error.tsx: Full HTML shell with "Ops! Algo deu errado" + retry button + support links | Retry button + support/help links | Sentry.captureException(error) | **8/10** |

### File Evidence for Key Scenarios

**Scenario 1 (PNCP API down):**
- Backend: `backend/routes/search.py` L217-229 -- maps `PNCPAPIError` to HTTP 502 with user-friendly detail
- Frontend: `frontend/app/buscar/hooks/useSearch.ts` L282-283 -- client retries 500/502/503 up to 2 times before showing error
- Frontend: `frontend/lib/error-messages.ts` L21 -- maps "502" to "O portal PNCP esta temporariamente indisponivel"
- Frontend: `frontend/app/buscar/components/SearchResults.tsx` L209-236 -- error display with retry button + 30s cooldown

**Scenario 4 (checkout.session.completed -- P0 GAP):**
- Backend: `backend/webhooks/stripe.py` L120-127 -- switch statement handles `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded` but **NOT** `checkout.session.completed`
- Backend: `backend/routes/billing.py` L82-112 -- `_activate_plan()` function exists and is correct, but no code path calls it
- Consequence: User pays via Stripe, gets redirected to success_url, but their plan is NEVER activated in the database
- This was previously identified in the GTM-OK pre-assessment and remains unfixed

**Scenario 18 (invoice.payment_failed -- P0 GAP):**
- Backend: `backend/webhooks/stripe.py` L120-127 -- no handler for this event type
- Consequence: When a payment fails (card declined, expired, insufficient funds), the user receives no notification
- Combined with missing `checkout.session.completed`, the entire payment lifecycle has gaps

**Scenario 11 (Network disconnection):**
- Frontend: `frontend/lib/error-messages.ts` L8-12 -- five variants of network error all map to "Erro de conexao. Verifique sua internet."
- Gap: No `navigator.onLine` listener or ServiceWorker offline detection. Error only appears AFTER a failed fetch attempt, not proactively.

---

## D06: Observability Diagnostic Test

### Can We Answer These Questions Within 5 Minutes?

| # | Question | Can Answer? | How? | Estimated Time | Grade |
|---|----------|------------|------|----------------|-------|
| 1 | "What happened with user X's search 10 minutes ago?" | PARTIAL | Correlation: Backend logs have `req_id={uuid}` per request (middleware.py L55-57). Search sessions saved to `search_sessions` table with user_id, UFs, dates, total_filtered, valor_total. **However**: No log aggregation service configured (see below). Must SSH into Railway and grep logs manually. | 5-15 min | **5/10** |
| 2 | "Why did user X get 0 results?" | YES (if logs accessible) | Backend `search_pipeline.py` saves `FilterStats` with rejection counts (rejeitadas_keyword, rejeitadas_valor, rejeitadas_uf). Stored in response AND in `search_sessions` table. Frontend also shows EmptyState with breakdown. | 3-5 min via DB query | **7/10** |
| 3 | "How long did user X's search take?" | YES | Middleware logs duration: `"GET /buscar -> 200 (1234ms) [req_id=xxx]"` (middleware.py L55-57). Also: frontend tracks `time_elapsed_ms` in `search_completed` analytics event. | 2-3 min | **7/10** |
| 4 | "Did user X's payment go through?" | PARTIAL | Stripe webhook events stored in `stripe_webhook_events` table with event_id, type, processed_at, payload. **But**: `checkout.session.completed` is unhandled (logged as "Unhandled event type" at INFO). Must cross-reference Stripe Dashboard for checkout events. | 5-10 min (requires Stripe Dashboard) | **4/10** |
| 5 | "Is PNCP API currently degraded?" | YES | `/health` endpoint (main.py L327-412) checks Supabase, OpenAI, Redis. `/sources/health` (main.py L415+) checks per-source health with response times. `health.py` has dedicated `check_source_health()` for PNCP with timeout/connection error detection. Circuit breaker status exposed. | <1 min | **9/10** |

### Observability Infrastructure Assessment

#### What IS Configured (Code Level)

| Component | Status | Evidence |
|-----------|--------|----------|
| **Request correlation IDs** | EXCELLENT | `middleware.py` L29-70: Every request gets UUID, logged in format `[req_id={uuid}]`, returned in `X-Request-ID` header |
| **Frontend correlation IDs** | GOOD | `correlationId.ts`: Per-session UUID stored in sessionStorage, sent as `X-Correlation-ID` header on every request |
| **Structured logging (backend)** | GOOD | `log_sanitizer.py`: 606-line module with PII masking (emails, tokens, IPs, passwords). `SanitizedLogAdapter` class auto-sanitizes. Specialized helpers: `log_user_action()`, `log_admin_action()`, `log_auth_event()` |
| **Audit trail** | GOOD | `audit.py`: Dual-destination (stdout + Supabase `audit_events` table). SHA-256 hashed identifiers. 10 valid event types covering auth, admin, billing, data operations. Correlation ID included. |
| **Health checks** | EXCELLENT | `/health` checks Supabase, OpenAI, Redis, per-source status, circuit breaker. `/sources/health` checks all procurement sources with response times. Always returns 200 for Railway. |
| **Sentry integration (backend)** | CODE READY, LIKELY NOT DEPLOYED | `main.py` L125-131: `sentry_sdk.init()` called only if `SENTRY_DSN` env var is set. `config.py` L522: `SENTRY_DSN` is in "recommended" (not required) vars. `.env.example` L130: `SENTRY_DSN=` (empty). Pre-assessment noted "Sentry DSN not configured" in production. |
| **Sentry integration (frontend)** | CODE READY, LIKELY NOT DEPLOYED | `sentry.client.config.ts` L5-13: Init only if `NEXT_PUBLIC_SENTRY_DSN` is set. `error.tsx` L18: `Sentry.captureException(error)` called. `global-error.tsx` L19: Same. `.env.example` L131: `NEXT_PUBLIC_SENTRY_DSN=` (empty). |
| **Mixpanel analytics** | CODE READY, LIKELY NOT DEPLOYED | `useAnalytics.ts` L80: All tracking gated behind `process.env.NEXT_PUBLIC_MIXPANEL_TOKEN`. `.env.example` L122: `NEXT_PUBLIC_MIXPANEL_TOKEN=` (empty). Pre-assessment noted "Mixpanel token not set (zero analytics data)". |
| **Search session persistence** | GOOD | `search_pipeline.py` calls `quota.save_search_session()` for every search (even zero results). Stores user_id, sectors, UFs, dates, total_filtered, valor_total. Queryable via Supabase. |
| **Deprecation tracking** | GOOD | `middleware.py` L73-130: `DeprecationMiddleware` adds RFC 8594 headers and logs once-per-path warning for legacy routes. |

#### What is NOT Configured (Deployment Level)

| Component | Status | Impact |
|-----------|--------|--------|
| **Sentry DSN (production)** | NOT SET | `error.tsx` and `global-error.tsx` call `Sentry.captureException()` but it is a no-op. Backend `sentry_sdk.init()` is never called. **All unhandled exceptions in production are invisible.** |
| **Mixpanel token (production)** | NOT SET | All 50+ `trackEvent()` calls throughout the frontend are no-ops. **Zero analytics data is being collected.** Search started, search completed, search failed, checkout initiated, download completed -- all lost. |
| **Log aggregation service** | NONE | Railway provides `railway logs` CLI and web dashboard, but there is no Datadog, Grafana Loki, CloudWatch, or similar. Logs are ephemeral -- when containers restart, historical logs may be lost. No structured query capability beyond `railway logs --tail`. |
| **Alerting** | NONE | No PagerDuty, OpsGenie, or Slack webhook configured. If PNCP goes down at 3am, nobody knows until a user complains. Health endpoint exists but nothing polls it. |
| **Error rate monitoring** | NONE | Without Sentry, there is no way to know the error rate. No percentage threshold triggers, no anomaly detection. |
| **Payment monitoring** | NONE | No Stripe webhook failure alerts. The `checkout.session.completed` gap means payments silently fail to activate plans, and there is no monitoring to catch this. |

---

## Critical Gaps

### P0: Silent Payment Failure (D05 Score Impact: -3 points)

**Files:** `backend/webhooks/stripe.py` L120-127, `backend/routes/billing.py` L82-112

The webhook handler does NOT process `checkout.session.completed`. When a user completes Stripe checkout:
1. Stripe sends `checkout.session.completed` webhook
2. Backend logs "Unhandled event type: checkout.session.completed" (L127)
3. `_activate_plan()` (billing.py L82) is NEVER called
4. User's `profiles.plan_type` stays as `free_trial`
5. User has been charged but gets no premium access

Similarly, `invoice.payment_failed` is not handled, so users whose cards decline on renewal receive no notification and their subscription quietly lapses.

**User impact:** Paying customers silently do not receive their purchased plan. This is a revenue and trust destroyer.

### P1: Observability is Code-Complete but Deployment-Absent (D06 Score Impact: -4 points)

**Files:** `sentry.client.config.ts` L5-7, `main.py` L125-128, `useAnalytics.ts` L80, `.env.example` L122+130

The codebase has excellent observability instrumentation:
- 50+ Mixpanel events (search, download, checkout, errors)
- Sentry integration in both frontend error boundaries
- Backend Sentry with FastAPI/Starlette integrations
- Correlation IDs on every request (frontend + backend)
- Audit trail with Supabase persistence

But in production, `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN`, and `NEXT_PUBLIC_MIXPANEL_TOKEN` are all empty strings. The entire observability pipeline is dark.

**Diagnosis capability:** Without Sentry, answering "what went wrong for user X?" requires SSHing into Railway, hoping logs haven't rotated, and grepping through unstructured text. This is a 15-30 minute task instead of a 1-minute Sentry search.

### P1: No Proactive Offline Detection (D05 Score Impact: -1 point)

**File:** `frontend/lib/error-messages.ts` L8-12

Network errors are mapped to user-friendly messages, but only AFTER a fetch fails. There is no `navigator.onLine` event listener, no ServiceWorker, and no proactive banner that says "You appear to be offline." Users could type in search parameters and hit "Search" before discovering they have no connection.

### P2: No Alerting Infrastructure

No integration with any alerting service (PagerDuty, OpsGenie, Slack webhooks). The health endpoint (`/health`) is comprehensive but nothing monitors it. PNCP degradation, Supabase outages, and Redis failures go unnoticed until a user reports a problem.

### P2: Ephemeral Logs

Railway logs are not persisted to a durable log aggregation service. Container restarts or redeployments may lose historical logs. For regulatory compliance (LGPD audit requirements), the `audit_events` Supabase table provides persistence, but operational logs (search durations, error rates, PNCP response times) are ephemeral.

---

## Strengths Worth Preserving

1. **Error message architecture** (`frontend/lib/error-messages.ts`): The `getUserFriendlyError()` function with its ERROR_MAP pattern is production-grade. It handles 20+ error variants, strips technical jargon, preserves plan-limit messages via `keep_original`, and has a robust fallback chain (exact match -> partial match -> jargon check -> length check -> generic).

2. **Degradation UI system** (5 components): `DegradationBanner`, `FailedUfsBanner`, `PartialResultsBanner`, `SourcesUnavailable`, `EmptyState` -- this is among the best degradation UX seen in Brazilian SaaS. Each component targets a specific failure mode with appropriate severity coloring and actionable next steps.

3. **Correlation ID chain**: Frontend generates session-level correlation IDs (`correlationId.ts`), sends them as `X-Correlation-ID`, and backend generates per-request IDs (`middleware.py`). Both are logged. This chain, once connected to a log aggregation service, will enable full distributed tracing.

4. **Audit trail**: `audit.py` with dual-destination (stdout + Supabase), SHA-256 hashed PII, and 10 validated event types is LGPD-ready. The fail-safe design (stdout always logs even if Supabase write fails) ensures audit visibility is never lost.

5. **Health endpoint**: `/health` (main.py L327-412) checks every dependency (Supabase, OpenAI, Redis, per-source PNCP status, circuit breaker). Returns 200 always (correct for Railway) with degradation status in body. Ready for external monitoring -- just needs something to poll it.

6. **Client-side retry logic**: `useSearch.ts` L248-328 implements up to 2 automatic retries with delays (3s, 8s) for 500/502/503 errors, plus force-fresh cache bypass. Search state is saved to localStorage before auth redirects and restored after re-login.

7. **PII-safe logging**: `log_sanitizer.py` (606 lines) is comprehensive -- masks emails, API keys, tokens, user IDs, IPs, phones, passwords. `SanitizedLogAdapter` auto-sanitizes all log calls. Auto-detection patterns catch leaked secrets in free-text log messages.

---

## Recommendations (Prioritized)

### Must-Fix Before GTM (P0)

1. **Handle `checkout.session.completed` webhook** -- Add handler that calls `_activate_plan()`. Without this, every paying customer's plan activation is broken. (Estimated: 30 min)

2. **Handle `invoice.payment_failed` webhook** -- Send user email notification + log the event. Without this, card declines are invisible. (Estimated: 1 hour)

3. **Set SENTRY_DSN and NEXT_PUBLIC_SENTRY_DSN in Railway** -- The code is ready, just needs the env vars. Create Sentry project (5 min), set 2 env vars (2 min), redeploy. (Estimated: 15 min)

### Should-Fix Before GTM (P1)

4. **Set NEXT_PUBLIC_MIXPANEL_TOKEN in Railway** -- Unlocks 50+ analytics events already instrumented. (Estimated: 10 min)

5. **Add offline detection** -- `navigator.onLine` + `window.addEventListener('offline')` with a top-level banner component. (Estimated: 1 hour)

6. **Configure uptime monitoring** -- Point UptimeRobot, Better Uptime, or similar at `/health` endpoint. Set up Slack/email alerts for degraded/unhealthy status. (Estimated: 30 min)

### Nice-to-Have (P2)

7. **Log aggregation** -- Connect Railway logs to Datadog, Grafana Cloud, or Axiom. Enable structured JSON logging format.

8. **Stripe webhook failure alerts** -- Configure Stripe Dashboard webhook alerts for consecutive failures.

9. **Add error rate dashboard** -- Once Sentry is live, configure error rate alerts (>1% 5xx rate triggers alert).
