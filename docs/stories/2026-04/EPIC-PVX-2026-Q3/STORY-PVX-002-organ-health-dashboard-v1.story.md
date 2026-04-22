# STORY-PVX-002: Organ Health Dashboard v1 — Backend Materialized View

**Priority:** P0 — Segunda feature 0-de-6-concorrentes (virgin blue ocean)
**Effort:** S (5 SP, ~5-6h)
**Squad:** @dev + @qa + @data-engineer (review obrigatório — materialized view design)
**Status:** Ready
**Epic:** [EPIC-PVX-2026-Q3](EPIC.md)
**Source:** PR #476 §8 Brief 2 (research blue-ocean-product-value-extraction.md)

---

## Contexto

PR #476 (research blue ocean) validou empiricamente que **0 de 6 concorrentes** entregam dashboard de saúde operacional do órgão comprador. Usuários B2G declinam ou participam cegamente de editais sem saber:

- **Cancellation rate**: % de editais que o órgão cancela após publicação (12m trailing)
- **Desert rate**: % de editais sem propostas vencedoras (12m trailing)
- **Avg time-to-contract**: dias entre publicação do edital e assinatura do contrato (12m trailing)

Dados existem em `supplier_contracts` + `pncp_raw_bids` mas não há aggregation materializada. Esta v1 entrega a **materialized view + cron de refresh + score composto** (sem frontend).

**Decisão de escopo:** v1 backend-only para validar viabilidade do dataset antes de investir em UI completa. Frontend (`/orgaos/[cnpj]/saude` + Health Badge widget no `/buscar` + filtro "score ≥70") fica para STORY-PVX-002-v2 na sprint 2 (8 SP adicionais).

---

## Acceptance Criteria

### AC1: Materialized view `organ_health_metrics`
- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_create_organ_health_metrics.sql` (+ `.down.sql`)
- [ ] Schema:
  ```sql
  CREATE MATERIALIZED VIEW organ_health_metrics AS
  SELECT
    cnpj_orgao,
    nome_orgao,
    uf,
    COUNT(*) AS sample_size_12m,
    SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0) AS cancellation_rate_12m,
    SUM(CASE WHEN status = 'deserto' OR resultado IS NULL THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0) AS desert_rate_12m,
    AVG(EXTRACT(EPOCH FROM (data_assinatura_contrato - data_publicacao_edital))/86400) AS avg_time_to_contract_days,
    NOW() AS computed_at
  FROM pncp_raw_bids
  WHERE data_publicacao >= NOW() - interval '12 months'
  GROUP BY cnpj_orgao, nome_orgao, uf;
  ```
- [ ] Index em `cnpj_orgao` (UNIQUE) + `uf` + `sample_size_12m DESC`
- [ ] RLS: read público autenticado; write apenas service role

### AC2: Score composto `reliability_score_v1`
- [ ] Computed column ou separate function:
  ```python
  reliability_score_v1 = (
      0.40 * (1 - cancellation_rate_12m) +
      0.30 * (1 - desert_rate_12m) +
      0.30 * normalize(avg_time_to_contract_days, lower_is_better=True, baseline=90)
  ) * 100
  ```
- [ ] Range: 0-100 (higher = better)
- [ ] Pesos documentados como **V1 educated default** — sujeitos a calibração ground truth (PVX-CALIBRATION-001 sprint 3)

### AC3: Flag `low_sample` para dados pouco confiáveis
- [ ] Coluna `low_sample BOOLEAN GENERATED AS (sample_size_12m < 30)`
- [ ] APIs e exports devem expor flag para que UI mostre warning

### AC4: ARQ cron `refresh_organ_health` daily 04:00 BRT
- [ ] `backend/jobs/cron/organ_health_refresh.py`
- [ ] Schedule: daily 04:00 BRT (07:00 UTC) — antes do contract_radar (06h BRT) para data fresca
- [ ] Comando: `REFRESH MATERIALIZED VIEW CONCURRENTLY organ_health_metrics`
- [ ] Budget: 5min; Prometheus `smartlic_organ_health_refresh_duration_seconds`
- [ ] Alert se duration > 4min p95

### AC5: Backend service `OrganHealthService`
- [ ] Novo módulo `backend/services/organ_health.py`
- [ ] Função `get_organ_health(cnpj_orgao: str) -> OrganHealthDTO | None`
- [ ] Função `get_top_organs_by_reliability(uf: str | None, limit: int = 100) -> list[OrganHealthDTO]`
- [ ] Pydantic DTO com todos campos + `reliability_score_v1` + `low_sample` flag

### AC6: Feature flag `ORGAN_HEALTH_ENABLED`
- [ ] Default: `false` (env var)
- [ ] Service retorna `None` (graceful) quando flag off
- [ ] Sem flag = no-op silencioso

### AC7: Tests backend ≥ 80% cobertura
- [ ] `backend/tests/test_organ_health_service.py`
  - Unit: score computation com diferentes cenários (high cancel, high desert, slow time)
  - Unit: low_sample flag respeitado
  - Unit: feature flag off → returns None
  - Unit: top_organs query com filtro UF
  - Integration: full refresh cycle com fixture dataset
- [ ] `backend/tests/test_organ_health_refresh_cron.py`
  - Unit: cron triggers REFRESH MATERIALIZED VIEW
  - Unit: cron handles refresh failures gracefully (Sentry capture)

### AC8: Backfill inicial em prod
- [ ] Após migration aplicada, executar `REFRESH MATERIALIZED VIEW organ_health_metrics` manualmente uma vez (Railway run)
- [ ] Validar: `SELECT COUNT(*) FROM organ_health_metrics WHERE NOT low_sample` retorna ≥ 100 órgãos

---

## Scope IN

- Materialized view + index + RLS + migration up/down
- Score composto V1 com pesos fixos (40/30/30)
- Cron diário de refresh
- Backend service + Pydantic DTO
- Feature flag + tests
- Backfill inicial manual

## Scope OUT (vai para STORY-PVX-002-v2)

- **Payment delay metric V2** — requer crawl ComprasGov v3, separate spike
- **Score calibration via ground truth survey** — PVX-CALIBRATION-001 sprint 3
- **Comparação histórica órgão vs órgão** — V2
- **Frontend `/orgaos/[cnpj]/saude`** — V2 (8 SP)
- **Health Badge widget no /buscar e /pipeline** — V2
- **Filtro em /buscar "apenas órgãos com score ≥70"** — V2
- **API endpoint público `GET /v1/orgaos/{cnpj}/health`** — V2 (decisão pricing primeiro)
- **A/B com pesos diferentes (50/25/25 vs 30/40/30)** — sprint separada após baseline V1

---

## Dependências

- **Existing:** `pncp_raw_bids` populada via DataLake — disponível
- **Existing:** `supplier_contracts` populada — disponível (para validação cross-check)
- **Existing:** ARQ worker rodando — disponível
- **Required from PVX-001:** consolidar pattern de cron + Prometheus metrics; este pode reusar
- **Blocker para v2:** `STORY-PVX-002-v2` (frontend) requer este Done + pricing definido

---

## Complexidade

**5 SP** (1 sprint, ~5-6h)

Componentes:
- Migration + materialized view design: 1.5 SP (data-engineer review)
- Service + DTO + score computation: 1.5 SP
- Cron + tests: 2 SP

---

## Tier de Pagamento (preview)

V1 sem exposição a usuário final. v2 (frontend) defines tier:
- Pro+: score resumido (badge + filtro)
- Pro Plus / Enterprise: detalhamento completo + comparação histórica

Definição em `STORY-PVX-PRICING-001` sprint 3.

---

## Arquivos previstos

**Novos:**
- `supabase/migrations/YYYYMMDDHHMMSS_create_organ_health_metrics.sql`
- `supabase/migrations/YYYYMMDDHHMMSS_create_organ_health_metrics.down.sql`
- `backend/services/organ_health.py` (service + DTO)
- `backend/jobs/cron/organ_health_refresh.py` (ARQ cron)
- `backend/tests/test_organ_health_service.py`
- `backend/tests/test_organ_health_refresh_cron.py`

**Modificados:**
- `backend/jobs/queue/config.py` (registrar cron)
- `backend/metrics.py` (+1 Prometheus counter)
- `.env.example` (+ `ORGAN_HEALTH_ENABLED=false`)
- `backend/config.py` (load env var)

---

## Riscos & Mitigações

| Risk | Impact | Mitigation |
|------|--------|------------|
| `pncp_raw_bids` não tem `data_assinatura_contrato` populada | Alto — score incompleto | Validar via spike SQL antes de iniciar; se ausente, calcular `time_to_contract` a partir de `supplier_contracts.data_inicio_vigencia` (cross-table) |
| Materialized view refresh muito lento (>5min) com 50K bids | Médio — cron timeout | `CONCURRENTLY` evita lock; index strategy + partial refresh se necessário |
| Pesos 40/30/30 produzem ranking nada-aderente vs intuição user | Médio — feature credibility | Documentar como "preview/beta"; calibração obrigatória sprint 3 |
| Status field em `pncp_raw_bids` não tem 'cancelado'/'deserto' literais | Alto — query quebra | Validar enum/string distincts via SQL antes; ajustar CASE WHEN para valores reais |

---

## Definition of Done

- [ ] Todos AC ✅
- [ ] Migration aplicada em prod via deploy.yml + smoke test pós-deploy
- [ ] Tests passando local + CI Backend Tests (PR Gate) verde
- [ ] @qa gate PASS
- [ ] @data-engineer review aprovado (materialized view design)
- [ ] PR mergeado em main via @devops
- [ ] Feature flag global=true em prod
- [ ] Backfill manual executado (`SELECT COUNT(*) FROM organ_health_metrics WHERE NOT low_sample` ≥ 100)
- [ ] Cron executa com sucesso 2× em prod (validar logs)
- [ ] Story file atualizada com `Status: Done` + Change Log entry

---

## PO Validation (10-Point Checklist)

**Validator:** @po (Sarah) — 2026-04-22
**Verdict:** GO (10/10)

| # | Critério | Resultado |
|---|----------|-----------|
| 1 | Título claro e objetivo | ✅ |
| 2 | Descrição completa (problema/necessidade) | ✅ |
| 3 | AC testáveis (checkboxes + SQL schema explícito + computation formula) | ✅ |
| 4 | Scope IN/OUT bem definido (v1 backend-only, v2 frontend separado) | ✅ |
| 5 | Dependências mapeadas (Existing + Blocker para v2 nominado) | ✅ |
| 6 | Complexidade estimada (5 SP, ~5-6h) | ✅ |
| 7 | Valor de negócio claro (virgin moat 0/6 concorrentes; tier upsell preview) | ✅ |
| 8 | Riscos documentados + mitigações (4 riscos com strategy each) | ✅ |
| 9 | Definition of Done explícito (8 itens incluindo backfill manual) | ✅ |
| 10 | Alinhamento com EPIC-PVX-2026-Q3 + PR #476 | ✅ |

**Decisão:** Story aprovada para execução. Pode iniciar imediatamente após @dev claim.

**Observação @po:** Story tem dependência implícita de @data-engineer review obrigatório antes de @dev iniciar (campo já listado em Squad). AC1 SQL schema deve ser validado com @data-engineer antes de migration ser commitada — risco mais alto identificado é "campos não populados em pncp_raw_bids" (R3 e R4 da seção Riscos). @dev deve abrir spike de validação SQL como **AC0** antes de seguir para AC1.

---

## Change Log

| Data | Quem | Mudança |
|------|------|---------|
| 2026-04-22 | @sm (River) | Story criada a partir de PR #476 §8 Brief 2; status=Draft |
| 2026-04-22 | @po (Sarah) | 10/10 GO em validate-story-draft com observação re: data-engineer review obrigatório; status Draft → Ready |
