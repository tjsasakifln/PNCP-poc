-- ============================================================================
-- DOWN: search_datalake_use_portuguese_smartlic — reverses
--       20260415120001_search_datalake_use_portuguese_smartlic.sql
-- Date: 2026-04-16
-- Story: STORY-5.4 AC3 (TD-SYS-015)
-- ============================================================================
-- Context:
--   Up migration changed all FTS parsing in public.search_datalake from
--   the builtin 'portuguese' config to 'public.portuguese_smartlic'
--   (to_tsquery / plainto_tsquery / websearch_to_tsquery).
--
--   This down file restores the version from the PREVIOUS migration:
--   20260414133000_search_datalake_coalesce_dates.sql, which used the
--   builtin 'portuguese' config.
--
--   Grants and function signature are unchanged.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.search_datalake(
    p_ufs            TEXT[]       DEFAULT NULL,
    p_date_start     DATE         DEFAULT NULL,
    p_date_end       DATE         DEFAULT NULL,
    p_tsquery        TEXT         DEFAULT NULL,
    p_websearch_text TEXT         DEFAULT NULL,
    p_modalidades    INTEGER[]    DEFAULT NULL,
    p_valor_min      NUMERIC      DEFAULT NULL,
    p_valor_max      NUMERIC      DEFAULT NULL,
    p_esferas        TEXT[]       DEFAULT NULL,
    p_modo           TEXT         DEFAULT 'publicacao',
    p_limit          INTEGER      DEFAULT 2000,
    p_embedding      VECTOR(256)  DEFAULT NULL
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
    ts_rank              REAL
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_ts_query      TSQUERY;
    v_ws_query      TSQUERY;
    v_combined_q    TSQUERY;
    v_limit         INTEGER;
    v_cos_threshold FLOAT := 0.6;
BEGIN
    IF p_modo NOT IN ('publicacao', 'abertas') THEN
        RAISE EXCEPTION 'p_modo must be ''publicacao'' or ''abertas'', got: %', p_modo;
    END IF;

    v_limit := LEAST(COALESCE(p_limit, 2000), 5000);

    IF p_tsquery IS NOT NULL AND trim(p_tsquery) <> '' THEN
        BEGIN
            v_ts_query := to_tsquery('portuguese', p_tsquery);
        EXCEPTION WHEN OTHERS THEN
            v_ts_query := plainto_tsquery('portuguese', p_tsquery);
        END;
    END IF;

    IF p_websearch_text IS NOT NULL AND trim(p_websearch_text) <> '' THEN
        BEGIN
            v_ws_query := websearch_to_tsquery('portuguese', p_websearch_text);
        EXCEPTION WHEN OTHERS THEN
            v_ws_query := plainto_tsquery('portuguese', p_websearch_text);
        END;
    END IF;

    IF v_ts_query IS NOT NULL AND v_ws_query IS NOT NULL THEN
        v_combined_q := v_ts_query && v_ws_query;
    ELSIF v_ts_query IS NOT NULL THEN
        v_combined_q := v_ts_query;
    ELSIF v_ws_query IS NOT NULL THEN
        v_combined_q := v_ws_query;
    ELSE
        v_combined_q := NULL;
    END IF;

    RETURN QUERY
    SELECT
        b.pncp_id, b.uf, b.municipio, b.orgao_razao_social, b.orgao_cnpj,
        b.objeto_compra, b.valor_total_estimado, b.modalidade_id,
        b.modalidade_nome, b.situacao_compra, b.data_publicacao,
        b.data_abertura, b.data_encerramento, b.link_pncp, b.esfera_id,
        CASE
            WHEN p_embedding IS NOT NULL AND v_combined_q IS NOT NULL
                 THEN (0.4 * ts_rank(b.tsv, v_combined_q) + 0.6 * (1.0 - (b.embedding <=> p_embedding)))::REAL
            WHEN p_embedding IS NOT NULL
                 THEN (1.0 - (b.embedding <=> p_embedding))::REAL
            WHEN v_combined_q IS NOT NULL
                 THEN ts_rank(b.tsv, v_combined_q)::REAL
            ELSE 0.0::REAL
        END AS ts_rank
    FROM public.pncp_raw_bids b
    WHERE
        b.is_active = true
        AND (p_ufs IS NULL        OR b.uf = ANY(p_ufs))
        AND (p_modalidades IS NULL OR b.modalidade_id = ANY(p_modalidades))
        AND (p_esferas IS NULL    OR b.esfera_id = ANY(p_esferas))
        AND (p_valor_min IS NULL  OR b.valor_total_estimado >= p_valor_min)
        AND (p_valor_max IS NULL  OR b.valor_total_estimado <= p_valor_max)
        AND (
            v_combined_q IS NULL
            OR b.tsv @@ v_combined_q
            OR (p_embedding IS NOT NULL AND b.embedding IS NOT NULL
                AND (1.0 - (b.embedding <=> p_embedding)) > v_cos_threshold)
        )
        AND (
            p_modo <> 'publicacao'
            OR (
                (p_date_start IS NULL
                 OR COALESCE(b.data_publicacao, b.ingested_at) >= p_date_start::TIMESTAMPTZ)
                AND
                (p_date_end   IS NULL
                 OR COALESCE(b.data_publicacao, b.ingested_at) <  (p_date_end + INTERVAL '1 day')::TIMESTAMPTZ)
            )
        )
        AND (
            p_modo <> 'abertas'
            OR COALESCE(b.data_encerramento, b.ingested_at + INTERVAL '30 days') > now()
        )
    ORDER BY
        CASE
            WHEN p_embedding IS NOT NULL AND v_combined_q IS NOT NULL
                 THEN (0.4 * ts_rank(b.tsv, v_combined_q) + 0.6 * (1.0 - (b.embedding <=> p_embedding)))
            WHEN p_embedding IS NOT NULL
                 THEN (1.0 - (b.embedding <=> p_embedding))
            WHEN v_combined_q IS NOT NULL
                 THEN ts_rank(b.tsv, v_combined_q)::FLOAT
            ELSE NULL
        END DESC NULLS LAST,
        b.data_publicacao DESC NULLS LAST
    LIMIT v_limit;
END;
$$;

COMMENT ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER, VECTOR) IS
    'STORY-2.12 AC3: hybrid search with COALESCE-based date fallbacks. '
    'FTS parsing uses builtin ''portuguese'' config (pre-STORY-5.4).';

GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER, VECTOR) TO authenticated;
GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER, VECTOR) TO service_role;
