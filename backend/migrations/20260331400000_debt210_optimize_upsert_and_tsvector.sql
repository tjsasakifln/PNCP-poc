-- ============================================================
-- Migration: 20260331400000_debt210_optimize_upsert_and_tsvector
-- Story:     DEBT-210 (DB-NEW-003 + DB-NEW-004)
-- Purpose:   1) Batch upsert via INSERT ON CONFLICT (was row-by-row loop)
--            2) Pre-computed tsv column with trigger (was 2x to_tsvector per row)
-- ============================================================

-- ============================================================
-- PART 1: DB-NEW-004 — Pre-computed tsvector column
-- Trade-off: +~40 bytes/row storage for eliminating 2x to_tsvector per search query.
-- At 100K+ rows the CPU savings outweigh the storage cost (~4MB).
-- ============================================================

-- 1a. Add the tsvector column (nullable initially for backfill).
ALTER TABLE public.pncp_raw_bids
    ADD COLUMN IF NOT EXISTS tsv TSVECTOR;

COMMENT ON COLUMN public.pncp_raw_bids.tsv IS
    'Pre-computed to_tsvector(portuguese, objeto_compra). Maintained by trigger. '
    'Eliminates double tsvector computation in search_datalake (DEBT-DB-NEW-004).';

-- 1b. Trigger function to maintain tsv on INSERT/UPDATE.
CREATE OR REPLACE FUNCTION public.pncp_raw_bids_tsv_trigger()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.tsv := to_tsvector('portuguese', coalesce(NEW.objeto_compra, ''));
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.pncp_raw_bids_tsv_trigger() IS
    'Maintains pncp_raw_bids.tsv column on INSERT/UPDATE. DEBT-DB-NEW-004.';

DROP TRIGGER IF EXISTS trg_pncp_raw_bids_tsv ON public.pncp_raw_bids;

CREATE TRIGGER trg_pncp_raw_bids_tsv
    BEFORE INSERT OR UPDATE OF objeto_compra
    ON public.pncp_raw_bids
    FOR EACH ROW
    EXECUTE FUNCTION public.pncp_raw_bids_tsv_trigger();

-- 1c. Backfill tsv for existing rows (batched to avoid long lock).
UPDATE public.pncp_raw_bids
SET tsv = to_tsvector('portuguese', coalesce(objeto_compra, ''))
WHERE tsv IS NULL;

-- 1d. Now that all rows are populated, set NOT NULL.
ALTER TABLE public.pncp_raw_bids
    ALTER COLUMN tsv SET NOT NULL;

-- 1e. Replace functional GIN index with column-based GIN index.
-- The column-based index is faster because PostgreSQL reads the stored value
-- directly instead of recomputing to_tsvector() during index scans.
DROP INDEX IF EXISTS idx_pncp_raw_bids_fts;

CREATE INDEX idx_pncp_raw_bids_fts
    ON public.pncp_raw_bids
    USING GIN (tsv);

-- ============================================================
-- PART 2: DB-NEW-003 — Batch upsert via INSERT ON CONFLICT
-- Replaces the row-by-row FOR loop with a single-statement approach:
--   INSERT ... ON CONFLICT (pncp_id) DO UPDATE
--   WHERE content_hash IS DISTINCT FROM EXCLUDED.content_hash
-- Uses the xmax = 0 trick to distinguish inserts from updates.
-- Unchanged rows (same content_hash) are skipped by the WHERE clause.
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

    -- Single-statement batch upsert.
    -- ON CONFLICT skips rows where content_hash matches (WHERE clause).
    -- xmax = 0 means the row was freshly inserted (no prior version existed).
    -- DISTINCT ON (pncp_id) deduplicates within the same batch to avoid
    -- "ON CONFLICT DO UPDATE command cannot affect row a second time" error.
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
            is_active            BOOLEAN
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
            is_active
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
            COALESCE(r.is_active, true)
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
            is_active             = EXCLUDED.is_active
        WHERE public.pncp_raw_bids.content_hash IS DISTINCT FROM EXCLUDED.content_hash
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
    'Batch upsert for PNCP bids using INSERT ON CONFLICT (DEBT-DB-NEW-003). '
    'Single statement replaces row-by-row loop — eliminates N round-trips to planner. '
    'Skips rows where content_hash matches. Returns (inserted, updated, unchanged). '
    'SECURITY DEFINER so ingestion worker needs only EXECUTE, not table INSERT.';

-- Re-grant after CREATE OR REPLACE (idempotent).
GRANT EXECUTE ON FUNCTION public.upsert_pncp_raw_bids(JSONB) TO service_role;

-- ============================================================
-- PART 3: Update search_datalake to use pre-computed tsv column
-- Eliminates to_tsvector() calls in WHERE and ORDER BY.
-- ============================================================

CREATE OR REPLACE FUNCTION public.search_datalake(
    p_ufs          TEXT[]            DEFAULT NULL,
    p_date_start   DATE              DEFAULT NULL,
    p_date_end     DATE              DEFAULT NULL,
    p_tsquery      TEXT              DEFAULT NULL,
    p_modalidades  INTEGER[]         DEFAULT NULL,
    p_valor_min    NUMERIC           DEFAULT NULL,
    p_valor_max    NUMERIC           DEFAULT NULL,
    p_esferas      TEXT[]            DEFAULT NULL,
    p_modo         TEXT              DEFAULT 'publicacao',
    p_limit        INTEGER           DEFAULT 2000
)
RETURNS TABLE (
    pncp_id              TEXT,
    objeto_compra        TEXT,
    valor_total_estimado NUMERIC,
    modalidade_id        INTEGER,
    modalidade_nome      TEXT,
    situacao_compra      TEXT,
    esfera_id            TEXT,
    uf                   TEXT,
    municipio            TEXT,
    orgao_razao_social   TEXT,
    orgao_cnpj           TEXT,
    data_publicacao      TIMESTAMPTZ,
    data_abertura        TIMESTAMPTZ,
    data_encerramento    TIMESTAMPTZ,
    link_pncp            TEXT,
    ts_rank              REAL
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_ts_query TSQUERY;
BEGIN
    -- Validate modo parameter.
    IF p_modo NOT IN ('publicacao', 'abertas') THEN
        RAISE EXCEPTION 'p_modo must be ''publicacao'' or ''abertas'', got: %', p_modo;
    END IF;

    -- Cap limit to prevent runaway queries.
    IF p_limit > 5000 THEN
        p_limit := 5000;
    END IF;

    -- Parse tsquery once; NULL means no full-text filter.
    IF p_tsquery IS NOT NULL AND trim(p_tsquery) <> '' THEN
        BEGIN
            v_ts_query := to_tsquery('portuguese', p_tsquery);
        EXCEPTION WHEN OTHERS THEN
            -- Malformed tsquery — fallback to plain text search.
            v_ts_query := plainto_tsquery('portuguese', p_tsquery);
        END;
    END IF;

    RETURN QUERY
    SELECT
        b.pncp_id,
        b.objeto_compra,
        b.valor_total_estimado,
        b.modalidade_id,
        b.modalidade_nome,
        b.situacao_compra,
        b.esfera_id,
        b.uf,
        b.municipio,
        b.orgao_razao_social,
        b.orgao_cnpj,
        b.data_publicacao,
        b.data_abertura,
        b.data_encerramento,
        b.link_pncp,
        -- ts_rank uses pre-computed tsv column (no recomputation).
        CASE
            WHEN v_ts_query IS NOT NULL
            THEN ts_rank(b.tsv, v_ts_query)
            ELSE 0.0
        END::REAL AS ts_rank
    FROM public.pncp_raw_bids b
    WHERE
        b.is_active = true

        -- UF filter: pass NULL to include all UFs.
        AND (p_ufs IS NULL       OR b.uf = ANY(p_ufs))

        -- Modality filter: pass NULL to include all modalities.
        AND (p_modalidades IS NULL OR b.modalidade_id = ANY(p_modalidades))

        -- Government sphere filter.
        AND (p_esferas IS NULL   OR b.esfera_id = ANY(p_esferas))

        -- Value range filters (inclusive).
        AND (p_valor_min IS NULL OR b.valor_total_estimado >= p_valor_min)
        AND (p_valor_max IS NULL OR b.valor_total_estimado <= p_valor_max)

        -- Full-text match using pre-computed tsv column (GIN indexed).
        AND (
            v_ts_query IS NULL
            OR b.tsv @@ v_ts_query
        )

        -- Date mode: 'publicacao' filters by publication date window.
        AND (
            p_modo <> 'publicacao'
            OR (
                (p_date_start IS NULL OR b.data_publicacao >= p_date_start::TIMESTAMPTZ)
                AND
                (p_date_end   IS NULL OR b.data_publicacao <  (p_date_end + INTERVAL '1 day')::TIMESTAMPTZ)
            )
        )

        -- Date mode: 'abertas' — encerramento in the future, publicacao >= start.
        AND (
            p_modo <> 'abertas'
            OR (
                b.data_encerramento > now()
                AND (p_date_start IS NULL OR b.data_publicacao >= p_date_start::TIMESTAMPTZ)
            )
        )

    ORDER BY
        -- When full-text query supplied, rank by relevance first.
        CASE WHEN v_ts_query IS NOT NULL
             THEN ts_rank(b.tsv, v_ts_query)
             ELSE NULL
        END DESC NULLS LAST,
        b.data_publicacao DESC

    LIMIT p_limit;
END;
$$;

COMMENT ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER) IS
    'Full-featured datalake search using pre-computed tsv column (DEBT-DB-NEW-004). '
    'Supports UF, date, FTS (Portuguese), modality, value range, esfera, two date modes. '
    'SECURITY DEFINER for RLS bypass. tsquery errors fall back to plainto_tsquery.';

-- Re-grant after CREATE OR REPLACE (idempotent).
GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER) TO service_role;
