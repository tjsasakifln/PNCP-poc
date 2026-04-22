# MON-SCH-02: CATMAT/CATSER Parsing e Indexação

**Priority:** P0
**Effort:** M (3-4 dias — inclui re-ingestão dos 2.1M registros)
**Squad:** @data-engineer + @dev
**Status:** Draft
**Epic:** [EPIC-MON-SCHEMA-2026-04](EPIC-MON-SCHEMA-2026-04.md)
**Sprint:** Wave 1

---

## Contexto

CATMAT (Catálogo de Materiais) e CATSER (Catálogo de Serviços) são códigos padronizados do governo federal para classificar objeto de contratação (ex: CATMAT 150015 = "Papel sulfite A4 75g"). Hoje `pncp_supplier_contracts` não armazena esses códigos — apenas `objeto_contrato` (texto livre). Isso limita:

- **Benchmark estatístico de preço** (MON-REP-04 + MON-API-04): sem código padronizado, "média por categoria" vira busca textual imprecisa
- **Páginas `/categoria/[slug]`** (MON-SEO-02): slugs precisam de IDs padronizados para ser estáveis
- **Radar Preditivo** (MON-AI-03): detecção de sazonalidade requer categoria estável

PNCP expõe CATMAT/CATSER no endpoint de itens do contrato (`/contratos/{id}/itens`). Também existe catálogo público de códigos (para tabela de referência com labels).

---

## Acceptance Criteria

### AC1: Schema enriquecimento em `pncp_supplier_contracts`

- [ ] Migração adiciona:
  - `catmat_catser varchar(10) NULL` (código principal — primeiro item do contrato ou moda dos itens)
  - `catmat_catser_tipo char(1) NULL CHECK (catmat_catser_tipo IN ('M', 'S'))` (Material ou Serviço)
  - `catmat_catser_secondary varchar(10)[] NULL` (códigos adicionais de itens secundários)
- [ ] Migração paired down
- [ ] Índice B-tree em `catmat_catser` (covering: `(catmat_catser, uf, data_assinatura)` para benchmark queries)
- [ ] Índice GIN em `catmat_catser_secondary`

### AC2: Tabela catálogo de referência

- [ ] Migração cria `catmat_catser_catalog`:
  - `codigo varchar(10) PRIMARY KEY`
  - `tipo char(1) NOT NULL CHECK (tipo IN ('M','S'))`
  - `label text NOT NULL`
  - `categoria text NULL` (grupo pai no catálogo PNCP)
  - `slug text UNIQUE NOT NULL` (kebab-case para URLs: `papel-sulfite-a4-75g`)
  - `row_count int NOT NULL DEFAULT 0` (contador denormalizado, atualizado via trigger ou cron)
- [ ] Seed inicial via script `scripts/seed_catmat_catser_catalog.py` (fonte: ComprasGov v3 catálogo público)
- [ ] RLS: leitura pública (`FOR SELECT USING (TRUE)`), escrita service-role

### AC3: Parsing no transformer + re-ingestão

- [ ] `backend/ingestion/transformer.py` estende parse para extrair CATMAT/CATSER do payload de contrato (campo `itens[].codigoCatmatCatser` ou similar)
- [ ] Fallback LLM quando ausente: GPT-4.1-nano classifica `objeto_contrato` no catálogo (prompt em `backend/llm/prompts/catmat_classifier.py`) — marcado com flag `catmat_source='llm'`
- [ ] ARQ job `backfill_catmat_catser` processa em batches de 500 rows/batch; ~42 horas estimadas full backfill com 10k batches
- [ ] Tracking em `ingestion_runs` com checkpoint por `data_assinatura` (resumable)
- [ ] Prometheus: `smartlic_catmat_coverage_pct{source}` com labels `source=pncp_direct|llm|none`

### AC4: RPC de benchmark por CATMAT

- [ ] Migração cria função SQL:
```sql
CREATE OR REPLACE FUNCTION public.benchmark_by_catmat(
  p_catmat varchar, p_uf varchar DEFAULT NULL, p_periodo_dias int DEFAULT 365
) RETURNS TABLE (
  n_contratos int, valor_medio numeric, valor_mediano numeric,
  p10 numeric, p25 numeric, p75 numeric, p90 numeric,
  stddev numeric, periodo_inicio date, periodo_fim date
) LANGUAGE sql STABLE SECURITY DEFINER ...;
```
- [ ] Performance: p95 < 300ms com 80% coverage (via índice composto `(catmat_catser, uf, data_assinatura)`)
- [ ] Teste de regressão: snapshot de benchmark para CATMAT 150015 (papel sulfite) vs valor oficial

### AC5: Testes

- [ ] Unit: `backend/tests/ingestion/test_transformer_catmat.py`
  - parse CATMAT direto do PNCP (3 formatos diferentes)
  - fallback LLM quando ausente (mock GPT-4.1-nano)
  - código inválido → `catmat_catser=NULL` + log
- [ ] Integration: `backend/tests/test_benchmark_rpc.py`
  - Seed 100 contratos CATMAT X em UF SP
  - `benchmark_by_catmat('X', 'SP')` retorna estatísticas corretas
- [ ] Snapshot test de performance (Benchmark < 300ms)

---

## Scope

**IN:**
- Migrações (schema + catálogo + RPC)
- Transformer parsing + LLM fallback
- Backfill job
- Seed do catálogo via ComprasGov v3
- Prometheus metrics
- Testes

**OUT:**
- UI de navegação do catálogo (fica em MON-SEO-02)
- Benchmark API endpoint (fica em MON-API-04, usa este RPC)
- Relatório PDF de preço referência (fica em MON-REP-04)

---

## Dependências

- Catálogo CATMAT/CATSER acessível via ComprasGov v3 (já usado em `compras_gov_client.py`)
- OpenAI API configurado (já existe) — custo estimado LLM fallback: ~R$ 150 para classificar 500k rows restantes (0,0003/row × 500k)
- ARQ worker deploy (já em produção)

---

## Riscos

- **Coverage direto do PNCP incompleto:** pilot sample mostra ~40% dos contratos têm CATMAT no payload; LLM fallback obrigatório para atingir 80%
- **LLM fallback custo:** estimativa R$150 razoável; se custo real >R$500, reduzir scope (só contratos últimos 3 anos)
- **Backfill longo (42h):** rodar em background sem impacto em produção; trigger manual via CLI admin

---

## Dev Notes

_(a preencher pelo @dev durante implementação)_

---

## Arquivos Impactados

- `supabase/migrations/.../add_catmat_catser_columns.sql` + `.down.sql`
- `supabase/migrations/.../create_catmat_catser_catalog.sql` + `.down.sql`
- `supabase/migrations/.../create_benchmark_by_catmat_rpc.sql` + `.down.sql`
- `backend/ingestion/transformer.py` (estender)
- `backend/llm/prompts/catmat_classifier.py` (novo)
- `scripts/seed_catmat_catser_catalog.py` (novo)
- `backend/jobs/cron/backfill_catmat.py` (novo)
- `backend/tests/ingestion/test_transformer_catmat.py` (novo)
- `backend/tests/test_benchmark_rpc.py` (novo)

---

## Definition of Done

- [ ] Migrações aplicadas + catálogo seeded (~50k entries)
- [ ] Backfill Tier 1 (últimos 2 anos, top valor) completo: coverage CATMAT >= 70%
- [ ] RPC `benchmark_by_catmat` rodando p95 < 300ms
- [ ] Prometheus mostra `smartlic_catmat_coverage_pct` atualizado
- [ ] Testes passando (unit + integration + snapshot)
- [ ] Desbloqueia MON-REP-04 + MON-API-04 + MON-SEO-02

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — prereq para Benchmark API, páginas /categoria, Radar Preditivo |
