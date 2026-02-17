# D05: Failure Transparency | D06: Observability

**Assessment Date:** 2026-02-17
**Assessor:** @architect (Phase 5 -- GTM-OK v2.0)
**Method:** Cross-referencing Phase 1 pipeline evidence (D01-D04) and Phase 6 security/infra evidence (D10-D11) with direct frontend component and backend middleware analysis.

---

## D05: Failure Transparency -- Score: 7/10

---

### 5.1 User-Facing Error States Inventory

SmartLic has a comprehensive set of dedicated UI components for every failure mode in the search pipeline:

| Component | File | Failure Scenario | User Message | Recovery Action |
|-----------|------|------------------|--------------|-----------------|
| `DegradationBanner` | `buscar/components/DegradationBanner.tsx` | One or more data sources failed/timed out but partial results available | Per-source status breakdown (ok/timeout/error/skipped) with human-readable labels | Collapsible details + "Tentar novamente" button |
| `CacheBanner` | `buscar/components/CacheBanner.tsx` | All live sources failed; stale cache served | "Resultados de [relative time] ([source names]). Dados podem estar desatualizados." | "Tentar atualizar" button |
| `TruncationWarningBanner` | `buscar/components/TruncationWarningBanner.tsx` | Results hit page limit on one or more sources | Per-source truncation detail (PNCP/PCP) + actionable advice to refine filters | Guidance to reduce UFs/period/value range |
| `SourcesUnavailable` | `buscar/components/SourcesUnavailable.tsx` | ALL sources failed AND no cache available | "Nossas fontes de dados governamentais estao temporariamente indisponiveis" | 30s cooldown retry + "Ver ultima busca salva" fallback |
| `PartialResultsPrompt` | `buscar/components/PartialResultsPrompt.tsx` | Search exceeding 15 seconds | Offers to show partial results | Accept partial / continue waiting |
| Error boundary | `app/error.tsx` | Unhandled React errors | "Ops! Algo deu errado" + Sentry report | "Tentar novamente" + support/help links |
| Global error boundary | `app/global-error.tsx` | Root-level unhandled errors | Generic error page | Recovery action |
| EmptyState | `buscar/components/EmptyState.tsx` | Zero results after filtering | Filter rejection breakdown with per-reason counts | "Ajustar criterios de busca" |
| Quota exceeded | Within `SearchResults.tsx` | Monthly quota limit reached | "Escolha um plano para continuar buscando" | "Ver Planos" CTA |

### 5.2 Error Communication Quality

**Strengths (+):**

1. **Non-technical language throughout.** Error messages are in Portuguese and describe the situation ("fontes governamentais temporariamente indisponiveis") without exposing internal error codes, stack traces, or HTTP status codes.

2. **Per-source transparency.** The `DegradationBanner` component (AC21-23) shows a collapsible detail section with per-source status (ok/timeout/error/skipped) and record counts. Source names are humanized ("Fonte principal" for PNCP, "Fonte secundaria" for PCP).

3. **Every error state has a recovery action.** No dead ends. SourcesUnavailable offers retry + "last saved search." DegradationBanner offers retry. CacheBanner offers refresh. EmptyState suggests filter adjustments. Error boundary offers reset + support link.

4. **Cooldown prevents panic-clicking.** Both SourcesUnavailable and search error retry use 30-second cooldowns to prevent hammering failing APIs.

5. **ARIA attributes are correct.** All banners use `role="alert"` and `aria-live="polite"` for screen reader announcements.

6. **Cache staleness communicated clearly.** CacheBanner uses `Intl.RelativeTimeFormat` for relative time ("ha 30 minutos") and names which sources contributed to cached data (AC8r).

7. **Truncation is source-specific.** TruncationWarningBanner distinguishes between PNCP-only, PCP-only, and both-source truncation.

**Weaknesses (-):**

1. **No proactive staleness indicator on normal results.** When results are fresh from live sources, there is no "as of" timestamp. Users cannot tell if results are from 1 minute ago or 4 hours ago (InMemory cache hit).

2. **Source name inconsistency.** DegradationBanner uses "Fonte principal"/"Fonte secundaria" while CacheBanner and TruncationWarningBanner use explicit names "PNCP"/"Portal de Compras Publicas." The abstracted names in DegradationBanner are less transparent.

3. **No notification for persistent failures.** If a user's search consistently fails, there is no mechanism to notify them when sources recover.

4. **Error.tsx exposes raw `error.message`.** The global error boundary displays `error.message` in a monospace block. Some backend error messages may contain internal details (function names, module paths) that are not user-friendly.

### 5.3 Backend-to-Frontend Error Propagation

The error propagation chain is well-designed:

```
Backend: AllSourcesFailedError / PNCPDegradedError
    |
    v
search_pipeline.py: catches, sets ctx.is_partial + ctx.degradation_reason
    |
    v
BuscaResponse: includes is_partial, degradation_reason, cached, cached_at,
               cached_sources, is_truncated, truncated_ufs, truncation_details,
               sources_used, data_source_status[]
    |
    v
Frontend: useSearch hook interprets response fields
    |
    v
SearchResults: conditionally renders DegradationBanner / CacheBanner /
               TruncationWarningBanner / SourcesUnavailable
```

Every failure mode in the backend has a corresponding UI state. The `data_source_status[]` array carries per-source details that the DegradationBanner renders directly.

### 5.4 D05 Score Justification

**Why 7/10:**
- 8+ dedicated UI components for every failure mode
- Non-technical Portuguese error messages with recovery actions throughout
- Per-source transparency with collapsible details
- Correct ARIA attributes and cooldown protections
- Well-designed backend-to-frontend error propagation chain
- (-1) No proactive freshness indicator on normal results
- (-1) Source name inconsistency across components
- (-1) Error.tsx leaks raw error.message text

---

## D06: Observability -- Score: 5/10

---

### 6.1 Instrumentation Quality (Code-Level): 9/10

| Layer | Implementation | Evidence |
|-------|---------------|----------|
| **Request correlation** | `CorrelationIDMiddleware` generates/propagates `X-Request-ID` on every request; stored in `ContextVar`; injected into all log records via `RequestIDFilter` | middleware.py L29-70 |
| **Structured logging** | JSON format in production via `python-json-logger`; configurable via `LOG_FORMAT` | config.py L118-135 |
| **Log sanitization** | `log_sanitizer.py` with 6 masking functions (email, API key, token, user ID, IP, phone); auto-detection patterns | log_sanitizer.py (606 lines) |
| **Error tracking (backend)** | `sentry_sdk.init()` with `FastApiIntegration`, `traces_sample_rate=0.1`, PII scrubbing via `before_send` callback | main.py L128-135 |
| **Error tracking (frontend)** | `@sentry/nextjs` with source map upload, `/monitoring` tunnel route | next.config.js L73-94 |
| **Health check** | `/health` with dependency checks (Supabase, OpenAI, Redis) + per-source circuit breaker status | main.py L330-417 |
| **Request timing** | Duration logged per-request in ms | middleware.py L52-58 |
| **Analytics (frontend)** | Mixpanel + GA4 with LGPD consent gating, 25+ event types | AnalyticsProvider.tsx, useAnalytics.ts |
| **Circuit breaker status** | Per-source state exposed in `/health` response | main.py L389-392 |
| **Deprecation tracking** | RFC 8594 headers + once-per-path logging for legacy routes | middleware.py L73-130 |

### 6.2 Deployment Reality

Despite excellent code, deployment status is uncertain for critical components:

| Component | Code Status | Deployed? | Evidence |
|-----------|-------------|-----------|----------|
| Sentry (backend) | Configured | **UNCERTAIN** | `.env.example` has empty `SENTRY_DSN=`; STORY-211 setup unconfirmed |
| Sentry (frontend) | Configured | **UNCERTAIN** | `NEXT_PUBLIC_SENTRY_DSN` build arg status unknown |
| Mixpanel | Configured | **NO** | STORY-219 AC2 UNCHECKED; `.env.example` empty token |
| GA4 | Configured | **UNCERTAIN** | `NEXT_PUBLIC_GA4_MEASUREMENT_ID` not documented in `.env.example` |
| Structured logging | Configured | **YES** | Railway captures stdout |
| Request correlation | Configured | **YES** | Middleware runs automatically |
| Health endpoint | Configured | **YES** | Railway health checks hit `/health` |

### 6.3 Alerting & Monitoring

| Capability | Status |
|------------|--------|
| Deploy failure alerting | YES (GitHub Actions) |
| Runtime error alerting | **UNCERTAIN** (Sentry-dependent) |
| API latency monitoring | **NO** (no APM) |
| Uptime monitoring | **NO** (no external monitor) |
| Log aggregation/search | **PARTIAL** (Railway viewer only) |
| Business metrics dashboard | **NO** (Mixpanel not deployed) |
| Alert routing (PagerDuty) | **NO** |
| SLO/SLA monitoring | **NO** |

### 6.4 Production Incident Proof

**Critical evidence from production logs (2026-02-17):**

```
PCP API returning 404: "A rota GET /publico/obterprocessosabertos?...&uf=AC&publicKey=... nao existe."
PNCP health canary returning 400: "must be greater than or equal to 10" (tamanhoPagina=1)
```

These errors are occurring NOW in production, causing ZERO RESULTS across ALL sectors. The team had no automated detection -- the user discovered it manually. This is a clear and present failure of operational observability.

### 6.5 D06 Score Justification

**Why 5/10:**
- (+4) Observability code is excellent: correlation IDs, structured logging, PII masking, Sentry integration, health checks, 25+ analytics events
- (+1) Health endpoint deployed and functional
- (-2) Sentry deployment uncertain for both backend and frontend
- (-1) Mixpanel confirmed NOT deployed -- zero client-side analytics
- (-1) No external monitoring (uptime, APM, log search)
- (-1) No alerting integration
- The production PCP 404 + PNCP 400 incident demonstrates the gap: system is currently broken, nobody was alerted

---

## Files Analyzed

**Backend:**
- `backend/middleware.py` (153 lines)
- `backend/main.py` (referenced -- Sentry, health endpoint)
- `backend/config.py` (referenced -- logging config)
- `backend/log_sanitizer.py` (606 lines, referenced)
- `backend/consolidation.py` (referenced -- AllSourcesFailedError, degradation_reason)
- `backend/search_pipeline.py` (referenced -- error handling, ctx propagation)
- `backend/pncp_client.py` (referenced -- PNCPDegradedError, circuit breaker)

**Frontend:**
- `frontend/app/buscar/components/DegradationBanner.tsx` (238 lines)
- `frontend/app/buscar/components/CacheBanner.tsx` (138 lines)
- `frontend/app/buscar/components/TruncationWarningBanner.tsx` (94 lines)
- `frontend/app/buscar/components/SourcesUnavailable.tsx` (137 lines)
- `frontend/app/buscar/components/PartialResultsPrompt.tsx` (referenced)
- `frontend/app/error.tsx` (86 lines)
- `frontend/app/global-error.tsx` (referenced)

**Cross-reference:**
- `docs/gtm-ok/evidence/D01-D04-multi-source-pipeline.md`
- `docs/gtm-ok/evidence/D10-D11-security-infra.md`
- `docs/gtm-ok/evidence/D12-D15-rapid-scan.md`
