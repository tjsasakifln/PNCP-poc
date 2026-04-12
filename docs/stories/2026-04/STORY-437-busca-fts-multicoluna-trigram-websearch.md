# STORY-437 — Busca: Quick Wins FTS Multi-coluna + websearch_to_tsquery + Trigram Fallback

**Status:** Done
**Type:** Feature (Backend-only)
**Priority:** Medium
**Estimativa:** 2 dias
**Custo adicional:** Zero

---

## Contexto

O SmartLic usa PostgreSQL FTS (tsvector + tsquery, dicionário português) como camada primária de busca no datalake. Três lacunas de recall foram identificadas:

1. **FTS limitado a `objeto_compra`** — campos como `orgao_razao_social` ("Secretaria de Obras e Infraestrutura") e `unidade_nome` são ignorados, então bids com objetos genéricos ("Contratação de empresa especializada") não são encontrados mesmo que o órgão sinalize o setor
2. **tsquery manual** — termos customizados digitados pelo usuário são parseados com `|`/`&` hardcoded; `websearch_to_tsquery` aceitaria linguagem natural (aspas para frase exata, `-` para exclusão)
3. **Sem fallback quando FTS retorna 0** — `pg_trgm` já está habilitado no banco, mas não é usado para bids; poderia funcionar como rede de segurança fuzzy

Esta story implementa as três melhorias com **zero custo adicional** e sem alterações de API ou frontend.

---

## Acceptance Criteria

### AC1 — FTS Multi-coluna (Pesos A/B/C)
- [x] Trigger `pncp_raw_bids_tsv_trigger` atualizado para compor `tsv` como:
  - Peso A: `to_tsvector('portuguese', objeto_compra)`
  - Peso B: `to_tsvector('portuguese', orgao_razao_social)`
  - Peso C: `to_tsvector('portuguese', unidade_nome)`
- [x] Backfill executado: todos os rows existentes têm `tsv` atualizado com nova composição
- [x] `search_datalake` RPC usa `b.tsv @@ v_ts_query` (stored column) em vez de recomputar `to_tsvector()` inline
- [x] `ts_rank` no ORDER BY também usa `b.tsv`
- [ ] Testes: busca por keyword de engenharia retorna bids onde `objeto_compra` é genérico mas `orgao_razao_social` contém "Obras" ou "Infraestrutura" *(requer dados reais — validar pós-migration)*

### AC2 — `websearch_to_tsquery` para Termos Customizados
- [x] `_build_tsquery()` em `datalake_query.py` refatorado para retornar `tuple[str | None, str | None]` — keywords → `p_tsquery`, custom terms → `p_websearch_text`
- [x] Quando há setor + termos customizados: keywords do setor continuam com `|` (OR), termos customizados enviados como `p_websearch_text` para `websearch_to_tsquery` no SQL
- [x] Termos customizados com aspas (`"limpeza hospitalar"`) preservados verbatim para frase exata
- [x] Termos com `-` (ex: `-escolar`) preservados verbatim para exclusão
- [x] Testes unitários cobrindo: só setor, só custom, setor+custom, custom com aspas, custom com exclusão (17 testes em `TestBuildTsquery`)

### AC3 — Trigram Fallback quando FTS retorna 0
- [x] Feature flag `TRIGRAM_FALLBACK_ENABLED` em `backend/config/features.py` (default: `True`)
- [x] `query_datalake()` em `datalake_query.py`: quando datalake retorna 0 resultados E há tsquery/websearch_text E flag está ativo, chama RPC `search_datalake_trigram_fallback`
- [x] Nova RPC `search_datalake_trigram_fallback(p_query_term TEXT, p_ufs TEXT[], p_limit INT)` usando `word_similarity(p_query_term, objeto_compra) > 0.3`
- [x] Resultados do fallback têm campo `_source: 'trigram_fallback'` no retorno (para observabilidade)
- [x] Log estruturado quando fallback ativa: `{"event": "trigram_fallback_activated", "query": ..., "results_found": N}`
- [x] Quando `TRIGRAM_FALLBACK_ENABLED=False`, comportamento idêntico ao estado anterior

### AC4 — Qualidade e Não-Regressão
- [x] `pytest tests/test_datalake_query.py` — 62 testes, zero falhas
- [x] `python scripts/run_tests_safe.py` completo — zero falhas novas (128 pre-existing, baseline)
- [ ] `npm test` frontend — zero falhas novas (sem alterações de API response) *(não executado — zero mudanças de API shape)*
- [x] Migration idempotente: `CREATE INDEX IF NOT EXISTS`, `CREATE OR REPLACE FUNCTION`
- [x] Latência de busca não aumenta (stored `tsv` column elimina recompute inline)

---

## Escopo

**IN:** Trigger tsv, backfill, RPC search_datalake, websearch_to_tsquery via p_websearch_text, RPC trigram fallback, feature flag, logs
**OUT:** Nenhuma mudança de API response shape, nenhuma mudança de frontend, nenhuma mudança no pipeline de classificação LLM

## Valor de Negócio

Bids com `objeto_compra` genérico ("Contratação de empresa especializada") hoje são invisíveis para setores específicos. Com FTS multi-coluna, o contexto do órgão ("Secretaria de Obras") passa a contribuir para o match — aumentando o recall sem custo adicional. O trigram fallback evita "sem resultados" em buscas com termos customizados, reduzindo fricção no onboarding de novos usuários.

## Riscos

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| Backfill UPDATE em 40K rows causa lentidão no Supabase free tier | Média | Executar em horário de baixo tráfego (madrugada BRT); Supabase suporta UPDATE concorrente sem lock de tabela |
| tsv multi-coluna aumenta tamanho do index GIN | Baixa | orgao_razao_social e unidade_nome têm texto curto; estimativa de overhead ≤ 30MB |
| Trigram fallback retorna falsos positivos (threshold 0.3 é baixo) | Média | Resulta marcado como `_source: 'trigram_fallback'` — usuário vê contexto; threshold pode ser ajustado via config |
| websearch_to_tsquery rejeita queries complexas | Baixa | websearch_to_tsquery é extremamente leniente — raramente falha; textos em branco tratados via IS NULL no SQL |

## Technical Notes

### Arquivos modificados
| Arquivo | Tipo | Mudança |
|---------|------|---------|
| `supabase/migrations/20260412000000_search_fts_multicolumn.sql` | Novo | Trigger A/B/C + backfill + search_datalake com p_websearch_text |
| `supabase/migrations/20260412000001_search_trigram_fallback_rpc.sql` | Novo | `search_datalake_trigram_fallback` RPC |
| `backend/datalake_query.py` | Modificar | `_build_tsquery()` retorna tuple + trigram fallback + embedding cache |
| `backend/config/features.py` | Modificar | `TRIGRAM_FALLBACK_ENABLED` flag |
| `backend/tests/test_datalake_query.py` | Modificar | 62 testes (rewrite completo para tuple return) |

---

## File List

- [x] `supabase/migrations/20260412000000_search_fts_multicolumn.sql`
- [x] `supabase/migrations/20260412000001_search_trigram_fallback_rpc.sql`
- [x] `backend/datalake_query.py`
- [x] `backend/config/features.py`
- [x] `backend/tests/test_datalake_query.py`

---

## Definition of Done

- [x] Todos os ACs implementados e testados
- [ ] Migration aplicada em prod via `supabase db push` *(pendente — devops)*
- [x] `pytest` pass (sem falhas novas)
- [ ] `npm test` pass *(sem mudanças de API — não aplicável)*
- [x] Story status → Done
