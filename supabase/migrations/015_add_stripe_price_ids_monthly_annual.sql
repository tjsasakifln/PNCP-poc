-- ============================================================
-- SmartLic: Add monthly/annual Stripe price IDs to plans
-- Migration: 015_add_stripe_price_ids_monthly_annual
-- Date: 2026-02-10
-- ============================================================

-- Add separate columns for monthly and annual Stripe price IDs
ALTER TABLE public.plans
  ADD COLUMN IF NOT EXISTS stripe_price_id_monthly TEXT,
  ADD COLUMN IF NOT EXISTS stripe_price_id_annual TEXT;

-- Populate Stripe price IDs for the 3 active subscription plans
UPDATE public.plans SET
  stripe_price_id_monthly = 'price_1Syir09FhmvPslGYOCbOvWVB',
  stripe_price_id_annual  = 'price_1SzRAC9FhmvPslGYLBuYTaSa',
  stripe_price_id         = 'price_1Syir09FhmvPslGYOCbOvWVB'  -- default to monthly
WHERE id = 'consultor_agil';

UPDATE public.plans SET
  stripe_price_id_monthly = 'price_1Syirk9FhmvPslGY1kbNWxaz',
  stripe_price_id_annual  = 'price_1SzR8F9FhmvPslGYDW84AzYA',
  stripe_price_id         = 'price_1Syirk9FhmvPslGY1kbNWxaz'
WHERE id = 'maquina';

UPDATE public.plans SET
  stripe_price_id_monthly = 'price_1Syise9FhmvPslGYAR8Fbf5E',
  stripe_price_id_annual  = 'price_1SzR5c9FhmvPslGYQym74G6K',
  stripe_price_id         = 'price_1Syise9FhmvPslGYAR8Fbf5E'
WHERE id = 'sala_guerra';
