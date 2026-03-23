-- DEBT Quick Wins — Batch 1
-- DB-H04, DA-02, DB-M04, DB-M05, DA-01, DB-L05, DB-L03, DB-M07, DA-04
-- Idempotent: safe to run multiple times. Zero-downtime compatible.

-- ============================================================================
-- DB-H04 + DA-02: Backfill NULLs and add NOT NULL on timestamp columns
-- classification_feedback.created_at, user_oauth_tokens.created_at/updated_at
-- ============================================================================

-- classification_feedback.created_at: backfill NULLs
UPDATE public.classification_feedback
SET created_at = now()
WHERE created_at IS NULL;

-- Add NOT NULL constraint (idempotent via DO block)
DO $$
BEGIN
    -- classification_feedback.created_at NOT NULL
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'classification_feedback'
          AND column_name = 'created_at'
          AND is_nullable = 'YES'
    ) THEN
        ALTER TABLE public.classification_feedback
            ALTER COLUMN created_at SET NOT NULL;
        RAISE NOTICE 'DB-H04: classification_feedback.created_at set to NOT NULL';
    ELSE
        RAISE NOTICE 'DB-H04: classification_feedback.created_at already NOT NULL or does not exist';
    END IF;
END $$;

-- user_oauth_tokens.created_at: backfill NULLs
UPDATE public.user_oauth_tokens
SET created_at = now()
WHERE created_at IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'user_oauth_tokens'
          AND column_name = 'created_at'
          AND is_nullable = 'YES'
    ) THEN
        ALTER TABLE public.user_oauth_tokens
            ALTER COLUMN created_at SET NOT NULL;
        RAISE NOTICE 'DB-H04: user_oauth_tokens.created_at set to NOT NULL';
    ELSE
        RAISE NOTICE 'DB-H04: user_oauth_tokens.created_at already NOT NULL or does not exist';
    END IF;
END $$;

-- user_oauth_tokens.updated_at: backfill NULLs
UPDATE public.user_oauth_tokens
SET updated_at = COALESCE(created_at, now())
WHERE updated_at IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'user_oauth_tokens'
          AND column_name = 'updated_at'
          AND is_nullable = 'YES'
    ) THEN
        ALTER TABLE public.user_oauth_tokens
            ALTER COLUMN updated_at SET NOT NULL;
        RAISE NOTICE 'DB-H04: user_oauth_tokens.updated_at set to NOT NULL';
    ELSE
        RAISE NOTICE 'DB-H04: user_oauth_tokens.updated_at already NOT NULL or does not exist';
    END IF;
END $$;

-- ============================================================================
-- DB-M04: CHECK constraint on search_sessions.response_state
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.search_sessions'::regclass
          AND conname = 'chk_search_sessions_response_state'
    ) THEN
        ALTER TABLE public.search_sessions
            ADD CONSTRAINT chk_search_sessions_response_state
            CHECK (response_state IN ('live', 'cached', 'degraded', 'empty_failure'));
        RAISE NOTICE 'DB-M04: CHECK constraint on search_sessions.response_state added';
    ELSE
        RAISE NOTICE 'DB-M04: chk_search_sessions_response_state already exists';
    END IF;
END $$;

-- ============================================================================
-- DB-M05: CHECK constraint on search_sessions.pipeline_stage
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.search_sessions'::regclass
          AND conname = 'chk_search_sessions_pipeline_stage'
    ) THEN
        ALTER TABLE public.search_sessions
            ADD CONSTRAINT chk_search_sessions_pipeline_stage
            CHECK (pipeline_stage IN (
                'validate', 'prepare', 'execute', 'filter',
                'enrich', 'generate', 'persist', 'consolidating'
            ));
        RAISE NOTICE 'DB-M05: CHECK constraint on search_sessions.pipeline_stage added';
    ELSE
        RAISE NOTICE 'DB-M05: chk_search_sessions_pipeline_stage already exists';
    END IF;
END $$;

-- ============================================================================
-- DA-01 + DB-L05: Restore priority-aware cache eviction (cold->warm->hot)
-- Regression: DEBT-017 (20260309) overwrote the priority-aware version from
-- migration 032 with a simpler FIFO version and reduced limit from 10 to 5.
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_search_cache_per_user()
RETURNS TRIGGER AS $$
DECLARE
    entry_count INTEGER;
BEGIN
    -- Short-circuit: skip cleanup if user has 10 or fewer entries
    SELECT COUNT(*) INTO entry_count
    FROM search_results_cache
    WHERE user_id = NEW.user_id;

    IF entry_count <= 10 THEN
        RETURN NEW;
    END IF;

    -- Priority-aware eviction: cold first, then warm, then hot
    -- Within same priority, oldest (by last access) evicted first
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- DB-L03: Add COMMENTs on tables missing them
-- ============================================================================

COMMENT ON TABLE public.profiles IS
    'User profiles linked to auth.users. Stores plan_type, display_name, onboarding state, and subscription metadata. Primary source of truth for user plan status (fail-to-last-known-plan pattern).';

COMMENT ON TABLE public.user_subscriptions IS
    'Stripe subscription records. Synced via webhook handlers. subscription_status uses Stripe enum values (active, past_due, canceled, trialing, incomplete, incomplete_expired, unpaid, paused).';

COMMENT ON TABLE public.conversations IS
    'Support conversations between users and admin. Each conversation has a subject, category, and status (open/closed/pending).';

COMMENT ON TABLE public.messages IS
    'Individual messages within conversations. sender_type is either user or admin. Supports unread tracking via is_read flag.';

-- ============================================================================
-- DB-M07: COMMENT documenting subscription_status enum mapping
-- ============================================================================

COMMENT ON COLUMN public.profiles.plan_type IS
    'Current plan ID (free_trial, smartlic_pro, consultoria, etc). Synced from Stripe webhooks. Used as fallback when Supabase CB is open. Must match plans.id.';

COMMENT ON COLUMN public.user_subscriptions.subscription_status IS
    'Stripe subscription status enum: active, past_due, canceled, trialing, incomplete, incomplete_expired, unpaid, paused. Maps to profiles.plan_type via webhook sync — both must agree for correct quota enforcement.';

-- ============================================================================
-- DA-04: Add updated_at column to partners table + auto-update trigger
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'partners'
          AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE public.partners
            ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
        RAISE NOTICE 'DA-04: partners.updated_at column added';
    ELSE
        RAISE NOTICE 'DA-04: partners.updated_at already exists';
    END IF;
END $$;

-- Ensure set_updated_at() function exists (created in earlier migration)
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger (idempotent via DROP IF EXISTS)
DROP TRIGGER IF EXISTS trg_partners_updated_at ON public.partners;
CREATE TRIGGER trg_partners_updated_at
    BEFORE UPDATE ON public.partners
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();
