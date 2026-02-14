# STORY-233: Fix Redirect Reason Messaging

**Status:** Done
**Priority:** P2 — Polish
**Sprint:** Sprint 3 (pre-GTM)
**Estimated Effort:** XS (30min)
**Source:** GTM-READINESS-VALIDATION-REPORT.md (MIN-2)
**Squad:** team-bidiq-frontend (dev)

---

## Context

When an anonymous user (never logged in) tries to access `/buscar` directly, they are redirected to `/login?redirect=/buscar&reason=session_expired`. The `reason=session_expired` is misleading — there was never a session. It should say `login_required` or similar.

## Acceptance Criteria

- [x] AC1: When an unauthenticated user (no prior session) accesses a protected route, redirect reason is `login_required` (not `session_expired`)
- [x] AC2: `session_expired` reason is only used when there was an actual session that expired (e.g., JWT expired, refresh token failed)
- [x] AC3: Login page displays appropriate message per reason:
  - `login_required` → "Faça login para acessar esta página"
  - `session_expired` → "Sua sessão expirou. Faça login novamente."
- [x] AC4: No other redirect reasons are affected by this change

## Dependencies

- None

## File List

| File | Action | Description |
|------|--------|-------------|
| `frontend/middleware.ts` | Modified | Detect auth cookies to distinguish login_required vs session_expired |
| `frontend/app/login/page.tsx` | Modified | Added login_required to ERROR_MESSAGES, INFO_REASONS set, reason param handling |
| `frontend/__tests__/middleware-redirect-reason.test.ts` | Created | 7 tests covering middleware redirect reason decision matrix |
| `frontend/__tests__/login-reason-messages.test.tsx` | Created | 6 tests covering login page message display per reason code |
