# GTM-RESILIENCE-E03 — Metrics Exporter (Prometheus/StatsD)

| Campo | Valor |
|-------|-------|
| **Track** | E — "Log Cirurgico" |
| **Prioridade** | P0 |
| **Sprint** | 2 |
| **Estimativa** | 6-8 horas |
| **Gaps Endereçados** | Observabilidade ausente (investigacao FRENTE 5) |
| **Dependências** | E-01 (log consolidation cria os aggregation points onde metricas serao emitidas) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

O sistema SmartLic calcula internamente diversas metricas de performance e qualidade — latencia de busca, taxa de acerto de cache, taxa de erro por fonte, ratios de filtro — mas **nenhuma e exportada como metrica estruturada**. Todos os dados sao apenas logados como texto, impossibilitando:

- Dashboards de operacao em tempo real
- Alertas automaticos (p95 > 30s, error rate > 10%)
- Trending historico de performance
- Deteccao de anomalias na qualidade de classificacao

**Metricas atualmente calculadas mas nao exportadas:**

| Metrica | Onde e Calculada | Arquivo | Como e Usada |
|---------|-----------------|---------|--------------|
| Duracao do pipeline | `elapsed` em `_run_pipeline()` | `search_pipeline.py` | Logado como texto |
| Duracao do fetch | `fetch_elapsed` em `stage_execute` | `search_pipeline.py` L555 | Logado como texto |
| Items fetched por UF | Acumulado em `fetch_all()` | `pncp_client.py` | Logado como texto |
| Filter pass/reject counts | `filter_stats` dict | `search_pipeline.py` L1093+ | Logado como 9 linhas (sera 1 JSON apos E-01) |
| Cache hit/miss | Branching em `stage_execute` | `search_pipeline.py` L503 | Logado como texto |
| LLM calls count | `classify_contract_primary_match()` | `filter.py` | Nao rastreado |
| LLM duration | Nao medido | `filter.py` / `llm_arbiter.py` | Nao existe |
| Error rate por fonte | `SourceResult.error` | `consolidation.py` | Sentry tags apenas |
| Circuit breaker state | `is_degraded` | `pncp_client.py` | Health endpoint apenas |
| Cache age (staleness) | `fetched_at` em cache | `search_cache.py` | Banner no frontend |

**Infraestrutura atual:** Railway nao possui Prometheus nativo, mas suporta exportacao via HTTP endpoint que pode ser scrapeado por servicos externos (Grafana Cloud Free Tier, por exemplo). Alternativa: push-based via StatsD para Datadog/Grafana.

---

## Problema

Sem metricas exportadas, a equipe opera "as cegas" em relacao a:

1. **Performance baseline** — Nao existe p50/p95/p99 de latencia historico. Impossivel saber se uma busca de 45s e normal ou degradada.
2. **Cache effectiveness** — Nao sabemos o hit rate real. Pode ser 5% ou 80%. Sem dados, nao e possivel justificar investimento em Redis (Track B).
3. **Error trending** — Erros aparecem no Sentry como incidents isolados. Nao existe visualizacao de "error rate subiu de 2% para 15% nas ultimas 2h".
4. **Filter quality** — O ratio pass/reject nao e rastreado historicamente. Uma mudanca de keywords que aumente rejeicao de 40% para 90% nao seria detectada.
5. **LLM cost/accuracy** — Nao sabemos quantas chamadas LLM sao feitas por busca, nem a taxa de SIM vs NAO.

---

## Solucao

### S1: Biblioteca `prometheus_client` (Pull-Based)

Adicionar `prometheus_client` ao `requirements.txt` e expor endpoint `/metrics` no FastAPI. Esta e a abordagem mais simples e compativel com o ecossistema:

```python
# metrics.py
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    make_asgi_app,
)

# === Histogramas (latencia) ===
SEARCH_DURATION = Histogram(
    "smartlic_search_duration_seconds",
    "Total search pipeline duration",
    ["sector", "uf_count", "cache_status"],
    buckets=[1, 2, 5, 10, 20, 30, 60, 120, 300],
)

FETCH_DURATION = Histogram(
    "smartlic_fetch_duration_seconds",
    "Data source fetch duration",
    ["source"],  # pncp, pcp, compras_gov
    buckets=[1, 2, 5, 10, 20, 30, 60, 120],
)

LLM_DURATION = Histogram(
    "smartlic_llm_call_duration_seconds",
    "LLM arbiter call duration",
    ["model", "decision"],  # gpt-4.1-nano, SIM/NAO
    buckets=[0.1, 0.25, 0.5, 1, 2, 5],
)

# === Contadores ===
CACHE_HITS = Counter(
    "smartlic_cache_hits_total",
    "Cache hit count",
    ["level", "freshness"],  # supabase/memory/file, fresh/stale
)

CACHE_MISSES = Counter(
    "smartlic_cache_misses_total",
    "Cache miss count",
    ["level"],
)

API_ERRORS = Counter(
    "smartlic_api_errors_total",
    "API error count by source and type",
    ["source", "error_type"],  # pncp/pcp, timeout/429/422/500
)

FILTER_DECISIONS = Counter(
    "smartlic_filter_decisions_total",
    "Filter pass/reject decisions",
    ["stage", "decision"],  # uf/status/keyword/llm, pass/reject
)

LLM_CALLS = Counter(
    "smartlic_llm_calls_total",
    "LLM arbiter invocations",
    ["model", "decision", "zone"],  # gpt-4.1-nano, SIM/NAO, standard/conservative/zero_match
)

SEARCHES = Counter(
    "smartlic_searches_total",
    "Total searches executed",
    ["sector", "result_status"],  # facilities/uniformes, success/partial/empty/error
)

# === Gauges ===
CIRCUIT_BREAKER_STATE = Gauge(
    "smartlic_circuit_breaker_degraded",
    "Circuit breaker degraded state (1=degraded, 0=healthy)",
    ["source"],
)

ACTIVE_SEARCHES = Gauge(
    "smartlic_active_searches",
    "Number of currently running search pipelines",
)
```

### S2: Instrumentacao nos Pontos-Chave

Adicionar emissao de metricas nos locais onde os dados ja sao calculados:

| Metrica | Onde Instrumentar | Impacto no Hot Path |
|---------|-------------------|---------------------|
| `SEARCH_DURATION.observe()` | `_run_pipeline()` final | ~0.01ms (negligivel) |
| `FETCH_DURATION.observe()` | `stage_execute` apos fetch | ~0.01ms |
| `CACHE_HITS.inc()` | `stage_execute` no cache hit branch | ~0.01ms |
| `CACHE_MISSES.inc()` | `stage_execute` no cache miss branch | ~0.01ms |
| `API_ERRORS.inc()` | `record_failure()` no CB e handlers de erro | ~0.01ms |
| `FILTER_DECISIONS.inc()` | Cada filtro em `filter.py` no return | ~0.01ms por filtro |
| `LLM_CALLS.inc()` | `classify_contract_primary_match()` | ~0.01ms |
| `LLM_DURATION.observe()` | Wrapper ao redor da chamada OpenAI | ~0.01ms |
| `CIRCUIT_BREAKER_STATE.set()` | `record_failure()` e `try_recover()` | ~0.01ms |
| `ACTIVE_SEARCHES.inc/dec()` | Entry/exit de `_run_pipeline()` | ~0.01ms |

**Overhead total estimado:** <0.5ms por busca (insignificante vs pipeline de 10-60s).

### S3: Endpoint `/metrics`

Montar o endpoint Prometheus como sub-aplicacao ASGI no FastAPI:

```python
# main.py
from prometheus_client import make_asgi_app

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

Proteger com autenticacao basica ou IP allowlist para nao expor metricas publicamente:

```python
@app.middleware("http")
async def metrics_auth(request: Request, call_next):
    if request.url.path == "/metrics":
        token = request.headers.get("Authorization")
        expected = f"Bearer {os.getenv('METRICS_TOKEN', '')}"
        if not token or token != expected:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)
```

### S4: Grafana Cloud Free Tier (Opcional — Documentar Setup)

Documentar como conectar o `/metrics` ao Grafana Cloud Free Tier (10K metricas, 14 dias retencao):

1. Criar conta Grafana Cloud
2. Configurar Prometheus remote write ou Grafana Agent
3. Apontar scrape target para `https://bidiq-backend-production.up.railway.app/metrics`
4. Importar dashboard pre-configurado

---

## Criterios de Aceite

### AC1: Endpoint `/metrics` Funcional
- [ ] `GET /metrics` retorna output em formato Prometheus text exposition (`text/plain; version=0.0.4`)
- [ ] Endpoint protegido por Bearer token (`METRICS_TOKEN` env var)
- [ ] Requests sem token recebem HTTP 401
- [ ] Health checks (`/health`) nao sao afetados pela protecao
- **Verificacao:** `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/metrics` retorna metricas validas

### AC2: Latencia de Busca como Histograma
- [ ] `smartlic_search_duration_seconds` registra duracao total do pipeline em segundos
- [ ] Labels incluem `sector`, `uf_count`, `cache_status` (fresh/stale/miss)
- [ ] Buckets configurados para range relevante: 1s, 2s, 5s, 10s, 20s, 30s, 60s, 120s, 300s
- [ ] p50, p95, p99 calculaveis a partir dos buckets
- **Verificacao:** Executar 3 buscas via mock, verificar que `/metrics` mostra `_bucket`, `_sum`, `_count` com valores corretos

### AC3: Cache Hit/Miss Rate
- [ ] `smartlic_cache_hits_total` incrementado em cada cache hit com labels `level` (supabase/memory) e `freshness` (fresh/stale)
- [ ] `smartlic_cache_misses_total` incrementado em cada cache miss com label `level`
- [ ] Hit rate calculavel como `hits / (hits + misses)`
- **Verificacao:** Executar busca com cache hit e cache miss, verificar contadores no `/metrics`

### AC4: Error Rate por Fonte
- [ ] `smartlic_api_errors_total` incrementado por cada erro de API com labels `source` (pncp/pcp/compras_gov) e `error_type` (timeout/429/422/500/connection)
- [ ] Counter nao incrementado para erros de cache ou LLM (metricas separadas)
- **Verificacao:** Simular timeout do PNCP via mock, verificar que counter `source=pncp, error_type=timeout` incrementa

### AC5: Filter Pass/Reject Ratios
- [ ] `smartlic_filter_decisions_total` incrementado por cada decisao de filtro com labels `stage` (uf/status/valor/keyword/llm/zero_match) e `decision` (pass/reject)
- [ ] Ratio pass/reject calculavel por stage
- **Verificacao:** Executar busca com bids que passam e falham em diferentes estagios, verificar contadores

### AC6: LLM Calls Rastreadas
- [ ] `smartlic_llm_calls_total` incrementado por cada invocacao do LLM arbiter com labels `model`, `decision` (SIM/NAO/ERROR), `zone` (standard/conservative/zero_match)
- [ ] `smartlic_llm_call_duration_seconds` registra latencia de cada chamada LLM
- [ ] Taxa SIM/NAO calculavel para medir "yield" do LLM
- **Verificacao:** Executar busca com bids que trigam LLM arbiter, verificar contadores e histograma

### AC7: Circuit Breaker State Exportado
- [ ] `smartlic_circuit_breaker_degraded` gauge com label `source` (pncp/pcp) indica 1 quando degradado, 0 quando saudavel
- [ ] Gauge atualizado em `record_failure()` (quando trip) e `try_recover()` (quando recovery)
- **Verificacao:** Trigger circuit breaker trip via mock, verificar gauge=1; trigger recovery, verificar gauge=0

### AC8: Zero Impacto no Hot Path
- [ ] Benchmark mostrando overhead < 1ms por busca completa
- [ ] Nenhuma chamada de rede (push) no hot path — metricas sao in-memory, servidas sob demanda via `/metrics`
- [ ] Se `prometheus_client` nao esta instalado ou `/metrics` esta desabilitado, o sistema funciona normalmente sem erro
- **Verificacao:** Rodar `pytest --benchmark` (ou comparar duracao de busca com/sem metricas) e verificar diferenca < 1ms

### AC9: Testes de Instrumentacao
- [ ] Testes unitarios para cada metrica: verificar que o counter/histogram/gauge correto e atualizado com os labels corretos
- [ ] Teste de integracao: executar pipeline completo via mock e verificar que `/metrics` contem todas as 5+ metricas com valores > 0
- [ ] Testes isolados (cada teste reseta o registry para evitar contaminacao)
- **Verificacao:** `pytest test_metrics.py -v` verde

### AC10: Documentacao de Setup Externo
- [ ] README ou doc em `docs/guides/` explicando como conectar Grafana Cloud ao endpoint `/metrics`
- [ ] Env vars documentadas: `METRICS_TOKEN`, `METRICS_ENABLED` (default true)
- [ ] Exemplo de dashboard Grafana com queries para p95, cache hit rate, error rate
- **Verificacao:** Documento existe e contem instrucoes reproduziveis

---

## Arquivos Afetados

| Arquivo | Mudanca |
|---------|---------|
| `backend/metrics.py` | **NOVO** — definicao de todas as metricas Prometheus |
| `backend/main.py` | Mount `/metrics` endpoint, middleware de auth, import metrics |
| `backend/search_pipeline.py` | Instrumentar `SEARCH_DURATION`, `FETCH_DURATION`, `CACHE_HITS/MISSES`, `ACTIVE_SEARCHES`, `SEARCHES` |
| `backend/pncp_client.py` | Instrumentar `API_ERRORS`, `CIRCUIT_BREAKER_STATE` |
| `backend/filter.py` | Instrumentar `FILTER_DECISIONS`, `LLM_CALLS`, `LLM_DURATION` |
| `backend/consolidation.py` | Instrumentar `FETCH_DURATION` por fonte, `API_ERRORS` |
| `backend/search_cache.py` | Instrumentar `CACHE_HITS`, `CACHE_MISSES` |
| `backend/requirements.txt` | Adicionar `prometheus_client>=0.20.0` |
| `backend/config.py` | Adicionar `METRICS_ENABLED`, `METRICS_TOKEN` |
| `backend/tests/test_metrics.py` | **NOVO** — testes de todas as metricas |
| `docs/guides/metrics-setup.md` | **NOVO** — guia de conexao com Grafana Cloud |

---

## Metricas — Resumo Quick Reference

| Nome | Tipo | Labels | Descricao |
|------|------|--------|-----------|
| `smartlic_search_duration_seconds` | Histogram | sector, uf_count, cache_status | Duracao total do pipeline |
| `smartlic_fetch_duration_seconds` | Histogram | source | Duracao do fetch por fonte |
| `smartlic_llm_call_duration_seconds` | Histogram | model, decision | Latencia de chamada LLM |
| `smartlic_cache_hits_total` | Counter | level, freshness | Cache hits |
| `smartlic_cache_misses_total` | Counter | level | Cache misses |
| `smartlic_api_errors_total` | Counter | source, error_type | Erros de API |
| `smartlic_filter_decisions_total` | Counter | stage, decision | Decisoes de filtro |
| `smartlic_llm_calls_total` | Counter | model, decision, zone | Invocacoes LLM |
| `smartlic_searches_total` | Counter | sector, result_status | Total de buscas |
| `smartlic_circuit_breaker_degraded` | Gauge | source | Estado do CB |
| `smartlic_active_searches` | Gauge | — | Buscas em execucao |

---

## Definition of Done

- [ ] Todos os 10 ACs verificados e marcados
- [ ] PR aprovado com screenshot do output de `/metrics`
- [ ] `prometheus_client` adicionado ao `requirements.txt`
- [ ] Testes existentes passam sem regressao (baseline backend mantido)
- [ ] Novos testes em `test_metrics.py` cobrindo todas as 11 metricas
- [ ] Endpoint `/metrics` acessivel em staging com token
- [ ] Documentacao de setup Grafana Cloud criada
- [ ] `METRICS_ENABLED` e `METRICS_TOKEN` adicionados ao `.env.example`
- [ ] MEMORY.md atualizado com lista de metricas disponiveis
