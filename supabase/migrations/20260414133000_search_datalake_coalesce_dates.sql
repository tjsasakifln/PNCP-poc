-- ============================================================================
-- STORY-2.12 (TD-DB-015) AC3 EPIC-TD-2026Q2: search_datalake date-filter
-- COALESCE fallback to ingested_at for resilient period queries.
-- Date: 2026-04-14
-- ============================================================================
-- Context:
--   Even after the STORY-2.12 AC2 backfill + AC4 transformer fallback, we
--   still want the runtime query to be resilient: if a future ingestion bug
--   lands a NULL data_publicacao, the row should STILL be discoverable by
--   period search (using ingested_at as last-resort) instead of vanishing.
--
--   This migration is a targeted wrapper around
--   20260413000001_search_datalake_hybrid.sql. The body is preserved byte-for-
--   byte except:
--     * Period filter for p_modo='publicacao' wraps data_publicacao in
--       COALESCE(data_publicacao, ingested_at).
--     * Period filter for p_modo='abertas' wraps data_encerramento in
--       COALESCE(data_encerramento, ingested_at + INTERVAL '30 days')
--       so missing-encerramento rows remain visible in the 'abertas' slice
--       for at least ~1 month after ingestion (bounded exposure — not
--       permanent).
--
--   Signature, return shape, COMMENT semantics, GRANTs and hybrid-scoring
--   logic are identical to the hybrid migration.
-- ============================================================================

-- Use CREATE OR REPLACE (same signature); no DROP needed.

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
    -- Validate p_modo
    IF p_modo NOT IN ('publicacao', 'abertas') THEN
        RAISE EXCEPTION 'p_modo must be ''publicacao'' or ''abertas'', got: %', p_modo;
    END IF;

    -- Cap limit at 5000 to prevent runaway queries
    v_limit := LEAST(COALESCE(p_limit, 2000), 5000);

    -- Parse sector keywords tsquery (OR-joined by Python caller)
    IF p_tsquery IS NOT NULL AND trim(p_tsquery) <> '' THEN
        BEGIN
            v_ts_query := to_tsquery('portuguese', p_tsquery);
        EXCEPTION WHEN OTHERS THEN
            v_ts_query := plainto_tsquery('portuguese', p_tsquery);
        END;
    END IF;

    -- Parse websearch query for custom user terms (supports "phrase", -exclusion)
    IF p_websearch_text IS NOT NULL AND trim(p_websearch_text) <> '' THEN
        BEGIN
            v_ws_query := websearch_to_tsquery('portuguese', p_websearch_text);
        EXCEPTION WHEN OTHERS THEN
            v_ws_query := plainto_tsquery('portuguese', p_websearch_text);
        END;
    END IF;

    -- Combine: when both present, AND them together
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
        -- Hybrid score: FTS + cosine similarity (unchanged from hybrid migration)
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

        -- UF filter
        AND (p_ufs IS NULL        OR b.uf = ANY(p_ufs))

        -- Modality filter
        AND (p_modalidades IS NULL OR b.modalidade_id = ANY(p_modalidades))

        -- Sphere filter
        AND (p_esferas IS NULL    OR b.esfera_id = ANY(p_esferas))

        -- Value range
        AND (p_valor_min IS NULL  OR b.valor_total_estimado >= p_valor_min)
        AND (p_valor_max IS NULL  OR b.valor_total_estimado <= p_valor_max)

        -- Full-text OR semantic match (OR so either path can find results)
        AND (
            v_combined_q IS NULL
            OR b.tsv @@ v_combined_q
            OR (p_embedding IS NOT NULL AND b.embedding IS NOT NULL
                AND (1.0 - (b.embedding <=> p_embedding)) > v_cos_threshold)
        )

        -- STORY-2.12 AC3: date filter for 'publicacao' uses COALESCE fallback
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

        -- STORY-2.12 AC3: 'abertas' mode — fall back to ingested_at + 30d when
        -- data_encerramento is NULL so recently-ingested rows with missing
        -- deadline are temporarily visible (not permanently, to avoid staleness).
        AND (
            p_modo <> 'abertas'
            OR COALESCE(b.data_encerramento, b.ingested_at + INTERVAL '30 days') > now()
        )

    ORDER BY
        -- Hybrid score descending (unchanged from hybrid migration)
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
    'Otherwise identical to STORY-438 hybrid behaviour: FTS ts_rank + pgvector '
    'cosine similarity, p_embedding=NULL path unchanged. '
    'Period filter coalesces data_publicacao -> ingested_at; abertas filter '
    'coalesces data_encerramento -> ingested_at + 30 days.';

-- Grants unchanged (same signature as hybrid migration, but be explicit
-- since CREATE OR REPLACE does not re-grant).
GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER, VECTOR) TO authenticated;
GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER, VECTOR) TO service_role;
