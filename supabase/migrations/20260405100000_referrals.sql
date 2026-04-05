-- SEO-PLAYBOOK: Referral program — 1 month free per conversion
-- Enables viral growth via shareable referral codes

-- ---------------------------------------------------------------------------
-- Function: generate_referral_code()
-- Returns 8-char alphanumeric (uppercase A-Z, 0-9) unique code
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.generate_referral_code()
RETURNS text
LANGUAGE plpgsql
VOLATILE
AS $$
DECLARE
  alphabet text := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  code text := '';
  i int;
BEGIN
  FOR i IN 1..8 LOOP
    code := code || substr(alphabet, floor(random() * length(alphabet) + 1)::int, 1);
  END LOOP;
  RETURN code;
END;
$$;

-- ---------------------------------------------------------------------------
-- Table: referrals
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.referrals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  referrer_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  referred_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  code TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'signed_up', 'converted', 'credited')),
  created_at TIMESTAMPTZ DEFAULT now(),
  converted_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON public.referrals(referrer_user_id);
CREATE INDEX IF NOT EXISTS idx_referrals_code ON public.referrals(code);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON public.referrals(status);

-- ---------------------------------------------------------------------------
-- RLS: referrers can view their own records; service_role has full access
-- ---------------------------------------------------------------------------
ALTER TABLE public.referrals ENABLE ROW LEVEL SECURITY;

-- Authenticated referrers can read rows where they are the referrer
CREATE POLICY "referrals_select_own"
  ON public.referrals
  FOR SELECT
  TO authenticated
  USING (auth.uid() = referrer_user_id);

-- Authenticated users can insert rows where they are the referrer (for signup redeem)
CREATE POLICY "referrals_insert_own"
  ON public.referrals
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = referrer_user_id);

-- Service role bypasses RLS by default; add explicit policy for clarity
CREATE POLICY "referrals_service_all"
  ON public.referrals
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

COMMENT ON TABLE public.referrals IS
  'Referral program — tracks codes, signups, and conversions for 1-month-free credit.';
COMMENT ON COLUMN public.referrals.status IS
  'pending=code issued; signed_up=referred user signed up; converted=paid subscription; credited=referrer month credited';
