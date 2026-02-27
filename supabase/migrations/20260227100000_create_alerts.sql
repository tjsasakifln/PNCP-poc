-- STORY-301: Email Alert System — alerts + alert_sent_items tables
-- AC19: alerts table (id, user_id, name, filters JSONB, active, created_at, updated_at)
-- AC20: alert_sent_items table (alert_id, item_id, sent_at) — dedup tracking
-- AC21: RLS: user can only see their own alerts

-- ============================================================================
-- 1. alerts table
-- ============================================================================

CREATE TABLE IF NOT EXISTS alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL DEFAULT '',
  filters JSONB NOT NULL DEFAULT '{}'::jsonb,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

COMMENT ON TABLE alerts IS 'STORY-301: User-defined email alerts with search filters';
COMMENT ON COLUMN alerts.filters IS 'JSONB: {setor, ufs[], valor_min, valor_max, keywords[]}';

-- Indexes
CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_active ON alerts(user_id, active) WHERE active = true;

-- RLS
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own alerts"
  ON alerts FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own alerts"
  ON alerts FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own alerts"
  ON alerts FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own alerts"
  ON alerts FOR DELETE
  USING (auth.uid() = user_id);

CREATE POLICY "Service role full access to alerts"
  ON alerts FOR ALL
  TO service_role
  USING (true) WITH CHECK (true);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_alerts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_alerts_updated_at
  BEFORE UPDATE ON alerts
  FOR EACH ROW
  EXECUTE FUNCTION update_alerts_updated_at();

-- ============================================================================
-- 2. alert_sent_items table (dedup tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS alert_sent_items (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  alert_id UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
  item_id TEXT NOT NULL,
  sent_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

COMMENT ON TABLE alert_sent_items IS 'STORY-301 AC6: Tracks which items were already sent per alert to prevent duplicates';

-- Indexes for dedup lookups and cleanup
CREATE UNIQUE INDEX idx_alert_sent_items_dedup ON alert_sent_items(alert_id, item_id);
CREATE INDEX idx_alert_sent_items_alert_id ON alert_sent_items(alert_id);
CREATE INDEX idx_alert_sent_items_sent_at ON alert_sent_items(sent_at);

-- RLS (accessed only via service_role from cron job)
ALTER TABLE alert_sent_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access to alert_sent_items"
  ON alert_sent_items FOR ALL
  TO service_role
  USING (true) WITH CHECK (true);

-- Users can view sent items for their own alerts (read-only via join)
CREATE POLICY "Users can view own alert sent items"
  ON alert_sent_items FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM alerts
      WHERE alerts.id = alert_sent_items.alert_id
      AND alerts.user_id = auth.uid()
    )
  );
