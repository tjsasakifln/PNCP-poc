# GTM-RESILIENCE-A03 — Ativar Leitura do L3 Cache (Local File)

**Track:** A — "Nunca Resposta Vazia" (P0)
**Prioridade:** P0
**Sprint:** 1
**Estimativa:** 2-3 horas
**Gaps cobertos:** P-04 (Local file cache escrito mas nunca lido no pipeline)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

A investigacao estrategica (FRENTE 1 — P-04) identificou que o sistema possui uma arquitetura de cache em 3 niveis:

| Nivel | Storage | TTL | Write | Read |
|-------|---------|-----|-------|------|
| L1 | Supabase | 24h | Sim (`_save_to_supabase`) | Sim (`_supabase_get_cache`) |
| L2 | Redis/InMemory | 4h | Sim (`InMemoryCache`) | Sim (proativo, antes de L1) |
| L3 | Local file (JSON) | 24h | **Sim** (`_save_to_local`) | **NUNCA** no pipeline |

O `search_cache.py` possui implementacao completa de escrita (`_save_to_local`, L189-200) e leitura (`_get_from_local`, L203-212) para arquivos locais. O `save_to_cache()` chama `_save_to_local()` como ultimo nivel do cascade de escrita. Porem, nenhum path de fallback no `search_pipeline.py` chama `_get_from_local()`.

### Impacto

Quando Supabase esta indisponivel (manutencao, rede, quota) e Redis/InMemory nao tem a chave (worker reiniciado, cold start), o cache L3 local — que pode conter dados validos de minutos atras — e completamente ignorado. O pipeline retorna vazio ou 504, desperdicando dados que JA EXISTEM no disco.

---

## Problema

1. **Escrita sem leitura**: A funcao `_get_from_local()` existe mas nao e chamada em nenhum path de fallback. O cascade de leitura em `search_pipeline.py` apenas consulta `_supabase_get_cache()`.

2. **Sem metadata de freshness no L3**: O arquivo local contem `fetched_at` (timestamp ISO) mas nao ha validacao de idade na leitura. `_get_from_local()` retorna qualquer arquivo existente sem verificar se esta dentro do TTL de 24h.

3. **Sem indicacao de nivel de cache**: Quando o pipeline serve dados de cache, `ctx.cache_level` e setado como `"supabase"` hardcoded. Nao ha distincao entre L1 (Supabase), L2 (InMemory) e L3 (local file) para observabilidade.

---

## Solucao Proposta

### 1. Integrar `_get_from_local()` no fallback cascade

Nos handlers de falha do pipeline (`except asyncio.TimeoutError`, `except Exception`, `except AllSourcesFailedError`), apos tentativa de Supabase falhar, adicionar chamada a `_get_from_local()` com o mesmo `cache_key` (hash dos parametros).

### 2. Validacao de TTL no L3

Adicionar verificacao de idade em `_get_from_local()`: se `fetched_at` + 24h < now, retornar None (expirado). Expor a idade em horas no retorno para metadata.

### 3. Funcao unificada `get_from_cache_cascade()`

Criar funcao publica em `search_cache.py` que encapsula o cascade completo:
```
L2 (InMemory) → L1 (Supabase) → L3 (Local file)
```
Retorna `{results, sources, cache_level, cache_age_hours, cache_status}` ou None.

Os handlers de fallback no pipeline chamariam esta funcao unica em vez de consultar niveis individualmente.

---

## Acceptance Criteria

### AC1 — `_get_from_local()` valida TTL
A funcao `_get_from_local()` em `search_cache.py` DEVE verificar `fetched_at` do arquivo JSON e retornar `None` se `fetched_at + 24h < datetime.now(UTC)`.

### AC2 — `_get_from_local()` retorna metadata de freshness
Quando o arquivo e valido (dentro do TTL), o retorno DEVE incluir `cache_age_hours: float` calculado como `(now - fetched_at).total_seconds() / 3600`.

### AC3 — `get_from_cache_cascade()` implementada
Nova funcao publica em `search_cache.py` que tenta L2 → L1 → L3 em sequencia, retornando o primeiro resultado valido com `cache_level` indicando qual nivel respondeu.

### AC4 — `get_from_cache_cascade()` retorna cache_level correto
O retorno DEVE incluir `cache_level: "memory" | "supabase" | "local"` correspondendo ao nivel que forneceu os dados.

### AC5 — Pipeline usa `get_from_cache_cascade()` no timeout handler
O `except asyncio.TimeoutError` em `search_pipeline.py` DEVE chamar `get_from_cache_cascade()` (substituindo a chamada direta a `_supabase_get_cache()`).

### AC6 — Pipeline usa `get_from_cache_cascade()` no exception handler
O `except Exception` em `search_pipeline.py:L818` DEVE chamar `get_from_cache_cascade()` (substituindo `_supabase_get_cache()`).

### AC7 — Pipeline usa `get_from_cache_cascade()` no AllSourcesFailedError handler
Se existir handler para `AllSourcesFailedError`, DEVE usar `get_from_cache_cascade()`.

### AC8 — `ctx.cache_level` reflete nivel real
Quando cache e servido, `ctx.cache_level` DEVE ser setado com o valor retornado por `get_from_cache_cascade()` (nao mais hardcoded "supabase").

### AC9 — Log indicando nivel de cache utilizado
Quando L3 e servido, DEVE logar: `event: "cache_l3_served"`, `cache_key`, `cache_age_hours`, `results_count`.

### AC10 — Teste: L1 falha, L3 serve
Teste unitario: mock `_supabase_get_cache` retornando None + mock `_get_from_local` retornando dados validos → `get_from_cache_cascade()` retorna dados com `cache_level="local"`.

### AC11 — Teste: L3 com arquivo expirado retorna None
Teste unitario: arquivo local com `fetched_at` de 25 horas atras → `_get_from_local()` retorna None.

### AC12 — Teste: L3 com arquivo valido retorna dados + age
Teste unitario: arquivo local com `fetched_at` de 3 horas atras → `_get_from_local()` retorna dados com `cache_age_hours` entre 2.9 e 3.1.

### AC13 — Teste: cascade completo (L2 miss → L1 miss → L3 hit)
Teste de integracao: InMemoryCache miss + Supabase Exception + local file presente → pipeline retorna dados com `cache_level="local"`.

---

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/search_cache.py` | Adicionar TTL validation em `_get_from_local()`; criar `get_from_cache_cascade()` |
| `backend/search_pipeline.py` | Substituir `_supabase_get_cache()` por `get_from_cache_cascade()` nos 3 handlers de erro |
| `backend/tests/test_search_cache.py` | AC10, AC11, AC12 |
| `backend/tests/test_search_pipeline.py` | AC13 |

---

## Dependencias

| Story | Relacao |
|-------|---------|
| **A-01** (Timeout Cache Fallback) | A-01 adiciona o path de cache no timeout handler; A-03 substitui a chamada direta por cascade. Podem ser implementadas juntas ou A-01 primeiro (usando apenas Supabase) e A-03 depois (upgrade para cascade). |
| **B-04** (Redis na Railway) | Quando Redis estiver disponivel, L2 passara de InMemoryCache para Redis distribuido. `get_from_cache_cascade()` ja suporta ambos — nenhuma mudanca necessaria. |

---

## Notas Tecnicas

### Anatomia do arquivo L3

```json
// backend/.cache/search/{hash[:32]}.json
{
  "results": [...],        // Array de licitacoes raw
  "sources_json": ["PNCP", "PCP"],
  "fetched_at": "2026-02-18T14:30:00+00:00"
}
```

### Consideracoes de disco

- Cada arquivo: ~50KB-500KB (dependendo do numero de licitacoes)
- Cleanup existente: cron cada 6h remove arquivos > 24h
- Railway disco efemero: arquivos sobrevivem entre requests mas NAO entre deploys
- L3 e util para: cold start de worker, Supabase downtime, rede intermitente

### Por que L2 antes de L1 no cascade

InMemoryCache (L2) e O(1) lookup sem I/O. Supabase (L1) requer HTTP roundtrip (~100-300ms). Local file (L3) requer disk I/O (~5-20ms). Ordem otima: L2 → L1 → L3.

---

## Definition of Done

- [x] Todos os 13 ACs verificados e passing
- [x] Testes unitarios: 8 novos (4 TTL + 4 cascade), zero regressoes
- [x] `_get_from_local()` nunca retorna dados com mais de 24h
- [x] `get_from_cache_cascade()` tenta todos os 3 niveis em ordem (L2→L1→L3)
- [x] Log de `cache_l3_served` visivel quando L3 e utilizado
- [x] Code review aprovado
- [x] Commit convencional: `feat(backend): GTM-RESILIENCE-A03 — L3 local file cache read + unified cascade`
