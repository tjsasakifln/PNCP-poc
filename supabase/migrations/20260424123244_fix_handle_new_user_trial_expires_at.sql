-- ============================================================================
-- Migration: 20260424123244_fix_handle_new_user_trial_expires_at.sql
-- Mission: empresa-morrendo — sessão velvet-music
-- Date: 2026-04-24
-- Depends on: 20260225110000_fix_handle_new_user_trigger.sql
--
-- Problem (REVENUE-DIRECT):
-- The handle_new_user trigger does NOT set profiles.trial_expires_at. Every
-- signup via the Supabase SDK legacy path (runLegacySignup in frontend) and
-- via backend /v1/auth/signup (which relies on the same trigger) ends up
-- with trial_expires_at = NULL. Consequence: plan_enforcement.py:237
-- check `if expires_at_dt and now > expires_at_dt` evaluates False when
-- NULL → trial NEVER expires → paywall never triggers → zero conversion
-- pressure for trial users. Confirmed 2026-04-24: both external users in
-- prod (2/2) have trial_expires_at = NULL.
--
-- Fix:
-- Populate trial_expires_at = NOW() + 14 days on INSERT for new signups.
-- Covers BOTH paths (legacy Supabase SDK + backend /v1/auth/signup).
-- Backfill existing free_trial users with NULL trial_expires_at using
-- created_at + 14 days. Migration 20260228170000 did a similar backfill
-- in Feb but only for users existing at that time — 2 users created in
-- April (dsl*, pau*) slipped through.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
DECLARE
  _phone text;
BEGIN
  _phone := regexp_replace(COALESCE(NEW.raw_user_meta_data->>'phone_whatsapp', ''), '[^0-9]', '', 'g');
  IF length(_phone) > 11 AND left(_phone, 2) = '55' THEN _phone := substring(_phone from 3); END IF;
  IF left(_phone, 1) = '0' THEN _phone := substring(_phone from 2); END IF;
  IF length(_phone) NOT IN (10, 11) THEN _phone := NULL; END IF;

  INSERT INTO public.profiles (
    id, email, full_name, company, sector,
    phone_whatsapp, whatsapp_consent, plan_type,
    avatar_url, context_data, trial_expires_at
  )
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
    COALESCE(NEW.raw_user_meta_data->>'company', ''),
    COALESCE(NEW.raw_user_meta_data->>'sector', ''),
    _phone,
    COALESCE((NEW.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
    'free_trial',
    NEW.raw_user_meta_data->>'avatar_url',
    '{}'::jsonb,
    NOW() + INTERVAL '14 days'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Backfill: set trial_expires_at for existing free_trial profiles where NULL.
-- Uses created_at + 14 days to give each user a reasonable deadline based on
-- when they signed up. Users whose 14 days have already passed will be marked
-- as expired immediately — this is correct behavior (they were supposed to
-- expire but the paywall was broken).
UPDATE public.profiles
SET trial_expires_at = created_at + INTERVAL '14 days'
WHERE trial_expires_at IS NULL
  AND plan_type = 'free_trial';
