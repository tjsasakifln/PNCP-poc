# STORY-202: Monolith Decomposition and Quality

**Status:** Backlog
**Sprint:** 3 (Weeks 4-6)
**Priority:** P2 -- Decomposition + Quality
**Effort:** 93-131h
**Epic:** EPIC-TD (Technical Debt Resolution)
**Dependencies:** STORY-201 (ORM consolidation must be complete; shared app shell must exist; CI pipeline must be green)

---

## Context

With Sprint 2 complete, SmartLic/BidIQ has a single ORM, unified API patterns, a shared app shell, and a green CI pipeline. Sprint 3 tackles the two largest refactoring efforts:

1. **Backend monolith:** `main.py` is 1,959 lines containing 20+ endpoints, business logic, helper functions, and billing handlers. It cannot be tested in isolation and is difficult to maintain.

2. **Frontend monolith:** `buscar/page.tsx` is ~1,100 lines with 30+ useState hooks and all business logic inline. It is the single most complex component in the application and prevents iterative UX improvement.

3. **Horizontal scaling blockers:** In-memory SSE state (`_active_trackers` dict) breaks with multiple instances. Excel files stored in temporary filesystem are not shared between instances and are lost on restart.

4. **Test coverage:** Frontend coverage is 49.46% vs the 60% target. The CI coverage gate fails.

5. **Accessibility gaps:** Several WCAG violations identified in the assessment need resolution.

This is the longest sprint (3 weeks) due to the scope of decomposition work. Items are ordered so that decomposition happens first (enabling subsequent changes), followed by infrastructure, testing, and accessibility work that can be parallelized.

---

## Acceptance Criteria

### Backend Decomposition

- [ ] **SYS-C02 + SYS-H04**: Decompose `main.py` into router modules
  - Extract endpoints into: `backend/routes/search.py`, `backend/routes/auth.py`, `backend/routes/billing.py`, `backend/routes/sessions.py`, `backend/routes/admin.py` (or similar structure)
  - Extract authorization logic (`_check_user_roles`, `_is_admin`, `_has_master_access`) into `backend/authorization.py`
  - Extract other helper functions into appropriate modules
  - `main.py` should be reduced to app initialization, middleware setup, and router imports (~100-200 lines)
  - No file in `backend/` should exceed 500 lines
  - Files: `backend/main.py`, `backend/routes/search.py` (new), `backend/routes/auth.py` (new), `backend/routes/billing.py` (new), `backend/routes/sessions.py` (new), `backend/routes/admin.py` (new or extend existing), `backend/authorization.py` (new)
  - Validation: All 20+ endpoints still respond identically (same status codes, same response bodies). `pytest` passes with no new failures. Import graph is clean (no circular imports).
  - Effort: 12-16h

### Frontend Decomposition

- [ ] **FE-C01**: Decompose `buscar/page.tsx` into components and hooks
  - Extract: `SearchForm` component, `FilterPanel` component, `SearchResults` component, `useSearch` hook, `useSearchFilters` hook
  - Page component should orchestrate child components (~100-200 lines)
  - Each extracted component should be independently testable
  - No file should exceed 300 lines
  - Preserve all 30+ state variables (refactor into custom hooks)
  - Files: `frontend/app/(protected)/buscar/page.tsx` (refactored), `frontend/app/components/SearchForm.tsx` (new), `frontend/app/components/FilterPanel.tsx` (new), `frontend/app/components/SearchResults.tsx` (new), `frontend/hooks/useSearch.ts` (new), `frontend/hooks/useSearchFilters.ts` (new)
  - Validation: All search functionality works identically (UF selection, date range, keyword search, results display, download). Playwright E2E tests pass. No visual regressions.
  - Effort: 16-24h

### Horizontal Scaling Infrastructure

- [ ] **SYS-C01**: Migrate SSE state from in-memory dict to Redis pub/sub
  - Replace `_active_trackers` dict in `progress.py:98` with Redis-backed state
  - Use Redis pub/sub for SSE event distribution across instances
  - Ensure state survives instance restarts
  - Add graceful fallback to in-memory if Redis is unavailable (with logged warning)
  - Files: `backend/progress.py`, `backend/redis_client.py` (new or extend existing)
  - Validation: Start search on instance A, track progress from instance B. State persists across backend restart. Fallback to in-memory works when Redis is down.
  - Effort: 16-24h

- [ ] **CROSS-C02 + SYS-H02 + FE-H06**: Migrate Excel storage from tmpdir to object storage
  - Replace `tmpdir()` file storage with Supabase Storage or S3-compatible storage
  - Generate signed URLs for Excel downloads (time-limited, e.g., 60 minutes)
  - Remove `setTimeout` cleanup from frontend proxy
  - Files shared between instances and persistent across restarts
  - Files: `frontend/app/api/buscar/route.ts` (lines 180-204), `frontend/app/api/download/route.ts`, `backend/excel.py` (if upload logic added to backend)
  - Validation: Generate Excel, restart server, download still works. Download URL expires after configured TTL. No temp files left on filesystem.
  - Effort: 8-12h

### Observability

- [ ] **SYS-M01**: Add correlation IDs (request ID tracking)
  - Add middleware that generates a unique request ID for each incoming request
  - Pass request ID in all log entries
  - Forward request ID from frontend proxy to backend in `X-Request-ID` header
  - Files: `backend/middleware.py` (new or extend), `frontend/app/api/` (all proxy routes)
  - Validation: Every log line includes a request ID. Same request ID appears in frontend proxy logs and backend logs for the same user action.
  - Effort: 3-4h

### Test Coverage Improvement

- [ ] **SYS-M07 + FE-L07**: Improve frontend test coverage to 60%+
  - Add tests for: `LoadingProgress`, `RegionSelector`, `SavedSearchesDropdown`, `AnalyticsProvider`
  - Add tests for newly extracted components from FE-C01 decomposition
  - Target: 60% overall coverage (branches, functions, lines, statements)
  - Files: `frontend/__tests__/` (new test files for each component)
  - Validation: `npm run test:coverage` exits successfully (threshold enforcement at 60%). Coverage report shows >= 60% on all metrics.
  - Effort: 12-16h

### Database Improvements

- [ ] **DB-M04**: Add `sync_profile_plan_type` database trigger
  - Create trigger on `user_subscriptions` table that automatically syncs `profiles.plan_type` whenever subscription state changes
  - Eliminates drift between `user_subscriptions.plan_id` and `profiles.plan_type` permanently
  - Files: `supabase/migrations/017_sync_plan_type_trigger.sql` (new)
  - Validation: Update a `user_subscriptions` row -- `profiles.plan_type` automatically updates to match. No manual sync needed in application code.
  - Effort: 2-3h

- [ ] **DB-M01**: Standardize foreign key references (all reference `profiles(id)` instead of some referencing `auth.users(id)`)
  - Update `monthly_quota`, `user_oauth_tokens`, `google_sheets_exports` to reference `profiles(id)` consistently
  - Files: `supabase/migrations/018_standardize_fk_references.sql` (new)
  - Validation: All user-related FKs point to `profiles(id)`. No FK references `auth.users(id)` directly (except `profiles.id` itself).
  - Effort: 3-4h

- [ ] **DB-M06 + DB-M07**: Create RPC functions to eliminate N+1 and full-table-scan queries
  - DB-M06: Create `get_conversations_with_unread_count()` RPC function to replace N+1 query in conversation list
  - DB-M07: Create `get_analytics_summary()` RPC function with date range and pagination to replace fetching ALL sessions
  - Files: `supabase/migrations/019_rpc_performance_functions.sql` (new), `backend/routes/messages.py` (lines 112-122), `backend/routes/analytics.py` (lines 78-83)
  - Validation: Conversation list loads in single query. Analytics endpoint accepts date range parameters. No Python-side aggregation of large datasets.
  - Effort: 4-6h

### Accessibility (WCAG Sprint)

- [ ] **FE-NEW-03**: Add `aria-describedby` linking search term input to validation error messages
  - Files: `frontend/app/(protected)/buscar/page.tsx` or extracted `SearchForm.tsx` (term validation section)
  - Validation: Screen reader announces validation errors when they appear. Error element has unique `id` matching the input's `aria-describedby` value.
  - Effort: 1h

- [ ] **FE-NEW-06**: Add `prefers-reduced-motion` support to framer-motion animations
  - Check `prefers-reduced-motion` media query and disable/reduce framer-motion JS animations accordingly
  - Apply to all 9 files that import framer-motion
  - Files: All files importing `framer-motion` (9 files -- check with `grep -r "framer-motion" frontend/`)
  - Validation: Enable "Reduce motion" in OS accessibility settings. All framer-motion animations are disabled or reduced to simple opacity transitions.
  - Effort: 2-3h

- [ ] **FE-NEW-07**: Implement roving tabindex for UF selection grid
  - Replace 27 individual tab stops with single tab stop + arrow key navigation within the group
  - Follow WAI-ARIA grid or toolbar pattern
  - Files: `frontend/app/components/RegionSelector.tsx`
  - Validation: Tab into UF grid = 1 Tab stop. Arrow keys move between states. Enter/Space toggles selection. Tab out of grid = 1 Tab stop. Total Tab stops through grid: 2 (in + out), not 27.
  - Effort: 3-4h

- [ ] **FE-L01**: Fix generic SVG `aria-label="Icone"` across all pages
  - For decorative SVGs: use `aria-hidden="true"` only (remove `role="img"` and `aria-label`)
  - For meaningful SVGs: use descriptive `aria-label` (e.g., "Search icon", "Download icon")
  - Remove all instances of contradictory `role="img" aria-label="Icone"` + `aria-hidden="true"`
  - Files: Multiple pages (search codebase for `aria-label="Icone"`)
  - Validation: No SVG has `aria-label="Icone"`. No SVG has both `role="img"` and `aria-hidden="true"`. Screen reader does not announce "Icone" for any icon.
  - Effort: 3-4h

### Testing Infrastructure

- [ ] **TEST-01 + TEST-02**: Document backend and frontend testing strategies
  - Backend: Document mocking strategy for PNCP API, test data fixture templates, unit vs integration test structure
  - Frontend: Document unit vs integration vs E2E coverage targets, MSW setup guide, accessibility test tooling (jest-axe)
  - Files: `docs/testing/backend-testing-strategy.md` (new), `docs/testing/frontend-testing-strategy.md` (new)
  - Validation: New developer can read the docs and understand how to write tests for any component/module.
  - Effort: 2-4h

- [ ] **TEST-04 + TEST-05**: Create Excel validation and LLM fallback test suites
  - TEST-04: Test Excel file structure (column count, headers, data types, currency formatting, styling, 500+ rows)
  - TEST-05: Test OpenAI API timeout, invalid JSON response, token limit exceeded, rate limiting (429), fallback behavior
  - Files: `backend/tests/test_excel_validation.py` (new), `backend/tests/test_llm_fallback.py` (new)
  - Validation: All new tests pass. Tests cover documented edge cases. `pytest --cov` shows improved coverage for `excel.py` and `llm.py`.
  - Effort: 5-7h

---

## Technical Notes

### main.py Decomposition Strategy

Recommended module structure:

```python
# backend/main.py (~150 lines after decomposition)
from fastapi import FastAPI
from routes import search, auth, billing, sessions, admin, health, analytics, messages

app = FastAPI(title="SmartLic API", version="0.3.0")

# Middleware
app.add_middleware(...)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(search.router, tags=["search"])
app.include_router(billing.router, tags=["billing"])
app.include_router(sessions.router, tags=["sessions"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
```

Authorization logic (`_check_user_roles`, `_is_admin`, `_has_master_access`) should be extracted to `backend/authorization.py` as dependency-injectable functions using FastAPI's `Depends()`.

### buscar/page.tsx Decomposition Strategy

```
buscar/page.tsx (orchestrator, ~150 lines)
  ├── components/SearchForm.tsx (UF selection, date range, keywords)
  ├── components/FilterPanel.tsx (advanced filters: esfera, municipio, value range)
  ├── components/SearchResults.tsx (results table, summary card, download)
  ├── hooks/useSearch.ts (search execution, SSE progress, results state)
  └── hooks/useSearchFilters.ts (filter state, validation, saved searches)
```

### Redis SSE Architecture

```
Instance A (receives search request)
  → Writes search state to Redis Hash: `search:{search_id}`
  → Publishes progress events to Redis Channel: `progress:{search_id}`

Instance B (serves SSE connection)
  → Subscribes to Redis Channel: `progress:{search_id}`
  → Reads current state from Redis Hash: `search:{search_id}`
  → Streams events to client via SSE
```

Fallback: If Redis is unavailable, log warning and use in-memory dict (current behavior). Document that horizontal scaling requires Redis.

### Object Storage for Excel

Options (in preference order):
1. **Supabase Storage:** Already in the stack. Use a private bucket with signed URLs.
2. **S3-compatible:** If Supabase Storage is insufficient.

Flow: Backend generates Excel -> uploads to storage -> returns file key in JSON response -> frontend download route generates signed URL -> redirects user to signed URL.

---

## Testing Requirements

- All existing tests must pass (0 failures -- established in Sprint 2)
- All 20+ backend endpoints must be tested before AND after decomposition (regression suite)
- Playwright E2E tests must pass before AND after frontend decomposition
- New components from decomposition must have unit tests
- Frontend coverage must reach 60%+ (`npm run test:coverage` must pass)
- `npx tsc --noEmit --pretty` must pass
- Redis failover behavior must be tested (kill Redis, verify fallback)
- Excel download must be tested across server restarts

---

## Rollback Plan

- **main.py decomposition:** Git revert to pre-decomposition commit. Router modules can be individually reverted.
- **buscar/page.tsx decomposition:** Git revert. Keep original monolithic file in git history for reference.
- **Redis migration:** Fallback to in-memory is built into the design. Disable Redis config to revert.
- **Object storage for Excel:** Revert to tmpdir storage by restoring old route handlers.
- **Database migrations:** Each migration can be rolled back with inverse SQL.

---

## Definition of Done

- [ ] All acceptance criteria checked
- [ ] Tests pass (pytest + npm test) with 0 failures
- [ ] Frontend test coverage >= 60% (`npm run test:coverage` passes)
- [ ] TypeScript check clean (`npx tsc --noEmit`)
- [ ] No new lint errors
- [ ] No file in backend/ exceeds 500 lines
- [ ] No file in frontend/ exceeds 300 lines (for page components)
- [ ] main.py reduced to ~150 lines (app setup + router imports)
- [ ] buscar/page.tsx reduced to ~150 lines (orchestrator)
- [ ] PR reviewed and approved
- [ ] Deployed to staging
- [ ] Redis SSE verified with 2 instances
- [ ] Excel download verified across server restart

---

## File List

**New files:**
- `backend/routes/search.py`
- `backend/routes/auth.py`
- `backend/routes/billing.py`
- `backend/routes/sessions.py`
- `backend/authorization.py`
- `backend/redis_client.py` (or extend existing)
- `frontend/app/components/SearchForm.tsx`
- `frontend/app/components/FilterPanel.tsx`
- `frontend/app/components/SearchResults.tsx`
- `frontend/hooks/useSearch.ts`
- `frontend/hooks/useSearchFilters.ts`
- `frontend/__tests__/LoadingProgress.test.tsx`
- `frontend/__tests__/RegionSelector.test.tsx`
- `frontend/__tests__/SavedSearchesDropdown.test.tsx`
- `frontend/__tests__/AnalyticsProvider.test.tsx`
- `frontend/__tests__/SearchForm.test.tsx`
- `frontend/__tests__/FilterPanel.test.tsx`
- `frontend/__tests__/SearchResults.test.tsx`
- `backend/tests/test_excel_validation.py`
- `backend/tests/test_llm_fallback.py`
- `docs/testing/backend-testing-strategy.md`
- `docs/testing/frontend-testing-strategy.md`
- `supabase/migrations/017_sync_plan_type_trigger.sql`
- `supabase/migrations/018_standardize_fk_references.sql`
- `supabase/migrations/019_rpc_performance_functions.sql`

**Modified files:**
- `backend/main.py` (major: decompose into routers)
- `backend/progress.py` (Redis migration)
- `frontend/app/(protected)/buscar/page.tsx` (major: decompose into components)
- `frontend/app/api/buscar/route.ts` (object storage)
- `frontend/app/api/download/route.ts` (signed URL downloads)
- `frontend/app/components/RegionSelector.tsx` (roving tabindex)
- `backend/routes/messages.py` (RPC call)
- `backend/routes/analytics.py` (RPC call with pagination)
- Multiple files with `aria-label="Icone"` (fix SVG labels)
- 9 files importing framer-motion (prefers-reduced-motion)
