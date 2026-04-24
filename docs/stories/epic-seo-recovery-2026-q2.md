# Epic: SEO Recovery — 10k+ Pages Indexable Pipeline

**Epic ID:** EPIC-SEO-RECOVERY-2026-Q2
**Date:** 2026-04-24
**Owner:** @pm (Morgan)
**Status:** PLANNING
**Depends on:** STORY-SEO-001 (AC1 concluído per memory `reference_railway_backend_url_already_set`)

---

## Problema

Estratégia SEO do SmartLic está quebrada em múltiplas camadas, mesmo após STORY-SEO-001 setar `BACKEND_URL` em Railway frontend. Diagnóstico empírico 2026-04-24:

### Evidências verificadas (prod https://smartlic.tech)

| Métrica | Esperado | Real | Gap |
|---------|----------|------|-----|
| Páginas indexáveis no sitemap | 10.000+ | **1.269** | **-87%** |
| `sitemap/4.xml` (entity pages) URLs | ~10.000 | **0** | **-100%** |
| URLs no sitemap retornando 404 | 0 | **43** (42 /blog/licitacoes-do-dia/* + 1 /observatorio/*) | — |
| Endpoints `/v1/sitemap/*` respondendo | 7/7 | **0/7** (todos timeout 30s) | — |
| Endpoint `/health` backend | 200 | timeout 15s | — |
| Rotas entity em código e 404 em prod | 0 | **5+** (`/observatorio/raio-x-{uf}`, `/municipios/{slug}`, `/orgaos/{slug}`, `/itens/{catmat}`, `/alertas-publicos/{setor}`) | — |
| `/v1/orgao/{cnpj}/stats` latência p99 | <2s | **443s** (logs Railway) | — |

### Root causes (4 ortogonais)

**A. Missing index em `pncp_raw_bids.orgao_cnpj`** — handlers `/v1/orgao/*/stats` e `/v1/sitemap/cnpjs` fazem seq scan 1.5M rows em queries com predicate por `orgao_cnpj`. Explica latência 443s e timeouts em cascata. `pncp_supplier_contracts` tem `idx_psc_orgao_cnpj`; `pncp_raw_bids` não tem equivalente. Comprovado por inspeção de `supabase/migrations/20260326000000_datalake_raw_bids.sql`.

**B. Backend saturação crônica por `WEB_CONCURRENCY=2`** — `backend/start.sh` limita a 2 workers (SLA-002 "Railway 1GB can't sustain 4"). Quando query lenta (#A) trava 1 worker por 443s, 50% da capacidade desaparece. Crawlers + usuários competem pelos workers restantes → `/v1/sitemap/*` timeout no frontend fetcher 15s → `_cnpjCache=[]` → `sitemap/4.xml` vazio.

**C. Silent failure observabilidade** — `frontend/app/sitemap.ts:22-47` captura falhas via Sentry (adicionado em STORY-SEO-001 AC3) mas sem alerta ativo. `sitemap/4.xml=0` persiste dias sem ação. Prometheus counter `smartlic_sitemap_urls_last` existe (AC4) mas sem alert rule em Grafana (AC5 documentado, ativação manual pendente).

**D. SEO ops gaps (404s no sitemap + rotas broken)** — 43 URLs no sitemap/3.xml retornam 404 (datas antigas geradas sem check de dados reais). Rotas entity em `frontend/app/` existem mas sem data source funcional nem entry no sitemap — 404 direto em prod.

---

## Filosofia

**Desbloquear receita orgânica. Sem desinventar.**

SEO orgânico é o canal de aquisição mais barato e escalável para SmartLic (baseline: 126 clicks / 9.9k impressions 28d, CTR 1.3%, position 7.1 per memory `reference_smartlic_baseline_2026_04_24`). Com 87% do long-tail ausente, estamos deixando dinheiro na mesa.

**Regras:**
1. P0 = fix que desbloqueia TUDO (A — 1 migration 1 linha)
2. P1/P2 são independentes entre si após A (paralelizáveis)
3. Sem novas features: só recuperar o que já existe em código
4. Cada story tem métrica mensurável pré/pós

---

## Escopo

### Incluído (7 stories)

| ID | Título | Priority | SP | Owner | Depends on |
|----|--------|----------|----|----|------------|
| STORY-SEO-013 | Index `pncp_raw_bids.orgao_cnpj` (root cause fix) | 🔴 P0 | 2 | @data-engineer | — |
| STORY-SEO-014 | Verify + redeploy sitemap RPCs (get_sitemap_*_json) | 🟠 P1 | 2 | @data-engineer | SEO-013 |
| STORY-SEO-015 | CDN cache `/v1/sitemap/*` 6h (isolar crawlers do backend) | 🟠 P1 | 5 | @devops | SEO-013 |
| STORY-SEO-016 | Alerta Prometheus/Sentry em sitemap URL count drop | 🟡 P2 | 3 | @devops | SEO-015 |
| STORY-SEO-017 | Remover 404s de `/blog/licitacoes-do-dia/*` do sitemap | 🟠 P1 | 2 | @dev | — |
| STORY-SEO-018 | Rotas entity broken: implementar OR noindex+remove | 🟡 P2 | 8 | @dev + @data-engineer | SEO-013 |
| STORY-SEO-019 | Crawler protection: robots Crawl-delay + rate limit Googlebot | 🟡 P2 | 3 | @dev | SEO-015 |

**Total:** 25 SP (~40-50h).

### Excluído

- Criação de NOVAS páginas programáticas (só recuperar as que já existem)
- Content quality em páginas entity (thin content) — separar em epic próprio pós-recovery
- Backlinks/outreach — estratégia off-page fora deste escopo
- Mobile/CWV beyond o que vier naturalmente do fix de latência

---

## Critérios de Sucesso

| Métrica | Baseline (2026-04-24) | Meta | Como medir |
|---------|----------------------|------|------------|
| Total URLs no sitemap | 1.269 | ≥8.000 | `for i in 0 1 2 3 4; do curl -sL https://smartlic.tech/sitemap/$i.xml \| grep -c '<loc>'; done` |
| `sitemap/4.xml` URLs | 0 | ≥5.000 | `curl -sL https://smartlic.tech/sitemap/4.xml \| grep -c '<loc>'` |
| URLs no sitemap retornando 404 | 43 | 0 | HTTP sweep `sitemap_sweep.py` (ver `tests/selenium/`) |
| Rotas entity retornando 404 (não no sitemap) | 5+ | 0 (OR todas noindex documentadas) | `curl -I /observatorio/raio-x-sp /municipios/* /orgaos/* /itens/* /alertas-publicos/*` |
| `/v1/orgao/{cnpj}/stats` p95 | 443s | <1s | Prometheus `smartlic_http_duration_seconds` |
| `/v1/sitemap/*` p95 | timeout (>30s) | <3s | Prometheus |
| GSC "Valid" coverage em 28d | ~150 URLs | ≥1.500 URLs | Google Search Console → Coverage |
| Organic sessions 28d | ~150 | ≥500 (4 semanas pós-deploy) | GA4/GSC |

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Index creation trava tabela 1.5M rows | `CREATE INDEX CONCURRENTLY` (não bloqueia writes) — STORY-SEO-013 AC |
| CDN cache mascara falhas reais do backend | Alertas em STORY-SEO-016 vigiam ambos: origin + edge |
| Rate limit crawler ranqueia pior por parecer lento | Somente Crawl-delay suave (1s) + 429 apenas acima de 100 req/min — STORY-SEO-019 |
| Entity pages implementadas mas com thin content | Scope out dessa epic; próxima epic de content quality |
| Google demora 4-8 semanas pra recrawlear entity pages | Aceitável; submissão manual via GSC acelera — STORY-SEO-014 AC |

---

## Sequência de Execução Recomendada

```
Wave 1 (P0, hoje):           SEO-013 (unblock everything)
Wave 2 (P1, semana 1):       SEO-014 + SEO-015 + SEO-017 (paralelo)
Wave 3 (P2, semana 2):       SEO-016 + SEO-019 (paralelo)
Wave 4 (P2, semana 2-3):     SEO-018 (last; maior — 8 SP)
Wave 5 (monitor, semana 4+): GSC coverage validation (AC nas stories)
```

---

## Change Log

| Date | Agent | Action |
|------|-------|--------|
| 2026-04-24 | @sm (River) | Epic criado a partir de investigação causa raiz (tiago.sasaki, via advisor alignment). Esperado 10k+ pages, real 1269. 4 root causes ortogonais identificados empiricamente. |
