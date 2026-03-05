-- CRIT: Restore check_and_increment_quota RPC function
-- Root cause: Legacy migration 003_atomic_quota_increment.sql was never applied
-- by Supabase CLI (no timestamp prefix). This causes PGRST202 errors which
-- trip the circuit breaker, cascading into PDF 404s and hidden Excel buttons.
--
-- Also restores increment_quota_atomic (used as fallback in quota.py).

-- 1. Atomic increment function (used by fallback path)
CREATE OR REPLACE FUNCTION increment_quota_atomic(
    p_user_id UUID,
    p_month_year VARCHAR(7),
    p_max_quota INT DEFAULT NULL
)
RETURNS TABLE(
    new_count INT,
    was_at_limit BOOLEAN,
    previous_count INT
) AS $$
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
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION increment_quota_atomic TO service_role;

-- 2. Check-and-increment function (primary path used by quota.py)
CREATE OR REPLACE FUNCTION check_and_increment_quota(
    p_user_id UUID,
    p_month_year VARCHAR(7),
    p_max_quota INT
)
RETURNS TABLE(
    allowed BOOLEAN,
    new_count INT,
    previous_count INT,
    quota_remaining INT
) AS $$
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
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION check_and_increment_quota TO service_role;

-- 3. Send schema reload to PostgREST
NOTIFY pgrst, 'reload schema';
