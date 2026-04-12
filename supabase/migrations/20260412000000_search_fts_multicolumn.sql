-- ============================================================
-- Migration: 20260412000000_search_fts_multicolumn
-- Story:     STORY-437 AC1 + AC2
-- Purpose:   1) FTS multi-column (A/B/C weights): objeto_compra + orgao_razao_social + unidade_nome
--            2) search_datalake uses stored b.tsv (no inline to_tsvector recompute)
--            3) New p_websearch_text param for natural language queries
-- ============================================================

-- ============================================================
-- SECTION 1: Update tsv trigger for multi-column weights
-- Peso A: objeto_compra (highest relevance)
-- Peso B: orgao_razao_social (context — "Secretaria de Obras")
-- Peso C: unidade_nome (context — unit name)
-- Trigger now fires on changes to all three source columns.
-- ============================================================

CREATE OR REPLACE FUNCTION public.pncp_raw_bids_tsv_trigger()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.tsv :=
        setweight(to_tsvector('portuguese', coalesce(NEW.objeto_compra,      '')), 'A') ||
        setweight(to_tsvector('portuguese', coalesce(NEW.orgao_razao_social,  '')), 'B') ||
        setweight(to_tsvector('portuguese', coalesce(NEW.unidade_nome,        '')), 'C');
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.pncp_raw_bids_tsv_trigger() IS
    'Maintains pncp_raw_bids.tsv with weighted multi-column FTS (STORY-437 AC1). '
    'Peso A: objeto_compra, B: orgao_razao_social, C: unidade_nome.';

-- Replace trigger to fire on all three source columns.
DROP TRIGGER IF EXISTS trg_pncp_raw_bids_tsv ON public.pncp_raw_bids;

CREATE TRIGGER trg_pncp_raw_bids_tsv
    BEFORE INSERT OR UPDATE OF objeto_compra, orgao_razao_social, unidade_nome
    ON public.pncp_raw_bids
    FOR EACH ROW
    EXECUTE FUNCTION public.pncp_raw_bids_tsv_trigger();

-- Backfill all existing rows with the new multi-column composition.
-- Runs as a single UPDATE; Supabase supports concurrent reads during this.
UPDATE public.pncp_raw_bids
SET tsv =
    setweight(to_tsvector('portuguese', coalesce(objeto_compra,     '')), 'A') ||
    setweight(to_tsvector('portuguese', coalesce(orgao_razao_social, '')), 'B') ||
    setweight(to_tsvector('portuguese', coalesce(unidade_nome,       '')), 'C')
WHERE is_active = true;

-- ============================================================
-- SECTION 2: Updated search_datalake with:
--   - b.tsv stored column (no inline to_tsvector recompute)
--   - p_websearch_text for natural language queries
--   - Combined scoring: tsquery (sector keywords) AND websearch_to_tsquery (custom terms)
-- Must DROP first because adding p_websearch_text changes the function signature.
-- ============================================================

DROP FUNCTION IF EXISTS public.search_datalake(TEXT[], DATE, DATE, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER);

CREATE OR REPLACE FUNCTION public.search_datalake(
    p_ufs            TEXT[]    DEFAULT NULL,
    p_date_start     DATE      DEFAULT NULL,
    p_date_end       DATE      DEFAULT NULL,
    p_tsquery        TEXT      DEFAULT NULL,
    p_websearch_text TEXT      DEFAULT NULL,
    p_modalidades    INTEGER[] DEFAULT NULL,
    p_valor_min      NUMERIC   DEFAULT NULL,
    p_valor_max      NUMERIC   DEFAULT NULL,
    p_esferas        TEXT[]    DEFAULT NULL,
    p_modo           TEXT      DEFAULT 'publicacao',
    p_limit          INTEGER   DEFAULT 2000
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
            -- fallback: treat as plain text
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
        -- ts_rank on stored tsv column (multi-column weights A/B/C)
        CASE WHEN v_combined_q IS NOT NULL
             THEN ts_rank(b.tsv, v_combined_q)
             ELSE 0.0
        END::REAL AS ts_rank
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

        -- Full-text match using stored tsv (GIN indexed — no inline recompute)
        AND (
            v_combined_q IS NULL
            OR b.tsv @@ v_combined_q
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
        CASE WHEN v_combined_q IS NOT NULL
             THEN ts_rank(b.tsv, v_combined_q)
             ELSE NULL
        END DESC NULLS LAST,
        b.data_publicacao DESC

    LIMIT v_limit;
END;
$$;

COMMENT ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER) IS
    'Multi-column FTS datalake search (STORY-437). Uses stored b.tsv (A/B/C weights). '
    'p_tsquery: sector keywords OR-joined (raw tsquery syntax from Python). '
    'p_websearch_text: user free-text (websearch_to_tsquery — supports "phrase", -exclusion). '
    'Both params combined with AND when present. '
    'SECURITY DEFINER; tsquery errors fall back to plainto_tsquery.';

GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION public.search_datalake(TEXT[], DATE, DATE, TEXT, TEXT, INTEGER[], NUMERIC, NUMERIC, TEXT[], TEXT, INTEGER) TO service_role;
