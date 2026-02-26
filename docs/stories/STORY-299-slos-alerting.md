# STORY-299: SLOs + Alerting

**Sprint:** 2 — Make It Observable
**Size:** M (4-8h)
**Root Cause:** Track D (Infrastructure Audit)
**Depends on:** STORY-290 through STORY-298
**Industry Standard:** [Google SRE — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/), [Google SRE — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)

## Contexto

Hoje temos Prometheus metrics + Sentry errors mas ZERO SLOs definidos. Não temos como responder: "O sistema está saudável?" Sem SLOs, todo alert é ad-hoc e toda decisão é reativa.

Google SRE estabelece que SLOs são a fundação de toda operação confiável. Sem eles, não há erro budget, não há priorização objetiva.

## Acceptance Criteria

### SLO Definitions
- [ ] AC1: SLOs definidos e documentados:
  | SLI | SLO | Window |
  |-----|-----|--------|
  | Search success rate | 95% | 7 days rolling |
  | Search latency p50 | <15s | 7 days rolling |
  | Search latency p99 | <60s | 7 days rolling |
  | SSE connection success | 99% | 7 days rolling |
  | API availability (non-5xx) | 99.5% | 30 days rolling |

- [ ] AC2: Prometheus recording rules para cada SLI
- [ ] AC3: Error budget calculation: `1 - SLO` = budget consumível

### Alerting
- [ ] AC4: Alert rules (Prometheus ou Sentry):
  | Alert | Condition | Severity |
  |-------|-----------|----------|
  | SearchSuccessLow | success rate <90% for 15min | critical |
  | SearchLatencyHigh | p99 >90s for 10min | warning |
  | SSEDropRate | >20% drops in 5min | warning |
  | ErrorBudgetBurn | >50% budget consumed in 1h | critical |
  | WorkerTimeout | any SIGABRT in 5min | critical |

- [ ] AC5: Sentry alerts configurados para erros críticos (worker timeout, circuit breaker open)
- [ ] AC6: Health endpoint expandido: `GET /health` retorna SLO compliance status

### Dashboard
- [ ] AC7: `/admin` dashboard com SLO compliance visual (gauge charts)
- [ ] AC8: Error budget remaining (percentage bar)
- [ ] AC9: Trend charts: SLI over last 7/30 days

### Quality
- [ ] AC10: Documentação SLO em `docs/slos.md`
- [ ] AC11: Testes existentes passando

## Technical Notes

```python
# Prometheus recording rules (in metrics.py or separate rules file)
SEARCH_SUCCESS_RATE = (
    smartlic_searches_completed_total /
    (smartlic_searches_completed_total + smartlic_searches_failed_total)
)

# Error budget burn rate
BURN_RATE_1H = (1 - success_rate_1h) / (1 - SLO_TARGET)
# Alert if burn_rate > 14.4 (consuming 1d budget in 1h)
```

SLOs são conservadores intencionalmente — 95% search success (não 99%) porque estamos saindo de ~0% para um sistema funcional. SLOs serão apertados conforme estabilidade aumenta.

## Files to Change

- `backend/metrics.py` — recording rules, SLI calculations
- `backend/health.py` — SLO compliance status
- `backend/routes/admin.py` — SLO dashboard data endpoints
- `frontend/app/admin/page.tsx` — SLO dashboard UI
- `docs/slos.md` — NEW: SLO documentation

## Definition of Done

- [ ] SLOs definidos e measuráveis
- [ ] Alerts configurados e testados
- [ ] Dashboard mostra compliance em tempo real
- [ ] Todos os testes passando
- [ ] PR merged
