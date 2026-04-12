-- ============================================================
-- Migration: 20260412000001_search_trigram_fallback_rpc
-- Story:     STORY-437 AC3
-- Purpose:   New RPC search_datalake_trigram_fallback
--            Called when FTS returns 0 results as a fuzzy safety net.
--            Uses pg_trgm word_similarity (already enabled on the cluster).
-- ============================================================

CREATE OR REPLACE FUNCTION public.search_datalake_trigram_fallback(
    p_query_term TEXT,
    p_ufs        TEXT[]  DEFAULT NULL,
    p_limit      INTEGER DEFAULT 200
)
RETURNS TABLE (
    pncp_id              TEXT,
    uf                   TEXT,
    municipio            TEXT,
    orgao_razao_social   TEXT,
    orgao_cnpj           TEXT,
    objeto_compra        TEXT,
    valor_total_estimado NUMERIC,
    modalidade_id        INTEGER,
    modalidade_nome      TEXT,
    situacao_compra      TEXT,
    data_publicacao      TIMESTAMPTZ,
    data_abertura        TIMESTAMPTZ,
    data_encerramento    TIMESTAMPTZ,
    link_pncp            TEXT,
    esfera_id            TEXT,
    ts_rank              REAL,
    sim_score            REAL
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT
        b.pncp_id,
        b.uf,
        b.municipio,
        b.orgao_razao_social,
        b.orgao_cnpj,
        b.objeto_compra,
        b.valor_total_estimado,
        b.modalidade_id,
        b.modalidade_nome,
        b.situacao_compra,
        b.data_publicacao,
        b.data_abertura,
        b.data_encerramento,
        b.link_pncp,
        b.esfera_id,
        0.0::REAL                                              AS ts_rank,
        word_similarity(p_query_term, b.objeto_compra)::REAL  AS sim_score
    FROM public.pncp_raw_bids b
    WHERE
        b.is_active = true
        AND (p_ufs IS NULL OR b.uf = ANY(p_ufs))
        AND word_similarity(p_query_term, b.objeto_compra) > 0.3
    ORDER BY sim_score DESC
    LIMIT LEAST(p_limit, 500);
$$;

COMMENT ON FUNCTION public.search_datalake_trigram_fallback(TEXT, TEXT[], INTEGER) IS
    'Fuzzy trigram fallback search (STORY-437 AC3). '
    'Called when FTS (search_datalake) returns 0 results. '
    'Uses pg_trgm word_similarity > 0.3 on objeto_compra. '
    'Returns same columns as search_datalake plus sim_score. '
    'SECURITY DEFINER: caller needs only EXECUTE.';

-- Restrict to service_role only (same policy as search_datalake)
REVOKE ALL ON FUNCTION public.search_datalake_trigram_fallback(TEXT, TEXT[], INTEGER) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.search_datalake_trigram_fallback(TEXT, TEXT[], INTEGER) TO service_role;
