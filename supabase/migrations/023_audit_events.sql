-- ============================================================================
-- Migration 023: Audit Events Table
-- STORY-226 Track 5: Observability (AC18-AC20)
-- Date: 2026-02-13
-- ============================================================================
-- Creates the audit_events table for persistent audit logging.
-- All actor IDs and IP addresses are stored as SHA-256 hashes (truncated to
-- 16 hex chars) for privacy compliance (LGPD/GDPR).
--
-- RETENTION POLICY: 12 months.
-- Rows older than 12 months are automatically purged via pg_cron job
-- (see section 3 below). For manual cleanup, run:
--   DELETE FROM audit_events WHERE timestamp < NOW() - INTERVAL '12 months';
-- ============================================================================

-- ============================================================
-- 1. Create audit_events table
-- ============================================================

CREATE TABLE IF NOT EXISTS public.audit_events (
    id              uuid            PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       timestamptz     NOT NULL DEFAULT now(),
    event_type      text            NOT NULL,
    actor_id_hash   text,           -- SHA-256 hash of user ID, truncated to 16 hex chars
    target_id_hash  text,           -- SHA-256 hash of target user ID, truncated to 16 hex chars
    details         jsonb,          -- Structured event metadata (sanitized, no PII)
    ip_hash         text            -- SHA-256 hash of client IP, truncated to 16 hex chars
);

-- Retention policy comment (12 months)
COMMENT ON TABLE public.audit_events IS
    'Persistent audit log for security-relevant events. '
    'RETENTION: 12 months — rows older than 12 months are automatically purged by pg_cron job cleanup-audit-events. '
    'All PII (actor_id, target_id, IP) is stored as SHA-256 hashes truncated to 16 hex chars for LGPD/GDPR compliance.';

COMMENT ON COLUMN public.audit_events.actor_id_hash IS
    'SHA-256 hash of the acting user ID, truncated to 16 hex chars. NULL for system events.';

COMMENT ON COLUMN public.audit_events.target_id_hash IS
    'SHA-256 hash of the target user ID, truncated to 16 hex chars. NULL when not applicable.';

COMMENT ON COLUMN public.audit_events.ip_hash IS
    'SHA-256 hash of the client IP address, truncated to 16 hex chars. NULL when unavailable.';

COMMENT ON COLUMN public.audit_events.event_type IS
    'Event category. Valid types: auth.login, auth.logout, auth.signup, '
    'admin.user_create, admin.user_delete, admin.plan_assign, '
    'billing.checkout, billing.subscription_change, data.search, data.download';

-- ============================================================
-- 2. Indexes for common query patterns
-- ============================================================

-- Query by event type (dashboards, alerting)
CREATE INDEX IF NOT EXISTS idx_audit_events_event_type
    ON public.audit_events (event_type);

-- Query by timestamp (retention cleanup, time-range queries)
CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp
    ON public.audit_events (timestamp);

-- Query by actor (investigation, user activity audit)
CREATE INDEX IF NOT EXISTS idx_audit_events_actor
    ON public.audit_events (actor_id_hash)
    WHERE actor_id_hash IS NOT NULL;

-- Composite index for common dashboard query: type + time range
CREATE INDEX IF NOT EXISTS idx_audit_events_type_timestamp
    ON public.audit_events (event_type, timestamp DESC);

-- ============================================================
-- 3. RLS Policies
-- ============================================================

ALTER TABLE public.audit_events ENABLE ROW LEVEL SECURITY;

-- Service role has full access (backend writes via service_role key)
CREATE POLICY "Service role can manage audit events" ON public.audit_events
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Admins can read audit events (for admin dashboard)
CREATE POLICY "Admins can read audit events" ON public.audit_events
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid() AND profiles.is_admin = true
        )
    );

-- ============================================================
-- 4. pg_cron retention cleanup (12-month retention)
-- ============================================================

-- Schedule: 1st day of every month at 4:00 AM UTC
-- Purges audit events older than 12 months
SELECT cron.schedule(
    'cleanup-audit-events',                              -- job name
    '0 4 1 * *',                                          -- cron: 4am on 1st of month
    $$
        DELETE FROM public.audit_events
        WHERE timestamp < NOW() - INTERVAL '12 months'
    $$
);

-- ============================================================
-- 5. Initial cleanup (run once — no-op on fresh install)
-- ============================================================

DELETE FROM public.audit_events
WHERE timestamp < NOW() - INTERVAL '12 months';

-- ============================================================================
-- Verification queries (run after applying):
-- ============================================================================
-- 1. Check table exists:
--    SELECT * FROM information_schema.tables WHERE table_name = 'audit_events';
--
-- 2. Check indexes:
--    SELECT indexname FROM pg_indexes WHERE tablename = 'audit_events';
--
-- 3. Check RLS policies:
--    SELECT policyname, roles FROM pg_policies WHERE tablename = 'audit_events';
--
-- 4. Check pg_cron job:
--    SELECT jobname, schedule FROM cron.job WHERE jobname = 'cleanup-audit-events';
--
-- 5. Check retention comment:
--    SELECT obj_description('public.audit_events'::regclass, 'pg_class');
-- ============================================================================
