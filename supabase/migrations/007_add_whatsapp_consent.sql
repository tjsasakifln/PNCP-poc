-- ============================================================
-- Smart PNCP: STORY-166 - Marketing Consent & Sector Fields
-- ============================================================
-- Adds phone number, sector, and marketing consent fields to profiles
-- for Email and WhatsApp promotional communications (LGPD compliant)
-- ============================================================

-- 1. Add new columns to profiles table
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS sector TEXT,
  ADD COLUMN IF NOT EXISTS phone_whatsapp TEXT,
  ADD COLUMN IF NOT EXISTS whatsapp_consent BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS whatsapp_consent_at TIMESTAMPTZ;

-- 2. Add check constraint for phone format (Brazilian)
-- Accepts: 10-11 digits (with or without formatting)
ALTER TABLE public.profiles
  ADD CONSTRAINT phone_whatsapp_format CHECK (
    phone_whatsapp IS NULL OR
    phone_whatsapp ~ '^[0-9]{10,11}$'
  );

-- 3. Create index for querying consented users (marketing campaigns)
CREATE INDEX IF NOT EXISTS idx_profiles_whatsapp_consent
  ON public.profiles(whatsapp_consent)
  WHERE whatsapp_consent = TRUE;

-- 4. Update trigger to handle new fields from user_metadata
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (
    id,
    email,
    full_name,
    company,
    sector,
    avatar_url,
    phone_whatsapp,
    whatsapp_consent,
    whatsapp_consent_at
  )
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'),
    new.raw_user_meta_data->>'company',
    new.raw_user_meta_data->>'sector',
    new.raw_user_meta_data->>'avatar_url',
    new.raw_user_meta_data->>'phone_whatsapp',
    COALESCE((new.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
    CASE
      WHEN (new.raw_user_meta_data->>'whatsapp_consent')::boolean = TRUE
      THEN NOW()
      ELSE NULL
    END
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Comment for documentation
COMMENT ON COLUMN public.profiles.sector IS 'User business sector (vestuario, alimentos, informatica, etc. or custom text)';
COMMENT ON COLUMN public.profiles.phone_whatsapp IS 'Brazilian phone number (10-11 digits, no formatting)';
COMMENT ON COLUMN public.profiles.whatsapp_consent IS 'User consented to receive promotional Email and WhatsApp messages';
COMMENT ON COLUMN public.profiles.whatsapp_consent_at IS 'Timestamp when user gave consent (LGPD audit trail)';
