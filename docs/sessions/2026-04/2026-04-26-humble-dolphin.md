# Session humble-dolphin — 2026-04-26 / 2026-04-27

## Objetivo

Mover sitemap programmatic 0 → ≥1000 `<loc>` em prod (SEO unblock 3 ships).

## Entregue

- **PR #513** ([merged 23:58Z](https://github.com/tjsasakifln/PNCP-poc/pull/513)) — `fix(seo)(seo-020)`: ARG `BACKEND_URL` no `frontend/Dockerfile`. Build env propaga `https://api.smartlic.tech` corretamente (debug log confirma). Build do Railway frontend FALHOU em `/api/badge/stats` por backend overload pós-merge.
- **PR #514** ([open](https://github.com/tjsasakifln/PNCP-poc/pull/514)) — `feat(seo)(seo-021,022)`: FAQPage JSON-LD em landing + audit close SEO-021/022. CI pass. Aguardando merge pós-hotfix.
- **PR #515** ([open](https://github.com/tjsasakifln/PNCP-poc/pull/515)) — `hotfix(incident)`: cache empty stats em DB failure (stops 502 retry storm) + `AbortSignal.timeout(8000)` em `/api/badge/stats` e `estatisticas/page.tsx`. CI pending.

## Incident 2026-04-27 ~00:08Z (~20min)

Build do PR #513 hammered backend. Sintomas: `/api/badge/stats` exit 1 após 60s × 3 retries; `_compute_contratos_stats(uf, municipio_pattern ilike)` em `pncp_supplier_contracts` (2M rows) raised `statement_timeout` 8s; uvicorn worker (`WEB_CONCURRENCY=1`) wedged em DB; `/health` 5-15s timeout 00:09-00:25Z.

Recovery 00:27Z via:
1. `WEB_CONCURRENCY=2` set via Railway MCP (auto-redeploy SUCCESS).
2. Backend `/health` 200 em 1.9s post-restart.

Hotfix #515 previne recorrência (negative cache + abort timeouts).

## Impacto em receita

- **Sitemap-4 ainda 0** em prod — fix técnico correto, mas ciclo deploy bloqueado pelo build fail. Após merge #515 + retrigger frontend build, espera ≥1000 `<loc>` populados (aquisição orgânica destravada).
- Backend down ~20min — pagantes affected (signup/buscar/onboarding indisponível). Recovery 00:27Z.
- Hotfix #515 + bump `WEB_CONCURRENCY` reduzem fragility para próximo build.

## Pendente (dono + prazo)

- [ ] Merge PR #515 hotfix — @devops — quando CI pass (~10min)
- [ ] Re-trigger frontend build (cachebust ou push trivial) — @devops — após #515 deploy
- [ ] Validar `curl https://smartlic.tech/sitemap/4.xml | grep -c "<loc>"` ≥1000 — @qa — pós-rebuild
- [ ] Merge PR #514 (FAQPage) — @devops — após #515 stable
- [ ] Submit GSC sitemap atualizado — @devops — pós-validação
- [ ] Composite index `pncp_supplier_contracts(is_active, uf, lower(municipio))` — @data-engineer — esta semana
- [ ] Investigar warning `./app/api/buscar-progress: Can't resolve 'undici'` — @dev — quando ENG-DEBT janela
- [ ] Agendar `/schedule` agente em 14d para conferir GSC indexação — @devops — pós-merge

## Riscos vivos

- **Sev1 24h**: rebuild frontend pode FALHAR de novo se `_compute_contratos_stats` ainda timeout (cache hotfix mitiga, mas DB query ainda lenta sem index). Backup: revert PR #513 caso loop continue.
- **Sev2 7d**: `WEB_CONCURRENCY=2` em hobby pode aumentar custo do $5 credit. Monitorar Railway billing.
- **Sev3 30d**: composite index pendente — query continua 8s timeout em traffic spike sem fix root.

## Memory updates

- `reference_railway_hobby_plan_actual.md` (criar) — 48 GB RAM/serviço (não 1GB), 5 replicas × 8 GB cada, $5 credit. Suporta `WEB_CONCURRENCY` >1.
- `feedback_build_hammers_backend_cascade.md` (criar) — Frontend build SSG (4146 pages) chama backend → satura workers → DB timeout → retry storm 502 → wedge total. Mitigação: `AbortSignal.timeout` em todos build-time fetch + negative cache em DB failure.
- `reference_compute_contratos_stats_query_lenta.md` (criar) — `pncp_supplier_contracts` ilike `municipio` + sort `data_assinatura` em 2M rows = 8s timeout sem index composto. Pendente: `(is_active, uf, lower(municipio), data_assinatura)`.
