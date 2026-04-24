-- Rollback: restore handle_new_user() without trial_expires_at column.
-- Restores the INSERT to the 10-field version from migration
-- 20260225110000_fix_handle_new_user_trigger.sql. Does NOT un-backfill
-- trial_expires_at — rollback preserves data correctness since the
-- populated values are still valid (14 days from signup).

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
    avatar_url, context_data
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
    '{}'::jsonb
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
