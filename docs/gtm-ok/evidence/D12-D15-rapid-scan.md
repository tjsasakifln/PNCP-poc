# D12-D15 Rapid Scan Evidence

**Date:** 2026-02-17
**Analyst:** @analyst (Phase 7, GTM-OK v2.0)
**Method:** Fresh codebase analysis, no reuse of prior assessments

---

## D12: Pricing-Risk Alignment

**Score: 7/10 (Production-ready)**

### What Was Examined

- `frontend/app/planos/page.tsx` -- pricing page, plan display, checkout flow
- `backend/routes/billing.py` -- plan definitions, Stripe checkout, billing portal
- `backend/webhooks/stripe.py` -- subscription lifecycle (creation, update, cancellation)
- `frontend/app/conta/page.tsx` -- subscription management, cancel button
- `frontend/lib/copy/valueProps.ts` -- ROI messaging and framing
- `frontend/lib/copy/comparisons.ts` -- defensive messaging vs. competitors

### Pricing Structure

| Period | Monthly Cost | Total | Discount |
|--------|-------------|-------|----------|
| Monthly | R$1,999 | R$1,999/mo | -- |
| Semiannual | R$1,799 | R$10,794/6mo | 10% |
| Annual | R$1,599 | R$19,188/yr | 20% |

Single plan model (SmartLic Pro) with billing period toggle. Clean, no confusion about feature tiers.

### ROI Justification (Code Evidence)

The pricing page (`planos/page.tsx` L311-330) includes an explicit ROI anchor:

```
"Uma unica licitacao ganha pode pagar um ano inteiro"
R$150,000 (oportunidade media) vs. R$19,188 (SmartLic Pro anual)
```

The copy library (`valueProps.ts` L178-189) provides calculator defaults:
- `defaultContractValue: 200_000`
- `defaultWinRate: 0.05`
- `potentialReturn: "100x"`
- Tagline: "Uma unica licitacao ganha paga o investimento do ano inteiro."

This is an illustrative example (page says "Exemplo ilustrativo com base em oportunidades tipicas do setor"). Honest framing.

### Cancel Experience

**1-click cancel EXISTS** but routed through Stripe:

1. `frontend/app/conta/page.tsx` L367-378: "Cancelar SmartLic Pro" button with confirmation modal
2. `frontend/app/api/billing-portal/route.ts`: Proxies to `backend/v1/billing-portal`
3. `backend/routes/billing.py` L88-141: Creates Stripe Billing Portal session
4. `backend/webhooks/stripe.py` L313-363: Handles `customer.subscription.deleted` event
5. Cancellation confirmation email sent (L581-619)
6. UI shows "Ativa ate [date]" with grace period after cancellation

The FAQ on the pricing page explicitly addresses cancellation:
- "Posso cancelar a qualquer momento?" -> "Sim. Sem contrato de fidelidade"
- "O que acontece se eu cancelar?" -> "Voce mantem acesso completo ate o fim do periodo atual"

### Risk Factors

1. **R$1,999/mo is premium pricing** for Brazil's procurement market. This positions SmartLic as enterprise-grade, not SMB-friendly. Target market must be companies bidding on R$100K+ contracts.
2. **No free tier** beyond the 7-day trial with 3 analyses. Conversion barrier is high.
3. **No money-back guarantee** beyond "avalie sem compromisso" 7-day trial.
4. **Cancel is via Stripe Billing Portal**, not a pure in-app 1-click. User is redirected to Stripe-hosted page. This adds friction compared to a truly native "cancel" button that calls a backend API directly.

### What Justifies 7/10

- Clean single-plan model eliminates confusion
- Honest ROI framing ("exemplo ilustrativo", not fake claims)
- Cancel path EXISTS and is documented in UI/FAQ
- Billing period toggle (monthly/semiannual/annual) gives flexibility
- Stripe handles proration automatically
- Dunning flow for failed payments (GTM-FIX-007)
- (-1) Cancel routes through Stripe portal, not pure native
- (-1) No explicit money-back guarantee
- (-1) No competitive pricing validation (no evidence of market research)

---

## D13: Analytics & Metrics

**Score: 4/10 (Not ready)**

### What Was Examined

- `frontend/app/components/AnalyticsProvider.tsx` -- Mixpanel initialization
- `frontend/hooks/useAnalytics.ts` -- Event tracking hook
- `frontend/app/components/GoogleAnalytics.tsx` -- GA4 component
- `backend/routes/analytics.py` -- Personal dashboard analytics endpoints
- `.env.example` -- Token configuration
- Audit reports: `AUDIT-FRENTE-6-BUSINESS-READINESS.md`, `STORY-219`

### Instrumentation Quality: HIGH (Code is Good)

The analytics code is comprehensive:

**Mixpanel (AnalyticsProvider.tsx):**
- LGPD-compliant: Only initializes after cookie consent (L47-57)
- Tracks: `page_load`, `page_exit` (with session duration), all consent changes
- Consent revocation handled (opt_out_tracking)

**useAnalytics Hook (useAnalytics.ts):**
- `trackEvent()`: Generic event tracker with timestamp/environment metadata
- `identifyUser()`: Links events to user profiles
- `resetUser()`: Clears identity on logout
- `captureUTMParams()`: Captures UTM attribution from URLs
- All functions check `hasAnalyticsConsent()` before firing

**Tracked Events (from codebase grep):**
- `search_started`, `search_completed`, `search_failed`
- `download_started`, `download_completed`
- `checkout_initiated`, `checkout_failed`
- `login_attempted`, `login_completed`
- `onboarding_completed`, `onboarding_dismissed`, `onboarding_step`
- `saved_search_created`, `search_state_auto_restored`
- `dashboard_viewed`, `analytics_exported`
- `plan_page_viewed`, `custom_term_search`
- `pull_to_refresh_triggered`, `error_encountered`
- `search_progress_stage`

This covers the full funnel: signups -> activation -> search -> download -> conversion -> retention.

**GA4 (GoogleAnalytics.tsx):**
- Separate GA4 component with LGPD consent check
- Predefined event helpers: `trackSearchEvent`, `trackDownloadEvent`, `trackSignupEvent`, `trackLoginEvent`, `trackPlanSelectedEvent`

**Backend Analytics (analytics.py):**
- `/analytics/summary` -- total searches, downloads, opportunities, value, hours saved
- `/analytics/searches-over-time` -- time-series data (day/week/month)
- `/analytics/top-dimensions` -- top UFs and sectors
- `/analytics/trial-value` -- trial conversion metrics

### CRITICAL PROBLEM: Token Not Deployed

Multiple audit reports confirm the token is NOT set in production:

From `AUDIT-FRENTE-6-BUSINESS-READINESS.md`:
> "Problem: `.env.local` has no `NEXT_PUBLIC_MIXPANEL_TOKEN`. Unknown if it is set in Railway production environment."

From `STORY-219`:
> "AC2: Set `NEXT_PUBLIC_MIXPANEL_TOKEN` in Railway production env vars (ops - manual)" -- checkbox UNCHECKED

From `.env.example` L122:
```
NEXT_PUBLIC_MIXPANEL_TOKEN=
```
Empty value. No actual token.

**Impact:** The entire Mixpanel analytics system is dead code in production. When `NEXT_PUBLIC_MIXPANEL_TOKEN` is empty/undefined, `AnalyticsProvider.tsx` L38-44 returns early:
```typescript
const token = process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
if (!token) {
  if (process.env.NODE_ENV === 'development') {
    console.log('Mixpanel token not configured. Analytics disabled.');
  }
  return;
}
```

Similarly, `NEXT_PUBLIC_GA4_MEASUREMENT_ID` is not documented in `.env.example` at all, meaning GA4 is also likely dead.

### Can We Measure the Funnel?

| Metric | Instrumented? | Actually Working in Prod? |
|--------|--------------|--------------------------|
| Signups | Yes (login_completed) | NO (no Mixpanel token) |
| Activations | Yes (onboarding_completed) | NO |
| Searches | Yes (search_started/completed) | NO |
| Downloads | Yes (download_started/completed) | NO |
| Conversions | Yes (checkout_initiated/checkout_failed) | NO |
| Churn | Partially (via Stripe webhooks) | Stripe data only |
| Page views | Yes (page_load) | NO |
| UTM attribution | Yes (captureUTMParams) | NO |

### What Justifies 4/10

- (+3) Instrumentation code is comprehensive, LGPD-compliant, well-tested
- (+1) Backend analytics endpoints exist and work (dashboard data from DB)
- (-3) Mixpanel token NOT deployed in production -- zero client-side analytics data
- (-2) GA4 token likely also missing
- (-1) No evidence of any analytics dashboard being configured or reviewed
- Cannot answer basic business questions: "How many users searched last week?" "What is our trial-to-paid conversion rate?"

**To reach 7/10:** Deploy Mixpanel token (15 min ops task), verify data flows, configure at least one dashboard for signup-to-conversion funnel.

---

## D14: Differentiation

**Score: 7/10 (Production-ready)**

### What Was Examined

- `backend/llm.py` -- AI analysis capability (GPT-4.1-nano)
- `backend/sectors.py` + `backend/sectors_data.yaml` -- 15 sector configurations
- `backend/clients/portal_compras_client.py` -- Portal de Compras Publicas integration
- `backend/pncp_client.py` -- PNCP API client
- `backend/consolidation.py` -- Multi-source deduplication
- `frontend/lib/copy/comparisons.ts` -- Competitive positioning copy
- `frontend/lib/copy/valueProps.ts` -- Value proposition messaging

### Competitive Moat Analysis

**1. Multi-Source Data Aggregation (Strong)**

SmartLic consolidates two official procurement data sources:
- **PNCP** (Portal Nacional de Contratacoes Publicas) -- federal/state
- **PCP** (Portal de Compras Publicas) -- complementary municipal/state

Evidence: `backend/consolidation.py` implements priority-based deduplication (PNCP=1 wins), value discrepancy monitoring (>5% cross-source delta logs warning), and the pipeline handles partial failures gracefully (if one source fails, the other still returns results).

Most competitors offer single-source searches. This dual-source approach provides genuinely broader coverage.

**2. Sector-Specific Keyword Intelligence (Strong)**

`backend/sectors_data.yaml` defines 15 specialized sectors:

| Sector | Type |
|--------|------|
| vestuario | Uniformes, fardamentos |
| alimentos | Merenda escolar |
| informatica | Hardware TI |
| mobiliario | Mobiliario |
| papelaria | Material escritorio |
| engenharia | Projetos e obras |
| software | Sistemas |
| facilities | Manutencao |
| saude | Saude |
| vigilancia | Seguranca patrimonial |
| transporte | Veiculos |
| manutencao_predial | Conservacao predial |
| engenharia_rodoviaria | Infraestrutura viaria |
| materiais_eletricos | Instalacoes eletricas |
| materiais_hidraulicos | Saneamento |

Each sector has:
- Primary keywords (high precision)
- Exclusion terms (false positive prevention)
- Context-required keywords (disambiguation)
- Max contract value thresholds (anti-false-positive for huge multi-sector contracts)

This is a genuine differentiator. Competitors typically use keyword-search where the USER must know the terms. SmartLic encodes domain expertise in 1000+ rules.

**3. AI-Powered Strategic Analysis (Medium-Strong)**

`backend/llm.py` provides:
- GPT-4.1-nano structured output via Pydantic schemas
- Strategic consultant persona with sector-specific context
- Urgency classification (alta/media/baixa based on days remaining)
- Actionable recommendations (max 5, prioritized by value + urgency + viability)
- Terminology enforcement (forbidden terms like "prazo de abertura" are validated)
- Heuristic fallback (`gerar_resumo_fallback`) when OpenAI API is unavailable

The output schema (`ResumoEstrategico`) includes:
- `resumo_executivo`: Consultive overview
- `recomendacoes`: Prioritized recommendations with action, justification, urgency
- `alertas_urgencia`: Time-sensitive alerts
- `insight_setorial`: Market context

This goes beyond "summary" to "decision intelligence" -- telling users what to DO, not just what exists.

**4. Competitive Messaging (Well-Crafted)**

`comparisons.ts` defines a 10-row comparison table covering:
- Search method (sector vs. keyword guessing)
- Intelligence (evaluation vs. raw list)
- Multi-source (2 sources vs. 1)
- Pricing transparency (fixed vs. hidden fees)
- Cancel friction (1-click vs. bureaucratic)

The copy is positioned around "decision intelligence, not search speed" (from `valueProps.ts` header comment). BANNED_PHRASES list (L364-406) explicitly prohibits commodity-positioning language ("160x mais rapido", "95% de precisao", "3 minutos", "economize tempo").

### Weaknesses

1. **No named competitor comparison** -- copy uses "traditional platforms" generically. No direct Licitanet/ComprasNet/BLL benchmarking.
2. **AI analysis quality is unvalidated** -- no systematic evaluation of GPT output quality. The forbidden-term check (L211-228) is a good start but covers only deadline terminology.
3. **Only 2 data sources** -- some competitors may aggregate more portals (state-specific portals, DOU, etc.).
4. **No proprietary data** -- all data comes from public APIs. Competitive advantage is in the filtering/analysis layer, not raw data access.

### What Justifies 7/10

- (+3) Sector-specific keyword intelligence with 15 sectors and 1000+ rules is a genuine moat
- (+2) Multi-source aggregation with dedup is a real capability advantage
- (+1) AI strategic analysis goes beyond summarization to actionable recommendations
- (+1) Well-crafted competitive positioning copy with systematic banned/preferred phrase governance
- (-1) No competitor-specific benchmarking or market validation
- (-1) AI output quality not systematically evaluated
- (-1) Two data sources is good but not comprehensive (no DOU, no state portals beyond PCP)

---

## D15: Feedback Loop Speed

**Score: 7/10 (Production-ready)**

### What Was Examined

- `.github/workflows/tests.yml` -- Unit tests CI (backend + frontend + E2E)
- `.github/workflows/backend-ci.yml` -- Backend linting, typing, security scan
- `.github/workflows/deploy.yml` -- Production deployment with health checks
- `.github/workflows/codeql.yml` -- Security scanning (CodeQL + TruffleHog + dependency review)
- `.github/workflows/lighthouse.yml` -- Performance auditing
- `.github/workflows/e2e.yml` -- End-to-end tests
- `.github/workflows/load-test.yml` -- Load testing
- `.github/workflows/staging-deploy.yml` -- Staging environment
- `.github/workflows/pr-validation.yml` -- PR validation
- `.github/workflows/cleanup.yml` -- Cleanup automation
- `.github/workflows/dependabot-auto-merge.yml` -- Dependency automation
- `.github/workflows/sync-sectors.yml` -- Sector sync automation

### CI/CD Pipeline (12 Workflows)

**Trigger Coverage:**

| Trigger | Workflows |
|---------|-----------|
| Push to main | tests, backend-ci, deploy, codeql |
| Pull request | tests, backend-ci, codeql, lighthouse, pr-validation, e2e |
| Scheduled | codeql (weekly Monday 00:00 UTC) |
| Manual dispatch | deploy (with service selector) |

**Quality Gates in CI:**

1. **Backend Tests** (tests.yml L14-88):
   - Python 3.11 + 3.12 matrix
   - pytest with coverage report
   - 70% coverage threshold enforced (L82: `if [ $COVERAGE_PERCENT -lt 70 ]`)
   - Coverage uploaded to Codecov

2. **Backend CI** (backend-ci.yml):
   - `ruff check .` -- linting
   - `mypy .` -- type checking
   - `safety check` -- vulnerability scan
   - `pytest --cov-fail-under=70` -- coverage threshold

3. **Frontend Tests** (tests.yml L90-188):
   - `npx tsc --noEmit` -- TypeScript check
   - `npm test -- --coverage --ci --no-cache`
   - Generated API types verification
   - Security audit (`npm audit`)
   - Quarantined tests run (non-blocking)
   - Coverage uploaded to Codecov

4. **E2E Tests** (tests.yml L222-411):
   - Depends on backend + frontend unit tests passing
   - Starts both servers, waits for health
   - Playwright (Chromium)
   - Uploads report artifacts (30-day retention)

5. **Security** (codeql.yml):
   - CodeQL for Python + JavaScript (security-and-quality queries)
   - TruffleHog secret scanning
   - Dependency review (fails on high severity, denies GPL-3.0/AGPL-3.0)

6. **Performance** (lighthouse.yml):
   - Lighthouse CI on PRs
   - Core Web Vitals tracking (FCP, LCP, TBT, CLS, SI)
   - PR comment with scores

### Deployment Pipeline

`deploy.yml` implements:
1. **Change detection** (L22-62): Only deploys services that changed
2. **Railway deployment** with retry logic (3 attempts, 10s backoff)
3. **Health check** post-deploy (5 attempts, 15s intervals)
4. **Smoke tests** (L183-253): Backend API, frontend page load, integration test
5. **Frontend waits for backend** (L125-129): `needs: [detect-changes, deploy-backend]`

**Deployment cadence:** Push to `main` auto-deploys. Manual dispatch available for selective service deployment.

### Test Coverage

| Component | Coverage | Threshold | Status |
|-----------|----------|-----------|--------|
| Backend | ~96.69% | 70% | PASSING |
| Frontend | ~49.46% | 60% | BELOW threshold |
| E2E | 60 test cases | Pass/fail | PASSING |

Frontend coverage is below threshold -- CI will fail until improved.

### Monitoring Gap

**Sentry is configured in code but deployment status uncertain:**
- Backend: `main.py` L126 checks `SENTRY_DSN`
- Frontend: `AnalyticsProvider.tsx` L14-21 initializes Sentry client-side
- `.env.example` has empty `SENTRY_DSN=` and `NEXT_PUBLIC_SENTRY_DSN=`
- `STORY-211-SENTRY-SETUP.md` shows Railway commands but does not confirm execution

**Would the team know within minutes if something breaks?**
- **Deploy failures:** YES -- GitHub Actions fails with health check + smoke test
- **Runtime errors:** UNCERTAIN -- depends on whether Sentry DSN is actually deployed
- **API degradation:** PARTIAL -- health endpoint exists but no alerting on response time

### What Justifies 7/10

- (+3) 12 GitHub Actions workflows covering tests, security, performance, deployment
- (+2) Automated deployment with health checks and smoke tests
- (+1) Backend coverage excellent (96.69%)
- (+1) Security scanning (CodeQL + TruffleHog + dependency review)
- (-1) Frontend coverage below threshold (49.46% vs 60% required)
- (-1) Sentry deployment status uncertain (code exists, token may not be set)
- (-1) No explicit alerting/PagerDuty integration for production incidents
- (-0) Lighthouse performance tracking in PR is a strong quality signal

---

## Score Summary

| Dimension | Score | Category | Rationale |
|-----------|-------|----------|-----------|
| **D12: Pricing-Risk** | **7/10** | Production-ready | Clean single plan, honest ROI framing, cancel path exists. Cancel via Stripe portal adds minor friction. No money-back guarantee. |
| **D13: Analytics** | **4/10** | Not ready | Excellent instrumentation code, zero production data. Mixpanel token not deployed. Cannot answer any business questions. |
| **D14: Differentiation** | **7/10** | Production-ready | 15-sector keyword intelligence, dual-source aggregation, AI strategic analysis. No competitor benchmarking. |
| **D15: Feedback Loop** | **7/10** | Production-ready | 12 CI/CD workflows, 96.69% backend coverage, auto-deploy with health checks. Frontend coverage gap, uncertain monitoring deployment. |

### Remediation Priority

| Priority | Action | Impact | Effort |
|----------|--------|--------|--------|
| **P0** | Deploy `NEXT_PUBLIC_MIXPANEL_TOKEN` to Railway | D13: 4->7 | 15 min |
| **P0** | Verify `SENTRY_DSN` is deployed in Railway | D15: 7->8 | 15 min |
| **P1** | Deploy `NEXT_PUBLIC_GA4_MEASUREMENT_ID` | D13: +0.5 | 15 min |
| **P1** | Improve frontend test coverage to 60% | D15: 7->8 | 4-8 hrs |
| **P2** | Add native in-app cancel (not Stripe redirect) | D12: 7->8 | 4 hrs |
| **P2** | Competitive benchmarking (Licitanet, BLL, ComprasNet) | D14: 7->8 | 2-4 hrs |
| **P3** | Production alerting (PagerDuty/OpsGenie) | D15: 7->9 | 4 hrs |
| **P3** | AI output quality evaluation framework | D14: 7->8 | 8 hrs |
