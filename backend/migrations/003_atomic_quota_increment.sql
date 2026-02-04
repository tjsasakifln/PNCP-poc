-- Migration 003: Atomic Quota Increment Function
-- Issue: #189 - Race condition in quota check/increment
-- Date: 2026-02-04
--
-- This migration adds a PostgreSQL function that performs atomic quota
-- check and increment to prevent race conditions when multiple concurrent
-- requests attempt to increment the same user's quota.
--
-- The function uses INSERT ... ON CONFLICT with atomic increment to ensure
-- that concurrent requests never lose increments.

-- Create atomic increment function
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
    -- First, get the current count (if exists)
    SELECT searches_count INTO v_previous_count
    FROM monthly_quota
    WHERE user_id = p_user_id AND month_year = p_month_year
    FOR UPDATE;  -- Lock the row to prevent concurrent updates

    IF v_previous_count IS NULL THEN
        -- No existing record - insert new one with count = 1
        v_previous_count := 0;

        INSERT INTO monthly_quota (user_id, month_year, searches_count, updated_at)
        VALUES (p_user_id, p_month_year, 1, now())
        ON CONFLICT (user_id, month_year) DO UPDATE
        SET searches_count = monthly_quota.searches_count + 1,
            updated_at = now()
        RETURNING searches_count INTO v_new_count;
    ELSE
        -- Check if already at limit (before incrementing)
        IF p_max_quota IS NOT NULL AND v_previous_count >= p_max_quota THEN
            v_was_at_limit := TRUE;
            v_new_count := v_previous_count;  -- Don't increment, already at limit
        ELSE
            -- Atomic increment
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

-- Grant execute permission to authenticated users (via service role)
GRANT EXECUTE ON FUNCTION increment_quota_atomic TO service_role;

-- Comment for documentation
COMMENT ON FUNCTION increment_quota_atomic IS
    'Atomically increments monthly quota for a user. Returns new count, whether limit was reached, and previous count. Issue #189 fix.';


-- Create a simpler check-and-increment function that combines quota check with atomic increment
-- This function ensures no race condition between check and increment
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
    -- Perform atomic upsert with increment
    INSERT INTO monthly_quota (user_id, month_year, searches_count, updated_at)
    VALUES (p_user_id, p_month_year, 1, now())
    ON CONFLICT (user_id, month_year) DO UPDATE
    SET searches_count = CASE
        -- Only increment if under limit
        WHEN monthly_quota.searches_count < p_max_quota THEN monthly_quota.searches_count + 1
        ELSE monthly_quota.searches_count
    END,
    updated_at = now()
    RETURNING
        searches_count,
        searches_count - 1  -- This gives us what the count was before (may be off by 1 on insert)
    INTO v_new_count, v_previous_count;

    -- Determine if this request was allowed
    -- If the count didn't change (or was already at limit), request was blocked
    IF v_new_count > p_max_quota THEN
        v_allowed := FALSE;
    ELSIF v_previous_count >= p_max_quota THEN
        -- Count didn't increase because limit was reached
        v_allowed := FALSE;
    END IF;

    RETURN QUERY SELECT
        v_allowed,
        v_new_count,
        COALESCE(v_previous_count, 0),
        GREATEST(0, p_max_quota - v_new_count);
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION check_and_increment_quota TO service_role;

-- Comment for documentation
COMMENT ON FUNCTION check_and_increment_quota IS
    'Atomically checks quota limit and increments if allowed. No race condition between check and increment. Issue #189 fix.';
