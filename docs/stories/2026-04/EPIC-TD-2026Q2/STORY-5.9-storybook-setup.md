# STORY-5.9: Storybook Setup + Canonical Components (TD-FE-011)

**Priority:** P2 | **Effort:** M (16-24h) | **Squad:** @ux-design-expert + @dev | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** dev SmartLic, **I want** Storybook com components canônicos, **so that** discovery + reuse melhore + design system seja documentado.

## Acceptance Criteria
- [x] AC1: Storybook 8.6.x setup em `frontend/` (react-webpack5 framework — `@storybook/nextjs` incompatível com Next.js 16)
- [x] AC2: 11 stories para canonical components (Button, Input, Label, Pagination, Modal, EmptyState, ErrorMessage, ErrorStateWithRetry, Skeleton, ViabilityBadge, PageHeader)
- [x] AC3: CVA variants documentadas (Button: 6 variants × 4 sizes, Input: 3 sizes × 3 states)
- [ ] AC4: Hosted — **BLOCKED: requires Chromatic/Vercel account setup**
- [x] AC5: CI workflow `storybook-build.yml` — builds on PR when component files change

## Implementation Notes

### Storybook Setup (AC1)
- Framework: `@storybook/react-webpack5` (not `@storybook/nextjs` — incompatible with Next.js 16 which removed `next/config`)
- Config: `.storybook/main.ts` + `.storybook/preview.ts`
- Webpack alias: `@/` → project root (matches tsconfig paths)
- Build verified locally: `storybook-static/` generated successfully

### Stories Created (AC2) — 11 components
| Component | Story File | Variants |
|-----------|-----------|----------|
| Button | `components/ui/button.stories.tsx` | Primary, Secondary, Destructive, Ghost, Link, Outline, Small, Large, Loading, Disabled, Icon |
| Input | `components/ui/Input.stories.tsx` | Default, WithError, Success, Small, Large, Disabled, WithHelper |
| Label | `components/ui/Label.stories.tsx` | Default, Required |
| Pagination | `components/ui/Pagination.stories.tsx` | Default, MiddlePage, SmallDataset, FiftyPerPage |
| Modal | `components/Modal.stories.tsx` | Default, Small, Large, AlertDialog, Interactive |
| EmptyState | `components/EmptyState.stories.tsx` | Pipeline, History |
| ErrorMessage | `components/ErrorMessage.stories.tsx` | Default, NetworkError |
| ErrorStateWithRetry | `components/ErrorStateWithRetry.stories.tsx` | Default, WithTimestamp, Retrying, Compact |
| Skeleton | `components/skeletons/Skeleton.stories.tsx` | Text, TextMultiple, Card, List, Avatar, Block |
| ViabilityBadge | `components/ViabilityBadge.stories.tsx` | Alta, Media, Baixa, WithMissingValue, NoLevel |
| PageHeader | `components/PageHeader.stories.tsx` | Default, WithControls |

### CI (AC5)
- `.github/workflows/storybook-build.yml` — runs on PR when component paths change
- `npm run build-storybook` verified locally

## File List
- `frontend/.storybook/main.ts` — Storybook config
- `frontend/.storybook/preview.ts` — Storybook preview
- `frontend/components/**/*.stories.tsx` — 11 story files
- `frontend/package.json` — storybook + build-storybook scripts
- `frontend/.gitignore` — storybook-static/ excluded
- `.github/workflows/storybook-build.yml` — CI workflow

## Definition of Done
- [x] AC1-AC3, AC5 met (4/5)
- [ ] AC4 deferred (hosting account)

## Risks
- R1: `@storybook/nextjs` incompatible with Next.js 16 — mitigated with `react-webpack5`
- R2: Tailwind CSS not loaded in Storybook — globals.css import causes webpack issues (use class-based stories)

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-16 | 1.1 | Implementation: Storybook 8.6 + 11 stories + CI. AC4 deferred (hosting). | @dev |
