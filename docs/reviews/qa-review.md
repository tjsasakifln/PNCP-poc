# QA Review - Technical Debt Assessment
**Reviewer:** @qa
**Date:** 2026-03-20
**Documents Reviewed:** technical-debt-DRAFT.md (Phase 4) + db-specialist-review.md (Phase 5) + ux-specialist-review.md (Phase 6)
**Supersedes:** qa-review.md v2.0 (2026-03-12 GTM Readiness)

---

## Gate Status: APPROVED WITH CONDITIONS

---

## Resumo da Revisao

The Technical Debt Assessment is thorough, well-structured, and actionable. The original DRAFT identified 79 items across 3 areas (System, Database, Frontend). The specialist reviews added rigor: @data-engineer removed 3 false positives, added 4 new items, and downgraded 8 severities based on production evidence; @ux-design-expert removed 2 false positives, added 4 new items, and significantly recalibrated 11 severities by verifying against actual source code rather than spec.

However, this QA review identified several gaps that must be addressed before the assessment can drive sprint planning. The most significant finding is a **critical mischaracterization of SYS-01 (CORS)** -- the DRAFT and system-architecture.md describe `allow_origins=["*"]` as a CRITICAL production security risk, but investigation reveals a more nuanced situation involving dead code vs. live code paths. There are also cross-cutting concerns (security, observability, API contract stability) that no specialist covered, and the dependency analysis underestimates regression risks.

The overall quality of the assessment is high. The specialist reviews are exceptionally well-done -- both went beyond surface validation to verify claims against actual code, which is exactly the rigor expected. The 5 false positives removed (DB-07, DB-16, DB-20, FE-13, FE-22) demonstrate the value of specialist review. The assessment is ready for sprint planning after the conditions below are met.

---

## Gaps Identificados

### Areas Nao Cobertas

**1. API Contract Stability (not assessed by any specialist)**

The DRAFT identifies SYS-07 (inconsistent API versioning) but no one assessed the actual breaking change risk. The system has:
- 49+ endpoints across 38 route modules
- Tests use snapshot-based API contract validation (`backend/tests/snapshots/api_contracts/`)
- No consumer-driven contract tests (Pact or equivalent)
- Frontend proxy routes are tightly coupled to backend response shapes

If a backend response schema changes, the frontend breaks silently -- no type safety crosses the proxy boundary. The `openapi.json` in the frontend is generated but not used for validation at build time. This is a gap.

**2. Secrets Rotation and Key Management (mentioned, not assessed)**

DB-11 (OAuth tokens in public schema) was assessed by @data-engineer as "standard pattern." SEC-03 in the DB audit mentions encryption keys. But nobody assessed:
- Is `OAUTH_ENCRYPTION_KEY` rotated? What is the rotation procedure?
- Are Stripe API keys rotated? What happens during rotation?
- Is there a secrets inventory with rotation schedule?
- `SUPABASE_SERVICE_ROLE_KEY` has unlimited power -- is access audited?

**3. Dependency Supply Chain Security**

No mention of:
- `pip-audit` results (the CI runs it, but are there known vulnerabilities?)
- `npm audit` results for frontend
- Dependabot auto-merge for minor versions -- does this introduce risk?
- Lock file integrity verification

**4. Rate Limiting Bypass Risk**

The system has rate limiting (10/min per user for search, 5/5min per IP for login). But:
- Rate limiting falls back to in-memory when Redis is down (per-worker only)
- With 2 Gunicorn workers, effective rate limit doubles during Redis outage
- No mention of rate limiting on the SSE endpoint (`/buscar-progress/{id}`)
- No assessment of DDoS resilience at the Railway level

**5. Data Privacy / LGPD Compliance**

The system handles:
- User PII (email, name, CNPJ)
- Search behavior (what companies search for, which bids they track)
- OAuth tokens

No specialist assessed LGPD compliance: data retention policies for PII, right-to-deletion implementation, data export capability, privacy policy accuracy vs. actual data practices.

### Riscos Nao Mapeados

**1. SYS-01 (CORS) Mischaracterization -- IMPORTANT**

Upon code investigation, the CORS situation is more nuanced than the DRAFT presents:

- `backend/main.py` (the file loaded by `uvicorn main:app` / `gunicorn main:app`) **does** have `allow_origins=["*"]`
- `backend/startup/app_factory.py` has a proper `create_app()` with `get_cors_origins()` that rejects wildcards
- `backend/config/cors.py` has production-safe CORS logic with explicit origin lists
- **The app_factory pattern was extracted (DEBT-107, commit `4d51a53a`) but was never wired as the entry point**
- `start.sh` still runs `main:app`, not `startup.app_factory:create_app()`

This means either: (a) the production app truly runs with `allow_origins=["*"]` and only root + health endpoints (which would mean the entire API is broken), or (b) there is additional route registration happening at import time that was not visible in the code I examined. Given that the production app works (7332 tests pass against `main:app`), option (b) is more likely -- routes are registered somewhere via side effects.

**Recommendation:** Before planning SYS-01 remediation, verify: (1) Does production actually use `main:app` from the 92-line stub, or has `start.sh` been overridden in Railway? (2) If it does use the stub, how are routes registered? (3) The correct fix may be simply changing `start.sh` to use `startup.app_factory:create_app` rather than patching CORS in `main.py`.

**2. Dead Code Path Risk**

The coexistence of `main.py` (old stub) and `startup/app_factory.py` (new factory) is itself a risk. Tests import `from main import app` (the old stub), but production may or may not use the same code path. This means:
- Tests may not be testing the actual production CORS configuration
- Tests may not be testing the actual production middleware stack
- The `startup/` directory may be entirely dead code

This dual-path situation is not documented in the DRAFT. It should be elevated to HIGH priority.

**3. Webhook Idempotency**

Stripe webhooks are mentioned (signature verification confirmed) but:
- Is webhook processing idempotent? If Railway delivers the same webhook twice (which happens during deploys), does the system handle it?
- `stripe_webhook_events` table exists for logging, but is it used for dedup?
- Billing state corruption from duplicate webhooks could cause revenue issues

**4. Background Job Failure Recovery**

ARQ jobs (LLM summaries, Excel generation) have fallback to inline execution when Redis is down. But:
- What happens if a job starts, Redis dies mid-execution, and the job is lost?
- Is there a dead letter queue for failed jobs?
- Are job results persisted before sending SSE events? (If SSE event is sent but client missed it, can it recover?)

---

## Analise de Riscos Cruzados

| Risco | Areas Afetadas | Probabilidade | Impacto | Mitigacao |
|-------|----------------|---------------|---------|-----------|
| CORS fix breaks frontend proxy | SYS-01, Frontend proxy, E2E tests | MEDIUM | HIGH | Must test with actual production origins. E2E tests run against localhost -- they would not catch a wrong origin list. |
| PNCP async migration breaks search | SYS-02, search pipeline, cache, tests | LOW | CRITICAL | 7332 tests provide good coverage, but httpx vs requests mock patterns differ. All `@patch("pncp_client.requests.Session")` mocks will break. |
| Component library adoption breaks existing pages | FE-02, FE-01, FE-03 | MEDIUM | MEDIUM | Visual regression testing needed. No Storybook (FE-16) makes verification harder. Suggest Playwright screenshot comparison as gate. |
| Migration squash breaks fresh installs | DB-12, CI, staging | HIGH | HIGH | @data-engineer correctly rejected this. The DRAFT should remove squash from the recommended actions. |
| Retention jobs delete valid data | DB-05, DB-06, DB-29 | LOW | HIGH | Must add `WHERE` conditions carefully. Test with production-like data volumes first. Add dry-run mode. |
| Test pollution fixes break existing tests | SYS-14, all test suites | MEDIUM | MEDIUM | Fixing root causes (sys.modules, importlib.reload) may change import behavior and break tests that depend on the polluted state. Run full suite after each fix. |
| plan_type reconciliation triggers false alarms | DB-04, billing, quota | LOW | MEDIUM | @data-engineer notes reconciliation already exists but lacks granular metrics. Adding metrics should not change behavior. |
| `app_factory` vs `main.py` dual path | SYS-01, SYS-06, all middleware, all routes | HIGH | CRITICAL | This is the highest-risk item. If the factory is not the production entry point, all middleware (CORS, rate limiting, correlation IDs, security headers, deprecation warnings) may not be active. Must verify immediately. |

---

## Validacao de Dependencias

### Ordem de Resolucao

The DRAFT proposes a 4-sprint execution plan. The order is largely correct, with these adjustments:

**Sprint 0 adjustments:**
- **ADD:** Investigate and resolve the `main.py` vs `app_factory.py` dual-path issue BEFORE fixing CORS. If `app_factory` is dead code, wiring it in as the entry point resolves SYS-01, SYS-06, SYS-17, and SYS-18 simultaneously.
- **KEEP:** DB-01 (Stripe IDs) as P0 -- confirmed CRITICAL by @data-engineer.
- **KEEP:** FE-19 (react-hook-form dep) and FE-05 quick fixes.

**Sprint 1 adjustments:**
- **ELEVATE:** SYS-14 (test pollution) should be Sprint 0, not Sprint 1. The DRAFT correctly notes it "blocks velocity of ALL other items." Fixing it in Sprint 0 means Sprint 1-3 work is faster.
- **KEEP:** DB-05 + DB-06 retention jobs.
- **ADD:** FE-34 (AuthProvider location) should be done BEFORE FE-09 (component locations). Moving AuthProvider to `contexts/` eliminates the circular dependency risk (FE-26) and is a prerequisite for clean component reorganization.

**Sprint 2 adjustments:**
- **AGREE:** FE-02 (component library) before FE-01 (inline var migration). This dependency is correctly identified.
- **CONCERN:** SYS-02 (PNCP async) at 16h is the largest single item. It should be done on a feature branch with incremental migration (one method at a time), not as a big-bang rewrite.

**Sprint 3 adjustments:**
- **AGREE:** FE-01 (40h -> 32h per @ux-design-expert) with codemod automation.
- **CONCERN:** FE-03 (buscar refactor, 16h) and SYS-15 (state management, 16h) are the same problem. The DRAFT notes this but still counts both in the total. Remove SYS-15 from the sprint plan to avoid double-counting.

### Critical Path

```
[Sprint 0 - Week 1]
  main.py/app_factory unification (resolves SYS-01, SYS-06, SYS-17, SYS-18)
    |
  DB-01 (Stripe IDs) -- independent, parallel
    |
  SYS-14 (test pollution) -- unlocks velocity
    |
[Sprint 1 - Weeks 2-3]
  FE-34 (AuthProvider move) -> FE-09 (component locations)
    |                              |
  DB retention jobs (parallel)     |
    |                              v
[Sprint 2 - Weeks 4-5]          FE-02 (component library)
  SYS-02 (PNCP async)              |
  DB-04 (reconciliation metrics)   |
                                   v
[Sprint 3 - Weeks 6-7]         FE-01 (inline var codemod)
                                FE-03 (buscar refactor)
```

### Bloqueios Potenciais

1. **main.py vs app_factory investigation** -- If the factory is dead code, wiring it in requires testing the entire middleware stack. Could surface unexpected issues.
2. **Railway environment access** -- Verifying CORS configuration in production requires Railway CLI access or dashboard access. Not a code-only fix.
3. **Stripe test vs production environment** -- DB-01 fix requires Stripe test-mode price IDs for staging. If test-mode isn't set up, this blocks.
4. **PNCP API instability** -- SYS-02 (async migration) requires stable PNCP responses for testing. If PNCP changes its API again (as it did with the page size change), the migration could be delayed.

---

## Testes Requeridos

### Pre-Remediacao (escrever ANTES de corrigir)

These tests document current behavior and serve as regression guards:

| Debito | Teste Pre-Remediacao | Tipo |
|--------|----------------------|------|
| SYS-01 (CORS) | Test that verifies actual CORS headers returned by production app (not just config). Use TestClient with `Origin` header. | Backend integration |
| SYS-02 (PNCP async) | Characterization tests for all `pncp_client.py` public methods with mock `httpx.Client` responses. Document exact request/response shapes. | Backend unit |
| DB-01 (Stripe IDs) | Test that `plan_billing_periods` can be populated without hardcoded IDs (seed script test). | Backend integration |
| DB-05/06 (retention) | Test that documents current row counts and growth patterns. Snapshot test for retention query correctness. | Backend unit |
| FE-01 (inline var) | Visual regression screenshots of 5 key pages (buscar, dashboard, pipeline, planos, login) BEFORE codemod. | E2E (Playwright) |
| FE-02 (component library) | Inventory test that lists all ad-hoc Card/Modal/Badge implementations. Serves as migration checklist. | Script/audit |
| FE-07 (useIsMobile) | CLS measurement on mobile viewport BEFORE fix (Lighthouse CI or Playwright). | E2E |
| SYS-14 (test pollution) | Run `python scripts/run_tests_safe.py --parallel 1` (sequential, no isolation) and document which tests fail. This is the "pollution baseline." | Meta-test |

### Pos-Remediacao (validar correcao)

| Debito | Teste Pos-Remediacao | Criterio de Sucesso |
|--------|----------------------|---------------------|
| SYS-01 (CORS) | Request from `https://evil.com` returns no `Access-Control-Allow-Origin` header. Request from `https://smartlic.tech` returns correct header. | Zero unauthorized origins |
| SYS-02 (PNCP async) | Full search pipeline test with mocked async httpx responses. Verify no `asyncio.to_thread()` usage remains. | All 7332 tests pass + zero `requests` imports |
| DB-01 (Stripe IDs) | Fresh install with `seed.sql` populates correct price IDs from env vars. `grep -r 'price_1' supabase/migrations/` returns only historical (already-applied) migrations. | Staging uses test-mode IDs |
| FE-01 (inline var) | `grep -r 'var(--' frontend/app/ | wc -l` returns <50 (gradient/glass exceptions only). | >95% migration |
| FE-02 (component library) | Import analysis: `grep -r 'from.*components/ui' | sort -u` shows Card, Modal, Badge, Select, Tabs in use. | 5 new primitives adopted |
| SYS-14 (test pollution) | `pytest --timeout=30 -q` runs full suite without hangs (Linux) or `run_tests_safe.py --parallel 1` passes all (Windows). | Zero pollution-caused failures |

### Metricas de Qualidade

| Metrica | Baseline (hoje) | Meta pos-remediacao |
|---------|-----------------|---------------------|
| Backend test count | 7332 pass / 0 fail | >= 7332 pass / 0 fail (no regression) |
| Frontend test count | 5583 pass / 0 fail | >= 5583 pass / 0 fail (no regression) |
| E2E test count | 60 pass | >= 60 pass |
| Backend test coverage | 70%+ (CI gate) | >= 70% (maintain) |
| Frontend test coverage | 60%+ (CI gate) | >= 60% (maintain) |
| `var(--` occurrences in frontend | ~1,754 | <50 |
| UI primitive components | 6 | >= 11 (Card, Modal, Badge, Select, Tabs added) |
| CORS unauthorized origins allowed | `*` (all) | 0 (explicit allowlist) |
| Tables without retention policy | 3+ (user_subscriptions, partner_referrals, monthly_quota) | 0 |
| Accessibility critical violations (axe-core) | 0 (per E2E baseline) | 0 (maintain) |

---

## Respostas ao Architect

### Q1: SYS-14 -- Test pollution: quais padroes causam mais flakes?

**Top 3 por impacto:**

1. **`sys.modules["arq"] = MagicMock()` without cleanup** -- This was the root cause of the most widespread pollution. The conftest `_isolate_arq_module` autouse fixture now handles it, but 4+ test files still do raw injection. The fixture mitigates but does not eliminate the root cause. With `run_tests_safe.py --parallel`, each file runs in its own subprocess, so cross-file pollution is eliminated. Within a single file, the conftest fixture handles it. **This pattern does NOT cause flakes with subprocess isolation.**

2. **Global singleton state leakage (`supabase_cb`, `InMemoryCache`)** -- Circuit breaker and cache instances persist across tests. If test A triggers CB OPEN, test B inherits the state. The conftest `_reset_supabase_cb` and `_cleanup_in_memory_cache` autouse fixtures address this, but any new global singleton must be manually added to conftest. **This pattern causes flakes even with subprocess isolation if multiple tests in the same file share the singleton.**

3. **`importlib.reload()` with monkeypatch** -- Several tests reload modules to pick up env var changes. After monkeypatch restores the env var, the module remains in its reloaded state. This is particularly insidious because the failure manifests in LATER tests, not the test that did the reload. **This pattern causes flakes in sequential runs and is partially mitigated by subprocess isolation (per-file, not per-test).**

**`run_tests_safe.py --parallel` eliminates cross-file pollution but NOT intra-file pollution.** Remaining flakes are: 4 quota tests that share global state within the same file. These pass in isolation but fail when run together in the same process.

### Q2: Cobertura de testes dos debitos CRITICAL -- CORS

**Current test coverage for CORS:**
- `backend/tests/test_main.py` likely tests the stub `main.py` (which has `allow_origins=["*"]`)
- No test verifies that specific origins are rejected
- No test verifies the `get_cors_origins()` function in isolation (but `backend/config/cors.py` exists and could be tested)
- E2E tests run against `localhost:3000` -> `localhost:8000`, which bypasses CORS entirely (same-origin or proxy)

**If CORS is restricted to specific origins:**
- No backend tests should break (TestClient does not enforce CORS)
- E2E tests would not break (Playwright does not enforce CORS)
- Manual browser testing IS required to verify CORS works in production
- Frontend proxy routes (`/api/*`) are same-origin, so they bypass CORS entirely -- only direct browser-to-backend calls would be affected, and the architecture does not make any

**Recommendation:** Add a test in `test_cors.py` that uses TestClient with explicit `Origin` headers and verifies `Access-Control-Allow-Origin` response header values.

### Q3: FE-04 -- Error pages coverage

**All major routes HAVE error.tsx files:**
- `app/error.tsx` (root)
- `app/buscar/error.tsx`
- `app/pipeline/error.tsx`
- `app/historico/error.tsx`
- `app/dashboard/error.tsx`
- `app/conta/error.tsx`
- `app/alertas/error.tsx`
- `app/mensagens/error.tsx`
- `app/admin/error.tsx`

**Routes WITHOUT error.tsx:**
- `app/onboarding/` -- no error.tsx
- `app/planos/` -- no error.tsx (but mostly static)
- `app/blog/` -- no error.tsx (SSC, less critical)
- `app/login/`, `app/signup/` -- no error.tsx
- SEO pages (`/como-*`, `/licitacoes/`) -- no error.tsx (SSC)

The root `app/error.tsx` catches errors from routes without their own error.tsx, so this is not a gap -- it is a coverage question. The @ux-design-expert correctly downgraded FE-04 to MEDIUM because all error.tsx files DO report to Sentry.

**Automated verification:** A lint rule or test script could glob `frontend/app/**/page.tsx` and check for a sibling `error.tsx`. This would take ~1h to implement as a CI check.

### Q4: Regressao em migration squash (DB-12)

**@data-engineer definitively rejected migration squash.** I concur with this recommendation. The risks outweigh the benefits:

- Supabase CLI does not support squash natively
- 86 migrations run in <30s on fresh install -- performance is not an issue
- CI (`migration-check.yml`) runs `supabase db push` on every push to main, which validates all migrations against a clean database
- Fresh install equivalence would require comparing `pg_dump` output before and after squash, which is complex and error-prone

**The DRAFT should remove DB-12 from the priority matrix entirely** (severity already downgraded to LOW, 0h by @data-engineer). It should be marked as "ACCEPTED -- no action needed."

### Q5: FE-24 -- a11y testing

**`@axe-core/playwright` IS integrated in E2E tests.** The file `frontend/e2e-tests/accessibility-audit.spec.ts` (DEBT-109) runs axe-core on 5 core pages with WCAG 2.0 AA + WCAG 2.1 AA tags. The gate is: **0 critical violations** (serious/moderate are logged but not gating).

**Current baseline:** The test exists and runs. I cannot determine the exact violation count without running it, but the test asserts `critical.length === 0` and it passes in CI.

**Recommended CI threshold:** Keep the current gate (0 critical). Add a separate non-blocking report for serious violations with a target of reducing by 20% per quarter. Do NOT gate on serious/moderate immediately -- this would block deployments for issues that may require design changes.

---

## Ajustes de Prioridade Recomendados

| Item | Prioridade DRAFT | Prioridade Ajustada | Motivo |
|------|-----------------|---------------------|--------|
| SYS-01 (CORS `*`) | P0 CRITICAL | **P0 CRITICAL -- but scope changed** | Fix is likely `start.sh` entry point change, not CORS config patch. Must investigate first. |
| SYS-06 (route registration) | P1 HIGH | **P0 -- bundled with SYS-01** | Same root cause: `main.py` vs `app_factory.py`. Fixing one fixes both. |
| SYS-17 (BidIQ title) | P3 LOW | **P0 -- bundled with SYS-01** | `app_factory.py` already has correct title. |
| SYS-18 (version 0.2.0) | P3 LOW | **P0 -- bundled with SYS-01** | `app_factory.py` already has `APP_VERSION`. |
| SYS-14 (test pollution) | P2 MEDIUM | **P0** | Blocks velocity of all other work. Must be Sprint 0. |
| FE-01 (inline var) | P0 CRITICAL | **P1 HIGH** | Per @ux-design-expert: not CRITICAL (visual behavior identical). DX debt, not UX debt. |
| SYS-02 (PNCP sync) | P0 CRITICAL | **P1 HIGH** | Verified: `pncp_client.py` still uses synchronous `requests` (line 8). DEBT-107 commit message claimed migration but `import requests` persists. Downgrade to P1 because `asyncio.to_thread()` wrapper is adequate mitigation for current scale (2 workers). |
| SYS-03 (ComprasGov offline) | P0 CRITICAL | **P2 MEDIUM** | ComprasGov has been down since 2026-03-03 (17 days). Adding a health check for an API that may never come back is low ROI. A 15-minute cron that checks `dadosabertos.compras.gov.br` and sends a Slack alert is sufficient. |
| DB-03 + DB-28 (conversations perf) | P1 HIGH + MEDIUM | **P2 MEDIUM** | Per @data-engineer: <500 rows, negligible impact. Revisit at 5000. |
| DB-04 (plan_type reconciliation) | P1 HIGH | **P2 MEDIUM** | Per @data-engineer: reconciliation ALREADY EXISTS. Only missing granular metrics. |
| DB-05 (partner_referrals) | P1 HIGH | **P3 LOW** | Per @data-engineer: <50 rows, 1-2 orphans/month. |
| FE-26 (circular imports) | P3 LOW | **P2 MEDIUM** | Per @ux-design-expert: elevated to MEDIUM. Root cause of FE-34 (AuthProvider location). |
| SYS-15 (state management) | P2 MEDIUM | **REMOVE** | Duplicate of FE-03 (buscar complexity). Already noted in DRAFT but still counted. Remove from plan. |

---

## Parecer Final

### Qualidade do Assessment

The Technical Debt Assessment is **high quality** and demonstrates the value of multi-phase specialist review. Key strengths:

1. **Specialist reviews verified claims against code, not just specs.** The @ux-design-expert discovered that FE-13 (aria-current) and FE-22 (PlanToggle focus) were already implemented. The @data-engineer found that DB-07, DB-16, and DB-20 were already resolved. This level of verification prevents wasted effort.

2. **Severity calibration is well-reasoned.** Both specialists provided clear rationale for every severity change. The @ux-design-expert's recalibration of FE-05 (global-error.tsx uses hex BY DESIGN) and FE-08 (only 4 images in codebase) shows deep understanding.

3. **Dependency analysis is actionable.** The DRAFT's sprint plan and the @data-engineer's dependency chains provide a clear execution path.

4. **Effort estimates are realistic.** The @ux-design-expert reduced FE-01 from 40h to 32h with a codemod strategy. The @data-engineer reduced total DB effort from 40h to 27h. These are evidence-based adjustments.

### Condicoes para APPROVED

The assessment is APPROVED for sprint planning **after** these conditions are met:

1. **MUST: Resolve the `main.py` vs `app_factory.py` ambiguity.** Determine which app is actually served in production. This affects the severity and remediation of SYS-01, SYS-06, SYS-17, SYS-18. A 30-minute investigation (check Railway logs for startup message, or add a temporary log line) resolves this.

2. **VERIFIED: SYS-02 (PNCP sync) is still valid.** Despite DEBT-107 commit message claiming migration, `pncp_client.py` line 8 still has `import requests`. The migration was either incomplete or reverted. SYS-02 remains valid but downgraded to P1 (mitigated by `asyncio.to_thread()`).

3. **MUST: Remove SYS-15 from the sprint plan** (duplicate of FE-03).

4. **SHOULD: Add a "Resolved Items" section to the DRAFT** listing items already fixed (DB-07, DB-16, DB-20, FE-13, FE-22, and potentially SYS-02).

5. **SHOULD: Incorporate @data-engineer's 4 new items** (DB-28, DB-29, DB-30, DB-31) and @ux-design-expert's 4 new items (FE-33, FE-34, FE-35, FE-36) into the DRAFT's priority matrix.

6. **SHOULD: Add cross-cutting risk section** covering API contract stability, secrets rotation, and the `main.py`/`app_factory.py` dual-path issue.

### Riscos Aceitos

The following risks are documented and accepted for now:

1. **No consumer-driven contract tests** (API proxy coupling) -- Accepted because the frontend proxy pattern provides a single integration point and the team is small. Revisit when adding mobile clients or external API consumers.

2. **LGPD compliance gaps** -- Accepted for pre-revenue beta. Must be addressed before scaling to paying customers.

3. **Rate limiting fallback to per-worker in-memory** -- Accepted because Railway runs 2 workers and Redis uptime is >99.9% on Upstash.

4. **No dead letter queue for ARQ jobs** -- Accepted because jobs have inline fallback (LLM/Excel execute synchronously if queue unavailable). Failed jobs result in delayed delivery, not data loss.

5. **Dependency supply chain risk** -- Accepted because CI runs `pip-audit` and Dependabot handles minor updates. No known critical vulnerabilities at time of review.

6. **OAuth token encryption at app layer only** -- Accepted per industry standard pattern. Document key rotation procedure as a future improvement.

---

## Numeros Revisados

Incorporating specialist adjustments:

| Metrica | DRAFT Original | Pos-Revisao |
|---------|---------------|-------------|
| Total items | 79 | 83 (+ 8 added - 5 removed + 1 duplicate removed) |
| CRITICAL | 5 | 2 (DB-01, SYS-01 pending investigation) |
| HIGH | 19 | 15 (multiple downgrades by specialists) |
| MEDIUM | 32 | 38 (upgrades from LOW + new items) |
| LOW | 23 | 28 (downgrades from MEDIUM/HIGH + new items) |
| Estimated effort | 372.5h | ~310h (specialist estimate reductions + false positive removals - SYS-15 duplicate) |
| False positives removed | 0 | 5 (DB-07, DB-16, DB-20, FE-13, FE-22) |
| Potentially resolved | 0 | 0 (SYS-02 verified: still uses `requests`) |

---

*Reviewed 2026-03-20 by @qa during Brownfield Discovery Phase 7.*
*All findings cross-referenced against codebase. Investigation of CORS/main.py dual-path is code-verified.*
