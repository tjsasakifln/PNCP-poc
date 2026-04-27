# RES-BE-004: Observabilidade Datalake Hit/Miss/Error (Prometheus)

**Priority:** P1
**Effort:** S (1 dia)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 2 (2026-05-06 → 2026-05-12) — paralelizável com RES-BE-003
**Dependências bloqueadoras:** [RES-BE-001](RES-BE-001-audit-execute-without-budget.md) (linha temporal apenas; não funcional)

---

## Contexto

`backend/datalake_query.py` (L34, L61-79) é a camada de query para `pncp_raw_bids` (~1.5M rows) e `supplier_contracts` (~2M rows) — fonte primária de Layer 2 Search Pipeline (CLAUDE.md). O fallback de `query_datalake()` é **fail-open** (em caso de erro, retorna lista vazia e a busca cai para Layer 3 live API), mas hoje **não há observabilidade Prometheus** para distinguir os 3 cenários:

1. **Hit:** datalake retornou ≥1 result (caminho feliz)
2. **Miss:** datalake retornou 0 results (queda silenciosa para fallback live)
3. **Error:** datalake levantou exceção (e.g. timeout RPC, Supabase 5xx)

Sem essa instrumentação, regressões silenciosas — e.g. ingestion pipeline parou e datalake fica vazio — só são detectadas dias depois quando user reporta resultados ruins. O pivô SEO programático (memory `project_smartlic_onpage_pivot_2026_04_26`) depende de datalake confiável; observabilidade é foundational.

Esta story é P1 mas effort S — adiciona 3 counters + 1 histogram em ~2 callsites de `datalake_query.py`. Baixo risco, alto valor.

---

## Acceptance Criteria

### AC1: Métricas Prometheus

- [ ] Em `backend/metrics.py` (ou seu split RES-BE-006), adicionar:
  ```python
  DATALAKE_HIT_TOTAL = Counter(
      "smartlic_datalake_hit_total",
      "DataLake queries returning >=1 result",
      ["source"],  # source: "pncp_raw_bids" | "supplier_contracts"
  )
  DATALAKE_MISS_TOTAL = Counter(
      "smartlic_datalake_miss_total",
      "DataLake queries returning 0 results (fall-through to live)",
      ["source"],
  )
  DATALAKE_ERROR_TOTAL = Counter(
      "smartlic_datalake_error_total",
      "DataLake queries that raised exceptions",
      ["source", "reason"],  # reason: "timeout" | "supabase_5xx" | "rpc_error" | "other"
  )
  DATALAKE_LATENCY_SECONDS = Histogram(
      "smartlic_datalake_latency_seconds",
      "DataLake query duration",
      ["source"],
      buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
  )
  ```
- [ ] Counters acessíveis via `/metrics` endpoint Prometheus

### AC2: Instrumentação em `datalake_query.py`

- [ ] Em `backend/datalake_query.py` na função `query_datalake()` (e equivalentes para `supplier_contracts`):
  ```python
  start = time.perf_counter()
  source_label = "pncp_raw_bids"  # ou "supplier_contracts"
  try:
      result = await _execute_query(...)
      duration = time.perf_counter() - start
      DATALAKE_LATENCY_SECONDS.labels(source=source_label).observe(duration)
      if result and len(result) > 0:
          DATALAKE_HIT_TOTAL.labels(source=source_label).inc()
      else:
          DATALAKE_MISS_TOTAL.labels(source=source_label).inc()
      return result
  except asyncio.TimeoutError:
      DATALAKE_ERROR_TOTAL.labels(source=source_label, reason="timeout").inc()
      raise
  except SupabaseException as e:  # adapter
      DATALAKE_ERROR_TOTAL.labels(source=source_label, reason=_classify_error(e)).inc()
      raise
  except Exception as e:
      DATALAKE_ERROR_TOTAL.labels(source=source_label, reason="other").inc()
      logger.exception("datalake unexpected error")
      raise
  ```
- [ ] Helper `_classify_error()` mapeia exceções para labels: `"timeout"`, `"supabase_5xx"`, `"rpc_error"`, `"other"` (cap a cardinalidade do label `reason`)
- [ ] Apply em ambos callsites (L34 + L61-79); refatorar para função decorator se reduz duplicação

### AC3: Sentry alerting

- [ ] Sentry `capture_message(level="error")` apenas para `reason="other"` (sinal de bug; outros são esperados sob falha downstream)
- [ ] Fingerprint `["datalake_error", source, reason]` para dedup
- [ ] Sentry rule (manual via dashboard): alerta se `rate(smartlic_datalake_error_total[5m]) > 0.1` por 10 min

### AC4: Grafana panel mock

- [ ] Documento `docs/runbooks/datalake-observability.md`:
  - Query 1: `sum(rate(smartlic_datalake_hit_total[5m])) by (source)` — taxa de hit por source
  - Query 2: `sum(rate(smartlic_datalake_miss_total[5m])) by (source) / sum(rate(smartlic_datalake_hit_total[5m] + smartlic_datalake_miss_total[5m])) by (source)` — miss rate
  - Query 3: `sum(rate(smartlic_datalake_error_total[5m])) by (source, reason)` — erros por causa
  - Query 4: `histogram_quantile(0.95, rate(smartlic_datalake_latency_seconds_bucket[5m]))` — p95 latency
  - Alarmes: miss rate >50% por 10min → ingestion paralisado; p95 >2s → query lenta
- [ ] Se Grafana ainda não está em prod, documentar PromQL para uso futuro

### AC5: Testes

- [ ] **Unit tests:** `backend/tests/test_datalake_observability.py`
  - Hit case: query retorna 5 results → `DATALAKE_HIT_TOTAL{source="pncp_raw_bids"}` incrementa em 1
  - Miss case: query retorna [] → `DATALAKE_MISS_TOTAL` incrementa
  - Timeout case: `_execute_query` levanta `asyncio.TimeoutError` → `DATALAKE_ERROR_TOTAL{reason="timeout"}` incrementa
  - Supabase 5xx case: → `DATALAKE_ERROR_TOTAL{reason="supabase_5xx"}` incrementa
  - Latency observation registrada em ambos hit e miss (não em error)
  - Cobertura ≥85% nas linhas tocadas
- [ ] **Integration test:** simular query real com fixture `pncp_raw_bids` mock; validar metric output via `/metrics` HTTP endpoint
- [ ] Smoke test: deploy staging, hit `/buscar` 10x, confirmar counters incrementam em `/metrics`

---

## Scope

**IN:**
- 3 counters + 1 histogram em `backend/metrics.py`
- Instrumentação em `backend/datalake_query.py` (2 callsites)
- Sentry alerting para `reason="other"`
- Runbook + Grafana queries documentadas
- Testes unit + integration + smoke

**OUT:**
- Dashboard Grafana fisicamente publicado (depende de stack ops; documentar PromQL é suficiente para MVP)
- Métricas de ingestion pipeline (cron jobs) — escopo separado
- Tracing OpenTelemetry distribuído — escopo futuro
- Alerting PagerDuty/email — depende de stack ops

---

## Definition of Done

- [ ] 4 métricas (3 counters + 1 histogram) implementadas
- [ ] `datalake_query.py` instrumentado em ambos callsites
- [ ] Sentry capture funcional (validado em staging)
- [ ] Cobertura testes ≥85% nas linhas tocadas
- [ ] Sem regressão em testes existentes
- [ ] CodeRabbit clean (CRITICAL=0, HIGH=0)
- [ ] PR review por @architect (Aria) com verdict PASS
- [ ] Smoke test produção: counters visíveis em `/metrics` após 1h tráfego real
- [ ] Runbook `docs/runbooks/datalake-observability.md` criado
- [ ] CLAUDE.md seção "Critical Implementation Notes" referencia novas métricas

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/datalake_query.py` (L34, L61-79 — instrumentar)
- `/mnt/d/pncp-poc/backend/metrics.py` (adicionar 4 métricas)
- `/mnt/d/pncp-poc/backend/tests/test_datalake_observability.py` (novo)
- `/mnt/d/pncp-poc/docs/runbooks/datalake-observability.md` (novo)

### Padrões existentes

- `backend/metrics.py` já registra ~50 métricas Prometheus (`smartlic_*` prefix); seguir convenção
- `backend/redis_client.py` e `backend/datalake_query.py` já usam `time.perf_counter()` para latência em alguns callsites — manter consistência

### Mapeamento de erros

```python
def _classify_error(exc: Exception) -> str:
    if isinstance(exc, asyncio.TimeoutError):
        return "timeout"
    if hasattr(exc, "response") and getattr(exc.response, "status_code", 0) >= 500:
        return "supabase_5xx"
    if "rpc" in str(exc).lower() or "function" in str(exc).lower():
        return "rpc_error"
    return "other"
```

Cardinalidade do label `reason` cap em 4 valores (evita explosão Prometheus).

### Frameworks de teste

- pytest 8.x + pytest-asyncio
- File location: `backend/tests/test_datalake_observability.py`
- Marks: `@pytest.mark.timeout(10)`
- Fixtures: usar `prometheus_client.CollectorRegistry` isolado por teste (evitar leakage entre testes)
- Helper para assertion: `from prometheus_client import REGISTRY; sample = REGISTRY.get_sample_value("smartlic_datalake_hit_total", {"source": "pncp_raw_bids"})`

### Convenções

- Métricas seguem prefix `smartlic_` (CLAUDE.md)
- Buckets do histogram: 50ms..5s (cobre p50 esperado ~100ms, p99 esperado <500ms — outliers visíveis acima de 1s)
- Type hints obrigatórios

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| Cardinalidade Prometheus explode (label `reason` com >10 valores únicos) | Refator `_classify_error` para cap explícito; fallback para `"other"` em casos não-mapeados |
| Latência regredida >5% em `query_datalake` por overhead de instrumentação | Profile; remover histogram se gargalo (counters são cheaper) |
| Sentry flood por `reason="other"` | Aumentar fingerprint dedup; investigar bug raiz (provavelmente é sinal real) |
| `metrics.py` shim pós-RES-BE-006 quebra import | Coordenar release com RES-BE-006; importar via `from metrics import ...` (façade) |

**Rollback completo:** revert PR. Não há feature flag — observabilidade pura, baixo risco. Métricas inofensivas se ignoradas.

---

## Dependencies

**Entrada:**
- [RES-BE-001](RES-BE-001-audit-execute-without-budget.md) — linha temporal apenas
- `backend/datalake_query.py` (existente)
- `backend/metrics.py` (existente)

**Saída:** Nenhuma (story horizontal, não bloqueia outras).

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | Hit/Miss/Error explicitamente nomeados — 3 cenários distintos. |
| 2 | Complete description | ✓ | Explica fail-open silencioso atual e por que Layer 2 sem observabilidade é débito. |
| 3 | Testable acceptance criteria | ✓ | 5 ACs com pseudocódigo de instrumentação + 5 casos de teste unit. |
| 4 | Well-defined scope | ✓ | IN/OUT delimitados; OUT exclui Grafana físico, OTel distribuído, alerting PagerDuty. |
| 5 | Dependencies mapped | ✓ | Entrada RES-BE-001 (linha temporal); saída horizontal (não bloqueia outras). |
| 6 | Complexity estimate | ✓ | S (1 dia) coerente — 4 métricas + ~2 callsites + tests. |
| 7 | Business value | ✓ | "Pivô SEO programático depende de datalake confiável; observabilidade foundational." |
| 8 | Risks documented | ✓ | Cardinalidade explosion + latency regression cobertos; cap 4 valores em `reason`. |
| 9 | Criteria of Done | ✓ | 9 itens DoD incluindo smoke test produção 1h. |
| 10 | Alignment with PRD/Epic | ✓ | Story horizontal de observabilidade — habilita debug futuro do Layer 2 (CLAUDE.md §Data Architecture). |

### Required Fixes

Nenhuma.

### Observations

- Effort S apropriado — escopo cirúrgico, baixo risco.
- Cardinalidade cap (4 valores em `reason`) demonstra consciência de Prometheus best practices.
- Coordenação com RES-BE-006 (metrics split) flagged em Risk — sem bloqueio sequencial.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — observabilidade Layer 2 | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Story horizontal pequena, baixo risco, alto valor. Status: Draft → Ready. | @po (Pax) |
