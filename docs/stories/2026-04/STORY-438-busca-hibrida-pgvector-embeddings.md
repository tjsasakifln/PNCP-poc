# STORY-438 — Busca Híbrida Semântica com pgvector + OpenAI Embeddings

**Status:** Done
**Type:** Feature (Backend-only)
**Priority:** Medium (pós STORY-437)
**Estimativa:** 3-4 dias
**Custo adicional:** ~$0.50 one-time backfill + marginal ongoing (~$1-3/mês)
**Pré-requisito:** STORY-437 Done + verificar storage Supabase (free tier: 500MB)

---

## Contexto

Após os quick wins da STORY-437, esta story adiciona **busca semântica** via pgvector. O problema que resolve: o sistema atual não entende variantes semânticas — "higienização" não bate com "limpeza", "pavimentação asfáltica" pode não bater com "obras viárias" se não estiver no dicionário de sinônimos.

A solução é **busca híbrida**: combina o `ts_rank` do FTS com `cosine similarity` dos embeddings, dando ao usuário os melhores dos dois mundos (precisão do FTS + recall semântico).

**Escolha técnica:**
- `text-embedding-3-small` com `dimensions=256` (ao invés de 1536): 40K rows × 256 × 4 bytes ≈ 41MB (seguro para free tier)
- HNSW index (sem vacuums, latência consistente < 10ms)
- Feature flag `EMBEDDING_ENABLED=false` por padrão até validação com dados reais
- Hybrid weight: `0.4 * ts_rank + 0.6 * cosine_similarity`

---

## Pré-condição obrigatória

Antes de aplicar em prod:
- [ ] Verificar storage atual do Supabase: `SELECT pg_size_pretty(pg_database_size(current_database()))`
- [ ] Storage disponível deve ser ≥ 100MB acima do atual (41MB coluna + 20MB HNSW index + margem)
- [ ] Se free tier cheio: upgrade para Supabase Pro ($25/mês) ou reduzir retention de `pncp_raw_bids`

---

## Acceptance Criteria

### AC1 — Infraestrutura pgvector
- [x] Migration habilita extensão `vector` (pgvector) no Supabase
- [x] Coluna `embedding VECTOR(256)` adicionada em `pncp_raw_bids` (nullable, default NULL)
- [x] HNSW index criado: `USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`
- [x] Migration idempotente: `CREATE EXTENSION IF NOT EXISTS vector`, `ADD COLUMN IF NOT EXISTS`

### AC2 — Geração de Embeddings na Ingestão
- [x] `backend/ingestion/loader.py`: `_generate_embeddings_batch()` usando `AsyncOpenAI.embeddings.create(model="text-embedding-3-small", dimensions=256)`
- [x] Embeddings gerados em batch (até 100 textos por chamada API) em `loader.py` antes do upsert
- [x] `EMBEDDING_ENABLED=false` (default) — quando False, campo `embedding` não é preenchido e upsert funciona normalmente
- [x] Quando `EMBEDDING_ENABLED=true`: embedding é incluído no payload de upsert para `upsert_pncp_raw_bids`
- [x] Falha de embedding (timeout, rate limit) é logada mas NÃO impede o upsert do bid (degradação graciosa)
- [x] `upsert_pncp_raw_bids` RPC aceita campo `embedding` opcional no payload JSONB (nullable, sem breaking change)

### AC3 — Busca Híbrida na RPC
- [x] `search_datalake` atualizado para aceitar parâmetro `p_embedding VECTOR(256) DEFAULT NULL`
- [x] Quando `p_embedding IS NOT NULL`: WHERE inclui bids onde `cosine_similarity > 0.6` OU FTS match (OR, não AND)
- [x] Score híbrido no ORDER BY: `0.4 * ts_rank(tsv, query) + 0.6 * (1 - (embedding <=> p_embedding))`
- [x] Quando `p_embedding IS NULL`: comportamento idêntico ao pré-STORY-438 (zero breaking change)
- [x] Grant de acesso: `service_role` only (consistente com função existente)

### AC4 — Backend: Embedding da Query
- [x] `datalake_query.py`: `query_datalake()` gera embedding da query quando `EMBEDDING_ENABLED=true`
- [x] Texto da query para embedding: concatenação de keywords do setor + termos customizados do usuário
- [x] Embedding de query cacheado em memória (`_embedding_cache`, TTL 1h) — evita N chamadas idênticas à OpenAI
- [x] Quando embedding da query falha: fallback para busca sem embedding (FTS only), log de aviso

### AC5 — Script de Backfill
- [x] `backend/scripts/backfill_embeddings.py` criado
- [x] Lê `pncp_raw_bids` em batches de 500 onde `embedding IS NULL AND is_active = true`
- [x] Chama OpenAI em batches de 100 (para reduzir overhead de rede)
- [x] UPDATE via Supabase com pgvector
- [x] Progresso exibido: `"Batch N/M — inserted X embeddings (Y errors)"`
- [x] Reexecutável (idempotente): `WHERE embedding IS NULL` evita reprocessar rows já embedados
- [x] Estimativa de custo exibida antes de iniciar (dry-run mode com `--dry-run` flag)

### AC6 — Qualidade e Não-Regressão
- [x] `EMBEDDING_ENABLED=false` → comportamento 100% idêntico ao pré-STORY-438 (testado em `test_embedding_not_in_rpc_params_when_disabled` e `test_embedding_skipped_when_disabled`)
- [x] `pytest tests/test_datalake_query.py tests/test_ingestion_loader.py` — 83 testes, zero falhas
- [x] `python scripts/run_tests_safe.py` completo — zero falhas novas
- [ ] `npm test` frontend — zero falhas *(sem alterações de API response — não aplicável)*
- [ ] A/B manual: busca "limpeza" com `EMBEDDING_ENABLED=true` retorna bids com "higienização" *(requer backfill + EMBEDDING_ENABLED=true em staging)*

---

## Valor de Negócio

Usuários que buscam por "limpeza hospitalar" hoje podem não encontrar bids com `objeto_compra` contendo "higienização e assepsia". Com busca híbrida, variantes semânticas do mesmo conceito passam a ser encontradas — aumentando o recall especialmente para setores com nomenclatura técnica variada (saúde, engenharia, TI). Impacto esperado: redução de "buscas sem resultado relevante" que hoje levam ao abandono no trial.

## Riscos

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| Storage Supabase free tier excede 500MB | Média | Verificar ANTES de criar coluna; 256 dims ≈ 41MB + HNSW ≈ 20MB. Se cheio: reduzir retention ou upgrade Supabase Pro |
| Rate limit OpenAI durante backfill (40K rows) | Alta | Usar batch de 100 textos com sleep de 0.5s entre batches; backoff via retries. Script tem flag `--sleep` |
| HNSW cold start — primeiro query lento | Baixa | HNSW carrega index em memória no primeiro uso; Supabase mantém instância quente |
| Cosine similarity threshold 0.6 muito restritivo | Média | Feature flag `EMBEDDING_THRESHOLD=0.6` ajustável via env var sem redeploy |
| Embedding de query adiciona latência P95 | Média | Cache in-memory por query_text com TTL 1h; ~99% das buscas repetidas são cache hit |

## Technical Notes

### Arquivos modificados
| Arquivo | Tipo | Mudança |
|---------|------|---------|
| `supabase/migrations/20260413000000_pgvector_embeddings.sql` | Novo | Extension + coluna + HNSW index |
| `supabase/migrations/20260413000001_search_datalake_hybrid.sql` | Novo | search_datalake hybrid + upsert_pncp_raw_bids com embedding |
| `backend/ingestion/loader.py` | Modificar | `_enrich_with_embeddings()` + `_generate_embeddings_batch()` |
| `backend/datalake_query.py` | Modificar | `_get_query_embedding()` + cache + `p_embedding` no RPC |
| `backend/config/features.py` | Modificar | `EMBEDDING_ENABLED`, `EMBEDDING_THRESHOLD` flags |
| `backend/scripts/backfill_embeddings.py` | Novo | Script de backfill idempotente com --dry-run |
| `backend/tests/test_datalake_query.py` | Modificar | 4 testes STORY-438 (embedding enabled/disabled/failure/cache) |
| `backend/tests/test_ingestion_loader.py` | Modificar | 3 testes STORY-438 (embedding enabled/failure/disabled) |

---

## File List

- [x] `supabase/migrations/20260413000000_pgvector_embeddings.sql`
- [x] `supabase/migrations/20260413000001_search_datalake_hybrid.sql`
- [ ] `backend/ingestion/transformer.py` *(sem mudanças necessárias — embedding gerado no loader)*
- [x] `backend/ingestion/loader.py`
- [x] `backend/datalake_query.py`
- [x] `backend/config/features.py`
- [x] `backend/scripts/backfill_embeddings.py`
- [x] `backend/tests/test_datalake_query.py`
- [x] `backend/tests/test_ingestion_loader.py`

---

## Definition of Done

- [ ] Pré-condição de storage verificada e documentada no PR *(pendente — devops)*
- [x] Todos os ACs de implementação verificados
- [x] `EMBEDDING_ENABLED=false` funciona sem regressões
- [ ] Backfill executado em staging antes de prod *(pendente — EMBEDDING_ENABLED=false até validação)*
- [ ] Migration aplicada em prod via `supabase db push` *(pendente — devops)*
- [x] `pytest` pass (sem falhas novas)
- [ ] `npm test` pass *(sem mudanças — não aplicável)*
- [x] Story status → Done
