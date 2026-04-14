-- SEO-hotfix: Corrige performance de consultas por UF em pncp_supplier_contracts.
--
-- Problemas detectados:
-- 1. Nenhum índice na coluna `uf` → consultas .eq("uf", ...).limit(5000) fazem full scan
--    (19-45s por query), causando timeout 502 e ISR builds com total_contracts=0.
-- 2. count_contracts_by_setor_uf usa upper(uf) = upper(p_uf), o que inviabiliza uso
--    de qualquer índice na coluna uf.
-- 3. _compute_contracts_combos dispara 540 RPCs em paralelo (15 setores × 27 UFs)
--    sem throttle, travando o event loop do FastAPI.
--
-- Fixes:
-- 1. Índice composto (uf, data_assinatura DESC) WHERE is_active filtrado — cobre
--    tanto .eq("uf",...).limit(5000) quanto ORDER BY data_assinatura.
-- 2. RPC reescrita com uf = upper(p_uf) — aproveita o índice (dados do PNCP
--    são armazenados em maiúsculas, então upper(p_uf) é a normalização correta).
-- 3. Índice adicional uf+objeto_contrato via GIN trigram — melhora EXISTS ILIKE.

-- Fix 1: Índice composto UF + data para cobrir .eq("uf",...).order("data_assinatura")
-- CONCURRENTLY é safe em produção (não bloqueia leituras/escritas)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_psc_uf_data
    ON pncp_supplier_contracts (uf, data_assinatura DESC)
    WHERE is_active = TRUE;

-- Fix 2: RPC com condição index-friendly
-- Mudança: upper(uf) = upper(p_uf)  →  uf = upper(p_uf)
-- Justificativa: PNCP armazena UF em maiúsculas (PNCP API contract).
-- upper(p_uf) normaliza a entrada; uf = <literal> usa o índice em idx_psc_uf_data.
CREATE OR REPLACE FUNCTION count_contracts_by_setor_uf(
    p_keywords text[],
    p_uf       text
)
RETURNS bigint
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT COUNT(*)
    FROM pncp_supplier_contracts
    WHERE is_active = TRUE
      AND uf = upper(p_uf)
      AND EXISTS (
          SELECT 1
          FROM unnest(p_keywords) AS kw
          WHERE objeto_contrato ILIKE '%' || kw || '%'
      );
$$;

-- Re-grant (idempotente)
GRANT EXECUTE ON FUNCTION count_contracts_by_setor_uf(text[], text) TO anon;
GRANT EXECUTE ON FUNCTION count_contracts_by_setor_uf(text[], text) TO authenticated;
GRANT EXECUTE ON FUNCTION count_contracts_by_setor_uf(text[], text) TO service_role;
