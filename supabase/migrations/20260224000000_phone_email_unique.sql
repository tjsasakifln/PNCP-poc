-- STORY-258: Phone uniqueness + Email uniqueness constraints
-- AC5: UNIQUE on profiles.email (defense-in-depth, auth.users is source of truth)
-- AC7: UNIQUE on profiles.phone_whatsapp (partial — WHERE NOT NULL)

-- AC7: Phone uniqueness (partial index — multiple NULLs allowed)
CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_phone_whatsapp_unique
ON profiles (phone_whatsapp)
WHERE phone_whatsapp IS NOT NULL;

-- AC5: Email uniqueness (defense-in-depth)
-- First check for duplicates before creating constraint
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes WHERE indexname = 'idx_profiles_email_unique'
  ) THEN
    CREATE UNIQUE INDEX idx_profiles_email_unique ON profiles (email)
    WHERE email IS NOT NULL;
  END IF;
END $$;

-- AC10: Update handle_new_user() to check phone uniqueness before insert
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
DECLARE
  _phone text;
  _existing_count int;
BEGIN
  -- Normalize phone if provided
  _phone := regexp_replace(COALESCE(NEW.raw_user_meta_data->>'phone_whatsapp', ''), '[^0-9]', '', 'g');
  IF length(_phone) > 11 AND left(_phone, 2) = '55' THEN
    _phone := substring(_phone from 3);
  END IF;
  IF left(_phone, 1) = '0' THEN
    _phone := substring(_phone from 2);
  END IF;
  IF length(_phone) NOT IN (10, 11) THEN
    _phone := NULL;
  END IF;

  -- Check phone uniqueness if provided
  IF _phone IS NOT NULL THEN
    SELECT COUNT(*) INTO _existing_count FROM public.profiles WHERE phone_whatsapp = _phone;
    IF _existing_count > 0 THEN
      RAISE EXCEPTION 'Phone already registered' USING ERRCODE = '23505';
    END IF;
  END IF;

  INSERT INTO public.profiles (id, email, full_name, phone_whatsapp)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
    _phone
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
