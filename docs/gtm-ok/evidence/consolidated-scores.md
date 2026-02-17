# Consolidated GTM-OK v2.0 Scores

**Date:** 2026-02-17
**Phase:** 9 of 10 (Cross-Validation & Consolidated Scoring)
**Assessor:** @architect (GTM-OK v2.0 Workflow)
**Dimensions:** 16 (D01-D16)

---

## Scoring Table

| # | Dimension | Weight | Score | Threshold Check | Source |
|---|-----------|--------|-------|-----------------|--------|
| D01 | Core Value Delivery | [5] | 6/10 | [5]-weight: BELOW 7 | D01-D04-multi-source-pipeline.md |
| D02 | Revenue Infrastructure | [5] | 6/10 | [5]-weight: BELOW 7 | D02-stripe-revenue.md |
| D03 | Autonomous UX | [5] | 6/10 | [5]-weight: BELOW 7 | D03-autonomous-ux.md |
| D04 | Data Reliability | [5] | 5/10 | [5]-weight: BELOW 7 | D01-D04-multi-source-pipeline.md |
| D05 | Failure Transparency | [3] | 7/10 | - | D05-D06-failure-observability.md |
| D06 | Observability | [3] | 5/10 | - | D05-D06-failure-observability.md |
| D07 | Value Before Payment | [3] | 7/10 | - | D03-autonomous-ux.md |
| D08 | Onboarding Friction | [3] | 5/10 | - | D03-autonomous-ux.md |
| D09 | Copy-Code Alignment | [3] | 6/10 | - | D09-copy-alignment.md |
| D10 | Security & LGPD | [3] | 7/10 | - | D10-D11-security-infra.md |
| D11 | Infrastructure | [3] | 6/10 | - | D10-D11-security-infra.md |
| D12 | Pricing-Risk Alignment | [1] | 7/10 | - | D12-D15-rapid-scan.md |
| D13 | Analytics & Metrics | [1] | 4/10 | - | D12-D15-rapid-scan.md |
| D14 | Differentiation | [1] | 7/10 | - | D12-D15-rapid-scan.md |
| D15 | Feedback Loop Speed | [1] | 7/10 | - | D12-D15-rapid-scan.md |
| D16 | SEO & Discovery | [3] | 5/10 | - | D16-seo-discovery.md |

---

## Weighted Overall Score Calculation

**Formula:** Sum(score_i * weight_i) / Sum(weight_i) * 10

Total weight: (4 * 5) + (8 * 3) + (4 * 1) = 20 + 24 + 4 = 48

| Dimension | Weight | Score | Weighted |
|-----------|--------|-------|----------|
| D01 | 5 | 6 | 30 |
| D02 | 5 | 6 | 30 |
| D03 | 5 | 6 | 30 |
| D04 | 5 | 5 | 25 |
| D05 | 3 | 7 | 21 |
| D06 | 3 | 5 | 15 |
| D07 | 3 | 7 | 21 |
| D08 | 3 | 5 | 15 |
| D09 | 3 | 6 | 18 |
| D10 | 3 | 7 | 21 |
| D11 | 3 | 6 | 18 |
| D12 | 1 | 7 | 7 |
| D13 | 1 | 4 | 4 |
| D14 | 1 | 7 | 7 |
| D15 | 1 | 7 | 7 |
| D16 | 3 | 5 | 15 |
| **TOTAL** | **48** | | **284** |

**Weighted Overall Score: 284 / 48 = 5.92 / 10**

---

## Threshold Analysis

### GO Threshold: All [5]-weight >= 7, weighted overall >= 7.0

- D01 (6/10): **BELOW 7 -- FAIL**
- D02 (6/10): **BELOW 7 -- FAIL**
- D03 (6/10): **BELOW 7 -- FAIL**
- D04 (5/10): **BELOW 7 -- FAIL**
- Weighted overall (5.92): **BELOW 7.0 -- FAIL**
- **Result: NOT GO**

### GO CONDICIONAL Threshold: All [5]-weight >= 5, weighted overall >= 5.5

- D01 (6/10): PASS (>= 5)
- D02 (6/10): PASS (>= 5)
- D03 (6/10): PASS (>= 5)
- D04 (5/10): PASS (>= 5)
- Weighted overall (5.92): **PASS (>= 5.5)**
- **Result: GO CONDICIONAL**

### NO GO Threshold: Any [5]-weight < 5

- All [5]-weight dimensions >= 5: D01=6, D02=6, D03=6, D04=5
- **Result: NOT NO GO**

---

## Verdict: GO CONDICIONAL

**The system passes GO CONDICIONAL with a 5.92/10 weighted score.** All [5]-weight dimensions meet the >= 5 floor, and the weighted average exceeds 5.5.

**However, a CRITICAL production incident threatens this verdict:**

```
PCP API returning 404: "A rota GET /publico/obterprocessosabertos?...&uf=AC&publicKey=... nao existe."
PNCP health canary returning 400: "must be greater than or equal to 10" (tamanhoPagina=1)
```

Both primary data sources are currently returning errors in production, causing ZERO RESULTS for users across all sectors. This is an active incident that, if unresolved, would drop D01 from 6 to 3-4 (PNCP-only path broken, PCP fully broken) and trigger NO GO.

**Conditional on:** Fixing the PCP 404 and PNCP canary 400 within 24 hours.

---

## Score Delta from Previous Assessment (2026-02-16)

| Dimension | Old Score | New Score | Delta | Reason |
|-----------|-----------|-----------|-------|--------|
| D02 | 3 | 6 | +3 | Stripe lifecycle implemented (checkout, payment_failed, dunning) |
| D09 | 4 | 6 | +2 | Copy rewrite (GTM-FIX-003 remediation) |
| D12 | 4 | 7 | +3 | Clean single-plan model, honest ROI framing |
| D16 | (new) | 5 | -- | New dimension added in v2.0 |
| Overall | 5.42 | 5.92 | +0.50 | D02 improvement is the primary driver |

---

## Cross-Validation Checks

### 1. D01 (Pipeline) x D05 (Failure Transparency)

**ALIGNED.** Phase 1 identified `to_legacy_format()` data loss in multi-source mode. Phase 5 confirmed the degradation UI handles detected failures well but cannot display per-bid deadline data that the backend drops. Both agree: the UI layer is solid, the data layer has gaps.

### 2. D02 (Revenue) x D09 (Copy)

**ALIGNED.** Phase 2 found the checkout-to-activation depends entirely on webhook delivery with no polling fallback. Phase 4 found the "obrigado" page trusts the `?plan=` URL parameter regardless of backend state. Both identify the same gap from different angles.

### 3. D06 (Observability) x D13 (Analytics)

**ALIGNED AND COMPOUNDING.** Phase 5 found Sentry DSN deployment uncertain. Phase 7 independently confirmed Mixpanel token NOT deployed. The observability + analytics gap is corroborated by the production incident: PCP 404 and PNCP 400 went undetected until manual user discovery.

### 4. D10 (Security) x D11 (Infrastructure)

**ALIGNED.** Phase 6 scored both independently. D10 (security) at 7 reflects strong auth, RLS, LGPD compliance. D11 (infra) at 6 reflects single-worker uvicorn and no auto-scaling. These are consistent -- the security code is excellent, the deployment configuration is minimal.

### 5. Production Incident Cross-Check

The PCP 404 error validates:
- D06 at 5/10 (observability gap -- incident went undetected)
- D01 at 6/10 (core pipeline resilience works for PNCP-only path, but PCP integration is fragile)
- D04 at 5/10 (data reliability suffers when a primary source returns 404 silently)
- D11 at 6/10 (no automated recovery or alerting for source failures)

---

## Strengths Worth Preserving

1. **Error handling architecture** (D05: 7/10) -- 8+ dedicated UI components for every failure mode, non-technical Portuguese messaging, recovery actions on every screen.

2. **Security posture** (D10: 7/10) -- JWT with local verification + JWKS, comprehensive RLS, LGPD stack (consent, masking, audit, privacy page), no secrets in source code.

3. **Sector-specific intelligence** (D14: 7/10) -- 15 sectors, 2,486 keyword/exclusion rules, context validation. Genuine competitive moat.

4. **CI/CD pipeline** (D15: 7/10) -- 12 GitHub Actions workflows, auto-deploy with health checks, 96.69% backend coverage, CodeQL + TruffleHog.

5. **Revenue infrastructure** (D02: 6/10, up from 3) -- Complete Stripe lifecycle now implemented. Checkout, activation, renewal, cancellation, dunning flow, payment failure emails. 54 tests.

6. **Pricing clarity** (D12: 7/10) -- Single-plan model eliminates confusion. Honest ROI framing with disclaimers.

7. **Differentiation** (D14: 7/10) -- Multi-source aggregation, AI strategic analysis, 15-sector keyword intelligence.

---

## Top Remediation Priorities (WIN-Ranked)

See `GTM-OK-VERDICT.md` for the full WIN-ranked remediation plan with effort estimates and score impacts.

### Immediate (P0 -- blocks GTM launch)

1. **Fix PCP 404 + PNCP canary 400** -- Production is returning zero results NOW
2. **Deploy Sentry DSN + Mixpanel token** -- Zero observability and analytics in production
3. **Remove fabricated AggregateRating** -- Google penalty risk + legal liability

### Short-term (P1 -- required for comfortable GO CONDICIONAL)

4. **Fix pipeline access for smartlic_pro** -- Paying customers blocked from promised feature
5. **Add checkout completion polling** -- Webhook-dependent activation has no fallback
6. **Fix `to_legacy_format()` data loss** -- Multi-source mode drops deadline data

### Medium-term (P2 -- path to GO)

7. **Reduce signup friction** -- 8 fields + forced consent is conversion-killing
8. **Add multi-worker uvicorn** -- Single worker cannot scale
9. **Improve frontend test coverage** -- 49.46% below 60% threshold

---

*Cross-validation completed 2026-02-17. All 8 evidence documents reviewed (D01-D04, D02, D03+D07+D08, D05-D06, D09, D10-D11, D12-D15, D16). Score consistency verified across independent phase assessments. Production incident (PCP 404 + PNCP 400) incorporated as critical context.*
