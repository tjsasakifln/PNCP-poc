-- DEBT-DB-001: Unify subscription_status between user_subscriptions and profiles
--
-- Problem: profiles.subscription_status and user_subscriptions.subscription_status
-- can drift because they have different enum values and no sync mechanism.
--
-- profiles CHECK: trial, active, canceling, past_due, expired
-- user_subscriptions CHECK: active, trialing, past_due, canceled, expired
--
-- Canonical source of truth: user_subscriptions (Stripe-sourced state).
-- profiles.subscription_status is the app-visible fallback used by quota.py.
--
-- This trigger maps user_subscriptions values to profiles values:
--   active    -> active
--   trialing  -> trial
--   past_due  -> past_due
--   canceled  -> canceling
--   expired   -> expired

CREATE OR REPLACE FUNCTION sync_subscription_status_to_profile()
RETURNS TRIGGER AS $$
DECLARE
  mapped_status text;
BEGIN
  -- Map user_subscriptions enum values to profiles enum values
  CASE NEW.subscription_status
    WHEN 'active'   THEN mapped_status := 'active';
    WHEN 'trialing' THEN mapped_status := 'trial';
    WHEN 'past_due' THEN mapped_status := 'past_due';
    WHEN 'canceled' THEN mapped_status := 'canceling';
    WHEN 'expired'  THEN mapped_status := 'expired';
    ELSE mapped_status := NULL;  -- Unknown status, skip update
  END CASE;

  -- Only update if we have a valid mapping and the status actually changed
  IF mapped_status IS NOT NULL THEN
    UPDATE profiles
    SET subscription_status = mapped_status,
        updated_at = now()
    WHERE id = NEW.user_id
      AND (subscription_status IS DISTINCT FROM mapped_status);
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comment documenting the function purpose
COMMENT ON FUNCTION sync_subscription_status_to_profile() IS
  'DEBT-DB-001: Syncs user_subscriptions.subscription_status -> profiles.subscription_status with enum mapping. Source of truth: user_subscriptions.';

-- Create trigger on INSERT and UPDATE of subscription_status
DROP TRIGGER IF EXISTS trg_sync_subscription_status ON user_subscriptions;

CREATE TRIGGER trg_sync_subscription_status
  AFTER INSERT OR UPDATE OF subscription_status
  ON user_subscriptions
  FOR EACH ROW
  EXECUTE FUNCTION sync_subscription_status_to_profile();

-- Add comment to trigger
COMMENT ON TRIGGER trg_sync_subscription_status ON user_subscriptions IS
  'DEBT-DB-001: Keeps profiles.subscription_status in sync with user_subscriptions changes.';
