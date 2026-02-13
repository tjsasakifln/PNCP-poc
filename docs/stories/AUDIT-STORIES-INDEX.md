# Audit Stories Index — Pre-GTM Backlog

**Created:** 2026-02-12
**Source:** 7 audit reports (Frentes 1-6 + Consolidated)
**Total Stories:** 17 (STORY-210 to STORY-226)
**Total Estimated Effort:** ~50 developer-days

---

## Priority Matrix

### Tier 0 — Deploy Today (Ops Only, 0 days)
*Verify env vars in production — no code changes.*

Included in **STORY-210** AC1-AC2.

### Tier 1 — Fix This Week / P0 Blockers (8 days)

| Story | Title | Effort | GTM Blocker? | Source Frentes |
|-------|-------|--------|-------------|----------------|
| **STORY-210** | Security Hardening — Critical & High Fixes | 3 days | **YES** | F1, F2, Consolidated |
| **STORY-211** | Error Tracking — Sentry | 2 days | **YES** | F4, F6, Consolidated |
| **STORY-212** | Automated Alerting & Uptime | 0.5 day | **YES** | F4, Consolidated |
| **STORY-214** | Rewrite Stale Auth Tests | 2 days | **YES** | F3, F5, Consolidated |
| **STORY-215** | Stripe/Billing Test Suite | 3 days | **YES** | F3, Consolidated |

### Tier 2 — Fix Before Launch / P1 (15 days)

| Story | Title | Effort | Source Frentes |
|-------|-------|--------|----------------|
| **STORY-213** | LGPD Compliance Sprint | 5-7 days | F2, F6, Consolidated |
| **STORY-216** | Decompose God Function | 3 days | F1, Consolidated |
| **STORY-217** | Unify Triple Redis | 2 days | F1, Consolidated |
| **STORY-218** | Frontend CI Fix + Test Quarantine | 2 days | F3, Consolidated |
| **STORY-219** | Analytics Activation + Funnel Tracking | 3 days | F6, Consolidated |
| **STORY-220** | JSON Structured Logging | 1 day | F4, Consolidated |
| **STORY-221** | Async Fixes (blocking code, Stripe, lifespan) | 2 days | F1, Consolidated |
| **STORY-222** | Shared API Contract (OpenAPI codegen) | 2 days | F1, Consolidated |

### Tier 3 — Fix Before Paid Scale / P2 (8 days)

| Story | Title | Effort | Source Frentes |
|-------|-------|--------|----------------|
| **STORY-223** | Historical Bug Regression Tests | 3 days | F5, Consolidated |
| **STORY-224** | Test Coverage Expansion (SSE, OAuth, Routes) | 5 days | F3, Consolidated |
| **STORY-225** | Transactional Email Infrastructure | 5-7 days | F6, Consolidated |

### Tier 4 — Post-GTM Polish / P3 (10 days)

| Story | Title | Effort | Source Frentes |
|-------|-------|--------|----------------|
| **STORY-226** | Post-GTM Polish (debt, audit logs, FAQ) | 10 days | F1, F4, F6, Consolidated |

---

## Audit Findings Coverage Map

This matrix shows how each audit finding maps to a story.

### Frente 1: Codebase Architecture (32 findings → 5 stories)

| Finding | Severity | Story |
|---------|----------|-------|
| CRIT-01: God function | CRITICAL | STORY-216 |
| CRIT-02: Triple Redis | CRITICAL | STORY-217 |
| CRIT-03: Contract mismatch | CRITICAL | STORY-222 |
| HIGH-01: Blocking time.sleep | HIGH | STORY-221 |
| HIGH-02: Token cache collision | HIGH | STORY-210 |
| HIGH-03: Dead code quota | HIGH | STORY-223 |
| HIGH-04: asyncio.run crash | HIGH | STORY-217, STORY-221 |
| HIGH-05: Stripe module-level key | HIGH | STORY-221 |
| HIGH-06: Filesystem Excel | HIGH | STORY-226 |
| HIGH-07: Deprecated on_event | HIGH | STORY-221 |
| HIGH-08: Dual router | HIGH | STORY-226 |
| MED-01 to MED-12 | MEDIUM | STORY-226 |
| LOW-01 to LOW-09 | LOW | STORY-226 |

### Frente 2: Security (19 findings → 2 stories)

| Finding | Severity | Story |
|---------|----------|-------|
| CRIT-01: JWT production | CRITICAL | STORY-210 |
| CRIT-02: Token cache collision | CRITICAL | STORY-210 |
| CRIT-03: Debug endpoint | CRITICAL | STORY-210 |
| CRIT-04: Download open redirect | CRITICAL | STORY-210 |
| HIGH-01: JWT audience disabled | HIGH | STORY-210 |
| HIGH-02: Encryption fallback | HIGH | STORY-210 |
| HIGH-03: No rate limit change-pw | HIGH | STORY-210 |
| HIGH-04: OpenAPI exposed | HIGH | STORY-210 |
| HIGH-05: Security headers | HIGH | STORY-210 |
| HIGH-06: Stripe price IDs | HIGH | STORY-210 |
| MED-01 to MED-05 | MEDIUM | STORY-210, STORY-213 |
| LOW-01 to LOW-04 | LOW | STORY-226 |
| SEC-08 LGPD | COMPLIANCE | STORY-213 |

### Frente 3: Test Coverage (14 gaps → 4 stories)

| Finding | Severity | Story |
|---------|----------|-------|
| C1: Stripe webhook fake tests | CRITICAL | STORY-215 |
| C2: SSE zero tests | HIGH | STORY-224 |
| C3: Google OAuth zero tests | HIGH | STORY-224 |
| C4: Lead prospecting zero tests | HIGH | STORY-224 |
| C5: Middleware zero tests | HIGH | STORY-224 |
| QA-01: Frontend CI `\|\| true` | HIGH | STORY-218 |
| QA-06: 91 pre-existing failures | HIGH | STORY-218 |
| QA-07: Lead prospecting | MEDIUM | STORY-224 |
| QA-08: Route coverage | MEDIUM | STORY-224 |
| H6: 6 routes no tests | MEDIUM | STORY-224 |
| GAP-2: Coverage thresholds | HIGH | STORY-218 |
| GAP-5: Download test skipped | MEDIUM | STORY-218 |

### Frente 4: Observability (13 risks → 3 stories)

| Finding | Severity | Story |
|---------|----------|-------|
| Risk #1: Error tracking ABSENT | CRITICAL (GTM) | STORY-211 |
| Risk #2: Alerting ABSENT | CRITICAL (GTM) | STORY-212 |
| Risk #3: No JSON logging | HIGH | STORY-220 |
| Risk #4: No global-error.tsx | HIGH | STORY-211 |
| Risk #5: No app metrics | HIGH | STORY-226 |
| Risk #6: Trivial FE health check | MEDIUM | STORY-212 |
| Risk #7: No audit log table | MEDIUM | STORY-226 |
| Risk #8: No trace propagation | MEDIUM | STORY-226 |
| Risk #9: No log forwarding | MEDIUM | STORY-220 |
| Risk #10-13 | LOW | STORY-226 |

### Frente 5: Historical Bugs (7 bugs → 2 stories)

| Finding | Status | Story |
|---------|--------|-------|
| Bug 1: Logging cascade | Fixed, no test | STORY-223 |
| Bug 2: JWT InvalidAlgorithm | Fixed, stale tests | STORY-214 |
| Bug 3: Paid users as free | Fixed, partial test | STORY-223 |
| Bug 4: Login button visible | Fixed, no test | STORY-223 |
| Bug 5: History not saved | Fixed, no test | STORY-223 |
| Bug 6: Inconsistent quota | Fixed, dead locks | STORY-223 |
| Bug 7: Header state /buscar | Architecture risk | STORY-223 |
| Pattern 1: Stale auth tests | CRITICAL | STORY-214 |

### Frente 6: Business Readiness (15 gaps → 4 stories)

| Finding | Severity | Story |
|---------|----------|-------|
| GAP-01: No cookie consent | CRITICAL | STORY-213 |
| GAP-02: Mixpanel not configured | CRITICAL | STORY-219 |
| GAP-03: Identity not linked | CRITICAL | STORY-219 |
| GAP-04: Zero revenue funnel | CRITICAL | STORY-219 |
| GAP-05: No data deletion | CRITICAL | STORY-213 |
| GAP-06: No error monitoring | HIGH | STORY-211 |
| GAP-07: No signup/login tracking | HIGH | STORY-219 |
| GAP-08: No email infrastructure | HIGH | STORY-225 |
| GAP-09: Privacy policy inaccurate | HIGH | STORY-213 |
| GAP-10: Checkout uses alert() | MEDIUM | STORY-226 |
| GAP-11: No FAQ | MEDIUM | STORY-226 |
| GAP-12: Error page no support link | MEDIUM | STORY-226 |
| GAP-13: No UTM tracking | MEDIUM | STORY-219 |
| GAP-14: No data portability | MEDIUM | STORY-213 |
| GAP-15: No contact email | MEDIUM | STORY-226 |

---

## Recommended Sprint Plan

### Sprint 1 (Week 1): Security + Observability Foundation — 8 days

| Story | Owner | Days |
|-------|-------|------|
| STORY-210 (Security Critical) | Dev 1 | 3 |
| STORY-211 (Sentry) | Dev 2 | 2 |
| STORY-212 (Alerting) | DevOps | 0.5 |
| STORY-214 (Auth Tests) | QA | 2 |

**Exit Criteria:** Zero CRITICAL security findings. Sentry capturing errors. UptimeRobot monitoring health.

### Sprint 2 (Weeks 2-3): Architecture + LGPD + Revenue Tests — 15 days

| Story | Owner | Days |
|-------|-------|------|
| STORY-213 (LGPD) | Dev 1 + PO | 5-7 |
| STORY-215 (Stripe Tests) | QA | 3 |
| STORY-216 (God Function) | Dev 2 | 3 |
| STORY-218 (Frontend CI) | Dev 3 | 2 |

**Exit Criteria:** LGPD-compliant. Billing tests real. CI enforces tests. God function decomposed.

### Sprint 3 (Weeks 4-5): Stability + Analytics + Coverage — 15 days

| Story | Owner | Days |
|-------|-------|------|
| STORY-217 (Redis) | Dev 1 | 2 |
| STORY-219 (Analytics) | Dev 2 | 3 |
| STORY-220 (JSON Logs) | Dev 1 | 1 |
| STORY-221 (Async Fixes) | Dev 1 | 2 |
| STORY-222 (API Contract) | Dev 2 | 2 |
| STORY-223 (Bug Regression) | QA | 3 |

**Exit Criteria:** Analytics flowing. JSON logs. No async bugs. API contract shared.

### Sprint 4+ (Post-GTM): Ongoing Polish

| Story | Owner | Days |
|-------|-------|------|
| STORY-224 (Coverage Expansion) | QA | 5 |
| STORY-225 (Email Infra) | Dev | 5-7 |
| STORY-226 (Polish) | Rotating | 10 |

---

*Index generated by @pm (Morgan) on 2026-02-12 from 7 audit reports totaling ~80 findings.*
