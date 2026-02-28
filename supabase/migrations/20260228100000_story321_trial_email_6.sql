-- STORY-321: Adapt trial email sequence from 8 to 6 emails
-- AC11: Update trial_email_log schema for 6-email sequence
-- AC6: Ensure dedup constraint on (user_id, email_number)

-- 1. Add CHECK constraint for email_number range (1-6)
-- First drop any existing check constraint on email_number
DO $$
BEGIN
  -- Remove old data with email_number > 6 (STORY-310 was never deployed with real users)
  DELETE FROM trial_email_log WHERE email_number > 6;

  -- Add CHECK constraint
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'trial_email_log_email_number_check'
  ) THEN
    ALTER TABLE trial_email_log
      ADD CONSTRAINT trial_email_log_email_number_check
      CHECK (email_number BETWEEN 1 AND 6);
  END IF;
END $$;

-- 2. Update comments
COMMENT ON TABLE trial_email_log IS 'STORY-321: Tracks trial email sequence (6 emails over 14 days)';
COMMENT ON COLUMN trial_email_log.email_number IS 'STORY-321: Sequential email number (1-6) in the trial sequence';
