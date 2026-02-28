# STORY-316: Health Canary + Status Page

**Epic:** EPIC-PRE-GTM-2026-02
**Sprint:** Sprint 3 (Post-launch)
**Priority:** MEDIUM
**Story Points:** 5 SP
**Estimate:** 3-4 dias
**Owner:** @dev + @devops

---

## Problem

O sistema de health check (`health.py`) e completo internamente mas nao ha pagina de status publica para usuarios verificarem se o servico esta operacional. Alem disso, o canary de saude do PNCP usa `tamanhoPagina=10` que nao detecta o bug de `tamanhoPagina > 50` (silent HTTP 400). Usuarios reportam problemas sem visibilidade sobre status do sistema.

## Solution

Criar pagina de status publica acessivel sem autenticacao, alimentada pelo health check existente, com historico de disponibilidade e notificacao de incidentes. Aprimorar canary para detectar cenarios reais.

---

## Acceptance Criteria

### Backend — Canary Aprimorado

- [ ] **AC1:** Criar canary "realista" em `health.py` que testa com parametros reais:
  - PNCP: `tamanhoPagina=50` (detecta bug de page size limit)
  - PCP v2: request real com pagination
  - ComprasGov: dual-endpoint test
  - Timeout: 10s por fonte (nao bloquear health check)
- [ ] **AC2:** Health check deve retornar per-source status:
  ```json
  {
    "status": "degraded",
    "sources": {
      "pncp": { "status": "healthy", "latency_ms": 450, "last_check": "..." },
      "pcp": { "status": "unhealthy", "latency_ms": null, "error": "timeout" },
      "comprasgov": { "status": "healthy", "latency_ms": 320 }
    },
    "components": {
      "redis": "healthy",
      "supabase": "healthy",
      "arq_worker": "healthy"
    },
    "uptime_pct_24h": 99.2,
    "last_incident": "2026-02-25T14:30:00Z"
  }
  ```
- [ ] **AC3:** Criar endpoint publico `GET /status` (sem auth) com response acima
- [ ] **AC4:** Endpoint interno `GET /health` continua existente (com detalhes, requer auth admin)

### Backend — Historico de Disponibilidade

- [ ] **AC5:** Criar tabela `health_checks`:
  - `id`, `checked_at`, `overall_status`, `sources_json`, `components_json`, `latency_ms`
  - Retention: 30 dias
- [ ] **AC6:** Cron job a cada 5 minutos que executa health check e salva resultado:
  - ARQ task `health_canary_check`
  - Respeitar feature flag `HEALTH_CANARY_ENABLED`
- [ ] **AC7:** Calcular uptime percentages de historico:
  - Ultimas 24h, 7 dias, 30 dias
  - healthy = 100%, degraded = 50%, unhealthy = 0%

### Backend — Alertas de Incidente

- [ ] **AC8:** Se status muda de healthy → degraded/unhealthy:
  - Enviar email para admin (fire-and-forget)
  - Log estruturado com Sentry alert
  - Criar registro em `incidents` table
- [ ] **AC9:** Criar tabela `incidents`:
  - `id`, `started_at`, `resolved_at`, `status` (ongoing|resolved), `affected_sources`, `description`
- [ ] **AC10:** Deteccao automatica de resolucao:
  - Se 3 checks consecutivos sao healthy apos incident → auto-resolve
  - Enviar email "Incidente resolvido"

### Frontend — Status Page Publica

- [ ] **AC11:** Criar pagina `/status` (publica, sem auth):
  - Header: "Status do SmartLic" com status geral (Operacional / Degradado / Indisponivel)
  - Icone e cor: verde / amarelo / vermelho
  - Componentes individuais: PNCP, Portal de Compras, ComprasGov, Redis, Banco de Dados
  - Cada componente: nome + status badge + latencia
- [ ] **AC12:** Grafico de uptime dos ultimos 90 dias (barras horizontais por dia):
  - Verde: 100% uptime
  - Amarelo: parcialmente degradado
  - Vermelho: incidente
  - Tooltip com detalhes ao hover
- [ ] **AC13:** Secao "Incidentes Recentes":
  - Lista de incidentes dos ultimos 30 dias
  - Data, duracao, componentes afetados, descricao
- [ ] **AC14:** Auto-refresh a cada 60 segundos (polling)
- [ ] **AC15:** Design limpo, minimalista, carrega rapido (nao depende de auth/session)

### Frontend — Status Badge no Footer

- [ ] **AC16:** No footer de todas as paginas: "Status: Operacional" (ou Degradado/Indisponivel) com link para /status
- [ ] **AC17:** Badge usa dados de `BackendStatusIndicator` existente (CRIT-008) — reusar polling

### Metricas

- [ ] **AC18:** Prometheus:
  - `smartlic_health_canary_duration_seconds`
  - `smartlic_health_canary_status` (gauge: 1=healthy, 0.5=degraded, 0=unhealthy)
  - `smartlic_incidents_total` (labels: source, severity)

### Testes

- [ ] **AC19:** Testes para canary realista (mock de cada fonte)
- [ ] **AC20:** Testes para calculo de uptime
- [ ] **AC21:** Testes para deteccao e resolucao de incidentes
- [ ] **AC22:** Testes frontend (render page, auto-refresh, incident list)
- [ ] **AC23:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Health check completo | `backend/health.py:1-455` | Existe, aprimorar canary |
| HealthStatus enum | `backend/health.py:34-39` | Existe |
| Circuit breaker canary | `backend/health.py:407-420` | Existe |
| SLO compliance | `backend/health.py:437-444` | Existe |
| Health routes | `backend/routes/health.py` | Existe |
| BackendStatusIndicator | `frontend/components/BackendStatusIndicator.tsx` | Existe |
| Health polling | Frontend polls `/api/health` every 30s | Existe |

## Files Esperados (Output)

**Novos:**
- `frontend/app/status/page.tsx`
- `frontend/app/status/components/UptimeChart.tsx`
- `frontend/app/status/components/IncidentList.tsx`
- `backend/tests/test_health_canary.py`
- `frontend/__tests__/status/status-page.test.tsx`
- `supabase/migrations/XXXXXXXX_add_health_checks_table.sql`
- `supabase/migrations/XXXXXXXX_add_incidents_table.sql`

**Modificados:**
- `backend/health.py` (canary realista)
- `backend/cron_jobs.py` (canary job)
- `backend/config.py` (HEALTH_CANARY_ENABLED)
- `backend/metrics.py`

## Dependencias

- Nenhuma (independente)

## Riscos

- Canary com `tamanhoPagina=50` pode ser bloqueado por PNCP rate limit — usar IP do worker, nao do web
- Status page publica pode expor informacoes sensiveis — sanitizar (nao mostrar IPs, tokens, etc.)
- Polling a cada 5 min = 288 checks/dia = ~8640/mes — avaliar custo DB
