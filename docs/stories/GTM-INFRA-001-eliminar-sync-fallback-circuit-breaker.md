# GTM-INFRA-001: Eliminar Sync PNCPClient Fallback + Ajustar Circuit Breaker

## Epic
Root Cause — Infraestrutura (EPIC-GTM-ROOT)

## Sprint
Sprint 8: GTM Root Cause — Tier 3

## Prioridade
P2

## Estimativa
8h

## Descricao

O `PNCPClient` tem fallback sincrono usando `requests.Session` + `time.sleep()` que bloqueia o event loop inteiro do asyncio quando acionado. O circuit breaker tem threshold de 50 falhas — demorando 3-5 minutos para tripar, tempo no qual o sistema fica irresponsivo. O Gunicorn timeout esta em 900s (15 min), muito acima do Railway hard timeout de 120s.

### Situacao Atual

| Componente | Comportamento | Problema |
|------------|---------------|----------|
| `PNCPClient` fallback | `requests.Session` sync | Bloqueia event loop asyncio |
| `time.sleep()` | Backoff sincrono | Bloqueia worker inteiro |
| Circuit breaker threshold | 50 falhas | 3-5min para tripar — muito lento |
| Gunicorn timeout | 900s | Dead code — Railway mata em 120s |
| `start.sh` | `--timeout 900` | Nao reflete realidade |

### Evidencia da Investigacao (Squad Root Cause 2026-02-23)

| Finding | Agente | Descricao |
|---------|--------|-----------|
| ARCH-2 | Architect | Sync fallback bloqueia event loop |
| ARCH-4 | Architect | time.sleep() bloqueia worker |
| ARCH-9 | Architect | Gunicorn timeout 900s e dead code |

## Criterios de Aceite

### Eliminar Sync Fallback

- [ ] AC1: `PNCPClient` sync removido OU wrappado em `asyncio.to_thread()` (nao bloqueia event loop)
- [ ] AC2: `time.sleep()` substituido por `asyncio.sleep()` em TODO o codebase backend
- [ ] AC3: `requests.Session` substituido por `httpx.AsyncClient` no fallback

### Circuit Breaker

- [ ] AC4: Threshold reduzido: 50 → 15 falhas
- [ ] AC5: Recovery timeout reduzido: proporcional ao novo threshold
- [ ] AC6: Circuit breaker state reportado via metrica Prometheus (ja existe `circuit_breaker_degraded`)

### Gunicorn/Railway

- [ ] AC7: Gunicorn timeout: 900s → 180s (acima de Railway 120s mas realista)
- [ ] AC8: `start.sh` atualizado com timeout correto
- [ ] AC9: Documentar em CLAUDE.md que Railway hard timeout e ~120s

## Testes Obrigatorios

```bash
cd backend && pytest -k "test_pncp_client or test_circuit_breaker" --no-coverage
```

- [ ] T1: Fallback nao bloqueia event loop (mock async test)
- [ ] T2: Circuit breaker tripa apos 15 falhas (nao 50)
- [ ] T3: Zero `time.sleep()` no codebase (grep test)
- [ ] T4: Gunicorn timeout configurado em 180s

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/pncp_client.py` | Modificar — remover sync fallback, asyncio.to_thread() |
| `backend/start.sh` | Modificar — timeout 900→180 |
| `backend/config.py` | Modificar — CB_THRESHOLD default 50→15 |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Depende de | GTM-ARCH-001 | Menos critico apos async job pattern |
| Paralela | GTM-INFRA-002 | Config changes complementam |
