-- SEO-471: RPC para contar contratos em pncp_supplier_contracts por setor×UF.
--
-- Usada por sitemap_licitacoes._compute_contracts_combos para identificar
-- combos setor×UF com contratos históricos, mesmo quando não há editais
-- ativos recentes. Permite que o sitemap descubra páginas com conteúdo
-- válido (ex: "Limpeza no AM" com 240 contratos e 0 editais abertos).
--
-- Parâmetros:
--   p_keywords: array de palavras-chave do setor (até 20, limitado pelo caller)
--   p_uf:       sigla da UF (2 letras, case-insensitive)
--
-- Retorna: bigint — número de contratos ativos que contêm ao menos uma keyword

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
      AND upper(uf) = upper(p_uf)
      AND EXISTS (
          SELECT 1
          FROM unnest(p_keywords) AS kw
          WHERE objeto_contrato ILIKE '%' || kw || '%'
      );
$$;

-- Permite chamada pública (via PostgREST anon key) — dados são públicos
GRANT EXECUTE ON FUNCTION count_contracts_by_setor_uf(text[], text) TO anon;
GRANT EXECUTE ON FUNCTION count_contracts_by_setor_uf(text[], text) TO authenticated;
GRANT EXECUTE ON FUNCTION count_contracts_by_setor_uf(text[], text) TO service_role;
