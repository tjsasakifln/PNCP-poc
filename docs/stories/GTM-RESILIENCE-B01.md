# GTM-RESILIENCE-B01 — Stale-While-Revalidate Real (Background Refresh)

**Track:** B — Cache Inteligente
**Prioridade:** P1
**Sprint:** 2
**Estimativa:** 6-8 horas
**Gaps Endereados:** C-01, C-07
**Dependencias:** GTM-RESILIENCE-B04 (Redis provisionado), GTM-RESILIENCE-B03 (metadata de health)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

O sistema SmartLic possui uma arquitetura de cache 3-level (Supabase, Redis/InMemory, Local file) com politica SWR (Stale-While-Revalidate). O cache classifica entradas como Fresh (0-6h), Stale (6-24h) e Expired (>24h). Quando uma entrada stale e servida, o usuario recebe dados defasados -- o que e correto e desejavel como colchao de impacto.

Porem, **o sistema nao dispara revalidacao em background apos servir cache stale**. Isso significa que a proxima busca do usuario (ou de qualquer usuario com os mesmos parametros) paga o custo total de fetch live, mesmo que o cache stale tenha acabado de ser servido. O comportamento atual e puramente reativo: so busca dados frescos quando o usuario explicitamente executa uma nova busca.

### Estado Atual (search_cache.py + search_pipeline.py)

- `get_from_cache()` retorna entradas stale com flag `is_stale: True`
- O pipeline em `search_pipeline.py` serve o cache stale quando fontes live falham
- **Nenhum `asyncio.create_task()` e disparado** para revalidar em background
- O proximo request com os mesmos parametros repete 100% do fetch

### Principio Arquitetural

> Cache = Colchao de Impacto, nao Acelerador. O colchao absorve o impacto e permite vender assinatura.

Se o cache e servido stale, a revalidacao em background garante que o proximo acesso (do mesmo usuario ou de outro com mesmos parametros) encontre dados frescos -- sem pagar o custo de fetch.

---

## Problema

1. **Custo repetido**: Cada request apos cache stale paga custo total de fetch (10-30s, N requests HTTP)
2. **Desperdicio de oportunidade**: O momento em que se serve stale e ideal para revalidar -- o sistema esta ocioso apos responder
3. **Experiencia degradada**: Usuarios frequentes (hot keys) recebem stale repetidamente sem melhoria
4. **Sem notificacao**: Se o usuario ainda esta conectado via SSE quando a revalidacao completa, nao recebe os dados atualizados

---

## Solucao

### 1. Background Revalidation Task

Apos servir cache stale no pipeline, disparar `asyncio.create_task()` que:
- Executa fetch live completo (PNCP + PCP) com os mesmos parametros
- Atualiza o cache em todos os niveis (Supabase, Redis, Local)
- Respeita circuit breakers e rate limiters existentes
- Tem budget limit (max 1 revalidacao por chave a cada 10 minutos)

### 2. Dedup de Revalidacoes

Manter set de chaves em revalidacao (in Redis ou in-memory) para evitar disparar multiplas revalidacoes para a mesma chave simultaneamente.

### 3. SSE Notification (opcional)

Se o ProgressTracker do search_id original ainda estiver ativo:
- Emitir evento SSE `revalidated` com resumo dos dados atualizados
- Frontend pode opcionalmente mostrar toast "Dados atualizados disponveis"

### 4. Budget Control

- Max 3 revalidacoes simultaneas por worker
- Min 10 minutos entre revalidacoes da mesma chave
- Timeout de 180s para a revalidacao (nao compete com requests ativos)
- Skip se circuit breaker estiver degraded (nao faz sentido revalidar se a fonte esta fora)

---

## Criterios de Aceite

### AC1 — Background task disparado apos cache stale
Quando `get_from_cache()` retorna uma entrada com `is_stale: True` e o pipeline serve essa entrada ao usuario, um `asyncio.create_task()` deve ser criado para revalidar os dados em background.
**Teste**: Mock `get_from_cache` para retornar stale; verificar que `asyncio.create_task` foi chamado com a funcao de revalidacao.

### AC2 — Revalidacao atualiza cache em todos os niveis
A task de background deve chamar o fetch live e, em caso de sucesso, chamar `save_to_cache()` com os novos resultados, atualizando Supabase, Redis e Local.
**Teste**: Disparar revalidacao mock; verificar que `save_to_cache` foi chamado com resultados novos.

### AC3 — Dedup de revalidacoes concorrentes
Se uma revalidacao para a mesma `params_hash` ja esta em andamento, uma nova nao deve ser disparada. Usar chave em Redis (`revalidating:{params_hash}`) com TTL de 10 minutos.
**Teste**: Disparar 3 revalidacoes para a mesma chave simultaneamente; verificar que apenas 1 fetch live ocorreu.

### AC4 — Budget limit de revalidacoes simultaneas
Maximo de 3 revalidacoes simultaneas por worker. Se o limite for atingido, a revalidacao e silenciosamente descartada (nao falha, nao bloqueia).
**Teste**: Disparar 5 revalidacoes; verificar que apenas 3 foram executadas e 2 foram descartadas.

### AC5 — Timeout de revalidacao independente
A task de background tem timeout proprio de 180s (`REVALIDATION_TIMEOUT`), configuravel via env var. Nao interfere com timeouts de requests ativos.
**Teste**: Mock fetch que demora 200s; verificar que a revalidacao e cancelada apos 180s sem afetar o pipeline principal.

### AC6 — Circuit breaker check antes de revalidar
Se o circuit breaker da fonte principal (PNCP) estiver degraded, a revalidacao nao e disparada.
**Teste**: Setar `_circuit_breaker.degraded_until` no futuro; disparar revalidacao; verificar que fetch live nao foi chamado.

### AC7 — SSE notification quando usuario conectado (opcional)
Se o `ProgressTracker` do `search_id` original ainda existir e tiver listeners, emitir evento `revalidated` com `total_results` e `fetched_at` atualizados. Se nao houver listeners, skip silenciosamente.
**Teste**: Criar ProgressTracker, disparar revalidacao, verificar que evento `revalidated` foi emitido na queue.

### AC8 — Logging estruturado da revalidacao
Cada revalidacao gera 1 log JSON com: `params_hash`, `trigger` (stale_served), `duration_ms`, `result` (success/timeout/error/skipped), `new_results_count`.
**Teste**: Executar revalidacao; capturar log; verificar campos obrigatorios.

### AC9 — Metadata de health atualizada (depende B-03)
Apos revalidacao bem-sucedida, atualizar `last_success_at` e resetar `fail_streak` na tabela `search_results_cache`. Apos falha, incrementar `fail_streak` e setar `last_attempt_at`.
**Teste**: Revalidacao com sucesso atualiza `last_success_at`; revalidacao com falha incrementa `fail_streak`.

### AC10 — Nenhuma regressao no pipeline sincrono
O fluxo sincrono (usuario aguardando resposta) nao deve ser afetado pela revalidacao em background. Nenhum await adicional no hot path.
**Teste**: Rodar suite completa de testes do pipeline; zero falhas novas.

---

## Arquivos Afetados

| Arquivo | Alteracao |
|---------|-----------|
| `backend/search_cache.py` | Adicionar `trigger_background_revalidation()`, `_is_revalidating()`, `_mark_revalidating()` |
| `backend/search_pipeline.py` | Chamar `trigger_background_revalidation()` apos servir stale cache (~L805-817) |
| `backend/progress.py` | Adicionar metodo `emit_revalidated()` no ProgressTracker |
| `backend/config.py` | Adicionar constantes `REVALIDATION_TIMEOUT`, `MAX_CONCURRENT_REVALIDATIONS`, `REVALIDATION_COOLDOWN_S` |
| `backend/tests/test_background_revalidation.py` | Testes unitarios (10+ testes) |
| `backend/tests/test_search_pipeline.py` | Atualizar testes existentes para verificar que revalidacao e disparada |

---

## Dependencias

- **GTM-RESILIENCE-B04**: Redis deve estar provisionado para dedup de revalidacoes funcionar cross-worker
- **GTM-RESILIENCE-B03**: Campos `last_success_at`, `fail_streak`, `last_attempt_at` devem existir na tabela

---

## Definition of Done

- [ ] Todos os 10 ACs implementados e testados
- [ ] Testes unitarios passando (10+ novos)
- [ ] Zero regressoes na suite existente do pipeline
- [ ] Log de revalidacao visivel no Railway (1 linha JSON por revalidacao)
- [ ] Documentacao inline no codigo (docstrings)
- [ ] Code review aprovado
- [ ] Metricas de revalidacao rastreaveeis (success/skip/timeout/error)
