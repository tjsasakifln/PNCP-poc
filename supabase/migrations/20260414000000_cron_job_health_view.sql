-- STORY-1.1 (TD-DB-040): pg_cron monitoring view + RPC
-- Aggregates cron.job + cron.job_run_details into a health summary
-- accessible to the backend via service_role RPC only.

-- View: last 7 days of pg_cron run history per job
CREATE OR REPLACE VIEW public.cron_job_health AS
SELECT
  j.jobname,
  j.schedule,
  j.active,
  max(d.start_time) AS last_run_at,
  (ARRAY_AGG(d.status ORDER BY d.start_time DESC))[1] AS last_status,
  count(*) FILTER (WHERE d.start_time > now() - interval '24 hours') AS runs_24h,
  count(*) FILTER (WHERE d.status = 'failed' AND d.start_time > now() - interval '24 hours') AS failures_24h,
  round(
    avg(EXTRACT(EPOCH FROM (d.end_time - d.start_time)) * 1000)::numeric,
    1
  ) AS latency_avg_ms
FROM cron.job j
LEFT JOIN cron.job_run_details d
  ON j.jobid = d.jobid
  AND d.start_time > now() - interval '7 days'
GROUP BY j.jobname, j.schedule, j.active;

-- RPC: SECURITY DEFINER so service_role can read cron.* without direct access
CREATE OR REPLACE FUNCTION public.get_cron_health()
RETURNS TABLE (
  jobname text,
  schedule text,
  active boolean,
  last_run_at timestamptz,
  last_status text,
  runs_24h bigint,
  failures_24h bigint,
  latency_avg_ms numeric
)
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT
    jobname,
    schedule,
    active,
    last_run_at,
    last_status,
    runs_24h,
    failures_24h,
    latency_avg_ms
  FROM public.cron_job_health
  ORDER BY jobname;
$$;

-- Grant only to service_role (admin-only; anon/authenticated must not call this)
GRANT EXECUTE ON FUNCTION public.get_cron_health() TO service_role;
REVOKE EXECUTE ON FUNCTION public.get_cron_health() FROM PUBLIC;
