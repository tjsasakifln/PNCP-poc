# STORY-5.9: Storybook Setup + Canonical Components (TD-FE-011)

**Priority:** P2 | **Effort:** M (16-24h) | **Squad:** @ux-design-expert + @dev | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** dev SmartLic, **I want** Storybook com components canonicos, **so that** discovery + reuse melhore + design system seja documentado.

## Acceptance Criteria
- [ ] AC1: Storybook 8.x setup em `frontend/`
- [ ] AC2: Stories para 10+ canonical components (`<Button>`, `<Input>`, `<Modal>`, `<Card>`, etc.)
- [ ] AC3: Variants documentadas (CVA-based)
- [ ] AC4: Hosted (Chromatic, Vercel, ou GitHub Pages)
- [ ] AC5: CI builds Storybook successfully

## Tasks
- [ ] Storybook init
- [ ] 10 stories
- [ ] Hosting setup
- [ ] CI integration
- [ ] Docs link em CLAUDE.md

## Dev Notes
- TD-FE-011 ref
- `Button.examples.tsx` órfão (TD-FE-032) — convert to Storybook story

## Definition of Done
- [ ] Storybook deployed + 10 stories + CI verde

## Risks
- R1: Maintenance overhead — mitigation: enforce "new component = new story"

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
