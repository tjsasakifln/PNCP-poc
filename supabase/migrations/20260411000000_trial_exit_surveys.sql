-- STORY-369 AC1: Exit survey table for trial users
CREATE TABLE trial_exit_surveys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  reason TEXT NOT NULL CHECK (reason IN ('no_editais', 'preco_alto', 'ainda_avaliando', 'outro')),
  reason_text TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE trial_exit_surveys ENABLE ROW LEVEL SECURITY;

-- 1 survey por usuário
CREATE UNIQUE INDEX trial_exit_surveys_user_id_idx ON trial_exit_surveys(user_id);
-- Index para analytics
CREATE INDEX trial_exit_surveys_created_at_idx ON trial_exit_surveys(created_at);

-- Usuário só pode inserir seu próprio registro
CREATE POLICY "users_insert_own_survey" ON trial_exit_surveys
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Admin/master pode ler todos
CREATE POLICY "admin_read_surveys" ON trial_exit_surveys
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid() AND (is_admin = true OR plan_type = 'master')
    )
  );
