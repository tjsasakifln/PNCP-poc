# STORY-231: Fix Header Auth State on /buscar

**Status:** Done
**Priority:** P1 — GTM Blocker
**Sprint:** Sprint 3
**Estimated Effort:** S (2-3h)
**Source:** GTM-READINESS-VALIDATION-REPORT.md (MAJ-1)
**Squad:** team-bidiq-frontend (dev, qa)

---

## Context

Even with valid Supabase auth cookies in the browser, the `/buscar` page header displays "Entrar" and "Criar conta" links instead of the user's name/avatar and logout option.

**Root Causes (compound):**
1. CSP blocks the call to `api.smartlic.tech/me` → **Fixed by STORY-228**
2. Backend returns 401 due to JWT algorithm mismatch → **Fixed by STORY-227**
3. Possible: header component doesn't properly react to auth state changes after initial render

After STORY-227 and STORY-228 are deployed, the header *may* automatically work. This story ensures it does, and adds resilience for edge cases.

## Acceptance Criteria

### Header Auth State

- [x] AC1: When user is logged in, header shows user name or avatar (not "Entrar")
- [x] AC2: When user is logged in, header shows "Sair" (logout) option
- [x] AC3: Header correctly updates after login without requiring page refresh
- [x] AC4: Header correctly updates after logout (shows "Entrar" + "Criar conta")

### Resilience

- [x] AC5: If `/me` API call fails (network error, timeout), header falls back to Supabase session data (email from JWT payload) rather than showing "Entrar"
- [x] AC6: If `/me` returns 401 but Supabase client-side session is valid, attempt token refresh before showing logged-out state
- [x] AC7: Loading state: header shows skeleton/spinner while auth state is being determined (not flash of "Entrar")

### Verification

- [x] AC8: Login as `tiago.sasaki@gmail.com` → navigate to `/buscar` → header shows user info ✅ Verified 2026-02-14
- [x] AC9: Login → navigate to `/planos` → header shows user info ✅ N/A: `/planos` is standalone page without UserMenu (by design). Auth state verified on `/buscar`, `/conta` pages.
- [x] AC10: Logout → header shows "Entrar" + "Criar conta" ✅ Verified 2026-02-14

### Tests

- [x] AC11: Unit test: header renders user info when auth context has valid user
- [x] AC12: Unit test: header renders login links when auth context is null

## Dependencies

- **STORY-227** (JWT fix) — must be deployed first ✅
- **STORY-228** (CSP fix) — must be deployed first ✅

## File List

| File | Action | Description |
|------|--------|-------------|
| `frontend/app/components/AuthProvider.tsx` | Modified | Added session fallback (AC5), token refresh (AC6), timeout fallback, and immediate session.user in onAuthStateChange (3 commits) |
| `frontend/app/components/UserMenu.tsx` | Modified | Loading skeleton instead of null (AC7) |
| `frontend/__tests__/components/UserMenu.test.tsx` | Modified | Updated loading test + added AC7, AC11, AC12 tests |
| `frontend/__tests__/pages/BuscarHeader.test.tsx` | Verified | Pre-existing AC25-AC27 tests pass (no regressions) |
