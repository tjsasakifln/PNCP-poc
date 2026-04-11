# Alerting Rules & Runbooks — SmartLic

> Inventario de alertas configurados e procedimentos de resposta para cada cenario.
> Ultima atualizacao: 2026-03-11 | Story: DEBT-129

---

## 1. Inventario de Alertas

### 1.1 Sentry Alerts (Existentes)

| # | Nome | Condicao | Severidade | Projeto | Rule ID |
|---|------|----------|------------|---------|---------|
| 1 | High Error Rate Alert - Backend | Sessions affected > 5% in 5min | Critical | smartlic-backend | 16688768 |
| 2 | New Issue Alert - Backend | A new issue is created | Info | smartlic-backend | 16688756 |
| 3 | High Error Rate Alert - Frontend | Sessions affected > 5% in 5min | Critical | smartlic-frontend | 16688769 |
| 4 | New Issue Alert - Frontend | A new issue is created | Info | smartlic-frontend | 16688757 |
| 5 | Stripe Webhook Error - Backend | Stripe webhook failures | Critical | smartlic-backend | 16688772 |
| 6 | High Priority Issues (Backend) | High priority issues | Warning | smartlic-backend | 16137961 |
| 7 | High Priority Issues (Frontend) | High priority issues | Warning | smartlic-frontend | 16688648 |
| 8 | Uptime Monitoring (auto) | HTTP uptime check every 1 min | Critical | smartlic-backend | 6595733 |

### 1.2 Sentry Alerts (DEBT-129 — Novos)

| # | Nome | Condicao | Severidade | Projeto | Status |
|---|------|----------|------------|---------|--------|
| 9 | Circuit Breaker Open | Error message contains "circuit_breaker" AND tag cb_state:open | Critical | smartlic-backend | A configurar |
| 10 | SSE Error Rate High | `smartlic_sse_connection_errors_total` rate > 5/min | Warning | smartlic-backend | A configurar |
| 11 | SSE Error Rate Critical | `smartlic_sse_connection_errors_total` rate > 20/min | Critical | smartlic-backend | A configurar |
| 12 | Response Latency P99 High | Transaction p99 > 10s on `/buscar` | Warning | smartlic-backend | A configurar |
| 13 | Error Rate > 5% | Error rate > 5% of all transactions in 10min | Critical | smartlic-backend | A configurar |

### 1.2b Sentry Alerts (STORY-423 — EPIC-INCIDENT-2026-04-10)

Alert rules complementares que cobrem o ruído e as regressões identificadas
no incidente 2026-04-10. Pré-requisito: canais Slack `#incident-response`
e `#sentry-new-issues` criados + `SENTRY_SLACK_WEBHOOK` setado no Railway.

| # | Nome | Condicao | Destino | Severidade | Projeto |
|---|------|----------|---------|------------|---------|
| 14 | Fatal or Escalating (imediato) | Issue level == `fatal` OR status == `escalating` | Slack `#incident-response` + email tiago.sasaki@gmail.com | Critical | ambos |
| 15 | Burst >100 events/1h (early warning) | Event count > 100 in 1h para qualquer issue | Slack `#sentry-new-issues` | Warning | ambos |
| 16 | New issue em prod (15min agregado) | A new issue is created in `environment:production` | Slack `#sentry-new-issues` (batched 15min) | Info | ambos |

**Setup manual (Sentry UI):**
1. Abrir cada projeto (`smartlic-backend`, `smartlic-frontend`) em
   `Settings → Alerts → Create Alert Rule → Issue Alert`
2. Definir as condições acima.
3. Em `Actions`, usar `Send a notification to a Slack workspace` apontando
   para `SENTRY_SLACK_WEBHOOK` + fallback `Send a notification via email`.
4. Salvar e verificar que o alert dispara enviando um evento de teste via
   `sentry-cli send-event -m 'test fatal'`.

**Checklist pré-deploy:**
- [ ] Canais Slack criados e bot `Sentry Integration` adicionado.
- [ ] `SENTRY_SLACK_WEBHOOK` definido no Railway (`railway variables set ...`).
- [ ] Alert rules 14/15/16 ativas em ambos os projetos.
- [ ] Teste manual disparado e recebido em `#incident-response`.
- [ ] Runbook `docs/runbook/sentry-triage.md` linkado no canal como pinned.

### 1.3 Railway Alerts (Nativos)

| # | Metrica | Threshold Warning | Threshold Critical | Status |
|---|---------|-------------------|-------------------|--------|
| R1 | CPU Usage | > 80% por 5min | > 95% por 2min | A configurar |
| R2 | Memory Usage | > 80% do limite | > 95% do limite | A configurar |
| R3 | Restart Count | > 2 restarts/hora | > 5 restarts/hora | A configurar |

### 1.4 UptimeRobot (Existentes)

| # | Servico | URL | Intervalo | Status |
|---|---------|-----|-----------|--------|
| U1 | Backend Health | `/health` | 5 min | Ativo |
| U2 | Frontend Health | `/api/health` | 5 min | Ativo |
| U3 | Homepage | `smartlic.tech` | 5 min | Ativo |

### 1.5 Roteamento de Alertas (AC6)

| Canal | Alertas | Configuracao |
|-------|---------|-------------|
| Email (tiago.sasaki@gmail.com) | Todos | Sentry + UptimeRobot + Railway |
| Sentry Dashboard | Todos os Sentry alerts | Automatico |
| Railway Dashboard | CPU, Memory, Restarts | Railway native alerts |

**Futuro (quando equipe crescer):**
- Slack channel `#smartlic-alerts` para warning
- Slack channel `#smartlic-critical` para critical (com @here)
- PagerDuty para on-call rotation

---

## 2. Configuracao dos Novos Alertas

### 2.1 Sentry: Circuit Breaker Open (AC1)

**Como configurar:**

1. Acesse https://confenge.sentry.io/alerts/rules/
2. Create Alert > Issue Alert > Project: smartlic-backend
3. Conditions:
   - **When:** An event's message contains "circuit_breaker"
   - **AND:** An event's tags match `cb_state:open`
   - **OR:** An event's message contains "CIRCUIT BREAKER OPEN"
4. Action: Send notification to `IssueOwners` + `ActiveMembers`
5. Frequency: Alert at most once every 5 minutes
6. Name: "Circuit Breaker Open"

**Alternativa via Prometheus (futuro):**
```promql
smartlic_supabase_cb_state > 0
# ou
smartlic_circuit_breaker_degraded{source="pncp"} == 1
```

### 2.2 Sentry: SSE Error Rate (AC2)

**Como configurar:**

1. Create Alert > Metric Alert > Project: smartlic-backend
2. Metric: `count()` where `tags[logger]:progress OR tags[module]:progress`
3. Thresholds:
   - Warning: > 5 events in 1 minute window
   - Critical: > 20 events in 1 minute window
4. Action: Notify IssueOwners
5. Name: "SSE Error Rate High/Critical"

**Alternativa via log filter:**
- Filter issues com tag `logger:progress` ou `module:sse`

### 2.3 Sentry: Response Latency P99 (AC3)

**Como configurar:**

1. Create Alert > Metric Alert > Project: smartlic-backend
2. Metric: `p99(transaction.duration)`
3. Filter: `transaction:/buscar OR transaction:/v1/search`
4. Threshold: Critical when > 10000ms for 5 minutes
5. Action: Notify IssueOwners
6. Name: "Response Latency P99 > 10s"

### 2.4 Sentry: Error Rate > 5% (AC4)

**Ja configurado** como Rule #1 (High Error Rate Alert - Backend, Rule ID 16688768).
Verificar se threshold esta correto (5% of sessions in 5min).

### 2.5 Railway: CPU/Memory Limits (AC5)

**Como configurar:**

1. Acesse Railway Dashboard > Project > Service Settings
2. Em Observability/Alerts (se disponivel no plano):
   - CPU: Alert when > 80% sustained for 5min
   - Memory: Alert when > 80% of container limit
3. **Alternativa:** Monitorar via Prometheus metrics:
   - `smartlic_process_memory_rss_bytes` (exportado pela app)
   - `smartlic_process_memory_peak_rss_bytes`
4. **Sentry custom alert** como fallback:
   - Ja temos `gunicorn_conf.py` que reporta worker timeouts ao Sentry
   - Usar tag `reason:memory_exceeded` para filtrar

---

## 3. Runbooks

### 3.1 Runbook: Circuit Breaker Open (AC10)

**Trigger:** Alerta "Circuit Breaker Open" disparado

**Diagnostico (5 min):**

1. **Verificar qual circuit breaker abriu:**
   ```bash
   # Railway logs filtrados
   railway logs --tail | grep -i "circuit.breaker\|cb_state"
   ```

2. **Verificar estado atual via Prometheus:**
   ```bash
   curl -H "Authorization: Bearer $METRICS_TOKEN" \
     https://bidiq-backend-production.up.railway.app/metrics \
     | grep "circuit_breaker\|cb_state"
   ```
   - `smartlic_supabase_cb_state` — 0=closed, 1=open, 2=half_open
   - `smartlic_circuit_breaker_degraded{source="pncp"}` — 1=degraded

3. **Identificar causa raiz:**
   - Se `supabase_cb_state == 1` (open): Supabase esta indisponivel
   - Se `circuit_breaker_degraded{source="pncp"} == 1`: PNCP API esta fora
   - Se `circuit_breaker_degraded{source="pcp"} == 1`: PCP v2 esta fora
   - Se `circuit_breaker_degraded{source="comprasgov"} == 1`: ComprasGov esta fora

**Acao — Supabase CB Open:**

1. Verificar status do Supabase: https://status.supabase.com/
2. Testar conexao direta:
   ```bash
   railway run python -c "from supabase_client import get_supabase; print(get_supabase().table('profiles').select('count').limit(1).execute())"
   ```
3. Se Supabase esta OK mas CB continua open:
   - CB tem cooldown de 60s — aguardar auto-recovery
   - Se nao recuperar, restart do servico: `railway up`
4. Se Supabase esta DOWN:
   - App continua funcionando com cache (SWR) — degradado mas funcional
   - Monitorar https://status.supabase.com/ para resolucao
   - Comunicar usuarios se downtime > 15min

**Acao — Data Source CB Open (PNCP/PCP/ComprasGov):**

1. A app serve resultados parciais automaticamente (CRIT-053)
2. Verificar se fonte esta realmente fora:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20260301&dataFinal=20260311&tamanhoPagina=10&pagina=1"
   ```
3. CB auto-recover em 60s apos fonte voltar — nao requer intervencao manual
4. Se todas as fontes caem simultaneamente: verificar rede do Railway

**Resolucao:**
- CB auto-recovery e automatico (60s cooldown)
- Verificar que metrica voltou a 0 (closed) apos recuperacao
- Se nao recuperar em 5 min, considerar restart: `railway up`

---

### 3.2 Runbook: High Error Rate (AC11)

**Trigger:** Alerta "Error Rate > 5%" ou "High Error Rate Alert - Backend" disparado

**Diagnostico (5 min):**

1. **Abrir Sentry dashboard:**
   - https://confenge.sentry.io/issues/?project=smartlic-backend
   - Ordenar por "Last Seen" para ver erros mais recentes

2. **Verificar logs Railway:**
   ```bash
   railway logs --tail | grep -i "error\|exception\|traceback" | head -50
   ```

3. **Verificar health endpoint:**
   ```bash
   curl -s https://bidiq-backend-production.up.railway.app/health | python -m json.tool
   ```

4. **Classificar o tipo de erro:**

   | Tipo | Exemplos | Acao |
   |------|----------|------|
   | Transient | Timeout, rate limit, 429, 503 | Monitorar, auto-recovery |
   | Dependency | Supabase down, Redis down, OpenAI down | Ver runbook CB Open |
   | Bug | NullPointer, KeyError, ValidationError | Fix + deploy urgente |
   | Config | Missing env var, bad credentials | Verificar Railway variables |

**Acao por tipo:**

**Transient (timeout/rate limit):**
- Verificar se rate limiting esta muito agressivo
- Verificar se PNCP API esta lenta (metrica `smartlic_fetch_duration_seconds`)
- Normalmente auto-resolve em minutos — monitorar

**Dependency failure:**
- Seguir runbook 3.1 (Circuit Breaker Open) se CB disparou
- Verificar status pages: Supabase, OpenAI, Redis (Upstash)
- App tem fallbacks para todas as dependencias — verificar se estao funcionando

**Bug real:**
- Analisar stack trace no Sentry
- Criar hotfix branch: `git checkout -b fix/issue-description`
- Testar localmente, deploy via `git push` (CI/CD automatico)
- Tempo maximo para hotfix: 2 horas. Se nao resolver, rollback

**Config issue:**
- Verificar env vars: `railway variables`
- Comparar com `.env.example` para vars faltantes
- Fix: `railway variables set KEY=value` + restart

**Resolucao:**
- Verificar que error rate voltou abaixo de 5% no Sentry
- Marcar issues como "Resolved" no Sentry
- Post-mortem se error rate ficou > 5% por mais de 15 minutos

---

### 3.3 Runbook: High Latency (AC12)

**Trigger:** Alerta "Response Latency P99 > 10s" disparado

**Diagnostico (5 min):**

1. **Verificar metricas de latencia:**
   ```bash
   curl -H "Authorization: Bearer $METRICS_TOKEN" \
     https://bidiq-backend-production.up.railway.app/metrics \
     | grep "duration_seconds"
   ```

2. **Identificar gargalo:**

   | Metrica | Valor Normal | Alerta | Causa Provavel |
   |---------|-------------|--------|----------------|
   | `smartlic_search_duration_seconds` p99 | < 30s | > 60s | Pipeline inteiro lento |
   | `smartlic_fetch_duration_seconds{source="pncp"}` | < 10s | > 30s | PNCP API lenta |
   | `smartlic_llm_call_duration_seconds` p99 | < 2s | > 5s | OpenAI API lenta |
   | `smartlic_supabase_execute_duration_seconds` p99 | < 100ms | > 1s | Supabase lenta |
   | `smartlic_search_queue_time_seconds` p99 | < 2s | > 10s | ARQ queue congestionada |

3. **Verificar concorrencia:**
   ```bash
   curl -H "Authorization: Bearer $METRICS_TOKEN" \
     https://bidiq-backend-production.up.railway.app/metrics \
     | grep "active_searches\|active_requests"
   ```

**Acao por gargalo:**

**PNCP API lenta:**
- Verificar se PNCP esta lento para todos ou so para nos (rate limiting)
- Reduzir `PNCP_BATCH_SIZE` temporariamente (5 -> 3)
- Aumentar `PNCP_BATCH_DELAY_S` (2.0 -> 3.0)
- Cache warmup alivia carga: verificar se warming esta rodando

**OpenAI API lenta:**
- Verificar https://status.openai.com/
- Se persistente, considerar:
  - Reduzir `MAX_ZERO_MATCH_ITEMS` para menos classificacoes LLM
  - Temporariamente desabilitar `LLM_ZERO_MATCH_ENABLED=false`
- LLM budget timeout ja protege contra runaway: verificar `smartlic_llm_batch_timeout_total`

**Supabase lenta:**
- Verificar Supabase dashboard para slow queries
- Verificar se connection pool esta saturado (`smartlic_supabase_pool_active_connections`)
- Se saturado: considerar PgBouncer ou reduzir query concurrency

**ARQ queue congestionada:**
- Verificar se worker esta processando: `railway logs --tail | grep "arq\|worker"`
- Se worker travou: restart do worker service
- Se muitos jobs na fila: verificar se buscas estao sendo enfileiradas demais

**Resolucao:**
- Verificar que p99 voltou abaixo de 10s
- Se causado por fonte externa (PNCP, OpenAI), documentar no post-mortem
- Se causado por carga: considerar scaling (ver `capacity-limits.md`)

---

## 4. Procedimentos de Verificacao de Alertas

### 4.1 Verificacao Manual de Alerta (Test Plan)

Para validar que alertas estao funcionando:

1. **Sentry Error Rate Alert:**
   - Disparar erro intencional via endpoint de test (se existir)
   - Ou: monitorar proxima ocorrencia natural e confirmar que email chegou

2. **UptimeRobot:**
   - Ja verificado — emails de DOWN/UP chegam em < 5 min

3. **Circuit Breaker:**
   - Simular CB open temporariamente em staging (se disponivel)
   - Ou: verificar que Sentry captura eventos com tag `cb_state:open` nos logs

4. **Railway (CPU/Memory):**
   - Verificar via Railway dashboard se alertas estao configurados
   - Testar com load test se necessario

### 4.2 Checklist de Verificacao Periodica (Mensal)

- [ ] Todos os alertas Sentry estao ativos (nao desabilitados)
- [ ] UptimeRobot monitors estao ativos
- [ ] Emails de alerta estao chegando (verificar spam)
- [ ] Railway alerts (se configurados) estao ativos
- [ ] Runbooks estao atualizados com informacoes corretas
- [ ] Contatos de alerta estao atualizados

---

## 5. Historico de Alteracoes

| Data | Alteracao | Story |
|------|-----------|-------|
| 2026-03-11 | Documento criado: inventario de alertas + runbooks CB/error rate/latency | DEBT-129 |
| 2026-04-10 | Alert rules 14/15/16 para EPIC-INCIDENT (Fatal/Escalating, Burst, New issue prod) + link para sentry-triage runbook | STORY-423 |
