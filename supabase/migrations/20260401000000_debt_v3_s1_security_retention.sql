-- ============================================================================
-- DEBT-v3-S1: Security DEFINER + SET search_path + Retention + Indexes
-- Story: story-debt-v3-S1-seguranca.md
-- Date: 2026-04-01
-- Sprint: S1 (Pre-GTM Technical Surgery)
--
-- This single, idempotent migration addresses:
--   AC1-AC3:  All SECURITY DEFINER functions get SET search_path = public
--   AC4-AC11: pg_cron retention jobs (create/update)
--   AC12:     Drop redundant indexes
--   AC13:     Trigger rename (verified — already done in 20260331100000)
--   AC14:     Composite indexes
-- ============================================================================

-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║  SECTION 1: SECURITY DEFINER + SET search_path                        ║
-- ║  Fix ALL functions that have SECURITY DEFINER without search_path     ║
-- ╚══════════════════════════════════════════════════════════════════════════╝

-- ──────────────────────────────────────────────────────────────────────────
-- 1.1 handle_new_user() — auth trigger (latest from debt_w4_db_micro_fixes)
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  _phone text;
BEGIN
  _phone := regexp_replace(COALESCE(NEW.raw_user_meta_data->>'phone_whatsapp', ''), '[^0-9]', '', 'g');
  IF length(_phone) > 11 AND left(_phone, 2) = '55' THEN _phone := substring(_phone from 3); END IF;
  IF left(_phone, 1) = '0' THEN _phone := substring(_phone from 2); END IF;
  IF length(_phone) NOT IN (10, 11) THEN _phone := NULL; END IF;

  BEGIN
    INSERT INTO public.profiles (
      id, email, full_name, company, sector,
      phone_whatsapp, whatsapp_consent, plan_type,
      avatar_url, context_data
    )
    VALUES (
      NEW.id,
      NEW.email,
      COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
      COALESCE(NEW.raw_user_meta_data->>'company', ''),
      COALESCE(NEW.raw_user_meta_data->>'sector', ''),
      _phone,
      COALESCE((NEW.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
      'free_trial',
      NEW.raw_user_meta_data->>'avatar_url',
      '{}'::jsonb
    )
    ON CONFLICT (id) DO NOTHING;

  EXCEPTION
    WHEN unique_violation THEN
      INSERT INTO public.profiles (
        id, email, full_name, company, sector,
        phone_whatsapp, whatsapp_consent, plan_type,
        avatar_url, context_data
      )
      VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        COALESCE(NEW.raw_user_meta_data->>'company', ''),
        COALESCE(NEW.raw_user_meta_data->>'sector', ''),
        NULL,
        COALESCE((NEW.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
        'free_trial',
        NEW.raw_user_meta_data->>'avatar_url',
        '{}'::jsonb
      )
      ON CONFLICT (id) DO NOTHING;
  END;

  RETURN NEW;
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.2 get_conversations_with_unread_count() — RPC (latest from debt017)
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.get_conversations_with_unread_count(
    p_user_id UUID,
    p_is_admin BOOLEAN DEFAULT FALSE,
    p_status TEXT DEFAULT NULL,
    p_limit INT DEFAULT 50,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    user_email TEXT,
    subject TEXT,
    category TEXT,
    status TEXT,
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    unread_count BIGINT,
    total_count BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    WITH filtered_conversations AS (
        SELECT c.*,
            p.email as profile_email,
            COUNT(*) OVER() as total
        FROM conversations c
        LEFT JOIN profiles p ON p.id = c.user_id
        WHERE (p_is_admin OR c.user_id = p_user_id)
            AND (p_status IS NULL OR c.status = p_status)
        ORDER BY c.last_message_at DESC
        LIMIT p_limit OFFSET p_offset
    )
    SELECT
        fc.id,
        fc.user_id,
        CASE WHEN p_is_admin THEN fc.profile_email ELSE NULL END,
        fc.subject,
        fc.category,
        fc.status,
        fc.last_message_at,
        fc.created_at,
        COALESCE(uc.unread, 0)::BIGINT as unread_count,
        fc.total as total_count
    FROM filtered_conversations fc
    LEFT JOIN LATERAL (
        SELECT COUNT(*) as unread
        FROM messages m
        WHERE m.conversation_id = fc.id
        AND CASE
            WHEN p_is_admin THEN (m.is_admin_reply = FALSE AND m.read_by_admin = FALSE)
            ELSE (m.is_admin_reply = TRUE AND m.read_by_user = FALSE)
        END
    ) uc ON TRUE;
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.3 get_analytics_summary() — RPC (from 019)
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.get_analytics_summary(
    p_user_id UUID,
    p_start_date TIMESTAMPTZ DEFAULT NULL,
    p_end_date TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE (
    total_searches BIGINT,
    total_downloads BIGINT,
    total_opportunities BIGINT,
    total_value_discovered NUMERIC,
    member_since TIMESTAMPTZ
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_searches,
        COUNT(*) FILTER (WHERE ss.total_filtered > 0)::BIGINT as total_downloads,
        COALESCE(SUM(ss.total_filtered), 0)::BIGINT as total_opportunities,
        COALESCE(SUM(ss.valor_total), 0)::NUMERIC as total_value_discovered,
        (SELECT p.created_at FROM profiles p WHERE p.id = p_user_id) as member_since
    FROM search_sessions ss
    WHERE ss.user_id = p_user_id
        AND (p_start_date IS NULL OR ss.created_at >= p_start_date)
        AND (p_end_date IS NULL OR ss.created_at <= p_end_date);
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.4 increment_quota_atomic() — adds SECURITY DEFINER (from 20260305100000)
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.increment_quota_atomic(
    p_user_id UUID,
    p_month_year VARCHAR(7),
    p_max_quota INT DEFAULT NULL
)
RETURNS TABLE(
    new_count INT,
    was_at_limit BOOLEAN,
    previous_count INT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_previous_count INT;
    v_new_count INT;
    v_was_at_limit BOOLEAN := FALSE;
BEGIN
    SELECT searches_count INTO v_previous_count
    FROM monthly_quota
    WHERE user_id = p_user_id AND month_year = p_month_year
    FOR UPDATE;

    IF v_previous_count IS NULL THEN
        v_previous_count := 0;
        INSERT INTO monthly_quota (user_id, month_year, searches_count, updated_at)
        VALUES (p_user_id, p_month_year, 1, now())
        ON CONFLICT (user_id, month_year) DO UPDATE
        SET searches_count = monthly_quota.searches_count + 1,
            updated_at = now()
        RETURNING searches_count INTO v_new_count;
    ELSE
        IF p_max_quota IS NOT NULL AND v_previous_count >= p_max_quota THEN
            v_was_at_limit := TRUE;
            v_new_count := v_previous_count;
        ELSE
            UPDATE monthly_quota
            SET searches_count = searches_count + 1,
                updated_at = now()
            WHERE user_id = p_user_id AND month_year = p_month_year
            RETURNING searches_count INTO v_new_count;
        END IF;
    END IF;

    RETURN QUERY SELECT v_new_count, v_was_at_limit, v_previous_count;
END;
$$;

GRANT EXECUTE ON FUNCTION public.increment_quota_atomic TO service_role;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.5 check_and_increment_quota() — adds SECURITY DEFINER (from 20260305100000)
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.check_and_increment_quota(
    p_user_id UUID,
    p_month_year VARCHAR(7),
    p_max_quota INT
)
RETURNS TABLE(
    allowed BOOLEAN,
    new_count INT,
    previous_count INT,
    quota_remaining INT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_previous_count INT;
    v_new_count INT;
    v_allowed BOOLEAN := TRUE;
BEGIN
    INSERT INTO monthly_quota (user_id, month_year, searches_count, updated_at)
    VALUES (p_user_id, p_month_year, 1, now())
    ON CONFLICT (user_id, month_year) DO UPDATE
    SET searches_count = CASE
        WHEN monthly_quota.searches_count < p_max_quota THEN monthly_quota.searches_count + 1
        ELSE monthly_quota.searches_count
    END,
    updated_at = now()
    RETURNING
        searches_count,
        searches_count - 1
    INTO v_new_count, v_previous_count;

    IF v_new_count > p_max_quota THEN
        v_allowed := FALSE;
    ELSIF v_previous_count >= p_max_quota THEN
        v_allowed := FALSE;
    END IF;

    RETURN QUERY SELECT
        v_allowed,
        v_new_count,
        COALESCE(v_previous_count, 0),
        GREATEST(0, p_max_quota - v_new_count);
END;
$$;

GRANT EXECUTE ON FUNCTION public.check_and_increment_quota TO service_role;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.6 get_user_billing_period() — from 011
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.get_user_billing_period(p_user_id UUID)
RETURNS VARCHAR(10)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_billing_period VARCHAR(10);
BEGIN
  SELECT billing_period INTO v_billing_period
  FROM public.user_subscriptions
  WHERE user_id = p_user_id AND is_active = true
  ORDER BY created_at DESC
  LIMIT 1;

  RETURN COALESCE(v_billing_period, 'monthly');
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.7 user_has_feature() — from 011
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.user_has_feature(
  p_user_id UUID,
  p_feature_key VARCHAR(100)
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_plan_id TEXT;
  v_billing_period VARCHAR(10);
  v_has_feature BOOLEAN;
BEGIN
  SELECT us.plan_id, us.billing_period INTO v_plan_id, v_billing_period
  FROM public.user_subscriptions us
  WHERE us.user_id = p_user_id AND us.is_active = true
  ORDER BY us.created_at DESC
  LIMIT 1;

  IF v_plan_id IS NULL THEN
    RETURN false;
  END IF;

  SELECT EXISTS (
    SELECT 1 FROM public.plan_features
    WHERE plan_id = v_plan_id
      AND billing_period = v_billing_period
      AND feature_key = p_feature_key
      AND enabled = true
  ) INTO v_has_feature;

  RETURN v_has_feature;
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.8 get_user_features() — from 011
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.get_user_features(p_user_id UUID)
RETURNS TEXT[]
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_plan_id TEXT;
  v_billing_period VARCHAR(10);
  v_features TEXT[];
BEGIN
  SELECT us.plan_id, us.billing_period INTO v_plan_id, v_billing_period
  FROM public.user_subscriptions us
  WHERE us.user_id = p_user_id AND us.is_active = true
  ORDER BY us.created_at DESC
  LIMIT 1;

  IF v_plan_id IS NULL THEN
    RETURN ARRAY[]::TEXT[];
  END IF;

  SELECT ARRAY_AGG(feature_key) INTO v_features
  FROM public.plan_features
  WHERE plan_id = v_plan_id
    AND billing_period = v_billing_period
    AND enabled = true;

  RETURN COALESCE(v_features, ARRAY[]::TEXT[]);
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.9 sync_profile_plan_type() — trigger function from 017
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.sync_profile_plan_type()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    IF NEW.status IN ('active', 'trialing') THEN
        UPDATE profiles
        SET plan_type = NEW.plan_id,
            updated_at = NOW()
        WHERE id = NEW.user_id;
    END IF;

    IF NEW.status IN ('canceled', 'expired', 'past_due') THEN
        UPDATE profiles
        SET plan_type = 'free_trial',
            updated_at = NOW()
        WHERE id = NEW.user_id;
    END IF;

    RETURN NEW;
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.10 sync_subscription_status_to_profile() — from debt_db001
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.sync_subscription_status_to_profile()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  mapped_status text;
BEGIN
  CASE NEW.subscription_status
    WHEN 'active'   THEN mapped_status := 'active';
    WHEN 'trialing' THEN mapped_status := 'trial';
    WHEN 'past_due' THEN mapped_status := 'past_due';
    WHEN 'canceled' THEN mapped_status := 'canceling';
    WHEN 'expired'  THEN mapped_status := 'expired';
    ELSE mapped_status := NULL;
  END CASE;

  IF mapped_status IS NOT NULL THEN
    UPDATE profiles
    SET subscription_status = mapped_status,
        updated_at = now()
    WHERE id = NEW.user_id
      AND (subscription_status IS DISTINCT FROM mapped_status);
  END IF;

  RETURN NEW;
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.11 cleanup_search_cache_per_user() — latest from debt_quick_wins
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.cleanup_search_cache_per_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    entry_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO entry_count
    FROM search_results_cache
    WHERE user_id = NEW.user_id;

    IF entry_count <= 10 THEN
        RETURN NEW;
    END IF;

    DELETE FROM search_results_cache
    WHERE id IN (
        SELECT id FROM search_results_cache
        WHERE user_id = NEW.user_id
        ORDER BY
            CASE priority
                WHEN 'cold' THEN 0
                WHEN 'warm' THEN 1
                WHEN 'hot'  THEN 2
                ELSE 0
            END ASC,
            COALESCE(last_accessed_at, created_at) ASC
        LIMIT (entry_count - 10)
    );
    RETURN NEW;
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.12 get_table_columns_simple() — from 20260221100001
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.get_table_columns_simple(p_table_name TEXT)
RETURNS TABLE(column_name TEXT)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
STABLE
AS $$
  SELECT column_name::TEXT
  FROM information_schema.columns
  WHERE table_schema = 'public'
    AND table_name = p_table_name
  ORDER BY ordinal_position;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.13 pg_total_relation_size_safe() — from debt010
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.pg_total_relation_size_safe(tbl text)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  result bigint;
BEGIN
  EXECUTE format('SELECT pg_total_relation_size(%L)', 'public.' || tbl) INTO result;
  RETURN COALESCE(result, 0);
EXCEPTION
  WHEN undefined_table THEN
    RETURN 0;
  WHEN insufficient_privilege THEN
    RETURN -1;
END $$;

-- ──────────────────────────────────────────────────────────────────────────
-- 1.14 check_ingestion_orphans() — from debt207_checkpoint
-- ──────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.check_ingestion_orphans()
RETURNS TABLE(orphan_count BIGINT, oldest_orphan TIMESTAMPTZ, sample_batch_ids TEXT[])
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*)::BIGINT AS orphan_count,
    MIN(ic.started_at) AS oldest_orphan,
    ARRAY(
      SELECT DISTINCT ic2.crawl_batch_id
      FROM public.ingestion_orphan_checkpoints ic2
      LIMIT 5
    ) AS sample_batch_ids
  FROM public.ingestion_orphan_checkpoints ic;
END;
$$;


-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║  SECTION 2: RETENTION pg_cron JOBS                                    ║
-- ║  Idempotent: unschedule + schedule pattern                            ║
-- ╚══════════════════════════════════════════════════════════════════════════╝

-- ──────────────────────────────────────────────────────────────────────────
-- AC4: search_state_transitions — 90 days, daily 05:00 UTC
-- (was 30 days at 04:00 — now 90 days at 05:00 per story spec)
-- ──────────────────────────────────────────────────────────────────────────
SELECT cron.unschedule('cleanup-search-state-transitions')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-search-state-transitions');

SELECT cron.schedule(
    'retention-search-state-transitions',
    '0 5 * * *',
    $$DELETE FROM public.search_state_transitions WHERE created_at < now() - interval '90 days'$$
);

-- Also unschedule old name if it exists
SELECT cron.unschedule('retention-search-state-transitions')
WHERE EXISTS (
    SELECT 1 FROM cron.job
    WHERE jobname = 'retention-search-state-transitions'
    AND schedule != '0 5 * * *'
);

SELECT cron.schedule(
    'retention-search-state-transitions',
    '0 5 * * *',
    $$DELETE FROM public.search_state_transitions WHERE created_at < now() - interval '90 days'$$
);

-- ──────────────────────────────────────────────────────────────────────────
-- AC5: classification_feedback — 180 days, daily 05:05 UTC (NEW)
-- ──────────────────────────────────────────────────────────────────────────
SELECT cron.unschedule('retention-classification-feedback')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'retention-classification-feedback');

SELECT cron.schedule(
    'retention-classification-feedback',
    '5 5 * * *',
    $$DELETE FROM public.classification_feedback WHERE created_at < now() - interval '180 days'$$
);

-- ──────────────────────────────────────────────────────────────────────────
-- AC6: alert_runs — 90 days, daily 05:10 UTC
-- (was 04:25 with status='completed' filter — now all statuses)
-- ──────────────────────────────────────────────────────────────────────────
SELECT cron.unschedule('cleanup-alert-runs')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-alert-runs');

SELECT cron.unschedule('retention-alert-runs')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'retention-alert-runs');

SELECT cron.schedule(
    'retention-alert-runs',
    '10 5 * * *',
    $$DELETE FROM public.alert_runs WHERE run_at < now() - interval '90 days'$$
);

-- ──────────────────────────────────────────────────────────────────────────
-- AC7: mfa_recovery_attempts — 30 days, daily 05:15 UTC
-- (was 04:20 — reschedule with consistent naming)
-- ──────────────────────────────────────────────────────────────────────────
SELECT cron.unschedule('cleanup-mfa-recovery-attempts')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-mfa-recovery-attempts');

SELECT cron.unschedule('retention-mfa-recovery-attempts')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'retention-mfa-recovery-attempts');

SELECT cron.schedule(
    'retention-mfa-recovery-attempts',
    '15 5 * * *',
    $$DELETE FROM public.mfa_recovery_attempts WHERE attempted_at < now() - interval '30 days'$$
);

-- ──────────────────────────────────────────────────────────────────────────
-- AC8: search_sessions (terminal states) — 180 days, daily 05:20 UTC (NEW)
-- ──────────────────────────────────────────────────────────────────────────
SELECT cron.unschedule('retention-search-sessions')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'retention-search-sessions');

SELECT cron.schedule(
    'retention-search-sessions',
    '20 5 * * *',
    $$DELETE FROM public.search_sessions WHERE status IN ('completed','failed','expired') AND updated_at < now() - interval '180 days'$$
);

-- ──────────────────────────────────────────────────────────────────────────
-- AC10: VACUUM ANALYZE for pncp_raw_bids — daily 07:30 UTC (NEW)
-- (30 min after purge at 07:00 UTC)
-- ──────────────────────────────────────────────────────────────────────────
SELECT cron.unschedule('vacuum-pncp-raw-bids')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'vacuum-pncp-raw-bids');

SELECT cron.schedule(
    'vacuum-pncp-raw-bids',
    '30 7 * * *',
    $$VACUUM ANALYZE public.pncp_raw_bids$$
);

-- ──────────────────────────────────────────────────────────────────────────
-- AC11: Weekly bloat check for pncp_raw_bids — Sundays 06:30 UTC
-- (was daily — change to weekly per story spec)
-- ──────────────────────────────────────────────────────────────────────────
SELECT cron.unschedule('bloat-check-pncp-raw-bids')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'bloat-check-pncp-raw-bids');

SELECT cron.schedule(
    'bloat-check-pncp-raw-bids',
    '30 6 * * 0',
    $$SELECT public.check_pncp_raw_bids_bloat()$$
);


-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║  SECTION 3: INDEX CLEANUP + COMPOSITE INDEXES                         ║
-- ╚══════════════════════════════════════════════════════════════════════════╝

-- ──────────────────────────────────────────────────────────────────────────
-- AC12: Drop redundant indexes
-- ──────────────────────────────────────────────────────────────────────────

-- alert_preferences.user_id is redundant — UNIQUE(user_id) already provides
-- the same index coverage
DROP INDEX IF EXISTS idx_alert_preferences_user_id;

-- google_sheets_exports GIN index on search_params is unused
-- (no queries filter by JSONB search_params)
DROP INDEX IF EXISTS idx_google_sheets_exports_search_params;

-- ──────────────────────────────────────────────────────────────────────────
-- AC13: Trigger rename — ALREADY DONE in 20260331100000
-- All tr_* and trigger_* were renamed to trg_* in that migration.
-- Verification query (should return 0 rows):
--   SELECT tgname FROM pg_trigger
--   WHERE tgname !~ '^(trg_|pg_)' AND NOT tgisinternal;
-- ──────────────────────────────────────────────────────────────────────────

-- ──────────────────────────────────────────────────────────────────────────
-- AC14: Composite indexes
-- ──────────────────────────────────────────────────────────────────────────

-- search_state_transitions(search_id, to_state) — for queries filtering
-- by search_id + specific state transitions
CREATE INDEX IF NOT EXISTS idx_state_transitions_search_id_to_state
    ON public.search_state_transitions (search_id, to_state);

-- classification_feedback(setor_id, created_at DESC) — for time-ordered
-- feedback queries per sector (analytics, retraining)
CREATE INDEX IF NOT EXISTS idx_classification_feedback_setor_created
    ON public.classification_feedback (setor_id, created_at DESC);


-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║  SECTION 4: VERIFICATION + SCHEMA RELOAD                             ║
-- ╚══════════════════════════════════════════════════════════════════════════╝

-- Notify PostgREST to reload schema (picks up new function signatures)
NOTIFY pgrst, 'reload schema';

-- Verification queries (run manually after migration):
-- 1. SECURITY DEFINER without search_path (should be 0):
--    SELECT proname FROM pg_proc
--    WHERE prosecdef = true
--      AND pronamespace = 'public'::regnamespace
--      AND NOT (proconfig @> ARRAY['search_path=public']);
--
-- 2. Retention jobs (should be >= 7):
--    SELECT jobname, schedule, command FROM cron.job
--    WHERE command LIKE '%DELETE%' OR command LIKE '%VACUUM%' OR command LIKE '%bloat%'
--    ORDER BY jobname;
--
-- 3. Trigger naming (should be 0 legacy):
--    SELECT tgname FROM pg_trigger
--    WHERE tgname !~ '^(trg_|pg_)' AND NOT tgisinternal;
