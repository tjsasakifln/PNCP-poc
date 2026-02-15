# PRE-GTM CONSOLIDATED AUDIT REPORT

**Project:** SmartLic (formerly BidIQ Uniformes)
**Date:** 2026-02-12
**Lead Auditor:** @architect (Claude Opus 4.6)
**Methodology:** Line-by-line codebase read, pattern-based analysis, security review, test coverage audit, historical bug deep dive
**Scope:** Full-stack analysis of `main` branch (commit `f1d7fdb`)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [GTM Readiness Verdict](#gtm-readiness-verdict)
3. [Consolidated Risk Heatmap](#consolidated-risk-heatmap)
4. [Top 10 Blockers -- Prioritized Action Plan](#top-10-blockers)
5. [Frente 1: Codebase Architecture](#frente-1-codebase-architecture)
6. [Frente 2: Security](#frente-2-security)
7. [Frente 3: Test Coverage](#frente-3-test-coverage)
8. [Frente 5: Historical Bugs](#frente-5-historical-bugs)
9. [Cross-Frente Patterns](#cross-frente-patterns)
10. [LGPD Compliance Gap Analysis](#lgpd-compliance)
11. [Full Proposed Story Backlog](#proposed-stories)
12. [Effort Summary](#effort-summary)

---

## Executive Summary

SmartLic is a functional product with strong domain logic (filtering, synonym matching, LLM arbiter) and solid security foundations (PII sanitization, JWT validation, input validation). The codebase demonstrates rapid, competent feature development. However, four audits reveal **systemic debt across architecture, security, testing, and historical bug regression coverage** that collectively **block a safe GTM launch**.

### By the Numbers

| Dimension | Findings | GTM Blockers |
|-----------|----------|--------------|
| **Architecture** (Frente 1) | 32 findings (3 CRIT, 8 HIGH, 12 MED, 9 LOW) | 4 critical stories |
| **Security** (Frente 2) | 19 findings (4 CRIT, 6 HIGH, 5 MED, 4 LOW) | 6 critical stories |
| **Test Coverage** (Frente 3) | 6 critical gaps, 8 high gaps, 12 missing categories | 8 critical stories |
| **Historical Bugs** (Frente 5) | 7 bugs reviewed, 5/7 lack regression tests | 6 stories |
| **TOTALS** | **~80 findings** | **~24 unique stories** |

### Overall Safety Score: 4.5/10

| Category | Score | Assessment |
|----------|-------|------------|
| Domain Logic | 8/10 | Strong filtering, synonym matching, LLM arbiter |
| Code Structure | 4/10 | God function, triple Redis, 35 deferred imports |
| Security | 3/10 | 4 CRITICAL vulns (cache collision, OAuth CSRF, hardcoded key) |
| Test Coverage | 5.5/10 | Core modules excellent, billing/auth/SSE have zero coverage |
| Operational Readiness | 4/10 | No env var validation, debug endpoints exposed, no security headers |
| LGPD Compliance | 2/10 | Missing privacy policy, deletion, cookie consent, retention |

---

## GTM Readiness Verdict

### DO NOT SHIP until the following are resolved:

**Tier 0 -- Deploy Today (1-2 hours, zero code changes needed):**
1. Verify `SUPABASE_JWT_SECRET` in Railway production (SEC CRIT-01)
2. Verify `ENCRYPTION_KEY` in Railway production (SEC CRIT-03)

**Tier 1 -- Fix This Week (3-5 days engineering):**
3. Fix token cache hash collision -- 1 line change (SEC CRIT-02 / ARCH HIGH-02)
4. Secure OAuth CSRF with cryptographic nonce (SEC CRIT-04)
5. Remove hardcoded encryption key fallback (SEC CRIT-03)
6. Disable Swagger/debug endpoints in production (SEC HIGH-01/02)
7. Add security headers (SEC HIGH-05)
8. Fix `asyncio.run()` crash in redis_client.py (ARCH HIGH-04)
9. Replace blocking `time.sleep()` in async code (ARCH HIGH-01)

**Tier 2 -- Fix Before Launch (5-8 days engineering):**
10. Decompose god function `buscar_licitacoes` (ARCH CRIT-01)
11. Unify Redis clients (ARCH CRIT-02)
12. Rewrite stale auth test suite (BUGS Pattern-1)
13. Add Stripe/billing test suite (TEST C1)
14. Fix frontend CI -- remove `|| true` (TEST QA-01)
15. Quarantine 91 pre-existing test failures (TEST QA-06)

**Tier 3 -- Fix Before Paid Scale (10+ days):**
16. LGPD compliance sprint (SEC-08)
17. Shared API contract / OpenAPI TypeScript codegen (ARCH CRIT-03)
18. SSE progress tracking tests (TEST C2)
19. Route coverage expansion (TEST QA-08)
20. Lead prospecting tests (TEST QA-07)

---

## Consolidated Risk Heatmap

The following table de-duplicates findings across all four audits. Where the same issue was identified by multiple audits, it is listed once with cross-references.

### CRITICAL (9 unique findings)

| # | Finding | Source(s) | Impact | Fix Effort |
|---|---------|-----------|--------|------------|
| 1 | **Token cache key collision** -- first 16 chars of JWT are identical for all HS256 tokens. Horizontal privilege escalation. | SEC CRIT-02, ARCH HIGH-02, BUGS Bug-2 | CVSS 9.1: User A impersonates User B | 0.5 day |
| 2 | **JWT production error** -- `SUPABASE_JWT_SECRET` missing/incorrect in Railway | SEC CRIT-01, BUGS Bug-2 | All auth fails, app non-functional | 1 hour (env var fix) |
| 3 | **OAuth CSRF forgeable** -- state param is `base64(user_id:redirect)`, no nonce, callback has no auth, open redirect | SEC CRIT-04 | Token hijacking, open redirect | 2 days |
| 4 | **Hardcoded encryption fallback** -- all-zeros key for OAuth tokens when `ENCRYPTION_KEY` not set | SEC CRIT-03 | Mass token compromise | 0.5 day |
| 5 | **God function** -- `buscar_licitacoes` at 860+ lines, cyclomatic complexity 50+, single point of failure | ARCH CRIT-01 | Unmaintainable, untestable | 3 days |
| 6 | **Triple Redis architecture** -- 3 clients (async, sync, per-request), inconsistent fallback, connection waste | ARCH CRIT-02 | Connection exhaustion, subtle bugs | 2 days |
| 7 | **Backend-frontend contract mismatch** -- proxy silently drops 5+ fields, no type generation | ARCH CRIT-03 | Silent data loss, feature breakage | 2 days |
| 8 | **Stripe/billing ZERO test coverage** -- revenue-critical path has placeholder assertions only | TEST C1 | Undetected payment failures | 3 days |
| 9 | **29 stale auth tests** -- all mock deprecated `sb.auth.get_user()`, cover zero production code | BUGS Pattern-1 | False confidence, regression invisible | 2 days |

### HIGH (18 unique findings)

| # | Finding | Source(s) | Fix Effort |
|---|---------|-----------|------------|
| 10 | Blocking `time.sleep(0.3)` in async authorization.py | ARCH HIGH-01 | 0.5 day |
| 11 | `asyncio.run()` inside running event loop in redis_client.py | ARCH HIGH-04 | 0.5 day |
| 12 | Stripe API key set at module level (non-thread-safe) | ARCH HIGH-05 | 0.5 day |
| 13 | Filesystem Excel download fails in multi-instance deployment | ARCH HIGH-06 | 1 day |
| 14 | Deprecated `@app.on_event("startup")` | ARCH HIGH-07 | 0.5 day |
| 15 | Dual router mounting doubles attack surface | ARCH HIGH-08, SEC LOW-04 | 1 day |
| 16 | Swagger/OpenAPI/debug endpoints exposed in production | SEC HIGH-01/02 | 0.5 day |
| 17 | JWT audience verification disabled | SEC HIGH-03 | 0.25 day |
| 18 | Weak 6-char password policy | SEC HIGH-04 | 0.5 day |
| 19 | No security headers (CSP, HSTS, X-Frame-Options, etc.) | SEC HIGH-05 | 1 day |
| 20 | Plans endpoint leaks Stripe Price IDs without auth | SEC HIGH-06 | 0.25 day |
| 21 | SSE progress tracking: zero tests for complex async code | TEST C2 | 2 days |
| 22 | Google OAuth E2E: zero tests for primary login method | TEST C3 | 1.5 days |
| 23 | Lead prospecting: 5 modules, 500+ LOC, zero tests | TEST C4 | 2 days |
| 24 | Middleware/authorization: zero tests for security code | TEST C5 | 1.5 days |
| 25 | Frontend CI uses `|| true` -- test failures invisible | TEST QA-01 | 1 day |
| 26 | 6 of 12 backend route modules have zero test files | TEST H6 | 3 days |
| 27 | Dead quota locks -- `_quota_locks` defined but never used | BUGS Bug-6 | 0.5 day |

### MEDIUM (23 unique findings)

| # | Finding | Source(s) |
|---|---------|-----------|
| 28 | 35 deferred Supabase imports (dependency injection needed) | ARCH MED-01 |
| 29 | Duplicate sync/async code in pncp_client.py | ARCH MED-02 |
| 30 | `Optional[any]` type annotations (lowercase any) | ARCH MED-03 |
| 31 | 8 `any` types in frontend TypeScript | ARCH MED-04 |
| 32 | `dateDiffInDays` duplicated across files | ARCH MED-05 |
| 33 | No error boundary beyond root `error.tsx` | ARCH MED-06 |
| 34 | `InMemoryCache` has no size limit | ARCH MED-07 |
| 35 | `_` prefix functions used cross-module | ARCH MED-08 |
| 36 | Plan capabilities hardcoded in if/elif chain (OCP violation) | ARCH MED-09 |
| 37 | `response.text()` on consumed body | ARCH MED-10 |
| 38 | Feature flags not runtime-reloadable | ARCH MED-11 |
| 39 | sectors.py is 1600+ lines of static data | ARCH MED-12 |
| 40 | `STRIPE_WEBHOOK_SECRET` not validated at startup | SEC MED-01 |
| 41 | In-memory rate limiter per-instance only | SEC MED-02 |
| 42 | SSE progress endpoint lacks user isolation | SEC MED-03 |
| 43 | Error responses leak internal details | SEC MED-04 |
| 44 | `dangerouslySetInnerHTML` in layout.tsx | SEC MED-05 |
| 45 | `/api/features/me` lacks multi-layer plan fallback | BUGS Bug-3 |
| 46 | Silent failure anti-pattern (catch+log, no retry/metric) | BUGS Pattern-2 |
| 47 | Multiple sources of truth for user plan | BUGS Pattern-3 |
| 48 | LandingNavbar shows Login to logged-in users | BUGS Bug-4 |
| 49 | Search history save is silently swallowed | BUGS Bug-5 |
| 50 | Correlation IDs only partially implemented | BUGS Pattern-5 |

---

## Frente 1: Codebase Architecture

**Full report:** `docs/reports/AUDIT-FRENTE-1-CODEBASE.md`

### Key Metrics

| Metric | Value |
|--------|-------|
| Total findings | 32 (3 CRIT, 8 HIGH, 12 MED, 9 LOW) |
| SOLID rating | S:D, O:D, L:B, I:C, D:D |
| Largest function | `buscar_licitacoes()` -- 860+ lines |
| Global mutable singletons | 7 |
| Deferred imports | 35 across 18 files |
| Dead code instances | 4 identified |
| Frontend `any` types | 8 |
| Error boundaries | 1 (root only) |

### Top 3 Structural Issues

1. **God Function** (CRIT-01): `routes/search.py:buscar_licitacoes()` handles request validation, quota checking, plan capability resolution, term parsing, PNCP API calls, filtering (5 stages), LLM arbiter, relevance scoring, deduplication, pagination, Excel generation, LLM summary, and session saving -- all in one 860-line function with 12+ inline imports and an inline class definition.

2. **Triple Redis** (CRIT-02): Three independent Redis connection strategies with different client types (async vs sync), different fallback behaviors, and one that creates a new connection per request.

3. **Contract Mismatch** (CRIT-03): Frontend proxy silently drops `source_stats`, `hidden_by_min_match`, `filter_relaxed`, `synonym_matches`, `llm_arbiter_stats` from backend responses. Frontend types define fields that don't exist in backend schemas.

---

## Frente 2: Security

**Full report:** `docs/reports/AUDIT-FRENTE-2-SECURITY.md`

### Key Metrics

| Metric | Value |
|--------|-------|
| Total findings | 19 (4 CRIT, 6 HIGH, 5 MED, 4 LOW) |
| CVSS 9.0+ findings | 1 (token cache collision) |
| CVSS 8.0+ findings | 3 (OAuth CSRF, encryption fallback, cache collision) |
| Missing security headers | 7 (CSP, HSTS, X-Frame, etc.) |
| LGPD compliance items failed | 8 of 13 |
| Known CVEs in dependencies | 0 |

### Top 3 Security Issues

1. **Token Cache Collision** (CRIT-02, CVSS 9.1): Auth cache key uses only first 16 chars of JWT. All Supabase HS256 JWTs share the same 16-char prefix (`eyJhbGciOiJIUzI1`). User B authenticating within 60s of User A gets User A's identity. **One line fix**: `token[:16]` -> `token`.

2. **OAuth CSRF** (CRIT-04, CVSS 8.1): The OAuth state parameter is `base64(user_id:redirect_path)` -- predictable, forgeable, no nonce. Callback has no authentication. Redirect path is not validated (open redirect).

3. **Hardcoded Encryption Fallback** (CRIT-03, CVSS 8.6): When `ENCRYPTION_KEY` env var is absent, all OAuth tokens are encrypted with a hardcoded all-zeros key visible in source code.

---

## Frente 3: Test Coverage

**Full report:** `docs/reports/AUDIT-FRENTE-3-TESTS.md`

### Key Metrics

| Metric | Value |
|--------|-------|
| Overall Safety Net Score | 5.5/10 |
| Backend test files | 64 in `backend/tests/` |
| Frontend test files | 75+ in `frontend/__tests__/` |
| E2E spec files | 14 in `frontend/e2e-tests/` |
| Pre-existing backend failures | 21 (billing/stripe/prorata) |
| Pre-existing frontend failures | 70 (various) |
| Total pre-existing failures | **91** |
| Modules with ZERO tests | 11 backend modules, 1 critical frontend page |
| Frontend CI enforces tests? | **NO** (`|| true` in CI) |

### Critical Coverage Gaps

| Module | Impact | Score |
|--------|--------|-------|
| Stripe webhooks/billing/subscriptions | Revenue loss | 0-2/10 |
| SSE progress tracking | Frozen UI | 0/10 |
| Google OAuth E2E | Onboarding failure | 0/10 |
| Lead prospecting (5 modules) | Feature regression | 0/10 |
| Middleware/authorization | Security bypass | 0/10 |
| Frontend buscar page (integration) | Core feature | 4/10 |

### The Coverage Debt Spiral

The 91 pre-existing failures have created a vicious cycle:
1. Tests break -> thresholds lowered (60% -> 49% -> 44% -> 35%)
2. Frontend CI uses `|| true` -> failures invisible
3. Developers treat tests as obstacles -> less test investment
4. More tests break -> cycle continues

---

## Frente 5: Historical Bugs

**Full report:** `docs/reports/AUDIT-FRENTE-5-HISTORICAL-BUGS.md`

### Bug Status Summary

| # | Bug | Fixed? | Regression Test? | Remaining Risk |
|---|-----|--------|-----------------|----------------|
| 1 | Logging cascade (missing request_id) | YES | **NO** | Fragile import chain |
| 2 | JWT InvalidAlgorithmError | YES | **NO** (29 stale tests) | Stale tests = false confidence |
| 3 | Paid users treated as free | YES (4-layer fallback) | Partial | `/api/features/me` skips fallback |
| 4 | Login button visible to logged-in users | YES (by design) | **NO** | UX issue on landing page |
| 5 | Search history not saved | YES | **NO** | Silent failure, no retry |
| 6 | Inconsistent quota consumption | YES (atomic RPC) | Partial | `_quota_locks` is dead code |
| 7 | Incorrect header state on /buscar | ARCHITECTURE RISK | **NO** | Not using protected layout |

### Most Dangerous Finding

**ALL 29 AUTH TESTS ARE STALE.** The auth module was rewritten from Supabase API validation (`sb.auth.get_user()`) to local JWT validation (`jwt.decode()`) on 2026-02-11. But every test still mocks the old API. These tests pass but cover zero lines of production code. This is the exact pattern that caused the original P0 JWT outage.

---

## Cross-Frente Patterns

Five systemic patterns emerge across all four audits:

### Pattern A: Security-Critical Code Has Zero Tests

| Security Code | Test Coverage | Risk |
|--------------|--------------|------|
| `auth.py` (JWT validation) | 0% of production path (stale mocks) | Auth bypass undetected |
| `authorization.py` (role checks) | 0% | Admin exposure undetected |
| `middleware.py` (correlation IDs) | 0% | Logging cascade undetected |
| `webhooks/stripe.py` (payment) | ~5% (placeholder asserts) | Revenue loss undetected |
| `oauth.py` (token encryption) | Basic tests, no production-env test | Token compromise undetected |

### Pattern B: Multiple Sources of Truth

User plan information comes from 4 sources that can diverge:
1. `user_subscriptions` table (primary)
2. `profiles.plan_type` column (fallback)
3. Frontend localStorage (1hr TTL)
4. Redis features cache (5min TTL)

The `/buscar` endpoint uses a 4-layer lookup but `/api/features/me` only checks source 1 and falls back to `free_trial`, creating inconsistent UX for paid users.

### Pattern C: Silent Failure Anti-Pattern

At least 5 critical code paths catch exceptions and silently continue:
- Search history save (routes/search.py)
- Quota fallback (routes/search.py)
- Feature flags (routes/features.py)
- Admin check retry (authorization.py)
- Redis connection (redis_client.py, cache.py)

While this improves resilience, it makes production debugging extremely difficult. No error counters or metrics exist to detect systemic silent failures.

### Pattern D: Architectural Boundaries Are Porous

- 35 files use deferred imports of `get_supabase()` instead of dependency injection
- `routes/search.py` imports from 15+ modules and defines an inline class
- `quota.py` handles quota management AND session saving (SRP violation)
- `sectors.py` embeds 1600+ lines of configuration data in Python source

### Pattern E: CI Pipeline Provides False Confidence

The CI pipeline appears functional but has critical weaknesses:
- Frontend tests run with `|| true` (failures never block merges)
- Coverage threshold lowered from 60% to 35-44%
- Integration test job is a placeholder (`echo "will be implemented"`)
- 91 pre-existing failures mask new regressions

---

## LGPD Compliance

Brazilian LGPD (Lei Geral de Protecao de Dados) compliance is required for a product targeting Brazilian businesses.

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Lawful basis for processing | PARTIAL | Add explicit consent dialog at signup |
| Purpose limitation | PASS | -- |
| Data minimization | PASS | -- |
| Accuracy | PASS | -- |
| Storage limitation | **FAIL** | Add retention policy; auto-delete sessions > 365 days |
| Integrity & confidentiality | PARTIAL | Fix encryption fallback key |
| Transparency | **FAIL** | Add privacy policy page at `/privacidade` |
| Right to access | PARTIAL | Add `GET /me/export` for data portability |
| Right to deletion | **FAIL** | Add `DELETE /me` self-service account deletion |
| Right to portability | **FAIL** | Add data export as JSON |
| Data Protection Officer | **FAIL** | Designate DPO |
| Cookie consent | **FAIL** | Add consent banner for Mixpanel analytics |
| Records of processing | **FAIL** | Create ROPA (Records of Processing Activities) |

**LGPD Verdict:** NOT COMPLIANT. Must address deletion, privacy policy, cookie consent, and data retention before GTM.

---

## Proposed Story Backlog

### Tier 0: Deploy Today (0 engineering days)

| ID | Title | Source | Effort |
|----|-------|--------|--------|
| OPS-01 | Verify SUPABASE_JWT_SECRET in Railway production | SEC CRIT-01 | 1 hour |
| OPS-02 | Verify ENCRYPTION_KEY in Railway production | SEC CRIT-03 | 1 hour |

### Tier 1: Fix This Week -- Pre-GTM Critical (5 days)

| ID | Title | Source | Effort |
|----|-------|--------|--------|
| SEC-01 | Fix token cache key collision (hash full token) | SEC CRIT-02, ARCH HIGH-02 | 0.5 day |
| SEC-02 | Secure OAuth CSRF with cryptographic nonce | SEC CRIT-04 | 2 days |
| SEC-03 | Remove hardcoded encryption key fallback | SEC CRIT-03 | 0.5 day |
| SEC-04 | Disable Swagger + remove debug endpoint in production | SEC HIGH-01/02 | 0.5 day |
| SEC-05 | Add security headers (backend + frontend) | SEC HIGH-05 | 1 day |
| FIX-01 | Fix `asyncio.run()` crash in redis_client.py | ARCH HIGH-04 | 0.5 day |

### Tier 2: Fix Before Launch -- Pre-GTM Important (15 days)

| ID | Title | Source | Effort |
|----|-------|--------|--------|
| REFACTOR-01 | Decompose `buscar_licitacoes` into SearchPipeline | ARCH CRIT-01 | 3 days |
| REFACTOR-02 | Unify Redis into single async client with pool | ARCH CRIT-02 | 2 days |
| REFACTOR-03 | Shared API contract (OpenAPI TypeScript codegen) | ARCH CRIT-03 | 2 days |
| QA-01 | Fix frontend CI (remove `|| true`, quarantine failures) | TEST QA-01 | 1 day |
| QA-02 | Stripe/billing test suite (20+ tests) | TEST C1 | 3 days |
| QA-03 | Rewrite 29 stale auth tests for JWT validation | BUGS Pattern-1 | 2 days |
| QA-04 | SSE progress tracking tests (12+ tests) | TEST C2 | 2 days |

### Tier 3: Fix Before Paid Scale (20 days)

| ID | Title | Source | Effort |
|----|-------|--------|--------|
| SEC-06 | Strengthen password policy (8+ chars, complexity) | SEC HIGH-04 | 0.5 day |
| SEC-07 | Enable JWT audience verification | SEC HIGH-03 | 0.25 day |
| SEC-08 | LGPD compliance sprint (privacy, deletion, cookies) | SEC LGPD | 5 days |
| FIX-02 | Replace blocking `time.sleep()` with `asyncio.sleep()` | ARCH HIGH-01 | 0.5 day |
| FIX-03 | Use per-request Stripe client instances | ARCH HIGH-05 | 0.5 day |
| FIX-04 | Migrate to FastAPI lifespan context manager | ARCH HIGH-07 | 0.5 day |
| FIX-05 | Validate required env vars at startup | Cross-cutting | 0.5 day |
| QA-05 | Google OAuth E2E test (6+ tests) | TEST C3 | 1.5 days |
| QA-06 | Security/authorization test suite (15+ tests) | TEST C5 | 1.5 days |
| QA-07 | Quarantine and triage 91 pre-existing failures | TEST QA-06 | 2 days |
| QA-08 | Route coverage expansion (6 modules, 48+ tests) | TEST QA-08 | 3 days |
| QA-09 | Lead prospecting test suite (20+ tests) | TEST QA-07 | 2 days |
| CLEANUP-01 | Remove dead code from quota.py | ARCH HIGH-03 | 0.5 day |
| CLEANUP-02 | Remove filesystem Excel fallback | ARCH HIGH-06 | 1 day |
| CLEANUP-03 | Add deprecation warnings on legacy routes | ARCH HIGH-08 | 1 day |

### Tier 4: Post-GTM Polish (10 days)

| ID | Title | Source | Effort |
|----|-------|--------|--------|
| REFACTOR-04 | Extract sectors.py to YAML configuration | ARCH MED-12 | 1 day |
| REFACTOR-05 | Add route-specific error boundaries | ARCH MED-06 | 1 day |
| REFACTOR-06 | Dependency injection for Supabase | ARCH MED-01 | 2 days |
| REFACTOR-07 | Data-driven plan capabilities (OCP) | ARCH MED-09 | 1 day |
| FIX-06 | Add size limit to InMemoryCache | ARCH MED-07 | 0.25 day |
| FIX-07 | Align `/api/features/me` with multi-layer fallback | BUGS Bug-3 | 1 day |
| FIX-08 | LandingNavbar auth-aware CTA | BUGS Bug-4 | 0.5 day |
| FIX-09 | Search history reliability (retry + metrics) | BUGS Bug-5 | 1 day |
| FIX-10 | Fix dead quota locks or remove | BUGS Bug-6 | 0.5 day |
| CLEANUP-04 | Eliminate `any` types in frontend | ARCH MED-04 | 0.5 day |
| CLEANUP-05 | Extract `dateDiffInDays` to shared util | ARCH MED-05 | 0.25 day |
| QA-10 | Logging cascade regression tests | BUGS Bug-1 | 1 day |

---

## Effort Summary

| Tier | Stories | Engineering Days | GTM Impact |
|------|---------|-----------------|------------|
| **T0: Deploy Today** | 2 | 0 (ops only) | Unblocks auth |
| **T1: This Week** | 6 | 5 | Closes critical security holes |
| **T2: Before Launch** | 7 | 15 | Architectural stability + test safety net |
| **T3: Before Paid Scale** | 15 | 20 | Full security + test coverage |
| **T4: Post-GTM Polish** | 12 | 10 | Technical debt reduction |
| **TOTAL** | **42** | **~50 days** | |

### Recommended Sprint Plan

**Sprint 1 (Week 1):** Tiers 0 + 1 = 5 days
- Focus: Security hardening, env var fixes, critical 1-line patches
- Exit criteria: Zero CRITICAL security findings, auth works in production

**Sprint 2 (Weeks 2-3):** Tier 2 = 15 days (2 devs, 7.5 days)
- Focus: God function decomposition, Redis unification, test foundation
- Exit criteria: CI runs green, billing tests exist, auth tests cover production code

**Sprint 3 (Weeks 4-5):** Tier 3 = 20 days (2 devs, 10 days)
- Focus: LGPD compliance, remaining test coverage, password policy
- Exit criteria: LGPD compliance checklist passes, all routes have tests

**Sprint 4+ (Post-GTM):** Tier 4 = 10 days
- Focus: Polish, error boundaries, DI, config extraction
- Ongoing debt reduction

---

## Appendix: Source Reports

| Report | Location | Findings |
|--------|----------|----------|
| Frente 1: Codebase Architecture | `docs/reports/AUDIT-FRENTE-1-CODEBASE.md` | 32 findings, 19 stories |
| Frente 2: Security | `docs/reports/AUDIT-FRENTE-2-SECURITY.md` | 19 findings, 8 stories |
| Frente 3: Test Coverage | `docs/reports/AUDIT-FRENTE-3-TESTS.md` | 6C + 8H gaps, 8 stories |
| Frente 5: Historical Bugs | `docs/reports/AUDIT-FRENTE-5-HISTORICAL-BUGS.md` | 7 bugs, 6 stories |

---

*Consolidated audit report generated on 2026-02-12 by @architect (Claude Opus 4.6)*
*Total files analyzed: ~140+ (50 backend Python, 90+ frontend TypeScript/config)*
*Methodology: Line-by-line code read, grep pattern analysis, security review, test inventory, historical bug trace*
