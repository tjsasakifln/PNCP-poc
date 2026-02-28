-- STORY-317: MFA Recovery Codes table
-- Stores bcrypt-hashed recovery codes for TOTP MFA backup authentication

CREATE TABLE IF NOT EXISTS mfa_recovery_codes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,
    used_at TIMESTAMPTZ DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Index for fast lookup by user_id (recovery code verification)
CREATE INDEX IF NOT EXISTS idx_mfa_recovery_codes_user_id
    ON mfa_recovery_codes(user_id);

-- Index for cleanup of used codes
CREATE INDEX IF NOT EXISTS idx_mfa_recovery_codes_used_at
    ON mfa_recovery_codes(used_at) WHERE used_at IS NOT NULL;

-- RLS policies
ALTER TABLE mfa_recovery_codes ENABLE ROW LEVEL SECURITY;

-- Users can only read their own recovery codes (used_at status)
CREATE POLICY "Users can view own recovery codes"
    ON mfa_recovery_codes FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Service role can insert/update/delete (backend manages codes)
CREATE POLICY "Service role full access to recovery codes"
    ON mfa_recovery_codes FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Brute force tracking table
CREATE TABLE IF NOT EXISTS mfa_recovery_attempts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    attempted_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    success BOOLEAN DEFAULT false NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mfa_recovery_attempts_user_id_time
    ON mfa_recovery_attempts(user_id, attempted_at DESC);

ALTER TABLE mfa_recovery_attempts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access to recovery attempts"
    ON mfa_recovery_attempts FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
