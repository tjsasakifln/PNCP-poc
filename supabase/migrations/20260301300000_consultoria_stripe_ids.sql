-- Migration: STORY-322 — Consultoria Plan Stripe IDs
-- Date: 2026-03-01
-- Story: STORY-322 AC7
--
-- Summary:
-- 1. Inserts "consultoria" plan into plans table with Stripe price IDs
-- 2. Inserts billing periods into plan_billing_periods
-- 3. Inserts plan features
-- 4. Updates profiles.plan_type constraint to include 'consultoria'
--
-- Stripe Product (LIVE): prod_U45sj3Z9GYA1Dj (SmartLic Consultoria)
-- Stripe Product (TEST): prod_U45lwa0NL7wwG7
-- Prices (LIVE mode):
--   Monthly:    R$ 997/mês     → price_1T5xgc9FhmvPslGYgN2Mw3RL
--   Semiannual: R$ 897/mês x6  → price_1T5xge9FhmvPslGYvlyTokpt
--   Annual:     R$ 797/mês x12 → price_1T5xgg9FhmvPslGYu9rD7XbC
-- Prices (TEST mode):
--   Monthly:    price_1T5xgc9FhmvPslGYgN2Mw3RL
--   Semiannual: price_1T5xge9FhmvPslGYvlyTokpt
--   Annual:     price_1T5xgg9FhmvPslGYu9rD7XbC

BEGIN;

-- 1. Insert consultoria plan into plans table
INSERT INTO public.plans (id, name, description, price_brl, max_searches, duration_days, is_active,
  stripe_price_id_monthly, stripe_price_id_semiannual, stripe_price_id_annual)
VALUES (
  'consultoria',
  'SmartLic Consultoria',
  'Multi-user para consultorias de licitação — até 5 membros, dashboard consolidado, logo nos relatórios',
  997.00,
  5000,
  365,
  true,
  'price_1T5xgc9FhmvPslGYgN2Mw3RL',
  'price_1T5xge9FhmvPslGYvlyTokpt',
  'price_1T5xgg9FhmvPslGYu9rD7XbC'
)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  price_brl = EXCLUDED.price_brl,
  max_searches = EXCLUDED.max_searches,
  is_active = EXCLUDED.is_active,
  stripe_price_id_monthly = EXCLUDED.stripe_price_id_monthly,
  stripe_price_id_semiannual = EXCLUDED.stripe_price_id_semiannual,
  stripe_price_id_annual = EXCLUDED.stripe_price_id_annual;

-- 2. Insert billing periods into plan_billing_periods
INSERT INTO public.plan_billing_periods (plan_id, billing_period, price_cents, discount_percent, stripe_price_id)
VALUES
  ('consultoria', 'monthly',    99700, 0,  'price_1T5xgc9FhmvPslGYgN2Mw3RL'),
  ('consultoria', 'semiannual', 89700, 10, 'price_1T5xge9FhmvPslGYvlyTokpt'),
  ('consultoria', 'annual',     79700, 20, 'price_1T5xgg9FhmvPslGYu9rD7XbC')
ON CONFLICT (plan_id, billing_period) DO UPDATE SET
  price_cents = EXCLUDED.price_cents,
  discount_percent = EXCLUDED.discount_percent,
  stripe_price_id = EXCLUDED.stripe_price_id;

-- 3. Insert plan features for consultoria
INSERT INTO public.plan_features (plan_id, billing_period, feature_key, enabled, metadata)
VALUES
  ('consultoria', 'monthly',    'full_access',      true, '{"description": "Acesso completo ao produto"}'::jsonb),
  ('consultoria', 'monthly',    'early_access',     true, '{"description": "Acesso antecipado a novos recursos"}'::jsonb),
  ('consultoria', 'monthly',    'proactive_search', true, '{"description": "Alertas automáticos de novas licitações"}'::jsonb),
  ('consultoria', 'monthly',    'multi_user',       true, '{"description": "Até 5 membros por organização", "max_members": 5}'::jsonb),
  ('consultoria', 'monthly',    'custom_branding',  true, '{"description": "Logo da consultoria nos relatórios"}'::jsonb),
  ('consultoria', 'semiannual', 'full_access',      true, '{"description": "Acesso completo ao produto"}'::jsonb),
  ('consultoria', 'semiannual', 'early_access',     true, '{"description": "Acesso antecipado a novos recursos"}'::jsonb),
  ('consultoria', 'semiannual', 'proactive_search', true, '{"description": "Alertas automáticos de novas licitações"}'::jsonb),
  ('consultoria', 'semiannual', 'multi_user',       true, '{"description": "Até 5 membros por organização", "max_members": 5}'::jsonb),
  ('consultoria', 'semiannual', 'custom_branding',  true, '{"description": "Logo da consultoria nos relatórios"}'::jsonb),
  ('consultoria', 'annual',     'full_access',      true, '{"description": "Acesso completo ao produto"}'::jsonb),
  ('consultoria', 'annual',     'early_access',     true, '{"description": "Acesso antecipado a novos recursos"}'::jsonb),
  ('consultoria', 'annual',     'proactive_search', true, '{"description": "Alertas automáticos de novas licitações"}'::jsonb),
  ('consultoria', 'annual',     'multi_user',       true, '{"description": "Até 5 membros por organização", "max_members": 5}'::jsonb),
  ('consultoria', 'annual',     'custom_branding',  true, '{"description": "Logo da consultoria nos relatórios"}'::jsonb),
  ('consultoria', 'annual',     'ai_analysis',      true, '{"description": "Análise estratégica com IA avançada"}'::jsonb)
ON CONFLICT (plan_id, billing_period, feature_key) DO NOTHING;

-- 4. Update profiles.plan_type constraint to include 'consultoria'
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_plan_type_check;
ALTER TABLE public.profiles ADD CONSTRAINT profiles_plan_type_check
  CHECK (plan_type IN ('free_trial', 'consultor_agil', 'maquina', 'sala_guerra', 'master', 'smartlic_pro', 'consultoria'));

COMMIT;
