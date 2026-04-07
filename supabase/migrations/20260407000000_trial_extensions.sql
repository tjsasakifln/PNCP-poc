-- Trial Extension mechanism (Zero-Churn P2 §8.2)
CREATE TABLE IF NOT EXISTS trial_extensions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  condition TEXT NOT NULL CHECK (condition IN ('profile_complete','feedback_given','referral_signup')),
  days_added INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, condition)
);

ALTER TABLE trial_extensions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own extensions" ON trial_extensions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service role full access" ON trial_extensions FOR ALL USING (auth.role() = 'service_role');

CREATE INDEX idx_trial_extensions_user ON trial_extensions(user_id);

-- Atomic RPC: extend trial + insert record in one transaction
CREATE OR REPLACE FUNCTION extend_trial_atomic(
  p_user_id UUID, p_condition TEXT, p_days INT, p_max_total INT
) RETURNS JSONB AS $$
DECLARE
  v_total INT;
  v_new_expires TIMESTAMPTZ;
BEGIN
  SELECT COALESCE(SUM(days_added), 0) INTO v_total
  FROM trial_extensions WHERE user_id = p_user_id;

  IF v_total + p_days > p_max_total THEN
    RETURN jsonb_build_object('error', 'max_extension_reached', 'total_extended', v_total);
  END IF;

  INSERT INTO trial_extensions (user_id, condition, days_added)
  VALUES (p_user_id, p_condition, p_days);

  UPDATE profiles
  SET trial_expires_at = trial_expires_at + (p_days || ' days')::INTERVAL
  WHERE id = p_user_id
  RETURNING trial_expires_at INTO v_new_expires;

  RETURN jsonb_build_object(
    'days_added', p_days,
    'total_extended', v_total + p_days,
    'new_expires_at', v_new_expires
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
