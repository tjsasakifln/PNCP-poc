# Monitoramento Operacional — SmartLic

> Referência operacional para monitors de uptime, alert rules de erro e procedimentos de resposta.
> Última atualização: 2026-02-21

---

## 1. Monitors de Uptime (UptimeRobot)

| # | Serviço | URL Monitorada | Intervalo | Destinatário | Monitor ID | Status |
|---|---------|----------------|-----------|-------------|-----------|--------|
| 1 | Backend Health | `https://bidiq-backend-production.up.railway.app/health` | 5 min | tiago.sasaki@gmail.com | 802345290 | ✅ Ativo |
| 2 | Frontend Health | `https://smartlic.tech/api/health` | 5 min | tiago.sasaki@gmail.com | 802345291 | ✅ Ativo |
| 3 | Homepage | `https://smartlic.tech` | 5 min | tiago.sasaki@gmail.com | 802345057 | ✅ Ativo |

**Dashboard:** https://dashboard.uptimerobot.com/

### Detalhes dos Health Endpoints

**Backend `/health`** retorna:
```json
{
  "status": "healthy",
  "ready": true,
  "uptime_seconds": 12345,
  "dependencies": { "redis": "ok", "supabase": "ok" }
}
```
- HTTP 200 = saudável
- HTTP 503 = dependência crítica indisponível

**Frontend `/api/health`** retorna:
```json
{
  "status": "ok",
  "backend": "reachable",
  "timestamp": "2026-02-21T10:00:00Z"
}
```
- HTTP 200 = frontend + backend OK
- HTTP 503 = backend indisponível (deep check)

---

## 2. Alert Rules (Sentry)

| # | Nome da Rule | Condição | Ação | Projeto | Rule ID |
|---|-------------|----------|------|---------|---------|
| 1 | High Error Rate Alert - Backend | Sessions affected > 5% in 5min | Notify IssueOwners/ActiveMembers | smartlic-backend | 16688768 |
| 2 | New Issue Alert - Backend | A new issue is created | Notify IssueOwners/ActiveMembers | smartlic-backend | 16688756 |
| 3 | High Error Rate Alert - Frontend | Sessions affected > 5% in 5min | Notify IssueOwners/ActiveMembers | smartlic-frontend | 16688769 |
| 4 | New Issue Alert - Frontend | A new issue is created | Notify IssueOwners/ActiveMembers | smartlic-frontend | 16688757 |
| 5 | Stripe Webhook Error - Backend | Stripe webhook failures | Notify IssueOwners/ActiveMembers | smartlic-backend | 16688772 |
| 6 | High Priority Issues (Backend) | High priority issues | Notify IssueOwners | smartlic-backend | 16137961 |
| 7 | High Priority Issues (Frontend) | High priority issues | Notify IssueOwners | smartlic-frontend | 16688648 |
| 8 | Uptime Monitoring (auto) | HTTP uptime check every 1 min | Auto-detected | smartlic-backend | 6595733 |

**Dashboard Sentry:** https://confenge.sentry.io/

### Projetos Sentry

| Projeto | Slug | Tipo |
|---------|------|------|
| SmartLic Backend | `smartlic-backend` | FastAPI (Python) |
| SmartLic Frontend | `smartlic-frontend` | Next.js (TypeScript) |

**Organização:** `confenge`

### Configuração Sentry Ativa

- **PII Scrubbing:** Ativo (emails, tokens, IPs mascarados antes do envio)
- **Transient Fingerprinting:** Timeouts e rate limits agrupados como `warning` (não disparam alerts)
- **Traces Sampling:** 10% (health checks excluídos)
- **Environment:** `production`

---

## 3. Métricas Prometheus

**Endpoint:** `GET /metrics` (Bearer token auth via `METRICS_TOKEN`)

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `search_duration_seconds` | Histogram | Duração total de buscas |
| `fetch_duration_seconds` | Histogram | Duração de fetch por fonte |
| `llm_call_duration_seconds` | Histogram | Duração de chamadas LLM |
| `cache_hits_total` | Counter | Cache hits (L1 + L2) |
| `cache_misses_total` | Counter | Cache misses |
| `api_errors_total` | Counter | Erros de API por fonte |
| `searches_total` | Counter | Total de buscas realizadas |
| `circuit_breaker_degraded` | Gauge | Estado do circuit breaker |
| `active_searches` | Gauge | Buscas ativas no momento |

**Status:** Endpoint ativo, scraper Grafana Cloud não conectado.

---

## 4. Procedimentos

### 4.1 Adicionar Novo Monitor UptimeRobot

1. Acesse https://dashboard.uptimerobot.com/
2. Clique em **"+ Add New Monitor"**
3. Configure:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Nome descritivo do serviço
   - **URL:** URL do health endpoint
   - **Monitoring Interval:** 5 minutes
4. Em **"Alert Contacts To Notify"**, selecione `tiago.sasaki@gmail.com`
5. Clique **"Create Monitor"**
6. Atualize esta tabela com o novo monitor

### 4.2 Adicionar Nova Alert Rule Sentry

1. Acesse https://confenge.sentry.io/alerts/rules/
2. Clique **"Create Alert"**
3. Selecione o projeto (backend ou frontend)
4. Configure condições:
   - **Issue Alerts:** "When" → condição → "Then" → Send notification to email
   - **Metric Alerts:** "When" → threshold → "Critical" → Notify email
5. Defina destinatário: `tiago.sasaki@gmail.com`
6. Salve e atualize esta tabela

### 4.3 Remover/Pausar Monitor

**UptimeRobot:**
- Dashboard → Selecione monitor → **"Pause"** (1 clique, reversível)
- Para remover: **"Delete"** (irreversível)

**Sentry:**
- Dashboard → Alerts → Rules → Toggle **"Disable"** (reversível)
- Para remover: **"Delete Rule"** (irreversível)

### 4.4 Resposta a Alerta de Downtime

1. **Recebeu email "DOWN"** → Verificar qual serviço caiu (backend ou frontend)
2. **Verificação manual:**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" https://bidiq-backend-production.up.railway.app/health
   curl -s -o /dev/null -w "%{http_code}" https://smartlic.tech/api/health
   ```
3. **Diagnóstico:** `railway logs --tail` para ver logs recentes
4. **Resolução:** Railway auto-restart (1-2 min) ou `railway up` para redeploy
5. **Verificação:** Aguardar email "UP" do UptimeRobot (< 10 min)

### 4.5 Resposta a Alerta Sentry

1. **Recebeu email de alerta** → Abrir link do issue no Sentry
2. **Analisar:** Stack trace, breadcrumbs, request data (PII já mascarado)
3. **Classificar:**
   - Transient (timeout, rate limit) → Monitorar, sem ação imediata
   - Bug real → Criar issue no GitHub, priorizar fix
   - Configuração → Verificar env vars no Railway
4. **Resolver:** Fix + deploy + marcar issue como "Resolved" no Sentry

---

## 5. Links Rápidos

| Recurso | URL |
|---------|-----|
| UptimeRobot Dashboard | https://dashboard.uptimerobot.com/ |
| Sentry (confenge) | https://confenge.sentry.io/ |
| Sentry Backend Project | https://confenge.sentry.io/projects/smartlic-backend/ |
| Sentry Frontend Project | https://confenge.sentry.io/projects/smartlic-frontend/ |
| Railway Dashboard | https://railway.app/dashboard |
| Prometheus Metrics | `https://bidiq-backend-production.up.railway.app/metrics` |
| Backend Health | https://bidiq-backend-production.up.railway.app/health |
| Frontend Health | https://smartlic.tech/api/health |

---

## 6. Contatos

| Função | Nome | Email |
|--------|------|-------|
| Responsável Operacional | Tiago Sasaki | tiago.sasaki@gmail.com |

---

## 7. Histórico de Alterações

| Data | Alteração | Story |
|------|-----------|-------|
| 2026-02-21 | Documento criado com monitors e alert rules | GTM-GO-001 |
