-- SEO Wave 2: Indexes for /contratos/{setor}/{uf} and /fornecedores/{setor}/{uf} queries
-- These indexes optimize queries on pncp_supplier_contracts filtering by UF and aggregating by org/supplier.

CREATE INDEX IF NOT EXISTS idx_psc_orgao_cnpj ON pncp_supplier_contracts (orgao_cnpj);
CREATE INDEX IF NOT EXISTS idx_psc_uf ON pncp_supplier_contracts (uf);
CREATE INDEX IF NOT EXISTS idx_psc_uf_data ON pncp_supplier_contracts (uf, data_assinatura DESC);
CREATE INDEX IF NOT EXISTS idx_psc_uf_fornecedor ON pncp_supplier_contracts (uf, ni_fornecedor);
