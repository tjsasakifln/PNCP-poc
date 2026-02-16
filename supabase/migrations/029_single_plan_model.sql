-- Migration 029: GTM-002 Single Plan Model - SmartLic Pro
-- Date: 2026-02-15
-- Author: AIOS Development Team
-- Story: GTM-002
--
-- Summary:
-- Implements the new single-plan pricing model (SmartLic Pro) with multi-period billing.
-- Replaces the legacy 3-tier model (Consultor Ágil, Máquina de Guerra, Sala de Guerra)
-- with a single SmartLic Pro plan available in monthly, semiannual (10% off), and annual (20% off) periods.
--
-- Changes:
-- 1. Add smartlic_pro plan to plans table
-- 2. Update billing_period constraint to include 'semiannual'
-- 3. Add stripe_price_id_semiannual column to plans table
-- 4. Create plan_billing_periods table for multi-period pricing
-- 5. Insert billing periods for smartlic_pro
-- 6. Add plan_features for smartlic_pro
-- 7. Deactivate legacy plans (consultor_agil, maquina, sala_guerra)
-- 8. Update profiles.plan_type constraint to include smartlic_pro

BEGIN;

-- 1. Add smartlic_pro plan to plans table
-- Using ON CONFLICT to handle idempotent migrations
INSERT INTO public.plans (id, name, description, price_brl, max_searches, duration_days, is_active)
VALUES (
  'smartlic_pro',
  'SmartLic Pro',
  'Produto completo com inteligência de decisão em licitações',
  1999.00,
  1000,
  30,
  true
)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  price_brl = EXCLUDED.price_brl,
  max_searches = EXCLUDED.max_searches,
  is_active = EXCLUDED.is_active;

-- 2. Update billing_period constraint on user_subscriptions to include 'semiannual'
ALTER TABLE public.user_subscriptions DROP CONSTRAINT IF EXISTS user_subscriptions_billing_period_check;
ALTER TABLE public.user_subscriptions ADD CONSTRAINT user_subscriptions_billing_period_check
  CHECK (billing_period IN ('monthly', 'semiannual', 'annual'));

-- 3. Add stripe_price_id_semiannual column for semiannual billing
ALTER TABLE public.plans ADD COLUMN IF NOT EXISTS stripe_price_id_semiannual TEXT;

-- 4. Create plan_billing_periods table for multi-period pricing
CREATE TABLE IF NOT EXISTS public.plan_billing_periods (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id TEXT NOT NULL REFERENCES public.plans(id) ON DELETE CASCADE,
  billing_period TEXT NOT NULL CHECK (billing_period IN ('monthly', 'semiannual', 'annual')),
  price_cents INTEGER NOT NULL,
  discount_percent INTEGER DEFAULT 0,
  stripe_price_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(plan_id, billing_period)
);

-- Enable RLS on plan_billing_periods
ALTER TABLE public.plan_billing_periods ENABLE ROW LEVEL SECURITY;

-- Public read access (plan pricing is public info)
CREATE POLICY "plan_billing_periods_public_read" ON public.plan_billing_periods
  FOR SELECT TO authenticated, anon USING (true);

-- Service role full access
CREATE POLICY "plan_billing_periods_service_all" ON public.plan_billing_periods
  FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 5. Insert billing periods for smartlic_pro
-- Monthly: R$ 1,999.00 (no discount)
-- Semiannual: R$ 1,799.00 per month (10% off)
-- Annual: R$ 1,599.00 per month (20% off)
INSERT INTO public.plan_billing_periods (plan_id, billing_period, price_cents, discount_percent, stripe_price_id)
VALUES
  ('smartlic_pro', 'monthly', 199900, 0, 'price_1T1ILH9FhmvPslGY4mNcGfso'),
  ('smartlic_pro', 'semiannual', 179900, 10, 'price_1T1ILK9FhmvPslGYtJdkkBlB'),
  ('smartlic_pro', 'annual', 159900, 20, 'price_1T1ILN9FhmvPslGYGQjfYdXA')
ON CONFLICT (plan_id, billing_period) DO UPDATE SET
  stripe_price_id = EXCLUDED.stripe_price_id;

-- 5b. Update plans table with Stripe Price IDs for direct lookup
UPDATE public.plans SET
  stripe_price_id_monthly = 'price_1T1ILH9FhmvPslGY4mNcGfso',
  stripe_price_id_semiannual = 'price_1T1ILK9FhmvPslGYtJdkkBlB',
  stripe_price_id_annual = 'price_1T1ILN9FhmvPslGYGQjfYdXA'
WHERE id = 'smartlic_pro';

-- 6. Add plan_features for smartlic_pro
-- Note: plan_features has a unique constraint on (plan_id, feature_key)
INSERT INTO public.plan_features (plan_id, feature_key, feature_value)
VALUES
  ('smartlic_pro', 'max_requests_per_month', '1000'),
  ('smartlic_pro', 'allow_excel', 'true'),
  ('smartlic_pro', 'allow_pipeline', 'true'),
  ('smartlic_pro', 'max_summary_tokens', '10000'),
  ('smartlic_pro', 'max_history_days', '1825'),
  ('smartlic_pro', 'priority', 'normal')
ON CONFLICT (plan_id, feature_key) DO UPDATE SET
  feature_value = EXCLUDED.feature_value;

-- 7. Deactivate legacy plans
-- Keep them in DB for historical records and existing subscriptions
UPDATE public.plans
SET is_active = false
WHERE id IN ('consultor_agil', 'maquina', 'sala_guerra');

-- 8. Update profiles.plan_type constraint to include smartlic_pro
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_plan_type_check;
ALTER TABLE public.profiles ADD CONSTRAINT profiles_plan_type_check
  CHECK (plan_type IN ('free_trial', 'consultor_agil', 'maquina', 'sala_guerra', 'master', 'smartlic_pro'));

COMMIT;

-- Verification Queries
-- Run these after migration to verify correct state

-- Check smartlic_pro plan exists and is active
SELECT id, name, price_brl, max_searches, is_active
FROM public.plans
WHERE id = 'smartlic_pro';

-- Check legacy plans are deactivated
SELECT id, name, is_active
FROM public.plans
WHERE id IN ('consultor_agil', 'maquina', 'sala_guerra');

-- Check billing periods for smartlic_pro
SELECT plan_id, billing_period, price_cents, discount_percent, stripe_price_id
FROM public.plan_billing_periods
WHERE plan_id = 'smartlic_pro'
ORDER BY billing_period;

-- Check plan_features for smartlic_pro
SELECT plan_id, feature_key, feature_value
FROM public.plan_features
WHERE plan_id = 'smartlic_pro'
ORDER BY feature_key;

-- Check user_subscriptions constraint allows semiannual
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.user_subscriptions'::regclass
  AND conname = 'user_subscriptions_billing_period_check';

-- Check profiles constraint includes smartlic_pro
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.profiles'::regclass
  AND conname = 'profiles_plan_type_check';

-- Check plan_billing_periods table structure
\d public.plan_billing_periods;

-- Check RLS policies on plan_billing_periods
SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'plan_billing_periods';
