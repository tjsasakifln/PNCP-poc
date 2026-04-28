-- Migration: Set service_role statement_timeout to 60s
--
-- Why: Backend uses SUPABASE_SERVICE_ROLE_KEY for admin client (RLS bypass).
-- Default: anon=3s, authenticated=8s, service_role=NULL (no timeout).
-- Without a timeout, runaway queries can exhaust the connection pool —
-- root-cause class for the 2026-04-27 Stage 2 outage where Googlebot waves
-- on perfil-b2g + fornecedor SEO routes saturated the pool.
--
-- 60s is generous enough for legitimate ingestion + reporting queries while
-- bounding worst-case impact. Individual queries needing more can override
-- with `SET LOCAL statement_timeout = '<n>s'` inside a transaction.
--
-- See: feedback memory `reference_supabase_service_role_no_timeout_default.md`
-- and `project_backend_outage_2026_04_27.md`.

ALTER ROLE service_role SET statement_timeout = '60s';

-- Reload PostgREST schema/role config so the new setting takes effect immediately.
NOTIFY pgrst, 'reload config';
