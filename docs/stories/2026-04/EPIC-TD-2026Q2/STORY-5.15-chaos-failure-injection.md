# STORY-5.15: Chaos/Failure Injection toxiproxy (TD-QA-061)

**Priority:** P2 | **Effort:** M (16-24h) | **Squad:** @qa + @devops + @architect | **Status:** Blocked
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** chaos tests com toxiproxy injetando falhas em PNCP/PCP/Stripe/OpenAI, **so that** circuit breakers + fallbacks sejam validados.

## Acceptance Criteria
- [ ] AC1: toxiproxy setup em test env
- [ ] AC2: 5+ chaos scenarios:
  - PNCP timeout
  - PCP slow response
  - OpenAI rate limit
  - Supabase connection drop
  - Stripe webhook delayed
- [ ] AC3: E2E tests assertam graceful degradation (cache served, fallback summary, etc.)
- [ ] AC4: CI workflow `chaos-tests.yml` weekly

## Tasks
- [ ] toxiproxy setup
- [ ] Scenarios
- [ ] E2E assertions
- [ ] CI workflow

## Dev Notes
- TD-QA-061 ref
- toxiproxy: https://github.com/Shopify/toxiproxy

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
