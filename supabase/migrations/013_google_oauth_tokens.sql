-- Migration 004: Google OAuth Tokens Storage
-- STORY-180: Google Sheets Export - OAuth Token Management
--
-- This migration creates the infrastructure for storing encrypted OAuth 2.0 tokens
-- for Google Sheets integration. Tokens are encrypted at rest using AES-256.

-- Create user_oauth_tokens table
CREATE TABLE IF NOT EXISTS user_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL CHECK (provider IN ('google', 'microsoft', 'dropbox')),
    access_token TEXT NOT NULL,      -- AES-256 encrypted
    refresh_token TEXT,               -- AES-256 encrypted (nullable for some OAuth flows)
    expires_at TIMESTAMPTZ NOT NULL,
    scope TEXT NOT NULL,              -- e.g., 'https://www.googleapis.com/auth/spreadsheets'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure one OAuth connection per provider per user
    CONSTRAINT unique_user_provider UNIQUE(user_id, provider)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_oauth_tokens_user_id
    ON user_oauth_tokens(user_id);

CREATE INDEX IF NOT EXISTS idx_user_oauth_tokens_expires_at
    ON user_oauth_tokens(expires_at);

CREATE INDEX IF NOT EXISTS idx_user_oauth_tokens_provider
    ON user_oauth_tokens(provider);

-- Enable Row Level Security
ALTER TABLE user_oauth_tokens ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view their own tokens
DROP POLICY IF EXISTS "Users can view own OAuth tokens" ON user_oauth_tokens;
CREATE POLICY "Users can view own OAuth tokens"
    ON user_oauth_tokens
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLS Policy: Users can update their own tokens
DROP POLICY IF EXISTS "Users can update own OAuth tokens" ON user_oauth_tokens;
CREATE POLICY "Users can update own OAuth tokens"
    ON user_oauth_tokens
    FOR UPDATE
    USING (auth.uid() = user_id);

-- RLS Policy: Users can delete their own tokens
DROP POLICY IF EXISTS "Users can delete own OAuth tokens" ON user_oauth_tokens;
CREATE POLICY "Users can delete own OAuth tokens"
    ON user_oauth_tokens
    FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policy: Service role can manage all tokens
DROP POLICY IF EXISTS "Service role can manage all OAuth tokens" ON user_oauth_tokens;
CREATE POLICY "Service role can manage all OAuth tokens"
    ON user_oauth_tokens
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Add comments for documentation
COMMENT ON TABLE user_oauth_tokens IS
    'Stores encrypted OAuth 2.0 tokens for third-party integrations (Google Sheets, etc.). Tokens are encrypted using AES-256 before storage. STORY-180';

COMMENT ON COLUMN user_oauth_tokens.access_token IS
    'AES-256 encrypted access token. NEVER log this value in plaintext. Used to authenticate API calls to OAuth provider.';

COMMENT ON COLUMN user_oauth_tokens.refresh_token IS
    'AES-256 encrypted refresh token. Used to obtain new access tokens when expired. May be NULL for some OAuth flows.';

COMMENT ON COLUMN user_oauth_tokens.expires_at IS
    'Timestamp when access_token expires (UTC). Backend automatically refreshes using refresh_token before expiration.';

COMMENT ON COLUMN user_oauth_tokens.scope IS
    'OAuth scopes granted by user. For Google Sheets: "https://www.googleapis.com/auth/spreadsheets"';
