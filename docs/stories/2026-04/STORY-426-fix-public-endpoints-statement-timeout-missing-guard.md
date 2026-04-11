# STORY-426: Fix Statement Timeout em Endpoints Públicos sem Timeout Guard

**Priority:** P1
**Effort:** M (1-2 days)
**Squad:** @dev + @data-engineer
**Status:** Ready
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sprint:** Sprint Seguinte (48h-1w)

---

## Contexto

Sentry (varredura 2026-04-11) mostra `PostgreSQL error code 57014 — statement_timeout` em múltiplos endpoints públicos da aplicação. Esses endpoints realizam queries de agregação pesadas em tabelas grandes (`pncp_raw_bids`, `search_sessions`) **sem timeout guard no código da aplicação** e **sem circuit breaker** — quando o DB está sob carga, as queries excedem o `statement_timeout` configurado no Supabase (default 8s).

**Endpoints afetados identificados no Sentry:**
- Endpoints que realizam agregações sobre `pncp_raw_bids` (contagem por UF, modalidade, período)
- Endpoints de estatísticas de município (`/v1/municipios/{uf}/stats`)
- RPC calls pesadas do tipo `search_datalake` sob alta carga concorrente

**Padrão do erro no Sentry:**
```
ERROR: canceling statement due to statement timeout
CONTEXT: SQL function "..." during inlining
code: 57014
```

**Root cause:** Ausência de:
1. `SET LOCAL statement_timeout` antes de queries longas
2. `httpx.Timeout` / `asyncio.wait_for` com timeout explícito no código Python
3. Circuit breaker para isolar falhas de timeout dos demais endpoints

**Relação com STORY-416:** O CB de Supabase (read_cb) protege contra falhas de conexão/rate, mas não tem configuração especial para statement_timeout (código 57014). O erro não chega a abrir o CB porque é tratado como erro excluso via `_is_schema_error` — mas `57014` NÃO é schema error, apenas PGRST204/205 são.

---

## Acceptance Criteria

### AC1: Identificar todos os call sites sem timeout guard
- [ ] Auditar `backend/routes/municipios_publicos.py` — mapear queries sem `asyncio.wait_for`
- [ ] Auditar `backend/datalake_query.py` — verificar `search_datalake` RPC timeout
- [ ] Auditar `backend/routes/analytics.py` — queries de agregação
- [ ] Listar todos os pontos vulneráveis no Dev Notes

### AC2: Adicionar timeout guard nos call sites críticos
- [ ] Envolver queries pesadas em `asyncio.wait_for(coroutine, timeout=X)` com `X` configurable via env var
- [ ] Default timeout para queries públicas de agregação: 6s (< Supabase statement_timeout de 8s)
- [ ] Retornar resposta degradada (dados parciais ou cache stale) em vez de 500 quando timeout ocorre
- [ ] Logar métricas `smartlic_public_query_timeout_total{endpoint}` via Prometheus

### AC3: Garantir que `57014` conta como falha no CB
- [ ] Verificar `_is_schema_error()` em `supabase_client.py` — confirmar que código `57014` NÃO está na lista de exclusão
- [ ] Se estiver excluído por engano, corrigir para que timeout conta como failure no CB
- [ ] Test: simular 5 erros `57014` consecutivos → confirmar que `read_cb` abre

### AC4: Índices para queries de agregação pesadas
- [ ] Verificar se `pncp_raw_bids` tem índice em `(uf, is_active, created_at)` — colunas usadas em municipios_publicos
- [ ] Criar migration com índice faltante se necessário
- [ ] `EXPLAIN ANALYZE` da query mais lenta deve mostrar Index Scan (não Seq Scan)

### AC5: Runbook
- [ ] Adicionar seção "Statement Timeout (57014)" ao `docs/runbook/supabase-circuit-breaker.md`
- [ ] Documentar como identificar query ofensora via `pg_stat_activity`

---

## Scope

**IN:**
- `backend/routes/municipios_publicos.py` — timeout guard
- `backend/datalake_query.py` — timeout em `search_datalake`
- `supabase_client.py` — verificação de `_is_schema_error`
- Migration de índice (se identificado em AC4)

**OUT:**
- Refatoração completa do sistema de aggregation (scope excessivo)
- Materialized views (escopo de STORY-417 pattern, avaliar separadamente)
- Endpoints autenticados com menos carga — focar nos públicos primeiro

---

## Dependências

- STORY-416 (implementado): CB segregado. AC3 desta story pode precisar ajustar a lógica de exclusão de erros.

---

## Riscos

- **Degraded mode complexidade:** retornar dados parciais pode confundir usuários — use cache stale quando disponível, só retorne vazio se não houver cache
- **Índice em produção:** `CREATE INDEX CONCURRENTLY` é necessário em tabelas grandes para não bloquear writes

---

## Dev Notes

_(a preencher pelo @dev durante implementação)_

---

## Arquivos Impactados

- `backend/routes/municipios_publicos.py`
- `backend/datalake_query.py`
- `backend/supabase_client.py`
- `supabase/migrations/` (novo índice, se necessário)
- `backend/tests/test_story426_statement_timeout_guard.py` (novo)

---

## Definition of Done

- [ ] Zero novos eventos `57014` no Sentry por 24h após deploy
- [ ] Queries com timeout retornam 200 com dados degradados (não 500)
- [ ] CB `read_cb` abre corretamente após burst de erros `57014`

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — statement timeouts identificados em varredura Sentry pós-EPIC-INCIDENT-2026-04-10 |
| 2026-04-11 | @po (Sarah) | Validação `*validate-story-draft`. Score: 8/10. GO. Status: Draft → Ready. |
