# GTM-RESILIENCE-E02 — Dedup Sentry + Circuit Breaker Log Hygiene

| Campo | Valor |
|-------|-------|
| **Track** | E — "Log Cirurgico" |
| **Prioridade** | P0 |
| **Sprint** | 1 |
| **Estimativa** | 4-5 horas |
| **Gaps Endereçados** | L-05, L-06, L-07 |
| **Dependências** | Nenhuma (paralelizavel com E-01) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

O backend possui **dupla emissao de excecoes**: erros sao reportados simultaneamente via `logger.error(..., exc_info=True)` no stdout e via `sentry_sdk.capture_exception()` para o Sentry. Isso resulta em log lines duplicados e stack traces desnecessarios para erros esperados (timeout, 429, 422). Alem disso, o circuit breaker loga **cada falha individual** em nivel debug, e `exc_info=True` e usado indiscriminadamente para erros transientes.

**Impacto quantitativo:**

| Problema | Volume Estimado | Reducao |
|----------|-----------------|---------|
| Double exception (stdout + Sentry) | 5-10 logs/busca com erros | -5 por busca |
| Circuit breaker per-failure debug | 5-10 logs/serie de erros | -8 por serie |
| `exc_info=True` para erros esperados | Stack traces de 5-15 linhas cada | -5 logs efetivos |

**Locais de double-reporting identificados:**

| Arquivo | Linha | Padrao |
|---------|-------|--------|
| `search_pipeline.py` | L733 | `logger.error(...)` + `sentry_sdk.capture_exception(e)` |
| `search_pipeline.py` | L827 | `logger.error(..., exc_info=True)` + `sentry_sdk.capture_exception(e)` |
| `search_pipeline.py` | L961 | `logger.error(...)` + `sentry_sdk.capture_exception(e)` |
| `consolidation.py` | L490 | `logger.error(...)` + `sentry_sdk.capture_exception(e)` |
| `search_cache.py` | L245-246 | `logger.error(..., exc_info=True)` + `sentry_sdk.capture_exception(e, extras=...)` |
| `search_cache.py` | L317 | `logger.error(...)` + `sentry_sdk.capture_exception(e, extras=...)` |

**Locais de `exc_info=True` para erros esperados:**

| Arquivo | Linha | Erro | Esperado? |
|---------|-------|------|-----------|
| `consolidation.py` | L496 | PCP/ComprasGov timeout | Sim — transiente |
| `consolidation.py` | L508 | PCP diagnosis | Sim — transiente |
| `routes/search.py` | L206 | PNCP rate limit 429 | Sim — esperado |
| `routes/search.py` | L221 | PNCP API error | Depende do tipo |
| `search_cache.py` | L245 | Supabase cache save | Sim — non-fatal |
| `search_pipeline.py` | L824 | Multi-source timeout | Sim — transiente |
| `search_pipeline.py` | L1251 | LLM fallback | Sim — graceful |

**Circuit breaker logging — per-failure (L-05):**

Em `pncp_client.py` L140-143, o circuit breaker loga cada falha individual:

```python
async def record_failure(self) -> None:
    async with self._lock:
        self.consecutive_failures += 1
        logger.debug(
            f"Circuit breaker [{self.name}]: failure #{self.consecutive_failures} "
            f"(threshold={self.threshold})"
        )
```

E em L155-158, loga cada sucesso que reseta o counter:

```python
async def record_success(self) -> None:
    async with self._lock:
        if self.consecutive_failures > 0:
            logger.debug(
                f"Circuit breaker [{self.name}]: success after {self.consecutive_failures} "
                f"failures -- resetting counter"
            )
```

Com threshold=3, isso gera 3 debug logs antes do trip + 1 warning no trip. Se o LOG_LEVEL esta em DEBUG (comum em diagnostico), sao 4 logs por trip cycle. Para erros intermitentes com recovery, sao ate 10 logs por ciclo completo (3 failures + trip + recover + success + reset).

---

## Problema

### P1: Double Exception Reporting (L-06)

O mesmo erro aparece no Railway logs (stdout via `logger.error`) **e** no Sentry (via `capture_exception`). Sentry ja captura o traceback completo. O stdout deveria conter apenas um resumo de 1 linha, nao o traceback inteiro repetido.

Consequencia: cada erro consome 2x o espaco em logs, contribuindo para o estouro do rate limit Railway.

### P2: Circuit Breaker Loga Cada Falha (L-05)

O circuit breaker loga em nivel debug cada `record_failure()` e `record_success()`. Isso e ruido: o unico evento relevante e a **mudanca de estado** (trip e recovery), nao cada incremento do contador.

### P3: `exc_info=True` para Erros Transientes (L-07)

Stack traces completos sao gerados para erros que sao **esperados e tratados**: timeouts, rate limits (429), erros de cache non-fatal. Um stack trace de `httpx.TimeoutException` tem 15+ linhas mas zero valor diagnostico — o timeout e o comportamento esperado.

---

## Solucao

### S1: Regra de Emissao — Sentry XOR Stdout

Estabelecer regra clara:

| Tipo de Erro | Stdout (logger) | Sentry | `exc_info` |
|--------------|----------------|--------|------------|
| **Esperado/transiente** (timeout, 429, 422, cache fail) | `logger.warning(msg)` — 1 linha, sem traceback | `capture_exception` com tags | **Nao** |
| **Inesperado** (bug, schema error, null pointer) | `logger.error(msg, exc_info=True)` | `capture_exception` com tags | **Sim** |
| **Degradacao operacional** (all sources failed, LLM fallback) | `logger.warning(msg)` — 1 linha | `capture_message` com level=warning | **Nao** |

Implementar helper function:

```python
def report_error(
    error: Exception,
    message: str,
    *,
    expected: bool = False,
    tags: dict | None = None,
) -> None:
    """Centralized error reporting — avoids double emission."""
    if expected:
        logger.warning(f"{message}: {type(error).__name__}: {error}")
        sentry_sdk.capture_exception(error, tags=tags or {})
    else:
        logger.error(f"{message}: {error}", exc_info=True)
        sentry_sdk.capture_exception(error, tags=tags or {})
```

### S2: Circuit Breaker — Log Apenas Transicao de Estado

Remover logs de `record_failure()` e `record_success()`. Manter logs apenas em:

- **Trip**: `logger.warning(f"Circuit breaker [{name}] TRIPPED ...")` (ja existe, L146-148)
- **Recovery**: `logger.info(f"Circuit breaker [{name}] cooldown expired ...")` (ja existe, L179-181)

### S3: Sentry `ignore_errors` e `traces_filter`

Configurar Sentry para filtrar ruido:

```python
sentry_sdk.init(
    dsn=_sentry_dsn,
    ignore_errors=[
        httpx.TimeoutException,
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
    ],
    traces_sampler=_traces_sampler,
    # ... rest
)

def _traces_sampler(sampling_context):
    """Exclude health checks from traces."""
    path = sampling_context.get("asgi_scope", {}).get("path", "")
    if path in ("/health", "/v1/health", "/v1/health/cache"):
        return 0.0  # Never trace health checks
    return 0.1  # 10% for everything else
```

**Nota:** `ignore_errors` suprime excecoes inteiramente do Sentry. Para erros transientes que queremos rastrear em volume (mas nao como incidents), usar fingerprinting e rate limiting no Sentry em vez de `ignore_errors`:

```python
before_send=_before_send_filter,
```

```python
def _before_send_filter(event, hint):
    """Rate-limit transient errors in Sentry."""
    exc = hint.get("exc_info", (None, None, None))[1]
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectTimeout)):
        event["fingerprint"] = ["transient-timeout", str(type(exc).__name__)]
        event["level"] = "warning"
    return event
```

### S4: Conditional `exc_info`

Substituir todos os `exc_info=True` para erros esperados por `exc_info=False` (ou omitir o parametro). Lista de substituicoes:

| Arquivo | Linha | Acao |
|---------|-------|------|
| `consolidation.py` | L496 | Remover `exc_info=True` |
| `consolidation.py` | L508 | Remover `exc_info=True` |
| `routes/search.py` | L206 | Remover `exc_info=True` |
| `search_cache.py` | L245 | Remover `exc_info=True` |
| `search_pipeline.py` | L824 | Remover `exc_info=True` |
| `search_pipeline.py` | L1251 | Remover `exc_info=True` |

Manter `exc_info=True` nos locais de erros inesperados:

| Arquivo | Linha | Manter |
|---------|-------|--------|
| `cron_jobs.py` | L41 | Sim — erro de cleanup inesperado |
| `filter.py` | L2854 | Sim — FLUXO 2 failure inesperado |
| `pncp_client_resilient.py` | L238 | Sim — erro inesperado per-UF |
| `storage.py` | L120 | Sim — falha de upload inesperada |
| `routes/subscriptions.py` | L134, L144, L231, L234, L247 | Sim — erros Stripe/DB inesperados |
| `webhooks/stripe.py` | L146 | Sim — erro de webhook inesperado |

---

## Criterios de Aceite

### AC1: Sem Double-Reporting para Erros Esperados
- [ ] Nos 6 locais de double-reporting identificados, erros esperados (timeout, 429, cache fail) emitem `logger.warning` (1 linha, sem traceback) **e** `sentry_sdk.capture_exception` com tags, mas **nao** `logger.error(..., exc_info=True)` + `sentry_sdk.capture_exception`
- [ ] Helper function `report_error()` (ou equivalente) centraliza a decisao de emissao
- **Verificacao:** Simular timeout no PNCP via mock, verificar que stdout contem 1 linha warning (sem stack trace) e Sentry recebe o evento

### AC2: Circuit Breaker Loga Somente Transicao de Estado
- [ ] `record_failure()` em `pncp_client.py` L140-143 nao emite mais `logger.debug` por cada falha
- [ ] `record_success()` em `pncp_client.py` L155-158 nao emite mais `logger.debug` por cada sucesso
- [ ] Logs preservados: `logger.warning` no trip (L146-148) e `logger.info` na recovery (L179-181)
- **Verificacao:** Trigger 5 falhas consecutivas no circuit breaker via mock. Verificar que apenas 1 log WARNING (trip) aparece, nao 5 logs DEBUG de incremento

### AC3: `exc_info=True` Somente para Erros Inesperados
- [ ] `exc_info=True` removido de: `consolidation.py` L496, L508; `routes/search.py` L206; `search_cache.py` L245; `search_pipeline.py` L824, L1251
- [ ] `exc_info=True` mantido em: `cron_jobs.py` L41; `filter.py` L2854; `pncp_client_resilient.py` L238; `storage.py` L120; `routes/subscriptions.py` (todos); `webhooks/stripe.py` L146
- **Verificacao:** `grep -rn "exc_info=True" backend/ --include="*.py" | grep -v test | grep -v venv` retorna apenas os locais de erros inesperados

### AC4: Sentry Configurado com Fingerprinting para Transientes
- [ ] `before_send` ou `before_send_transaction` em `main.py` agrupa erros transientes com fingerprint customizado (evita flood de issues identicas no Sentry)
- [ ] `httpx.TimeoutException`, `httpx.ConnectTimeout`, `httpx.ReadTimeout` agrupados sob fingerprint `["transient-timeout"]`
- [ ] Nivel do evento rebaixado para `warning` (nao `error`) para excecoes transientes
- **Verificacao:** Inspecionar configuracao do `sentry_sdk.init()` em `main.py`

### AC5: Health Checks Excluidos de Traces
- [ ] `traces_sampler` (ou `traces_sample_rate` com filter) exclui paths `/health`, `/v1/health`, `/v1/health/cache` do sampling de traces
- [ ] Traces de health check nao consomem quota do Sentry
- **Verificacao:** Verificar `traces_sampler` callback na configuracao do Sentry

### AC6: Teste de Nao-Regressao do Circuit Breaker
- [ ] Testes existentes do circuit breaker (`test_timeout_chain.py` e testes em `test_pncp_client.py`) passam sem regressao
- [ ] Novo teste confirma que circuit breaker so emite log em trip e recovery (nao per-failure)
- **Verificacao:** `pytest -k "circuit" -v` verde

### AC7: Reducao Mensuravel de Volume
- [ ] Teste que simula cenario de erro (3 timeouts + circuit breaker trip + recovery) e conta logs nivel INFO+WARNING+ERROR
- [ ] O total de logs para o cenario de erro nao excede 5 linhas (1 warning por timeout final + 1 trip + 1 recovery + 1 sumario)
- [ ] Comparado com baseline anterior de ~20 linhas para o mesmo cenario
- **Verificacao:** Teste automatizado com contagem de log records

---

## Arquivos Afetados

| Arquivo | Mudanca |
|---------|---------|
| `backend/main.py` | Sentry `before_send` filter, `traces_sampler`, fingerprinting |
| `backend/pncp_client.py` | Remover logs debug de `record_failure()` e `record_success()` |
| `backend/search_pipeline.py` | Substituir double-reporting por `report_error()`, remover `exc_info=True` transientes |
| `backend/consolidation.py` | Remover `exc_info=True` L496, L508; usar `report_error()` |
| `backend/search_cache.py` | Remover `exc_info=True` L245; usar `report_error()` |
| `backend/routes/search.py` | Remover `exc_info=True` L206; manter Sentry |
| `backend/utils/error_reporting.py` | **NOVO** — helper `report_error()` centralizado |
| `backend/tests/test_error_reporting.py` | **NOVO** — testes da funcao `report_error()` |
| `backend/tests/test_circuit_breaker_logs.py` | **NOVO** — teste de volume de log do CB |

---

## Definition of Done

- [ ] Todos os 7 ACs verificados e marcados
- [ ] PR aprovado com lista de todos os locais alterados
- [ ] Helper `report_error()` com docstring e exemplos
- [ ] Testes existentes passam sem regressao (baseline backend ~47 fail mantido)
- [ ] Novos testes para `report_error()` e circuit breaker log volume
- [ ] `grep -rn "exc_info=True" backend/ --include="*.py" | grep -v test | grep -v venv` revisa lista final e confirma apenas erros inesperados
- [ ] MEMORY.md atualizado com regra de emissao (Sentry XOR stdout para transientes)
