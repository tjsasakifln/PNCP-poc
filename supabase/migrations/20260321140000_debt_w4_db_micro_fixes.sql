-- DEBT-W4: DB Micro-Fixes (Wave 4)
-- Addresses: DB-012, DB-013, DB-015, DB-016, DB-017, DB-007
-- Idempotent: safe to run multiple times.
--
-- Summary:
-- DB-012: Tighten organizations.plan_type CHECK to match actual plan enum
-- DB-013: pg_cron job to purge reconciliation_log older than 90 days
-- DB-015: COMMENT ON CONSTRAINT documenting ON DELETE RESTRICT on legacy plan FKs
-- DB-016: CHECK constraint on search_sessions.error_code (SearchErrorCode enum)
-- DB-017: Stagger existing 4:00 UTC pg_cron cluster (already staggered; add new job at 4:30)
-- DB-007: Improve handle_new_user() error message — TOCTOU race note

-- ============================================================================
-- DB-012: Tighten organizations.plan_type CHECK
--
-- The existing chk_organizations_plan_type (added in DEBT-100) is too broad:
-- it allows ghost values like 'pro', 'free', 'avulso', 'pack', 'monthly',
-- 'annual' which are not real plan IDs in the plans table.
--
-- Authoritative plan IDs (from plans seed + profiles CHECK constraint):
--   free_trial, consultor_agil, maquina, sala_guerra, master,
--   smartlic_pro, consultoria
--
-- organizations can only be on multi-user plans, but we keep all plan IDs
-- for FK-compatibility (orgs may mirror the profiles.plan_type set).
-- ============================================================================

DO $$
BEGIN
    -- Drop the overly-broad constraint added by DEBT-100 (DB-021)
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.organizations'::regclass
          AND conname = 'chk_organizations_plan_type'
    ) THEN
        ALTER TABLE public.organizations
            DROP CONSTRAINT chk_organizations_plan_type;
        RAISE NOTICE 'DB-012: Dropped overly-broad chk_organizations_plan_type';
    END IF;

    -- Add tightened constraint matching actual plan enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.organizations'::regclass
          AND conname = 'chk_organizations_plan_type_v2'
    ) THEN
        ALTER TABLE public.organizations
            ADD CONSTRAINT chk_organizations_plan_type_v2
            CHECK (plan_type IN (
                'free_trial',
                'consultor_agil',
                'maquina',
                'sala_guerra',
                'master',
                'smartlic_pro',
                'consultoria'
            ));
        RAISE NOTICE 'DB-012: Added tightened chk_organizations_plan_type_v2 (7 valid plan IDs)';
    ELSE
        RAISE NOTICE 'DB-012: chk_organizations_plan_type_v2 already exists — skipping';
    END IF;
END $$;


-- ============================================================================
-- DB-013: pg_cron job — purge reconciliation_log older than 90 days
--
-- reconciliation_log grows ~1 row/day (Stripe reconciliation runs daily).
-- 90-day window covers 3 billing cycles for auditing.
-- Staggered to 4:30 UTC (within the existing 4:00-4:30 cluster window).
-- ============================================================================

SELECT cron.unschedule('cleanup-reconciliation-log')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-reconciliation-log');

SELECT cron.schedule(
    'cleanup-reconciliation-log',
    '30 4 * * *',
    $$DELETE FROM public.reconciliation_log WHERE created_at < now() - interval '90 days'$$
);


-- ============================================================================
-- DB-015: COMMENT ON CONSTRAINT — document intentional ON DELETE RESTRICT
--         on legacy plan FKs
--
-- user_subscriptions.plan_id -> plans(id) ON DELETE RESTRICT is intentional:
-- prevents accidental deletion of plans that have historical subscription rows.
-- To retire a plan: set plans.is_active = false (soft delete), never hard-delete.
-- ============================================================================

-- Note: COMMENT ON CONSTRAINT ... ON TABLE syntax requires the constraint to exist.
-- The FK was created by the initial schema migration (001_profiles_and_sessions.sql
-- or equivalent). We add/replace the comment idempotently.

DO $$
BEGIN
    -- user_subscriptions plan FK
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.user_subscriptions'::regclass
          AND conname = 'user_subscriptions_plan_id_fkey'
    ) THEN
        COMMENT ON CONSTRAINT user_subscriptions_plan_id_fkey ON public.user_subscriptions IS
            'INTENTIONAL ON DELETE RESTRICT: prevents hard-deleting a plan that has '
            'historical or active subscription rows. To retire a plan, set '
            'plans.is_active = false (soft delete). Hard delete is never safe. '
            'DB-015 — added Wave 4 2026-03-21.';
        RAISE NOTICE 'DB-015: COMMENT added to user_subscriptions_plan_id_fkey';
    ELSE
        RAISE NOTICE 'DB-015: user_subscriptions_plan_id_fkey not found — skipping comment';
    END IF;
END $$;


-- ============================================================================
-- DB-016: CHECK constraint on search_sessions.error_code
--
-- error_code maps to the SearchErrorCode / ErrorCode enum in error_response.py:
--   SOURCE_UNAVAILABLE, ALL_SOURCES_FAILED, TIMEOUT, RATE_LIMIT,
--   QUOTA_EXCEEDED, VALIDATION_ERROR, INTERNAL_ERROR,
--   AUTH_ERROR, FORBIDDEN, NOT_FOUND, CONFLICT,
--   SERVICE_UNAVAILABLE, BILLING_ERROR
--
-- NULL is allowed (no error = no code).
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.search_sessions'::regclass
          AND conname = 'chk_search_sessions_error_code'
    ) THEN
        ALTER TABLE public.search_sessions
            ADD CONSTRAINT chk_search_sessions_error_code
            CHECK (error_code IS NULL OR error_code IN (
                -- Original CRIT-009 search/pipeline codes
                'SOURCE_UNAVAILABLE',
                'ALL_SOURCES_FAILED',
                'TIMEOUT',
                'RATE_LIMIT',
                'QUOTA_EXCEEDED',
                'VALIDATION_ERROR',
                'INTERNAL_ERROR',
                -- SYS-011 cross-cutting codes
                'AUTH_ERROR',
                'FORBIDDEN',
                'NOT_FOUND',
                'CONFLICT',
                'SERVICE_UNAVAILABLE',
                'BILLING_ERROR'
            ));
        RAISE NOTICE 'DB-016: CHECK constraint chk_search_sessions_error_code added (13 valid codes + NULL)';
    ELSE
        RAISE NOTICE 'DB-016: chk_search_sessions_error_code already exists — skipping';
    END IF;
END $$;


-- ============================================================================
-- DB-017: pg_cron job schedule audit
--
-- The existing cluster (from 20260308310000_debt009_retention_pgcron_jobs.sql
-- and 20260309200000_debt100_db_quick_wins.sql) is already correctly staggered:
--
--   4:00 UTC  — search_state_transitions (30d)
--   4:05 UTC  — alert_sent_items         (180d)
--   4:10 UTC  — health_checks            (30d)
--   4:15 UTC  — incidents                (90d)
--   4:20 UTC  — mfa_recovery_attempts    (30d)
--   4:25 UTC  — alert_runs               (90d)
--   4:30 UTC  — reconciliation_log       (90d)  ← added by DB-013 above
--   4:30 UTC  — search_sessions          (12mo) ← from DEBT-100
--
-- search_sessions and reconciliation_log both run at 4:30 UTC. Stagger
-- search_sessions to 4:35 UTC to avoid simultaneous I/O.
-- ============================================================================

SELECT cron.unschedule('cleanup-old-search-sessions')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-old-search-sessions');

SELECT cron.schedule(
    'cleanup-old-search-sessions',
    '35 4 * * *',
    $$DELETE FROM public.search_sessions WHERE created_at < now() - interval '12 months'$$
);


-- ============================================================================
-- DB-007: Improve handle_new_user() — TOCTOU note + cleaner error handling
--
-- The phone_whatsapp partial unique index enforces uniqueness only at the
-- DB level. Between the application-level uniqueness check and the INSERT,
-- a concurrent signup with the same phone can slip through. This is a
-- TOCTOU (time-of-check/time-of-use) race. We handle it by catching the
-- unique violation and setting phone_whatsapp = NULL (not failing the signup).
-- The original trigger did no such handling — a duplicate phone on signup
-- would silently fail the trigger (ON CONFLICT (id) DO NOTHING swallowed it).
--
-- This version adds an EXCEPTION block to gracefully handle phone uniqueness
-- conflicts without breaking the signup flow.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
DECLARE
  _phone text;
BEGIN
  -- Normalize phone number: strip non-digits, remove country code +55,
  -- remove leading 0, reject if not 10 or 11 digits.
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
      -- TOCTOU race: two concurrent signups with the same phone_whatsapp.
      -- The unique partial index (idx_profiles_phone_whatsapp_unique) fires
      -- after our application-level check. To avoid blocking signup, retry
      -- the insert with phone_whatsapp = NULL (graceful degradation).
      -- DB-007: this race is rare but real in high-concurrency environments.
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
        NULL,  -- phone cleared to resolve uniqueness conflict
        COALESCE((NEW.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
        'free_trial',
        NEW.raw_user_meta_data->>'avatar_url',
        '{}'::jsonb
      )
      ON CONFLICT (id) DO NOTHING;
  END;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
