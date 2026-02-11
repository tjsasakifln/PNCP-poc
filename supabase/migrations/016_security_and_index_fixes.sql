-- ============================================================================
-- Migration 016: Security and Index Fixes
-- STORY-200: Security and Trust Foundation
-- Date: 2026-02-11
-- ============================================================================
-- This migration combines multiple targeted security and performance fixes:
--   DB-C03: Fix stripe_webhook_events admin policy (plan_type → is_admin)
--   DB-H04: Tighten RLS on monthly_quota and search_sessions
--   DB-H03: Add unique index on user_subscriptions.stripe_subscription_id
--   NEW-DB-03: Add trigram index on profiles.email for admin ILIKE search
--   DB-C02: Add service role write policy on user_subscriptions
--   NEW-DB-02: Fix handle_new_user() trigger default to free_trial
-- ============================================================================

-- ============================================================
-- 1. DB-C03: Fix stripe_webhook_events admin policy
--    Bug: checks plan_type = 'master' instead of is_admin = true
--    Impact: non-admin master users can view webhook events;
--            admin users with different plan_type cannot
-- ============================================================

DROP POLICY IF EXISTS "webhook_events_select_admin" ON public.stripe_webhook_events;
CREATE POLICY "webhook_events_select_admin" ON public.stripe_webhook_events
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid() AND profiles.is_admin = true
    )
  );

-- ============================================================
-- 2. DB-H04: Tighten RLS on monthly_quota and search_sessions
--    Bug: FOR ALL USING (true) without TO service_role allows
--    any authenticated user to INSERT/UPDATE/DELETE directly
-- ============================================================

-- monthly_quota: replace overly permissive policy with service_role-scoped one
DROP POLICY IF EXISTS "Service role can manage quota" ON public.monthly_quota;
CREATE POLICY "Service role can manage quota" ON public.monthly_quota
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- search_sessions: replace overly permissive policy with service_role-scoped one
DROP POLICY IF EXISTS "Service role can manage search sessions" ON public.search_sessions;
CREATE POLICY "Service role can manage search sessions" ON public.search_sessions
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ============================================================
-- 3. DB-H03: Add unique index on user_subscriptions.stripe_subscription_id
--    Missing index causes sequential scans and allows duplicate
--    subscription IDs
-- ============================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_subscriptions_stripe_sub_id
  ON public.user_subscriptions(stripe_subscription_id)
  WHERE stripe_subscription_id IS NOT NULL;

-- ============================================================
-- 4. NEW-DB-03: Add trigram index on profiles.email for admin
--    ILIKE search (requires pg_trgm extension)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_profiles_email_trgm
  ON public.profiles
  USING gin (email gin_trgm_ops);

-- ============================================================
-- 5. DB-C02: Add service role RLS write policy on user_subscriptions
--    Matches pattern from monthly_quota and search_sessions
-- ============================================================

DROP POLICY IF EXISTS "Service role can manage subscriptions" ON public.user_subscriptions;
CREATE POLICY "Service role can manage subscriptions" ON public.user_subscriptions
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ============================================================
-- 6. NEW-DB-02: Fix handle_new_user() trigger default
--    Bug: sets plan_type = 'free' but should be 'free_trial'
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, avatar_url, plan_type)
  VALUES (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'),
    new.raw_user_meta_data->>'avatar_url',
    'free_trial'
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- Verification queries (run after applying):
-- ============================================================================
-- 1. Check webhook policy uses is_admin:
--    SELECT policyname, qual FROM pg_policies WHERE tablename = 'stripe_webhook_events';
--
-- 2. Check monthly_quota policy is role-scoped:
--    SELECT policyname, roles FROM pg_policies WHERE tablename = 'monthly_quota';
--
-- 3. Check unique index exists:
--    SELECT indexname FROM pg_indexes WHERE tablename = 'user_subscriptions' AND indexname LIKE '%stripe%';
--
-- 4. Check trigram index:
--    EXPLAIN ANALYZE SELECT * FROM profiles WHERE email ILIKE '%test%';
--
-- 5. Check handle_new_user sets free_trial:
--    SELECT prosrc FROM pg_proc WHERE proname = 'handle_new_user';
-- ============================================================================
