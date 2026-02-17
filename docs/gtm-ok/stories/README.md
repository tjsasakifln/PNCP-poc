# GTM-OK v2.0 Remediation Stories

**Date:** 2026-02-17
**Source:** GTM-OK v2.0 Assessment (GO CONDICIONAL at 5.92/10)
**Stories:** 12 (GTM-FIX-012 through GTM-FIX-023)
**Ranking Method:** WIN = (DeltaScore x Weight x Confidence) / Effort

---

## Execution Order (WIN-Ranked)

### Immediate -- P0 Critical (Must complete before any GTM activity)

| # | Story | WIN | Effort | Files | Impact |
|---|-------|-----|--------|-------|--------|
| 1 | **GTM-FIX-014** -- Remove fabricated AggregateRating from StructuredData.tsx | 30.00 | 5 min | `frontend/app/components/StructuredData.tsx` | D09+D16: eliminates Google penalty risk + CDC Art. 37 liability |
| 2 | **GTM-FIX-015** -- Add `smartlic_pro` to pipeline `allowed_plans` | 30.00 | 5 min | `backend/routes/pipeline.py` L61 | D09: unblocks promised feature for paying customers |
| 3 | **GTM-FIX-013** -- Deploy Sentry DSN + Mixpanel token to Railway | 11.40 | 30 min | Railway env vars (ops) | D06: 5->7, D13: 4->6 -- enables error tracking + analytics |
| 4 | **GTM-FIX-012** -- Fix PCP 404 + PNCP health canary 400 | 3.38 | 4 hrs | `backend/pncp_client.py`, `backend/clients/portal_compras_client.py` | D01+D04: restores production data flow (currently zero results) |

**P0 total effort: ~5 hours**

### Short-term -- P1 High (Required for comfortable GO CONDICIONAL)

| # | Story | WIN | Effort | Files | Impact |
|---|-------|-----|--------|-------|--------|
| 5 | **GTM-FIX-018** -- Fix copy claims (GPT-4o, daily analysis, SLA, ranking) | 2.85 | 1 hr | `planos/page.tsx`, `StatsSection.tsx`, `comparisons.ts`, `DifferentialsGrid.tsx` | D09: 6->7 |
| 6 | **GTM-FIX-017** -- Fix `to_legacy_format()` missing field mappings | 1.13 | 4 hrs | `backend/clients/base.py`, `backend/pncp_client.py` | D01+D04: multi-source data integrity |
| 7 | **GTM-FIX-016** -- Add checkout completion polling on obrigado page | 0.67 | 6 hrs | `backend/routes/billing.py`, `frontend/app/planos/obrigado/page.tsx` | D02: 6->7 -- webhook delay fallback |

**P1 total effort: ~11 hours**

### Medium-term -- P2 (Path toward GO)

| # | Story | WIN | Effort | Files | Impact |
|---|-------|-----|--------|-------|--------|
| 8 | **GTM-FIX-020** -- Add multi-worker uvicorn (gunicorn) | 5.70 | 30 min | `backend/Dockerfile` | D11: 6->7 -- scalability |
| 9 | **GTM-FIX-022** -- Add external uptime monitoring (UptimeRobot) | 5.40 | 30 min | External (ops) | D06: incident detection |
| 10 | **GTM-FIX-021** -- Create og-image.png + logo.png assets | 3.00 | 1 hr | `frontend/public/` | D16: 5->6 -- social sharing |
| 11 | **GTM-FIX-019** -- Reduce signup friction (8 fields -> 3) | 0.44 | 8 hrs | `frontend/app/signup/page.tsx` | D03+D08: conversion rate |
| 12 | **GTM-FIX-023** -- Improve frontend test coverage to 60% | 0.05 | 8 hrs | `frontend/__tests__/` | D15: CI stability |

**P2 total effort: ~18 hours**

---

## Dependencies

```
GTM-FIX-014 (fabricated reviews)     -- no deps, do first
GTM-FIX-015 (pipeline access)        -- no deps, do first
GTM-FIX-013 (observability tokens)   -- no deps, do first (ops)
    |
    v
GTM-FIX-012 (PCP 404 + PNCP canary) -- blocks everything else
    |
    +---> GTM-FIX-017 (to_legacy_format) -- soft dep on 012 for testing
    +---> GTM-FIX-018 (copy claims)      -- parallelizable with 017
    +---> GTM-FIX-016 (checkout polling)  -- independent

GTM-FIX-020 (uvicorn workers)        -- independent, anytime
GTM-FIX-022 (uptime monitoring)      -- after 013 (Sentry first)
GTM-FIX-021 (OG image)               -- independent, anytime
GTM-FIX-019 (signup friction)        -- independent, anytime
GTM-FIX-023 (test coverage)          -- independent, anytime
```

---

## Effort Summary

| Size | Stories | Total |
|------|---------|-------|
| **XS (< 30 min)** | GTM-FIX-014, GTM-FIX-015 | ~10 min |
| **S (30 min - 1 hr)** | GTM-FIX-013, GTM-FIX-018, GTM-FIX-020, GTM-FIX-021, GTM-FIX-022 | ~3.5 hrs |
| **M (4-8 hrs)** | GTM-FIX-012, GTM-FIX-016, GTM-FIX-017, GTM-FIX-019, GTM-FIX-023 | ~30 hrs |

**Grand total: ~34 hours** (1 dev ~5 days, 2 devs ~3 days)

---

## Projected Score Impact

| Phase | Stories | Weighted Score | Verdict |
|-------|---------|---------------|---------|
| Current | -- | 5.92 | GO CONDICIONAL |
| After P0 | FIX-012 to FIX-015 | ~6.3 | Strong GO CONDICIONAL |
| After P0+P1 | + FIX-016 to FIX-018 | ~6.6 | Near GO |
| After All | + FIX-019 to FIX-023 | ~6.85 | Near GO (need D08+D16 for full GO) |

---

## Relationship to Previous Stories (GTM-FIX-001 to GTM-FIX-011)

Stories GTM-FIX-001 through GTM-FIX-011 were defined in the v1.0 assessment (2026-02-16). Several have been completed:

| Old Story | Status | Notes |
|-----------|--------|-------|
| GTM-FIX-001 (Stripe checkout fix) | COMPLETED | D02 improved 3->6 |
| GTM-FIX-002 (Observability) | PARTIAL | Sentry code exists but tokens not deployed (-> FIX-013) |
| GTM-FIX-003 (Copy rewrite) | COMPLETED | D09 improved 4->6 (residual issues -> FIX-018) |
| GTM-FIX-004 (Truncation) | COMPLETED | Per-source truncation banners working |
| GTM-FIX-005 (Circuit breaker) | COMPLETED | Per-source circuit breakers implemented |
| GTM-FIX-006 (Cancel subscription) | COMPLETED | Cancel at period end via Stripe |
| GTM-FIX-007 (Payment dunning) | COMPLETED | invoice.payment_failed handler + email |
| GTM-FIX-008 (Mobile nav) | Not started | Deferred (mobile menu exists, needs polish) |
| GTM-FIX-009 (Email confirmation) | Not started | Deferred |
| GTM-FIX-010 (SWR cache) | COMPLETED | Two-level cache (InMemory + Supabase) |
| GTM-FIX-011 (PCP integration) | COMPLETED | Portal de Compras client active (now returning 404 -> FIX-012) |

The v2.0 stories (FIX-012 to FIX-023) address NEW issues discovered in the fresh assessment, including the production outage, fabricated review data, pipeline access bug, and remaining copy/SEO gaps.

---

## Quick Reference: Story -> Dimension Mapping

| Story | Primary Dimensions | Score Impact |
|-------|-------------------|--------------|
| GTM-FIX-012 | D01, D04 | Restore production |
| GTM-FIX-013 | D06, D13 | Enable observability |
| GTM-FIX-014 | D09, D16 | Legal/SEO risk |
| GTM-FIX-015 | D09 | Feature access |
| GTM-FIX-016 | D02 | Activation reliability |
| GTM-FIX-017 | D01, D04 | Data integrity |
| GTM-FIX-018 | D09 | Copy accuracy |
| GTM-FIX-019 | D03, D08 | Conversion |
| GTM-FIX-020 | D11 | Scalability |
| GTM-FIX-021 | D16 | Social sharing |
| GTM-FIX-022 | D06 | Incident detection |
| GTM-FIX-023 | D15 | CI stability |

---

**Last updated:** 2026-02-17 (GTM-OK v2.0 assessment)
**Full verdict:** See [GTM-OK-VERDICT.md](../GTM-OK-VERDICT.md)
**Evidence:** See [evidence/](../evidence/) directory (9 files)
