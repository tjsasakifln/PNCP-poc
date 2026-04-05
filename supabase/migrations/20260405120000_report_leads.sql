-- SEO-PLAYBOOK: Report lead capture — Panorama Licitações 2026 T1
-- Captures email leads from the gated report download flow.
-- Upserts on (email, source) for idempotent resubmits.

-- ---------------------------------------------------------------------------
-- Table: report_leads
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.report_leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL,
  empresa TEXT NOT NULL,
  cargo TEXT NOT NULL
    CHECK (cargo IN ('diretor', 'gerente', 'analista', 'consultor', 'outro')),
  newsletter_opt_in BOOLEAN NOT NULL DEFAULT false,
  source TEXT NOT NULL DEFAULT 'panorama-2026-t1',
  ip_hash TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT report_leads_email_source_unique UNIQUE (email, source)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_report_leads_source_created
  ON public.report_leads(source, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_leads_email
  ON public.report_leads(email);

-- ---------------------------------------------------------------------------
-- RLS: service role full access; anon/authenticated blocked by default
-- The backend endpoint uses the service_role key to insert, so no
-- authenticated-user INSERT policy is required. SELECT is restricted to
-- service_role to prevent enumeration of captured leads.
-- ---------------------------------------------------------------------------
ALTER TABLE public.report_leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "report_leads_service_all"
  ON public.report_leads
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

COMMENT ON TABLE public.report_leads IS
  'Lead capture for gated report downloads (e.g. Panorama 2026 T1). Dedup by (email, source).';
COMMENT ON COLUMN public.report_leads.source IS
  'Identifier of the report / campaign. Allows multi-report reuse of the same table.';
COMMENT ON COLUMN public.report_leads.ip_hash IS
  'First 16 chars of SHA-256 of client IP — abuse signal only, not PII.';
