# GTM-OK Assessment: SmartLic v0.3

**Date:** 2026-02-16
**Assessor:** GTM-OK Workflow v1.0 (Claude Opus 4.6)
**Standard:** CTO-level production readiness
**Duration:** ~45 minutes (10 phases, 7 parallel agents)

---

## VERDICT: NO GO

### Verdict Rationale

SmartLic cannot charge R$1,999/month in its current state because **revenue cannot flow from checkout to plan activation**. The Stripe integration has three compounding P0 bugs: (1) `smartlic_pro` creates a one-time payment instead of a subscription (`billing.py:63`), (2) `checkout.session.completed` webhook is not handled (`webhooks/stripe.py:120-127`), and (3) `_activate_plan()` is dead code never called by any path (`billing.py:82`). A user who completes payment will be charged but remain on `free_trial` with 3 searches/month. This was independently identified by 4 of 7 assessment phases, confirming it is not an edge case but the primary payment pathway.

Beyond the revenue blocker, the marketing copy makes 19 NOT DELIVERED and 17 MISLEADING claims out of 95 total promises -- including "dezenas de fontes oficiais" (actually 3-4), "notificacoes em tempo real" (no notification system exists), "monitoramento continuo/diario" (system is 100% on-demand), and "R$ 2.3 bi em oportunidades mapeadas" (no measurement infrastructure). At R$1,999/month, these claims expose SmartLic to CDC Art. 37 (Brazilian Consumer Defense Code) complaints. A sophisticated B2B buyer discovering these gaps after payment would immediately churn and potentially file regulatory complaints.

The system has genuine strengths -- sector-specific filtering with 1000+ curated rules is a real competitive moat, the error handling architecture scores 7/10 with 14 of 20 failure scenarios handled excellently, security posture is strong (PII masking, LGPD compliance, JWT validation), and the CI/CD pipeline is comprehensive (13 workflows, auto-deploy, 96.69% backend coverage). The path to GO CONDICIONAL requires only fixing the 3 Stripe P0 bugs (~4-8 hours of work). The path to full GO requires 2-3 sprints.

---

## Executive Scorecard

| # | Dimension | Weight | Score | Verdict |
|---|-----------|--------|-------|---------|
| D01 | Core Value Delivery | [5] | 6/10 | CONDITIONAL |
| D02 | Revenue Infrastructure | [5] | **3/10** | **FAIL** |
| D03 | Autonomous UX | [5] | 6/10 | CONDITIONAL |
| D04 | Data Reliability | [5] | 5/10 | CONDITIONAL |
| D05 | Failure Transparency | [3] | 7/10 | PASS |
| D06 | Observability | [3] | 5/10 | NEEDS WORK |
| D07 | Value Before Payment | [3] | 7/10 | PASS |
| D08 | Onboarding Friction | [3] | 5/10 | NEEDS WORK |
| D09 | Copy-Code Alignment | [3] | 4/10 | FAIL |
| D10 | Security & LGPD | [3] | 7/10 | PASS |
| D11 | Infrastructure | [3] | 6/10 | CONDITIONAL |
| D12 | Pricing-Risk Alignment | [1] | 4/10 | FAIL |
| D13 | Analytics & Metrics | [1] | 3/10 | FAIL |
| D14 | Differentiation | [1] | 7/10 | PASS |
| D15 | Feedback Loop Speed | [1] | 7/10 | PASS |

**Weighted Overall Score: 5.42 / 10**

---

## Critical Findings

### Strengths (What's Working)

1. **Sector-specific filtering engine** (D14: 7/10) -- 15 sectors with 1000+ curated keyword rules, context-required keywords, red flag detection, exclusion-first fail-fast optimization. This represents genuine domain knowledge and a competitive moat. (`filter.py:682-799`, `sectors_data.yaml`)

2. **Error handling architecture** (D05: 7/10) -- 20 failure scenarios analyzed; 14 score 7+/10. Five degradation UI components (DegradationBanner, FailedUfsBanner, PartialResultsBanner, SourcesUnavailable, EmptyState). User-friendly Portuguese messages for every PNCP failure mode. (`error-messages.ts`, `SearchResults.tsx:209-345`)

3. **Security & LGPD compliance** (D10: 7/10) -- 606-line PII log sanitizer, JWT validation (ES256+JWKS+HS256), CORS allowlist, webhook signature validation, TruffleHog in CI, LGPD compliance (all Art. 18 rights: deletion, export, consent, DPO contact). (`log_sanitizer.py`, `auth.py`, `privacidade/page.tsx`)

4. **CI/CD pipeline** (D15: 7/10) -- 13 GitHub Actions workflows, auto-deploy with health checks and smoke tests, 96.69% backend coverage, multi-browser E2E testing. Push-to-production in ~3-5 minutes. (`deploy.yml`, `tests.yml`, `codeql.yml`)

5. **Quota enforcement** -- Atomic PostgreSQL RPC with FOR UPDATE row-level locking, 4-layer plan resolution (active subscription > grace period > profiles.plan_type > free_trial), 3-day billing grace period. (`quota.py:437-497`, migration 003)

6. **Observability instrumentation** (code: 9/10) -- 50+ Mixpanel events, Sentry integration in both error boundaries, correlation IDs (frontend + backend), audit trail with SHA-256 hashed PII, health endpoint checking all dependencies. Everything is wired up -- just needs env vars configured.

### Blockers (Must Fix for GO)

1. **[P0] Stripe checkout-to-activation chain is broken** (D02)
   - `smartlic_pro` not in `is_subscription` list (`billing.py:63`) -- creates one-time payment
   - `checkout.session.completed` not handled (`webhooks/stripe.py:120-127`)
   - `_activate_plan()` is dead code (`billing.py:82`) -- never called
   - **Impact:** Every paying customer charged but plan never activated
   - **Fix effort:** 4-8 hours

2. **[P0] Copy makes 36 undelivered/misleading claims** (D09)
   - "Dezenas de fontes" (3-4 actual), "R$ 2.3 bi" (no measurement), "notificacoes em tempo real" (doesn't exist), "monitoramento continuo" (on-demand only)
   - **Impact:** CDC Art. 37 regulatory risk, immediate churn on discovery
   - **Fix effort:** 1-2 days (copy rewrite) or 2-4 sprints (implement features)

3. **[P0] Silent data truncation at max_pages=500** (D01, D04)
   - User never notified when results are truncated (`pncp_client.py:694-703`)
   - Paying user could lose thousands of results silently
   - **Fix effort:** 4 hours

4. **[P0] Global circuit breaker cascade** (D01, D04)
   - Module-level singleton with threshold=20 (`pncp_client.py:170`) -- one user's aggressive search blocks all users for 120 seconds
   - **Fix effort:** 5 minutes (raise threshold) to 8 hours (per-user CB)

5. **[P1] Zero production observability** (D06, D13)
   - Sentry DSN not configured -- all production errors invisible
   - Mixpanel token not set -- zero analytics data (50+ events going nowhere)
   - **Fix effort:** 15 minutes (set 3 env vars in Railway)

6. **[P1] No self-service subscription cancellation** (D02, D12)
   - Users can only cancel by deleting their entire account
   - Copy promises "Cancele quando quiser" but no cancel button exists
   - **Fix effort:** 4-8 hours

### Risks (Known but Accepted for GO CONDICIONAL)

1. **PNCP API instability** -- The system has no local data lake or SWR cache. If PNCP is down, users get nothing. Circuit breaker and retry logic mitigate but don't eliminate this risk. (Addressed in Phase 10 architecture recommendation.)

2. **Single Uvicorn worker** -- Backend runs single async worker. Will bottleneck under concurrent heavy searches. Acceptable for launch (<50 concurrent users) but needs `--workers 2-4` before scaling.

3. **Trial is too short for price point** -- 3 searches in 7 days may not demonstrate enough value to justify R$1,999/month. Product decision required.

4. **Frontend test coverage below threshold** -- 49.46% vs 60% target. CI will fail. Not blocking launch but indicates test debt.

---

## Remediation Plan

### Sprint 1 (Week 1-2): Revenue & Observability Unlock

**Goal: Reach GO CONDICIONAL (D02 >= 5, weighted >= 5.5)**

Focus: Fix the revenue chain so money flows correctly, enable production observability, and fix the most dangerous copy claims.

| # | Story | Dimensions | Effort | Priority |
|---|-------|-----------|--------|----------|
| 1 | GTM-FIX-001: Fix Stripe checkout-to-activation chain | D02 | S (4-8h) | P0 |
| 2 | GTM-FIX-002: Enable production observability (Sentry + Mixpanel) | D06, D13 | XS (30min) | P0 |
| 3 | GTM-FIX-003: Rewrite copy to match delivered features | D09 | M (2-3d) | P0 |
| 4 | GTM-FIX-004: Fix PNCP silent truncation notification | D01, D04 | S (4h) | P0 |
| 5 | GTM-FIX-005: Raise circuit breaker threshold | D01 | XS (15min) | P0 |

### Sprint 2 (Week 3-4): UX & Lifecycle Completeness

**Goal: Approach GO (all [5]-weight >= 7)**

Focus: Complete the subscription lifecycle, fix UX blockers, implement PNCP resilience basics.

| # | Story | Dimensions | Effort | Priority |
|---|-------|-----------|--------|----------|
| 6 | GTM-FIX-006: Add subscription cancellation endpoint + UI | D02, D12 | S (8h) | P1 |
| 7 | GTM-FIX-007: Handle invoice.payment_failed with dunning | D02 | S (8h) | P1 |
| 8 | GTM-FIX-008: Fix mobile navigation + onboarding touch targets | D03, D08 | S (4h) | P1 |
| 9 | GTM-FIX-009: Fix email confirmation dead end | D03, D08 | S (4h) | P1 |
| 10 | GTM-FIX-010: Implement SWR cache for PNCP results | D01, D04 | M (3-5d) | P1 |

### Expected Score Improvement

| Dimension | Current | After Sprint 1 | After Sprint 2 |
|-----------|---------|-----------------|-----------------|
| D01 Core Value | 6 | 7 | 8 |
| D02 Revenue | 3 | 6 | 8 |
| D03 Autonomous UX | 6 | 6 | 7 |
| D04 Data Reliability | 5 | 6 | 7 |
| D05 Failure Transparency | 7 | 7 | 7 |
| D06 Observability | 5 | 7 | 7 |
| D07 Value Before Payment | 7 | 7 | 7 |
| D08 Onboarding Friction | 5 | 5 | 7 |
| D09 Copy-Code Alignment | 4 | 7 | 7 |
| D10 Security & LGPD | 7 | 7 | 7 |
| D11 Infrastructure | 6 | 6 | 7 |
| D12 Pricing-Risk Alignment | 4 | 5 | 6 |
| D13 Analytics & Metrics | 3 | 5 | 5 |
| D14 Differentiation | 7 | 7 | 7 |
| D15 Feedback Loop Speed | 7 | 7 | 7 |
| **Weighted Score** | **5.42** | **6.31** | **7.11** |
| **Verdict** | **NO GO** | **GO CONDICIONAL** | **GO** |

---

## Appendix: Evidence Files

| File | Dimensions | Phase |
|------|-----------|-------|
| `docs/gtm-ok/evidence/D01-pncp-pipeline.md` | D01, D04 | Phase 1 |
| `docs/gtm-ok/evidence/D02-stripe-revenue.md` | D02 | Phase 2 |
| `docs/gtm-ok/evidence/D03-autonomous-ux.md` | D03, D07, D08 | Phase 3 |
| `docs/gtm-ok/evidence/D05-D06-failure-observability.md` | D05, D06 | Phase 5 |
| `docs/gtm-ok/evidence/D09-copy-alignment.md` | D09 | Phase 4 |
| `docs/gtm-ok/evidence/D10-D11-security-infra.md` | D10, D11 | Phase 6 |
| `docs/gtm-ok/evidence/D12-D15-rapid-scan.md` | D12, D13, D14, D15 | Phase 7 |
| `docs/gtm-ok/evidence/consolidated-scores.md` | All | Phase 8 |

---

## Methodology Note

This assessment follows the GTM-OK Framework v1.0, evaluating 15 dimensions across 4 weight tiers ([5] Critical, [3] Important, [1] Nice-to-have). The standard applied is: "Would this pass scrutiny from a Silicon Valley CTO evaluating the system for investment or acquisition?" All findings are evidence-based with specific file:line code references. Seven parallel assessment agents were deployed for maximum speed and independence, followed by cross-validation to check for contradictions (none found).

**GO threshold:** All [5]-weight dimensions >= 7/10, weighted overall >= 7.0
**GO CONDICIONAL:** All [5]-weight dimensions >= 5/10, weighted overall >= 5.5
**NO GO:** Any [5]-weight dimension < 5/10

D02 (Revenue Infrastructure) scored 3/10, triggering NO GO.
