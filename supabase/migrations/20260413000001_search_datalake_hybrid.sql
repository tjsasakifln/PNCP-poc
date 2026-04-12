-- ============================================================
-- Migration: 20260413000001_search_datalake_hybrid
-- Story:     STORY-438 AC2 + AC3
-- Purpose:   Hybrid search: FTS ts_rank + cosine similarity (pgvector).
--            Also updates upsert_pncp_raw_bids to accept optional embedding.
-- Pre-requisite: 20260413000000_pgvector_embeddings.sql applied.
-- ============================================================

-- ============================================================
-- SECTION 1: Updated search_datalake with hybrid scoring
-- Adds p_embedding VECTOR(256) parameter.
-- When NULL: 100% identical to post-STORY-437 behavior.
-- When set: hybrid score = 0.4 * ts_rank + 0.6 * cosine_similarity
-- ============================================================

DROP FUNCTION IF EXISTS public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER);

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
        -- Hybrid score: FTS + cosine similarity
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

        -- Date mode: 'publicacao'
        AND (
            p_modo <> 'publicacao'
            OR (
                (p_date_start IS NULL OR b.data_publicacao >= p_date_start::TIMESTAMPTZ)
                AND
                (p_date_end   IS NULL OR b.data_publicacao <  (p_date_end + INTERVAL '1 day')::TIMESTAMPTZ)
            )
        )

        -- Date mode: 'abertas' — ALL open bids
        AND (
            p_modo <> 'abertas'
            OR b.data_encerramento > now()
        )

    ORDER BY
        -- Hybrid score descending
        CASE
            WHEN p_embedding IS NOT NULL AND v_combined_q IS NOT NULL
                 THEN (0.4 * ts_rank(b.tsv, v_combined_q) + 0.6 * (1.0 - (b.embedding <=> p_embedding)))
            WHEN p_embedding IS NOT NULL
                 THEN (1.0 - (b.embedding <=> p_embedding))
            WHEN v_combined_q IS NOT NULL
                 THEN ts_rank(b.tsv, v_combined_q)::FLOAT
            ELSE NULL
        END DESC NULLS LAST,
        b.data_publicacao DESC

    LIMIT v_limit;
END;
$$;

COMMENT ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER, VECTOR) IS
    'Hybrid search: FTS ts_rank + pgvector cosine similarity (STORY-437 + STORY-438). '
    'p_embedding=NULL: identical to STORY-437 behavior (zero breaking change). '
    'p_embedding set: hybrid score = 0.4*ts_rank + 0.6*cosine_similarity. '
    'WHERE uses OR so either FTS or semantic path can find results. '
    'SECURITY DEFINER; tsquery errors fall back to plainto_tsquery.';

GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER, VECTOR) TO authenticated;
GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER, VECTOR) TO service_role;

-- ============================================================
-- SECTION 2: Updated upsert_pncp_raw_bids to accept optional embedding
-- The embedding field is optional in the JSONB payload — NULL when
-- EMBEDDING_ENABLED=false (no breaking change for existing ingestion).
-- ============================================================

CREATE OR REPLACE FUNCTION public.upsert_pncp_raw_bids(p_records JSONB)
RETURNS TABLE(inserted INT, updated INT, unchanged INT)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_total     INT;
    v_affected  INT;
    v_inserted  INT;
    v_updated   INT;
BEGIN
    IF p_records IS NULL OR jsonb_array_length(p_records) = 0 THEN
        RETURN QUERY SELECT 0, 0, 0;
        RETURN;
    END IF;

    v_total := jsonb_array_length(p_records);

    -- Single-statement batch upsert with optional embedding field.
    -- embedding is nullable — existing rows without embedding are preserved.
    -- When embedding IS NOT NULL and existing row has NULL: update triggered
    -- even if content_hash is unchanged (OR condition on embedding).
    WITH deduped AS (
        SELECT DISTINCT ON (r.pncp_id)
            r.*
        FROM jsonb_to_recordset(p_records) AS r(
            pncp_id              TEXT,
            objeto_compra        TEXT,
            valor_total_estimado NUMERIC,
            modalidade_id        INTEGER,
            modalidade_nome      TEXT,
            situacao_compra      TEXT,
            esfera_id            TEXT,
            uf                   TEXT,
            municipio            TEXT,
            codigo_municipio_ibge TEXT,
            orgao_razao_social   TEXT,
            orgao_cnpj           TEXT,
            unidade_nome         TEXT,
            data_publicacao      TIMESTAMPTZ,
            data_abertura        TIMESTAMPTZ,
            data_encerramento    TIMESTAMPTZ,
            link_sistema_origem  TEXT,
            link_pncp            TEXT,
            content_hash         TEXT,
            source               TEXT,
            crawl_batch_id       TEXT,
            is_active            BOOLEAN,
            embedding            VECTOR(256)
        )
        ORDER BY r.pncp_id
    ),
    upserted AS (
        INSERT INTO public.pncp_raw_bids (
            pncp_id,
            objeto_compra,
            valor_total_estimado,
            modalidade_id,
            modalidade_nome,
            situacao_compra,
            esfera_id,
            uf,
            municipio,
            codigo_municipio_ibge,
            orgao_razao_social,
            orgao_cnpj,
            unidade_nome,
            data_publicacao,
            data_abertura,
            data_encerramento,
            link_sistema_origem,
            link_pncp,
            content_hash,
            ingested_at,
            updated_at,
            source,
            crawl_batch_id,
            is_active,
            embedding
        )
        SELECT
            r.pncp_id,
            r.objeto_compra,
            r.valor_total_estimado,
            r.modalidade_id,
            r.modalidade_nome,
            r.situacao_compra,
            r.esfera_id,
            r.uf,
            r.municipio,
            r.codigo_municipio_ibge,
            r.orgao_razao_social,
            r.orgao_cnpj,
            r.unidade_nome,
            r.data_publicacao,
            r.data_abertura,
            r.data_encerramento,
            r.link_sistema_origem,
            r.link_pncp,
            r.content_hash,
            now(),
            now(),
            COALESCE(r.source, 'pncp'),
            r.crawl_batch_id,
            COALESCE(r.is_active, true),
            r.embedding
        FROM deduped r
        ON CONFLICT (pncp_id) DO UPDATE SET
            objeto_compra         = EXCLUDED.objeto_compra,
            valor_total_estimado  = EXCLUDED.valor_total_estimado,
            modalidade_nome       = EXCLUDED.modalidade_nome,
            situacao_compra       = EXCLUDED.situacao_compra,
            esfera_id             = EXCLUDED.esfera_id,
            municipio             = EXCLUDED.municipio,
            codigo_municipio_ibge = EXCLUDED.codigo_municipio_ibge,
            orgao_razao_social    = EXCLUDED.orgao_razao_social,
            orgao_cnpj            = EXCLUDED.orgao_cnpj,
            unidade_nome          = EXCLUDED.unidade_nome,
            data_publicacao       = EXCLUDED.data_publicacao,
            data_abertura         = EXCLUDED.data_abertura,
            data_encerramento     = EXCLUDED.data_encerramento,
            link_sistema_origem   = EXCLUDED.link_sistema_origem,
            link_pncp             = EXCLUDED.link_pncp,
            content_hash          = EXCLUDED.content_hash,
            updated_at            = now(),
            crawl_batch_id        = EXCLUDED.crawl_batch_id,
            is_active             = EXCLUDED.is_active,
            -- Update embedding when: content changed OR new embedding provided for null row
            embedding             = CASE
                WHEN EXCLUDED.embedding IS NOT NULL THEN EXCLUDED.embedding
                ELSE public.pncp_raw_bids.embedding
            END
        WHERE
            public.pncp_raw_bids.content_hash IS DISTINCT FROM EXCLUDED.content_hash
            OR (EXCLUDED.embedding IS NOT NULL AND public.pncp_raw_bids.embedding IS NULL)
        RETURNING (xmax = 0) AS is_insert
    )
    SELECT
        count(*) FILTER (WHERE is_insert)::INT,
        count(*) FILTER (WHERE NOT is_insert)::INT
    INTO v_inserted, v_updated
    FROM upserted;

    RETURN QUERY SELECT v_inserted, v_updated, (v_total - v_inserted - v_updated)::INT;
END;
$$;

COMMENT ON FUNCTION public.upsert_pncp_raw_bids(JSONB) IS
    'Batch upsert for PNCP bids with optional embedding support (STORY-438 AC2). '
    'embedding field is optional in JSONB payload — NULL when EMBEDDING_ENABLED=false. '
    'Updates embedding when: content changed OR new embedding provided for null row. '
    'SECURITY DEFINER so ingestion worker needs only EXECUTE, not table INSERT.';

GRANT EXECUTE ON FUNCTION public.upsert_pncp_raw_bids(JSONB) TO service_role;
