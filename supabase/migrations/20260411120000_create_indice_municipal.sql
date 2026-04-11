-- STORY-435: Índice SmartLic de Transparência Municipal em Compras Públicas
--
-- Context:
--   Cria tabela para armazenar o índice trimestral de transparência calculado
--   para cada município a partir dos dados do pncp_raw_bids. Calculado sob demanda
--   pelo endpoint GET /v1/indice-municipal e persistido para consultas rápidas.
--
-- Scope:
--   * Tabela pública indice_municipal (5 scores + ranking + meta)
--   * UNIQUE(municipio_nome, uf, periodo) para upsert idempotente
--   * 3 índices: período, uf+período, score (ranking)
--   * RLS: leitura pública sem restrição (dados agregados, não PII)

CREATE TABLE IF NOT EXISTS public.indice_municipal (
    id                          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    municipio_nome              TEXT NOT NULL,
    municipio_ibge_code         TEXT,
    uf                          CHAR(2) NOT NULL,
    periodo                     TEXT NOT NULL,  -- "2026-Q1", "2026-Q2", ...
    score_total                 NUMERIC(5,2),   -- 0-100 (soma dos 5 scores)
    score_volume_publicacao     NUMERIC(5,2),   -- 0-20 pts
    score_eficiencia_temporal   NUMERIC(5,2),   -- 0-20 pts
    score_diversidade_mercado   NUMERIC(5,2),   -- 0-20 pts
    score_transparencia_digital NUMERIC(5,2),   -- 0-20 pts
    score_consistencia          NUMERIC(5,2),   -- 0-20 pts
    total_editais               INTEGER NOT NULL DEFAULT 0,
    ranking_nacional            INTEGER,
    ranking_uf                  INTEGER,
    percentil                   INTEGER,        -- 0-100
    calculado_em                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(municipio_nome, uf, periodo)
);

-- Indexes para queries frequentes
CREATE INDEX IF NOT EXISTS idx_indice_municipal_periodo
    ON indice_municipal(periodo);

CREATE INDEX IF NOT EXISTS idx_indice_municipal_uf_periodo
    ON indice_municipal(uf, periodo);

CREATE INDEX IF NOT EXISTS idx_indice_municipal_score_desc
    ON indice_municipal(score_total DESC NULLS LAST);

-- RLS: tabela pública — todos podem ler (dados agregados, sem PII)
ALTER TABLE public.indice_municipal ENABLE ROW LEVEL SECURITY;

CREATE POLICY "indice_municipal_public_read"
    ON public.indice_municipal
    FOR SELECT
    USING (true);

-- service_role pode inserir/atualizar (jobs de cálculo)
CREATE POLICY "indice_municipal_service_write"
    ON public.indice_municipal
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

COMMENT ON TABLE public.indice_municipal IS
    'Índice SmartLic de Transparência Municipal — ranking trimestral de 5.570 municípios '
    'calculado a partir de pncp_raw_bids. 5 dimensões (0-20 pts cada) = score 0-100. '
    'Mínimo 10 editais por município para inclusão no ranking. '
    'Fonte pública, licença CC BY 4.0.';
