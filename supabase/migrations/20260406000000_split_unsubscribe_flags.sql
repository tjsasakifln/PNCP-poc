-- Zero-churn P2 §1.2: Separate marketing vs conversion email preferences
-- Users who unsubscribe from marketing emails should still receive critical
-- trial conversion emails (Day 7 paywall, Day 10 value, Day 13 last day, Day 16 comeback).

ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS trial_conversion_emails_enabled boolean DEFAULT true;

COMMENT ON COLUMN profiles.trial_conversion_emails_enabled IS
  'Controls critical trial deadline/conversion emails (Day 7/10/13/16). Separate from marketing_emails_enabled.';
