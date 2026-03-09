-- DEBT-017: Database Long-Term Optimization
-- Addresses: DB-004, DB-009, DB-014, DB-016, DB-017, DB-020, DB-022, DB-023,
--            DB-024, DB-029, DB-034, DB-035, DB-044, DB-046, DB-050
-- Idempotent: safe to run multiple times.

-- ============================================================================
-- AC4: NOT NULL DEFAULT now() on created_at columns (DB-017)
-- ============================================================================

-- google_sheets_exports.created_at: add NOT NULL constraint
DO $$
BEGIN
    -- First ensure no NULLs exist
    UPDATE google_sheets_exports SET created_at = now() WHERE created_at IS NULL;
    -- Add NOT NULL constraint
    ALTER TABLE google_sheets_exports ALTER COLUMN created_at SET NOT NULL;
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'google_sheets_exports.created_at NOT NULL already set or error: %', SQLERRM;
END $$;

-- partners.created_at: add NOT NULL constraint
DO $$
BEGIN
    UPDATE partners SET created_at = now() WHERE created_at IS NULL;
    ALTER TABLE partners ALTER COLUMN created_at SET NOT NULL;
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'partners.created_at NOT NULL already set or error: %', SQLERRM;
END $$;

-- ============================================================================
-- AC3: Deprecate plans.stripe_price_id legacy column (DB-014)
-- ============================================================================

-- Mark column as deprecated via SQL COMMENT (cannot remove yet — billing.py fallback uses it)
COMMENT ON COLUMN plans.stripe_price_id IS
    'DEPRECATED (DEBT-017/DB-014): Legacy column. Use stripe_price_id_monthly/semiannual/annual or plan_billing_periods.stripe_price_id instead. Kept as fallback in billing.py checkout flow. Remove after billing code migration.';

-- ============================================================================
-- AC6: Cleanup trigger short-circuit optimization (DB-034)
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_search_cache_per_user()
RETURNS TRIGGER AS $$
DECLARE
    entry_count INTEGER;
BEGIN
    -- Short-circuit: skip cleanup if user has 5 or fewer entries (DB-034)
    SELECT COUNT(*) INTO entry_count
    FROM search_results_cache
    WHERE user_id = NEW.user_id;

    IF entry_count <= 5 THEN
        RETURN NEW;
    END IF;

    -- Delete oldest entries beyond the 5 most recent for this user
    DELETE FROM search_results_cache
    WHERE id IN (
        SELECT id FROM search_results_cache
        WHERE user_id = NEW.user_id
        ORDER BY created_at DESC
        OFFSET 5
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- AC7: Rewrite conversations query as LEFT JOIN (DB-035)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_conversations_with_unread_count(
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
) AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_conversations_with_unread_count IS
    'STORY-202 DB-M06 + DEBT-017/DB-035: Uses LEFT JOIN LATERAL instead of correlated subquery for unread count';

-- ============================================================================
-- DB-016: Document valid search_sessions.status transitions
-- ============================================================================

COMMENT ON COLUMN search_sessions.status IS
    'Valid transitions (enforced in search_state_manager.py):
     created -> processing -> consolidating -> completed
     created -> processing -> consolidating -> partial
     created -> processing -> error
     created -> processing -> timeout
     Any -> cancelled (user-initiated)
     Note: DB-level enforcement NOT added (app-layer state machine is the correct pattern for complex FSMs)';

-- ============================================================================
-- DB-020: Document naming convention for constraints
-- ============================================================================

COMMENT ON SCHEMA public IS
    'SmartLic schema. Constraint naming convention (DEBT-017/DB-020): chk_{table}_{column} for CHECK constraints, fk_{table}_{column} for foreign keys, uq_{table}_{column} for unique constraints, idx_{table}_{column} for indexes. Legacy constraints retain original names.';

-- ============================================================================
-- DB-050: Evaluate FK for search_state_transitions
-- ============================================================================

-- NOTE: Cannot add FK because search_sessions.search_id is nullable and not UNIQUE.
-- Adding UNIQUE would break the table since multiple sessions can share a search_id
-- (e.g., retries). Instead, document the relationship and rely on app-layer integrity.
COMMENT ON COLUMN search_state_transitions.search_id IS
    'UUID correlating with search_sessions.search_id. No FK constraint because search_sessions.search_id is nullable and not unique (retries share IDs). App-layer integrity enforced in search_state_manager.py. Orphan cleanup via pg_cron retention job (DEBT-017/DB-050).';

-- ============================================================================
-- DB-024: Add updated_at to plan_billing_periods
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plan_billing_periods'
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE plan_billing_periods
            ADD COLUMN updated_at TIMESTAMPTZ DEFAULT now();
        -- Add trigger for auto-update
        CREATE TRIGGER trg_plan_billing_periods_updated_at
            BEFORE UPDATE ON plan_billing_periods
            FOR EACH ROW
            EXECUTE FUNCTION set_updated_at();
    END IF;
END $$;

-- ============================================================================
-- Reload PostgREST schema cache
-- ============================================================================
NOTIFY pgrst, 'reload schema';
