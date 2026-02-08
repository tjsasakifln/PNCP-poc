-- ============================================================
-- SmartLic: Annual Subscriptions - Billing Helper Functions
-- Migration: 011_add_billing_helper_functions
-- Date: 2026-02-07
-- Story: STORY-171
-- ============================================================

-- Helper function: Get user's current billing period
-- Used for quick lookups without joining tables
CREATE OR REPLACE FUNCTION public.get_user_billing_period(p_user_id UUID)
RETURNS VARCHAR(10) AS $$
DECLARE
  v_billing_period VARCHAR(10);
BEGIN
  SELECT billing_period INTO v_billing_period
  FROM public.user_subscriptions
  WHERE user_id = p_user_id AND is_active = true
  ORDER BY created_at DESC
  LIMIT 1;

  RETURN COALESCE(v_billing_period, 'monthly');  -- Default to monthly if no active subscription
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.get_user_billing_period IS 'Get user''s current billing period (monthly/annual)';

-- Helper function: Check if user has specific feature
-- Handles both plan capabilities AND billing-period-specific features
CREATE OR REPLACE FUNCTION public.user_has_feature(
  p_user_id UUID,
  p_feature_key VARCHAR(100)
)
RETURNS BOOLEAN AS $$
DECLARE
  v_plan_id TEXT;
  v_billing_period VARCHAR(10);
  v_has_feature BOOLEAN;
BEGIN
  -- Get user's current plan and billing period
  SELECT us.plan_id, us.billing_period INTO v_plan_id, v_billing_period
  FROM public.user_subscriptions us
  WHERE us.user_id = p_user_id AND us.is_active = true
  ORDER BY us.created_at DESC
  LIMIT 1;

  -- No active subscription
  IF v_plan_id IS NULL THEN
    RETURN false;
  END IF;

  -- Check if feature exists for this plan + billing period
  SELECT EXISTS (
    SELECT 1 FROM public.plan_features
    WHERE plan_id = v_plan_id
      AND billing_period = v_billing_period
      AND feature_key = p_feature_key
      AND enabled = true
  ) INTO v_has_feature;

  RETURN v_has_feature;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.user_has_feature IS 'Check if user has specific feature based on plan + billing period';

-- Helper function: Get all enabled features for user
-- Returns array of feature keys
CREATE OR REPLACE FUNCTION public.get_user_features(p_user_id UUID)
RETURNS TEXT[] AS $$
DECLARE
  v_plan_id TEXT;
  v_billing_period VARCHAR(10);
  v_features TEXT[];
BEGIN
  -- Get user's current plan and billing period
  SELECT us.plan_id, us.billing_period INTO v_plan_id, v_billing_period
  FROM public.user_subscriptions us
  WHERE us.user_id = p_user_id AND us.is_active = true
  ORDER BY us.created_at DESC
  LIMIT 1;

  -- No active subscription
  IF v_plan_id IS NULL THEN
    RETURN ARRAY[]::TEXT[];
  END IF;

  -- Get all enabled features for this plan + billing period
  SELECT ARRAY_AGG(feature_key) INTO v_features
  FROM public.plan_features
  WHERE plan_id = v_plan_id
    AND billing_period = v_billing_period
    AND enabled = true;

  RETURN COALESCE(v_features, ARRAY[]::TEXT[]);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.get_user_features IS 'Get array of all enabled feature keys for user';

-- Verify migration
DO $$
DECLARE
  test_user_id UUID := '00000000-0000-0000-0000-000000000000';
  test_result TEXT[];
BEGIN
  -- Test get_user_features with non-existent user (should return empty array)
  test_result := public.get_user_features(test_user_id);

  IF test_result IS NULL OR ARRAY_LENGTH(test_result, 1) IS NOT NULL THEN
    RAISE WARNING 'Unexpected result from get_user_features for non-existent user: %', test_result;
  END IF;

  RAISE NOTICE 'Migration 011 completed successfully';
END $$;
