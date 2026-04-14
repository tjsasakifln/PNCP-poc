# STORY-5.7: DB Infrastructure (TD-DB-040, 041, 042 — monitoring/backup/pool)

**Priority:** P2 | **Effort:** M (10-20h) | **Squad:** @data-engineer + @devops | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6
**Note:** TD-DB-040 (cron monitoring) já está em STORY-1.1; aqui foco em 041 + 042

## Story
**As a** SRE SmartLic, **I want** backup off-site + connection pooler tunado, **so that** vendor lock-in reduza e pool não esgote em pico.

## Acceptance Criteria
- [ ] AC1 (TD-DB-041): Weekly `pg_dump` → S3 com encryption (GitHub Action ou Railway cron)
- [ ] AC2 (TD-DB-041): Restore script testado em dev environment
- [ ] AC3 (TD-DB-042): Audit Supavisor `default_pool_size` + `max_client_conn` vs worker count
- [ ] AC4 (TD-DB-042): Tune valores apropriados; documentar rationale

## Tasks
- [ ] AC1: GH Actions weekly + S3 setup
- [ ] AC2: Restore drill
- [ ] AC3: Supavisor audit
- [ ] AC4: Apply settings

## Dev Notes
- DB-AUDIT TD-DB-041, 042 refs
- Supavisor é Supabase-managed — config via dashboard ou API

## Definition of Done
- [ ] Backup off-site running + pooler tuned + restore tested

## Risks
- R1: S3 cost — mitigation: lifecycle policy delete >30d

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
