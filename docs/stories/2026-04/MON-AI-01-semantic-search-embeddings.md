# MON-AI-01: Semantic Search / Embeddings API (pgvector + HNSW)

**Priority:** P0 (pré-requisito para MON-AI-02)
**Effort:** L (6-8 dias)
**Squad:** @data-engineer + @dev + @architect
**Status:** Draft
**Epic:** [EPIC-MON-AI-2026-04](EPIC-MON-AI-2026-04.md)
**Sprint:** Wave 2

---

## Contexto

Para monetizar o dataset de 2.1M contratos como **moat de IA**, precisamos vetorização semântica. Isso habilita:
- Endpoint público "contratos similares a X" (R$ 0,10-1/query, distribuível via RapidAPI)
- Base para AI Copilot de Propostas (MON-AI-02) — RAG sobre vencedores similares
- Potencial futuro: Radar Preditivo (MON-AI-03) pode usar similaridade semântica como feature

**Tech stack:**
- Extensão Supabase `pgvector` (já disponível)
- Modelo: `text-embedding-3-small` da OpenAI (1536 dim, USD 0.02/1M tokens)
- Index: HNSW para busca aproximada sub-linear
- Cost: ~USD 200 para 2.1M rows (avg 250 tokens/objeto_contrato). Priorizar top 500k por valor primeiro

---

## Acceptance Criteria

### AC1: Schema + extensão pgvector

- [ ] Migração instala extensão:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE public.pncp_supplier_contracts
  ADD COLUMN embedding vector(1536) NULL,
  ADD COLUMN embedding_model varchar(50) NULL,
  ADD COLUMN embedding_updated_at timestamptz NULL;

CREATE INDEX idx_supplier_contracts_embedding_hnsw
  ON public.pncp_supplier_contracts
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```
- [ ] Migração paired down (drop column + extension se não usada em outro lugar)

### AC2: Batch embedding job

- [ ] `backend/ingestion/embed_contracts.py`:
  - Processa contratos sem embedding, priorizando por `valor_global DESC`
  - Chunks de 100 rows por call à OpenAI Embeddings API
  - Rate limit: 3k req/min (OpenAI limit) — respeitar com semaphore
  - Retry exponencial em 429/503
  - Update `embedding, embedding_model='text-embedding-3-small', embedding_updated_at=now()`
- [ ] ARQ cron diário `embed_contracts_batch` processa até 10k rows/dia (~R$ 2-3/dia custo OpenAI)
- [ ] Script `scripts/backfill_embeddings.py` para priorizar top 500k por valor (manual trigger)

### AC3: RPC `match_contracts`

- [ ] Função SQL:
```sql
CREATE OR REPLACE FUNCTION public.match_contracts(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 20,
  filter_uf text DEFAULT NULL,
  filter_setor text DEFAULT NULL
) RETURNS TABLE (
  numero_controle_pncp text, ni_fornecedor text, nome_fornecedor text,
  orgao_nome text, uf text, valor_global numeric, data_assinatura date,
  objeto_contrato text, similarity float
)
LANGUAGE sql STABLE PARALLEL SAFE AS $$
  SELECT ..., 1 - (embedding <=> query_embedding) as similarity
  FROM pncp_supplier_contracts
  WHERE embedding IS NOT NULL
    AND 1 - (embedding <=> query_embedding) > match_threshold
    AND (filter_uf IS NULL OR uf = filter_uf)
    AND (filter_setor IS NULL OR setor_classificado = filter_setor)
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
```
- [ ] Performance target: p95 < 300ms com 2M embeddings + HNSW

### AC4: Endpoint API público `GET /api/v1/contracts/similar`

- [ ] Query param: `text` (texto a buscar similaridade) OU `contract_id` (usa embedding daquele)
- [ ] Params opcionais: `limit` (1-50, default 20), `uf`, `setor`, `threshold` (0.0-1.0, default 0.7)
- [ ] Response: array de contratos similares com score de similarity
- [ ] Autenticação: X-API-Key (MON-API-01)
- [ ] Cost: 50 cents (R$ 0,50) por query via MON-API-02
- [ ] Rate limit: 60 req/min por key

### AC5: Observability

- [ ] Prometheus: `smartlic_embeddings_coverage_pct`, `smartlic_semantic_search_queries_total{hit}`, `smartlic_embeddings_generation_cost_cents_total`
- [ ] Sentry: alert se `embeddings_coverage_pct < 10%` (falha no backfill)

### AC6: Testes

- [ ] Unit: mock OpenAI response, valida insertion correto
- [ ] Integration: seed 1k contratos com embeddings + query semantic → ordenação por similaridade correta
- [ ] Performance: 100 concurrent queries p95 < 300ms

---

## Scope

**IN:**
- Migração + extension
- Batch embedding job + cron
- RPC match_contracts
- Endpoint público
- Testes

**OUT:**
- Embedding de outros campos (razão social, setor label) — v2
- Multi-vector per contract (hybrid search) — v2
- Fine-tuning de modelo próprio — fora de escopo

---

## Dependências

- Supabase com pgvector habilitado (verificar: alguns projetos Supabase têm por default)
- OpenAI API key (existente)
- MON-API-01 + MON-API-02 (para endpoint monetizado)

---

## Riscos

- **pgvector não habilitado em produção:** validar `CREATE EXTENSION vector;` em staging primeiro
- **Custo OpenAI runaway:** backfill priorizado + cron diário com budget cap USD 10/dia
- **HNSW index tempo de construção:** ~2h para 2M rows; aceitar downtime programado ou criar CONCURRENTLY
- **Dimensão 1536 → row size grande:** ~6KB por row; 2M × 6KB = 12GB tabela. Verificar storage Supabase

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../add_pgvector_embeddings.sql` + `.down.sql`
- `backend/ingestion/embed_contracts.py` (novo)
- `backend/jobs/cron/embed_batch.py` (novo)
- `scripts/backfill_embeddings.py` (novo)
- `supabase/migrations/.../create_match_contracts_rpc.sql` + `.down.sql`
- `backend/routes/public_api/similar_contracts.py` (novo)
- `backend/tests/ingestion/test_embed_contracts.py` (novo)
- `backend/tests/routes/public_api/test_similar_contracts.py` (novo)

---

## Definition of Done

- [ ] Extensão pgvector ativada em prod
- [ ] Top 100k contratos por valor com embedding
- [ ] Cron diário processando incrementalmente
- [ ] Endpoint público live com p95 < 300ms
- [ ] Testes passando
- [ ] Desbloqueia MON-AI-02

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — foundation de moat IA; pré-requisito AI Copilot |
