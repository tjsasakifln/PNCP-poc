-- Down migration: restore service_role to no timeout (Postgres default).
--
-- Use only if 60s proves too aggressive for ingestion/reporting workloads.
-- Prefer per-query `SET LOCAL statement_timeout` overrides instead of rolling back.

ALTER ROLE service_role RESET statement_timeout;

NOTIFY pgrst, 'reload config';
