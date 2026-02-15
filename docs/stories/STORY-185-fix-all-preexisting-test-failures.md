# STORY-185: Fix All Pre-Existing Test Failures + Obrigado Page Polish

**Status:** Ready for Development
**Priority:** P1 (Technical Debt / Quality Gate)
**Type:** Bug Fix + Polish
**Estimated Effort:** Medium (1-2 sessions)

---

## Context

After wiring up Stripe billing (STORY-171 continuation), the test suite has **25 FAILED + 8 ERROR** in the backend and **143 FAILED** (29 suites) in the frontend. All are **pre-existing** — no regressions from recent changes. Additionally, the `/planos/obrigado` thank-you page has text without proper Portuguese accents/cedilha and uses generic Unicode emojis instead of Lucide icons (project standard).

**Current baseline:**
- Backend: 1568 passed, 25 failed, 8 errors (33 issues total)
- Frontend: 921 passed, 143 failed, 8 skipped (29 failing suites)

**Target:** 0 failures in both backend and frontend.

---

## Acceptance Criteria

### AC1: Backend — Auth Tests (6 FAILED + 9 ERROR = 15 issues)

**Files:** `test_auth.py`, `test_auth_cache.py`
**Root Causes:**

1. **Token cache persistence between tests** — `test_auth.py` has no `autouse` fixture to clear `_token_cache` before each test. A successful validation in one test poisons subsequent tests that expect `HTTPException`.
   - Tests affected: `test_raises_401_when_token_invalid`, `test_raises_401_when_user_response_has_no_user`, `test_raises_401_on_supabase_exception`, `test_logs_warning_on_verification_failure`, `test_reraises_http_exception`
   - Fix: Add `@pytest.fixture(autouse=True)` that clears `auth._token_cache` before each test

2. **Wrong mock patch target** — `test_auth_cache.py` patches `'auth.get_supabase'` but `get_supabase` is imported locally inside `get_current_user()` from `supabase_client`, so it's never bound to the `auth` module namespace.
   - Tests affected: All 7 ERROR + 2 FAILED in `test_auth_cache.py`
   - Fix: Change patch target from `'auth.get_supabase'` to `'supabase_client.get_supabase'`

3. **String assertion mismatch** — `test_converts_user_id_to_string` asserts `'user-id'` but actual returns UUID.
   - Fix: Update assertion to match actual user ID format from mock

- [ ] Add `autouse` cache-clearing fixture to `test_auth.py`
- [ ] Fix mock patch targets in `test_auth_cache.py` (`auth.get_supabase` → `supabase_client.get_supabase`)
- [ ] Fix `test_converts_user_id_to_string` assertion
- [ ] All 15 auth tests pass

---

### AC2: Backend — Health & OpenAPI Tests (9 FAILED)

**File:** `test_main.py`
**Root Causes:**

1. **Health endpoint returns 503** — `/health` performs a live `get_supabase()` call. In test environment (no Supabase connection), it returns `status: "degraded"` with HTTP 503 instead of 200.
   - Tests affected: `test_health_status_code`, `test_health_status_healthy`, `test_health_response_time`, `test_health_no_authentication_required`
   - Fix: Add `autouse` fixture that mocks `supabase_client.get_supabase` to return a mock client, OR refactor health endpoint to only check env var presence (not live connectivity)

2. **Duplicate Operation ID warning** — `/webhooks/stripe` is defined twice: once in `main.py` (line ~728) and once in `webhooks/stripe.py` (registered as router). This causes `UserWarning: Duplicate Operation ID stripe_webhook_webhooks_stripe_post` that breaks OpenAPI schema tests.
   - Tests affected: `test_openapi_json_accessible`, `test_openapi_schema_structure`, `test_openapi_info_metadata`, `test_openapi_has_health_endpoint`, `test_openapi_has_root_endpoint`
   - Fix: Remove the older `@app.post("/webhooks/stripe")` definition from `main.py`, keep only the router version

- [ ] Fix health endpoint to not fail on missing Supabase (mock in tests or refactor endpoint)
- [ ] Remove duplicate `/webhooks/stripe` from `main.py` (keep `webhooks/stripe.py` router)
- [ ] All 9 health/OpenAPI tests pass

---

### AC3: Backend — Google Sheets Tests (2 FAILED)

**File:** `test_google_sheets.py`
**Root Causes:**

1. **`test_raises_404_when_spreadsheet_not_found`** — Test expects `HTTPException(404)` but implementation has a HOTFIX that catches 404 and falls back to `create_spreadsheet()` instead of raising.
   - Fix: Update test to verify the fallback-to-create behavior (since HOTFIX is intentional business logic)

2. **`test_handles_formatting_errors_gracefully`** — Test expects `_apply_formatting()` to catch `HttpError` gracefully, but the method has no try/except — errors propagate uncaught.
   - Fix: Add try/except to `_apply_formatting()` in `google_sheets.py` to log and swallow formatting errors (formatting is non-critical)

- [ ] Update `test_raises_404` to test fallback-to-create behavior
- [ ] Add error handling to `_apply_formatting()` in `google_sheets.py`
- [ ] Both Google Sheets tests pass

---

### AC4: Backend — GTM Critical Scenarios (1 ERROR + 3 FAILED = 4 issues)

**File:** `test_gtm_critical_scenarios.py`
**Root Causes:**

1. **`test_download_1000_plus_bids`** — ERROR in teardown + FAILED assertion. Missing mocks for `check_and_increment_quota_atomic` (per MEMORY.md: tests mocking `/buscar` MUST also mock quota check).
   - Fix: Add missing quota mock, verify response JSON structure matches endpoint

2. **`test_expired_session_returns_401`** — Patches `auth.verify_session_token` but that attribute doesn't exist in the `auth` module (same pattern as AC1).
   - Fix: Change patch target to correct module path

3. **`test_concurrent_searches_same_user_race_condition`** — Expects both concurrent requests to succeed (200) but quota logic blocks second request.
   - Fix: Allow assertion to accept one 403 for the second request, or fix quota mock to simulate atomic behavior

4. **`test_concurrent_quota_check_race_condition`** — Similar quota mock issue.
   - Fix: Align mock behavior with actual quota implementation

- [ ] Fix all 4 GTM critical scenario tests
- [ ] Add missing quota mocks where needed

---

### AC5: Backend — Remaining Tests (3 FAILED)

**Files:** `test_html_error_response.py`, `test_llm_fallback.py`

1. **`test_refresh_token_returns_none_on_html_error`** — Mock's `json=lambda: None` returns `None` instead of raising `json.JSONDecodeError`. Code tries to subscript `None` and gets 500 instead of 401.
   - Fix: Change mock to `json=side_effect_that_raises_JSONDecodeError`, then ensure `oauth.py` catches `JSONDecodeError` and returns `None`

2. **`test_urgency_alert_for_deadline_within_7_days`** — Test asserts `"menos de 7 dias"` in alert, but implementation generates `"encerra em 5 dia(s)"`.
   - Fix: Update implementation to include "menos de 7 dias" phrase, OR update test to match actual output format

- [ ] Fix HTML error response mock to raise JSONDecodeError
- [ ] Fix LLM urgency alert string mismatch
- [ ] Both tests pass

---

### AC6: Frontend — Fix All 143 Failing Tests (29 suites)

**Failing test suites by category:**

| Category | Suites | Tests | Common Root Cause |
|----------|--------|-------|-------------------|
| **Components** | `AuthProvider`, `LoadingProgress`, `RegionSelector`, `SavedSearchesDropdown`, `EmptyState`, `ThemeToggle`, `AnalyticsProvider` | ~45 | Mock setup issues, module resolution, Supabase client mocks |
| **Subscriptions** | `PlanCard`, `AnnualBenefits`, `TrustSignals` | ~12 | Component structure changes not reflected in tests |
| **Pages** | `page.test.tsx` (buscar), `AdminPage`, `HistoricoPage`, `LoginPage`, `PlanosPage` | ~35 | API mock patterns, AuthProvider mock, response format changes |
| **API Routes** | `api/buscar.test.ts` | ~4 | Retry logic mock, response format changes |
| **Hooks** | `useFeatureFlags` | ~5 | Mock setup, Supabase client |
| **Free User Flows** | `free-user-*.test.tsx` (5 files) | ~25 | AuthProvider/quota mock issues, navigation mocks |
| **Landing** | `BeforeAfter`, `HeroSection`, `OpportunityCost` | ~7 | Component structure/class changes |
| **Billing** | `PlanBadge`, `UpgradeModal`, `GoogleSheetsExportButton` | ~10 | Import changes, mock mismatches |
| **Auth** | `oauth-google-callback` | ~3 | Supabase OAuth mock |

**Approach:**
1. Fix shared mock infrastructure first (AuthProvider mock, Supabase client mock, fetch mock)
2. Fix component tests by category (bulk fixes for common patterns)
3. Fix page-level integration tests last

- [ ] Fix shared test mocks/infrastructure
- [ ] Fix all 29 failing test suites (143 tests)
- [ ] `npm test` passes with 0 failures

---

### AC7: Obrigado Page — Fix Accents, Cedilha, and Replace Emojis with Lucide Icons

**File:** `frontend/app/planos/obrigado/page.tsx`

**Text issues (missing accents/cedilha):**

| Current (wrong) | Correct |
|-----------------|---------|
| `Consultor Agil` | `Consultor Ágil` |
| `Maquina` | `Máquina` |
| `Voce agora tem 50 buscas/mes e historico de 30 dias.` | `Você agora tem 50 buscas/mês e histórico de 30 dias.` |
| `Voce agora tem 300 buscas/mes, download Excel e historico de 1 ano.` | `Você agora tem 300 buscas/mês, download Excel e histórico de 1 ano.` |
| `Voce agora tem 1.000 buscas/mes, processamento prioritario e historico de 5 anos.` | `Você agora tem 1.000 buscas/mês, processamento prioritário e histórico de 5 anos.` |
| `Seu plano esta ativo. Obrigado pela confianca!` | `Seu plano está ativo. Obrigado pela confiança!` |
| `Comecar a buscar` | `Começar a buscar` |
| `Um recibo sera enviado para` | `Um recibo será enviado para` |

**Emoji → Lucide icon replacements:**

| Plan | Current Emoji | Replace With Lucide |
|------|--------------|---------------------|
| Consultor Ágil | 🚀 (`\u{1F680}`) | `<Rocket />` from lucide-react |
| Máquina | ⚡ (`\u{26A1}`) | `<Zap />` from lucide-react |
| Sala de Guerra | 🏆 (`\u{1F3C6}`) | `<Trophy />` from lucide-react |
| Success checkmark | Raw SVG `<path d="M5 13l4 4L19 7" />` | `<CheckCircle />` from lucide-react |

- [ ] Fix all 8 text strings with proper accents/cedilha
- [ ] Replace 3 plan emojis with Lucide `<Rocket />`, `<Zap />`, `<Trophy />`
- [ ] Replace raw SVG checkmark with Lucide `<CheckCircle />`
- [ ] Visual verification on production

---

## Files to Modify

### Backend (AC1-AC5)
| File | Action |
|------|--------|
| `backend/tests/test_auth.py` | Add autouse cache-clearing fixture |
| `backend/tests/test_auth_cache.py` | Fix mock patch targets |
| `backend/main.py` | Remove duplicate `/webhooks/stripe` endpoint |
| `backend/tests/test_main.py` | Add Supabase mock for health endpoint tests |
| `backend/tests/test_google_sheets.py` | Update test expectations |
| `backend/google_sheets.py` | Add error handling to `_apply_formatting()` |
| `backend/tests/test_gtm_critical_scenarios.py` | Fix mock targets + add quota mocks |
| `backend/tests/test_html_error_response.py` | Fix JSON mock to raise JSONDecodeError |
| `backend/tests/test_llm_fallback.py` | Fix urgency alert assertion |
| `backend/llm.py` | Update urgency alert format (if needed) |

### Frontend (AC6-AC7)
| File | Action |
|------|--------|
| `frontend/app/planos/obrigado/page.tsx` | Fix accents, replace emojis with Lucide |
| `frontend/__tests__/` (29 suites) | Fix mocks and assertions |
| `frontend/jest.setup.js` | May need shared mock updates |

---

## Definition of Done

- [ ] `cd backend && pytest` → **0 failures, 0 errors**
- [ ] `cd frontend && npm test -- --ci` → **0 failures**
- [ ] `cd frontend && npx tsc --noEmit` → **clean**
- [ ] Obrigado page displays correct Portuguese (accents, cedilha)
- [ ] Obrigado page uses Lucide icons instead of emojis
- [ ] All changes committed and pushed
- [ ] No regressions in production

---

## Technical Notes

### Common Mock Patterns to Fix (Backend)
```python
# WRONG: Patching attribute that doesn't exist in module namespace
@patch("auth.get_supabase")  # ❌ get_supabase imported locally, not bound to auth

# CORRECT: Patch at the source module
@patch("supabase_client.get_supabase")  # ✅ Where get_supabase is defined
```

### Auth Cache Clearing Fixture
```python
@pytest.fixture(autouse=True)
def clear_auth_cache():
    """Clear auth token cache before each test."""
    import auth
    auth._token_cache.clear()
    yield
    auth._token_cache.clear()
```

### Frontend Shared Mock Pattern
Most frontend tests fail because `AuthProvider` and `supabaseClient` mocks are inconsistent or outdated. Fix the shared mock in `jest.setup.js` or a `__mocks__/` directory first, then individual tests will cascade to green.

---

## Risks

- **High test count (143 frontend):** Many share root causes — fixing shared mocks should cascade fixes
- **Duplicate webhook removal:** Must verify `webhooks/stripe.py` router handles all events before deleting `main.py` version
- **Health endpoint refactor:** Must not break production health checks (Railway uses these)
