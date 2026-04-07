-- S3/A2: Leads table for email capture (calculadora, CNPJ, alertas)
CREATE TABLE IF NOT EXISTS public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    source TEXT NOT NULL,
    setor TEXT,
    uf TEXT,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(email, source)
);

-- RLS
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;

-- Service role can do everything
CREATE POLICY leads_service_all ON public.leads
    FOR ALL USING (auth.role() = 'service_role');

-- Anonymous users can insert (lead capture is public)
CREATE POLICY leads_anon_insert ON public.leads
    FOR INSERT WITH CHECK (true);

-- Index for dedup lookups
CREATE INDEX IF NOT EXISTS idx_leads_email_source ON public.leads (email, source);
