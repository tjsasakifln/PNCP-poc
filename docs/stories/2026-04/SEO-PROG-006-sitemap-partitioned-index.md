# SEO-PROG-006: Sitemap particionado + `sitemap_index.xml` (shards ≤45k URLs, Redis cache 1h)

**Priority:** P0
**Effort:** L (5-7 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 2-3 (06–19/mai)
**Sprint Window:** 2026-05-06 → 2026-05-19
**Bloqueado por:** RES-BE-002 (rotas backend sitemap com budget)

---

## Contexto

O `frontend/app/sitemap.ts` atual (786L) implementa **sitemap_index** via Next.js 16 `generateSitemaps()` retornando 5 shards (`id:0` core static, `id:1` setores, `id:2` combos setor×UF, `id:3` blog/conteúdo, `id:4` entities ~10k+ URLs). Cada shard é renderizado por uma única função `sitemap()` switch-case. ISR 1h (`revalidate=3600`) + serialização de fetches (correção SEN-FE-001 pós-incidente 2026-04-21) já estão em produção.

**Problemas para escala 100x (10k → 1M URLs)**:

1. **Cap Google 50k URLs/sitemap.xml.** Atual ~10k em `sitemap/4.xml`; margem ~5x antes de hit. A 1M URLs projetada precisa de **~22 shards** mínimo.
2. **Coupling alto:** todos os shards no mesmo arquivo (786L) com fetch logic, cache layer e route logic misturados. Mudança em uma fonte (e.g., adicionar nova entidade) força re-leitura de 786L.
3. **Cache em memória (module-level let)** persiste entre revalidations no mesmo worker mas não compartilha entre workers/replicas. Multi-replica = N caches independentes = N fetches ao backend.
4. **Sem observabilidade fina por shard.** Tempo de render é Sentry breadcrumb apenas em fail; sem histograma `sitemap_render_seconds{shard}` para alertas SLO.
5. **`sitemap.xml` (sitemap_index gerado por Next) referencia `sitemap/{N}.xml`** (atual). Para escalar, precisamos refatorar para múltiplos route handlers `app/sitemap-{N}.xml/route.ts` (1 file por shard) + um `sitemap_index.xml` controlado.

**Por que P0:** sem este refator, na cardinalidade 100k+ URLs (atingível em 6-9 meses de SEO ramp), shard `id:4` excede 50k cap e Google **drop-out completo do shard** silenciosamente. Memory `feedback_handoff_stale_30h.md`: sitemap pode regenerar sem deploy via ISR, então monitoring + cap proativo é mandatório.

**Por que esforço L (não M):**

- Refator estrutural multi-arquivo (1 file → 6+ route handlers).
- Migração Redis cache layer com fallback in-memory (degradação graceful).
- Backward-compat: `sitemap.xml` (gerado por Next) deve coexistir com `sitemap_index.xml` (custom) durante migração — não pode quebrar GSC submission existente.
- Counter Prometheus + alert rules (Sentry OR Grafana) novos.

---

## Acceptance Criteria

### AC1: Refator multi-arquivo route handlers por shard

**Given** `frontend/app/sitemap.ts` (786L) é monolítico
**When** @dev refatora para route handlers separados
**Then**:

- [ ] Criar arquivo `frontend/app/sitemap_index.xml/route.ts` que retorna XML sitemap_index (referencing N shards):

```ts
import { NextResponse } from 'next/server';

export const revalidate = 3600;

const BASE_URL = process.env.NEXT_PUBLIC_CANONICAL_URL || 'https://smartlic.tech';

const SHARDS = [
  { id: 'core', name: 'core' },
  { id: 'sectors', name: 'sectors' },
  { id: 'combos', name: 'combos' },
  { id: 'content', name: 'content' },
  { id: 'entities-cnpj', name: 'entities-cnpj' },
  { id: 'entities-orgaos', name: 'entities-orgaos' },
  { id: 'entities-itens', name: 'entities-itens' },
  { id: 'entities-municipios', name: 'entities-municipios' },
  { id: 'entities-fornecedores', name: 'entities-fornecedores' },
  { id: 'entities-contratos-orgao', name: 'entities-contratos-orgao' },
];

export async function GET() {
  const lastmod = new Date().toISOString();
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${SHARDS.map(
  (s) => `  <sitemap>
    <loc>${BASE_URL}/sitemap-${s.id}.xml</loc>
    <lastmod>${lastmod}</lastmod>
  </sitemap>`,
).join('\n')}
</sitemapindex>`;
  return new NextResponse(xml, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
    },
  });
}
```

- [ ] Criar route handler por shard: `app/sitemap-{id}.xml/route.ts` para cada um dos 10 shards listados (core, sectors, combos, content, entities-cnpj, entities-orgaos, entities-itens, entities-municipios, entities-fornecedores, entities-contratos-orgao)
- [ ] Cada shard ≤ **45k URLs hard cap** (5k margem do limit Google 50k)
- [ ] Shards de entities particionados por **tipo de entidade** (não por hash) — facilita cache invalidation seletiva e debugging
- [ ] **Backward-compat:** manter `frontend/app/sitemap.ts` original durante migration window — adicionar comentário `@deprecated SEO-PROG-006: usar /sitemap_index.xml`
- [ ] `frontend/public/robots.txt` atualizado para `Sitemap: https://smartlic.tech/sitemap_index.xml` (em vez de `sitemap.xml`) — coordenar com SEO-PROG-007 que substitui robots.txt por route handler

### AC2: Hard cap 45k URLs por shard com particionamento automático

**Given** entidade `entities-cnpj` ultrapassa 45k URLs (top-1000 atual + crescimento)
**When** count(URLs) > 45k em um shard
**Then**:

- [ ] Shard split automático: `entities-cnpj-1.xml`, `entities-cnpj-2.xml`, etc.
- [ ] Pagination via `LIMIT/OFFSET` no fetch backend (`?limit=45000&offset=N`)
- [ ] `SHARDS` array em `sitemap_index.xml/route.ts` regenerado dinamicamente via fetch a `/v1/sitemap/shards-manifest` (TODO @architect: criar endpoint backend que retorna `{shards: [{id, count}]}`)
- [ ] Counter `sitemap_shard_url_count{shard}` exposto Prometheus
- [ ] Alert: shard count > 40k → @qa investiga ramp-up + planeja split antes do limit hit

### AC3: Redis cache layer (substitui module-level `let`)

**Given** atual cache é `let _cnpjCache: string[] = []` no module scope
**When** @dev migra para Redis
**Then**:

- [ ] Cliente Redis frontend: usar `@upstash/redis` (HTTP-based, compatível com edge runtime se aplicável) ou cliente Node.js `ioredis`
- [ ] TODO @architect: confirmar se frontend já tem Redis client (provavelmente não — backend usa Redis); senão, decidir entre `@upstash/redis` (recomendado por ser HTTP-based, menos deps) ou criar follow-up backend endpoint que devolve cached payload já agregado
- [ ] Cache key pattern: `sitemap:shard:{shard_id}:v1` (versioning para invalidation manual)
- [ ] TTL Redis 3600s (alinhado com ISR)
- [ ] Fallback graceful: se Redis indisponível, fetch direto backend + log warning (não fail build/render)
- [ ] **Decisão de arquitetura @architect:** Redis frontend pode introduzir dependency complexity — alternativa é manter Module-level cache + accept multi-worker overhead (já tolerado hoje). Decidir antes de implementar; se mantiver in-memory, ajustar AC para focar em particionamento + observabilidade.

### AC4: Manter serialização anti SEN-FE-001

**Given** memory `project_sitemap_serialize_isr_pattern.md` documenta padrão `await` sequenciais (não Promise.all paralelos) em shard 4
**When** @dev refatora
**Then**:

- [ ] Cada route handler shard que faz múltiplos fetches usa **`await` sequencial** (não Promise.all)
- [ ] Comentário inline:

```ts
// SEN-FE-001 + SEO-PROG-006: 6 fetches paralelos saturavam backend (todos timeoutavam ~30s+)
// → sitemap vazio em produção. Serializados: 5-7s cada, total ~30-45s, dentro do orçamento ISR.
```

- [ ] Cada fetch tem `next: { revalidate: 3600 }` + `AbortSignal.timeout(15000)` (NUNCA `cache: 'no-store'`)
- [ ] Sentry breadcrumb por fetch com tags `{shard, endpoint, latency_ms, outcome}`

### AC5: Observabilidade Prometheus por shard

- [ ] Histograma `sitemap_render_seconds{shard}` (buckets: 0.1, 0.5, 1, 2.5, 5, 10, 30)
- [ ] Counter `sitemap_render_total{shard,outcome}` (outcome=success|error|timeout)
- [ ] Counter `sitemap_shard_url_count{shard}` (gauge — current shard size)
- [ ] Counter `sitemap_redis_cache_hit_total{shard}` (se Redis layer adotado)
- [ ] Counter `sitemap_redis_cache_miss_total{shard}` (se Redis)
- [ ] Sentry breadcrumb por shard render: `tags={shard, latency_ms, url_count, outcome}`
- [ ] Alert SLO: `sitemap_render_seconds{shard, quantile=0.99} > 5` para qualquer shard sustentado 5min

### AC6: Backward-compat + migration window

**Given** GSC já tem `sitemap.xml` submitted (via Next.js auto-gen)
**When** migration deploy
**Then**:

- [ ] **Window 14 dias coexistência:** `sitemap.xml` (Next-gen) + `sitemap_index.xml` (custom) ambos servidos. URLs idênticas em ambos.
- [ ] GSC: submeter `sitemap_index.xml` manualmente (gh-cli ou Playwright MCP) — não remover `sitemap.xml` submitted ainda
- [ ] Após 14 dias + verificação Google está crawleando `sitemap_index.xml` (GSC dashboard "Sitemaps"): remover `frontend/app/sitemap.ts` antigo (delete file)
- [ ] PR description inclui runbook: "post-deploy +14d: remove sitemap.ts" (separar em PR follow-up)

### AC7: Cache alignment audit

- [ ] Zero `cache: 'no-store'` em qualquer `frontend/app/sitemap*.ts` ou `app/sitemap-*/route.ts`
- [ ] Comentário SEN-FE-001 inline em cada fetch
- [ ] Regression test (Jest): novos route handlers verificam que `init.next?.revalidate` é setado, não `init.cache === 'no-store'`

### AC8: Feature flag rollback

- [ ] `SITEMAP_USE_INDEX_VARIANT=legacy` reverte para `sitemap.xml` original
- [ ] Documentar em `frontend/.env.example`
- [ ] Rollback runbook: switch flag + redeploy + GSC re-submit

### AC9: Testes

- [ ] **Unit:** `frontend/__tests__/app/sitemap-index.test.ts`:
  - `sitemap_index.xml` retorna XML válido (parse com `fast-xml-parser` ou similar)
  - Cada shard listado tem `<loc>` válido
  - `<lastmod>` é ISO 8601
- [ ] **Unit:** por shard route handler:
  - Retorna XML válido
  - URLs ≤ 45k cap
  - Filtra noindex (não inclui pares thin)
- [ ] **E2E Playwright:** `frontend/e2e-tests/seo/sitemap-index.spec.ts`:
  - GET `/sitemap_index.xml` → 200 + `application/xml` header
  - Parse XML, verificar 10 shards listados
  - Por shard: GET → 200 + URL count <= 45k
- [ ] **Load test:** simular 10 crawler hits paralelos no `sitemap_index.xml` + cada shard — verificar p99 < 5s (Locust ou k6)

---

## Scope

**IN:**
- Refator multi-arquivo route handlers (1 sitemap_index + N shard files)
- Hard cap 45k URLs/shard com particionamento automático
- Redis cache layer (com fallback graceful) **OU** módule-cache + arch decision @architect
- Manter serialização anti SEN-FE-001
- Prometheus + Sentry per-shard
- Backward-compat 14 dias
- Feature flag `SITEMAP_USE_INDEX_VARIANT`
- Testes unit + E2E + load smoke

**OUT:**
- `robots.ts` (escopo SEO-PROG-007)
- GSC API ingest dashboard (escopo SEO-PROG-013)
- Backend endpoint `/v1/sitemap/shards-manifest` se complexo (criar follow-up backend story se @architect decidir)
- Edge runtime migration (defer; Node runtime é suficiente)
- Cross-region CDN cache (out-of-scope epic level)

---

## Definition of Done

- [ ] `sitemap_index.xml` servido em prod com 10 shards
- [ ] Cada shard route handler retorna XML válido ≤ 45k URLs
- [ ] Counter `sitemap_render_seconds{shard, quantile=0.99} < 5` em prod sob carga normal
- [ ] Counter `sitemap_shard_url_count{shard}` ativo (visibility para próximo split proativo)
- [ ] Redis cache hit rate ≥ 90% (se Redis adotado) **OU** documentação clara de decisão `@architect` se in-memory mantido
- [ ] Backward-compat: `sitemap.xml` (Next-gen) + `sitemap_index.xml` ambos 200 OK
- [ ] GSC re-submit `sitemap_index.xml` manual (Playwright MCP)
- [ ] Bundle delta < +5KB (Redis client pode adicionar peso; verificar)
- [ ] Feature flag em `.env.example`
- [ ] Zero `cache: 'no-store'`
- [ ] Load test p99 <5s em sitemap_index + cada shard sob 10 crawler paralelos
- [ ] CodeRabbit clean
- [ ] PR aprovado @qa + @architect (Aria)
- [ ] Change Log atualizado
- [ ] PR follow-up agendado para +14d: remove `frontend/app/sitemap.ts` legacy

---

## Dev Notes

### Paths absolutos

- **Atual sitemap (legacy):** `/mnt/d/pncp-poc/frontend/app/sitemap.ts` (786L)
- **Novo sitemap_index:** `/mnt/d/pncp-poc/frontend/app/sitemap_index.xml/route.ts`
- **Shards novos:** `/mnt/d/pncp-poc/frontend/app/sitemap-{id}.xml/route.ts` (10 arquivos)
- **Robots.txt atual:** `/mnt/d/pncp-poc/frontend/public/robots.txt` (será movido para `app/robots.ts` em SEO-PROG-007)
- **Backend endpoints sitemap:** `/mnt/d/pncp-poc/backend/routes/sitemap_*.py` (cnpjs, orgaos, itens, municipios, fornecedores-cnpj, contratos-orgao-indexable, licitacoes-indexable, etc.)
- **Tests:** `/mnt/d/pncp-poc/frontend/__tests__/app/sitemap-*` + `/mnt/d/pncp-poc/frontend/e2e-tests/seo/`
- **Memory:** `project_sitemap_serialize_isr_pattern.md`, `feedback_sen_fe_001_recidiva_sitemap.md`

### Padrões existentes a reutilizar

- `fetchSitemapJson` wrapper em `sitemap.ts:17-48` — extrair para `frontend/lib/sitemap-fetch.ts` utility (compartilhar entre shards).
- Per-entity caches (`_cnpjCache`, `_orgaoCache`, etc. em `sitemap.ts:104-181`) — refator para Redis ou per-shard module cache.
- `generateSitemaps()` Next.js API (atual em `sitemap.ts:203-211`) — substituído por route handlers individuais (não usar generateSitemaps na nova arquitetura).

### Architecture decision (@architect — Aria)

**Pergunta-chave:** adotar Redis frontend ou manter in-memory cache?

| Opção | Pros | Cons |
|---|---|---|
| Redis (`@upstash/redis`) | Cache compartilhado multi-worker, invalidation possível | Nova dep frontend (~30KB), config Upstash, latência HTTP |
| In-memory (status quo) | Zero deps, latência 0 | Cache duplicado por worker (Railway hobby = 1 worker, mitigation natural) |
| **Híbrido recomendado** | In-memory L1 (worker-local 60s) + Redis L2 (compartilhado 1h) | Complexity++ |

**Recomendação default:** **In-memory only** enquanto Railway = 1 worker (hobby). Se upgrade para Pro tier (>1 worker) acontecer, migrar para Redis L2 em follow-up. Esta story implementa **in-memory only** com interface de cache plugável (preparação para Redis sem implementar).

### Backend endpoint manifest (TODO follow-up)

`/v1/sitemap/shards-manifest` (proposed):

```json
{
  "shards": [
    {"id": "entities-cnpj", "url_count": 1023, "last_updated": "2026-04-27T12:00:00Z"},
    {"id": "entities-orgaos", "url_count": 2150, "last_updated": "2026-04-27T12:00:00Z"}
    // ...
  ]
}
```

Backend story para implementar este endpoint (escopo separado): consultar `pg_stat_user_tables` ou agregação custom.

### Testing standards

- Mockar fetch + Redis client.
- Load test via Locust: `locust -f load/sitemap_load.py --host=https://staging.smartlic.tech --users=10 --run-time=2m`. Memory `feedback_locust_catch_response.md`: chamar `response.success()` ou `response.failure()` explicitamente.
- E2E parse XML: usar lib `fast-xml-parser` para validar estrutura sitemap_index + sitemap.

### Build OOM

- Route handlers individuais geram XML em runtime (não SSG) → zero impacto em build OOM.
- Bundle frontend: monitorar `.size-limit.js` cap 1.75MB.

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Detecção |
|---|---|---|
| GSC sitemap reads errors | crawler errors >0 | GSC console manual |
| Sitemap render p99 | >10s | Prometheus alert |
| Sitemap shard URL count | >40k qualquer shard | Alert proativo |
| Redis errors (se adotado) | >5/min | Sentry alert |
| GSC clicks total 7d | -30% vs baseline | GSC API |

### Ações

1. Soft: `SITEMAP_USE_INDEX_VARIANT=legacy` + redeploy → reverte para `sitemap.xml` Next-gen.
2. Hard: revert PR via @devops.
3. Cap proativo: ajustar `SITEMAP_SHARD_MAX_URLS=30000` (env) para reduzir density.
4. Redis fallback: feature flag `SITEMAP_USE_REDIS=false` força in-memory.

---

## Dependencies

### Entrada

- RES-BE-002 (backend rotas sitemap com budget)
- SEO-PROG-001 a 005 (entidades populadas via SSG; shards refletem isso)

### Saída

- SEO-PROG-007 (`robots.ts` referencia `sitemap_index.xml`)

### Paralelas

- Pode rodar em paralelo com SEO-PROG-001..005 (mesmo sprint), embora a integração final aconteça após eles estabilizarem.

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO (conditional — observação operacional, não required fix)
**Score:** 8/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: refator partitioned + 45k cap + Redis cache 1h |
| 2 | Complete description | OK | 5 problemas para escala 100x identificados explicitamente |
| 3 | Testable acceptance criteria | PARTIAL | AC1-AC9 testáveis; AC3 contém decisão de arquitetura pendente (Redis vs in-memory) com recomendação default — não bloqueia, mas reduz testabilidade até decisão final |
| 4 | Well-defined scope (IN/OUT) | OK | IN/OUT explícitos; backend manifest endpoint listado como OUT (follow-up) |
| 5 | Dependencies mapped | OK | RES-BE-002 + 001-005 entrada; 007 saída; paralela aceitável |
| 6 | Complexity estimate | OK | Effort L (5-7 dias) consistente com multi-arquivo refator + Redis layer + counter Prometheus + backward-compat 14d |
| 7 | Business value | OK | Vincula a cap Google 50k + escala 100x + memory `feedback_handoff_stale_30h` (regen ortogonal) |
| 8 | Risks documented | OK | 5 triggers; 4 ações rollback (inclui Redis fallback flag) |
| 9 | Criteria of Done | OK | 14 itens incluindo follow-up PR scheduled +14d para delete legacy |
| 10 | Alignment with PRD/Epic | OK | Backward-compat preserva GSC submission; matches epic Validation Framework "Sitemap render time <5s" |

### Observations (não bloqueantes)

- **AC3 (Redis vs in-memory) tem decisão @architect pendente** mas com recomendação default explícita ("In-memory only enquanto Railway = 1 worker"). Aceitável para Ready porque há fallback claro. Score 8 (não 10) por essa indeterminação. Em implementação, @architect deve formalizar decisão antes de @dev iniciar — pode ser via comentário no PR description ou ADR leve.
- **Backward-compat 14 dias** (AC6) é processo crítico e bem documentado — previne CRIT em GSC.
- **AC1 lista 10 shards** (vs ~6 atuais) — particionamento por tipo de entidade facilita debugging vs hash.
- **Hard cap 45k** (5k margem do limit Google 50k) é defesa robusta com proactive alert >40k.
- **Effort L** justificado dado escopo (10 route handlers + cache layer + load test + backward-compat + GSC re-submit).
- Story documenta corretamente o pattern serialização anti SEN-FE-001 (memory `project_sitemap_serialize_isr_pattern.md`).

### Required Fixes

Nenhum — observações são operacionais (resolver decisão @architect durante implementação).

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — refator estrutural multi-shard com 45k cap | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO conditional (8/10). AC3 tem decisão @architect pendente (Redis vs in-memory) com recomendação default — formalizar antes de iniciar dev. Status Draft→Ready. | @po (Pax) |
