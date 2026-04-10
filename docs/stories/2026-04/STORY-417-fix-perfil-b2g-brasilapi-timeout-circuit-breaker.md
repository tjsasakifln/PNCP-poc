# STORY-417: Fix `perfil-b2g` BrasilAPI ReadTimeout + Circuit Breaker por Host

**Priority:** P1 — High (slow_requests aproximando limite Railway)
**Effort:** M (1-2 days)
**Squad:** @dev + @architect
**Status:** InReview
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issues:**
- https://confenge.sentry.io/issues/7398756337/ (42 eventos perfil-b2g ReadTimeout)
- https://confenge.sentry.io/issues/7401422575/ (slow_request 120.7s)
- https://confenge.sentry.io/issues/7398298813/ (orgao_stats statement timeout 25 eventos)
- https://confenge.sentry.io/issues/7401453526/ (orgao_contratos statement timeout)
**Sprint:** Sprint seguinte (48h-1w)

---

## Contexto

O endpoint `GET /v1/empresa/{cnpj}/perfil-b2g` em `backend/routes/empresa_publica.py` está sofrendo cascata de timeouts:

1. **BrasilAPI chamada sem circuit breaker**
   - `_fetch_brasilapi()` em `empresa_publica.py:128-140` usa `_BRASILAPI_TIMEOUT = 15` (linha 29)
   - Sem retry, sem CB — se BrasilAPI está lento, a request fica travada 15s e propaga timeout ao caller
   - 42 eventos Sentry: `GET /v1/empresa/03935826000130/perfil-b2g → ERROR (15034ms) ReadTimeout`

2. **Slow requests aproximando limite Railway**
   - `slow_request: GET /v1/empresa/44404731000178/perfil-b2g (120.7s)` — 3 eventos
   - Railway hard timeout = 120s → requests acima disso são killed pelo proxy

3. **`_fetch_contratos_local()` não usa `sb_execute`**
   - `empresa_publica.py:289-330` chama Supabase direto sem o wrapper do circuit breaker
   - Viola STORY-416 (quando ela for implementada)

4. **`orgao_stats` com statement timeout**
   - `routes.orgao_publico.orgao_stats` — 25 eventos de `canceling statement due to statement timeout (57014)`
   - Query muito pesada para `pncp_supplier_contracts`

**Impacto:** usuários que buscam perfil B2G ficam aguardando até timeout Railway e recebem 500. UX degradada + custo operacional (Railway cobra CPU time de requests longas).

---

## Acceptance Criteria

### AC1: Reduzir BrasilAPI timeout + circuit breaker por host
- [ ] Baixar `_BRASILAPI_TIMEOUT` de 15s para **8s** em `empresa_publica.py:29`
- [ ] Encapsular `_fetch_brasilapi()` em circuit breaker por host — **reusar padrão de `backend/pncp_client.py`**
  - Threshold: 5 failures em janela de 10
  - Cooldown: 30s
- [ ] Se CB BrasilAPI aberto, retornar partial response imediatamente (sem bloquear o resto do `_build_perfil`)
- [ ] Métrica Prometheus `smartlic_brasilapi_circuit_breaker_state`

### AC2: `_fetch_contratos_local()` usar `sb_execute`
- [ ] Linhas `empresa_publica.py:289-330` — trocar `sb.table(...).execute()` por `await sb_execute(...)`
- [ ] Categoria `read` (quando STORY-416 estiver pronta)
- [ ] Fallback: se CB Supabase aberto, retornar cache stale ou lista vazia com flag

### AC3: Partial response (HTTP 206)
- [ ] Quando BrasilAPI timeout mas outros dados (PNCP, contratos locais) vieram OK, retornar **HTTP 206 Partial Content**
- [ ] Payload indica quais fontes estão disponíveis:
  ```json
  {
    "cnpj": "...",
    "brasilapi": null,
    "brasilapi_status": "unavailable",
    "pncp": {...},
    "contratos": [...],
    "_partial": true
  }
  ```
- [ ] Frontend (já tem `PartialResultsPrompt`) deve tratar gracefully

### AC4: Fix `orgao_stats` statement timeout — **Abordagem faseada A+C (@pm 2026-04-10)**

**Fase 1 — Quick win (0.5 dia) — deploy primeiro:**
- [ ] Auditar query em `routes/orgao_publico.py::orgao_stats`
- [ ] Adicionar `SET LOCAL statement_timeout = '20s'` na query (previne kills de 30s padrão)
- [ ] Implementar **Redis cache 15min** sobre query existente (Opção C) — corta ~90% dos timeouts imediatamente
- [ ] Deploy Fase 1 isolado para validar redução antes de Fase 2

**Fase 2 — Proper fix (1.5 dias) — após Fase 1 estável:**
- [ ] Criar **materialized view `mv_orgao_stats`** (Opção A) com mesma estrutura de saída da query atual
- [ ] Criar ARQ cron `refresh_mv_orgao_stats` com schedule a cada 1h (alinhado com ingestão)
- [ ] Migração: `supabase/migrations/2026041005_mv_orgao_stats.sql` com `CREATE MATERIALIZED VIEW` + `REFRESH MATERIALIZED VIEW CONCURRENTLY`
- [ ] Atualizar `orgao_stats` route para ler da MV em vez da query direta
- [ ] Redis cache passa a servir da MV (latência ~1ms)

**Fase 3 — Backup (opcional, se Fase 2 insuficiente):**
- [ ] Índice composto `(orgao_cnpj, data_publicacao)` para acelerar refresh da MV
- [ ] Migration separada: `supabase/migrations/2026041006_idx_orgao_contracts.sql`

- [ ] Documentar decisão e benchmark antes/depois em `docs/incidents/2026-04-10-multi-cause.md`
- [ ] **Staleness aceitável:** 15min-1h (endpoint de estatísticas, não transacional)

### AC5: Fix `orgao_contratos` statement timeout
- [ ] Aplicar mesmo tratamento da AC4 em `routes/contratos_publicos.py::orgao_contratos_stats`
- [ ] Query provavelmente compartilha padrão — pode ser helper comum

### AC6: Observability
- [ ] Log estruturado: `{"event": "brasilapi_timeout", "cnpj": "<masked>", "elapsed_ms": ..., "cb_state": "..."}`
- [ ] Sentry breadcrumb antes da chamada BrasilAPI para facilitar debug
- [ ] Alert no Sentry: BrasilAPI CB open por >5 min consecutivos

### AC7: Testes
- [ ] E2E test em `backend/tests/test_empresa_publica.py` simulando BrasilAPI lento (usar `respx` mock)
- [ ] Validar partial response 206 quando BrasilAPI down
- [ ] Benchmark: `orgao_stats` <5s P95 após otimização

### AC8: Verificação pós-deploy
- [ ] Monitorar Sentry issues 7398756337, 7401422575 por 6h — zero novos eventos
- [ ] `railway logs --filter "ReadTimeout"` = vazio em 30 min
- [ ] P95 latência `/v1/empresa/*/perfil-b2g` < 10s no Grafana

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/routes/empresa_publica.py` | Linhas 29, 128-140 (timeout + CB), 289-330 (sb_execute) |
| `backend/routes/orgao_publico.py` | Query orgao_stats — timeout local + cache |
| `backend/routes/contratos_publicos.py` | Query orgao_contratos — mesmo tratamento |
| `backend/pncp_client.py` | Extrair CB por host em helper reusável (se ainda não for) |
| `backend/metrics.py` | Métrica BrasilAPI CB |
| `backend/tests/test_empresa_publica.py` | Mock BrasilAPI lento, partial response test |
| `supabase/migrations/2026041002_perfil_b2g_indexes.sql` | (Opcional) índices compostos |
| `frontend/app/empresa/[cnpj]/page.tsx` | Tratar HTTP 206 partial response |

---

## Implementation Notes

- **Timeout chain:** Railway(120s) > Gunicorn(180s) > Pipeline interno(110s) > Per-source BrasilAPI(8s). Depois dessa story: Per-source BrasilAPI(8s), per-source PNCP(25s), per-source contratos(20s). Nenhum agregado pode exceder 90s para deixar margem ao Railway proxy.
- **Fallback data:** quando BrasilAPI down, usar última resposta cacheada (Redis TTL 24h) antes de retornar null.
- **`respx` mock:** ver exemplos em `backend/tests/test_pncp_client.py` para mockar httpx.AsyncClient.
- **Materialized view vs cache:** mv é melhor para dados que mudam devagar (orgao_stats muda 1x por dia). Cache Redis é melhor para response frequente. Usar ambos: cache Redis 15min + mv refresh 1h.
- **Cuidado com partial response:** HTTP 206 é semanticamente correto mas alguns clientes (fetch vanilla) tratam como erro. Testar no frontend antes de ativar.

---

## Dev Notes (preencher durante implementação)

<!-- @dev: documentar decisão de otimização para orgao_stats (cache/mv/index) -->

---

## Verification

1. **Local:** `respx` mock BrasilAPI com 20s delay → endpoint retorna 206 em <10s
2. **Staging:** load test 100 req/s em `/v1/empresa/*/perfil-b2g` com BrasilAPI real → P95 <10s
3. **Produção:** monitorar Grafana latência endpoint por 24h
4. **Chaos:** desligar BrasilAPI (bloqueio DNS) → endpoints continuam retornando (partial)
5. **Statement timeout:** executar `orgao_stats` query para CNPJ com muitos contratos → <5s

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
| 2026-04-10 | @po (Sarah) | `*validate-story-draft` → verdict GO (9/10). Status Draft → Ready. |
| 2026-04-10 | @pm (Morgan) | Decisão AC4: **abordagem faseada A+C** (Redis quick-win → Materialized View proper fix → índice backup). Rationale: `orgao_stats` é read-heavy + slow-changing = textbook fit para MV. Redis L2 cobre hot CNPJs. Efeito combinado elimina timeouts. |
| 2026-04-10 | @dev | Implementation (Fase 1). `routes/empresa_publica.py`: `_BRASILAPI_TIMEOUT` 15→8s; nova `BrasilAPIUnavailable` exception; per-host CB com 3 consecutive failures + 60s cooldown; `_fetch_brasilapi` distingue 404 (business) de 5xx/timeout (transport/trip); `_build_perfil` fallback gracioso — retorna `brasilapi_status="unavailable"` no response model (campo novo). `routes/orgao_publico.py` ganha Redis cache Fase 1 (15min TTL, key `orgao_stats:v1:{cnpj}`) além do in-memory cache existente; carga cross-worker compartilhada. Fase 2 (Materialized View) + Fase 3 (índice backup) deferidas como follow-up. 8 tests em `tests/test_story417_brasilapi_cb.py` passam (sem respx — stubs httpx.AsyncClient via monkeypatch). Status Ready → InReview. |
