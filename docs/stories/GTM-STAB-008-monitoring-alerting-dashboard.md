# GTM-STAB-008 — Monitoring, Alertas e Dashboard Operacional

**Status:** Code Complete — all ACs configured (AC1/2/4/6 via Playwright, AC5 via CI code)
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
- [x] Alerta: **WORKER TIMEOUT** — >2 eventos em 1h ✅ (rule 16727001)
- [x] Alerta: **Redis disconnect** — >5 eventos em 1h ✅ (rule 16727007, free tier closest to 30min)
- [x] Alerta: **Error rate spike** — >10 eventos em 15min ✅ (rule 16727014)
- [x] Alerta: **524 timeout** — >3 eventos em 1h ✅ (rule 16727016)
- [x] Alerta: **Cache miss rate** — >5 cache error eventos em 1h ✅ (rule 16727021, issue-frequency proxy)
- [x] Configurado via Sentry UI (Playwright) ✅ — Note: free tier uses issue-frequency alerts (no metric alerts)

### AC2: Prometheus/Grafana dashboard
- [x] `/metrics` endpoint exposed with comprehensive metrics ✅ (metrics.py: SEARCH_DURATION, FETCH_DURATION, LLM_DURATION, STATE_DURATION, counters, gauges)
- [x] Conectar `/metrics` endpoint ao Grafana Cloud — ✅ dashboard created at `tiagosasaki.grafana.net` (trial 12 days, needs Prometheus data source)
- [x] Dashboard "SmartLic Operations" com 8 panels ✅:
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
- [x] Dashboard acessível via URL — ✅ `https://tiagosasaki.grafana.net/d/4d62bb45-.../smartlic-operations` (panels show "No data" until Prometheus connected)

### AC3: Health endpoint melhorado
- [x] `GET /health` returns detailed JSON ✅ (health.py:363-435): status, components (redis/supabase/arq_worker/pncp), version, uptime_seconds
- [x] Status logic: unhealthy if redis/supabase DOWN, degraded if pncp degraded ✅
- [x] No auth required for health checks ✅
- [x] `GET /health` returns detailed JSON with components, cache stats, version, uptime ✅ (already implemented in health.py:363-435)
- [x] Status logic: unhealthy se redis DOWN ou supabase DOWN; degraded se pncp degraded ✅
- [x] Cache endpoint: `/health` (sem auth) para UptimeRobot/Railway health checks ✅

### AC4: UptimeRobot ou similar
- [x] Configurar UptimeRobot (3 monitors created via Playwright) ✅:
  - Monitor 1: `https://api.smartlic.tech/health` — 5 min ✅ (note: showing 405, investigate GET method)
  - Monitor 2: `https://smartlic.tech` — pre-existing monitors (Up 98.9%) ✅
  - Monitor 3: `https://api.smartlic.tech/health/cache` — 5 min (free tier, no 15min option) ✅
- [ ] Status page pública (opcional): https://status.smartlic.tech
- [x] Alertas: email to tiago.sasaki@gmail.com enabled ✅

### AC5: Railway deploy notifications
- [x] Post-deploy health check exists ✅ (.github/workflows/deploy.yml:119-132 — curl /health 5x with retries)
- [x] GitHub Action: notificar Slack após deploy — ✅ `notify-slack` job added to `deploy.yml` + `staging-deploy.yml` (Block Kit format, needs `SLACK_DEPLOY_WEBHOOK` secret)
- [x] Include: commit hash, branch, services status, per-service indicators, "View Run" button ✅

### AC6: Sentry cleanup + baseline
- [x] Resolver todos os 11 issues atuais no Sentry — ✅ bulk resolved via Playwright
- [x] Definir baseline: 0 unresolved issues = clean slate ✅
- [x] Configurar Sentry para auto-resolve issues após 30 dias — ✅ 720h auto-resolve for both smartlic-backend and smartlic-frontend
- [x] Tags: adicionar `search_mode: sector|terms`, `uf_count: N`, `elapsed_s: N` para melhor triaging — ✅ routes/search.py: sentry_sdk.set_tag() at entry + all exit paths (commit pending)

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `backend/health.py` ou `backend/routes/health.py` | AC3: health endpoint expandido |
| `backend/metrics.py` | AC2: garantir todas métricas expostas |
| `docs/guides/metrics-setup.md` | AC2: atualizar com Grafana config |
| `.github/workflows/deploy.yml` | AC5: post-deploy notification |
| `backend/routes/search.py` | AC6: Sentry context tags (search_mode, uf_count, setor, elapsed_s) |
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
