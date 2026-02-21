# STORY-224 — Fix 52 Skipped Tests (Stale Mocks from STORY-216 Refactoring)

**Status:** READY
**Priority:** Medium-Low
**Sprint:** Backlog
**Estimate:** 6-8h
**Squad:** @qa + @dev

---

## Context

During STORY-216, the search endpoint was extracted from `main.py` to `routes/search.py` and the `SearchPipeline` class was introduced. This broke 52 tests whose mocks target old code locations (`main.rate_limiter`, `main.gerar_resumo`, `main.aplicar_todos_filtros`, etc.). Rather than fixing them inline, they were marked `@pytest.mark.skip(reason="Stale mock — STORY-224")` to keep CI green.

These tests represent **real coverage that was lost** during the refactoring. Each test needs its mocks updated to target the new module locations.

**Current state:** 52 skipped, 4307 passed, 0 failed (after STORY-258)

---

## Skipped Tests by File

### 1. `test_main.py` — 21 skipped (highest priority)

**Root cause:** `buscar` moved from `main.py` to `routes/search.py`. Mocks target `main.rate_limiter`, `main.gerar_resumo`, `main.aplicar_todos_filtros` which no longer exist in `main`.

| Count | Reason | Fix Pattern |
|-------|--------|-------------|
| 14 | Mocks `main.rate_limiter` which no longer exists | Patch `routes.search.rate_limiter` or remove rate_limiter mock (now middleware) |
| 3 | `/debug/pncp-test` now requires admin auth | Add `app.dependency_overrides[require_admin]` |
| 2 | Mocks `main.gerar_resumo` which moved | Patch `llm.gerar_resumo` or `search_pipeline.gerar_resumo` |
| 1 | Mocks `main.aplicar_todos_filtros` which moved | Patch at new location in `search_pipeline` |
| 1 | Health check Redis mock doesn't override async pool check | Update Redis mock to match `redis_pool.get_redis_pool()` pattern |

### 2. `test_api_buscar.py` — 11 skipped

**Root cause:** Mix of rate_limiter mock issues and SearchPipeline refactoring.

| Count | Reason | Fix Pattern |
|-------|--------|-------------|
| 5 | `rate_limiter` mock causes SearchPipeline async init to hang | Mock `search_pipeline.SearchPipeline` or patch rate limiter at correct location |
| 2 | `increment_monthly_quota` replaced by `check_and_increment_quota_atomic` | Update mock target |
| 1 | `aplicar_todos_filtros` and `create_excel` moved to SearchPipeline | Patch at `search_pipeline.SearchPipeline` methods |
| 1 | Invalid sector now returns 400 not 500 | Update expected status code |
| 1 | Missing `rate_limiter` mock causes async init failure | Add rate limiter mock |
| 1 | All-stopwords behavior changed (returns 400) | Update expected behavior |

### 3. `test_gtm_critical_scenarios.py` — 8 skipped

**Root cause:** Multiple issues — moved functions, missing AsyncMock import, auth mock format.

| Count | Reason | Fix Pattern |
|-------|--------|-------------|
| 4 | `gerar_resumo`/`aplicar_todos_filtros` moved out of `routes.search` | Patch at new location |
| 2 | Missing `AsyncMock` import + rate_limiter mock hangs | Add import + fix mock |
| 2 | Auth mock doesn't match current middleware (returns 500 not 401) | Use `app.dependency_overrides[require_auth]` pattern |

### 4. `test_plan_capabilities.py` — 5 skipped

**Root cause:** `check_quota` refactored to use RPC-based subscription lookup.

| Count | Reason | Fix Pattern |
|-------|--------|-------------|
| 3 | `check_quota` now uses RPC-based subscription lookup with different mock chain | Update Supabase mock to match `.rpc("check_subscription", ...)` pattern |
| 1 | `datetime.utcnow()` replaced by `datetime.now(timezone.utc)` | Update datetime mock |
| 1 | Error message format changed (includes reset date + upgrade text) | Update assertion string |

### 5. `test_routes_auth_oauth.py` — 4 skipped

**Root cause:** STORY-210 AC13 changed OAuth state from base64 to cryptographic nonce.

| Count | Reason | Fix Pattern |
|-------|--------|-------------|
| 4 | OAuth state now uses `secrets.token_urlsafe()` nonce, not `base64.b64encode()` | Mock `secrets.token_urlsafe` instead of base64; update state validation assertions |

### 6. `test_analytics.py` — 1 skipped

**Root cause:** Analytics endpoint switched from direct table queries to RPC function.

| Fix | Patch `supabase_client.get_supabase` to mock `.rpc("get_analytics_summary", ...)` return value |

### 7. `test_endpoints_story165.py` — 1 skipped

**Root cause:** `/me` endpoint subscription lookup chain changed.

| Fix | Update mock chain for subscription status query in `/me` handler |

### 8. `test_search_session_lifecycle.py` — 1 skipped (OUT OF SCOPE)

**Reason:** `test_session_cleanup_on_sigkill` — Gunicorn SIGKILL cannot be simulated in unit tests. Already covered by T9 (SIGTERM handler). This skip is intentional and correct.

---

## Acceptance Criteria

- [ ] **AC1:** All 21 `test_main.py` skipped tests pass or are deleted with justification
- [ ] **AC2:** All 11 `test_api_buscar.py` skipped tests pass or are deleted with justification
- [ ] **AC3:** All 8 `test_gtm_critical_scenarios.py` skipped tests pass or are deleted with justification
- [ ] **AC4:** All 5 `test_plan_capabilities.py` skipped tests pass or are deleted with justification
- [ ] **AC5:** All 4 `test_routes_auth_oauth.py` skipped tests pass or are deleted with justification
- [ ] **AC6:** `test_analytics.py` + `test_endpoints_story165.py` skipped tests pass (2 total)
- [ ] **AC7:** `test_search_session_lifecycle.py::test_session_cleanup_on_sigkill` remains skipped (intentional)
- [ ] **AC8:** Zero regressions — no previously-passing tests break
- [ ] **AC9:** Final baseline: 0 failed, ≤1 skipped (only SIGKILL), 4350+ passed
- [ ] **AC10:** No production code changes — test-only modifications

---

## Implementation Strategy

### Recommended order (dependency-aware)

1. **`test_plan_capabilities.py`** (5 tests) — fixes quota mock patterns reused elsewhere
2. **`test_api_buscar.py`** (11 tests) — depends on understanding SearchPipeline mock pattern
3. **`test_main.py`** (21 tests) — largest batch, similar patterns
4. **`test_gtm_critical_scenarios.py`** (8 tests) — mix of issues
5. **`test_routes_auth_oauth.py`** (4 tests) — isolated, OAuth-specific
6. **`test_analytics.py` + `test_endpoints_story165.py`** (2 tests) — quick wins

### Common mock migration patterns

| Old Pattern | New Pattern |
|-------------|-------------|
| `@patch("main.rate_limiter")` | Remove or `@patch("routes.search.require_rate_limit")` |
| `@patch("main.gerar_resumo")` | `@patch("llm.gerar_resumo")` |
| `@patch("main.aplicar_todos_filtros")` | `@patch("search_pipeline.SearchPipeline._apply_filters")` |
| `@patch("main.create_excel")` | `@patch("excel.create_excel")` |
| `@patch("quota.increment_monthly_quota")` | `@patch("quota.check_and_increment_quota_atomic")` |
| `mock_check_quota` standalone | Must also mock `check_and_increment_quota_atomic` |

### Decision: fix vs delete

**Fix** if the test covers a unique scenario not tested elsewhere.
**Delete** if the test is redundant with newer tests (e.g., `test_search_pipeline.py`, `test_search_error_codes.py`).

For each deleted test, add a comment referencing the replacement test.

---

## Files to Modify

| File | Skipped | Action |
|------|---------|--------|
| `tests/test_main.py` | 21 | Fix mocks or delete redundant tests |
| `tests/test_api_buscar.py` | 11 | Fix mocks or delete redundant tests |
| `tests/test_gtm_critical_scenarios.py` | 8 | Fix mocks or delete redundant tests |
| `tests/test_plan_capabilities.py` | 5 | Fix RPC-based mock chain |
| `tests/test_routes_auth_oauth.py` | 4 | Fix OAuth nonce mocks |
| `tests/test_analytics.py` | 1 | Fix RPC mock |
| `tests/test_endpoints_story165.py` | 1 | Fix subscription lookup mock |

---

## Out of Scope

- STORY-258 (7 failing tests — separate story)
- Frontend test failures
- New test coverage beyond what was originally skipped
- Production code changes
