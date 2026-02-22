# CRIT-023 — OpenTelemetry Tracing Nunca Ativado em Producao (trace_id = "-")

**Tipo:** Observabilidade / Debt
**Prioridade:** P1 (Sem tracing fim-a-fim, debug de incidentes e cego)
**Criada:** 2026-02-22
**Status:** Parcialmente Concluído (falta deploy + validação pós-deploy)
**Origem:** Investigacao P0 — trace_id e span_id aparecem como "-" em todos os logs
**Dependencias:** Nenhuma
**Estimativa:** S (configuracao + verificacao)

---

## Problema

O codigo de tracing OpenTelemetry esta implementado (`telemetry.py`, `middleware.py`) mas **nunca foi ativado em producao**.

### Cadeia Causal

1. `config.py:62-66`: `OTEL_EXPORTER_OTLP_ENDPOINT` nao esta setado em producao
2. `telemetry.py:64-66`: Sem endpoint, `_noop = True` — tracing fica em modo noop
3. `telemetry.py:191-204` (`get_trace_id()`): Retorna `None` quando `_noop = True`
4. `telemetry.py:207-217` (`get_span_id()`): Retorna `None` quando `_noop = True`
5. `middleware.py:38-45`: `record.trace_id = get_trace_id() or "-"` — sempre "-"

### Impacto

- **Sem tracing fim-a-fim** — impossivel correlacionar request → fetch → filter → LLM
- **Debug de incidentes** depende apenas de `correlation_id` (gerado por request, sem propagacao cross-service)
- **PNCP latency** invisivel — nao ha spans para medir tempo de cada chamada API
- **LLM calls** nao rastreadas — impossivel ver tempo de resposta do GPT-4.1-nano por classificacao

### Infra Existente

- Prometheus metrics ja ativo (CRIT-E03, commit `056e5dd`)
- Grafana Cloud Free Tier documentado em `docs/guides/metrics-setup.md`
- Railway suporta env vars via `railway variables set`

---

## Solucao

### Abordagem: Configurar OTEL_EXPORTER_OTLP_ENDPOINT no Railway

### Criterios de Aceitacao

- [x] **AC1:** `OTEL_EXPORTER_OTLP_ENDPOINT` configurado no Railway para backend service — `https://otlp-gateway-prod-sa-east-1.grafana.net/otlp` + `OTEL_EXPORTER_OTLP_HEADERS` com Basic auth (instanceId 1534562, token `smartlic-backend-otel`)
- [x] **AC2:** `OTEL_SERVICE_NAME=smartlic-backend` configurado
- [x] **AC3:** `.env.example` documentado com as variaveis OTEL
- [ ] **AC4:** Logs em producao mostram `trace_id` e `span_id` reais (nao "-") — pós-deploy
- [ ] **AC5:** Grafana Cloud mostra traces da aplicacao — pós-deploy
- [x] **AC6:** Verificar que tracing nao degrada performance (sampling rate adequado) — OTEL_SAMPLING_RATE=0.1 configurado

### Verificacao Pos-Deploy

- [ ] `railway logs` mostra trace_id != "-" nos logs
- [ ] Grafana Tempo (ou equivalente) mostra traces completos
- [ ] Latencia do endpoint `/buscar` nao aumenta com tracing ativo

---

## Arquivos Envolvidos

| Arquivo | Mudanca |
|---|---|
| `.env.example` | Documentar OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_EXPORTER_OTLP_HEADERS, OTEL_SERVICE_NAME, OTEL_SAMPLING_RATE |
| `backend/telemetry.py` | CRIT-023: HTTP/protobuf exporter (was gRPC) + OTEL_EXPORTER_OTLP_HEADERS parsing |
| `backend/requirements.txt` | Switch `opentelemetry-exporter-otlp-proto-grpc` → `opentelemetry-exporter-otlp-proto-http` |
| Railway env vars | 4 OTEL vars configuradas (ENDPOINT, HEADERS, SERVICE_NAME, SAMPLING_RATE) |

---

## Notas de Implementacao

- Grafana Cloud Free Tier inclui 50GB traces/mes — suficiente para volume atual
- Sampling rate: considerar `OTEL_SAMPLING_RATE=0.1` (10%) inicialmente para controlar volume
- Pacotes OTel ja estao no `requirements.txt` (verificar se todos instalados no Railway)
- `telemetry.py` ja tem toda a logica de init — so precisa do endpoint configurado
- NAO requer mudanca de codigo Python se endpoint estiver correto
