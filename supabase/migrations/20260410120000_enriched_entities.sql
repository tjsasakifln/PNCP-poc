-- Sprint 2 Parte 13: tabela de cache de enriquecimento de entidades externas
-- Alimenta /fornecedores/{cnpj}, /municipios/{slug}, /compliance/{cnpj}
--
-- entity_type: 'fornecedor' | 'municipio' | 'orgao'
-- entity_id:   CNPJ 14 digitos (fornecedor/orgao) | codigo IBGE 7 digitos (municipio)
-- data:        payload JSONB completo da API externa (BrasilAPI, IBGE, Portal Transparencia)
-- enriched_at: timestamp do ultimo enriquecimento (usado para staleness check de 30 dias)

CREATE TABLE IF NOT EXISTS public.enriched_entities (
    entity_type  TEXT        NOT NULL,
    entity_id    TEXT        NOT NULL,
    data         JSONB       NOT NULL DEFAULT '{}',
    enriched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (entity_type, entity_id)
);

COMMENT ON TABLE public.enriched_entities IS
    'Cache de dados externos enriquecidos por entidade (fornecedor, municipio, orgao). '
    'Populado pelo job ARQ enrich_entities_job (diario 08:00 UTC). '
    'TTL logico: 30 dias (enriched_at < now() - interval 30 days).';

COMMENT ON COLUMN public.enriched_entities.entity_type IS
    'Tipo: ''fornecedor'' (CNPJ 14d) | ''municipio'' (IBGE 7d) | ''orgao'' (CNPJ 14d)';

COMMENT ON COLUMN public.enriched_entities.data IS
    'Payload JSONB: razao_social, cnae, simples_nacional, enderecos, '
    'total_contratos, valor_total_contratos, sancoes_ativas, situacao_tcu (fornecedor) '
    '| nome, uf, regiao, populacao, pib_per_capita, convenios_federais (municipio)';

-- Index por tipo + data de enriquecimento: queries de staleness (job ARQ)
CREATE INDEX IF NOT EXISTS idx_enriched_entities_type_enriched
    ON public.enriched_entities (entity_type, enriched_at DESC);

-- RLS: leitura publica, escrita apenas service_role
ALTER TABLE public.enriched_entities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "enriched_entities_read_all"
    ON public.enriched_entities
    FOR SELECT
    USING (true);

CREATE POLICY "enriched_entities_service_write"
    ON public.enriched_entities
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

GRANT SELECT ON public.enriched_entities TO authenticated;
GRANT SELECT ON public.enriched_entities TO anon;
GRANT ALL    ON public.enriched_entities TO service_role;
