-- Migration 002: Monthly Quota Table for Plan-Based Pricing
-- Story: PNCP-165
-- Date: 2026-02-03

-- Create monthly_quota table
CREATE TABLE IF NOT EXISTS monthly_quota (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    month_year VARCHAR(7) NOT NULL,  -- Format: "2026-02"
    searches_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_user_month UNIQUE(user_id, month_year)
);

-- Create index for fast lookups (IF NOT EXISTS requires PG 9.5+)
CREATE INDEX IF NOT EXISTS idx_monthly_quota_user_month ON monthly_quota(user_id, month_year);

-- Enable Row Level Security
ALTER TABLE monthly_quota ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view their own quota
-- Drop first to make idempotent (CREATE POLICY has no IF NOT EXISTS)
DROP POLICY IF EXISTS "Users can view own quota" ON monthly_quota;
CREATE POLICY "Users can view own quota" ON monthly_quota
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLS Policy: API service role can manage all quota
DROP POLICY IF EXISTS "Service role can manage quota" ON monthly_quota;
CREATE POLICY "Service role can manage quota" ON monthly_quota
    FOR ALL
    USING (true);

-- Comment for documentation
COMMENT ON TABLE monthly_quota IS 'Tracks monthly search quota usage per user for plan-based pricing (STORY-165)';
COMMENT ON COLUMN monthly_quota.month_year IS 'Month key in YYYY-MM format for lazy reset logic';
COMMENT ON COLUMN monthly_quota.searches_count IS 'Number of searches performed in this month';

-- Example query: Get current month quota for a user
-- SELECT searches_count FROM monthly_quota
-- WHERE user_id = 'uuid-here' AND month_year = to_char(now(), 'YYYY-MM');
