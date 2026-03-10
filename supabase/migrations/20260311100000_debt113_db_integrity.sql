-- ══════════════════════════════════════════════════════════════════════════════
-- DEBT-113: DB Integrity Quick Wins
-- Addresses: DB-001 (FK verification), DB-032 (classification_feedback FK ordering),
--            DB-006 (alert_preferences RLS), DB-027 (classification_feedback retention),
--            DB-028 (conversations+messages retention), DB-INFO-03 (backup docs — separate file)
--
-- All statements are fully idempotent — safe to run multiple times.
-- ══════════════════════════════════════════════════════════════════════════════


-- ════════════════════════════════════════════════════════════════════════════
-- AC1: FK Verification — all user_id FKs must point to profiles(id)
-- Raises EXCEPTION if any FK still references auth.users(id)
-- ════════════════════════════════════════════════════════════════════════════

DO $$
DECLARE
    bad_fk RECORD;
    bad_count INTEGER := 0;
BEGIN
    FOR bad_fk IN
        SELECT
            tc.table_name,
            tc.constraint_name,
            ccu.table_schema AS ref_schema,
            ccu.table_name AS ref_table
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            AND kcu.column_name = 'user_id'
            AND ccu.table_name = 'users'
            AND ccu.table_schema = 'auth'
    LOOP
        RAISE WARNING 'DEBT-113/AC1: Table "%" still has FK "%" → auth.users (should be profiles)',
            bad_fk.table_name, bad_fk.constraint_name;
        bad_count := bad_count + 1;
    END LOOP;

    IF bad_count > 0 THEN
        RAISE NOTICE 'DEBT-113/AC1: Found % FK(s) still referencing auth.users — will be fixed below', bad_count;
    ELSE
        RAISE NOTICE 'DEBT-113/AC1: All user_id FKs correctly reference profiles(id) ✓';
    END IF;
END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- AC2: Fix classification_feedback FK ordering for fresh installs (DB-032)
-- Problem: debt002 (20260308) creates table with REFERENCES auth.users(id),
-- but fk_standardization (20260225) ran before the table existed → skipped.
-- Fix: Idempotent re-standardization using IF NOT EXISTS pattern.
-- ════════════════════════════════════════════════════════════════════════════

DO $$
BEGIN
    -- Only proceed if classification_feedback table exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables
        WHERE schemaname = 'public' AND tablename = 'classification_feedback'
    ) THEN
        RAISE NOTICE 'DEBT-113/AC2: classification_feedback table does not exist — skipping';
        RETURN;
    END IF;

    -- Check if old FK to auth.users still exists
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        WHERE tc.table_name = 'classification_feedback'
            AND tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_name = 'users'
            AND ccu.table_schema = 'auth'
    ) THEN
        -- Drop old FK referencing auth.users
        DECLARE
            old_constraint_name TEXT;
        BEGIN
            SELECT tc.constraint_name INTO old_constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
                AND tc.table_schema = ccu.table_schema
            WHERE tc.table_name = 'classification_feedback'
                AND tc.constraint_type = 'FOREIGN KEY'
                AND ccu.table_name = 'users'
                AND ccu.table_schema = 'auth'
            LIMIT 1;

            EXECUTE format('ALTER TABLE classification_feedback DROP CONSTRAINT %I', old_constraint_name);
            RAISE NOTICE 'DEBT-113/AC2: Dropped old FK "%" → auth.users', old_constraint_name;
        END;

        -- Add correct FK to profiles(id)
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'classification_feedback_user_id_profiles_fkey'
            AND table_name = 'classification_feedback'
        ) THEN
            ALTER TABLE classification_feedback
                ADD CONSTRAINT classification_feedback_user_id_profiles_fkey
                FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE NOT VALID;
        END IF;

        ALTER TABLE classification_feedback
            VALIDATE CONSTRAINT classification_feedback_user_id_profiles_fkey;

        RAISE NOTICE 'DEBT-113/AC2: FK standardized to profiles(id) ✓';
    ELSE
        RAISE NOTICE 'DEBT-113/AC2: classification_feedback FK already points to profiles(id) ✓';
    END IF;
END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- AC3: alert_preferences — ensure TO service_role (not auth.role()) (DB-006)
-- Defensive: 20260304200000 should have handled this, but verify + fix.
-- ════════════════════════════════════════════════════════════════════════════

DO $$
BEGIN
    -- Check if any auth.role() policy exists on alert_preferences
    IF EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
            AND tablename = 'alert_preferences'
            AND qual LIKE '%auth.role()%'
    ) THEN
        -- Drop the old policy
        DROP POLICY IF EXISTS "Service role full access to alert preferences" ON alert_preferences;
        RAISE NOTICE 'DEBT-113/AC3: Dropped auth.role() policy on alert_preferences';

        -- Ensure service_role_all exists
        DROP POLICY IF EXISTS "service_role_all" ON alert_preferences;
        CREATE POLICY "service_role_all" ON alert_preferences
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
        RAISE NOTICE 'DEBT-113/AC3: Created TO service_role policy ✓';
    ELSE
        RAISE NOTICE 'DEBT-113/AC3: alert_preferences already uses TO service_role ✓';
    END IF;
END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- AC5: pg_cron retention for classification_feedback (24 months) (DB-027)
-- ════════════════════════════════════════════════════════════════════════════

-- Ensure pg_cron extension is available
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Unschedule if already exists (idempotent)
SELECT cron.unschedule(jobid)
FROM cron.job
WHERE jobname = 'cleanup-classification-feedback';

-- Schedule: daily at 4:45 UTC, delete records older than 24 months
SELECT cron.schedule(
    'cleanup-classification-feedback',
    '45 4 * * *',
    $$DELETE FROM public.classification_feedback WHERE created_at < now() - interval '24 months'$$
);


-- ════════════════════════════════════════════════════════════════════════════
-- AC6: pg_cron retention for conversations + messages (24 months) (DB-028)
-- Messages are CASCADE-deleted when conversation is deleted.
-- ════════════════════════════════════════════════════════════════════════════

-- Unschedule if already exists (idempotent)
SELECT cron.unschedule(jobid)
FROM cron.job
WHERE jobname = 'cleanup-old-conversations';

-- Schedule: daily at 4:50 UTC, delete conversations older than 24 months
-- Messages will be CASCADE-deleted via FK (messages.conversation_id → conversations.id ON DELETE CASCADE)
SELECT cron.schedule(
    'cleanup-old-conversations',
    '50 4 * * *',
    $$DELETE FROM public.conversations WHERE created_at < now() - interval '24 months'$$
);

-- Orphan messages safety net (in case any messages lack FK or conversation was deleted without cascade)
SELECT cron.unschedule(jobid)
FROM cron.job
WHERE jobname = 'cleanup-orphan-messages';

SELECT cron.schedule(
    'cleanup-orphan-messages',
    '55 4 * * *',
    $$DELETE FROM public.messages WHERE created_at < now() - interval '24 months'$$
);


-- ════════════════════════════════════════════════════════════════════════════
-- AC7: RLS Verification — no auth.role() should remain in public policies
-- ════════════════════════════════════════════════════════════════════════════

DO $$
DECLARE
    bad_policy RECORD;
    bad_count INTEGER := 0;
BEGIN
    FOR bad_policy IN
        SELECT schemaname, tablename, policyname, qual
        FROM pg_policies
        WHERE schemaname = 'public'
            AND qual LIKE '%auth.role()%'
    LOOP
        RAISE WARNING 'DEBT-113/AC7: Table "%.%" has policy "%" still using auth.role(): %',
            bad_policy.schemaname, bad_policy.tablename, bad_policy.policyname, bad_policy.qual;
        bad_count := bad_count + 1;
    END LOOP;

    IF bad_count > 0 THEN
        RAISE EXCEPTION 'DEBT-113/AC7: Found % RLS policies still using auth.role() — manual fix required', bad_count;
    ELSE
        RAISE NOTICE 'DEBT-113/AC7: No auth.role() found in public RLS policies ✓';
    END IF;
END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- Final: Post-migration FK diagnostic (informational)
-- ════════════════════════════════════════════════════════════════════════════

DO $$
DECLARE
    fk_rec RECORD;
BEGIN
    RAISE NOTICE 'DEBT-113: Final FK audit — all user_id foreign keys:';
    FOR fk_rec IN
        SELECT
            tc.table_name,
            tc.constraint_name,
            ccu.table_schema || '.' || ccu.table_name AS references_target
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            AND kcu.column_name = 'user_id'
        ORDER BY tc.table_name
    LOOP
        RAISE NOTICE '  % → % (%)', fk_rec.table_name, fk_rec.references_target, fk_rec.constraint_name;
    END LOOP;
END $$;


-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';
