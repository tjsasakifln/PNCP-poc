-- STORY-266 AC14-AC15: Trial email log for idempotent reminder delivery
-- Tracks which trial emails have been sent to prevent duplicates.

CREATE TABLE IF NOT EXISTS trial_email_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    email_type TEXT NOT NULL,  -- midpoint, expiring, last_day, expired
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, email_type)
);

-- AC15: RLS — service_role only (backend accesses via service key)
ALTER TABLE trial_email_log ENABLE ROW LEVEL SECURITY;

-- No user-facing policies: only service_role (bypasses RLS) can read/write.
-- This ensures the table is only accessible from the backend.

-- Index for efficient lookups by user_id
CREATE INDEX IF NOT EXISTS idx_trial_email_log_user_id ON trial_email_log(user_id);

-- Comment for documentation
COMMENT ON TABLE trial_email_log IS 'STORY-266: Tracks trial reminder emails sent to prevent duplicates';
COMMENT ON COLUMN trial_email_log.email_type IS 'One of: midpoint, expiring, last_day, expired';
