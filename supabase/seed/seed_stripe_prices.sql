-- DEBT-017/DB-029: Parameterized Stripe Price IDs for staging/dev setup
-- Usage: Replace placeholders with actual Stripe Price IDs per environment.
--
-- Production values are in migrations (already applied).
-- For staging/dev, run this seed script AFTER migrations:
--
--   SMARTLIC_PRO_MONTHLY=price_xxx \
--   SMARTLIC_PRO_SEMIANNUAL=price_xxx \
--   SMARTLIC_PRO_ANNUAL=price_xxx \
--   CONSULTORIA_MONTHLY=price_xxx \
--   CONSULTORIA_SEMIANNUAL=price_xxx \
--   CONSULTORIA_ANNUAL=price_xxx \
--   psql $DATABASE_URL -f supabase/seed/seed_stripe_prices.sql
--
-- Or use the helper script: scripts/seed-stripe-prices.sh

-- SmartLic Pro plan
UPDATE plans SET
    stripe_price_id = COALESCE(current_setting('app.smartlic_pro_monthly', true), stripe_price_id),
    stripe_price_id_monthly = COALESCE(current_setting('app.smartlic_pro_monthly', true), stripe_price_id_monthly),
    stripe_price_id_semiannual = COALESCE(current_setting('app.smartlic_pro_semiannual', true), stripe_price_id_semiannual),
    stripe_price_id_annual = COALESCE(current_setting('app.smartlic_pro_annual', true), stripe_price_id_annual)
WHERE id = 'smartlic_pro'
AND current_setting('app.smartlic_pro_monthly', true) IS NOT NULL;

-- Consultoria plan
UPDATE plans SET
    stripe_price_id = COALESCE(current_setting('app.consultoria_monthly', true), stripe_price_id),
    stripe_price_id_monthly = COALESCE(current_setting('app.consultoria_monthly', true), stripe_price_id_monthly),
    stripe_price_id_semiannual = COALESCE(current_setting('app.consultoria_semiannual', true), stripe_price_id_semiannual),
    stripe_price_id_annual = COALESCE(current_setting('app.consultoria_annual', true), stripe_price_id_annual)
WHERE id = 'consultoria'
AND current_setting('app.consultoria_monthly', true) IS NOT NULL;

-- Update plan_billing_periods to match
UPDATE plan_billing_periods SET
    stripe_price_id = COALESCE(current_setting('app.smartlic_pro_monthly', true), stripe_price_id)
WHERE plan_id = 'smartlic_pro' AND billing_period = 'monthly'
AND current_setting('app.smartlic_pro_monthly', true) IS NOT NULL;

UPDATE plan_billing_periods SET
    stripe_price_id = COALESCE(current_setting('app.smartlic_pro_semiannual', true), stripe_price_id)
WHERE plan_id = 'smartlic_pro' AND billing_period = 'semiannual'
AND current_setting('app.smartlic_pro_semiannual', true) IS NOT NULL;

UPDATE plan_billing_periods SET
    stripe_price_id = COALESCE(current_setting('app.smartlic_pro_annual', true), stripe_price_id)
WHERE plan_id = 'smartlic_pro' AND billing_period = 'annual'
AND current_setting('app.smartlic_pro_annual', true) IS NOT NULL;

UPDATE plan_billing_periods SET
    stripe_price_id = COALESCE(current_setting('app.consultoria_monthly', true), stripe_price_id)
WHERE plan_id = 'consultoria' AND billing_period = 'monthly'
AND current_setting('app.consultoria_monthly', true) IS NOT NULL;

UPDATE plan_billing_periods SET
    stripe_price_id = COALESCE(current_setting('app.consultoria_semiannual', true), stripe_price_id)
WHERE plan_id = 'consultoria' AND billing_period = 'semiannual'
AND current_setting('app.consultoria_semiannual', true) IS NOT NULL;

UPDATE plan_billing_periods SET
    stripe_price_id = COALESCE(current_setting('app.consultoria_annual', true), stripe_price_id)
WHERE plan_id = 'consultoria' AND billing_period = 'annual'
AND current_setting('app.consultoria_annual', true) IS NOT NULL;
