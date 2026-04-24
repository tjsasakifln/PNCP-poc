# Story SEO-013: Index `pncp_raw_bids.orgao_cnpj` (Root Cause Fix)

**Epic:** EPIC-SEO-RECOVERY-2026-Q2
**Priority:** 🔴 P0
**Story Points:** 2 SP
**Owner:** @data-engineer (Dara)
**Status:** Ready

---

## Problem

`pncp_raw_bids` (~1.5M rows) não tem índice em `orgao_cnpj`. Todas queries com predicate `WHERE orgao_cnpj = X` executam seq scan completo. Impacto em produção (logs Railway 2026-04-24):

```
[INFO] GET /v1/orgao/03504182000126/stats -> 404 (397362ms) [req_id=...]
[WARN] DEBT-04 slow_request detected: GET /v1/orgao/03504182000126/stats took 443.2s (threshold=100s) — request will be killed by Railway at 120s
```

Railway mata após 120s, mas worker Gunicorn segura até DB retornar. Em `WEB_CONCURRENCY=2`, 1 query lenta trava 50% da capacidade. Endpoints adjacentes (`/v1/sitemap/cnpjs`, `/health`, `/setores`) timeout em cascata. Frontend ISR fetchers abortam em 15s → `sitemap/4.xml=[]` silenciosamente.

### Evidência empírica

- **Handler afetado:** `backend/routes/orgao_publico.py:204-226` faz `sb.table("pncp_raw_bids").select(...).eq("orgao_cnpj", cnpj).eq("is_active", True).limit(5000).execute()`
- **Handler 2:** `backend/routes/sitemap_cnpjs.py:128-217` fallback paginado faz `sb.table("pncp_raw_bids").select("orgao_cnpj").eq("is_active", True)...range(offset, offset+1000)` — se RPC `get_sitemap_cnpjs_json` não deployed, full scan
- **Índices existentes em `pncp_raw_bids`** (inspeção `supabase/migrations/`): `idx_pncp_raw_bids_fts`, `idx_pncp_raw_bids_uf_date`, `idx_pncp_raw_bids_modalidade`, `idx_pncp_raw_bids_valor`, `idx_pncp_raw_bids_esfera`, `idx_pncp_raw_bids_encerramento`, `idx_pncp_raw_bids_content_hash`, `idx_pncp_raw_bids_ingested_at`, `idx_pncp_raw_bids_dashboard_query (uf, modalidade_id, data_publicacao DESC) WHERE is_active=true`, `idx_pncp_raw_bids_embedding`, `idx_pncp_raw_bids_objeto_trgm`. **Nenhum cobre `orgao_cnpj`.**
- **Contraste:** `pncp_supplier_contracts` TEM `idx_psc_orgao_cnpj` (migração `20260409110000_wave2_contratos_indexes.sql:4`). Provavelmente esquecido em `pncp_raw_bids` no mesmo commit.

### Root Cause

Query plan (esperado via `EXPLAIN ANALYZE`):
```
Seq Scan on pncp_raw_bids  (cost=0.00..~150000.00 rows=N width=... )
  Filter: (orgao_cnpj = 'X' AND is_active = true)
```
Em 1.5M rows + Railway Postgres shared: ~300-500ms por query no melhor cenário, >60s sob concurrency/crawler load.

---

## Acceptance Criteria

- [ ] **AC1** — Migration `supabase/migrations/YYYYMMDDHHMMSS_seo013_index_orgao_cnpj_raw_bids.sql` criada com:
  ```sql
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pncp_raw_bids_orgao_cnpj
    ON public.pncp_raw_bids (orgao_cnpj)
    WHERE is_active = true;
  ```
  **NOTA:** `CONCURRENTLY` incompatível com transações — migration isolada, rodar fora do `supabase db push` padrão OU setar `transaction = false` no cabeçalho da migration conforme padrão do projeto (ver `supabase/migrations/20260408210000_debt01_index_retention.sql` comentário sobre CONCURRENTLY).
- [ ] **AC2** — `.down.sql` pareado com `DROP INDEX CONCURRENTLY IF EXISTS idx_pncp_raw_bids_orgao_cnpj;` (STORY-6.2 policy).
- [ ] **AC3** — Aplicar em prod via `npx supabase db push` (auto-deploy CI) OU manualmente via `psql $SUPABASE_DB_URL -c "CREATE INDEX CONCURRENTLY..."` se CI bloquear CONCURRENTLY.
- [ ] **AC4** — Validação empírica pós-deploy:
  ```sql
  EXPLAIN ANALYZE SELECT orgao_cnpj FROM pncp_raw_bids WHERE orgao_cnpj = '03504182000126' AND is_active = true LIMIT 5000;
  ```
  Plan usa `Index Scan using idx_pncp_raw_bids_orgao_cnpj`, não `Seq Scan`. Tempo execução <50ms.
- [ ] **AC5** — `curl -w "%{time_total}" https://api.smartlic.tech/v1/orgao/03504182000126/stats` retorna em <2s (vs 443s baseline).
- [ ] **AC6** — `curl -w "%{time_total}" https://api.smartlic.tech/v1/sitemap/cnpjs` retorna em <5s com `total >= 1000` no JSON (vs timeout 30s baseline).
- [ ] **AC7** — Prometheus `histogram_quantile(0.95, rate(smartlic_http_duration_seconds_bucket{path="/v1/orgao/{cnpj}/stats"}[5m]))` cai de >100s → <2s após 10min de deploy.
- [ ] **AC8** — Comentário de conclusão no story linkando Grafana snapshot ou output de EXPLAIN ANALYZE pré/pós.

---

## Scope IN

- 1 migration criando `idx_pncp_raw_bids_orgao_cnpj` (partial index WHERE is_active=true)
- 1 `.down.sql` pareado
- Validação de latência via curl + Prometheus
- Comentário documentando ganho

## Scope OUT

- Outros índices faltantes (analisar em story separada se houver)
- Refactor de handlers `/v1/orgao/*/stats` ou `/v1/sitemap/cnpjs` (mantém compatibilidade)
- Aumentar `WEB_CONCURRENCY` (OOM risk — ver STORY-SEO-015 CDN approach)

---

## Implementation Notes

### Passo 1: criar migration

```bash
cd /mnt/d/pncp-poc
TS=$(date -u +%Y%m%d%H%M%S)
cat > "supabase/migrations/${TS}_seo013_index_orgao_cnpj_raw_bids.sql" <<'SQL'
-- STORY-SEO-013: Partial index para pncp_raw_bids.orgao_cnpj (WHERE is_active=true).
-- Root cause de /v1/orgao/{cnpj}/stats levar 443s em prod (seq scan em 1.5M rows).
-- Desbloqueia: /v1/sitemap/cnpjs, /v1/sitemap/orgaos, /v1/sitemap/fornecedores-cnpj — todos
-- timeout em prod por saturação de workers atrelada a este handler lento.
-- pncp_supplier_contracts já tem idx_psc_orgao_cnpj (20260409110000) — paridade histórica.
--
-- CONCURRENTLY é necessário: tabela tem ~1.5M rows ativas e writes constantes (ingestion).
-- Bloqueio exclusivo destruiria SLA. CONCURRENTLY não pode rodar em transação.

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pncp_raw_bids_orgao_cnpj
  ON public.pncp_raw_bids (orgao_cnpj)
  WHERE is_active = true;

COMMENT ON INDEX idx_pncp_raw_bids_orgao_cnpj IS
  'STORY-SEO-013: unblock /v1/orgao/{cnpj}/stats + sitemap cnpjs. Partial (is_active=true) reduz tamanho ~60%.';
SQL

cat > "supabase/migrations/${TS}_seo013_index_orgao_cnpj_raw_bids.down.sql" <<'SQL'
DROP INDEX CONCURRENTLY IF EXISTS public.idx_pncp_raw_bids_orgao_cnpj;
SQL
```

### Passo 2: apply

Se `supabase db push` wrap em transação (migração CONCURRENTLY falha):
```bash
psql "$SUPABASE_DB_URL" -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pncp_raw_bids_orgao_cnpj ON public.pncp_raw_bids (orgao_cnpj) WHERE is_active = true;"
# Registrar manualmente na tabela schema_migrations após success, ou aguardar próximo migration runner idempotente.
```

Alternativa: ver padrão em `20260408210000_debt01_index_retention.sql` (comentário explica CONCURRENTLY sem transação).

### Passo 3: validar

```bash
# Tempo query
psql "$SUPABASE_DB_URL" <<'SQL'
EXPLAIN (ANALYZE, BUFFERS) SELECT orgao_cnpj
FROM pncp_raw_bids
WHERE orgao_cnpj = '03504182000126' AND is_active = true
LIMIT 5000;
SQL

# Endpoint latency
for i in {1..5}; do
  curl -o /dev/null -w "run$i: %{time_total}s HTTP %{http_code}\n" \
    https://api.smartlic.tech/v1/orgao/03504182000126/stats
done

# Sitemap endpoint latency
curl -o /tmp/cnpjs.json -w "HTTP %{http_code} size %{size_download}b time %{time_total}s\n" \
  https://api.smartlic.tech/v1/sitemap/cnpjs
python3 -c "import json; d=json.load(open('/tmp/cnpjs.json')); print('cnpjs count:', len(d.get('cnpjs',[])))"
```

### Risco + mitigação

- **CONCURRENTLY falha em transação:** padrão já conhecido no repo (`20260408210000_debt01_*`). Aplicar via psql direto se CI bloquear.
- **Table write lock durante CREATE:** CONCURRENTLY evita. Writes de ingestion continuam normalmente.
- **Index bloat pós-creation:** monitorar em 7 dias via `pg_stat_user_indexes`; VACUUM ANALYZE já cobre.

---

## Dependencies

- **Pre:** nenhuma (é o root unblocker)
- **Unlocks:** SEO-014, SEO-015, SEO-018 (todos precisam de backend responsivo para validar)

---

## Change Log

| Date | Agent | Action |
|------|-------|--------|
| 2026-04-24 | @sm (River) | Story criada como root cause fix. Evidência empírica: `orgao_publico.py:204` + logs Railway 443s + ausência de idx na migration `20260326000000_datalake_raw_bids.sql`. |
| 2026-04-24 | @po (Pax) | *validate-story-draft 10/10 → GO. Status Draft → Ready. Unblocker P0, sem issues. Pronta para @data-engineer. |
