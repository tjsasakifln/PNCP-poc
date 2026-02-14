-- Migration 024: Add context_data column to profiles for onboarding contextualization
-- STORY-247: Onboarding Profundo — Perfil de Contextualização
--
-- Stores business context collected during onboarding wizard:
-- - ufs_atuacao (string[]): States where company operates
-- - faixa_valor_min/max (float): Contract value range
-- - porte_empresa (enum): ME, EPP, MEDIO, GRANDE
-- - modalidades_interesse (int[]): Preferred procurement modalities
-- - palavras_chave (string[]): Business-specific keywords
-- - experiencia_licitacoes (enum): PRIMEIRA_VEZ, INICIANTE, EXPERIENTE

ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS context_data jsonb DEFAULT '{}'::jsonb;

-- Index for querying users by porte_empresa (future analytics/filtering)
CREATE INDEX IF NOT EXISTS idx_profiles_context_porte
  ON public.profiles USING btree (((context_data->>'porte_empresa')))
  WHERE context_data->>'porte_empresa' IS NOT NULL;

-- Update handle_new_user trigger to include context_data default
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, company, sector, phone_whatsapp, whatsapp_consent, context_data)
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', ''),
    COALESCE(new.raw_user_meta_data->>'company', ''),
    COALESCE(new.raw_user_meta_data->>'sector', ''),
    COALESCE(new.raw_user_meta_data->>'phone_whatsapp', ''),
    COALESCE((new.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
    '{}'::jsonb
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON COLUMN public.profiles.context_data IS
  'Business context from onboarding wizard (STORY-247). Schema: {ufs_atuacao, faixa_valor_min, faixa_valor_max, porte_empresa, modalidades_interesse, palavras_chave, experiencia_licitacoes}';
