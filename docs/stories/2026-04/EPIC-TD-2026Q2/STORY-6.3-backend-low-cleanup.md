# STORY-6.3: Backend Low Cleanup (TD-SYS-030, 031, 032)

**Priority:** P3 | **Effort:** S (8-12h) | **Squad:** @dev | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** dev SmartLic, **I want** débitos low backend resolvidos, **so that** codebase fique limpo.

## Acceptance Criteria
- [ ] AC1 (TD-SYS-030): Documentar coexistência `backend/migrations/` (Python) + `supabase/migrations/` (SQL) em CLAUDE.md
- [ ] AC2 (TD-SYS-031): Audit + remove dead code em `backend/legacy/`
- [ ] AC3 (TD-SYS-032): Avaliar re-enable OTEL spans completos (depende STORY-1.6 SIGSEGV resolution)

## Tasks
- [ ] Doc clarification (AC1)
- [ ] Dead code audit + delete (AC2)
- [ ] OTEL re-enable se SIGSEGV resolved (AC3)

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
