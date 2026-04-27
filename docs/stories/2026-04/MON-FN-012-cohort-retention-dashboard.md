# MON-FN-012: Cohort Retention Dashboard (W1/W4/W12)

**Priority:** P2
**Effort:** M (3-4 dias)
**Squad:** @data-engineer + @analyst
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 6 (03–09/jun)
**Sprint Window:** Sprint 6 (depende de MON-FN-006)
**Dependências bloqueadoras:** MON-FN-006 (eventos funil + audit DB de 90d)

---

## Contexto

Após MON-FN-006 instrumentar 12 eventos do funil + tabela `analytics_events` com retention 90d, ficamos com **fonte de dados limpa** para análise de retention. Hoje SmartLic não tem visibilidade de:
- Que % de signups da semana X ainda estão ativos em W1, W4, W12?
- Diferenças de cohort por canal (organic vs direct vs referral)?
- Segment retention por plan_type (trial → free → paid)?

Padrão Fortune-500 / B2B SaaS: **cohort retention curve** é métrica north-star de product-market fit. Sem ela, decisões editoriais SEO (EPIC B) e de produto são especulativas.

Cross-reference plano (`MON-FN-012`): "Dashboard SQL+Metabase: cohort signup mensal × retention W1/W4/W12; integra com STORY-OBS-001 retention 400d."

**Importante:** STORY-OBS-001 já elevou retention de `pncp_raw_bids` para 400d (memory `project_smartlic_onpage_pivot_2026_04_26`). Tabela `analytics_events` (MON-FN-006) tem retention 90d — suficiente para W1/W4/W12 (12 weeks = 84d, dentro de 90d window).

**Por que P2:** não bloqueia funcionalidade end-user; é instrumentação analytics. Mas necessário antes de qualquer decisão de pricing/plan structure pós-n≥30 (EPIC out-of-scope explicitamente).

**Paths críticos:**
- `supabase/migrations/` (view materializada `cohort_retention_weekly`)
- `backend/routes/admin.py` ou novo `routes/admin_dashboards.py` (endpoint expor data)
- Metabase external integration (SQL queries) — alternativa: dashboard frontend admin

---

## Acceptance Criteria

### AC1: Materialized view `cohort_retention_weekly`

Given `analytics_events` table de MON-FN-006 e `profiles.created_at`,
When view materializada criada,
Then provê data de cohort signup × week × retention rate.

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_create_cohort_retention_view.sql`:
```sql
CREATE MATERIALIZED VIEW public.cohort_retention_weekly AS
WITH cohorts AS (
  SELECT
    DATE_TRUNC('week', p.created_at) AS cohort_week,
    p.id AS user_id,
    p.created_at AS signup_at,
    COALESCE(p.plan_type, 'unknown') AS initial_plan_type,
    p.first_search_at,
    p.deleted_at
  FROM public.profiles p
  WHERE p.created_at >= now() - interval '90 days'
    AND p.deleted_at IS NULL
),
weekly_activity AS (
  SELECT
    user_id,
    DATE_TRUNC('week', occurred_at) AS active_week
  FROM public.analytics_events
  WHERE event_name IN ('first_search', 'paywall_hit', 'checkout_started', 'trial_converted')
    AND occurred_at >= now() - interval '90 days'
  GROUP BY user_id, DATE_TRUNC('week', occurred_at)
)
SELECT
  c.cohort_week,
  COUNT(DISTINCT c.user_id) AS cohort_size,
  COUNT(DISTINCT CASE
    WHEN wa.active_week = c.cohort_week + interval '1 week' THEN c.user_id
  END) AS retained_w1,
  COUNT(DISTINCT CASE
    WHEN wa.active_week = c.cohort_week + interval '4 weeks' THEN c.user_id
  END) AS retained_w4,
  COUNT(DISTINCT CASE
    WHEN wa.active_week = c.cohort_week + interval '12 weeks' THEN c.user_id
  END) AS retained_w12,
  ROUND(
    100.0 * COUNT(DISTINCT CASE WHEN wa.active_week = c.cohort_week + interval '1 week' THEN c.user_id END) /
    NULLIF(COUNT(DISTINCT c.user_id), 0),
    2
  ) AS retention_rate_w1,
  ROUND(
    100.0 * COUNT(DISTINCT CASE WHEN wa.active_week = c.cohort_week + interval '4 weeks' THEN c.user_id END) /
    NULLIF(COUNT(DISTINCT c.user_id), 0),
    2
  ) AS retention_rate_w4,
  ROUND(
    100.0 * COUNT(DISTINCT CASE WHEN wa.active_week = c.cohort_week + interval '12 weeks' THEN c.user_id END) /
    NULLIF(COUNT(DISTINCT c.user_id), 0),
    2
  ) AS retention_rate_w12,
  now() AS calculated_at
FROM cohorts c
LEFT JOIN weekly_activity wa ON wa.user_id = c.user_id
GROUP BY c.cohort_week
ORDER BY c.cohort_week DESC;

CREATE UNIQUE INDEX idx_cohort_retention_weekly_cohort ON public.cohort_retention_weekly (cohort_week);

-- Refresh schedule: daily at 13 UTC
SELECT cron.schedule('refresh-cohort-retention-weekly',
  '0 13 * * *',
  $$REFRESH MATERIALIZED VIEW CONCURRENTLY public.cohort_retention_weekly$$);
```
- [ ] Migration paired down `.down.sql` (DROP MATERIALIZED VIEW + cron unschedule)
- [ ] Refresh CONCURRENTLY (não bloqueia leitores) — requer índice único
- [ ] STORY-1.1 pg_cron monitor cobre este cron automatically

### AC2: View segmentada por plan_type e canal

Given que cohorts têm múltiplas dimensões,
When view criada,
Then permite slice por plan_type inicial.

- [ ] Migration adicional: `cohort_retention_weekly_by_plan`:
```sql
CREATE MATERIALIZED VIEW public.cohort_retention_weekly_by_plan AS
-- Same as AC1 but GROUP BY (cohort_week, initial_plan_type)
... ;
```
- [ ] View `cohort_retention_weekly_by_channel` se atribuição funcionar (`profiles.signup_source` se existir; senão skip)
- [ ] Refresh juntamente

### AC3: RPC `get_cohort_retention(weeks_back int)` (admin-only)

Given que dashboard precisa fetchar dados,
When RPC chamada,
Then retorna JSON estruturado.

- [ ] SQL function:
```sql
CREATE OR REPLACE FUNCTION public.get_cohort_retention(weeks_back int DEFAULT 12)
RETURNS jsonb
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
DECLARE
  result jsonb;
BEGIN
  -- Authz check (admin only)
  IF NOT EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid() AND (is_admin OR is_master)
  ) THEN
    RAISE EXCEPTION 'forbidden';
  END IF;

  SELECT jsonb_agg(row_to_json(c.*)) INTO result
  FROM public.cohort_retention_weekly c
  WHERE cohort_week >= now() - (weeks_back || ' weeks')::interval
  ORDER BY cohort_week DESC;

  RETURN COALESCE(result, '[]'::jsonb);
END;
$$;

GRANT EXECUTE ON FUNCTION public.get_cohort_retention(int) TO authenticated;
```

### AC4: Endpoint `GET /v1/admin/dashboards/cohort-retention`

Given admin autenticado,
When request,
Then JSON do RPC.

- [ ] Em `backend/routes/admin.py` ou novo módulo:
```python
@router.get("/v1/admin/dashboards/cohort-retention")
async def cohort_retention(
    weeks_back: int = Query(12, ge=1, le=52),
    user: User = Depends(require_admin),
):
    sb = get_supabase()
    result = sb.rpc("get_cohort_retention", {"weeks_back": weeks_back}).execute()
    return {"data": result.data, "calculated_at": datetime.now(timezone.utc).isoformat()}

@router.get("/v1/admin/dashboards/cohort-retention/by-plan")
async def cohort_retention_by_plan(
    weeks_back: int = Query(12, ge=1, le=52),
    user: User = Depends(require_admin),
):
    sb = get_supabase()
    result = sb.rpc("get_cohort_retention_by_plan", {"weeks_back": weeks_back}).execute()
    return {"data": result.data}
```

### AC5: Frontend dashboard `/admin/dashboards/cohort`

Given admin acessa,
When página carrega,
Then mostra cohort table + heatmap visual.

- [ ] `frontend/app/admin/dashboards/cohort/page.tsx`:
  - Table: rows = cohort_week, columns = W1, W4, W12, com células coloridas (heatmap green→red)
  - Recharts ou D3 simple heatmap
  - Filter por plan_type (smartlic_free, free_trial, smartlic_pro, smartlic_consultoria)
  - Export CSV button
- [ ] Server-side render protected: redirect se !is_admin
- [ ] Loading state + error state
- [ ] Mobile-friendly fallback (table compacta)

### AC6: Métricas de qualidade do dado

Given que dados podem ter gaps,
When dashboard exibe,
Then sinaliza data quality.

- [ ] Counter `smartlic_cohort_view_refresh_total` (incrementa em refresh)
- [ ] Counter `smartlic_cohort_view_refresh_failed_total` (Sentry capture em refresh fail)
- [ ] Header dashboard: "Última atualização: {calculated_at}" + "Próxima atualização: 13 UTC"
- [ ] Cohort com `cohort_size < 5` flag visual "n insuficiente" (memory `feedback_n2_below_noise_eng_theater`)

### AC7: Documentação metodológica

Given que retention pode ser definida de várias formas,
When time interpreta,
Then documentação explicit.

- [ ] Doc `docs/dashboards/cohort-retention.md`:
  - Definição "active": user emitiu pelo menos 1 evento `first_search|paywall_hit|checkout_started|trial_converted` na semana X
  - W1 = 1 semana após cohort signup
  - W4 = 4 semanas após
  - W12 = 12 semanas após
  - Cohort size minimum: 5 (abaixo, não exibir % por noise)
  - Refresh: daily 13 UTC
  - Storage: materialized view (refresh-on-demand não permitido — performance)
  - Compliance: dashboard só admin; user data anonimizada por default (apenas counts)

### AC8: Testes

- [ ] Unit `backend/tests/admin/test_cohort_retention.py`:
  - [ ] RPC retorna data válido
  - [ ] RPC com user não-admin → 403 (auth check)
  - [ ] Endpoint admin requer auth
- [ ] Integration `backend/tests/database/test_cohort_view.py`:
  - [ ] Seed 100 fake users com timestamps + analytics_events
  - [ ] REFRESH view → data correta
  - [ ] Edge case: cohort com 0 retained → retention_rate 0%, não NaN
  - [ ] Edge case: cohort_size 1 → flagged como n-insuficiente
- [ ] Frontend `frontend/__tests__/admin/cohort.test.tsx`:
  - [ ] Render heatmap com mock data
  - [ ] Filter por plan_type funciona
  - [ ] Export CSV download válido
- [ ] E2E (manual): admin loga + navega `/admin/dashboards/cohort` → dados visíveis
- [ ] Cobertura ≥85%

---

## Scope

**IN:**
- Materialized view `cohort_retention_weekly` + by_plan
- Refresh daily 13 UTC via pg_cron
- RPC + endpoint admin
- Frontend dashboard com heatmap
- Métricas de refresh quality
- Docs metodológicos

**OUT:**
- Real-time retention (over-engineering — daily refresh suficiente)
- Predictive churn ML model
- Custom cohort definitions (apenas weekly; daily/monthly defer)
- Multi-tenant slicing (single-tenant SmartLic)
- Export para BI externo (BigQuery, Tableau) — futuro
- Drill-down per user (cohort aggregates only; PII protection)

---

## Definition of Done

- [ ] Migration aplicada (view + cron)
- [ ] View refresh executando daily (validar via `cron_job_health`)
- [ ] Endpoint `/v1/admin/dashboards/cohort-retention` retorna JSON válido
- [ ] Frontend `/admin/dashboards/cohort` renderiza heatmap
- [ ] Cobertura ≥85%
- [ ] CodeRabbit clean
- [ ] Doc metodológico publicado
- [ ] Smoke test em staging: seed 50 users + events + view refresh → assert retention_rate calculado corretamente
- [ ] Sentry alert configurado em refresh failure
- [ ] Memory existente `reference_smartlic_baseline_2026_04_24` atualizada com cohort metric baseline (W1: x%, W4: y%)

---

## Dev Notes

### Padrões existentes a reutilizar

- **Materialized view + pg_cron:** STORY-1.1 (cron monitoring) cobre automatically
- **`require_admin`:** existing auth dependency
- **Heatmap:** Recharts ou react-heatmap-grid (verificar `frontend/package.json` deps)
- **`analytics_events` table:** MON-FN-006 (90d retention)

### Funções afetadas

- `supabase/migrations/YYYYMMDDHHMMSS_create_cohort_retention_view.sql` + `.down.sql`
- `backend/routes/admin.py` (novos endpoints) ou `routes/admin_dashboards.py` (NOVO)
- `frontend/app/admin/dashboards/cohort/page.tsx` (NOVO)
- `frontend/app/admin/dashboards/cohort/CohortHeatmap.tsx` (NOVO)
- `backend/metrics.py` (counters)
- `docs/dashboards/cohort-retention.md` (NOVO)

### Trade-off: Materialized View vs ad-hoc query

- Materialized view: refresh barato, query rápida, idempotente
- Ad-hoc: sempre fresh mas 50K-2M rows aggregation = timeout possível
- Decisão: materialized + daily refresh = correct trade-off

### Sample data seed para testing

`backend/tests/fixtures/cohort_seed.sql`:
```sql
-- 10 users signing up week N (n=10 cohort)
-- 5 users active in week N+1 (50% W1 retention)
-- 2 users active in week N+4 (20% W4)
-- 1 user active in week N+12 (10% W12)
INSERT INTO profiles (id, created_at) VALUES ...;
INSERT INTO analytics_events (user_id, event_name, occurred_at) VALUES ...;
```

### Testing Standards

- pytest + Supabase test client
- Frontend: Jest + Testing Library
- E2E: Playwright manual smoke
- Anti-hang: pytest-timeout 30s

---

## Risk & Rollback

### Triggers de rollback
- View refresh > 60s (data growth supera capacity)
- pg_cron schedule miss (STORY-1.1 alerta)
- Dashboard render lento (>5s) — view índices

### Ações de rollback
1. **Imediato:** drop matview via down.sql; endpoint retorna 503
2. **Cron-only:** `cron.unschedule('refresh-cohort-retention-weekly')` — view fica stale
3. **Communication:** dashboard mostra "dados não disponíveis"

### Compliance
- Dashboard admin-only (no user PII exposure)
- Retention 90d alinhada com `analytics_events`
- LGPD: cohort aggregations não são PII (counts only)

---

## Dependencies

### Entrada
- **MON-FN-006** (eventos funil): `analytics_events` populated
- STORY-OBS-001 (retention 400d): pattern já estabelecido
- STORY-1.1 (pg_cron monitoring): refresh visibility

### Saída
- **MON-FN-013** (ARPU/MRR): mesmas tabelas, dashboards complementares
- Decisões pricing pós-n≥30: cohort retention é input crítico

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 9/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "Cohort Retention Dashboard (W1/W4/W12)" — janelas explícitas |
| 2 | Complete description | Y | Cohort = north-star de PMF; cita STORY-OBS-001 retention 400d |
| 3 | Testable acceptance criteria | Y | 8 ACs incluindo seed 100 fake users + edge case n<5 |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui ML/realtime/PII drill-down |
| 5 | Dependencies mapped | Y | Entrada MON-FN-006 (analytics_events 90d); STORY-1.1 cron monitor |
| 6 | Complexity estimate | Y | M (3-4 dias) coerente — matview + RPC + endpoint + heatmap |
| 7 | Business value | Y | "Decisões editoriais SEO especulativas sem cohort visibility" |
| 8 | Risks documented | Y | Refresh >60s + cron miss + dashboard render lento |
| 9 | Criteria of Done | Y | Smoke test seed 50 users + view refresh + sentry alert + memory baseline |
| 10 | Alignment with PRD/Epic | Y | EPIC P2 Sprint 6; ARPU/MRR é complemento (MON-FN-013) |

### Observations
- Score 9 (não 10) reflete: P2 dashboard analytics — não bloqueia funcionalidade end-user mas é instrumentação. Story é bem escrita, mas trade-offs vs ad-hoc query (matview + daily refresh) são pragmáticos não Fortune-500-grade.
- Trade-off matview vs ad-hoc documentado corretamente
- n<5 cohort flag visual (memory `feedback_n2_below_noise_eng_theater` aplicada)
- pg_cron `refresh-cohort-retention-weekly` já coberto por STORY-1.1 monitor
- RPC `get_cohort_retention` com SECURITY DEFINER + auth check (admin-only)
- Frontend heatmap com filter por plan_type
- Migration paired `.down.sql`

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — cohort retention dashboard W1/W4/W12 | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (9/10). P2 instrumentação analytics; pragmatic v1; Status Draft → Ready. | @po (Pax) |
