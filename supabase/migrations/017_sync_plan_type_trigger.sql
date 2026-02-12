-- STORY-202 DB-M04: Auto-sync profiles.plan_type when user_subscriptions changes
-- This eliminates drift between user_subscriptions.plan_id and profiles.plan_type

CREATE OR REPLACE FUNCTION sync_profile_plan_type()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if the subscription is active or trialing
    IF NEW.status IN ('active', 'trialing') THEN
        UPDATE profiles
        SET plan_type = NEW.plan_id,
            updated_at = NOW()
        WHERE id = NEW.user_id;

        RAISE LOG 'sync_profile_plan_type: Updated user % plan to %', NEW.user_id, NEW.plan_id;
    END IF;

    -- Handle cancellation/expiry — revert to free_trial
    IF NEW.status IN ('canceled', 'expired', 'past_due') THEN
        UPDATE profiles
        SET plan_type = 'free_trial',
            updated_at = NOW()
        WHERE id = NEW.user_id;

        RAISE LOG 'sync_profile_plan_type: Reverted user % to free_trial (status=%)', NEW.user_id, NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on INSERT and UPDATE of user_subscriptions
DROP TRIGGER IF EXISTS trg_sync_profile_plan_type ON user_subscriptions;
CREATE TRIGGER trg_sync_profile_plan_type
    AFTER INSERT OR UPDATE ON user_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION sync_profile_plan_type();

-- Comment for documentation
COMMENT ON FUNCTION sync_profile_plan_type() IS
    'STORY-202 DB-M04: Auto-sync profiles.plan_type from user_subscriptions changes';
