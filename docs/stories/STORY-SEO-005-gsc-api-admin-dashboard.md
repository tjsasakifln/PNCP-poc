# Story SEO-005: Google Search Console API + Dashboard /admin/seo

**Epic:** EPIC-SEO-2026-04
**Priority:** 🟠 P1
**Story Points:** 8 SP
**Owner:** @dev + @data-engineer
**Status:** Ready
**Audit Ref:** Audit 9.1

---

## Problem

SmartLic está SEO-cego. Página `/admin/seo/page.tsx` existe mas não ingere dados reais do Google Search Console. Toda decisão de SEO é especulativa — não temos medição de:

- Queries impressas (volume, CTR, posição média)
- Pages com "Discovered currently not indexed" (crawl budget waste)
- Soft 404s
- Core Web Vitals p75 reais por page (complementa STORY-SEO-006)
- Cobertura (Valid / Excluded / Error)

**Impacto:** ciclo de iteração SEO é ~30 dias (espera + feeling). Objetivo: reduzir para ~7 dias (dados + ação).

---

## Acceptance Criteria

- [ ] **AC1** — Service account Google Cloud criado com:
  - GSC API habilitada
  - Acesso leitura ao property `sc-domain:smartlic.tech`
  - Credencial JSON armazenada em Railway secret `GSC_SERVICE_ACCOUNT_JSON`

- [ ] **AC2** — Migration Supabase `supabase/migrations/YYYYMMDD_gsc_metrics.sql`:
  ```sql
  CREATE TABLE gsc_metrics (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    query TEXT,
    page TEXT,
    country TEXT DEFAULT 'BRA',
    device TEXT,
    clicks INTEGER NOT NULL,
    impressions INTEGER NOT NULL,
    ctr NUMERIC(5,4),
    position NUMERIC(6,2),
    fetched_at TIMESTAMPTZ DEFAULT now()
  );
  CREATE INDEX idx_gsc_metrics_date ON gsc_metrics(date DESC);
  CREATE INDEX idx_gsc_metrics_page ON gsc_metrics(page);
  CREATE INDEX idx_gsc_metrics_query_gin ON gsc_metrics USING GIN (to_tsvector('portuguese', query));
  ```
  + `.down.sql` (STORY-6.2 EPIC-TD-2026Q2 policy)

- [ ] **AC3** — Job ARQ semanal em `backend/jobs/cron/gsc_sync.py`:
  - Schedule: domingos 03:00 BRT (baixo tráfego)
  - Fetch `searchanalytics.query` últimos 90 dias (API permite 16 meses, começar com 90d)
  - Dimensões: `query`, `page`, `country`, `device`
  - Rate limit: 1200 requests/day GSC API (usar backoff exponencial)
  - Upsert por `(date, query, page, country, device)` (dedupe)
  - Prometheus metric: `smartlic_gsc_sync_duration_seconds`, `smartlic_gsc_sync_rows_upserted_total`
  - Sentry capture em falhas

- [ ] **AC4** — Backend endpoint `GET /v1/admin/seo/summary` (admin-only):
  ```json
  {
    "top_queries": [{"query":"...","impressions":1234,"clicks":56,"ctr":0.045,"position":4.2}, ...],  // top 50
    "top_pages_ctr": [{"page":"...","clicks":..., "ctr": ...}, ...],  // top 50
    "low_ctr_opportunities": [{"page":"...","impressions":...,"ctr":0.008}, ...],  // <1% CTR
    "last_sync_at": "..."
  }
  ```

- [ ] **AC5** — Dashboard `frontend/app/admin/seo/page.tsx` renderiza:
  - 4 cards summary: Total impressões (30d), total cliques, CTR médio, posição média
  - Tabela "Top 50 Queries por Impressões" (sortable)
  - Tabela "Top 50 Pages por CTR" (sortable)
  - Tabela "Oportunidades: Pages com CTR <1%" (acionáveis para otimização)
  - Filtro de data: últimos 7d / 30d / 90d
  - Link "Abrir no GSC" por linha

- [ ] **AC6** — Autorização: endpoint requer `is_admin=true` (reuso de middleware `authorization.py` existente).

- [ ] **AC7** — Test backend: `backend/tests/test_gsc_sync.py` mocka GSC API response + valida upsert correto

---

## Scope IN

- Service account setup + Railway secret (via @devops coordination)
- Migration Supabase gsc_metrics + RLS
- Job ARQ gsc_sync
- Backend endpoint /v1/admin/seo/summary
- Frontend dashboard /admin/seo
- Testes

## Scope OUT

- Web Vitals reais (delegado para STORY-SEO-006)
- Submissão automática de sitemaps via API (nice-to-have, fora do escopo)
- Alert engine para queries caindo de ranking (fase 2)
- Export CSV (fase 2)

---

## Implementation Notes

### Python deps (adicionar em `backend/requirements.txt`)

```
google-api-python-client>=2.120.0
google-auth>=2.30.0
```

### Job ARQ skeleton

```python
# backend/jobs/cron/gsc_sync.py
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json, os

async def gsc_sync_job(ctx):
    creds_json = os.environ['GSC_SERVICE_ACCOUNT_JSON']
    creds = service_account.Credentials.from_service_account_info(
        json.loads(creds_json),
        scopes=['https://www.googleapis.com/auth/webmasters.readonly']
    )
    service = build('searchconsole', 'v1', credentials=creds)

    # Query last 90 days
    body = {
        'startDate': (date.today() - timedelta(days=90)).isoformat(),
        'endDate': date.today().isoformat(),
        'dimensions': ['date', 'query', 'page', 'country', 'device'],
        'rowLimit': 25000,  # max
        # paginate via startRow
    }
    rows = []
    start_row = 0
    while True:
        resp = service.searchanalytics().query(
            siteUrl='sc-domain:smartlic.tech', body={**body, 'startRow': start_row}
        ).execute()
        if not resp.get('rows'): break
        rows.extend(resp['rows'])
        if len(resp['rows']) < 25000: break
        start_row += 25000

    # Bulk upsert Supabase
    await bulk_upsert_gsc_metrics(rows)
```

---

## Files

- `backend/requirements.txt` (add google-api-python-client)
- `backend/jobs/cron/gsc_sync.py` (new)
- `backend/job_queue.py` (register cron schedule)
- `backend/routes/admin_seo.py` (new — endpoint /v1/admin/seo/summary)
- `backend/startup/routes.py` (register router)
- `backend/tests/test_gsc_sync.py` (new)
- `supabase/migrations/YYYYMMDD_gsc_metrics.sql` + `.down.sql` (new)
- `frontend/app/admin/seo/page.tsx` (modify — hoje é stub)
- `frontend/app/admin/seo/_components/QueriesTable.tsx` (new)
- `frontend/app/admin/seo/_components/OpportunitiesTable.tsx` (new)
- `frontend/app/api/admin/seo/route.ts` (proxy to backend)

---

## Dependencies

- **Blockers**: Service account Google Cloud (via @devops) + Supabase migration policy
- **Downstream**: feedback loop para SEO-002/003/004 (saber quais posts CTR <1%)

---

## Risks

| Risk | Mitigation |
|------|-----------|
| GSC API rate limit (1200 req/day) | Sync semanal; cache 7 dias |
| Service account revogado | Reuso do pattern Stripe webhook signature; rotate via @devops |
| PII em query strings | GSC anonimiza; mesmo assim NÃO logar query textual em Sentry |

---

## Success Metrics

- Dashboard mostra dados reais após primeiro sync (domingo seguinte ao deploy)
- CTR médio por template mensurável
- Lista de "pages with <1% CTR" acionáveis identificadas (objetivo: 20-50 oportunidades)
- Ciclo de iteração SEO reduz de 30d → 7d

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-21 | @sm (River) | Story criada a partir do audit SEO 2026-04-21 |
| 2026-04-21 | @po (Pax) | Validação 9.5/10 — GO. Status Draft → Ready |
