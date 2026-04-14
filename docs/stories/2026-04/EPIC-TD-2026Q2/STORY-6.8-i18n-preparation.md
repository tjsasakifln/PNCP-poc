# STORY-6.8: i18n Preparation (TD-FE-010) — IF LATAM Approved

**Priority:** P3 (BLOCKED — depende decisão produto LATAM expansion)
**Effort:** L (40h+)
**Squad:** @ux-design-expert + @dev + @architect
**Status:** Draft (BLOCKED)
**Epic:** EPIC-TD-2026Q2
**Sprint:** 7+

## Story
**As a** SmartLic LATAM expansion (se aprovado), **I want** i18n infrastructure pronta + strings extracted, **so that** novo locale (es-MX, en-US) seja addable em <2 semanas.

## Acceptance Criteria (HIGH-LEVEL — detail post-decisão)
- [ ] AC0 (BLOCKER): Decisão produto LATAM aprovada
- [ ] AC1: `next-intl` ou similar setup
- [ ] AC2: Strings extracted dos 170+ feature components → JSON catalog `pt-BR.json`
- [ ] AC3: Locale routing `/pt-br/buscar`, `/es-mx/buscar`
- [ ] AC4: Date/number formatting via `Intl.*`
- [ ] AC5: 5 páginas core fully translated (login, signup, buscar, conta, planos)

## Tasks (post-decisão)
- [ ] Tool selection
- [ ] String extraction codemod
- [ ] Locale routing
- [ ] Translation pipeline (Lokalise/Crowdin)

## Dev Notes
- TD-FE-010 ref
- BLOCKED até PM/sponsor confirmar LATAM no roadmap
- Custo estimado 40-80h (high uncertainty)

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft (BLOCKED) | @sm |
