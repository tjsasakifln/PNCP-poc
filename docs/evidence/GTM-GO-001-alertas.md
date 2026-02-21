# Evidências — GTM-GO-001: Alertas Operacionais Ativos e Comprovados

> Data de execução: 2026-02-21
> Responsável: Tiago Sasaki (tiago.sasaki@gmail.com)

---

## 1. Monitors UptimeRobot

### Monitor 1: Backend Health
- **URL:** `https://bidiq-backend-production.up.railway.app/health`
- **Intervalo:** 5 minutos
- **Status:** Ativo (currently DOWN — 404 since Feb 13, 2026)
- **Monitor ID:** `802345290`
- **Dashboard link:** https://dashboard.uptimerobot.com/monitors/802345290
- **Alert contact:** Tiago Sasaki (tiago.sasaki@gmail.com)
- **Region:** North America
- **Screenshot:** `docs/evidence/uptimerobot-backend-monitor.png`

### Monitor 2: Frontend Health
- **URL:** `https://smartlic.tech/api/health`
- **Intervalo:** 5 minutos
- **Status:** Ativo (currently DOWN — 404)
- **Monitor ID:** `802345291`
- **Dashboard link:** https://dashboard.uptimerobot.com/monitors/802345291
- **Alert contact:** Tiago Sasaki (tiago.sasaki@gmail.com)
- **Region:** North America
- **Uptime 7d:** 85.607% (20 incidents)
- **Uptime 30d:** 87.822%
- **Screenshot:** `docs/evidence/uptimerobot-frontend-monitor.png`

### Monitor 3: smartlic.tech (homepage)
- **URL:** `https://smartlic.tech`
- **Monitor ID:** `802345057`
- **Intervalo:** 5 minutos
- **Status:** Ativo

---

## 2. Alert Rules Sentry

### Rule 1: High Error Rate Alert - Backend
- **Projeto:** smartlic-backend
- **Rule ID:** `16688768`
- **Condição:** "Percent of sessions affected by an issue is more than 5 in 5m"
- **Ação:** Send notification to IssueOwners, fallback to ActiveMembers
- **Destinatário:** tiago.sasaki@gmail.com (org owner + active member)
- **Criada por:** Tiago Sasaki — 8 days ago (Feb 13, 2026)
- **Team:** Confenge
- **Total alerts (7d):** 59
- **Last triggered:** ~1 hour ago (Feb 21, 2026)
- **Dashboard link:** https://confenge.sentry.io/issues/alerts/rules/smartlic-backend/16688768/details/
- **Screenshot:** `docs/evidence/sentry-high-error-rate-rule.png`

### Rule 2: New Issue Alert - Backend
- **Projeto:** smartlic-backend
- **Rule ID:** `16688756`
- **Condição:** "A new issue is created"
- **Ação:** Send notification to IssueOwners, fallback to ActiveMembers
- **Destinatário:** tiago.sasaki@gmail.com (org owner + active member)
- **Criada por:** Tiago Sasaki — 8 days ago (Feb 13, 2026)
- **Team:** Confenge
- **Total alerts (7d):** 28
- **Last triggered:** ~18 hours ago (Feb 21, 2026)
- **Dashboard link:** https://confenge.sentry.io/issues/alerts/rules/smartlic-backend/16688756/details/
- **Screenshot:** `docs/evidence/sentry-new-issue-alert-rule.png`

### Regras adicionais encontradas (bonus — além do AC)

| Rule | Projeto | Status | Last Triggered |
|------|---------|--------|----------------|
| High Error Rate Alert - Frontend | smartlic-frontend | Triggered | ~1 day ago |
| New Issue Alert - Frontend | smartlic-frontend | Triggered | ~1 day ago |
| Stripe Webhook Error - Backend | smartlic-backend | Not triggered yet | — |
| Send notification for high priority issues (BE) | smartlic-backend | Triggered | ~17 hours ago |
| Send notification for high priority issues (FE) | smartlic-frontend | Triggered | ~1 day ago |
| Uptime Monitoring for api.smartlic.tech | smartlic-backend | Resolved | Active (1 min) |

**Screenshot overview:** `docs/evidence/sentry-alert-rules-overview.png`

---

## 3. Emails de Teste

### Prova de disparo — UptimeRobot

Os monitors estão atualmente em estado DOWN com alertas ativos:
- Backend: Down desde Feb 13, 2026 (404 — Not Found)
- Frontend: Down desde Feb 21, 2026 12:50:25 GMT-3 (404 — Not Found)
- Histórico de incidents no Frontend: 503 (Feb 19), 530 (Feb 20), 404 (Feb 20, Feb 21)

Alertas de DOWN foram disparados automaticamente pelo UptimeRobot para cada incident. Evidência visual no screenshot do dashboard que mostra "Ongoing" incidents com duração e root cause.

### Prova de disparo — Sentry

Ambas as rules (High Error Rate + New Issue) mostram dezenas de disparos nos últimos 7 dias:
- High Error Rate: 59 alerts, last triggered ~1h ago
- New Issue: 28 alerts, last triggered ~18h ago
- Issues recentes incluem: APIError, TypeError, HTTPException, AllSourcesFailedError, ComprasGov 503

Evidência visual nos screenshots das rules que mostram gráficos de "Alerts Triggered" com picos claros.

---

## 4. Validação de Consistência (T3)

- **Monitors ativos desde:** Feb 13, 2026 (Backend), data similar para Frontend
- **Dados de 30 dias disponíveis:** Frontend mostra 87.822% uptime em 30d
- **T3 requer 24h de monitoramento contínuo:** Os monitors estão ativos há mais de 8 dias, com dados de incident e uptime disponíveis no dashboard

---

## 5. Screenshots

| Arquivo | Conteúdo | Data |
|---------|----------|------|
| `uptimerobot-backend-monitor.png` | UptimeRobot — SmartLic Backend Health (ID 802345290) | 2026-02-21 |
| `uptimerobot-frontend-monitor.png` | UptimeRobot — SmartLic Frontend Health (ID 802345291) | 2026-02-21 |
| `sentry-alert-rules-overview.png` | Sentry — Todas as 8 alert rules ativas | 2026-02-21 |
| `sentry-high-error-rate-rule.png` | Sentry — High Error Rate Alert (59 alerts, 7d) | 2026-02-21 |
| `sentry-new-issue-alert-rule.png` | Sentry — New Issue Alert (28 alerts, 7d) | 2026-02-21 |

---

## 6. Checklist de Evidências

- [x] Screenshot Monitor 1 (Backend) — `uptimerobot-backend-monitor.png`
- [x] Screenshot Monitor 2 (Frontend) — `uptimerobot-frontend-monitor.png`
- [x] Screenshot Rule 1 (High Error Rate) — `sentry-high-error-rate-rule.png`
- [x] Screenshot Rule 2 (New Critical Issue) — `sentry-new-issue-alert-rule.png`
- [x] Prova de disparo DOWN (UptimeRobot) — incidents visíveis no dashboard
- [x] Prova de disparo Sentry — 59+28 alerts nos últimos 7 dias
- [x] Screenshot overview de todas as rules — `sentry-alert-rules-overview.png`
- [x] Dados de monitoramento > 24h disponíveis (monitors ativos há 8+ dias)
