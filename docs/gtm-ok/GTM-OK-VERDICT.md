# GTM-OK v2.0 VERDICT

**Date:** 2026-02-17
**Assessment Version:** v2.0 (16 dimensions, WIN-based ranking)
**Assessor Team:** Multi-phase agent audit (@architect, @analyst, @ux-design-expert)
**Method:** 8 independent evidence documents, 460+ source files analyzed, cross-validated
**Previous Assessment:** v1.0 (2026-02-16) -- NO GO at 5.42/10

---

## VERDICT: GO CONDICIONAL (5.92/10)

### Conditional On:

1. **P0-CRIT: Fix the active production outage** (PCP 404 + PNCP canary 400) within 24 hours
2. **P0-OPS: Deploy Sentry + Mixpanel tokens** to Railway within 48 hours
3. **P0-LEGAL: Remove fabricated review data** from StructuredData.tsx immediately

If any P0 condition is not met within its timeframe, verdict reverts to **NO GO**.

---

## Executive Scorecard

| # | Dimension | Weight | Score | Status |
|---|-----------|--------|-------|--------|
| D01 | Core Value Delivery | [5] | 6/10 | CONDITIONAL |
| D02 | Revenue Infrastructure | [5] | 6/10 | CONDITIONAL |
| D03 | Autonomous UX | [5] | 6/10 | CONDITIONAL |
| D04 | Data Reliability | [5] | 5/10 | AT FLOOR |
| D05 | Failure Transparency | [3] | 7/10 | PASS |
| D06 | Observability | [3] | 5/10 | WEAK |
| D07 | Value Before Payment | [3] | 7/10 | PASS |
| D08 | Onboarding Friction | [3] | 5/10 | WEAK |
| D09 | Copy-Code Alignment | [3] | 6/10 | CONDITIONAL |
| D10 | Security & LGPD | [3] | 7/10 | PASS |
| D11 | Infrastructure | [3] | 6/10 | CONDITIONAL |
| D12 | Pricing-Risk Alignment | [1] | 7/10 | PASS |
| D13 | Analytics & Metrics | [1] | 4/10 | FAIL |
| D14 | Differentiation | [1] | 7/10 | PASS |
| D15 | Feedback Loop Speed | [1] | 7/10 | PASS |
| D16 | SEO & Discovery | [3] | 5/10 | WEAK |

**Weighted Score:** 284 / 48 = **5.92 / 10**

### Threshold Results

| Threshold | Criteria | Result |
|-----------|----------|--------|
| **GO** | All [5]-weight >= 7, weighted >= 7.0 | FAIL (D01=6, D02=6, D03=6, D04=5) |
| **GO CONDICIONAL** | All [5]-weight >= 5, weighted >= 5.5 | **PASS** (min [5]-weight = 5, weighted = 5.92) |
| **NO GO** | Any [5]-weight < 5 | NOT TRIGGERED |

### Delta from Previous Assessment (2026-02-16 v1.0)

| Metric | v1.0 | v2.0 | Change |
|--------|------|------|--------|
| Overall Score | 5.42 | 5.92 | +0.50 |
| Verdict | NO GO | GO CONDICIONAL | UPGRADED |
| D02 (Revenue) | 3/10 | 6/10 | +3 (Stripe lifecycle implemented) |
| D09 (Copy) | 4/10 | 6/10 | +2 (copy remediation via GTM-FIX-003) |
| D12 (Pricing) | 4/10 | 7/10 | +3 (single-plan clarity via GTM-002) |
| D16 (SEO) | N/A | 5/10 | New dimension in v2.0 |

---

## CRITICAL PRODUCTION INCIDENT

**Status:** ACTIVE as of 2026-02-17
**Impact:** ZERO RESULTS for all users across all sectors
**Detection method:** Manual user discovery (no automated alerting)

### Root Causes

**1. PCP API returning 404:**
```
"A rota GET /publico/obterprocessosabertos?...&uf=AC&publicKey=... nao existe."
```
The Portal de Compras Publicas API endpoint no longer exists at the expected URL. This breaks the secondary data source entirely.

**2. PNCP health canary returning 400:**
```
"must be greater than or equal to 10" (tamanhoPagina=1)
```
The health canary probe sends `tamanhoPagina=1` to PNCP, but the API now requires a minimum page size of 10. This causes the health check to fail, potentially triggering the circuit breaker and blocking all PNCP queries.

### Why This Was Not Detected

- Sentry is NOT deployed (D06: 5/10)
- Mixpanel is NOT deployed (D13: 4/10)
- No synthetic canary search
- No uptime monitoring polling `/health`
- **The user discovered it manually** -- strongest evidence for the D06 score

---

## Critical Findings

### Strengths (What's Working)

1. **Sector-specific filtering** (D14: 7/10) -- 15 sectors with 2,486 keyword/exclusion rules. Genuine competitive moat. (`filter.py`, `sectors_data.yaml`)

2. **Error handling architecture** (D05: 7/10) -- 8+ dedicated UI components for every failure mode. Non-technical Portuguese messaging. Recovery actions on every screen. Cooldown protection. (`DegradationBanner`, `CacheBanner`, `SourcesUnavailable`, `TruncationWarningBanner`, `EmptyState`, `error.tsx`)

3. **Security & LGPD** (D10: 7/10) -- JWT with local verification + JWKS, comprehensive RLS across all tables, full LGPD stack (consent, PII masking, audit trail, privacy page, DPO contact), no secrets in source code. (`auth.py`, `log_sanitizer.py`, `privacidade/page.tsx`)

4. **CI/CD pipeline** (D15: 7/10) -- 12 GitHub Actions workflows, auto-deploy with health checks + smoke tests, 96.69% backend coverage, CodeQL + TruffleHog security scanning. (`deploy.yml`, `tests.yml`, `codeql.yml`)

5. **Revenue infrastructure** (D02: 6/10, up from 3) -- Complete Stripe lifecycle now implemented: checkout, activation, renewal, cancellation at period end, dunning (payment_failed with email), billing portal. 54 tests. (`webhooks/stripe.py`, `routes/billing.py`, `routes/subscriptions.py`)

6. **Pricing clarity** (D12: 7/10) -- Single SmartLic Pro plan with 3 billing periods eliminates tier confusion. Honest ROI framing with disclaimers. 1-click cancel path exists. (`planos/page.tsx`, `quota.py`)

7. **Multi-source resilience** (D01: 6/10) -- PNCP client with 5-level retry, circuit breaker, health canary, degraded mode. 4-level fallback cascade (primary -> partial -> ComprasGov -> cache). SWR cache with Supabase persistence. (`pncp_client.py`, `consolidation.py`, `search_cache.py`)

### Blockers

1. **[ACTIVE] Production outage** -- PCP 404 + PNCP canary 400 = zero results for all users NOW

2. **[CRITICAL] Fabricated review data** -- `StructuredData.tsx` claims 127 reviews with 4.8 rating. No review system exists. Google penalty risk + CDC Art. 37 liability.

3. **[HIGH] Zero observability in production** -- Sentry and Mixpanel tokens not deployed. 50+ analytics events and all error tracking are dead code.

4. **[HIGH] Pipeline access blocked for paying plan** -- `routes/pipeline.py` only allows legacy plans `maquina`/`sala_guerra`, not `smartlic_pro`

5. **[HIGH] Copy still has misleading claims** -- "GPT-4o" (actually GPT-4.1-nano), "Diario analises programadas" (no scheduler), "resposta garantida no mesmo dia" (no SLA), "Ranqueamento por relevancia" (no ranking algorithm)

6. **[MEDIUM] Multi-source data loss** -- `to_legacy_format()` drops `dataEncerramentoProposta` for ALL records in multi-source mode, breaking deadline filters and urgency badges

7. **[MEDIUM] Webhook-dependent activation** -- No polling fallback if Stripe webhook is delayed. User sees "Assinatura confirmada!" based on URL parameter regardless of backend state.

---

## WIN-RANKED REMEDIATION PLAN

**WIN Formula:** WIN = (DeltaScore x Weight x Confidence) / Effort

| Rank | Story | WIN | Effort | Priority | Impact |
|------|-------|-----|--------|----------|--------|
| 1 | GTM-FIX-014: Remove fabricated reviews | **30.00** | 5 min | P0 | D09+D16: legal/SEO risk elimination |
| 2 | GTM-FIX-015: Fix pipeline access for smartlic_pro | **30.00** | 5 min | P0 | D09: unblock promised feature |
| 3 | GTM-FIX-013: Deploy Sentry + Mixpanel tokens | **11.40** | 30 min | P0 | D06+D13: incident detection |
| 4 | GTM-FIX-020: Multi-worker uvicorn | **5.70** | 30 min | P2 | D11: scalability |
| 5 | GTM-FIX-022: Uptime monitoring | **5.40** | 30 min | P2 | D06: external health polling |
| 6 | GTM-FIX-012: Fix PCP 404 + PNCP canary 400 | **3.38** | 4 hrs | P0 | D01+D04: restore production |
| 7 | GTM-FIX-021: OG image + logo assets | **3.00** | 1 hr | P2 | D16: social sharing |
| 8 | GTM-FIX-018: Fix copy claims | **2.85** | 1 hr | P1 | D09: accuracy |
| 9 | GTM-FIX-017: Fix to_legacy_format() | **1.13** | 4 hrs | P1 | D01+D04: multi-source data integrity |
| 10 | GTM-FIX-016: Checkout completion polling | **0.67** | 6 hrs | P1 | D02: activation reliability |
| 11 | GTM-FIX-019: Reduce signup friction | **0.44** | 8 hrs | P2 | D03+D08: conversion |
| 12 | GTM-FIX-023: Frontend test coverage | **0.05** | 8 hrs | P2 | D15: CI stability |

---

## Remediation Story Details

### P0: CRITICAL (Must fix before any GTM activity)

#### GTM-FIX-012: Fix PCP 404 + PNCP Health Canary (WIN: 3.38)

**Problem:** PCP API returns 404 on `/publico/obterprocessosabertos`. PNCP canary sends `tamanhoPagina=1` but API now requires >= 10. Both sources broken, causing zero results.

**Tasks:**
1. Update PNCP health canary to use `tamanhoPagina=10` instead of 1
2. Investigate PCP: check if endpoint URL changed, API key expired, or service discontinued
3. Update `portal_compras_client.py` with correct endpoint or disable PCP if API is gone
4. Add integration smoke test validating both sources return non-error responses
5. Deploy and verify

**Files:** `backend/pncp_client.py` (canary params), `backend/clients/portal_compras_client.py` (endpoint URL)
**Effort:** 4 hours | **Impact:** D01: 6->7, D04: 5->6

#### GTM-FIX-013: Deploy Observability Tokens (WIN: 11.40)

**Problem:** `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN`, `NEXT_PUBLIC_MIXPANEL_TOKEN` not set in Railway.

**Tasks:**
1. Create Sentry project (or verify existing) and get DSN
2. Set `SENTRY_DSN` in Railway backend service
3. Set `NEXT_PUBLIC_SENTRY_DSN` in Railway frontend service
4. Set `NEXT_PUBLIC_MIXPANEL_TOKEN` in Railway frontend service
5. Trigger redeploy, verify events flow

**Effort:** 30 min | **Impact:** D06: 5->7, D13: 4->6

#### GTM-FIX-014: Remove Fabricated Review Data (WIN: 30.00)

**Problem:** `StructuredData.tsx` emits `aggregateRating: { ratingValue: "4.8", reviewCount: "127" }`. No review system exists. Google penalty risk + legal liability.

**Tasks:**
1. Remove the `aggregateRating` object from `frontend/app/components/StructuredData.tsx`
2. Deploy

**Files:** `frontend/app/components/StructuredData.tsx` lines 77-82
**Effort:** 5 min | **Impact:** D09: +0.5, D16: +0.5

#### GTM-FIX-015: Fix Pipeline Access for SmartLic Pro (WIN: 30.00)

**Problem:** `routes/pipeline.py` line 61: `allowed_plans = {"maquina", "sala_guerra"}` blocks `smartlic_pro`.

**Tasks:**
1. Add `"smartlic_pro"` to `allowed_plans` set
2. Add test
3. Deploy

**Files:** `backend/routes/pipeline.py` line 61
**Effort:** 5 min | **Impact:** Prevents paying customer 403 errors

### P1: HIGH (Required for comfortable GO CONDICIONAL)

#### GTM-FIX-016: Add Checkout Completion Polling (WIN: 0.67)

**Problem:** Plan activation depends entirely on webhook delivery with no fallback.

**Tasks:**
1. Create `GET /v1/subscription/status` that checks local DB + Stripe API
2. Frontend obrigado page polls every 5s for up to 2 min
3. Add timeout state with support contact info

**Effort:** 6 hours | **Impact:** D02: 6->7

#### GTM-FIX-017: Fix to_legacy_format() Data Loss (WIN: 1.13)

**Problem:** `to_legacy_format()` drops `dataEncerramentoProposta`, `esferaId`, `numeroEdital`, `anoCompra`. Multi-source records lose deadline data.

**Tasks:**
1. Add missing field mappings to `to_legacy_format()` in `base.py`
2. Fix `PNCPLegacyAdapter.fetch()` to set `data_encerramento` and `data_publicacao`
3. Add integration test

**Effort:** 4 hours | **Impact:** D01: 6->7, D04: 5->6

#### GTM-FIX-018: Fix Copy Claims (WIN: 2.85)

**Problem:** "GPT-4o" (uses 4.1-nano), "Diario analises programadas" (no scheduler), "resposta garantida no mesmo dia" (no SLA), "Ranqueamento por relevancia" (no algorithm).

**Tasks:**
1. Change "GPT-4o" to "IA avancada" on pricing page
2. Change "Diario -- analises programadas" to "Sob demanda"
3. Standardize support SLA to "24 horas uteis"
4. Remove or soften "Ranqueamento por relevancia"

**Effort:** 1 hour | **Impact:** D09: 6->7

### P2: MEDIUM (Path toward GO)

#### GTM-FIX-019: Reduce Signup Friction (WIN: 0.44)

**Problem:** 8 mandatory fields + consent scroll + mandatory WhatsApp consent.

**Tasks:** Reduce to 3 fields (email, password, name). Move extras to onboarding. Make WhatsApp optional.
**Effort:** 8 hours | **Impact:** D03: 6->7, D08: 5->6

#### GTM-FIX-020: Multi-Worker Uvicorn (WIN: 5.70)

**Problem:** Single uvicorn worker blocks on CPU-bound operations.

**Tasks:** Change CMD to `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`.
**Effort:** 30 min | **Impact:** D11: 6->7

#### GTM-FIX-021: Create OG Image + Logo Assets (WIN: 3.00)

**Problem:** `og-image.png` and `logo.png` referenced but missing from `frontend/public/`.

**Tasks:** Create and deploy both image assets.
**Effort:** 1 hour | **Impact:** D16: 5->6

#### GTM-FIX-022: Add Uptime Monitoring (WIN: 5.40)

**Problem:** No external service monitors `/health`. Outages go undetected.

**Tasks:** Set up UptimeRobot for `/health` and `/api/health`. Configure alerts.
**Effort:** 30 min | **Impact:** D06: +1

#### GTM-FIX-023: Improve Frontend Test Coverage (WIN: 0.05)

**Problem:** Frontend coverage at 49.46%, below 60% threshold.

**Tasks:** Add tests for LoadingProgress, RegionSelector, SavedSearchesDropdown, AnalyticsProvider.
**Effort:** 8 hours | **Impact:** D15: 7->7.5

---

## Path to GO

To reach GO, ALL [5]-weight dimensions must reach >= 7 and weighted average >= 7.0.

**Required improvements:**

| Dimension | Current | Target | Key Fixes |
|-----------|---------|--------|-----------|
| D01 | 6 | 7 | FIX-012 (PCP/PNCP), FIX-017 (to_legacy_format) |
| D02 | 6 | 7 | FIX-016 (checkout polling), atomic idempotency, Customer reuse |
| D03 | 6 | 7 | FIX-019 (signup friction), add preview/demo mode |
| D04 | 5 | 7 | FIX-017, validate dedup, per-record freshness indicator |

**Estimated effort for GO:** 3-4 sprints (6-8 weeks)

**Projected score after all P0+P1+P2 fixes:**

With D01=7, D02=7, D03=7, D04=7, D06=7, D09=7, D11=7, D13=6, D16=6:
Weighted = (7+7+7+7)*5 + (7+7+7+6+7+7+7+6)*3 + (7+6+7+7)*1 = 140 + 162 + 27 = 329
329 / 48 = **6.85** (still below 7.0 -- would need D08 and D16 to also reach 7)

---

## Evidence Document Index

| File | Dimensions | Date |
|------|-----------|------|
| `evidence/D01-D04-multi-source-pipeline.md` | D01, D04 | 2026-02-17 |
| `evidence/D02-stripe-revenue.md` | D02 | 2026-02-17 |
| `evidence/D03-autonomous-ux.md` | D03, D07, D08 | 2026-02-17 |
| `evidence/D05-D06-failure-observability.md` | D05, D06 | 2026-02-17 |
| `evidence/D09-copy-alignment.md` | D09 | 2026-02-17 |
| `evidence/D10-D11-security-infra.md` | D10, D11 | 2026-02-17 |
| `evidence/D12-D15-rapid-scan.md` | D12, D13, D14, D15 | 2026-02-17 |
| `evidence/D16-seo-discovery.md` | D16 | 2026-02-17 |
| `evidence/consolidated-scores.md` | All (cross-validation) | 2026-02-17 |

---

## Methodology

GTM-OK v2.0 evaluates 16 dimensions across 3 weight tiers:
- **[5] Critical (D01-D04):** Core value, revenue, UX, data reliability
- **[3] Important (D05-D11, D16):** Failure handling, observability, onboarding, copy, security, infra, SEO
- **[1] Nice-to-have (D12-D15):** Pricing, analytics, differentiation, feedback loops

**Total weight:** 48 (4x5 + 8x3 + 4x1)

**WIN ranking** (Weighted Impact Number) prioritizes fixes by: DeltaScore x Weight x Confidence / Effort. This ensures the highest-value, lowest-effort fixes are executed first.

**GO threshold:** All [5]-weight >= 7/10, weighted overall >= 7.0
**GO CONDICIONAL:** All [5]-weight >= 5/10, weighted overall >= 5.5
**NO GO:** Any [5]-weight < 5/10

---

*GTM-OK v2.0 assessment completed 2026-02-17. Previous verdict (v1.0, 2026-02-16): NO GO at 5.42/10. Current verdict: GO CONDICIONAL at 5.92/10. Primary improvement: D02 Revenue Infrastructure 3->6 (Stripe lifecycle implemented). Critical condition: production outage must be resolved within 24 hours.*
