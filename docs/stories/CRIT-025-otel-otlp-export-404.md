# CRIT-025 — OTel OTLP Export 404 (Grafana Cloud Endpoint Misconfiguration)

**Status:** Pending
**Priority:** High
**Severity:** Error (non-blocking, but blind observability)
**Sentry Issue:** SMARTLIC-BACKEND-1C (#7284033412)
**Created:** 2026-02-22
**Relates to:** CRIT-023 (OTel Tracing Production Setup)

---

## Contexto

Sentry reporta erro recorrente no backend:

```
Failed to export span batch code: 404, reason: 404 page not found
```

- **Logger:** `opentelemetry.exporter.otlp.proto.http.trace_exporter`
- **Environment:** production
- **URL target:** `https://otlp-gateway-prod-sa-east-1.grafana.net/otlp`
- **Python:** CPython 3.11.14

O OTel exporter foi configurado em CRIT-023 mas o endpoint OTLP retorna 404, significando que **nenhum trace esta sendo exportado para Grafana Cloud** — tracing esta cego.

## Causa Raiz

O SDK `opentelemetry-exporter-otlp-proto-http` auto-appenda `/v1/traces` ao `OTEL_EXPORTER_OTLP_ENDPOINT`.

Se o endpoint estiver configurado como:
```
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-sa-east-1.grafana.net/otlp
```

O SDK constroi:
```
https://otlp-gateway-prod-sa-east-1.grafana.net/otlp/v1/traces  -> 404
```

O correto seria **sem** o sufixo `/otlp`:
```
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-sa-east-1.grafana.net
```

Gerando:
```
https://otlp-gateway-prod-sa-east-1.grafana.net/v1/traces  -> 200
```

## Arquivos Envolvidos

- `backend/telemetry.py:100-105` — `OTLPSpanExporter()` auto-reads env vars
- `backend/config.py` — env var loading
- `backend/.env.example:138-150` — documentacao errada (sugere `/otlp` no endpoint)

## Acceptance Criteria

- [ ] **AC1:** Corrigir `OTEL_EXPORTER_OTLP_ENDPOINT` no Railway removendo `/otlp` do final
- [ ] **AC2:** Verificar `OTEL_EXPORTER_OTLP_HEADERS` tem formato correto: `Authorization=Basic <base64(instanceId:cloudApiToken)>`
- [ ] **AC3:** Atualizar `.env.example` com documentacao correta:
  ```
  # For Grafana Cloud: https://otlp-gateway-prod-<region>.grafana.net (SEM /otlp no final)
  # O SDK appenda /v1/traces automaticamente
  ```
- [ ] **AC4:** Adicionar validacao de startup em `telemetry.py` que loga WARNING se endpoint termina com `/otlp`
- [ ] **AC5:** Verificar traces aparecem no Grafana Cloud apos deploy
- [ ] **AC6:** Resolver issue SMARTLIC-BACKEND-1C no Sentry

## Verificacao

```bash
# Testar endpoint localmente
curl -v https://otlp-gateway-prod-sa-east-1.grafana.net/v1/traces \
  -H "Authorization: Basic <base64>" \
  -H "Content-Type: application/x-protobuf" \
  --data-binary ""
# Deve retornar 400 (bad request) ou 200, NAO 404

# Verificar no Railway
railway variables | grep OTEL
```

## Estimativa

- **Esforco:** Baixo (config change + doc fix + startup validation)
- **Risco:** Nenhum (nao afeta funcionalidade, apenas observability)
- **Impacto:** Alto (tracing cego impede diagnostico de issues em producao)
