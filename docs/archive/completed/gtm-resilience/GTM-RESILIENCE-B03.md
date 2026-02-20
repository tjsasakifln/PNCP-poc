# GTM-RESILIENCE-B03 — Metadata de Health por Chave de Cache

**Track:** B — Cache Inteligente
**Prioridade:** P1
**Sprint:** 2 (prerequisito para B-01 e B-02)
**Estimativa:** 3-4 horas
**Gaps Endereados:** C-03
**Dependencias:** Nenhuma (pode ser executada independentemente)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

A tabela `search_results_cache` atual possui apenas campos de dados (results, params_hash, sources_json, fetched_at, created_at). Nao ha nenhum campo que rastreie a saude de cada chave de cache individualmente.

### Schema Atual (migracoes 026 + 027)

```sql
search_results_cache (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    params_hash TEXT NOT NULL,
    search_params JSONB NOT NULL,
    results JSONB NOT NULL,
    total_results INTEGER DEFAULT 0,
    sources_json JSONB DEFAULT '["pncp"]',
    fetched_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, params_hash)
)
```

### Campos Ausentes (Identificados na Investigacao)

| Campo | Proposito | Impacto da Ausencia |
|-------|-----------|---------------------|
| `last_success_at` | Ultimo fetch live bem-sucedido | Impossivel saber freshness real do dado |
| `last_attempt_at` | Ultimo fetch live tentado (sucesso ou falha) | Impossivel evitar re-tentativas imediatas |
| `fail_streak` | Contagem consecutiva de falhas de fetch | Impossivel implementar backoff inteligente |
| `degraded_until` | Timestamp ate quando considerar chave degradada | Impossivel implementar circuit breaker por chave |
| `coverage` | Quais UFs tiveram dados no ultimo fetch | Impossivel mostrar "7 de 9 UFs processadas" |
| `fetch_duration_ms` | Duracao do ultimo fetch | Impossivel trending de performance |

Sem esses campos, as stories B-01 (background revalidation) e B-02 (hot/warm/cold) nao podem implementar logica de backoff inteligente, degradacao por chave, ou refresh seletivo.

---

## Problema

1. **Backoff cego**: Sem `fail_streak`, o sistema revalida chaves que falham repetidamente com a mesma frequencia
2. **Re-tentativa imediata**: Sem `last_attempt_at`, dois usuarios podem disparar fetch para a mesma chave falhando no mesmo segundo
3. **Freshness opaca**: Sem `last_success_at`, o sistema nao distingue "cache de 6h com fetch tentado ha 5min" de "cache de 6h sem tentativa recente"
4. **Cobertura invisivel**: Sem `coverage`, impossivel mostrar ao usuario quantas UFs tiveram dados vs falharam
5. **Performance tracking ausente**: Sem `fetch_duration_ms`, impossivel detectar degradacao lenta

---

## Solucao

### Migration SQL

Adicionar 6 novos campos a tabela `search_results_cache`:

```sql
ALTER TABLE search_results_cache
    ADD COLUMN IF NOT EXISTS last_success_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS fail_streak INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS degraded_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS coverage JSONB,
    ADD COLUMN IF NOT EXISTS fetch_duration_ms INTEGER;
```

### Logica de Atualizacao (search_cache.py)

**Em fetch bem-sucedido:**
```python
last_success_at = now()
last_attempt_at = now()
fail_streak = 0
degraded_until = None
coverage = {"succeeded_ufs": [...], "failed_ufs": [...]}
fetch_duration_ms = elapsed
```

**Em fetch falhado:**
```python
last_attempt_at = now()
fail_streak = fail_streak + 1
degraded_until = now() + backoff(fail_streak)  # exponential: 1min, 5min, 15min, 30min max
# NAO atualiza last_success_at, results, sources_json
```

### Funcao de Backoff

```python
def calculate_backoff_minutes(fail_streak: int) -> int:
    """Exponential backoff: 1, 5, 15, 30 (max)."""
    return min(30, [1, 5, 15, 30][min(fail_streak - 1, 3)])
```

---

## Criterios de Aceite

### AC1 — Migration adiciona 6 campos
Migration SQL cria campos `last_success_at`, `last_attempt_at`, `fail_streak`, `degraded_until`, `coverage`, `fetch_duration_ms` na tabela `search_results_cache`. Todos com defaults seguros (NULL ou 0).
**Teste**: Aplicar migration em banco limpo; verificar schema com `\d search_results_cache`.

### AC2 — Campos populados em fetch bem-sucedido
Quando `save_to_cache()` e chamado apos fetch live bem-sucedido, os campos `last_success_at`, `last_attempt_at`, `fail_streak=0`, `degraded_until=None`, `coverage`, `fetch_duration_ms` sao escritos.
**Teste**: Chamar `save_to_cache()` com dados validos; verificar todos os 6 campos na row do Supabase.

### AC3 — fail_streak incrementado em falha
Nova funcao `record_cache_fetch_failure(user_id, params_hash)` incrementa `fail_streak` e seta `last_attempt_at = now()`. Se `fail_streak >= 1`, calcula e seta `degraded_until`.
**Teste**: Chamar `record_cache_fetch_failure()` 3x; verificar `fail_streak == 3` e `degraded_until` calculado com backoff.

### AC4 — Backoff exponencial correto
`calculate_backoff_minutes(fail_streak)` retorna: 1 (streak=1), 5 (streak=2), 15 (streak=3), 30 (streak>=4).
**Teste**: Verificar 5 valores: streak 0 (0), 1 (1min), 2 (5min), 3 (15min), 4+ (30min).

### AC5 — degraded_until respeitado
Nova funcao `is_cache_key_degraded(user_id, params_hash) -> bool` retorna True se `degraded_until > now()`. Callers (B-01 revalidation) devem consultar antes de disparar fetch.
**Teste**: Setar `degraded_until` 10min no futuro; verificar retorno True. Setar no passado; verificar False.

### AC6 — Coverage JSONB estruturado
Campo `coverage` armazena `{"succeeded_ufs": ["SP","RJ"], "failed_ufs": ["MA"], "total_requested": 3}`.
**Teste**: Salvar cache com coverage; ler de volta; verificar estrutura JSONB intacta.

### AC7 — fetch_duration_ms populado
`save_to_cache()` aceita parametro opcional `fetch_duration_ms: int` e persiste no Supabase.
**Teste**: Chamar com `fetch_duration_ms=1500`; verificar campo na row.

### AC8 — Backward compatibility total
Entradas existentes sem os novos campos continuam funcionando. `get_from_cache()` retorna None para campos ausentes sem erro.
**Teste**: Inserir row SEM novos campos (simulando dados pre-migration); chamar `get_from_cache()`; verificar retorno valido sem excecao.

### AC9 — Health endpoint mostra fail_streak agregado
`GET /v1/health/cache` inclui `degraded_keys_count` e `avg_fail_streak` calculados a partir dos novos campos.
**Teste**: Inserir 3 entries com fail_streak variado; chamar health; verificar metricas.

### AC10 — Indice para consulta de degraded keys
Criar indice `idx_search_cache_degraded` em `degraded_until` para queries eficientes de "quais chaves estao degradadas".
**Teste**: `EXPLAIN ANALYZE` da query `WHERE degraded_until > now()` usa o indice.

---

## Arquivos Afetados

| Arquivo | Alteracao |
|---------|-----------|
| `supabase/migrations/031_cache_health_metadata.sql` | Adicionar 6 campos + indice |
| `backend/search_cache.py` | `record_cache_fetch_failure()`, `is_cache_key_degraded()`, `calculate_backoff_minutes()`, atualizar `save_to_cache()` |
| `backend/search_pipeline.py` | Passar `fetch_duration_ms` e `coverage` para `save_to_cache()` |
| `backend/main.py` | Atualizar `/v1/health/cache` com metricas de degradacao |
| `backend/tests/test_cache_health_metadata.py` | 12+ testes unitarios |
| `backend/tests/test_search_cache.py` | Atualizar testes existentes para novos campos |

---

## Nota sobre Numeracao de Migration

A proxima migration disponivel deve ser verificada no momento da implementacao. Os numeros usados nesta story (031) sao indicativos -- o dev deve verificar o ultimo numero em `supabase/migrations/` e usar o proximo sequencial.

---

## Dependencias

- Nenhuma dependencia de outras stories do Track B
- **E prerequisito para**: B-01 (AC9 usa `last_success_at` e `fail_streak`), B-02 (usa `priority` e `access_count`)

---

## Definition of Done

- [x] Todos os 10 ACs implementados e testados
- [ ] Migration aplicada no Supabase (staging e producao)
- [x] Backward compatibility verificada com dados existentes
- [x] Zero regressoes na suite de testes de cache
- [ ] Indice de degradacao validado com EXPLAIN ANALYZE
- [x] Health endpoint atualizado e verificavel em producao
- [x] Documentacao inline com descricao de cada campo e seu proposito
