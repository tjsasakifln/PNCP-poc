# EPIC-MON-SCHEMA-2026-04: Enriquecimento do Dataset de 2M+ Contratos (Prerequisito)

**Priority:** P0 — Prerequisito para todas as outras camadas de monetização
**Status:** Draft
**Owner:** @data-engineer (Dara) + @dev + @architect
**Sprint:** Wave 1 (paralelo às stories MON-API + MON-REP)
**Meta:** Enriquecer `pncp_supplier_contracts` com aditivos + CATMAT/CATSER + data_fim/status para desbloquear scoring, benchmarks e monitores.

---

## Contexto Estratégico

O SmartLic possui ~2.1M contratos históricos em `pncp_supplier_contracts` (migração `20260409100000_pncp_supplier_contracts.sql`) com colunas limitadas: `ni_fornecedor`, `nome_fornecedor`, `orgao_cnpj`, `orgao_nome`, `uf`, `municipio`, `esfera`, `valor_global`, `data_assinatura`, `objeto_contrato`, `numero_controle_pncp`.

Faltam dados críticos para os produtos monetizáveis:

- **Aditivos contratuais** — desbloqueia score de risco (Due Diligence, Radar) e alertas (Monitor Órgão)
- **CATMAT/CATSER** — códigos padronizados de classificação de material/serviço; desbloqueia benchmark estatístico de preço com precisão (versus busca textual sobre `objeto_contrato`)
- **data_fim + status detalhado** — permite filtros de vigência ("contratos ativos hoje") usados em relatórios e páginas SEO

Sem esses enriquecimentos, produtos pagos das camadas 2-4 ficam degradados (Due Diligence sem sinais de risco; Benchmark API sem precisão; relatórios sem filtro temporal correto).

---

## Stories do Epic

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| MON-SCH-01 | P0 | M | @data-engineer + @dev | Draft | Crawler + schema de aditivos contratuais |
| MON-SCH-02 | P0 | M | @data-engineer + @dev | Draft | CATMAT/CATSER parsing + indexação + catálogo |
| MON-SCH-03 | P0 | S | @data-engineer | Draft | data_fim + vigência + status detalhado |

---

## Ordem de Execução

MON-SCH-01, MON-SCH-02 e MON-SCH-03 são **independentes entre si** — podem executar em paralelo. Recomendado: MON-SCH-02 e MON-SCH-03 começam primeiro (fontes de dado já no PNCP, apenas parsing); MON-SCH-01 (crawler novo + backfill) em paralelo com owner separado.

---

## KPIs do Epic

| KPI | Baseline | Meta 30 dias | Meta 90 dias |
|-----|----------|-------------|--------------|
| Coverage CATMAT/CATSER | 0% | 50% dos 2.1M | 80% |
| Coverage aditivos (últimos 2 anos) | 0% | 30% | 70% |
| Coverage data_fim | 0% | 90% (onde PNCP expõe) | 95% |
| Queries benchmark p95 | N/A | <500ms | <300ms |

---

## Dependências Downstream (o que este epic desbloqueia)

- `MON-REP-04` (Relatório Preço Referência) — depende MON-SCH-02
- `MON-REP-06` (Due Diligence) — depende MON-SCH-01 + MON-SCH-02
- `MON-API-04` (Benchmark endpoint) — depende MON-SCH-02
- `MON-SUB-03` (Monitor Órgão alerts aditivos) — depende MON-SCH-01
- `MON-SUB-04` (Radar Risco) — depende MON-SCH-01
- `MON-SEO-01` (Score na página pública) — depende MON-SCH-01
- `MON-SEO-02` (Páginas /categoria) — depende MON-SCH-02
- `MON-AI-03` (Radar Preditivo) — depende MON-SCH-01 + MON-SCH-02

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Epic criado — prerequisito do lote de stories de monetização do dataset de 2M+ contratos |
