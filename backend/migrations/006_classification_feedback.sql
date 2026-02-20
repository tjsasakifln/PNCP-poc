-- GTM-RESILIENCE-D05: Classification Feedback table
-- Stores user feedback on search result relevance for continuous improvement

CREATE TABLE IF NOT EXISTS classification_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    search_id UUID NOT NULL,
    bid_id TEXT NOT NULL,
    setor_id TEXT NOT NULL,
    user_verdict TEXT NOT NULL CHECK (user_verdict IN ('false_positive', 'false_negative', 'correct')),
    reason TEXT,
    category TEXT CHECK (category IN ('wrong_sector', 'irrelevant_modality', 'too_small', 'too_large', 'closed', 'other')),
    bid_objeto TEXT,
    bid_valor DECIMAL,
    bid_uf TEXT,
    confidence_score INTEGER,
    relevance_source TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    -- AC5: One feedback per bid per search per user
    UNIQUE (user_id, search_id, bid_id)
);

-- AC2: Index for analysis queries (patterns by sector)
CREATE INDEX IF NOT EXISTS idx_feedback_sector_verdict
    ON classification_feedback (setor_id, user_verdict, created_at);

-- AC2: Index for rate limiting (user activity)
CREATE INDEX IF NOT EXISTS idx_feedback_user_created
    ON classification_feedback (user_id, created_at);

-- AC9: RLS policy — users can only see/insert their own feedback
ALTER TABLE classification_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY feedback_insert_own ON classification_feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY feedback_select_own ON classification_feedback
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY feedback_update_own ON classification_feedback
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY feedback_delete_own ON classification_feedback
    FOR DELETE USING (auth.uid() = user_id);

-- Admin policy for service role (patterns endpoint)
CREATE POLICY feedback_admin_all ON classification_feedback
    FOR ALL USING (auth.role() = 'service_role');
