# DEBT-S1.4: Observability e API Versioning
**Epic:** EPIC-DEBT
**Sprint:** 1
**Priority:** P1
**Estimated Hours:** 16h
**Assignee:** TBD

## Objetivo

Tornar metricas Prometheus persistentes (sobrevivem a deploys) e estabelecer versionamento de API consistente. Atualmente metricas resetam a cada deploy (in-memory) e rotas misturam `/v1/` com paths sem versao, sem negociacao de versao.

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| SYS-04 | Metricas Prometheus efemeras. Resetam a cada deploy (in-memory). Sem SLO tracking persistente. `reconciliation_log` ja persiste no DB. | HIGH | 8h |
| SYS-07 | Versionamento de API inconsistente. Algumas rotas usam `/v1/`, maioria nao. Sem negociacao de versao. | HIGH | 8h |

## Acceptance Criteria

- [ ] AC1: Metricas Prometheus chave (latency, error rate, request count) persistem entre deploys
- [ ] AC2: Push de metricas para tabela no DB (ou Redis) com granularidade de 1 minuto
- [ ] AC3: SLO dashboard data disponivel via endpoint admin (ex: `/admin/slo`)
- [ ] AC4: Todas as rotas publicas usam prefixo `/v1/` consistentemente
- [ ] AC5: Rotas legacy (sem `/v1/`) retornam redirect 308 ou continuam funcionando (backward compat)
- [ ] AC6: Header `API-Version` retornado em todas as respostas
- [ ] AC7: Documentacao OpenAPI reflete versionamento correto

## Tasks

### Track 1: Prometheus Persistence (8h)
- [ ] T1: Criar tabela `metrics_snapshots` (timestamp, metric_name, labels JSONB, value FLOAT)
- [ ] T2: Implementar push periodico (a cada 60s) das metricas chave para DB
- [ ] T3: Implementar restore de metricas do DB no startup (rehydrate counters)
- [ ] T4: Criar endpoint `/admin/slo` que agrega metricas persistidas
- [ ] T5: Testar que deploy nao reseta metricas

### Track 2: API Versioning (8h)
- [ ] T6: Mapear todas as 49 rotas e seus prefixos atuais (v1 vs sem versao)
- [ ] T7: Adicionar `/v1/` prefix para rotas que nao tem
- [ ] T8: Configurar redirect 308 das rotas legacy para versao versionada
- [ ] T9: Adicionar middleware que injeta header `API-Version: 1.0` em todas as respostas
- [ ] T10: Atualizar frontend API proxies para usar paths versionados
- [ ] T11: Atualizar documentacao OpenAPI

## Testes Requeridos

- [ ] `test_metrics_persistence.py`: metricas sobrevivem a "restart" (mock)
- [ ] `test_metrics_persistence.py`: restore no startup rehydrata counters
- [ ] `test_api_versioning.py`: todas as rotas publicas respondem em `/v1/`
- [ ] `test_api_versioning.py`: rotas legacy fazem redirect ou continuam funcionando
- [ ] `test_api_versioning.py`: header `API-Version` presente nas respostas
- [ ] Frontend tests passam com novos paths versionados
- [ ] E2E tests passam

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **SYS-04:** `reconciliation_log` ja persiste dados de reconciliacao no DB -- mesmo pattern pode ser usado para metricas.
- **SYS-07:** Rotas de billing, user, analytics ja usam `/v1/`. Faltam rotas de busca, pipeline, feedback, etc.
- **Backward compat:** Frontend proxies precisam ser atualizados junto com backend. Coordenar deploy.
- Considerar usar Redis TSDB (TimeSeries) se disponivel, ao inves de tabela SQL.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secao "Sistema" (SYS-04, SYS-07)
- Metrics: `backend/metrics.py`
- Routes: `backend/routes/` (19 modulos)
- Frontend proxies: `frontend/app/api/`
