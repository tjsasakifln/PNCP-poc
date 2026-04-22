# Sitemap Observability Alerts — STORY-SEO-001 AC5

**Status:** Documented (configuração manual em Sentry + Grafana ou via Terraform pós-STORY-ops-grafana).
**Owner:** @devops

## Contexto

O bug `sitemap/4.xml` vazio em produção (SEO-001) ficou ativo por semanas sem nenhum alerta. Esta doc define as regras de alerta que fecham essa lacuna — cinto (Sentry exceptions) + suspensório (Prometheus gauge threshold).

## Métricas emitidas

Backend (`backend/metrics.py::record_sitemap_count`) emite em todos os 7 endpoints de sitemap:

- **Counter:** `smartlic_sitemap_urls_served_total{endpoint="<name>"}` — soma URLs servidas desde start do worker
- **Gauge:** `smartlic_sitemap_urls_last{endpoint="<name>"}` — última contagem observada

Endpoints instrumentados: `cnpjs`, `fornecedores-cnpj`, `orgaos`, `contratos-orgao-indexable`, `licitacoes-indexable`, `municipios`, `itens`.

Frontend (`frontend/app/sitemap.ts::fetchSitemapJson`) captura via Sentry todas as falhas (`http_error`, `fetch_error`) com tags `sitemap_endpoint` + `sitemap_outcome`.

## Regras de alerta — Grafana (Prometheus)

### Warning: Sitemap shard sub-povoado

```promql
min_over_time(smartlic_sitemap_urls_last{endpoint=~"cnpjs|fornecedores-cnpj|orgaos|contratos-orgao-indexable|licitacoes-indexable|municipios|itens"}[15m]) < 100
```

- **Severity:** warning
- **For:** 15m (evita flapping em deploys)
- **Labels:** `team=seo`, `component=sitemap`
- **Annotations:**
  - `summary`: "Sitemap endpoint `{{ $labels.endpoint }}` servindo menos de 100 URLs"
  - `description`: "Verifique `backend/routes/sitemap_*.py`, `supplier_contracts` table, ingestion job last run. Runbook: `docs/seo/sitemap-observability-alerts.md`"
  - `dashboard`: link para dashboard Grafana "Sitemap Health"

### Critical: Sitemap shard quase vazio

```promql
min_over_time(smartlic_sitemap_urls_last{endpoint=~"cnpjs|fornecedores-cnpj|orgaos|contratos-orgao-indexable|licitacoes-indexable|municipios|itens"}[15m]) < 10
```

- **Severity:** critical
- **For:** 5m
- **Labels:** `team=seo`, `component=sitemap`, `page=true` (pager)
- **Annotations:**
  - `summary`: "Sitemap endpoint `{{ $labels.endpoint }}` quase vazio — revenue SEO em risco"
  - `description`: "Googlebot vai parar de indexar entity pages. Action: checar DataLake (`pncp_raw_bids` / `supplier_contracts`), backend deploy health, frontend BACKEND_URL env. Runbook: `docs/seo/sitemap-observability-alerts.md`"
  - `playbook`: "`railway logs --service bidiq-backend | grep sitemap`; `curl https://api.smartlic.tech/metrics | grep smartlic_sitemap_urls_last`"

## Regras de alerta — Sentry

### Sentry alert: Exceções em sitemap.ts

- **Trigger:** `event.tags['sitemap_outcome'] IN ['http_error', 'fetch_error']`
- **Threshold:** 5 eventos em 10 minutos
- **Action:** Slack `#ops-seo` + email `tiago.sasaki@gmail.com`
- **Fingerprint:** `["sitemap", "{sitemap_endpoint}", "{sitemap_outcome}"]` (dedup por endpoint + outcome)
- **Environment:** `production`

### Sentry alert: Silêncio de sitemap_urls_served_total

Complemento ao gauge: se o endpoint `/metrics` continua respondendo mas `smartlic_sitemap_urls_served_total` para de incrementar por 1h, indica que os crawlers não estão batendo no sitemap (pode ser DNS, CDN, ou worker morto).

- **Trigger:** `rate(smartlic_sitemap_urls_served_total[1h]) == 0`
- **Severity:** warning
- **For:** 1h

## Setup manual checklist

- [ ] Grafana: criar dashboard "Sitemap Health" com panels para `smartlic_sitemap_urls_last` por endpoint (gauge + timeseries)
- [ ] Grafana: importar as 2 regras acima (Warning + Critical) via UI ou provisioning YAML
- [ ] Sentry: criar alert rule via Issue Alert → Conditions → Tags match
- [ ] Slack: conectar channel `#ops-seo` com Grafana + Sentry webhooks
- [ ] Runbook link: apontar annotations para este arquivo

## Observação — Gauge em multi-worker

Prometheus `Gauge` em ambiente multi-worker (Gunicorn) usa valor da ÚLTIMA request atendida por worker. Para métricas de crawler (baixa frequência, poucas requests/min), isso é suficiente. Se virar problema, migrar para `multiproc_dir` do prometheus_client ou usar Counter.rate() como proxy.

## Validação

Após configurar, simular alerta:

```bash
# Force um sitemap endpoint a retornar 0 (dev only — NÃO em prod!)
# Exemplo: temporariamente renomeie a tabela no Supabase staging
# Ou: rode ingestion_purge sem corresponding crawl
```

Alert warning deve disparar em ≤15m. Critical em ≤5m.

## Related

- `backend/metrics.py` — `record_sitemap_count`
- `frontend/app/sitemap.ts` — `fetchSitemapJson`
- `docs/stories/STORY-SEO-001-fix-sitemap-shard-4-empty.md` — AC5 origem
- `frontend/__tests__/sitemap-coverage.test.ts` — AC7 E2E guard
