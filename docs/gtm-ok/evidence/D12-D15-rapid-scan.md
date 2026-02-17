# D12-D15: Rapid Scan Assessment
Date: 2026-02-16
Phase: 7 of 10

## Scores
- D12 (Pricing-Risk Alignment): 4/10
- D13 (Analytics & Metrics): 3/10
- D14 (Differentiation): 7/10
- D15 (Feedback Loop Speed): 7/10

---

## D12: Pricing-Risk Alignment

### Price Point Analysis

SmartLic Pro is priced at R$1,999/month (semiannual R$1,799/mo, annual R$1,599/mo).

**Evidence:** `frontend/app/planos/page.tsx:20-24`
```typescript
const PRICING: Record<BillingPeriod, { monthly: number; total: number; ... }> = {
  monthly: { monthly: 1999, total: 1999, period: "mes" },
  semiannual: { monthly: 1799, total: 10794, period: "semestre", discount: 10 },
  annual: { monthly: 1599, total: 19188, period: "ano", discount: 20 },
};
```

The pricing page uses an ROI anchor of "R$150,000 average opportunity vs R$19,188/year = 7.8x ROI" (`planos/page.tsx:316-329`). This is reasonable IF the tool reliably delivers winning opportunities. But the trial gives only 3 searches / 7 days -- insufficient to prove this ROI claim before asking for R$1,999/month.

### CRITICAL BUG: Checkout Mode is Wrong

**P0 FINDING:** `smartlic_pro` is NOT in the subscription mode list.

**Evidence:** `backend/routes/billing.py:63,69`
```python
is_subscription = plan_id in ("consultor_agil", "maquina", "sala_guerra")
# ...
"mode": "subscription" if is_subscription else "payment",
```

Since `smartlic_pro` is not in this tuple, Stripe creates a **one-time payment** session, NOT a recurring subscription. This directly contradicts all copy about monthly/semiannual/annual billing periods. Users paying R$1,999 would get a single payment with no recurring billing -- or worse, the Stripe Price object (which is likely set up as recurring) would fail when used in `mode: "payment"`.

### checkout.session.completed Webhook NOT Handled

The Stripe webhook handler (`backend/webhooks/stripe.py:119-127`) handles:
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`

It does NOT handle `checkout.session.completed`. The only reference in the entire codebase is in a test log sanitizer fixture (`test_log_sanitizer.py:427`), not in any handler code.

**Impact:** After a user completes checkout, `_activate_plan()` (`billing.py:82-112`) is NEVER called. The user pays but the plan is never activated. This is a revenue-critical bug.

### invoice.payment_failed NOT Handled

No handler exists for `invoice.payment_failed`. Grep confirms zero matches across the entire backend. Users whose payments fail will remain on an active plan indefinitely -- there is no dunning or grace period trigger.

### Cancellation Flow

Cancellation is available only through full account deletion (`frontend/app/conta/page.tsx`), which calls `stripe.Subscription.cancel()` as part of the deletion cascade (`routes/user.py:292`). There is NO self-service subscription cancellation without deleting the entire account.

The FAQ promises "Cancele quando quiser" (`planos/page.tsx:41,304`) and "Minha Conta" has a cancellation option (`ajuda/page.tsx:129`), but the actual `/conta` page only offers password change, data export, and account deletion. There is no "cancel subscription" button.

### Trial Value Proposition

Trial: 3 searches, 7 days, no credit card. Features list claims 1,000 analyses/month (`planos/page.tsx:28`). The 3-search trial barely demonstrates value for a R$1,999/month product. With the PNCP 500-page cap and potential for zero-result searches, a user could exhaust their trial without finding a single relevant opportunity.

### Score Justification: 4/10

- Checkout mode bug means paying users may not get their plans activated: P0
- `checkout.session.completed` not handled: P0
- `invoice.payment_failed` not handled: P1
- No self-service cancellation (only account deletion): P1
- Trial too limited to prove R$1,999/month ROI: P2
- ROI anchor is reasonable but unproven

---

## D13: Analytics & Metrics

### Mixpanel Implementation

Code infrastructure exists and is well-architected:

**AnalyticsProvider:** `frontend/app/components/AnalyticsProvider.tsx:1-128`
- Initializes Mixpanel after LGPD cookie consent
- Tracks page_load, page_exit with session duration
- Listens for consent changes

**useAnalytics hook:** `frontend/hooks/useAnalytics.ts:74-139`
- `trackEvent()` -- generic event tracking with consent check
- `identifyUser()` -- Mixpanel people profiles
- `resetUser()` -- identity reset on logout
- `trackPageView()` -- page view tracking
- UTM parameter capture (`captureUTMParams()`, lines 22-48)

**Event tracking is embedded throughout the frontend:**
- `checkout_initiated`, `checkout_failed` (`planos/page.tsx:155-182`)
- `plan_page_viewed` (`planos/page.tsx:90`)
- 41 files reference `trackEvent` or `useAnalytics`

### Production Status: NOT FUNCTIONAL

**Evidence:** `frontend/app/components/AnalyticsProvider.tsx:24-30`
```typescript
const token = process.env.NEXT_PUBLIC_MIXPANEL_TOKEN;
if (!token) {
  if (process.env.NODE_ENV === 'development') {
    console.log('Mixpanel token not configured. Analytics disabled.');
  }
  return;
}
```

From the MEMORY.md context: "Mixpanel token not set (zero analytics data)". The `NEXT_PUBLIC_MIXPANEL_TOKEN` environment variable is not configured in production. All tracking code is effectively dead code.

**Config reference:** `frontend/lib/config.ts:168-170` confirms the token comes from env:
```typescript
mixpanel: {
  token: process.env.NEXT_PUBLIC_MIXPANEL_TOKEN || '',
},
```

### Sentry: Code Exists, DSN Not Configured

**Frontend:** `frontend/sentry.client.config.ts:5-13` -- graceful no-op when `NEXT_PUBLIC_SENTRY_DSN` is absent.

**Backend:** `backend/main.py:125-128` -- conditional init with `SENTRY_DSN` env var.

From MEMORY.md: "Sentry DSN not configured" in production. Error monitoring is disabled.

### Can We Measure Key Metrics?

| Metric | Code Exists? | Production Data? |
|--------|-------------|-----------------|
| Signups | Yes (signup page tracks events) | NO -- Mixpanel not configured |
| Activations | Yes (first-search tracking) | NO |
| Searches | Yes (search_started event) | NO |
| Conversions | Yes (checkout_initiated event) | NO |
| Churn | Partially (subscription.deleted webhook logs) | Server logs only |
| MRR | NO -- no dashboard or calculation code | NO |
| LTV | NO | NO |
| Error rate | Yes (Sentry code exists) | NO -- DSN not configured |

### Revenue Metrics

There is NO code anywhere in the codebase for calculating MRR, churn rate, LTV, or any revenue metrics. The only financial data exists in Stripe's own dashboard -- there is no internal analytics layer for revenue.

### Score Justification: 3/10

- Excellent code architecture (LGPD-compliant, consent-gated, UTM tracking)
- Comprehensive event vocabulary (41 files with tracking)
- But ZERO production data -- Mixpanel token not set
- Sentry DSN not configured -- no error visibility
- No revenue metrics (MRR, LTV, churn calculations)
- The team is flying blind: no funnel visibility, no conversion tracking, no error monitoring

---

## D14: Differentiation

### What SmartLic Does

SmartLic provides automated procurement opportunity discovery from Brazil's PNCP portal with:

1. **Multi-sector keyword filtering** across 15 sectors
2. **AI-powered strategic analysis** (GPT-4.1-nano)
3. **Excel report generation** for offline analysis
4. **Multi-state parallel search** across all 27 Brazilian states

### Sector-Specific Filtering: Genuine Moat

**Evidence:** `backend/sectors_data.yaml` defines 15 sectors:
```
vestuario, alimentos, informatica, mobiliario, papelaria, engenharia,
software, facilities, saude, vigilancia, transporte, manutencao_predial,
engenharia_rodoviaria, materiais_eletricos, materiais_hidraulicos
```

Each sector has deeply curated keyword sets. The vestuario sector alone has:
- 84+ inclusion keywords (`filter.py:184-283`)
- 150+ exclusion keywords (`filter.py:294-582`)
- Red flag detection for medical/administrative/infrastructure false positives (`filter.py:637-679`)
- Context-required keywords (generic terms validated by surrounding context)
- Max contract value caps per sector (anti-false-positive)

This level of domain-specific filtering represents significant accumulated knowledge. The `context_required_keywords` mechanism (`sectors.py:29`) is particularly sophisticated -- generic terms like "mesa" or "banco" only match if confirming context words are also present.

The `match_keywords()` function (`filter.py:682-799`) implements:
- Unicode normalization for Portuguese text
- Word boundary matching with plural variation support
- Exclusion-first fail-fast optimization
- Context validation for ambiguous terms
- Pre-compiled regex patterns for batch performance

### AI Analysis: More Than a GPT Wrapper

**Evidence:** `backend/llm.py:127-169` -- the system prompt is a 42-line strategic consultant persona:

- Acts as a "consultor senior com 15 anos de experiencia"
- Provides concrete action recommendations per opportunity
- Classifies urgency based on days remaining (alta/media/baixa)
- Enforces terminology rules (forbidden ambiguous date phrases)
- Post-generation validation rejects output with ambiguous terms (`llm.py:211-228`)
- Structured output via Pydantic (`ResumoEstrategico` schema) ensures consistent format
- Fallback function (`gerar_resumo_fallback`, lines 233-377) provides heuristic-based analysis without LLM

The output schema includes: `resumo_executivo`, `recomendacoes` (with `acao_sugerida`, `urgencia`, `justificativa`), `alertas_urgencia`, `insight_setorial`. This goes beyond simple summarization into actionable intelligence.

However, the core AI is ultimately a GPT-4.1-nano call with a good prompt. The moat is in the prompt engineering and structured output, not proprietary models.

### What Competitors Likely Offer

The PNCP data is public. Competitors likely include:
- Manual PNCP portal search (free but tedious)
- Generic procurement platforms (Compras.gov.br, LicitaNet, Licitacao.net)
- Data aggregators (Portal de Licitacoes)

SmartLic's differentiation lies in the COMBINATION of:
1. Deep sector-specific filtering (15 sectors, 1000+ keyword rules)
2. AI strategic recommendations (not just summaries)
3. Multi-state parallel execution
4. Excel export with formatted reports

No single feature is a strong moat alone. The keyword curation (which must be maintained) and the sector-specific analysis create a defensible position, but the PNCP API is open to anyone.

### Score Justification: 7/10

- Genuinely sophisticated filtering engine (1000+ rules, context validation, red flags)
- AI goes beyond summarization into strategic recommendations with urgency classification
- 15 sector coverage is broad
- Prompt engineering quality is high (terminology enforcement, structured output)
- Core data source (PNCP) is public -- no exclusive data access
- No proprietary ML models -- GPT-4.1-nano is available to competitors
- Sector keyword curation is the primary moat but requires ongoing maintenance

---

## D15: Feedback Loop Speed

### CI/CD Pipeline

**Workflows found:** 13 GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `deploy.yml` | Push to main | Deploy to Railway (backend + frontend) |
| `tests.yml` | Push/PR to main | Backend tests (Python 3.11+3.12), Frontend tests, E2E |
| `backend-ci.yml` | Push/PR (backend changes) | Lint (ruff), mypy, security scan, tests with coverage |
| `e2e.yml` | Push/PR to main/develop | Playwright E2E tests |
| `pr-validation.yml` | PR | PR quality checks |
| `codeql.yml` | Push/PR | Security analysis |
| `lighthouse.yml` | (present) | Performance benchmarking |
| `load-test.yml` | (present) | Load testing |
| `sync-sectors.yml` | (present) | Sector data sync |
| `staging-deploy.yml` | (present) | Staging deployment |
| `dependabot-auto-merge.yml` | (present) | Dependency updates |
| `cleanup.yml` | (present) | Resource cleanup |

### Deploy Pipeline Quality

**Evidence:** `deploy.yml:64-101` -- Backend deployment:
1. Attempts Railway `redeploy` first (faster, uses GitHub source)
2. Falls back to `railway up` with 3 retries and 10s backoff
3. Waits 45s for deployment stabilization
4. Health check with 5 attempts, 15s intervals
5. Smoke tests: health endpoint, root endpoint, OpenAPI docs, integration test (POST /buscar)

**Frontend deployment:** Similar pattern with 60s wait and 5-attempt health check.

**Estimated deploy-to-production time:** ~3-5 minutes (push to main triggers automatic deployment).

### Test Suite Coverage

**Backend:**
- 96.69% coverage (82 tests) -- from CLAUDE.md
- Coverage threshold: 70% enforced in CI (`backend-ci.yml:52`)
- Matrix testing: Python 3.11 + 3.12
- Lint (ruff), type checking (mypy), security scan (safety)

**Frontend:**
- ~49.46% coverage (69 tests) -- below 60% threshold
- TypeScript type check enforced
- Quarantined test support (non-blocking)

**E2E:**
- Playwright tests covering search flow, theme, saved searches, empty state, error handling
- Runs against both Chromium and WebKit (Mobile Safari)
- 15-minute timeout

### Monitoring: Would They Know if Something Breaks?

**Within minutes:** Partially.
- Deploy health checks would catch crashes immediately
- Smoke tests catch 5xx errors on core endpoints
- BUT: Sentry is NOT configured in production -- runtime errors go undetected
- Mixpanel is NOT configured -- no user-facing anomaly detection
- No uptime monitoring (PagerDuty, UptimeRobot, etc.) found in the codebase
- No alerting pipeline for error rate spikes

**Evidence for monitoring gap:** Backend Sentry init is conditional (`main.py:125-128`):
```python
_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    sentry_sdk.init(dsn=_sentry_dsn, ...)
```
With `SENTRY_DSN` not set, runtime errors (like the checkout mode bug) would go completely unnoticed unless a user reports them.

### Score Justification: 7/10

- Excellent CI/CD pipeline (13 workflows, auto-deploy, health checks, smoke tests)
- Good test coverage on backend (96.69%), weak on frontend (49.46%)
- Fast deploy cycle (~3-5 minutes push-to-production)
- Multi-browser E2E testing
- BUT: No runtime error monitoring in production (Sentry not configured)
- No uptime monitoring or alerting
- No user behavior anomaly detection (Mixpanel not configured)
- The team would know about deploy failures but NOT about runtime bugs

---

## Key Findings

1. **P0 -- Checkout mode bug:** `smartlic_pro` creates a one-time payment instead of a subscription because it is not in the `is_subscription` tuple (`billing.py:63`). This means the entire billing model is broken for the current plan.

2. **P0 -- checkout.session.completed not handled:** Even if checkout succeeds, `_activate_plan()` is never called. Users pay but plans are not activated.

3. **P0 -- Zero production analytics:** Despite excellent code architecture (41 files with tracking, LGPD compliance, UTM capture), neither Mixpanel token nor Sentry DSN are configured in production. The team has no visibility into user behavior, errors, or conversion funnels.

4. **P1 -- No self-service cancellation:** Users can only cancel by deleting their entire account. The FAQ and terms promise easy cancellation but no subscription management UI exists.

5. **P1 -- invoice.payment_failed not handled:** Failed recurring payments have no dunning workflow.

6. **Positive -- Genuine differentiation:** The sector-specific filtering with 15 sectors, 1000+ rules, context validation, and red flag detection is sophisticated and represents real domain knowledge. The AI analysis goes beyond summarization into actionable recommendations.

7. **Positive -- Strong CI/CD:** 13 workflows with auto-deploy, health checks, smoke tests, and comprehensive test coverage on backend.

## Gaps

| # | Gap | Fix | Effort |
|---|-----|-----|--------|
| 1 | `smartlic_pro` not in subscription mode list (billing.py:63) | Add `smartlic_pro` to `is_subscription` tuple | 1 line, 10 min |
| 2 | `checkout.session.completed` webhook not handled | Add handler in webhooks/stripe.py calling `_activate_plan()` | 2-4 hours |
| 3 | Mixpanel token not set in production | Set `NEXT_PUBLIC_MIXPANEL_TOKEN` in Railway env vars | 5 min |
| 4 | Sentry DSN not configured in production | Set `SENTRY_DSN` and `NEXT_PUBLIC_SENTRY_DSN` in Railway env vars | 5 min |
| 5 | `invoice.payment_failed` not handled | Add webhook handler with dunning logic | 4-8 hours |
| 6 | No self-service subscription cancellation UI | Add cancel button to /conta page with Stripe API call | 4-8 hours |
| 7 | No revenue metrics (MRR, LTV, churn) | Build admin dashboard or Stripe integration | 1-2 sprints |
| 8 | No uptime monitoring | Add UptimeRobot or similar for /health endpoint | 30 min |
| 9 | Trial too limited for R$1,999/mo price point | Consider 14-day trial or 10 searches | Product decision |
| 10 | Frontend test coverage below threshold (49% < 60%) | Add tests for uncovered components | 1-2 days |
