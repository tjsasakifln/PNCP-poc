-- Migration 005: Google Sheets Export History
-- STORY-180: Google Sheets Export - Export History Tracking
--
-- This migration creates the infrastructure for tracking Google Sheets exports.
-- Enables audit trail, "re-open last export", and usage analytics.

-- Create google_sheets_exports table
CREATE TABLE IF NOT EXISTS google_sheets_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    spreadsheet_id VARCHAR(255) NOT NULL,
    spreadsheet_url TEXT NOT NULL,
    search_params JSONB NOT NULL,     -- Snapshot of search parameters (UFs, dates, setor, keywords)
    total_rows INT NOT NULL CHECK (total_rows >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_google_sheets_exports_user_id
    ON google_sheets_exports(user_id);

CREATE INDEX IF NOT EXISTS idx_google_sheets_exports_created_at
    ON google_sheets_exports(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_google_sheets_exports_spreadsheet_id
    ON google_sheets_exports(spreadsheet_id);

-- GIN index for JSONB search_params (enables efficient JSONB queries)
CREATE INDEX IF NOT EXISTS idx_google_sheets_exports_search_params
    ON google_sheets_exports USING GIN(search_params);

-- Enable Row Level Security
ALTER TABLE google_sheets_exports ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view their own exports
DROP POLICY IF EXISTS "Users can view own Google Sheets exports" ON google_sheets_exports;
CREATE POLICY "Users can view own Google Sheets exports"
    ON google_sheets_exports
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own exports
DROP POLICY IF EXISTS "Users can create Google Sheets exports" ON google_sheets_exports;
CREATE POLICY "Users can create Google Sheets exports"
    ON google_sheets_exports
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update their own exports
DROP POLICY IF EXISTS "Users can update own Google Sheets exports" ON google_sheets_exports;
CREATE POLICY "Users can update own Google Sheets exports"
    ON google_sheets_exports
    FOR UPDATE
    USING (auth.uid() = user_id);

-- RLS Policy: Service role can manage all exports
DROP POLICY IF EXISTS "Service role can manage all Google Sheets exports" ON google_sheets_exports;
CREATE POLICY "Service role can manage all Google Sheets exports"
    ON google_sheets_exports
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Add comments for documentation
COMMENT ON TABLE google_sheets_exports IS
    'Tracks all Google Sheets exports for audit trail and usage analytics. Enables "re-open last export" and search reproducibility. STORY-180';

COMMENT ON COLUMN google_sheets_exports.spreadsheet_id IS
    'Google Sheets spreadsheet ID (from URL: docs.google.com/spreadsheets/d/{spreadsheet_id})';

COMMENT ON COLUMN google_sheets_exports.spreadsheet_url IS
    'Full shareable URL to the Google Sheets spreadsheet. Used to re-open exports.';

COMMENT ON COLUMN google_sheets_exports.search_params IS
    'JSONB snapshot of search parameters used for this export. Example: {"ufs": ["SP", "RJ"], "dataInicial": "2026-01-01", "setor": "Vestuário e Uniformes"}. Enables search reproducibility and analytics.';

COMMENT ON COLUMN google_sheets_exports.total_rows IS
    'Number of licitações exported to this spreadsheet. Used for usage analytics and quota tracking.';

COMMENT ON COLUMN google_sheets_exports.last_updated_at IS
    'Timestamp of last update to this spreadsheet (for "update existing spreadsheet" mode). Differs from created_at for updated exports.';
