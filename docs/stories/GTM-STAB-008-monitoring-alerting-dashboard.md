# GTM-STAB-008 — Monitoring, Alertas e Dashboard Operacional

**Status:** To Do
**Priority:** P1 — High (operação cega = problemas invisíveis até usuário reclamar)
**Severity:** Ops — sem alertas, problemas descobertos manualmente
**Created:** 2026-02-24
**Sprint:** GTM Stabilization
**Relates to:** GTM-RESILIENCE-E03 (Prometheus metrics), GTM-STAB-001 a 007 (todas as fixes)

---

## Problema

Hoje o monitoramento é **reativo**: problemas são descobertos quando:
1. Tiago testa manualmente e vê o erro
2. Alguém abre o Sentry e olha os issues
3. Railway logs são inspecionados sob demanda

Não existe:
- Alertas automáticos para timeout, Redis down, PNCP failures
- Dashboard operacional com métricas em tempo real
- Indicador de saúde do sistema visível para o time
- SLA tracking (uptime, error rate, P95 latency)

---

## Acceptance Criteria

### AC1: Sentry alertas configurados
- [ ] Alerta: **WORKER TIMEOUT** — notificar Slack/email se >2 eventos em 1h
- [ ] Alerta: **Redis disconnect** — notificar se >5 eventos em 30min
- [ ] Alerta: **Error rate spike** — notificar se error rate >10% por 15min
- [ ] Alerta: **524 timeout** — notificar se >3 eventos em 1h
- [ ] Alerta: **Cache miss rate** — notificar se >80% misses por 1h (cache quebrado)
- [ ] Configurar via Sentry UI (Alerts > Create Alert Rule) ou CLI

### AC2: Prometheus/Grafana dashboard
- [ ] Conectar `/metrics` endpoint (GTM-RESILIENCE-E03) ao Grafana Cloud Free Tier
- [ ] Dashboard "SmartLic Operations" com panels:
  | Panel | Métrica | Threshold |
  |-------|---------|-----------|
  | Search Latency P95 | `search_duration_seconds` | <60s verde, <120s amarelo, >120s vermelho |
  | Error Rate | `api_errors_total / searches_total` | <5% verde, <15% amarelo, >15% vermelho |
  | Cache Hit Rate | `cache_hits / (cache_hits + cache_misses)` | >70% verde, >40% amarelo |
  | PNCP Circuit Breaker | `circuit_breaker_degraded` | 0=verde, 1=vermelho |
  | Active Searches | `active_searches` gauge | <10 verde, <20 amarelo |
  | LLM Call Duration | `llm_call_duration_seconds` | <5s verde, <15s amarelo |
  | ARQ Queue Depth | custom metric | <50 verde, <100 amarelo |
  | Redis Connectivity | health ping | up=verde, down=vermelho |
- [ ] Dashboard acessível via URL compartilhável (Grafana public dashboard)

### AC3: Health endpoint melhorado
- [ ] `GET /health` existente deve retornar status JSON detalhado:
  ```json
  {
    "status": "healthy|degraded|unhealthy",
    "components": {
      "pncp": { "status": "up", "latency_ms": 450, "circuit_breaker": "closed" },
      "pcp": { "status": "up", "latency_ms": 200 },
      "redis": { "status": "up", "latency_ms": 2 },
      "supabase": { "status": "up", "latency_ms": 15 },
      "openai": { "status": "up", "latency_ms": 800 },
      "arq_worker": { "status": "up", "last_heartbeat": "2s ago" }
    },
    "cache": {
      "hit_rate_1h": 0.72,
      "entries": 234,
      "oldest_entry": "3.5h"
    },
    "version": "0.5.1",
    "uptime_seconds": 3600
  }
  ```
- [ ] Status logic: unhealthy se redis DOWN ou supabase DOWN; degraded se pncp degraded
- [ ] Cache endpoint: `/health` (sem auth) para UptimeRobot/Railway health checks

### AC4: UptimeRobot ou similar
- [ ] Configurar UptimeRobot (free tier, 50 monitors):
  - Monitor 1: `https://api.smartlic.tech/health` — check a cada 5 min
  - Monitor 2: `https://smartlic.tech` — frontend alive check a cada 5 min
  - Monitor 3: `https://api.smartlic.tech/health/cache` — cache health a cada 15 min
- [ ] Status page pública (opcional): https://status.smartlic.tech
- [ ] Alertas: email + Slack webhook para downtime

### AC5: Railway deploy notifications
- [ ] GitHub Action: notificar Slack após deploy (sucesso ou falha)
- [ ] Include: commit hash, changelog summary, deploy duration
- [ ] Post-deploy health check: hit `/health` 30s após deploy, alert se unhealthy

### AC6: Sentry cleanup + baseline
- [ ] Resolver todos os 11 issues atuais no Sentry (após fixes aplicadas)
- [ ] Definir baseline: 0 unresolved issues = clean slate
- [ ] Configurar Sentry para auto-resolve issues após 30 dias sem recorrência
- [ ] Tags: adicionar `search_mode: sector|terms`, `uf_count: N`, `elapsed_s: N` para melhor triaging

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `backend/health.py` ou `backend/routes/health.py` | AC3: health endpoint expandido |
| `backend/metrics.py` | AC2: garantir todas métricas expostas |
| `docs/guides/metrics-setup.md` | AC2: atualizar com Grafana config |
| `.github/workflows/deploy.yml` | AC5: post-deploy notification |
| Sentry UI | AC1: alert rules, AC6: cleanup |
| Grafana Cloud | AC2: dashboard creation |
| UptimeRobot | AC4: monitor config |

---

## Decisões Técnicas

- **Grafana Cloud Free** — 14 dias retention, 10k series. Suficiente para POC/early startup. Zero infra management.
- **UptimeRobot Free** — 50 monitors, 5min interval. Gold standard para startups.
- **Health endpoint sem auth** — Necessário para health checks automatizados. Não expõe dados sensíveis, apenas status.
- **Sentry baseline zero** — Cada issue não resolvido é ruído que masca problemas reais. Clean slate = visibilidade.

## Estimativa
- **Esforço:** 4-6h (maioria é configuração, pouco código)
- **Risco:** Baixo (observability, não muda behavior)
- **Squad:** @devops (Grafana + UptimeRobot + Sentry alerts) + @dev (health endpoint) + @qa (validation)
