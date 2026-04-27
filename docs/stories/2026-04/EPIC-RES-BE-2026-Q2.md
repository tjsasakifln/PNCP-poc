# EPIC-RES-BE-2026-Q2 — Resiliência Backend (Anti-Reincidência P0)

**Status:** Draft
**Owner:** @architect (Aria) + @dev (Dex)
**Quality Gate:** @qa (Quinn)
**Sprint Window:** 2026-04-29 → 2026-06-23 (8 semanas, 4 sprints)
**Origem:** Auditoria sistêmica pós-incidente P0 (PR #529, 2026-04-27) — plano `/home/tjsasakifln/.claude/plans/sistema-est-amea-ado-por-serene-hanrahan.md`

---

## Context

Em 2026-04-27 SmartLic saiu de incidente P0 (Googlebot wave + build SSG saturando 1 worker hobby Railway → DB pool exhaustion → wedge total). Hotfix PR #529 protegeu apenas 2 endpoints de **56 callsites `.execute()` Supabase síncronos sem budget temporal** e cobriu 2 de **41 rotas sem negative cache no failure path**. Janela operacional realista de 7-14 dias antes que próxima onda de crawl reincida o cenário.

Auditoria identificou 4 classes de defeito correlatas:

1. **I/O sem budget temporal** — `.execute()` Supabase fora de `_run_with_budget` ou `asyncio.wait_for` em 56 callsites distribuídos por `routes/mfa.py` (10×), `referral.py` (7×), `founding.py` (4×), `conta.py` (4×), `sitemap_*.py` (7× total), `features.py` (3×), `user.py` (2×) e outros 20+ módulos com 1× cada.
2. **Failure paths sem negative cache** — 41 rotas sem proteção contra falha-repetição (query falha → próximo request repete query falha → amplificação de cascata downstream).
3. **God-modules acoplados** — `filter/pipeline.py` (1918L), `metrics.py` (1251L com 108 fan-in), `routes/blog_stats.py` (1179L), `routes/admin.py` (1132L) — coesão baixa, blast radius alto, testes lentos.
4. **Observabilidade incompleta** — datalake fallback fail-open sem Prometheus counters, healthcheck retorna 200 mesmo com DB indisponível, env vars de debug (PYTHONASYNCIODEBUG=1) descobertos em prod durante Stage 2 do incidente sem gate de auditoria.

Padrão `_run_with_budget` está definido em `backend/pipeline/budget.py` (L28-93) com instrumentação Prometheus (`smartlic_pipeline_budget_exceeded_total{phase,source}`), mas existe apenas 1 callsite (`pipeline/stages/execute.py:1240`). O padrão precisa virar lei universal nas rotas HTTP críticas antes de qualquer iniciativa SEO programática em escala.

---

## Goal

Eliminar 100% das rotas com I/O Supabase sem budget temporal e instituir negative cache + observabilidade Prometheus contínua nas 41 rotas do failure path em até 4 sprints (8 semanas).

---

## Business Value

- **Previne reincidência do P0 (PR #529)** — janela de 7-14 dias antes da próxima onda Googlebot.
- **Pré-requisito da tese SEO 100% inbound** — não é seguro escalar páginas programáticas (10k → 1M projetadas em 9-12 meses) com backend que falha sob 5x carga atual.
- **Trust score Googlebot** — incidente custou janela de indexação; reincidência amplia o prejuízo SEO compostamente.
- **Habilita Railway Hobby por mais 6-9 meses** — corrigir software antes de comprar tier (princípio: software-first).
- **Reduz superfície de "ponto sem volta" arquitetural** — god-modules splittados desbloqueiam refator futuros sem freeze.

---

## Success Metrics (binários ou numéricos pós-Sprint 6)

| # | Métrica | Baseline | Target | Fonte |
|---|---|---|---|---|
| 1 | `smartlic_route_timeout_total{route="*"}` sob carga 5x baseline | n/a (não instrumentado) | 0 | Prometheus + Locust load test |
| 2 | p99 latency rotas públicas | desconhecido | < 2.5s | `http_request_duration_seconds{quantile=0.99}` |
| 3 | DB pool utilization sob Googlebot wave conhecida | 100% (P0) | < 60% | `smartlic_db_pool_in_use` |
| 4 | % rotas críticas instrumentadas com `_run_with_budget` | 1/56 (1.8%) | 100% (56/56) | CI gate (RES-BE-001) |
| 5 | Sentry events/min (24h pós-deploy) | 30+/min durante P0 | < 5/min | Sentry dashboard |
| 6 | Suite de testes backend tempo CI total | desconhecido (estimado >12min) | < 8min | GitHub Actions |
| 7 | Cobertura de testes nas linhas tocadas | ≥85% | ≥85% | pytest --cov |

---

## Constraints

- **Railway Hobby:** 1 worker default, 512MB RAM (referência atual da auditoria); pool 10 conexões Supabase. Decisão de upgrade Hobby→Pro postergada até pós-refator (princípio: software-first).
- **n=2 baseline:** abaixo do noise floor; nenhum A/B test estatístico válido; rollback decidido por métricas técnicas (Prometheus/Sentry) e não por conversão.
- **14-day window:** Sprint 1 (RES-BE-001..002, RES-BE-011, RES-BE-013) é não-negociável dentro de 5 dias úteis para fechar a janela antes da próxima onda Googlebot.
- **Equipe pequena:** ~1 dev backend full-time + arquiteto compartilhado.
- **Compatibilidade:** mudanças não podem quebrar testes existentes (5131+ passando, 0 failures); pre-existing skipped/xfail mantidos até RES-BE-009.

---

## Stories deste Epic

| ID | Título | Prio | Esforço | Sprint | Dep |
|---|---|---|---|---|---|
| [RES-BE-001](RES-BE-001-audit-execute-without-budget.md) | Auditoria automatizada `.execute()` sem budget (CI gate) | P0 | M | 1 | — |
| [RES-BE-002](RES-BE-002-budget-top5-routes.md) | Hotfix budget temporal nas top-5 rotas por tráfego | P0 | M | 1 | RES-BE-001 |
| [RES-BE-003](RES-BE-003-negative-cache-failure-paths.md) | Negative cache padrão em 41 failure paths | P0 | L | 2 | RES-BE-002 |
| [RES-BE-004](RES-BE-004-datalake-observability.md) | Observabilidade datalake hit/miss/error (Prometheus) | P1 | S | 2 | RES-BE-001 |
| [RES-BE-005](RES-BE-005-godmodule-split-pipeline.md) | God-module split: `filter/pipeline.py` (1918L) | P1 | L | 4 | RES-BE-001 |
| [RES-BE-006](RES-BE-006-godmodule-split-metrics.md) | God-module split: `metrics.py` (1251L, 108 fan-in) | P1 | L | 5 | RES-BE-001 |
| [RES-BE-007](RES-BE-007-godmodule-split-blogstats.md) | God-module split: `routes/blog_stats.py` (1179L) | P1 | M | 4 | RES-BE-001 |
| [RES-BE-008](RES-BE-008-godmodule-split-admin.md) | God-module split: `routes/admin.py` (1132L) | P2 | M | 6 | RES-BE-001 |
| [RES-BE-009](RES-BE-009-test-suite-triage.md) | Test suite triage 30s+ timeouts (317/342 ≥30s) | P1 | L | 3 | — |
| [RES-BE-010](RES-BE-010-bulkheads-critical-routes.md) | Bulkheads asyncio nas 10 rotas top tráfego | P1 | M | 3 | RES-BE-002, RES-BE-003 |
| [RES-BE-011](RES-BE-011-healthcheck-dependency-aware.md) | Healthcheck `/health/live` + `/health/ready` | P0 | S | 1 | — |
| [RES-BE-012](RES-BE-012-circuit-breaker-supabase.md) | Circuit breaker Supabase client (open/half-open/closed) | P2 | M | 6 | RES-BE-002 |
| [RES-BE-013](RES-BE-013-audit-prod-env-vars.md) | Audit env vars Railway pós-incidente (CI gate) | P0 | S | 1 | — |

---

## Sequenciamento Crítico

```
Sprint 1 (29/abr–05/mai): RES-BE-001 → RES-BE-002 → RES-BE-011 → RES-BE-013
                                    ↘ (paralelo: RES-BE-004)
Sprint 2-3 (06–26/mai):  RES-BE-003 → RES-BE-010
                         RES-BE-009 (paralelo)
Sprint 4-5 (27/mai–16/jun): RES-BE-005, RES-BE-007 (paralelos)
                            RES-BE-006 (após RES-BE-005)
Sprint 6 (17–23/jun):    RES-BE-008, RES-BE-012 (P2 backlog)
```

---

## Validation Framework

### Prometheus invariants (alarmes)

```promql
# Hard fail: timeout em rota produção
sum by (route) (rate(smartlic_route_timeout_total[5m])) > 0.1

# Pool exhaustion approaching
max(smartlic_db_pool_in_use) > 0.6

# Negative cache não está protegendo (taxa hit baixa em failure burst)
rate(smartlic_negative_cache_hit_total[5m]) / rate(smartlic_route_error_total[5m]) < 0.5

# Bulkhead rejeitando indica saturação não absorvida
rate(smartlic_bulkhead_rejected_total[5m]) > 0
```

### Locust load test (sintético, simula Googlebot wave)

- 200 req/s nas top-10 rotas por 10 minutos
- Critério de sucesso: 0 wedge, p99 < 2.5s, sem 5xx > 0.1%
- Reproduz cenário PR #529 antes de declarar epic Done

### Sentry fingerprints

- `["route_timeout", route]` — timeout invariant violation
- `["pool_exhaustion"]` — pool > 80%
- `["budget_exceeded", phase, source]` — `_run_with_budget` exceeded

---

## Rollback Strategy

| Trigger | Ação |
|---|---|
| p99 latency > 2x baseline pós-deploy | `ENABLE_BUDGET_WRAP=false` (feature flag por story); revert PR específico |
| Pool exhaustion reincidente | Revert para versão pré-Sprint 1; investigar gap com `EXPLAIN ANALYZE` |
| Test suite tempo > 12min CI | Reverter RES-BE-009 changes; reativar `@pytest.mark.skip` ofensivos |
| God-module split quebra import externo | Backward-compat shim no módulo original re-exporta símbolos |

---

## Out-of-Scope (deste Epic)

- **Migração Hobby→Pro Railway** — software-first; pós-Sprint 6 reavaliar.
- **Rewrite Supabase client** — adapter atual aceita budget wrap; rewrite seria over-engineering.
- **Async migration ARQ → Celery/Temporal** — ARQ funciona; troca não justificada.
- **Graceful degradation HTTP 503 com Retry-After global** — escopo separado (futuro `RES-BE-XXX`).
- **Multi-region failover Supabase** — luxo pre-revenue.

---

## Dependencies (entrada)

- Plano aprovado: `/home/tjsasakifln/.claude/plans/sistema-est-amea-ado-por-serene-hanrahan.md`
- Padrão referência: `backend/pipeline/budget.py::_run_with_budget`
- Hotfix precedente: PR #529 (commit 11b368cc) — endpoints já protegidos: `routes/empresa_publica.py:169`, `routes/contratos_publicos.py:450`

## Dependencies (saída)

- **Bloqueia EPIC-SEO-PROG-2026-Q2** stories SEO-PROG-001..005 (rotas SSR→ISR exigem backend protegido em staging antes de SSG fan-out).

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Epic criado a partir do plano de auditoria pós-P0 | @sm (River) |
