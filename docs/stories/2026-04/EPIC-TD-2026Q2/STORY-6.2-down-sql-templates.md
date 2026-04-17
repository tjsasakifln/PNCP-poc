# STORY-6.2: down.sql Migration Rollback Templates (TD-DB-030)

**Priority:** P3 | **Effort:** S (4-8h) | **Squad:** @data-engineer + @devops | **Status:** Ready for Review
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** SmartLic, **I want** templates de rollback `down.sql` para migrations, **so that** failed migrations possam ser revertidas.

## Acceptance Criteria
- [x] AC1: `supabase/migrations/README.md` criado com convenção de nome (`YYYYMMDDHHMMSS_description.sql` up + `.down.sql` down), template de `down.sql` com cabeçalho de contexto, idempotência (`DROP ... IF EXISTS`), regra de ouro para DML irreversível (`-- NO AUTOMATIC ROLLBACK: manual restore from backup required`), e exemplos de casos (CREATE TABLE, ADD COLUMN, CREATE INDEX, RLS policy).
- [x] AC2: Regra forward-looking documentada — toda nova migration requer `.down.sql` pareado. Refletida na documentação do README.
- [x] AC3: Gate CI adicionado em `.github/workflows/migration-gate.yml` (step `Check down.sql pairing`): itera sobre novos `*.sql` adicionados no PR, falha com `exit 1` se `.down.sql` correspondente estiver ausente.
- [x] AC4: 5 migrations recentes back-filled com `.down.sql`:
  - `20260415140000_story56_db_medium_fixes.down.sql` — reverte is_active col, digest-scan idx, policy comment
  - `20260415120001_search_datalake_use_portuguese_smartlic.down.sql` — reverte FTS config para builtin portuguese
  - `20260415120000_fts_portuguese_smartlic.down.sql` — dropa public.portuguese_smartlic config
  - `20260414133000_search_datalake_coalesce_dates.down.sql` — reverte COALESCE date fallbacks
  - `20260414132000_backfill_pncp_raw_bids_dates.down.sql` — **NO AUTOMATIC ROLLBACK** (DML backfill; manual restore from backup)

## Tasks
- [x] Template setup (supabase/migrations/README.md)
- [x] CI gate (.github/workflows/migration-gate.yml)
- [x] Backfill (5 down.sql files)

## Dev Notes
- DB-AUDIT TD-DB-030 ref
- Supabase CLI suporta versioning mas não down — scripts manuais por design
- Migrations DML (backfill_pncp_raw_bids_dates) documentam `NO AUTOMATIC ROLLBACK` conforme convenção
- CI gate posicionado ANTES do step de schema contract para fail-fast em PRs

## File List
| File | Action |
|------|--------|
| `supabase/migrations/README.md` | Created |
| `.github/workflows/migration-gate.yml` | Modified (new step: Check down.sql pairing) |
| `supabase/migrations/20260415140000_story56_db_medium_fixes.down.sql` | Created |
| `supabase/migrations/20260415120001_search_datalake_use_portuguese_smartlic.down.sql` | Created |
| `supabase/migrations/20260415120000_fts_portuguese_smartlic.down.sql` | Created |
| `supabase/migrations/20260414133000_search_datalake_coalesce_dates.down.sql` | Created |
| `supabase/migrations/20260414132000_backfill_pncp_raw_bids_dates.down.sql` | Created |
| `docs/stories/2026-04/EPIC-TD-2026Q2/STORY-6.2-down-sql-templates.md` | Modified |

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-16 | 1.1 | AC1-AC4 completos. README criado, CI gate adicionado, 5 down.sql backfilled. Status → Ready for Review. | @data-engineer |
