-- ============================================================
-- Migration: 20260409200000_optimize_contracts_upsert
-- Purpose:   Replace row-by-row upsert with batch INSERT ON CONFLICT
--            Same pattern as upsert_pncp_raw_bids (DEBT-210, proven in prod).
--            ~1000 SQL ops/batch → 1 statement/batch.
-- ============================================================

CREATE OR REPLACE FUNCTION public.upsert_pncp_supplier_contracts(p_records JSONB)
RETURNS TABLE(inserted INT, updated INT, unchanged INT)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_total     INT;
    v_inserted  INT;
    v_updated   INT;
BEGIN
    IF p_records IS NULL OR jsonb_array_length(p_records) = 0 THEN
        RETURN QUERY SELECT 0, 0, 0;
        RETURN;
    END IF;

    v_total := jsonb_array_length(p_records);

    -- Single-statement batch upsert.
    -- DISTINCT ON (content_hash) deduplicates within the same batch.
    -- xmax = 0 means the row was freshly inserted (no prior version existed).
    -- WHERE IS DISTINCT FROM skips unchanged rows (no unnecessary writes).
    WITH deduped AS (
        SELECT DISTINCT ON (r.content_hash)
            r.*
        FROM jsonb_to_recordset(p_records) AS r(
            numero_controle_pncp TEXT,
            ni_fornecedor        TEXT,
            nome_fornecedor      TEXT,
            orgao_cnpj           TEXT,
            orgao_nome           TEXT,
            uf                   TEXT,
            municipio            TEXT,
            esfera               TEXT,
            valor_global         NUMERIC,
            data_assinatura      DATE,
            objeto_contrato      TEXT,
            content_hash         TEXT
        )
        ORDER BY r.content_hash
    ),
    upserted AS (
        INSERT INTO public.pncp_supplier_contracts (
            numero_controle_pncp, ni_fornecedor, nome_fornecedor,
            orgao_cnpj, orgao_nome, uf, municipio, esfera,
            valor_global, data_assinatura, objeto_contrato,
            content_hash, is_active, ingested_at, updated_at
        )
        SELECT
            r.numero_controle_pncp, r.ni_fornecedor, r.nome_fornecedor,
            r.orgao_cnpj, r.orgao_nome, r.uf, r.municipio, r.esfera,
            r.valor_global, r.data_assinatura, r.objeto_contrato,
            r.content_hash, TRUE, now(), now()
        FROM deduped r
        ON CONFLICT (content_hash) DO UPDATE SET
            nome_fornecedor = EXCLUDED.nome_fornecedor,
            orgao_nome      = EXCLUDED.orgao_nome,
            valor_global    = EXCLUDED.valor_global,
            objeto_contrato = EXCLUDED.objeto_contrato,
            is_active       = TRUE,
            updated_at      = now()
        WHERE
            pncp_supplier_contracts.nome_fornecedor IS DISTINCT FROM EXCLUDED.nome_fornecedor
            OR pncp_supplier_contracts.valor_global IS DISTINCT FROM EXCLUDED.valor_global
            OR pncp_supplier_contracts.objeto_contrato IS DISTINCT FROM EXCLUDED.objeto_contrato
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
