# MON-SCH-03: data_fim, Vigência e Status Detalhado

**Priority:** P0
**Effort:** S (1-2 dias)
**Squad:** @data-engineer
**Status:** Draft
**Epic:** [EPIC-MON-SCHEMA-2026-04](EPIC-MON-SCHEMA-2026-04.md)
**Sprint:** Wave 1

---

## Contexto

`pncp_supplier_contracts` hoje só tem `data_assinatura`. Sem `data_fim`, não é possível responder perguntas como:
- "Quais contratos estão ativos hoje?" (filtro temporal em relatórios e páginas)
- "Qual a vigência média de contratos de limpeza em SP?" (insight para relatórios de preço)
- "Este fornecedor tem contratos próximos do fim?" (sinal para radar comercial)

PNCP expõe `dataInicioVigencia`, `dataFimVigencia`, `situacaoContratacao` nos detalhes do contrato.

---

## Acceptance Criteria

### AC1: Schema enriquecimento

- [ ] Migração adiciona:
  - `data_inicio_vigencia date NULL`
  - `data_fim_vigencia date NULL`
  - `vigencia_meses int GENERATED ALWAYS AS (
      CASE WHEN data_fim_vigencia IS NOT NULL AND data_inicio_vigencia IS NOT NULL
      THEN (EXTRACT(EPOCH FROM (data_fim_vigencia - data_inicio_vigencia)) / 2592000)::int
      ELSE NULL END
    ) STORED`
  - `status_detalhado varchar(20) NULL CHECK (status_detalhado IN ('ativo','encerrado','rescindido','suspenso','anulado','desconhecido'))`
- [ ] Migração paired down
- [ ] Índice parcial `WHERE status_detalhado='ativo' AND data_fim_vigencia > NOW()` (para queries de contratos ativos)

### AC2: Parsing no transformer

- [ ] `backend/ingestion/transformer.py` estende parse para extrair os 3 campos
- [ ] Map de status: PNCP `situacaoContratacao.codigo` → enum interno (documentar em comments do transformer)
- [ ] Fallback quando ausente: `status_detalhado='desconhecido'`, vigência NULL
- [ ] Backfill via RPC `backfill_vigencia_batch(limit int)` em batches 500, checkpointing em `ingestion_runs`

### AC3: RPC auxiliar

- [ ] Função `is_contract_active(p_numero_controle_pncp varchar) RETURNS boolean` — true se `status_detalhado='ativo' AND data_fim_vigencia > NOW()`
- [ ] View `contratos_ativos_hoje` (simples, não materializada) para uso em relatórios

### AC4: Testes

- [ ] `backend/tests/ingestion/test_transformer_vigencia.py`:
  - parse todas as 6 situações PNCP + fallback desconhecido
  - vigencia_meses calculada corretamente (ex: 12 meses para contrato de 1 ano)
  - contratos sem data_fim → vigencia_meses NULL
- [ ] `backend/tests/test_is_contract_active.py` cobre 4 casos (ativo válido, encerrado, rescindido, sem data_fim)

---

## Scope

**IN:**
- Migração schema (generated column + índice parcial)
- Transformer parsing
- RPC `is_contract_active` + view `contratos_ativos_hoje`
- Backfill job (mais leve que MON-SCH-02 — reusa crawl diário)
- Testes

**OUT:**
- UI de filtro "contratos ativos" (ficará em MON-SEO-01/03, MON-REP-*)
- Alertas de "contrato vencendo" (fora do escopo deste lote — candidato a Q3)

---

## Dependências

- Nenhuma (pode rodar em paralelo com MON-SCH-01 e MON-SCH-02)

---

## Riscos

- **Coverage PNCP inconsistente para contratos antigos:** status_detalhado='desconhecido' para fallback (não afeta queries)
- **Generated column impacto em backfill:** `GENERATED ALWAYS AS ... STORED` calcula em insert/update; migração usa `ALTER TABLE ... ADD COLUMN ... GENERATED` que pode travar em 2.1M rows → rodar em modo `NOT VALID` + VACUUM/ANALYZE ou usar trigger

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../add_vigencia_status_to_supplier_contracts.sql` + `.down.sql`
- `supabase/migrations/.../create_is_contract_active_rpc.sql` + `.down.sql`
- `backend/ingestion/transformer.py` (estender)
- `backend/tests/ingestion/test_transformer_vigencia.py` (novo)

---

## Definition of Done

- [ ] Migração aplicada em produção
- [ ] Backfill >= 70% coverage para contratos últimos 3 anos
- [ ] RPC `is_contract_active` p95 < 50ms
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — desbloqueia filtros temporais em relatórios e páginas SEO |
