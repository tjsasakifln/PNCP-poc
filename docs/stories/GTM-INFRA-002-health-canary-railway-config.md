# GTM-INFRA-002: Health Canary Realista + Railway Config

## Epic
Root Cause — Infraestrutura (EPIC-GTM-ROOT)

## Sprint
Sprint 8: GTM Root Cause — Tier 3

## Prioridade
P2

## Estimativa
4h

## Descricao

O health canary do PNCP usa `tamanhoPagina=10`, mas producao usa `tamanhoPagina=50`. Quando PNCP mudou o limite max para 50, o canary nao detectou (testa com 10, que funciona). O Railway `drainingSeconds=15` mata buscas em andamento durante deploys. O frontend proxy so retenta 503, mas Railway retorna 502/524 em timeout.

### Situacao Atual

| Componente | Comportamento | Problema |
|------------|---------------|----------|
| Health canary | `tamanhoPagina=10` | Nao testa realidade da producao (50) |
| Railway config | `drainingSeconds=15` | Mata buscas em andamento no deploy |
| Frontend proxy | Retenta 503 apenas | 502/524 nao retentados |
| `PNCP_BATCH_DELAY` | 2.0s | Excessivo — adiciona 10s+ em buscas multi-UF |

### Evidencia da Investigacao (Squad Root Cause 2026-02-23)

| Finding | Agente | Descricao |
|---------|--------|-----------|
| ARCH-3 | Architect | Canary tamanhoPagina=10 nao detecta limite real |
| ARCH-6 | Architect | drainingSeconds=15 mata buscas em deploy |
| ARCH-7 | Architect | Frontend proxy so retenta 503 |
| ARCH-8 | Architect | PNCP_BATCH_DELAY 2.0s excessivo |

## Criterios de Aceite

### Health Canary

- [ ] AC1: Canary usa `tamanhoPagina=50` (mesmo que producao)
- [ ] AC2: Canary testa PCP v2 e ComprasGov alem de PNCP
- [ ] AC3: Health endpoint reporta status per-source (nao apenas "ok/fail" global)

### Railway Config

- [ ] AC4: `drainingSeconds` aumentado para 120 (alinhado com Railway hard timeout)
- [ ] AC5: Documentar em `railway.toml` ou `railway.json`

### Frontend Proxy Retry

- [ ] AC6: `RETRYABLE_STATUSES` expandido: `[502, 503, 504, 524]`
- [ ] AC7: Retry com backoff: 1s, 2s (max 2 retries no proxy level)

### Batch Delay

- [ ] AC8: `PNCP_BATCH_DELAY` reduzido: 2.0s → 0.5s (configuravel via env)
- [ ] AC9: Monitorar rate limits apos reducao (metrica `api_errors_total{source="pncp",status="429"}`)

## Testes Obrigatorios

```bash
cd backend && pytest -k "test_health_canary or test_pncp_batch" --no-coverage
```

- [ ] T1: Canary usa tamanhoPagina=50
- [ ] T2: Health endpoint reporta status per-source
- [ ] T3: Proxy retenta 502 e 524 (nao apenas 503)
- [ ] T4: Batch delay configuravel via env

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/pncp_client.py` | Modificar — canary tamanhoPagina=50, batch delay |
| `backend/health.py` | Modificar — per-source status |
| `frontend/app/api/buscar/route.ts` | Modificar — RETRYABLE_STATUSES expandido |
| `railway.toml` (ou config) | Criar/Modificar — drainingSeconds=120 |
| `backend/config.py` | Modificar — PNCP_BATCH_DELAY default 0.5 |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Paralela | GTM-INFRA-001 | Config changes complementam |
| Paralela | GTM-ARCH-001 | Menos critico apos async pattern |
