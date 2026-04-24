# Story SEO-015: CDN Cache para `/v1/sitemap/*` (6h TTL)

**Epic:** EPIC-SEO-RECOVERY-2026-Q2
**Priority:** 🟠 P1
**Story Points:** 5 SP
**Owner:** @devops (Gage)
**Status:** Ready
**Depends on:** SEO-013

---

## Problem

Endpoints `/v1/sitemap/*` são chamados por:

1. **Next.js ISR revalidation** (frontend/app/sitemap.ts, revalidate=3600s) — 1x/hora por shard
2. **Google/Bing crawlers diretos** ao inspecionar sitemap.xml → seguirem links indiretos
3. **Health checks / monitoring externo**

A resposta é **estável por horas** (CNPJ list muda ~semanalmente via ingestion diária). Mesmo com SEO-013 fixando latência para <5s, cada hit ainda consome 1 worker Gunicorn por 3-5s.

Com `WEB_CONCURRENCY=2` e múltiplos crawlers batendo simultaneamente (Googlebot parallelism pode atingir 10+ conexões), backend ainda pode saturar — especialmente combinado com load regular de usuários.

### Solução: cache na borda

Cloudflare (se já usado) ou Railway edge cache para `/v1/sitemap/*` com TTL 6h:
- Hit direto no edge → 0 carga backend
- Miss → 1 hit backend / 6h / shard — deminimis
- Stale-while-revalidate para Googlebot nunca ver timeout

---

## Acceptance Criteria

- [ ] **AC1** — Identificar CDN atual (Cloudflare / Railway edge / none). Se ausente: escolher entre (a) adicionar Cloudflare na frente de `api.smartlic.tech`, (b) usar Railway edge se suportado, (c) implementar cache headers + Redis cache layer no backend (menor escopo).
- [ ] **AC2** — Implementar cache com seguintes headers nos endpoints `/v1/sitemap/*`:
  ```
  Cache-Control: public, max-age=21600, stale-while-revalidate=43200, stale-if-error=86400
  ```
  6h fresh, 12h stale-while-revalidate (servir stale + background refresh), 24h stale-if-error (servir stale mesmo se origin 5xx).
- [ ] **AC3** — Adicionar endpoints `/v1/sitemap/cnpjs`, `/v1/sitemap/orgaos`, `/v1/sitemap/fornecedores-cnpj`, `/v1/sitemap/municipios`, `/v1/sitemap/itens`, `/v1/sitemap/contratos-orgao-indexable`, `/v1/sitemap/licitacoes-indexable` na regra de cache (CDN page rule OU `@router` decorator com middleware).
- [ ] **AC4** — Validar cache hit via header response:
  ```bash
  curl -I https://api.smartlic.tech/v1/sitemap/cnpjs | grep -iE 'cache-control|cf-cache-status|x-cache|age'
  ```
  Esperado: `cf-cache-status: HIT` (Cloudflare) OU equivalente após 2ª request.
- [ ] **AC5** — Carga simulada: 100 requests concorrentes a `/v1/sitemap/cnpjs` — todas devem retornar <200ms (cache HIT) exceto primeira (cache MISS <3s pós-SEO-013).
  ```bash
  seq 100 | xargs -P 50 -I{} curl -s -o /dev/null -w "%{time_total}\n" https://api.smartlic.tech/v1/sitemap/cnpjs | sort -n | awk 'END {print "p50:", a[int(NR*.5)]; p95=a[int(NR*.95)]; print "p95:", p95} {a[NR]=$1}'
  ```
- [ ] **AC6** — Prometheus counter `smartlic_sitemap_cdn_cache_hits_total` vs `smartlic_sitemap_backend_requests_total` — ratio hit >=95% após 24h de warmup.
- [ ] **AC7** — Documentar configuração em `docs/infra/cdn-sitemap-cache.md` (ou similar): qual CDN, qual TTL, como purgar, como monitorar.
- [ ] **AC8** — Purge trigger: após ingestion diária (ARQ cron 2am BRT), invalidar cache dos sitemap endpoints para que dados novos apareçam em <24h. Se CDN sem API de purge: aceitar TTL 6h natural.

---

## Scope IN

- Headers Cache-Control corretos nos endpoints backend
- Configuração CDN page rules (ou equivalente)
- Métricas Prometheus hit/miss
- Documentação
- Purge pós-ingestion (se API disponível)

## Scope OUT

- Cache de OUTROS endpoints /v1/* (escopo: só sitemap)
- Migração de CDN provider (usar o que já existe)
- Auth em sitemap endpoints (são públicos por design)

---

## Implementation Notes

### Opção A: Cloudflare (se já em uso)

1. Adicionar Page Rule: URL pattern `api.smartlic.tech/v1/sitemap/*`, Cache Level: Cache Everything, Edge Cache TTL: 6 hours, Browser Cache TTL: 30 minutes.
2. Headers no backend (redundância):
   ```python
   # backend/routes/sitemap_cnpjs.py (e outros)
   @router.get("/sitemap/cnpjs", ...)
   async def sitemap_cnpjs(response: Response):
       response.headers["Cache-Control"] = "public, max-age=21600, stale-while-revalidate=43200, stale-if-error=86400"
       # ... lógica existente
   ```
3. Purge via Cloudflare API:
   ```bash
   curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \
     -H "Authorization: Bearer $CF_API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"files":["https://api.smartlic.tech/v1/sitemap/cnpjs","..."]}'
   ```

### Opção B: Backend-only (se sem CDN)

Adicionar Redis cache layer em `backend/routes/sitemap_*.py` com TTL 6h (handlers já têm InMemory 24h por worker, mas não compartilhado). Redis já disponível no stack (`backend/redis_pool.py`).

Headers Cache-Control ainda importantes para intermediate proxies (ex: CF Workers) e clients.

### Opção C: Railway edge

Verificar se Railway oferece edge cache — se não, fallback Opção B.

### Invalidação

Após `ingestion/scheduler.py` completar crawl diário (2am BRT), chamar purge.
Registrar em ARQ cron `backend/jobs/cron/` ou hook no `loader.py`:

```python
# backend/ingestion/loader.py (após batch complete)
async def on_ingestion_complete():
    # Se Cloudflare configurado:
    await _purge_cloudflare_sitemap_cache()
    # Se Redis-only:
    await _clear_redis_sitemap_keys()
```

---

## Métrica de Impacto Esperada

| Métrica | Pré (baseline + SEO-013) | Pós (com CDN) |
|---------|--------------------------|---------------|
| Requests `/v1/sitemap/*` batendo no backend | ~100-500/h | ~4/h (1/shard/6h) |
| Latência p99 sitemap endpoints | ~3s | <100ms (cache HIT) |
| Worker saturation risk durante crawl burst | Alto | Zero |

---

## Dependencies

- **Pre:** SEO-013 (backend não pode estar timeout permanente mesmo com cache)
- **Unlocks:** SEO-019 (rate limit crawler faz menos sentido se CDN já isola)

---

## Change Log

| Date | Agent | Action |
|------|-------|--------|
| 2026-04-24 | @sm (River) | Story criada. Opção A/B/C abertas — @devops decide conforme CDN atual em uso. |
| 2026-04-24 | @po (Pax) | *validate-story-draft 9/10 → GO. Status Draft → Ready. 3 opções de implementação aceitáveis; @devops decide Opção A vs B vs C no kickoff. Sem blocker. |
