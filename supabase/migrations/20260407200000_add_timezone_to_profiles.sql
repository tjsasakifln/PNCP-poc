-- Zero-Churn P2 §1.2: Timezone-aware email scheduling
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'America/Sao_Paulo';

COMMENT ON COLUMN profiles.timezone IS
  'IANA timezone identifier for timezone-aware email scheduling';

-- Update handle_new_user() to capture timezone from signup metadata
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  _phone text;
BEGIN
  _phone := regexp_replace(COALESCE(NEW.raw_user_meta_data->>'phone_whatsapp', ''), '[^0-9]', '', 'g');
  IF length(_phone) > 11 AND left(_phone, 2) = '55' THEN _phone := substring(_phone from 3); END IF;
  IF left(_phone, 1) = '0' THEN _phone := substring(_phone from 2); END IF;
  IF length(_phone) NOT IN (10, 11) THEN _phone := NULL; END IF;

  BEGIN
    INSERT INTO public.profiles (
      id, email, full_name, company, sector,
      phone_whatsapp, whatsapp_consent, plan_type,
      avatar_url, context_data, timezone
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
      COALESCE(NEW.raw_user_meta_data->>'timezone', 'America/Sao_Paulo')
    )
    ON CONFLICT (id) DO NOTHING;

  EXCEPTION
    WHEN unique_violation THEN
      INSERT INTO public.profiles (
        id, email, full_name, company, sector,
        phone_whatsapp, whatsapp_consent, plan_type,
        avatar_url, context_data, timezone
      )
      VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        COALESCE(NEW.raw_user_meta_data->>'company', ''),
        COALESCE(NEW.raw_user_meta_data->>'sector', ''),
        NULL,
        COALESCE((NEW.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
        'free_trial',
        NEW.raw_user_meta_data->>'avatar_url',
        '{}'::jsonb,
        COALESCE(NEW.raw_user_meta_data->>'timezone', 'America/Sao_Paulo')
      )
      ON CONFLICT (id) DO NOTHING;
  END;

  RETURN NEW;
END;
$$;
