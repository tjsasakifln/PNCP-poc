# STORY-230: Fix Footer Navigation Links

**Status:** Done
**Priority:** P1 — GTM Blocker
**Sprint:** Sprint 3
**Estimated Effort:** XS (1h)
**Source:** GTM-READINESS-VALIDATION-REPORT.md (MAJ-4, UX-1)
**Squad:** team-bidiq-frontend (dev)

---

## Context

The footer on `/buscar` (and potentially other pages) has incorrect navigation links:
- "Central de Ajuda" → links to `/mensagens` (requires login) — should link to `/ajuda` (public)
- "Contato" → links to `/mensagens` (requires login) — should have a public fallback

Additionally, the `/ajuda` FAQ page has an "Enviar Mensagem" button that links to `/mensagens`, creating a dead end for unauthenticated users.

## Acceptance Criteria

### Footer Links Fix

- [x] AC1: "Central de Ajuda" footer link points to `/ajuda` (not `/mensagens`)
- [x] AC2: "Contato" footer link either points to `/ajuda#contato` or shows `suporte@smartlic.tech` email
- [x] AC3: Footer links are consistent across all pages (landing, `/buscar`, `/planos`, `/ajuda`)
- [x] AC4: All footer links are accessible to unauthenticated users (no auth-gated dead ends)

### FAQ Page Contact Fix

- [x] AC5: "Enviar Mensagem" button on `/ajuda` shows `suporte@smartlic.tech` email link for unauthenticated users, OR links to `/mensagens` only for authenticated users
- [x] AC6: Alternative: add a `mailto:suporte@smartlic.tech` link alongside the `/mensagens` button

### Verification

- [x] AC7: As an anonymous user, navigate to footer "Central de Ajuda" → lands on `/ajuda` successfully
- [x] AC8: As an anonymous user, clicking "Contato" does NOT redirect to login

## Dependencies

- None

## File List

| File | Action | Description |
|------|--------|-------------|
| `frontend/app/components/Footer.tsx` | Modify | Fix "Contato" href from `/mensagens` to `/ajuda#contato` |
| `frontend/app/ajuda/page.tsx` | Modify | Auth-aware contact section: `/mensagens` for logged-in, `mailto:` for anon; added `id="contato"` anchor |
| `frontend/__tests__/components/Footer.test.tsx` | Create | 5 tests for AC1-AC4 |
| `frontend/__tests__/pages/AjudaPage.test.tsx` | Create | 9 tests for AC5-AC8 |
