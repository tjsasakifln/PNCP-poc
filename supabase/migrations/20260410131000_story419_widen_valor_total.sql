-- STORY-419: Widen search_sessions.valor_total to NUMERIC(18,2)
--
-- Context:
--   ``search_sessions.valor_total`` was created as NUMERIC(14,2) in
--   supabase/migrations/001_profiles_and_sessions.sql:90, giving a ceiling
--   of R$ 999.999.999.999,99 (~R$ 1 trillion). Government megaprojects
--   (oil refineries, hydroelectric dams) already publish editais above
--   that threshold, which triggered 3 Sentry events with SQLSTATE 22003
--   (numeric field overflow) on 2026-04-10 (issue 7369847734).
--
--   The downstream ``datalake.valor_total_estimado`` is already
--   NUMERIC(18,2) (migration 20260326000000), so widening the session
--   column to match is both consistent and future-proof.
--
--   Widening the precision of a NUMERIC column is a metadata-only
--   operation in PostgreSQL: no table rewrite, no long lock, safe to run
--   in production during business hours. Rollback is equally safe as
--   long as no row exceeds 10^14.
--
-- Scope:
--   * search_sessions.valor_total  NUMERIC(14,2) -> NUMERIC(18,2)
--   * Matching validation at the API boundary lives in
--     backend/schemas/search.py (field_validator on valor_maximo), so the
--     column ceiling and the request ceiling move together.

ALTER TABLE public.search_sessions
    ALTER COLUMN valor_total TYPE NUMERIC(18, 2);

COMMENT ON COLUMN public.search_sessions.valor_total IS
    'Sum of opportunity values in BRL. Widened from NUMERIC(14,2) to NUMERIC(18,2) '
    'by STORY-419 (incident 2026-04-10) to accommodate federal megaprojects.';
