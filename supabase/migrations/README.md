# supabase/migrations — Conventions & Policy

## File Naming

| File | Convention | Purpose |
|------|-----------|---------|
| Up migration | `YYYYMMDDHHMMSS_description.sql` | Forward schema change |
| Down migration | `YYYYMMDDHHMMSS_description.down.sql` | Rollback of the corresponding up |

Both files must live in `supabase/migrations/`. The timestamp prefix is shared; only the `.down.sql` suffix distinguishes them.

## Forward-Looking Rule (STORY-6.2)

Every new `*.sql` migration **requires** a paired `*.down.sql`. This is enforced by CI (see `.github/workflows/migration-gate.yml`). PRs that add an `up` migration without a `down` will fail the gate.

## down.sql Template

```sql
-- ============================================================================
-- DOWN: <description> — reverses <YYYYMMDDHHMMSS_description.sql>
-- Date: YYYY-MM-DD
-- Author: @dev / @data-engineer
-- ============================================================================
-- Context:
--   Describe what the up migration did and what this down script undoes.
--   State any irreversible operations that require manual restore.
-- ============================================================================

-- Reverse operations in the OPPOSITE ORDER of the up migration.
-- Every statement MUST be idempotent (IF EXISTS / IF NOT EXISTS guards).

-- Example patterns:
-- CREATE TABLE   → DROP TABLE IF EXISTS public.<table>;
-- ADD COLUMN     → ALTER TABLE public.<t> DROP COLUMN IF EXISTS <col>;
-- CREATE INDEX   → DROP INDEX IF EXISTS <idx>;
-- CREATE POLICY  → DROP POLICY IF EXISTS <policy> ON public.<table>;
-- cron.schedule  → SELECT cron.unschedule('<job-name>');
-- COMMENT ON     → COMMENT ON COLUMN public.<t>.<col> IS NULL;
```

## Idempotence Requirements

- `DROP TABLE IF EXISTS`
- `DROP COLUMN IF EXISTS`
- `DROP INDEX IF EXISTS`
- `DROP POLICY IF EXISTS`
- `DROP CONSTRAINT IF EXISTS`
- `SELECT cron.unschedule(...)` for pg_cron jobs

## Irreversible Migrations (DML)

Migrations that INSERT, UPDATE, or DELETE data rows **cannot be automatically reversed** — there is no safe way to undo a bulk write without a backup. In these cases the `.down.sql` **must** contain:

```sql
-- NO AUTOMATIC ROLLBACK: manual restore from backup required.
-- This migration performed DML (INSERT/UPDATE/DELETE) that cannot be
-- deterministically reversed. To rollback:
--   1. Identify the affected rows (see the corresponding up migration).
--   2. Restore from the most recent backup taken before the migration ran.
--   3. Validate row counts and data integrity post-restore.
--
-- See STORY-6.2 TD-DB-030 for the full rollback policy.
```

## Common Patterns

| up operation | down operation |
|-------------|----------------|
| `CREATE TABLE IF NOT EXISTS t` | `DROP TABLE IF EXISTS public.t;` |
| `ALTER TABLE t ADD COLUMN IF NOT EXISTS c` | `ALTER TABLE public.t DROP COLUMN IF EXISTS c;` |
| `CREATE INDEX IF NOT EXISTS idx` | `DROP INDEX IF EXISTS public.idx;` |
| `CREATE POLICY p ON t` | `DROP POLICY IF EXISTS p ON public.t;` |
| `ALTER TABLE t ADD CONSTRAINT fk` | `ALTER TABLE public.t DROP CONSTRAINT IF EXISTS fk;` |
| `SELECT cron.schedule('job', ...)` | `SELECT cron.unschedule('job');` |
| `COMMENT ON COLUMN t.c IS '...'` | `COMMENT ON COLUMN public.t.c IS NULL;` |
| `CREATE TEXT SEARCH CONFIGURATION` | `DROP TEXT SEARCH CONFIGURATION IF EXISTS public.cfg;` |
| Bulk `UPDATE` / `INSERT` | `-- NO AUTOMATIC ROLLBACK: manual restore from backup required.` |

## CI Gate

`.github/workflows/migration-gate.yml` contains a step `check-down-sql-pairing` that runs on every PR touching `supabase/migrations/`. It checks every new `*.sql` file added in the PR for a matching `*.down.sql`. The step **fails the CI run** (exit 1) if a down file is missing.

## Related

- STORY-6.2 TD-DB-030 — introduced this convention
- STORY-6.3 TD-SYS-030 — documents `supabase/migrations/` vs `backend/migrations/` policy in `CLAUDE.md`
- CI flow: CRIT-050 (`migration-gate.yml`, `migration-check.yml`, `deploy.yml`)
