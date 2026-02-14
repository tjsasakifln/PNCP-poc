-- STORY-250: Pipeline de Oportunidades
-- Creates pipeline_items table for tracking procurement opportunities through stages

-- ============================================================================
-- Table: pipeline_items
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.pipeline_items (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Snapshot da licitação no momento de salvar
  pncp_id text NOT NULL,
  objeto text NOT NULL,
  orgao text,
  uf text,
  valor_estimado numeric,
  data_encerramento timestamptz,
  link_pncp text,

  -- Pipeline stage
  stage text NOT NULL DEFAULT 'descoberta'
    CHECK (stage IN ('descoberta', 'analise', 'preparando', 'enviada', 'resultado')),
  notes text,

  -- Timestamps
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL,

  -- Prevenir duplicatas por usuário
  UNIQUE(user_id, pncp_id)
);

-- Comentários
COMMENT ON TABLE public.pipeline_items IS 'Pipeline de oportunidades - tracking de licitações por estágio';
COMMENT ON COLUMN public.pipeline_items.stage IS 'Estágio: descoberta → analise → preparando → enviada → resultado';
COMMENT ON COLUMN public.pipeline_items.pncp_id IS 'ID único da licitação no PNCP (snapshot)';

-- ============================================================================
-- Indexes
-- ============================================================================

CREATE INDEX idx_pipeline_user_stage
  ON public.pipeline_items(user_id, stage);

CREATE INDEX idx_pipeline_encerramento
  ON public.pipeline_items(data_encerramento)
  WHERE stage NOT IN ('enviada', 'resultado');

CREATE INDEX idx_pipeline_user_created
  ON public.pipeline_items(user_id, created_at DESC);

-- ============================================================================
-- Auto-update updated_at trigger
-- ============================================================================

CREATE OR REPLACE FUNCTION public.update_pipeline_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_pipeline_items_updated_at
  BEFORE UPDATE ON public.pipeline_items
  FOR EACH ROW
  EXECUTE FUNCTION public.update_pipeline_updated_at();

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

ALTER TABLE public.pipeline_items ENABLE ROW LEVEL SECURITY;

-- Users can only see their own pipeline items
CREATE POLICY "Users can view own pipeline items"
  ON public.pipeline_items
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can only insert their own pipeline items
CREATE POLICY "Users can insert own pipeline items"
  ON public.pipeline_items
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can only update their own pipeline items
CREATE POLICY "Users can update own pipeline items"
  ON public.pipeline_items
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Users can only delete their own pipeline items
CREATE POLICY "Users can delete own pipeline items"
  ON public.pipeline_items
  FOR DELETE
  USING (auth.uid() = user_id);

-- Service role (backend) can manage all pipeline items
CREATE POLICY "Service role full access on pipeline_items"
  ON public.pipeline_items
  FOR ALL
  USING (true);
