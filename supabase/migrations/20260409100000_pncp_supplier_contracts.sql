-- Migration: pncp_supplier_contracts
-- Purpose: Index ALL PNCP contracts by ni_fornecedor (supplier CNPJ) for O(1)
--          supplier lookup on /cnpj/{cnpj} pages. Mirrors pncp_raw_bids pattern
--          but for the contracts side — populated by ingestion/contracts_crawler.py.
--
-- Volume estimate: ~5,800 contracts/day × 730 days = ~4.2M rows, ~800MB
-- Requires Supabase Pro tier (8GB storage).

CREATE TABLE IF NOT EXISTS pncp_supplier_contracts (
    id                   BIGSERIAL PRIMARY KEY,
    numero_controle_pncp TEXT        NOT NULL,
    ni_fornecedor        TEXT        NOT NULL,   -- 14-digit supplier CNPJ (digits only)
    nome_fornecedor      TEXT,
    orgao_cnpj           TEXT,                   -- buyer organ CNPJ (digits only)
    orgao_nome           TEXT,
    uf                   TEXT,
    municipio            TEXT,
    esfera               TEXT,                   -- F=Federal E=Estadual M=Municipal D=Distrital
    valor_global         NUMERIC(18, 2),
    data_assinatura      DATE,
    objeto_contrato      TEXT,
    content_hash         TEXT        NOT NULL UNIQUE,  -- SHA-256 of numero_controle_pncp (dedup key)
    is_active            BOOLEAN     NOT NULL DEFAULT TRUE,
    ingested_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Primary access pattern: supplier CNPJ lookup
CREATE INDEX IF NOT EXISTS idx_psc_ni_fornecedor
    ON pncp_supplier_contracts (ni_fornecedor);

-- Recent contracts first (pagination + ordering)
CREATE INDEX IF NOT EXISTS idx_psc_data_assinatura
    ON pncp_supplier_contracts (data_assinatura DESC);

-- Composite: fornecedor + date — covers the main query in _fetch_contratos_local
CREATE INDEX IF NOT EXISTS idx_psc_fornecedor_data
    ON pncp_supplier_contracts (ni_fornecedor, data_assinatura DESC);

-- Active-only filter (soft-delete pattern, consistent with pncp_raw_bids)
CREATE INDEX IF NOT EXISTS idx_psc_active
    ON pncp_supplier_contracts (is_active) WHERE is_active = TRUE;

-- RLS: public read (contracts are public data from PNCP)
ALTER TABLE pncp_supplier_contracts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "psc_public_read" ON pncp_supplier_contracts;
CREATE POLICY "psc_public_read" ON pncp_supplier_contracts
    FOR SELECT USING (TRUE);

-- Service role gets full access (needed by ingestion worker)
DROP POLICY IF EXISTS "psc_service_write" ON pncp_supplier_contracts;
CREATE POLICY "psc_service_write" ON pncp_supplier_contracts
    FOR ALL USING (auth.role() = 'service_role');

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_psc_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_psc_updated_at ON pncp_supplier_contracts;
CREATE TRIGGER trg_psc_updated_at
    BEFORE UPDATE ON pncp_supplier_contracts
    FOR EACH ROW EXECUTE FUNCTION update_psc_updated_at();

-- RPC for bulk upsert (mirrors upsert_pncp_raw_bids pattern, batch limit 500 rows)
CREATE OR REPLACE FUNCTION upsert_pncp_supplier_contracts(p_records jsonb)
RETURNS TABLE(inserted int, updated int, unchanged int)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_inserted  int := 0;
    v_updated   int := 0;
    v_unchanged int := 0;
    rec         jsonb;
    v_existing  int;
BEGIN
    FOR rec IN SELECT * FROM jsonb_array_elements(p_records)
    LOOP
        SELECT COUNT(1) INTO v_existing
        FROM pncp_supplier_contracts
        WHERE content_hash = rec->>'content_hash';

        INSERT INTO pncp_supplier_contracts (
            numero_controle_pncp, ni_fornecedor, nome_fornecedor,
            orgao_cnpj, orgao_nome, uf, municipio, esfera,
            valor_global, data_assinatura, objeto_contrato,
            content_hash, is_active
        ) VALUES (
            rec->>'numero_controle_pncp', rec->>'ni_fornecedor', rec->>'nome_fornecedor',
            rec->>'orgao_cnpj', rec->>'orgao_nome', rec->>'uf', rec->>'municipio', rec->>'esfera',
            NULLIF(rec->>'valor_global', '')::NUMERIC,
            NULLIF(rec->>'data_assinatura', '')::DATE,
            rec->>'objeto_contrato', rec->>'content_hash', TRUE
        )
        ON CONFLICT (content_hash) DO UPDATE SET
            nome_fornecedor = EXCLUDED.nome_fornecedor,
            orgao_nome      = EXCLUDED.orgao_nome,
            valor_global    = EXCLUDED.valor_global,
            objeto_contrato = EXCLUDED.objeto_contrato,
            is_active       = TRUE,
            updated_at      = NOW()
        WHERE
            pncp_supplier_contracts.nome_fornecedor IS DISTINCT FROM EXCLUDED.nome_fornecedor
            OR pncp_supplier_contracts.valor_global IS DISTINCT FROM EXCLUDED.valor_global
            OR pncp_supplier_contracts.objeto_contrato IS DISTINCT FROM EXCLUDED.objeto_contrato;

        IF NOT FOUND THEN
            v_unchanged := v_unchanged + 1;
        ELSIF v_existing = 0 THEN
            v_inserted := v_inserted + 1;
        ELSE
            v_updated := v_updated + 1;
        END IF;
    END LOOP;

    RETURN QUERY SELECT v_inserted, v_updated, v_unchanged;
END;
$$;
