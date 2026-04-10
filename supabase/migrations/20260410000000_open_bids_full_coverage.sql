-- ============================================================
-- Migration: Open Bids Full Coverage
--
-- Two changes to ensure 100% of open bids are stored and searchable:
--
-- 1. purge_old_bids() — purge by data_encerramento (not data_publicacao)
--    so bids still open for proposals are NEVER deleted.
--
-- 2. search_datalake() — remove data_publicacao filter in "abertas" mode
--    so users see ALL open bids regardless of publication date.
-- ============================================================

-- ============================================================
-- SECTION 1: Updated purge_old_bids()
-- Purge based on when the bid CLOSED, not when it was published.
-- Default grace: 30 days after data_encerramento.
-- Safety net: bids with NULL data_encerramento purged 180 days
-- after data_publicacao.
-- ============================================================

CREATE OR REPLACE FUNCTION public.purge_old_bids(
    p_retention_days INTEGER DEFAULT 30
)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_deleted INTEGER;
    v_cutoff  TIMESTAMPTZ;
BEGIN
    IF p_retention_days < 1 THEN
        RAISE EXCEPTION 'p_retention_days must be >= 1, got: %', p_retention_days;
    END IF;

    v_cutoff := now() - (p_retention_days || ' days')::INTERVAL;

    DELETE FROM public.pncp_raw_bids
    WHERE is_active = true
      AND (
          -- Bids with known closing date: purge N days after closure
          (data_encerramento IS NOT NULL AND data_encerramento < v_cutoff)
          OR
          -- Bids without closing date: safety net — purge 150 days after
          -- the grace period (effectively 180 days after publication at default)
          (data_encerramento IS NULL
           AND data_publicacao < v_cutoff - INTERVAL '150 days')
      );

    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    RETURN v_deleted;
END;
$$;

COMMENT ON FUNCTION public.purge_old_bids(INTEGER) IS
    'Purges closed bids: deletes rows where data_encerramento < now() - p_retention_days '
    '(default 30). Bids with NULL data_encerramento are purged 180 days after publication '
    'as a safety net. Open bids (data_encerramento in the future) are NEVER purged. '
    'SECURITY DEFINER: caller needs only EXECUTE, not DELETE on the table.';


-- ============================================================
-- SECTION 2: Updated search_datalake()
-- In "abertas" mode, the ONLY filter is data_encerramento > now().
-- No publication date constraint — returns ALL open bids.
-- Must DROP first because CREATE OR REPLACE cannot change return type.
-- ============================================================

DROP FUNCTION IF EXISTS public.search_datalake(TEXT[], DATE, DATE, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER);

CREATE OR REPLACE FUNCTION public.search_datalake(
    p_ufs         TEXT[]             DEFAULT NULL,
    p_date_start  DATE               DEFAULT NULL,
    p_date_end    DATE               DEFAULT NULL,
    p_tsquery     TEXT               DEFAULT NULL,
    p_modalidades INTEGER[]          DEFAULT NULL,
    p_valor_min   NUMERIC            DEFAULT NULL,
    p_valor_max   NUMERIC            DEFAULT NULL,
    p_esferas     TEXT[]             DEFAULT NULL,
    p_modo        TEXT               DEFAULT 'publicacao',
    p_limit       INTEGER            DEFAULT 2000
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
    v_ts_query tsquery;
    v_limit    INTEGER;
BEGIN
    -- Validate p_modo
    IF p_modo NOT IN ('publicacao', 'abertas') THEN
        RAISE EXCEPTION 'p_modo must be ''publicacao'' or ''abertas'', got: %', p_modo;
    END IF;

    -- Cap limit at 5000 to prevent runaway queries
    v_limit := LEAST(COALESCE(p_limit, 2000), 5000);

    -- Parse tsquery with safe fallback
    IF p_tsquery IS NOT NULL AND p_tsquery <> '' THEN
        BEGIN
            v_ts_query := to_tsquery('portuguese', p_tsquery);
        EXCEPTION WHEN OTHERS THEN
            -- Fall back to plainto_tsquery on syntax errors
            v_ts_query := plainto_tsquery('portuguese', p_tsquery);
        END;
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
        CASE WHEN v_ts_query IS NOT NULL
             THEN ts_rank(
                      to_tsvector('portuguese', coalesce(b.objeto_compra, '')),
                      v_ts_query
                  )
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

        -- Full-text match (uses GIN index on to_tsvector expression).
        AND (
            v_ts_query IS NULL
            OR to_tsvector('portuguese', coalesce(b.objeto_compra, '')) @@ v_ts_query
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

        -- Date mode: 'abertas' — ONLY filter: encerramento in the future.
        -- No publication date constraint — returns ALL open bids.
        AND (
            p_modo <> 'abertas'
            OR b.data_encerramento > now()
        )

    ORDER BY
        -- When full-text query supplied, rank by relevance first.
        CASE WHEN v_ts_query IS NOT NULL
             THEN ts_rank(
                      to_tsvector('portuguese', coalesce(b.objeto_compra, '')),
                      v_ts_query
                  )
             ELSE NULL
        END DESC NULLS LAST,
        b.data_publicacao DESC

    LIMIT v_limit;
END;
$$;

COMMENT ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER) IS
    'Full-featured datalake search. Supports UF, date, FTS (Portuguese), '
    'modality, value range, esfera, and two date modes (publicacao / abertas). '
    'In "abertas" mode, returns ALL bids with data_encerramento > now() '
    'regardless of publication date. '
    'SECURITY DEFINER for RLS bypass and consistent index usage. '
    'tsquery parse errors fall back to plainto_tsquery (safe degradation). '
    'Limit is capped at 5000 to prevent runaway queries.';

-- Ensure grants match the original migration
GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION public.purge_old_bids(INTEGER) TO service_role;
