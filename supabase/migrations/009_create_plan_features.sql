-- ============================================================
-- SmartLic: Annual Subscriptions - Plan Features Table
-- Migration: 009_create_plan_features
-- Date: 2026-02-07
-- Story: STORY-171
-- ============================================================

-- Create plan_features table for billing-period-specific features
CREATE TABLE IF NOT EXISTS public.plan_features (
  id SERIAL PRIMARY KEY,
  plan_id TEXT NOT NULL REFERENCES public.plans(id) ON DELETE CASCADE,
  billing_period VARCHAR(10) NOT NULL CHECK (billing_period IN ('monthly', 'annual')),
  feature_key VARCHAR(100) NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT true,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(plan_id, billing_period, feature_key)
);

COMMENT ON TABLE public.plan_features IS 'Billing-period-specific feature flags for subscription plans';
COMMENT ON COLUMN public.plan_features.plan_id IS 'References plans.id (consultor_agil, maquina, sala_guerra)';
COMMENT ON COLUMN public.plan_features.billing_period IS 'monthly or annual';
COMMENT ON COLUMN public.plan_features.feature_key IS 'Feature identifier (early_access, proactive_search, etc)';
COMMENT ON COLUMN public.plan_features.metadata IS 'Optional feature-specific configuration';

-- Performance index for common query pattern
-- Covers: SELECT ... WHERE plan_id = ? AND billing_period = ? AND enabled = true
CREATE INDEX idx_plan_features_lookup
  ON public.plan_features(plan_id, billing_period, enabled)
  WHERE enabled = true;

COMMENT ON INDEX idx_plan_features_lookup IS 'Optimize feature flag lookups for active features';

-- Updated_at trigger (reuse existing function)
CREATE TRIGGER plan_features_updated_at
  BEFORE UPDATE ON public.plan_features
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- Seed annual-exclusive features for all paid plans
-- CRITICAL: Only annual billing gets these benefits (20% discount incentive)
INSERT INTO public.plan_features (plan_id, billing_period, feature_key, enabled, metadata) VALUES
  -- Consultor Ágil (annual benefits)
  ('consultor_agil', 'annual', 'early_access', true, '{"description": "Acesso antecipado a novos recursos"}'::jsonb),
  ('consultor_agil', 'annual', 'proactive_search', true, '{"description": "Alertas automáticos de novas licitações"}'::jsonb),

  -- Máquina (annual benefits)
  ('maquina', 'annual', 'early_access', true, '{"description": "Acesso antecipado a novos recursos"}'::jsonb),
  ('maquina', 'annual', 'proactive_search', true, '{"description": "Alertas automáticos de novas licitações"}'::jsonb),

  -- Sala de Guerra (annual benefits - includes AI analysis)
  ('sala_guerra', 'annual', 'early_access', true, '{"description": "Acesso antecipado a novos recursos"}'::jsonb),
  ('sala_guerra', 'annual', 'proactive_search', true, '{"description": "Alertas automáticos de novas licitações"}'::jsonb),
  ('sala_guerra', 'annual', 'ai_edital_analysis', true, '{"description": "Análise de editais com IA (GPT-4)"}'::jsonb)
ON CONFLICT (plan_id, billing_period, feature_key) DO NOTHING;

-- Row Level Security
ALTER TABLE public.plan_features ENABLE ROW LEVEL SECURITY;

-- Everyone can read plan features (public catalog)
CREATE POLICY "plan_features_select_all" ON public.plan_features
  FOR SELECT USING (true);

-- Verify migration
DO $$
DECLARE
  feature_count INT;
BEGIN
  SELECT COUNT(*) INTO feature_count
  FROM public.plan_features
  WHERE enabled = true;

  IF feature_count < 7 THEN
    RAISE WARNING 'Expected at least 7 seeded features, found %', feature_count;
  END IF;

  RAISE NOTICE 'Migration 009 completed successfully (% features seeded)', feature_count;
END $$;
