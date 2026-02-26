-- STORY-278 AC1: alert_preferences table for email digest scheduling
-- Stores per-user email alert preferences (frequency, enabled, last sent timestamp)

-- Create frequency enum type
CREATE TYPE alert_frequency AS ENUM ('daily', 'twice_weekly', 'weekly', 'off');

-- Create alert_preferences table
CREATE TABLE IF NOT EXISTS alert_preferences (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  frequency alert_frequency NOT NULL DEFAULT 'daily',
  enabled BOOLEAN NOT NULL DEFAULT true,
  last_digest_sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  CONSTRAINT alert_preferences_user_id_unique UNIQUE (user_id)
);

-- Index for efficient lookups by user_id
CREATE INDEX idx_alert_preferences_user_id ON alert_preferences(user_id);

-- Index for cron job query: enabled users due for digest
CREATE INDEX idx_alert_preferences_digest_due
  ON alert_preferences(enabled, frequency, last_digest_sent_at)
  WHERE enabled = true AND frequency != 'off';

-- RLS: user can only see/edit own preferences
ALTER TABLE alert_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own alert preferences"
  ON alert_preferences FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own alert preferences"
  ON alert_preferences FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own alert preferences"
  ON alert_preferences FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Service role bypass for cron job
CREATE POLICY "Service role full access to alert preferences"
  ON alert_preferences FOR ALL
  USING (auth.role() = 'service_role');

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_alert_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_alert_preferences_updated_at
  BEFORE UPDATE ON alert_preferences
  FOR EACH ROW
  EXECUTE FUNCTION update_alert_preferences_updated_at();

-- Default: create alert_preferences for new users via trigger
CREATE OR REPLACE FUNCTION create_default_alert_preferences()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO alert_preferences (user_id)
  VALUES (NEW.id)
  ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_alert_preferences_on_profile
  AFTER INSERT ON profiles
  FOR EACH ROW
  EXECUTE FUNCTION create_default_alert_preferences();
