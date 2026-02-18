# GTM-RESILIENCE-F02 --- Distributed Tracing com OpenTelemetry

| Campo | Valor |
|-------|-------|
| **Track** | F: Infra para Escala |
| **Prioridade** | P2 |
| **Sprint** | 4 |
| **Estimativa** | 6-8 horas (3 tracks paralelizaveis) |
| **Gaps** | I-06 |
| **Dependencias** | Nenhuma hard dependency (Redis opcional para trace propagation em jobs) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

O SmartLic roda com 2 gunicorn workers (UvicornWorker) atras de um reverse proxy Railway. Cada busca percorre 7 estagios de pipeline, faz chamadas a 2-3 APIs externas (PNCP, PCP, ComprasGov), executa filtragem com LLM arbiter (GPT-4.1-nano), gera resumo LLM e planilha Excel. Uma unica busca pode gerar 50-120 log lines distribuidas entre modulos.

### Situacao Atual

- **Correlation ID**: `CorrelationIDMiddleware` em `middleware.py` injeta `X-Request-ID` (UUID) em cada request e propaga via `ContextVar`
- **RequestIDFilter**: Todos os log records incluem `request_id` para correlacao
- **X-Request-ID forwarded**: `pncp_client.py` L538 e `llm.py` L185 propagam o header para APIs externas
- **Sem tracing distribuido**: Nao ha OpenTelemetry, Jaeger, Datadog, ou qualquer SDK de tracing instalado
- **Sem spans**: Impossivel medir duracao individual de estagios do pipeline (fetch PNCP vs filter vs LLM vs Excel)
- **Sem trace context propagation**: Eventos SSE e background tasks (se implementados via F-01) nao herdam contexto de trace
- **Debug multi-worker**: Com 2 workers, uma mesma busca pode ter requests SSE no worker A e POST no worker B, sem como correlacionar

### Impacto

- Diagnosticar latencia requer ler 50-120 log lines manualmente e inferir tempos
- Impossivel saber se o gargalo e PNCP (fetch), filter (LLM arbiter), ou Excel (openpyxl)
- Incidentes multi-worker sao black boxes
- Sem baseline de performance por estagio para otimizacao futura

---

## Problema

O sistema nao possui tracing distribuido. Com 2+ workers, 3 APIs externas e 7 estagios de pipeline, e impossivel:

1. Seguir uma busca end-to-end atraves de todos os estagios
2. Medir duracao real de cada estagio (fetch, filter, LLM, Excel)
3. Correlacionar requests entre workers diferentes
4. Identificar gargalos de latencia sem analise manual de logs
5. Propagar contexto de trace para jobs em background ou eventos SSE

---

## Solucao

Integrar **OpenTelemetry SDK** com exportador OTLP (compativel com Jaeger, Grafana Tempo, Datadog) para instrumentar o pipeline de busca com spans hierarquicos:

1. **Instalar OpenTelemetry SDK** (core + instrumentacao FastAPI + httpx)
2. **Instrumentar 7 estagios do pipeline** como spans filhos de um span raiz "search"
3. **Instrumentar chamadas HTTP externas** (PNCP, PCP, ComprasGov) automaticamente via opentelemetry-instrumentation-httpx
4. **Propagar trace context** para SSE events e background jobs (ARQ, se F-01 implementado)
5. **Configurar sampling rate** em 10% para producao (100% em dev/staging)
6. **Exportar para OTLP endpoint** (compativel com qualquer backend: Jaeger, Tempo, Datadog)

---

## Acceptance Criteria

### Track 1 --- SDK e Configuracao (P0)

- [ ] **AC1**: Dependencias adicionadas a `requirements.txt`:
  - `opentelemetry-api>=1.25,<2.0`
  - `opentelemetry-sdk>=1.25,<2.0`
  - `opentelemetry-exporter-otlp-proto-grpc>=1.25,<2.0`
  - `opentelemetry-instrumentation-fastapi>=0.46b0`
  - `opentelemetry-instrumentation-httpx>=0.46b0`
- [ ] **AC2**: Modulo `backend/telemetry.py` criado com: `init_tracing()`, `get_tracer()`, `get_current_span()`
- [ ] **AC3**: `init_tracing()` chamado no `lifespan()` de `main.py` durante startup
- [ ] **AC4**: `FastAPIInstrumentor` automaticamente instrumenta todas as rotas (spans para cada endpoint)
- [ ] **AC5**: `HttpxClientInstrumentor` automaticamente instrumenta chamadas httpx para PNCP/PCP (spans filhos)
- [ ] **AC6**: Sampling rate configuravel via env var `OTEL_SAMPLING_RATE` (default: `0.1` = 10% em producao)
- [ ] **AC7**: Service name configuravel via env var `OTEL_SERVICE_NAME` (default: `smartlic-backend`)
- [ ] **AC8**: Exportador OTLP configuravel via env var `OTEL_EXPORTER_OTLP_ENDPOINT` (sem default --- tracing desabilitado se nao configurado)
- [ ] **AC9**: Se `OTEL_EXPORTER_OTLP_ENDPOINT` nao configurado, tracing e completamente no-op (zero overhead)

### Track 2 --- Instrumentacao do Pipeline (P0)

- [ ] **AC10**: Span raiz `"search_pipeline"` criado no inicio de `SearchPipeline.run()` com atributos:
  - `search.id` = search_id
  - `search.sector` = sector_name
  - `search.ufs` = lista de UFs
  - `search.user_id` = user_id (se autenticado)
- [ ] **AC11**: 7 spans filhos criados para cada estagio do pipeline:
  - `"pipeline.validate"` (estagio 1)
  - `"pipeline.prepare"` (estagio 2)
  - `"pipeline.fetch"` (estagio 3 --- inclui PNCP + PCP + ComprasGov)
  - `"pipeline.filter"` (estagio 4 --- inclui keyword + LLM arbiter)
  - `"pipeline.enrich"` (estagio 5 --- sanctions, metadata)
  - `"pipeline.generate"` (estagio 6 --- LLM summary + Excel)
  - `"pipeline.persist"` (estagio 7 --- cache + response)
- [ ] **AC12**: Cada span de estagio registra:
  - `duration_ms` como atributo
  - `items_in` e `items_out` (quando aplicavel, ex: filter input/output count)
  - `status` ("ok", "error", "timeout")
- [ ] **AC13**: Span `"pipeline.fetch"` tem sub-spans por fonte: `"fetch.pncp"`, `"fetch.pcp"`, `"fetch.compras_gov"`
- [ ] **AC14**: Span `"pipeline.filter"` tem sub-spans: `"filter.keyword"`, `"filter.llm_arbiter"`, `"filter.zero_match_llm"`
- [ ] **AC15**: Span `"pipeline.generate"` tem sub-spans: `"generate.llm_summary"`, `"generate.excel"`, `"generate.upload"`
- [ ] **AC16**: Erros capturados dentro de spans com `span.record_exception(e)` e `span.set_status(StatusCode.ERROR)`

### Track 3 --- Propagacao e Integracao (P1)

- [ ] **AC17**: Trace context (trace_id, span_id) incluido nos eventos SSE como campo `trace_id` no JSON do `ProgressEvent`
- [ ] **AC18**: Se F-01 (ARQ jobs) implementado, trace context propagado para jobs via headers ARQ
- [ ] **AC19**: `X-Request-ID` existente (middleware.py) e o `trace_id` do OpenTelemetry sao vinculados: o correlation middleware seta `trace_id` como atributo no span ativo
- [ ] **AC20**: Log records incluem `trace_id` e `span_id` via `LoggingInstrumentor` ou custom filter
- [ ] **AC21**: Endpoint `GET /v1/health` inclui campo `tracing: "enabled" | "disabled"` baseado na presenca de OTLP endpoint

### Track 4 --- Testes (P0)

- [ ] **AC22**: Teste unitario: `init_tracing()` sem OTLP endpoint = no-op (nenhuma exception, nenhum overhead)
- [ ] **AC23**: Teste unitario: `init_tracing()` com OTLP endpoint configura TracerProvider corretamente
- [ ] **AC24**: Teste unitario: sampling rate 0.0 = nenhum span exportado; 1.0 = todos exportados
- [ ] **AC25**: Teste unitario: `get_tracer()` retorna tracer funcional (cria spans)
- [ ] **AC26**: Teste de integracao: pipeline completo com tracing ativo gera span raiz + 7 spans filhos
- [ ] **AC27**: Teste de performance: tracing com sampling=0.1 adiciona <1ms de overhead por request (benchmark com 100 requests)
- [ ] **AC28**: Todos os testes existentes passam sem regressao (tracing no-op por default em test env)

---

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/requirements.txt` | Adicionar 5 pacotes opentelemetry |
| `backend/telemetry.py` | **NOVO** --- Inicializacao OTel, tracer factory, helpers |
| `backend/main.py` | Chamar `init_tracing()` no lifespan; registrar instrumentors |
| `backend/search_pipeline.py` | Wrapping de 7 estagios com spans; atributos de busca |
| `backend/pncp_client.py` | Atributos adicionais em spans httpx (UF, modalidade) |
| `backend/filter.py` | Sub-spans para keyword match e LLM arbiter |
| `backend/llm.py` | Sub-span para geracao de resumo |
| `backend/excel.py` | Sub-span para geracao de Excel |
| `backend/consolidation.py` | Sub-spans por fonte (PNCP, PCP, ComprasGov) |
| `backend/progress.py` | Campo `trace_id` nos ProgressEvents |
| `backend/middleware.py` | Vincular X-Request-ID ao span ativo |
| `backend/tests/test_telemetry.py` | **NOVO** --- Testes de configuracao e spans |

---

## Dependencias

| Dependencia | Tipo | Status |
|-------------|------|--------|
| OpenTelemetry SDK | Nova | A instalar (5 pacotes, ~2MB total) |
| OTLP endpoint (Jaeger/Tempo) | Soft | Opcional --- tracing no-op sem endpoint |
| GTM-RESILIENCE-F01 (ARQ) | Soft | Se implementado, propagar trace context para jobs |
| Redis | Soft | Ja suportado; necessario para trace propagation cross-worker via pub/sub |

---

## Definition of Done

- [ ] Tracing inicializa sem erros no startup (com e sem OTLP endpoint)
- [ ] Pipeline de busca gera span hierarquico com 7 estagios visiveis
- [ ] Chamadas PNCP/PCP geram sub-spans automaticamente (httpx instrumentation)
- [ ] Sampling rate de 10% funcional em producao
- [ ] Zero overhead mensuravel quando tracing desabilitado (no OTLP endpoint)
- [ ] <1ms overhead quando tracing habilitado com sampling=0.1
- [ ] Log records incluem trace_id para correlacao log-trace
- [ ] Health endpoint reporta status do tracing
- [ ] Todos os testes existentes passam sem regressao
- [ ] 7+ novos testes passando
- [ ] Documentacao inline no modulo telemetry.py

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Overhead de tracing em producao | Baixa | Medio | Sampling 10% + no-op quando desabilitado (AC9) |
| Dependencias OTel conflitam com versoes existentes | Baixa | Alto | Pinned versions; testar com requirements completo |
| OTLP endpoint nao provisionado na Railway | Alta | Baixo | Tracing e no-op sem endpoint; funcional localmente com Jaeger Docker |
| Spans muito verbosos (>100 por busca) | Media | Baixo | Instrumentar apenas 7 estagios + sub-spans criticos; nao instrumentar per-page |
| Memory leak em TracerProvider | Baixa | Medio | Shutdown gracioso no lifespan; span export com batch processor |

---

## Notas Tecnicas

### Hierarquia de Spans Proposta

```
search_pipeline (root span)
  |--- pipeline.validate
  |--- pipeline.prepare
  |--- pipeline.fetch
  |     |--- fetch.pncp
  |     |     |--- httpx: GET pncp.gov.br/api/... (auto)
  |     |     |--- httpx: GET pncp.gov.br/api/... (auto)
  |     |--- fetch.pcp
  |     |     |--- httpx: GET compras.api.portaldecompraspublicas.com.br/... (auto)
  |     |--- fetch.compras_gov (se habilitado)
  |--- pipeline.filter
  |     |--- filter.keyword
  |     |--- filter.llm_arbiter
  |     |--- filter.zero_match_llm
  |--- pipeline.enrich
  |--- pipeline.generate
  |     |--- generate.llm_summary
  |     |--- generate.excel
  |     |--- generate.upload
  |--- pipeline.persist
```

### Configuracao Zero-Config

Se nenhuma env var OTEL for configurada, o sistema comporta-se **identicamente** ao estado atual. Tracing e puramente aditivo:

```python
# telemetry.py
def init_tracing():
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set — tracing disabled (no-op)")
        return  # No-op: zero overhead, zero side effects
    ...
```

### Sampling Strategy

| Ambiente | Taxa | Justificativa |
|----------|------|---------------|
| Local/dev | 100% | Visibilidade total para debugging |
| Staging | 50% | Representativo sem custo excessivo |
| Producao | 10% | Baseline de performance + diagnostico de incidentes |

A taxa e configuravel via `OTEL_SAMPLING_RATE` sem redeploy.

### Compatibilidade com Correlation ID Existente

O `CorrelationIDMiddleware` (middleware.py) continuara funcionando. O `X-Request-ID` sera adicionado como atributo ao span ativo do OpenTelemetry, permitindo buscar traces por request ID nos dashboards.

```python
# middleware.py (apos integracao)
span = trace.get_current_span()
if span and span.is_recording():
    span.set_attribute("http.request_id", req_id)
```
