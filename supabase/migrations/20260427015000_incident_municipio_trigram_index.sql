-- INCIDENT 2026-04-27 humble-dolphin root cause fix
--
-- _compute_contratos_stats(uf, municipio_pattern ilike) em backend/routes/blog_stats.py:909
-- executa ILIKE '%pattern%' em pncp_supplier_contracts.municipio.
--
-- Sem trigram, ilike com leading wildcard faz seq scan parcial (mesmo com idx_psc_uf
-- filtrando por UF: SP tem ~400K contratos ativos, 8s statement_timeout estoura).
--
-- Resultado pre-hotfix: query 502 -> retry storm -> uvicorn worker wedge.
-- Resultado pos-hotfix: query timeout silencioso, empty stats servida (acceptable).
-- Esta migration: query passa a executar em <500ms via index-bitmap-scan.
--
-- Espelha pattern de 20260413120000_contracts_trigram_index.sql (objeto_contrato GIN).
-- pg_trgm ja habilitado.
--
-- Tamanho estimado: 2.1M rows x avg 25 chars municipio = ~52MB texto.
-- GIN trigram ~30-50% = ~16-25MB.
-- Sem CONCURRENTLY (incompativel com transacao Supabase CLI).
-- Criacao: ~30s-2min em 2.1M rows. Bloqueio writes durante: writes vem de ARQ worker
-- (cron full 5 UTC, incremental 11/17/23 UTC) — janela segura entre cron runs.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

SET statement_timeout = 0;

CREATE INDEX IF NOT EXISTS idx_psc_municipio_trgm
    ON pncp_supplier_contracts
    USING GIN (municipio gin_trgm_ops)
    WHERE is_active = TRUE;

COMMENT ON INDEX idx_psc_municipio_trgm IS
    'INCIDENT 2026-04-27: GIN trigram em municipio para acelerar ILIKE em '
    '_compute_contratos_stats. Espelha idx_psc_objeto_trgm. Reduz latencia de '
    '8s+ (seq scan) para <500ms (bitmap scan).';
