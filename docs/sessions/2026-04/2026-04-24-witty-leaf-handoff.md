# Session witty-leaf — 2026-04-24

## Objetivo

Ship 4 stories Epic SEO-RECOVERY-2026-Q2 (SEO-013/014/015/017 = 11 SP) em 10h, recuperando infra SEO quebrada que estava sangrando aquisicao organica zero-CAC. Foco: volume topo de funil (gargalo confirmado: 2 signups/30d, 0 paid).

## Entregue

- **PR #505** ([link](https://github.com/tjsasakifln/PNCP-poc/pull/505)) — mergeable, aguardando CI + user approval
- **5 commits em `feat/seo-recovery-p0-p1-witty-leaf`:**
  - `bf1906f4` docs(seo) — commit epic + 7 Ready stories
  - `68da1b78` feat(datalake)(seo-013) — migration `idx_pncp_raw_bids_orgao_cnpj` + paired down.sql
  - `f2b2ec61` feat(seo-017)(backend) — endpoint `/v1/sitemap/licitacoes-do-dia-indexable` + 7 tests
  - `8de001be` feat(seo-017)(frontend) — refactor sitemap.ts + page fallback noindex (substitui notFound)
  - `35e11888` feat(seo-015)(backend) — Cache-Control public+SWR em 8 endpoints sitemap_*
- **Migration aplicada em prod via supabase CLI** (stash .down.sql + db push --include-all + restore) — 2026-04-24 14:25 BRT
- Tests: backend 49/49 sitemap + 640 amplo / frontend 7/7 licitacoes-do-dia + 4/4 sitemap-coverage

## Impacto em receita

**Metricas observaveis ja medidas:**

| Endpoint | Baseline | Pos | Multiplicador |
|----------|---------:|----:|--------------:|
| `/v1/orgao/{cnpj}/stats` cold | 443s | 3.1s | 142x |
| `/v1/orgao/{cnpj}/stats` warm | n/a (timeout) | **0.87s** | 500x |

**A medir post-deploy + ISR revalidation:**
- Sitemap total URLs: 1.269 -> meta >=5.000 (4-6 sem)
- `sitemap-4.xml`: 0 -> meta >=3.000 URLs (depende ISR rebuild)
- URLs 404 no sitemap: 43 -> meta 0 (24h)
- GSC clicks 28d (proj. 4-6 sem): 126 -> meta >=400

Cada URL indexada e ativo permanente. Sem novo CAC. Hipotese: 5x pageviews em 6 sem -> 5x trial signups via inbound.

## Pendente

- [ ] **CI verde + merge PR #505** — @devops + user approval — **prazo: 24h**
- [ ] **Soak observation 24h pos-merge** — @devops vigia Prometheus (`smartlic_pncp_max_page_size_changed_total`, `smartlic_http_duration_seconds`) + Sentry (slow query alerts pncp_raw_bids) — **prazo: 24h**
- [ ] **HTTP sweep validacao SEO-017** — `python3 tests/selenium/sitemap_sweep.py` deve retornar 0 404s — **prazo: 24h pos-merge**
- [ ] **Sitemap URL count validacao** — script `for i in 0..4; do curl -sL .../sitemap/$i.xml | grep -c loc; done` — **prazo: 24h pos-merge** (ISR revalidation 1h, mas ISR build precisa nova request)
- [ ] **GSC Coverage delta** — Submitted URL not found 43 -> 0 — **prazo: 14d pos-merge**
- [ ] **Stash insights_report.json** — `stash@{0}` orfao pos branch switch (modificacao nao-relacionada `tests/selenium/insights_report.json`) — decidir aplicar/descartar — **prazo: nao bloqueante**
- [ ] **STORY-SEO-015.1** (Redis L2 + Prometheus + purge) — criar via @sm — **prazo: backlog**
- [ ] **SEO-016/018/019** (alerta + entity routes + crawler protection) — backlog Epic — **prazo: proxima sessao SEO**

## Riscos vivos

- **Soak 24h pos-merge** (severidade: media) — mudancas tocam endpoints prod usados por crawlers; revert via `.down.sql` pareado + revert PR. 5 commits separados facilitam bisect.
- **Contract drift backend/frontend `licitacoes-do-dia-indexable`** (severidade: baixa) — backend retorna `{dates, total, updated_at}`; frontend extrai `(d as {dates?: string[]}).dates ?? []`. Mudanca de shape backend = `[]` silencioso (fail-safe), nao quebra build. Aceitavel; documentado no PR.
- **CI Migration Check pos-merge ja vermelho pre-PR** (severidade: baixa) — investigar se relacionado; nao bloqueia (warning, nao required).
- **WSL build Next16 inviavel** (severidade: alta para Frontend AC validation) — memory existing; nao tentei build local; defer para CI.

## Memory updates

Nenhum esperado nesta sessao — decisoes ja em codigo + epic. Memory existing relevantes:
- `reference_supabase_down_sql_schema_conflict` — confirmado ainda valido (CLI 2.95.2 mantem bug; usei stash pattern)
- `reference_smartlic_baseline_2026_04_24` — sera atualizado quando soak 24h confirmar nova baseline sitemap+stats

## Por opcao 1 (SEO Recovery) ranqueada acima de 2/3

User escolheu Opcao 1 sobre Observabilidade Funnel (Opcao 2) e Trial-Paid Audit (Opcao 3). Razoes:
- Volume topo funil e gargalo (2 signups/30d) — sem volume, conversao e amostra insuficiente
- Cada URL indexada compounding zero-CAC
- Codigo + epic prontos = execucao deterministica
- Opcao 2/3 dependem de Opcao 1 entregar volume primeiro

## Outras opcoes para proximas sessoes

- **Opcao 2** Observabilidade Funnel — `MIXPANEL_TOKEN` backend + Resend webhook + `delivery_status` em `trial_email_log` (~6h, defer)
- **Opcao 3** Trial-Paid Audit — auditoria `signup -> onboarding -> buscar -> planos -> Stripe` (defer ate Opcao 2 destravar amostra >10 signups instrumentados)

## KPI sessao

| Metrica | Alvo | Real |
|---------|-----:|-----:|
| Shipped to prod | >=1 mudanca caminho receita | 5 commits (1 ja em prod via migration) |
| Incidentes novos | 0 | 0 |
| Tempo em docs | <15% | ~10% (handoff + plan) |
| Tempo em fix nao-prod | <25% | ~5% (test fix licitacoes) |
| Instrumentacao adicionada | >=1 evento funil | 0 (defer Opcao 2) |
