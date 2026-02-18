# GTM-RESILIENCE-B02 — Sistema Hot/Warm/Cold de Prioridade de Cache

**Track:** B — Cache Inteligente
**Prioridade:** P1
**Sprint:** 2
**Estimativa:** 5-7 horas
**Gaps Endereados:** C-02, C-08
**Dependencias:** GTM-RESILIENCE-B03 (metadata de health — campo `priority`)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

O cache atual do SmartLic trata todas as entradas igualmente. A tabela `search_results_cache` impoe um maximo de 5 entradas por usuario via trigger FIFO (`cleanup_search_cache_per_user()`). Isso significa que uma busca altamente frequente (ex: "Saude, SP+RJ, ultimos 10 dias") e evictada com a mesma prioridade que uma busca exploratoria feita uma unica vez.

### Estado Atual

- **Evicao FIFO**: Trigger remove entradas mais antigas alem de 5 por usuario (`026_search_results_cache.sql`)
- **TTL uniforme**: Fresh (0-6h), Stale (6-24h), Expired (>24h) — igual para todas as chaves
- **Sem frequencia de acesso**: Nenhum campo rastreia quantas vezes uma chave foi acessada
- **InMemoryCache**: LRU com max 10K entries — melhor que FIFO mas sem TTL diferenciado
- **Redis**: TTL fixo de 4h (`REDIS_CACHE_TTL_SECONDS = 14400`) para todas as chaves

### Impacto

- Usuarios power-user que fazem a mesma busca diariamente perdem cache com mesma probabilidade de usuarios casuais
- Setores de alto valor (Saude: contratos >R$1M) tratados igual a setores exploratarios
- Sem refresh proativo: chaves hot expiram e o proximo acesso paga custo total

---

## Problema

1. **Evicao cega**: FIFO remove as 5 entradas mais antigas, sem considerar frequencia ou valor
2. **TTL uniforme**: Uma busca feita 10x/dia tem o mesmo TTL de uma feita 1x
3. **Sem proatividade**: Chaves hot so sao refreshed quando alguem faz a busca novamente
4. **Sem classificacao**: Impossivel decidir quais chaves manter em cenarios de pressao de memoria

---

## Solucao

### Classificacao Hot/Warm/Cold

| Classe | Criterio | TTL Redis | TTL Supabase | Refresh |
|--------|----------|-----------|--------------|---------|
| **Hot** | >= 3 acessos em 24h OU setor top-3 do usuario | 2h | 12h | Proativo (B-01) |
| **Warm** | 1-2 acessos em 24h OU busca salva | 6h | 24h | On-demand |
| **Cold** | 0 acessos em 24h, nao salva | 1h | 24h | Nenhum |

### Mecanismo de Classificacao

1. **Contador de acessos**: Campo `access_count` na tabela, incrementado em cada `get_from_cache()` hit
2. **Ultimo acesso**: Campo `last_accessed_at` atualizado em cada hit
3. **Classificacao dinamica**: Funcao `classify_priority(access_count, last_accessed_at, is_saved_search) -> CachePriority`
4. **Evicao inteligente**: Modificar trigger para preservar hot keys e evictar cold primeiro

### Evicao Atualizada

```
Quando inserir nova entrada (6a entrada para o usuario):
  1. Se existem entradas COLD → evictar a mais antiga COLD
  2. Se todas sao WARM+ → evictar a mais antiga WARM
  3. Se todas sao HOT → evictar a mais antiga HOT (FIFO dentro da classe)
  4. Aumentar limite para 10 entries/user (de 5)
```

### TTL Diferenciado no Redis

```python
REDIS_TTL_BY_PRIORITY = {
    CachePriority.HOT: 7200,    # 2h
    CachePriority.WARM: 21600,  # 6h
    CachePriority.COLD: 3600,   # 1h
}
```

---

## Criterios de Aceite

### AC1 — Enum CachePriority com 3 niveis
Criar `CachePriority(str, Enum)` com valores `hot`, `warm`, `cold` em `search_cache.py`.
**Teste**: Importar enum e verificar valores.

### AC2 — Funcao classify_priority deterministica
`classify_priority(access_count, last_accessed_at, is_saved_search) -> CachePriority` retorna:
- HOT se `access_count >= 3` nas ultimas 24h OU `is_saved_search == True` com acesso recente
- WARM se `access_count >= 1` nas ultimas 24h
- COLD caso contrario
**Teste**: 6 cenarios (hot por frequencia, hot por saved, warm, cold, edge cases de 24h boundary).

### AC3 — Campo priority na tabela search_results_cache
Migration adiciona coluna `priority TEXT NOT NULL DEFAULT 'cold'` + `access_count INTEGER NOT NULL DEFAULT 0` + `last_accessed_at TIMESTAMPTZ`.
**Teste**: Verificar que migration aplica sem erro e novos registros tem defaults corretos.

### AC4 — Incremento de access_count em cada cache hit
`get_from_cache()` atualiza `access_count = access_count + 1` e `last_accessed_at = now()` no Supabase apos cada hit bem-sucedido.
**Teste**: Chamar `get_from_cache()` 3x; verificar que `access_count == 3` e `last_accessed_at` atualizado.

### AC5 — Reclassificacao automatica apos access_count update
Apos incrementar `access_count`, recalcular `priority` e atualizar na tabela se mudou.
**Teste**: Inserir entry cold, acessar 3x, verificar que priority mudou para hot.

### AC6 — TTL diferenciado no Redis por prioridade
`_save_to_redis()` usa `REDIS_TTL_BY_PRIORITY[priority]` em vez do TTL fixo de 4h.
**Teste**: Salvar entry hot no Redis; verificar TTL == 7200. Salvar cold; verificar TTL == 3600.

### AC7 — Evicao inteligente substitui FIFO
Trigger `cleanup_search_cache_per_user()` atualizado para:
1. Contar entries por usuario (limite agora 10, nao 5)
2. Evictar cold primeiro, depois warm, depois hot
3. Dentro da mesma classe, evictar por `last_accessed_at` (mais antigo primeiro)
**Teste**: Inserir 11 entries (3 hot, 4 warm, 4 cold); verificar que 1 cold foi evictada.

### AC8 — Campo priority exposto no retorno de get_from_cache
O dict retornado por `get_from_cache()` inclui campo `cache_priority: CachePriority`.
**Teste**: Verificar campo presente no retorno.

### AC9 — Proactive refresh para hot keys (integracao com B-01)
Quando uma entry hot esta a 30min de expirar (TTL < 30min), a revalidacao e disparada proativamente mesmo sem acesso. Requer B-01 implementado.
**Teste**: Setar entry hot com `fetched_at` a 5.5h atras (30min de expirar); verificar que revalidacao proativa e disparada.

### AC10 — Metricas de distribuicao de prioridade
Endpoint `GET /v1/health/cache` inclui `priority_distribution: {hot: N, warm: N, cold: N}`.
**Teste**: Inserir entries mistas; chamar health endpoint; verificar contagem correta.

---

## Arquivos Afetados

| Arquivo | Alteracao |
|---------|-----------|
| `backend/search_cache.py` | `CachePriority` enum, `classify_priority()`, TTL diferenciado, access_count update |
| `backend/redis_pool.py` | Nenhuma alteracao (InMemoryCache ja usa LRU) |
| `supabase/migrations/031_cache_priority_fields.sql` | Adicionar `priority`, `access_count`, `last_accessed_at`; atualizar trigger |
| `backend/main.py` | Atualizar `/v1/health/cache` com priority_distribution |
| `backend/tests/test_cache_priority.py` | 12+ testes unitarios |
| `backend/tests/test_search_cache.py` | Atualizar testes existentes para novos campos |

---

## Dependencias

- **GTM-RESILIENCE-B03**: Campo `priority` pode ser adicionado na mesma migration, mas B-03 define os campos de health separados
- **GTM-RESILIENCE-B01**: AC9 (proactive refresh) depende de B-01 estar implementado

---

## Definition of Done

- [ ] Todos os 10 ACs implementados e testados
- [ ] Migration aplicada sem erro no Supabase
- [ ] TTL diferenciado verificavel no Redis (quando provisionado)
- [ ] Trigger de evicao atualizado e testado com 11+ entries
- [ ] Zero regressoes na suite de testes existente
- [ ] Health endpoint mostrando distribuicao de prioridade
- [ ] Documentacao inline com exemplos de classificacao
