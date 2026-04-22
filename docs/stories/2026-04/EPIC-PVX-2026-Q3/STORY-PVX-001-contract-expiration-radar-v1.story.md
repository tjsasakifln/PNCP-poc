# STORY-PVX-001: Contract Expiration Radar v1 — Backend MVP

**Priority:** P0 — Primeira feature 0-de-6-concorrentes (virgin blue ocean)
**Effort:** S (5 SP, ~4-5h)
**Squad:** @dev + @qa + @data-engineer (review)
**Status:** Draft
**Epic:** [EPIC-PVX-2026-Q3](EPIC.md)
**Source:** PR #476 §8 Brief 1 (research blue-ocean-product-value-extraction.md)

---

## Contexto

PR #476 (research blue ocean product-value extraction, deep-research squad) validou empiricamente que **0 de 6 concorrentes** (Licitanet, ConectaBR, LicitaGov, ConLicitação, Banco de Preços, Effecti) entregam alerta preditivo de sucessão de contratos. Usuários B2G perdem 50-70% do pipeline por não receber esses alertas.

SmartLic tem ~2M contratos históricos em `supplier_contracts` com `data_fim_vigencia` populada — dataset suficiente para predizer janela de publicação de edital sucessor com 60-120 dias de antecedência.

Esta v1 entrega **backend-only MVP** (cron + email + feature flag). Frontend (badge no pipeline + página `/radar/expiracao` + API endpoint) fica para STORY-PVX-001-v2 na sprint 2 (8 SP adicionais).

**Decisão de escopo:** v1 backend-only reduz risco e ship mais defendido. Permite validar:
- Pipeline ETL funciona com volume real
- Cron diário não estoura budget de tempo
- Email engagement (open/click rate) antes de investir em UI completa

---

## Acceptance Criteria

### AC1: Cron diário `contract_expiration_radar` em ARQ
- [ ] Novo job em `backend/jobs/cron/contract_expiration_radar.py`
- [ ] Schedule: daily 06:00 BRT (09:00 UTC) via `WorkerSettings.cron_jobs`
- [ ] Query: `supplier_contracts` WHERE `data_fim_vigencia BETWEEN NOW() + interval '60 days' AND NOW() + interval '120 days'` AND `cnpj_fornecedor IN (user's monitored CNPJs)`
- [ ] Limite de processing: max 1000 alertas por run; budget 60s
- [ ] Prometheus: `smartlic_contract_radar_run_duration_seconds`, `smartlic_contract_radar_alerts_emitted_total{user_id}`

### AC2: Dedup via Redis flag
- [ ] Key: `radar:expiration:emitted:{user_id}:{contrato_id}` com TTL 90 dias
- [ ] Se key existe → skip (não re-emite alerta para mesmo contrato em janela 90d)
- [ ] Se Redis down → log warning + emite (fail-open prefere duplicate alert sobre missed alert)

### AC3: Email Resend com template novo
- [ ] Template `backend/templates/emails/contract_radar_alert.html` (HTML + plaintext fallback)
- [ ] Subject: "🔔 5 contratos expirando em sua watchlist (próximos 120 dias)"
- [ ] Body: lista até 10 contratos com órgão, objeto, valor, data fim vigência, CTA "Ver no SmartLic"
- [ ] Envio via `email_service.py::send_email_resend()` (helper existente)
- [ ] Rate limit: max 1 email/user/dia (mesmo se múltiplos contratos)

### AC4: Feature flag `CONTRACT_EXPIRATION_RADAR_ENABLED`
- [ ] Default: `false` (env var)
- [ ] Override per-user via `profiles.feature_flags->>'contract_expiration_radar'` (JSONB)
- [ ] Cron lê flag global + per-user antes de processar cada user
- [ ] Sem flag = no-op silencioso (log debug, sem email, sem Mixpanel)

### AC5: Server-side analytics emit
- [ ] Evento `radar_expiration_alert_emitted` via `analytics_events.track_funnel_event()`
- [ ] Properties: `user_id`, `contrato_id`, `cnpj_orgao`, `data_fim_vigencia`, `valor_contrato`, `dias_ate_vencimento`
- [ ] Permite medir: alertas emitidos × open rate × CVR para Pro Plus upsell

### AC6: Tests backend ≥ 80% cobertura
- [ ] `backend/tests/test_contract_expiration_radar.py`
  - Unit: cron job seleciona contratos corretos (window 60-120d)
  - Unit: dedup via Redis flag respeitado
  - Unit: email rendering com 0/1/N contratos (Jinja template)
  - Unit: feature flag global off → no-op
  - Unit: feature flag per-user respeitado
  - Unit: rate limit 1 email/user/dia
  - Integration: full cron run com fixture supplier_contracts mockada
- [ ] Coverage validado no CI Backend Tests (PR Gate)

---

## Scope IN

- Pipeline backend completo (cron + query + dedup + email + analytics + feature flag)
- Cobertura: vendor users (não G-Buyer)
- Acurácia target V1: ≥50% alertas dentro da janela prevista — validation passive (sem dashboard accuracy nesta v1; medir via Mixpanel `paywall_hit` rate em users com flag on vs control 90d post-launch)

## Scope OUT (vai para STORY-PVX-001-v2)

- Frontend: badge no pipeline, página `/radar/expiracao`, UI de filtros
- API endpoint público `GET /v1/radar/expiring-contracts`
- Tela de configuração de preferências (frequência, watchlist explícita)
- Webhook push externo (V2)
- Auto-pipeline-inject (V2)
- ML model avançado (V1 é heurística pura: window 60-120d fixo)
- Predição calibrada por órgão (V1 usa janela fixa global; V2 usa média móvel `edital_publicacao - prev_data_fim_vigencia` por órgão)

---

## Dependências

- **Existing:** Tabela `supplier_contracts` populada via DataLake (STORY-1.1+) — disponível em prod
- **Existing:** ARQ worker rodando em Railway service `bidiq-worker` — disponível
- **Existing:** Resend integration via `email_service.py::send_email_resend()` — disponível
- **Existing:** Redis pool via `redis_client.py` — disponível
- **Existing:** Mixpanel server-side via `analytics_events.track_funnel_event` — disponível (consolidado pós-Wave B / PR #480)
- **Existing:** Feature flag via `profiles.feature_flags` JSONB — disponível
- **NONE blocking:** Esta story pode iniciar imediatamente após @po validate

---

## Complexidade

**5 SP** (1 sprint, ~4-5h)

Componentes:
- Cron job + query + dedup: 2 SP
- Email template + send: 1 SP
- Feature flag + analytics: 0.5 SP
- Tests: 1.5 SP

---

## Tier de Pagamento (preview)

V1 ativada apenas para conta interna admin para validar pipeline. Definição de tier (Pro Plus / Enterprise) fica para `STORY-PVX-PRICING-001` na Sprint 3 — não bloqueia esta story.

---

## Arquivos previstos

**Novos:**
- `backend/jobs/cron/contract_expiration_radar.py` (cron job ARQ)
- `backend/services/contract_radar.py` (query + dedup logic)
- `backend/templates/emails/contract_radar_alert.html` (Resend template HTML+plaintext)
- `backend/tests/test_contract_expiration_radar.py` (unit + integration tests)

**Modificados:**
- `backend/jobs/queue/config.py` (registrar cron no `WorkerSettings.cron_jobs`)
- `backend/metrics.py` (+2 Prometheus counters)
- `.env.example` (+ `CONTRACT_EXPIRATION_RADAR_ENABLED=false`)
- `backend/config.py` (load env var)

---

## Riscos & Mitigações

| Risk | Impact | Mitigation |
|------|--------|------------|
| Query de janela 60-120d retorna milhares de contratos para users com pipeline grande | Alto — email spam | Cap 10 contratos por email; rate limit 1 email/user/dia (AC3) |
| Acurácia V1 muito baixa (<30%) | Médio — feature credibility damage | Subject explícito "preview"; medir via Mixpanel CVR antes de promover; v2 com calibração por órgão |
| Cron toma mais que 60s budget em prod | Baixo — alerts atrasados, não missed | Limit 1000 alertas/run + Prometheus alerting se duration > 50s p95 |
| Dedup Redis miss → spam alertas | Baixo — fail-open design | Redis flag check é best-effort; mesmo se falha, rate limit 1 email/user/dia limita blast radius |

---

## Definition of Done

- [ ] Todos AC ✅
- [ ] Tests passando local + CI Backend Tests (PR Gate) verde
- [ ] @qa gate PASS
- [ ] PR mergeado em main via @devops
- [ ] Feature flag ativada APENAS para `tiago.sasaki@gmail.com` em prod (Railway env var ou DB update)
- [ ] Cron executa com sucesso 1× em prod (validar via `railway logs --service bidiq-worker | grep contract_expiration_radar`)
- [ ] Email recebido em conta admin com pelo menos 1 alerta (ou empty no-op log se sem contratos na janela)
- [ ] Mixpanel Live View mostra evento `radar_expiration_alert_emitted` com properties corretas
- [ ] Story file atualizada com `Status: Done` + Change Log entry

---

## Change Log

| Data | Quem | Mudança |
|------|------|---------|
| 2026-04-22 | @sm (River) | Story criada a partir de PR #476 §8 Brief 1; status=Draft |
