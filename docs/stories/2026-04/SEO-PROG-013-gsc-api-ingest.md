# SEO-PROG-013: GSC API ingest diário → Mixpanel + dashboard interno admin

**Priority:** P2
**Effort:** M (3-4 dias)
**Squad:** @dev + @data-engineer
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 6 (03–09/jun)
**Sprint Window:** 2026-06-03 → 2026-06-09
**Bloqueado por:** — (independente)

---

## Contexto

GSC (Google Search Console) é a fonte de verdade para SEO orgânico (clicks, impressions, position, CTR, queries). Atualmente decisões SEO são tomadas via:

- **Manual GSC dashboard checks** (memory `reference_smartlic_baseline_2026_04_24`: 28d 126 clicks, 9.9k impr, CTR 1.3%, pos 7.1)
- **Sem ingest automatizado** = sem cohort analysis, sem alertas, sem cross-validation com Mixpanel

**Problemas**:

1. **Decisões SEO sem dados unificados**: `/cnpj/{X}` está com 50 impressions/dia ou 5? Sem ingest, ninguém sabe sem login GSC.
2. **Sem alertas de regression**: GSC clicks 28d cai 30% silenciosamente entre dashboards manuais.
3. **Cross-validation impossível**: Mixpanel `page_view{route}` vs GSC clicks deveriam alinhar dentro de margem (Mixpanel mede pageviews totais, GSC mede só search-driven). Sem ingest unificado, drift é invisível.
4. **Dashboard interno ausente**: `/admin/seo` não existe. PM/marketing não tem visibility recorrente.

**Por que P2:** SEO-PROG-001..005 (ISR) e bundle reduction são prerequisitos de impacto SEO. Sem rotas indexáveis estáveis, ingestar GSC é prematuro. Após Sprint 5, dados serão signal-rich.

---

## Acceptance Criteria

### AC1: Service account Google + GSC API permissions

**Given** GSC API requer auth via service account
**When** @devops cria
**Then**:

- [ ] Service account criada no GCP project SmartLic
- [ ] Email service account adicionado como **Owner** ou **Restricted user** do property GSC `sc-domain:smartlic.tech`
- [ ] JSON key encrypted at rest, salva em Railway service var `GSC_SERVICE_ACCOUNT_JSON` (single-line JSON)
- [ ] Backend pode autenticar via lib `google-auth` + `google-api-python-client`

### AC2: ARQ cron job diário de ingest

**Given** queremos ingest diário de últimos 28d (rolling window)
**When** @dev cria job
**Then**:

- [ ] Criar `backend/jobs/cron/gsc_ingest.py`:

```python
from arq import cron
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
import os

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
GSC_PROPERTY = 'sc-domain:smartlic.tech'

async def gsc_ingest_job(ctx):
    """
    SEO-PROG-013: Ingest GSC search analytics for last 28 days.
    Saves to gsc_search_analytics table + emits Mixpanel events.
    """
    creds_json = os.environ.get('GSC_SERVICE_ACCOUNT_JSON')
    if not creds_json:
        raise RuntimeError('GSC_SERVICE_ACCOUNT_JSON not set')

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(creds_json),
        scopes=SCOPES,
    )
    service = build('searchconsole', 'v1', credentials=credentials)

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=28)

    # Fetch by URL (paginated)
    rows = []
    start_row = 0
    while True:
        request = {
            'startDate': start_date.isoformat(),
            'endDate': end_date.isoformat(),
            'dimensions': ['page', 'query', 'country'],
            'rowLimit': 25000,
            'startRow': start_row,
        }
        response = service.searchanalytics().query(siteUrl=GSC_PROPERTY, body=request).execute()
        batch = response.get('rows', [])
        if not batch:
            break
        rows.extend(batch)
        start_row += len(batch)
        if len(batch) < 25000:
            break

    # Persist to Supabase
    await persist_gsc_rows(rows, ingestion_date=end_date)

    # Emit Mixpanel events (aggregated by URL)
    await emit_mixpanel_gsc_metrics(rows)

    return {'rows_ingested': len(rows), 'date_range': f'{start_date} to {end_date}'}


WorkerSettings_cron = [
    cron(gsc_ingest_job, hour=4, minute=0),  # Daily 4am UTC (1am BRT)
]
```

- [ ] Registrar cron em `backend/job_queue.py` `WorkerSettings.cron_jobs`
- [ ] Idempotência: tabela `gsc_search_analytics` tem PK `(date, page, query, country)` — UPSERT no conflict
- [ ] Sentry capture em failure + alert se 2 dias consecutivos falham

### AC3: Tabela Supabase `gsc_search_analytics`

**Given** queremos persist + query histórico
**When** @data-engineer cria migration
**Then**:

- [ ] `supabase/migrations/YYYYMMDDHHMMSS_create_gsc_search_analytics.sql`:

```sql
CREATE TABLE public.gsc_search_analytics (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  page TEXT NOT NULL,
  query TEXT NOT NULL DEFAULT '',
  country TEXT NOT NULL DEFAULT '',
  clicks INTEGER NOT NULL DEFAULT 0,
  impressions INTEGER NOT NULL DEFAULT 0,
  ctr NUMERIC(5,4) NOT NULL DEFAULT 0,
  position NUMERIC(5,2) NOT NULL DEFAULT 0,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT gsc_unique UNIQUE (date, page, query, country)
);

CREATE INDEX idx_gsc_date ON public.gsc_search_analytics (date DESC);
CREATE INDEX idx_gsc_page ON public.gsc_search_analytics (page);
CREATE INDEX idx_gsc_clicks ON public.gsc_search_analytics (clicks DESC) WHERE clicks > 0;

-- RLS: only admin can read
ALTER TABLE public.gsc_search_analytics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only" ON public.gsc_search_analytics
  FOR SELECT USING (
    auth.jwt() ->> 'role' = 'service_role'
    OR EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.is_admin = true)
  );
```

- [ ] Paired down migration `*.down.sql` (STORY-6.2)
- [ ] Retention policy: 365 dias (purge via pg_cron) — TODO @data-engineer adicionar separadamente
- [ ] Estimativa volume: ~25k rows/dia × 365 = ~9M rows/ano (manejável com índices)

### AC4: Mixpanel event emit

**Given** queremos cross-validation Mixpanel ↔ GSC
**When** ingest completes
**Then**:

- [ ] Para cada URL com `clicks > 0`, emitir Mixpanel event:

```python
async def emit_mixpanel_gsc_metrics(rows):
    aggregated = {}
    for row in rows:
        keys = row.get('keys', [])
        if len(keys) < 1:
            continue
        page = keys[0]
        if page not in aggregated:
            aggregated[page] = {'clicks': 0, 'impressions': 0}
        aggregated[page]['clicks'] += row.get('clicks', 0)
        aggregated[page]['impressions'] += row.get('impressions', 0)

    for page, metrics in aggregated.items():
        if metrics['clicks'] > 0:
            mixpanel_track('gsc_url_metrics', {
                'page': page,
                'clicks_28d': metrics['clicks'],
                'impressions_28d': metrics['impressions'],
                'ingested_at': datetime.utcnow().isoformat(),
            })
```

- [ ] Memory `reference_mixpanel_backend_token_gap_2026_04_24`: garantir `MIXPANEL_TOKEN` env presente em backend (MON-FN-005 já trata)

### AC5: Backend endpoint dashboard `GET /v1/admin/seo/gsc-summary`

**Given** queremos dashboard frontend admin
**When** @dev cria endpoint
**Then**:

- [ ] Rota `backend/routes/admin_seo.py` (admin-auth required):

```python
@router.get('/v1/admin/seo/gsc-summary')
async def gsc_summary(days: int = 28, current_user = Depends(require_admin)):
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    # Aggregations
    total_clicks = await query_total_clicks(start_date, end_date)
    total_impressions = await query_total_impressions(start_date, end_date)
    avg_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
    avg_position = await query_avg_position(start_date, end_date)

    top_pages = await query_top_pages(start_date, end_date, limit=20)
    top_queries = await query_top_queries(start_date, end_date, limit=50)
    declining_pages = await query_declining_pages(start_date, end_date)  # WoW comparison

    return {
        'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
        'totals': {
            'clicks': total_clicks,
            'impressions': total_impressions,
            'ctr': round(avg_ctr, 4),
            'avg_position': round(avg_position, 2),
        },
        'top_pages': top_pages,
        'top_queries': top_queries,
        'declining_pages': declining_pages,
    }
```

- [ ] `_run_with_budget(5s)` (RES-BE-002 pattern)
- [ ] Cache Redis 1h (`seo:gsc-summary:{days}:v1`)

### AC6: Frontend dashboard `/admin/seo`

**Given** queremos visualizar
**When** @dev cria página
**Then**:

- [ ] Criar `frontend/app/admin/seo/page.tsx` (admin-auth via middleware):
  - KPIs: total clicks 28d, impressions 28d, CTR, avg position (vs prev 28d % delta)
  - Top 20 pages table: page, clicks, impressions, CTR, position
  - Top 50 queries table: query, clicks, impressions, CTR
  - Declining pages alert: pages com -30% clicks WoW
  - Filtro por dias: 7/14/28/90 dropdown
- [ ] Recharts (já tree-shaken em SEO-PROG-009) para timeseries de clicks/impressions
- [ ] Acessibilidade: keyboard nav, contrast WCAG AA

### AC7: Sentry alert: GSC ingest failure

**Given** ingest falhar = invisible até dashboard staleness percebido
**When** ARQ cron falha
**Then**:

- [ ] Sentry `capture_message(level="error")` com fingerprint `["gsc_ingest", reason]`
- [ ] Alert configurado para 2 falhas consecutivas (24h)

### AC8: Testes

- [ ] **Backend unit:** `backend/tests/jobs/test_gsc_ingest.py`:
  - Mock GSC API client (não chamar Google em CI)
  - Verifica UPSERT idempotente
  - Mixpanel emit chamado com keys corretas
- [ ] **Backend integration:** `backend/tests/routes/test_admin_seo.py`:
  - Endpoint requires admin auth
  - Aggregations corretas via fixture data
- [ ] **Frontend unit:** `frontend/__tests__/app/admin/seo-page.test.tsx`:
  - Render KPIs with fixture data
  - Filtro por dias funciona
- [ ] **E2E manual:** após primeiro ingest real, validar dashboard mostra 28d data corretamente

---

## Scope

**IN:**
- Service account GCP + GSC permissions
- ARQ cron diário ingest 28d
- Tabela `gsc_search_analytics` + RLS admin
- Mixpanel event emit aggregated
- Backend endpoint `/v1/admin/seo/gsc-summary`
- Frontend `/admin/seo` dashboard
- Sentry alerts em failure
- Tests unit + integration + manual E2E

**OUT:**
- GSC URL Inspection API (defer; sitemap reconciliation pode ser script ad-hoc)
- Indexing API (out-of-scope; GSC submit manual via Playwright MCP é suficiente)
- Bing Webmaster Tools ingest (defer; cobrir Bing em follow-up se justificado)
- A/B test framework para títulos meta description (defer pre-revenue)
- ML keyword clustering (over-engineering)
- Real-time GSC streaming (não é API supported; daily batch é industry standard)

---

## Definition of Done

- [ ] ARQ cron `gsc_ingest_job` rodando diário 4am UTC, 0 failures em 7 dias
- [ ] Tabela `gsc_search_analytics` populada com 28d × 25k rows = ~700k rows
- [ ] Mixpanel events `gsc_url_metrics` ativos
- [ ] Endpoint `/v1/admin/seo/gsc-summary` retorna 200 OK
- [ ] Frontend `/admin/seo` dashboard funcional + responsive
- [ ] Sentry alert configurado + testado (force fail manualmente)
- [ ] RLS valida não-admin recebe 403
- [ ] Bundle delta < +5KB (Recharts já em frontend)
- [ ] Backend tests + frontend tests passing
- [ ] CodeRabbit clean
- [ ] PR aprovado @qa + @data-engineer + @dev
- [ ] Migration applied + paired down.sql
- [ ] Change Log atualizado
- [ ] Memory atualizada: `reference_gsc_ingest_pattern.md`

---

## Dev Notes

### Paths absolutos

- **Cron job novo:** `/mnt/d/pncp-poc/backend/jobs/cron/gsc_ingest.py`
- **Job queue config:** `/mnt/d/pncp-poc/backend/job_queue.py`
- **Backend route novo:** `/mnt/d/pncp-poc/backend/routes/admin_seo.py`
- **Backend service novo:** `/mnt/d/pncp-poc/backend/services/gsc_query.py`
- **Migration:** `/mnt/d/pncp-poc/supabase/migrations/YYYYMMDDHHMMSS_create_gsc_search_analytics.sql` + `.down.sql`
- **Frontend page:** `/mnt/d/pncp-poc/frontend/app/admin/seo/page.tsx`
- **Backend tests:** `/mnt/d/pncp-poc/backend/tests/jobs/test_gsc_ingest.py`, `tests/routes/test_admin_seo.py`
- **Frontend tests:** `/mnt/d/pncp-poc/frontend/__tests__/app/admin/seo-page.test.tsx`

### Reference

- [Google Search Console API](https://developers.google.com/webmaster-tools/v1/api_reference_index)
- [searchanalytics.query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)
- [Quotas & limits](https://developers.google.com/webmaster-tools/v1/limits) — 1200 queries/min default, OK para diário
- Memory `reference_smartlic_baseline_2026_04_24` (baseline GSC)
- Memory `reference_mixpanel_backend_token_gap_2026_04_24` (MIXPANEL_TOKEN)

### Padrões existentes

- ARQ cron em `backend/jobs/cron/cron_monitor.py`, `pncp_canary.py`, `cleanup_search_cache.py` — replicar pattern
- pg_cron monitoring (CLAUDE.md: "pg_cron Monitoring (STORY-1.1)") — `gsc_ingest_job` se for ARQ-based não usa pg_cron, usa cron monitoring via Sentry
- `_run_with_budget` pattern de RES-BE-002

### Testing standards

- Mockar `googleapiclient.discovery.build` em tests
- Fixture com 100 rows realísticos (page, query, country, clicks, impressions)
- Não chamar Google API em CI (rate limit + auth complexity)
- @data-engineer valida aggregations SQL via dbml ou explain

### Cost considerations

- GSC API: free dentro do quota (1200 queries/min, ~600k requests/day)
- Mixpanel events: free tier 100M events/month — 25k pages × 1 event/day = 750k/month, OK
- Supabase storage: ~9M rows/ano × ~200 bytes = 1.8GB; OK no plan atual

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Detecção |
|---|---|---|
| GSC API rate limit hit | 429 errors | Sentry alert |
| Service account creds rotation expira | auth fail | Sentry |
| Mixpanel events não chegam | dashboard Mixpanel mostra zero | Manual check |
| Dashboard frontend slow | LCP >4s | Lighthouse manual |

### Ações

1. Soft: pause cron `arq cron disable gsc_ingest_job` via Railway shell + investigate.
2. Hard: revert PR via @devops + drop migration.
3. Auth fail: @devops rota credentials.

---

## Dependencies

### Entrada

- MON-FN-005 (MIXPANEL_TOKEN backend assertion ativo)
- RES-BE-002 (`_run_with_budget` pattern disponível)

### Saída

- SEO-PROG decisões futuras informadas por dashboard (reranking analysis, keyword clustering manual)

### Paralelas

- SEO-PROG-014 (CI defer build validation — independente)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: GSC ingest + Mixpanel + dashboard admin |
| 2 | Complete description | OK | 4 problemas claros: decisões sem dados, sem alertas, cross-validation impossível, dashboard ausente |
| 3 | Testable acceptance criteria | OK | AC1-AC8 testáveis; mock GSC API client em CI |
| 4 | Well-defined scope (IN/OUT) | OK | OUT lista 6 itens deferidos: URL Inspection, Indexing API, Bing, A/B framework, ML clustering, real-time |
| 5 | Dependencies mapped | OK | MON-FN-005 (`MIXPANEL_TOKEN`) + RES-BE-002 (`_run_with_budget`) |
| 6 | Complexity estimate | OK | Effort M (3-4 dias) apropriado: cron + table + Mixpanel + endpoint + frontend + Sentry |
| 7 | Business value | OK | Cross-validation Mixpanel ↔ GSC + alertas regression |
| 8 | Risks documented | OK | 4 triggers; auth fail rotation pelo @devops |
| 9 | Criteria of Done | OK | 14 itens incluindo migration + paired down.sql (STORY-6.2 compliance) |
| 10 | Alignment with PRD/Epic | OK | Memory `reference_smartlic_baseline_2026_04_24` (baseline GSC) + `reference_mixpanel_backend_token_gap_2026_04_24` |

### Observations

- AC2 ARQ cron alinhado com pattern existente (`cron_monitor.py`, `pncp_canary.py`) — reuso de infra.
- AC3 RLS admin-only (consistente com `cron_job_health` view pattern) + paired down.sql (STORY-6.2).
- AC5 endpoint com `_run_with_budget(5s)` + cache Redis 1h — defesa robusta.
- AC6 frontend usa Recharts (já em frontend, tree-shaken em SEO-PROG-009) — bundle delta <+5KB.
- Cost analysis (GCP API free tier + Mixpanel free + Supabase storage 1.8GB) é diligente.
- Volume estimate: ~25k rows/dia × 365 = ~9M rows/ano — manejável com índices.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — GSC ingest diário + Mixpanel + admin dashboard | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Reuso de patterns ARQ + RLS + Redis cache. Status Draft→Ready. | @po (Pax) |
