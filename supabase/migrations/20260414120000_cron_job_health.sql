-- STORY-1.1 (EPIC-TD-2026Q2 P0): pg_cron monitoring infrastructure.
--
-- Creates a health view + RPC that surface the last 7 days of pg_cron runs
-- (jobs + run_details). The backend `/v1/admin/cron-status` endpoint reads
-- from `get_cron_health()` and an hourly ARQ job raises Sentry alerts when
-- any job is stale (>25h since last successful run) or last_status='failed'.
--
-- Prerequisite for STORY-1.2/1.3/1.4 (new scheduled crons) — without this,
-- scheduling more crons amplifies the silent-failure risk.

SET statement_timeout = 0;

CREATE EXTENSION IF NOT EXISTS pg_cron;

-- ───────────────────────────────────────────────────────────────────────────
-- View: public.cron_job_health
-- Aggregates cron.job + cron.job_run_details restricted to the last 7 days.
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW public.cron_job_health AS
WITH recent_runs AS (
    SELECT
        d.jobid,
        d.status,
        d.return_message,
        d.start_time,
        d.end_time,
        EXTRACT(EPOCH FROM (d.end_time - d.start_time)) * 1000 AS latency_ms
    FROM cron.job_run_details d
    WHERE d.start_time >= (now() - interval '7 days')
),
aggregated AS (
    SELECT
        j.jobid,
        j.jobname,
        j.schedule,
        j.active,
        MAX(r.start_time) AS last_run_at,
        COUNT(r.*) FILTER (WHERE r.start_time >= (now() - interval '24 hours')) AS runs_24h,
        COUNT(r.*) FILTER (
            WHERE r.status = 'failed'
              AND r.start_time >= (now() - interval '24 hours')
        ) AS failures_24h,
        AVG(r.latency_ms) FILTER (WHERE r.latency_ms IS NOT NULL)::bigint AS latency_avg_ms
    FROM cron.job j
    LEFT JOIN recent_runs r ON r.jobid = j.jobid
    GROUP BY j.jobid, j.jobname, j.schedule, j.active
),
last_status AS (
    SELECT DISTINCT ON (r.jobid)
        r.jobid,
        r.status AS last_status,
        r.return_message AS last_return_message
    FROM recent_runs r
    ORDER BY r.jobid, r.start_time DESC
)
SELECT
    a.jobname,
    a.schedule,
    a.active,
    COALESCE(ls.last_status, 'never_ran') AS last_status,
    a.last_run_at,
    COALESCE(a.runs_24h, 0) AS runs_24h,
    COALESCE(a.failures_24h, 0) AS failures_24h,
    a.latency_avg_ms,
    ls.last_return_message
FROM aggregated a
LEFT JOIN last_status ls ON ls.jobid = a.jobid
ORDER BY a.jobname;

COMMENT ON VIEW public.cron_job_health IS
    'STORY-1.1 — Health view aggregating cron.job + cron.job_run_details (7 day window). '
    'Consumed by get_cron_health() RPC + /v1/admin/cron-status + hourly Sentry monitor.';

-- ───────────────────────────────────────────────────────────────────────────
-- RPC: public.get_cron_health()
-- SECURITY DEFINER so backend (service_role) can read cron.* even though
-- those tables are owned by the supabase_admin/postgres role.
-- ───────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.get_cron_health()
RETURNS TABLE (
    jobname TEXT,
    schedule TEXT,
    active BOOLEAN,
    last_status TEXT,
    last_run_at TIMESTAMPTZ,
    runs_24h BIGINT,
    failures_24h BIGINT,
    latency_avg_ms BIGINT,
    last_return_message TEXT
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    SELECT
        jobname::TEXT,
        schedule::TEXT,
        active,
        last_status::TEXT,
        last_run_at,
        runs_24h,
        failures_24h,
        latency_avg_ms,
        last_return_message::TEXT
    FROM public.cron_job_health;
$$;

COMMENT ON FUNCTION public.get_cron_health() IS
    'STORY-1.1 — SECURITY DEFINER RPC returning pg_cron health snapshot. '
    'Backend admin endpoint calls this via supabase.rpc(''get_cron_health'').';

-- Only service_role (backend) may invoke — admin gating enforced at the API layer.
REVOKE ALL ON FUNCTION public.get_cron_health() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_cron_health() FROM anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_cron_health() TO service_role;
