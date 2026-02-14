# STORY-234: Migrate Frontend to Non-Deprecated API Routes

**Status:** Done
**Priority:** P2 — Polish
**Sprint:** Sprint 3 (pre-GTM)
**Estimated Effort:** XS (30min)
**Source:** GTM-READINESS-VALIDATION-REPORT.md (MIN-3)
**Squad:** team-bidiq-story234 (architect, dev-alpha, dev-beta, qa)

---

## Context

Railway backend logs show deprecation warnings:
```
DEPRECATED route accessed: GET /api/messages/unread-count — migrate to /v1/api/messages/unread-count before 2026-06-01
```

The frontend is still calling deprecated routes. While they still work, they should be migrated to the `/v1/` versions before the deprecation deadline.

## Acceptance Criteria

- [x] AC1: Frontend calls `/v1/api/messages/unread-count` instead of `/api/messages/unread-count`
- [x] AC2: All other deprecated route calls (if any) are migrated to their `/v1/` equivalents
- [ ] AC3: No `DEPRECATED route accessed` warnings appear in Railway logs after deployment
- [x] AC4: Verify the `/v1/` endpoints return the same response format as the deprecated versions

## Technical Notes

- Search frontend codebase for any API calls to non-`/v1/` backend routes
- The backend dual-mounts routes (legacy + v1) — only the frontend needs changing
- `/health` endpoint is exempt from deprecation (root utility route) — no migration needed
- Backend `DeprecationMiddleware` exempt paths: `/`, `/health`, `/docs`, `/redoc`, `/openapi.json`
- AC3 requires deployment to verify — will be confirmed post-deploy

## Dependencies

- None

## File List

| File | Action | Description |
|------|--------|-------------|
| `frontend/app/api/buscar/route.ts` | Modified | `/buscar` → `/v1/buscar` |
| `frontend/app/api/buscar-progress/route.ts` | Modified | `/buscar-progress/` → `/v1/buscar-progress/` |
| `frontend/app/api/me/route.ts` | Modified | `/me` → `/v1/me` (GET + DELETE) |
| `frontend/app/api/me/export/route.ts` | Modified | `/me/export` → `/v1/me/export` |
| `frontend/app/api/change-password/route.ts` | Modified | `/change-password` → `/v1/change-password` |
| `frontend/app/api/sessions/route.ts` | Modified | `/sessions` → `/v1/sessions` |
| `frontend/app/api/setores/route.ts` | Modified | `/setores` → `/v1/setores` |
| `frontend/app/api/analytics/route.ts` | Modified | `/analytics/` → `/v1/analytics/` |
| `frontend/app/api/admin/[...path]/route.ts` | Modified | `${backendPath}` → `/v1${backendPath}` |
| `frontend/app/api/messages/unread-count/route.ts` | Modified | `/api/messages/unread-count` → `/v1/api/messages/unread-count` |
| `frontend/app/api/messages/conversations/route.ts` | Modified | `/api/messages/conversations` → `/v1/api/messages/conversations` (GET + POST) |
| `frontend/app/api/messages/conversations/[id]/route.ts` | Modified | `/api/messages/conversations/${id}` → `/v1/api/messages/conversations/${id}` |
| `frontend/app/api/messages/conversations/[id]/reply/route.ts` | Modified | `/api/messages/conversations/${id}/reply` → `/v1/api/messages/conversations/${id}/reply` |
| `frontend/app/api/messages/conversations/[id]/status/route.ts` | Modified | `/api/messages/conversations/${id}/status` → `/v1/api/messages/conversations/${id}/status` |
| `frontend/app/api/health/route.ts` | Skipped | `/health` is exempt from deprecation middleware |
| `frontend/app/components/AuthProvider.tsx` | Modified | `/me` → `/v1/me` (NEXT_PUBLIC_BACKEND_URL call) |
| `frontend/app/planos/page.tsx` | Modified | `/me`, `/plans`, `/checkout` → `/v1/me`, `/v1/plans`, `/v1/checkout` |
| `frontend/app/components/UpgradeModal.tsx` | Modified | `/plans` → `/v1/plans` |
| `frontend/app/dashboard/page.tsx` | Modified | `/analytics/` → `/v1/analytics/` |
| `frontend/__tests__/api/analytics.test.ts` | Modified | Updated URL assertions to match `/v1/` prefix |
| `frontend/__tests__/api/buscar.test.ts` | Modified | Updated URL assertion to match `/v1/` prefix |
