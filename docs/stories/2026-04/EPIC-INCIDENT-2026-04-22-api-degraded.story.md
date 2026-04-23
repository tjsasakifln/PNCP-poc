# STORY-INCIDENT-2026-04-22: api.smartlic.tech intermittent unavailable + sitemap shard timeouts

**Priority:** P0 — Production incident affecting SEO indexation + sitemap generation
**Effort:** Investigation spike (3-5 SP)
**Squad:** @devops + @architect + @data-engineer (review)
**Status:** Draft (open for assignment)
**Discovered:** 2026-04-22 ~16:00 BRT during Wave F sitemap diagnose (generic-sparrow plan)

---

## Symptoms

**Empirical evidence collected 2026-04-22 ~15:00-16:00 BRT:**

| Endpoint | First check | Later check |
|----------|-------------|-------------|
| `https://api.smartlic.tech/health` | HTTP 200 / 1.9s | HTTP 000 / 10s timeout |
| `https://smartlic.tech/sitemap/4.xml` | HTTP 000 / 15s timeout | HTTP 000 / 20s timeout |
| `https://smartlic.tech/sitemap/2.xml` | HTTP 000 / 15s timeout | (untested re-check) |
| `https://smartlic.tech/sitemap/0.xml`, `/1.xml`, `/3.xml` | HTTP 200 / <1s | HTTP 200 / <1s |

**Affected sitemap backend endpoints (all timeout 30s):**
- `/v1/sitemap/licitacoes-indexable` (used by shard 2)
- `/v1/sitemap/contratos-orgao-indexable` (shard 4)
- `/v1/sitemap/cnpjs` (shard 4)
- `/v1/sitemap/orgaos` (shard 4)
- `/v1/sitemap/fornecedores-cnpj` (shard 4)
- `/v1/sitemap/municipios` (shard 4)
- `/v1/sitemap/itens` (shard 4)

**Pattern:**
- Static-only sitemap shards (0, 1, 3) work fast — no backend dependency
- Backend-dependent shards (2, 4) timeout because backend `/v1/sitemap/*` endpoints all hang
- `/health` endpoint also intermittently down

## Hypothesis (NOT verified — investigation needed)

1. **DB queries on sitemap endpoints lack index or hit OOM.** `pncp_supplier_contracts` (~2M rows) + filters likely missing index for the queries used to derive lists.
2. **Connection pool exhaustion.** If sitemap fetches hold connections + crawlers simultaneously, may saturate pool.
3. **Railway pod intermittent failure / OOM kill.** `/health` going from 200 to 000 in <1h points to pod cycling.
4. **Fastly proxy → Railway pod connectivity** (similar to incident reported in `2026-04-22-clever-beaver-handoff.md` "INCIDENT INFRA api.smartlic.tech timeout").

## Investigation steps

### Phase 1 — Confirm scope (≤30min)
- [ ] `railway logs --service bidiq-backend --tail` during a fresh `/health` failure → identify if pod is up
- [ ] `railway logs --service bidiq-backend --filter sitemap` → response times of slow endpoints
- [ ] Run failing endpoint queries directly via `railway run --service bidiq-backend python` → isolate DB vs HTTP layer
- [ ] Check Sentry for spike in 5xx or DB connection errors in last 2h
- [ ] Cross-reference with Stripe/external API rate limits (Resend, OpenAI, Mixpanel)

### Phase 2 — Root cause (1-2h)
- [ ] If DB-layer slow: `EXPLAIN ANALYZE` on each `/v1/sitemap/*` query; identify missing indexes
- [ ] If pod cycling: review Railway autoscaler config + memory limits + recent deploy history
- [ ] If pool exhaustion: review `supabase_client` pool config + circuit breaker state
- [ ] If proxy: test direct Railway URL `bidiq-backend.railway.internal` from frontend pod

### Phase 3 — Fix (variable)
- [ ] DB index strategy: add missing indexes on `pncp_raw_bids(uf, modalidade, data_publicacao)` etc.
- [ ] Caching layer for sitemap endpoints: 1h TTL via Redis or HTTP `Cache-Control`
- [ ] Reduce sitemap shard 4 timeout from 15s → 5s per-fetch + parallelize via `Promise.allSettled` (current code is serialized → 90s worst case)
- [ ] If pod issue: increase memory limit OR optimize hot paths to reduce per-request memory

## Out of scope

- Changing sitemap structure (5 shards by category) — current design is correct
- Implementing CDN cache for sitemaps at Fastly layer (separate optimization story)

## Acceptance Criteria for closure

- [ ] Root cause documented in this story
- [ ] Fix shipped + validated:
  - [ ] `curl https://api.smartlic.tech/health` consistent <2s for 10 consecutive minutes
  - [ ] `curl https://smartlic.tech/sitemap/4.xml` returns 200 with `<url>` count > 1000
  - [ ] `curl https://smartlic.tech/sitemap/2.xml` returns 200 with `<url>` count > 100
- [ ] Sentry alert configured for `/v1/sitemap/*` endpoint p95 > 10s
- [ ] If DB index added: migration paired with `.down.sql` per STORY-6.2
- [ ] GSC sitemap re-submission validated post-fix

## Linked artifacts

- `2026-04-22-clever-beaver-handoff.md` — earlier incident description (sec "INCIDENT INFRA api.smartlic.tech")
- `2026-04-22-mutable-simon-handoff.md` — declared "api.smartlic.tech 100% verde" (15:00 UTC observation, not durable)
- `frontend/app/sitemap.ts` — `fetchSitemapJson` wrapper with 15s timeout + Sentry capture
- `frontend/app/sitemap.xml/route.ts` — shard index handler

## Change Log

| Data | Quem | Mudança |
|------|------|---------|
| 2026-04-22 | @architect (generic-sparrow) | Story criada após Wave F diagnose; backend `/v1/sitemap/*` ALL timeout + `/health` re-degraded; Wave F bloqueada per spike-first decision rule |
