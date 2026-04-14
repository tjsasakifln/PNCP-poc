-- SEO-hotfix: Índice GIN trigram em objeto_contrato para acelerar ILIKE '%kw%'.
--
-- Contexto: pncp_supplier_contracts tem 2.1M+ rows. O RPC count_contracts_by_setor_uf
-- faz EXISTS (ILIKE '%kw%') que requer scan de texto. Sem índice trigram, cada RPC
-- leva 0.5-2s em 78K rows por UF — com 405 RPCs, sitemap leva >120s.
--
-- A extensão pg_trgm já está habilitada no Supabase (padrão em todos os projetos).
-- O índice GIN permite ILIKE '%kw%' via GIN rewrite automático do Postgres.
--
-- Estimativa de tamanho: 2.1M rows × avg 120 chars = ~252MB texto.
-- GIN trigram ~30-50% do texto = ~75-125MB de índice extra.
-- CONCURRENTLY: não bloqueia reads/writes durante criação (Railway-safe).

-- Habilitar extensão (já deve estar ativa no Supabase, idempotente)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Desabilita statement_timeout para esta sessão: criação de índice GIN em 2.1M
-- rows leva ~2-5 min. O timeout padrão do Supabase CLI (~8s) cancela a operação.
SET statement_timeout = 0;

-- Índice GIN trigram para ILIKE em objeto_contrato
-- Nota: sem CONCURRENTLY (incompatível com transações do Supabase CLI).
-- Criação pode levar 2-5min em 2.1M rows, bloqueia writes no período.
-- Escritas são apenas pelo ARQ worker (não hot path de usuários).
CREATE INDEX IF NOT EXISTS idx_psc_objeto_trgm
    ON pncp_supplier_contracts
    USING GIN (objeto_contrato gin_trgm_ops)
    WHERE is_active = TRUE;

-- Comentário para referência futura
COMMENT ON INDEX idx_psc_objeto_trgm IS
    'GIN trigram index para acelerar ILIKE no RPC count_contracts_by_setor_uf. '
    'Reduz latência de ~1-2s para ~10-50ms por RPC, permitindo 405 RPCs em <60s.';
