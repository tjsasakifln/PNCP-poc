# STORY-232: Visual Consistency — Header Translucency Across Pages

**Status:** Done
**Priority:** P2 — Polish
**Sprint:** Sprint 3 (pre-GTM)
**Estimated Effort:** XS (30min)
**Source:** GTM-READINESS-VALIDATION-REPORT.md (MIN-4)
**Squad:** team-bidiq-frontend (dev)

---

## Context

The landing page (`/`) header has a translucent/glass effect (backdrop blur). The `/buscar` page header is solid/opaque. This creates visual inconsistency across the app.

## Acceptance Criteria

- [x] AC1: Header on `/buscar` has the same translucent/glass effect as the landing page header
- [x] AC2: Header style is consistent across all pages: `/`, `/buscar`, `/planos`, `/ajuda`, `/login`
- [x] AC3: Header remains readable over all page backgrounds (sufficient contrast)
- [x] AC4: Glass effect works in both light and dark modes (if applicable)

## Dependencies

- None

## Implementation Summary

### Glass styling standard (all headers)
```
sticky top-0 z-50 bg-[var(--surface-0)] backdrop-blur-sm supports-[backdrop-filter]:bg-[var(--surface-0)]/95 border-b border-[var(--border)] shadow-sm
```

### Per-page header mapping

| Page | Header | Glass Effect | Notes |
|------|--------|-------------|-------|
| `/` | LandingNavbar | Scroll-based (transparent → glass) | Reference implementation |
| `/buscar` | Inline header | Always-on glass | Aligned border/shadow classes |
| `/planos` | LandingNavbar (added) | Scroll-based | Was missing header entirely |
| `/ajuda` | LandingNavbar (added) | Scroll-based | Was missing header entirely |
| `/login` | None (by design) | N/A | Auth flow, headerless |
| Protected pages | AppHeader | Always-on glass | Updated from solid opaque |

## File List

| File | Action | Description |
|------|--------|-------------|
| `frontend/app/components/AppHeader.tsx` | Modified | Added backdrop-blur-sm, /95 opacity, z-50 |
| `frontend/app/buscar/page.tsx` | Modified | Aligned header classes (border, shadow) |
| `frontend/app/planos/page.tsx` | Modified | Added LandingNavbar import and rendering |
| `frontend/app/ajuda/page.tsx` | Modified | Added LandingNavbar import and rendering |
