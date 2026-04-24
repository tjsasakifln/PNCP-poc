# Story SEO-016: Alerta Ativo em Sitemap URL Count Drop

**Epic:** EPIC-SEO-RECOVERY-2026-Q2
**Priority:** 🟡 P2
**Story Points:** 3 SP
**Owner:** @devops (Gage)
**Status:** Ready
**Depends on:** SEO-015 (backend estável + CDN)

---

## Problem

STORY-SEO-001 AC4+AC5 adicionou:
- Métrica Prometheus `smartlic_sitemap_urls_last{endpoint}` (Gauge) + `..._served_total` (Counter)
- Documentação de alert rules em `docs/seo/sitemap-observability-alerts.md`
- Sentry tag `sitemap_outcome` em `frontend/app/sitemap.ts:32`

**Mas ativação manual no Grafana + Sentry ficou pendente** (AC5 marcou como "cinto+suspensório... @devops ops task"). Resultado: `sitemap/4.xml=0` persistiu dias em produção sem alerta disparar. Memory `reference_smartlic_baseline_2026_04_24` registra como status observado hoje 2026-04-24, confirmando que observabilidade existe mas não alerta.

### Dano

Silent failure de SEO é o pior dos mundos:
- Métrica existe (falsa sensação de observabilidade)
- Gap de indexação custa semanas antes de alguém perceber manualmente
- GSC "Valid pages" drop só é detectado pelo user em retrospectiva

---

## Acceptance Criteria

- [ ] **AC1** — Ativar alertas Grafana/Prometheus conforme `docs/seo/sitemap-observability-alerts.md`:
  - **Warning:** `smartlic_sitemap_urls_last{endpoint=~"cnpjs|orgaos|fornecedores-cnpj"} < 1000` for 15m
  - **Critical:** `smartlic_sitemap_urls_last{endpoint=~".*"} < 10` for 5m
  - **Info:** `rate(smartlic_sitemap_urls_served_total[1h]) == 0` for 2h (endpoint não chamado — possível problema ISR frontend)
- [ ] **AC2** — Ativar Sentry issue alert para `sitemap_outcome IN ('http_error', 'fetch_error')` — dedupe por `sitemap_endpoint` tag, notificar em 1 ocorrência.
- [ ] **AC3** — Teste síntético de alerta: força 1 endpoint sitemap para retornar 0 URLs (ex: via feature flag temporário ou drop index temporário em staging), verificar que alerta dispara em <20min no canal configurado (Slack, email, PagerDuty — o que estiver em uso).
- [ ] **AC4** — Adicionar dashboard Grafana específico "SEO Sitemap Health" com:
  - Gráfico `smartlic_sitemap_urls_last` por endpoint (1h, 24h, 7d)
  - Gráfico `smartlic_sitemap_urls_served_total` rate (requests/h)
  - Gráfico latência p95 dos endpoints `/v1/sitemap/*`
  - Annotation em deploys (se Grafana configurado com webhook de CI)
- [ ] **AC5** — Runbook `docs/runbooks/sitemap-url-drop-alert.md` documenta:
  - Quando disparar acredita no alerta (ex: drop >50% indica incidente real)
  - Passos para diagnosticar (curl endpoints, check Railway logs, check Supabase status)
  - Escalation path (para @dev OR @data-engineer)
  - Como silenciar se false positive (ex: durante migração intencional)
- [ ] **AC6** — Teste de recuperação: disparar alerta (AC3), executar runbook, documentar MTTR em comentário da story.

---

## Scope IN

- Ativação manual de alertas em Grafana + Sentry
- Dashboard novo ou adicional
- Runbook
- Teste end-to-end (alert fires + runbook resolves)

## Scope OUT

- Criar NOVAS métricas (já existem em SEO-001)
- Migração de Grafana/Sentry provider
- Alertas em endpoints NÃO relacionados a sitemap

---

## Implementation Notes

### Passo 1: localizar config existente

```bash
cat /mnt/d/pncp-poc/docs/seo/sitemap-observability-alerts.md
# Referência: STORY-SEO-001 AC5 — documentação já tem thresholds/queries
```

### Passo 2: ativar Grafana

- Se Grafana Cloud: Alert Rules → New → PromQL query + threshold conforme AC1
- Se self-hosted: `grafana.yaml` + reload
- Notification policy: apontar para canal `#seo-alerts` (ou equivalente em uso)

### Passo 3: ativar Sentry

- Sentry Issue Alerts → New Alert:
  - When: `An event is seen`
  - If: `tags.sitemap_outcome equals http_error OR fetch_error`
  - Then: notify via Slack/email
  - Rate limit: 1 notification per issue per hour

### Passo 4: teste

```bash
# Induce failure em staging (NÃO em prod):
# Exemplo: drop index SEO-013 temporário, OU retornar [] mock no endpoint
# Aguardar 20min, verificar que alerta disparou
# Rollback do test change
```

### Passo 5: runbook

Template baseado em runbooks existentes em `docs/runbooks/` (se houver). Senão, estrutura mínima:

```markdown
# Runbook: Sitemap URL Drop Alert

## Quando disparar
`smartlic_sitemap_urls_last{endpoint=X} < threshold`

## Diagnóstico (5min)
1. `curl https://api.smartlic.tech/v1/sitemap/X` — retorna JSON? Quantos items?
2. `railway logs --service bidiq-backend | grep sitemap` — erro recente?
3. Supabase: RPC `get_sitemap_X_json` retornando dados?

## Fix comum
- Backend timeout → investigar saturação (SEO-013 similar)
- RPC missing → aplicar migration
- CDN stale após dados dropados → purge manual

## Escalation
- >30min sem resolver → @data-engineer
- >2h → @pm
```

---

## Métrica de Impacto

| Métrica | Pré | Pós |
|---------|-----|-----|
| MTTD (mean time to detect) sitemap failures | dias | <20min |
| Incidentes de regressão SEO descobertos pelo user | 1/mes+ | 0 |

---

## Dependencies

- **Pre:** SEO-013, SEO-015 (alerta em sistema estável é mais sinal/ruído)
- **Unlocks:** Observabilidade de qualquer futura regressão SEO

---

## Change Log

| Date | Agent | Action |
|------|-------|--------|
| 2026-04-24 | @sm (River) | Story criada. Reconhece que STORY-SEO-001 AC5 documentou mas não ativou — esta story fecha o loop. |
| 2026-04-24 | @po (Pax) | *validate-story-draft 8/10 → GO. Status Draft → Ready. Gap: alert fatigue não abordado — @devops deve considerar rate limit de notificações na Opção Sentry (1/issue/hora). Não blocker. |
