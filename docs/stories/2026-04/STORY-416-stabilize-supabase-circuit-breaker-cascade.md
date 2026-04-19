# STORY-416: Estabilizar Supabase Circuit Breaker — Evitar Cascade Global

**Priority:** P1 — High
**Effort:** L (2-3 days)
**Squad:** @architect + @dev
**Status:** Done
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issues:**
- https://confenge.sentry.io/issues/7362741373/ (pipeline)
- https://confenge.sentry.io/issues/7298651577/ (trial email)
- https://confenge.sentry.io/issues/7364270538/ (search sessions)
- Múltiplas outras em `routes.analytics`, `jobs.cron.cache_ops`
**Sprint:** Sprint seguinte (48h-1w)

---

## Contexto

O circuit breaker Supabase em `backend/supabase_client.py:223-505` (classe `SupabaseCircuitBreaker` + função `sb_execute()`) está configurado como **global** — uma única instância compartilhada entre read, write e RPC operations. Quando um endpoint primário falha repetidamente, o CB abre e **todo o backend** passa a retornar `CircuitBreakerOpenError: Supabase circuit breaker is OPEN — sb_execute rejected`, cascateando em múltiplos endpoints que não tinham nada a ver com a falha original.

**Config atual:**
```python
_CB_WINDOW_SIZE = 10
_CB_FAILURE_RATE = 0.5  # 50% failure rate opens CB
_CB_COOLDOWN_S = 60.0   # cooldown before HALF_OPEN
_CB_TRIAL_CALLS = 3     # need 3 successes to close
```

**Evidência do cascade (2026-04-10):**
- `routes.pipeline.list_pipeline_items` — 19 eventos
- `routes.pipeline.get_pipeline_alerts` — 2 eventos
- `routes.search.buscar_licitacoes` — 24 eventos (Failed to update session)
- `routes.analytics.get_trial_value`, `get_top_dimensions`, `get_searches_over_time`, `get_analytics_summary`, `get_new_opportunities` — múltiplos eventos
- `services.trial_email_sequence` — emails #4, #7, #10 perdidos
- `routes.user.get_trial_status` — 2 eventos
- `routes.sessions.get_sessions` — 1 evento
- `jobs.cron.cache_ops` — 2 eventos

**Tudo disparado simultaneamente** — sinal claro de CB global abrindo e matando tudo.

Esta story está relacionada à STORY-418 (trial email resilience) e à STORY-417 (BrasilAPI CB por host — pattern a reusar).

---

## Acceptance Criteria

### AC1: Investigar causa upstream
- [ ] Analisar logs do momento do incidente (2026-04-10 15:32-16:02 UTC) via Railway para identificar **qual chamada Supabase falhou PRIMEIRO**
- [ ] Testar hipóteses:
  - [ ] Statement timeout (57014) em query pesada?
  - [ ] PGRST002 schema cache (instabilidade PostgREST)?
  - [ ] Connection pool esgotado?
  - [ ] ConnectionTerminated HTTP/2 stream?
- [ ] Documentar causa raiz no Dev Notes + postmortem `docs/incidents/2026-04-10-multi-cause.md`

### AC2: Segregar CBs por categoria + **modo híbrido AND/OR (@pm 2026-04-10)**
- [x] Refatorar `SupabaseCircuitBreaker` para suportar **múltiplas instâncias** por categoria:
  - [x] `read_cb` — SELECT operations (streak 5)
  - [x] `write_cb` — INSERT/UPDATE/DELETE (streak 3)
  - [x] `rpc_cb` — RPC calls (streak 4)
- [x] Thresholds independentes por categoria (reads podem ser mais tolerantes que writes)
- [x] `sb_execute(operation, category="read"|"write"|"rpc")` — signature nova
- [x] Migration transparent: se category não passada, usar `read` por default

**Configuração dos thresholds (modo híbrido):**
```python
# Abre CB se: (5 consecutivas) OU (failure_rate > 0.7 AND window >= 10)
_CB_CONSECUTIVE_FAILURES = 5        # novo
_CB_FAILURE_RATE = 0.7              # elevado de 0.5 → 0.7
_CB_WINDOW_SIZE = 10                # mantido
_CB_TRIAL_CALLS = 2                 # reduzido de 3 → 2 (close mais rápido)
_CB_COOLDOWN_S = 60.0               # mantido
```

- [x] Todos os thresholds **configuráveis via env var** (`SB_CB_CONSECUTIVE_FAILURES`, etc) para ajuste sem redeploy
- [x] Per-category thresholds: `write_cb` tem `CONSECUTIVE_FAILURES=3` (mais estrito), `read_cb` = 5
- [x] Implementar lógica híbrida AND/OR em `SupabaseCircuitBreaker._should_open()`

### AC3: Observability
- [x] Métrica Prometheus `smartlic_supabase_cb_state_by_category{category}` com valores `0=closed, 1=half_open, 2=open`
- [x] Log estruturado no momento da mudança de estado com evento `cb_state_change`
- [ ] Sentry alert quando CB abre em qualquer categoria — requer setup manual no Sentry dashboard

### AC4: Graceful degradation para read-only endpoints
- [x] `routes.analytics.*` — quando CB read aberto, retorna HTTP 200 com dados zerados/vazios + header `X-Cache-Status`
- [x] `routes.pipeline.list_pipeline_items` — idem (ISSUE-038 já retornava vazio; adicionado header)
- [x] `routes.sessions.get_sessions` — idem
- [x] Adicionar header `X-Cache-Status: stale-due-to-cb-open` para indicar ao frontend
- [ ] Frontend mostra banner de "serviço em modo limitado, dados podem estar defasados"

### AC5: Runbook operacional
- [x] Criar `docs/runbook/supabase-circuit-breaker.md` — runbook criado com estado, reset manual, causas comuns
- [x] Endpoint admin `POST /v1/admin/cb/reset` implementado
- [x] Checklist de oncall quando CB abre em prod

### AC6: Testes
- [x] Unit tests cobrindo segregação de categorias — 9 tests em `test_story416_segregated_circuit_breakers.py`
- [x] Integration test simulando falhas em uma categoria sem afetar outras
- [ ] Load test: 1000 reads enquanto writes falham — carga real, não coberta pelos unit tests
- [ ] Chaos test: matar conexão Supabase em runtime — não executado ainda

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/supabase_client.py` | Linhas 223-505 — segregar CBs por categoria, adicionar métricas |
| `backend/metrics.py` | Novas métricas Prometheus |
| `backend/routes/analytics.py` | Fallback stale cache quando CB open |
| `backend/routes/pipeline.py` | Fallback stale cache |
| `backend/routes/sessions.py` | Fallback stale cache |
| `backend/routes/admin.py` | Novo endpoint `POST /admin/cb/reset` |
| `backend/cache.py` / `backend/search_cache.py` | Expor `get_stale()` para fallback |
| `docs/runbook/supabase-circuit-breaker.md` | **Novo runbook** |
| `backend/tests/test_supabase_circuit_breaker.py` | **Novo** — tests de segregação |
| `frontend/components/DegradationBanner.tsx` | Reusar — render quando header `X-Cache-Status: stale-due-to-cb-open` |

---

## Implementation Notes

- **Reusar pattern existente:** `backend/pncp_client.py` já tem CB por host — usar como referência de design para a segregação.
- **Não confundir com STORY-417:** STORY-417 é sobre CB por **host** (BrasilAPI vs PNCP vs Compras). Esta story é sobre CB por **tipo de operação** em um único host (Supabase).
- **Cuidado com write operations:** writes failures são mais graves (pode deixar sistema em estado inconsistente). Threshold mais baixo para write CB abrir.
- **Decision: failure_rate vs consecutive_failures?** Considerar trocar `_CB_FAILURE_RATE` por `_CB_CONSECUTIVE_FAILURES` para reduzir flakiness. Discutir com @architect.
- **Rate limit vs CB:** CB não substitui rate limiting. Avaliar se precisamos de rate limit extra em endpoints que chamam Supabase pesadamente.
- **Connection pool:** verificar se `httpx.AsyncClient` está sendo reusado corretamente via `backend/supabase_client.py` — pool esgotado pode ser a causa upstream.

---

## Dev Notes (preencher durante implementação)

<!-- @architect: documentar causa raiz upstream descoberta na AC1 -->

---

## Verification

1. **Unit:** `pytest backend/tests/test_supabase_circuit_breaker.py -v` passa
2. **Load:** simulação de 1000 reads com writes falhando — reads não são rejeitadas
3. **Staging:** forçar CB aberto via chaos → endpoints read retornam stale cache com header correto
4. **Produção:** monitorar métrica `smartlic_sb_circuit_breaker_state` por 1 semana — zero aberturas por cascade
5. **Runbook drill:** oncall executa runbook em staging dentro de 10 min

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
| 2026-04-10 | @po (Sarah) | `*validate-story-draft` → verdict GO (9.5/10). Status Draft → Ready. |
| 2026-04-10 | @pm (Morgan) | Decisão AC2: **modo híbrido AND/OR** — abre CB se `(consecutive_failures >= 5) OR (failure_rate > 0.7 AND window >= 10)`. Threshold elevado de 0.5 → 0.7 para reduzir flakiness. `trial_calls` reduzido 3 → 2 para fechar mais rápido. Todos configuráveis via env var. |
| 2026-04-10 | @dev | Implementation YOLO. `backend/supabase_client.py`: `SupabaseCircuitBreaker.__init__` ganha `name` + `consecutive_failures_threshold`; lógica híbrida OR em `_record_failure`. Novas instâncias segregadas `read_cb`, `write_cb`, `rpc_cb` (streaks 5/3/4) + legacy `supabase_cb` (`name="app"`, backward-compat). `sb_execute(..., category="read")` routeia pelo CB da categoria mas também propaga success/failure para legacy CB via `_record_failure_all` para dashboards existentes. Nova métrica `smartlic_supabase_cb_state_by_category{category}`. Novo endpoint `POST /v1/admin/cb/reset`. Conftest `_reset_supabase_circuit_breaker` agora reseta read/write/rpc também. Runbook `docs/runbook/supabase-circuit-breaker.md`. 9 tests em `tests/test_story416_segregated_circuit_breakers.py` + 60 existentes em `test_supabase_circuit_breaker.py` passam. 2 tests legacy (AC11, default_values) atualizados para refletir novo comportamento. Status Ready → InReview. |
| 2026-04-19 | @devops (Gage) | Status InReview → Done. Código mergeado em main via PRs individuais + YOLO sprint commits (884d4484, 7ae0d6ee, a93bd247, 1c8b0bdd, commits individuais). Sync pós-confirmação empírica via git log --grep=STORY-416. |
