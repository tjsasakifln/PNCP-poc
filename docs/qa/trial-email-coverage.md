# TRIAL-001 Audit — Trial Email Coverage

**Sessão**: keen-sutton 2026-04-26
**Escopo**: TRIAL-001 AC1, AC2 (slice). AC3+AC4+AC5+AC6+AC7+AC8 deferidos.
**Fonte de dados**: Supabase Management API queries em prod (`fqqyovlzdzimiwfofdjk`).
**n**: 3 trial profiles >14d (todos com plan_type=free_trial, COALESCE(is_admin,false)=false).

---

## AC1 — pg_cron health (parcial)

**Bom**:
- Maioria dos jobs `succeeded` em últimas 24h.

**Problemas encontrados (fora do escopo TRIAL mas registrados)**:

| Job | Status | Falha |
|-----|--------|-------|
| `bloat-check-pncp-raw-bids` | failed | `column "relpages" does not exist` (use `relname` em pg_stat_user_tables) |
| `cleanup-cold-cache-entries` | failed | syntax error: `INTERVAL 7 days` (precisa `INTERVAL '7 days'`) |
| `cleanup-reconciliation-log` | failed | (corrigir em sessão futura) |
| `retention-search-sessions` | failed | (corrigir em sessão futura) |
| `cleanup-audit-events` | never_ran | schedule `0 4 1 * *` — mensal, esperado se <30d desde criação |
| `cleanup-monthly-quota` | never_ran | mesma justificativa |
| `cleanup-trial-email-log` | never_ran | esperado, é cleanup periódico de log |

**Trial sequence cron**: `_trial_sequence_loop` é ARQ cron (não pg_cron), não aparece em `cron_job_health`. Validação requer Railway logs do worker — defer para AC6 follow-up.

---

## AC2 — `trial_email_log` cobertura por usuário

### Sequência esperada (`backend/services/trial_email_sequence.py:48-56`)

| # | Day | Type |
|---|-----|------|
| 1 | 0 | welcome |
| 2 | 3 | engagement |
| 3 | 7 | paywall_alert |
| 4 | 10 | value |
| 5 | 13 | last_day |
| 6 | 16 | expired |

### Cobertura observada

| user_id | created_at | Emails enviados | Missing |
|---------|-----------|----------------|---------|
| 39b32b6f-15ec-4347-b282-ab7da6ea43af | 2026-04-08 20:50 UTC | 2,3,4,5,6 | **1 (welcome)** |
| 285edd6e-6353-424a-9030-b488c01bcf50 | 2026-04-10 14:13 UTC | 2,3,4,5,6 | **1 (welcome)** |
| 00000000-0000-0000-0000-000000000000 | 2026-02-26 10:58 UTC | 2,3,4,5,6 | **1 (welcome)** |

**Cobertura global**:
- 5/6 emails core × 3 users = 15 enviados de 18 esperados = **83%**.
- Per email#: #1=0%, #2-#6=100%.

### Gap sistemático: email#1 (welcome day-0) faltando 100% das vezes

**Root cause** (analisado em `backend/services/trial_email_sequence.py:306-307`):

```python
target_start = (now - timedelta(days=day, hours=12)).isoformat()
target_end = (now - timedelta(days=day - 1, hours=-12)).isoformat()
```

Para `day=0`:
- `target_start = now - 12h`
- `target_end = now + 36h`
- Janela = [now-12h, now+36h] em vez do esperado [now-12h, now+12h]

**Cenário de falha**:
- User criado às 20:50 UTC (17:50 BRT).
- Cron `_trial_sequence_loop` roda 8-11am BRT = 11-14 UTC.
- Próximo cron @ 11 UTC dia seguinte: window-start = 23:00 UTC dia anterior.
- User created_at 20:50 UTC = **2h10m antes** do window-start → MISS.

Padrão se repete sistematicamente porque `target_start = now - 12h` cobre só 12h passadas, mas usuários típicos criam-se 12-23h antes do próximo 8-11am window.

**Fix proposto (não aplicado neste slice)**: trocar `target_start` para `now - timedelta(days=day, hours=24)` ou redesenhar para incluir users criados desde último cron run + lookback. Story de fix: TBD.

### Outras observações

- **Cadência fiel** após email 2: 3-4 dias entre cada emails 2→3→4→5→6.
- **Idempotência funcionando**: nenhum email duplicado por user.
- **`day-1` typo no `target_end`**: causa janela 48h em vez de 24h para emails ≥2. Idempotency (AC6 dedup) protege de envios duplos, mas tornar a janela 1d maior amplia risco de envios em day errado (ex: user day=2.5 receberia email day=3 antecipado). Não bloqueador imediato, mas vale fix junto do day-0 fix.

---

## AC5 — Opt-out smoke (deferido)

Não executado nesta sessão. Reason: prod side-effect em `email_preferences` exige email de teste dedicado + reverter. Defer para sessão TRIAL-001 follow-up.

---

## AC6 — Sentry triage (deferido)

Não executado nesta sessão. Reason: orçamento de slice priorizou AC2 (cobertura mensurada > triage qualitativa). Defer para sessão TRIAL-001 follow-up.

---

## Decisões / próximas ações

| Item | Owner | Sessão |
|------|-------|--------|
| Fix window calc em `process_trial_emails` (welcome day-0) | @dev | Próxima TRIAL slice |
| Fix `bloat-check-pncp-raw-bids` query (`relname` not `relpages`) | @data-engineer | Backlog low-priority |
| Fix `cleanup-cold-cache-entries` syntax | @data-engineer | Backlog low-priority |
| AC3 HMAC webhook verify, AC4 bounce, AC5 opt-out smoke, AC6 Sentry, AC7 Prom, AC8 runbook | TRIAL-001 follow-up | Sessão futura |

**Story TRIAL-001 fica `InProgress` após este slice.**
