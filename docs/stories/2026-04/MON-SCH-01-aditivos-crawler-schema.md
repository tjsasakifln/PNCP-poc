# MON-SCH-01: Crawler e Schema de Aditivos Contratuais

**Priority:** P0
**Effort:** M (2-3 dias)
**Squad:** @data-engineer + @dev
**Status:** Draft
**Epic:** [EPIC-MON-SCHEMA-2026-04](EPIC-MON-SCHEMA-2026-04.md)
**Sprint:** Wave 1

---

## Contexto

A tabela `pncp_supplier_contracts` (~2.1M rows, migração `20260409100000_pncp_supplier_contracts.sql`) não armazena informações de **aditivos contratuais** (termos aditivos de prazo/valor). Aditivos são sinal crítico para:

- **Score de risco de fornecedor** (Due Diligence Express — MON-REP-06): % contratos com aditivo >30% valor, % aditamento médio
- **Alertas de órgão** (Monitor de Órgão — MON-SUB-03): órgão aditou contrato em >20% valor ou >6 meses
- **Radar de risco** (MON-SUB-04): delta score quando CNPJ monitorado sofre aditivo anômalo
- **Página pública** (`/fornecedores/[cnpj]` — MON-SEO-01): exibir "índice de aditivos" como sinal de confiabilidade

PNCP expõe endpoint `/api/consulta/v1/contratos/{numeroControlePNCP}/termos-aditivos` que retorna lista de aditivos com `numeroAditivo`, `tipoAditivo` (prazo/valor/ambos), `valorAditado`, `prazoAditado`, `dataAssinatura`.

---

## Acceptance Criteria

### AC1: Schema enriquecimento em `pncp_supplier_contracts`

- [ ] Migração `supabase/migrations/YYYYMMDDHHMMSS_add_aditivos_to_supplier_contracts.sql` adiciona:
  - `aditivos_count int DEFAULT 0 NOT NULL`
  - `aditivos_valor_total numeric(18,2) DEFAULT 0 NOT NULL` (soma `valorAditado`)
  - `aditivos_prazo_total_dias int DEFAULT 0 NOT NULL` (soma `prazoAditado`)
  - `aditivos_last_checked_at timestamptz NULL`
  - `aditivos_pct_valor numeric(5,2) GENERATED ALWAYS AS (CASE WHEN valor_global > 0 THEN (aditivos_valor_total / valor_global) * 100 ELSE 0 END) STORED`
- [ ] Migração paired down `.down.sql` remove colunas (STORY-6.2 compliance)
- [ ] Índice B-tree em `aditivos_pct_valor` para queries "contratos aditados >X%"
- [ ] View `supplier_risk_summary_mv` (materialized, refresh diário) com agregados por CNPJ:
  - `ni_fornecedor`, `total_contratos`, `contratos_com_aditivo`, `pct_aditados`, `aditivo_medio_valor_pct`, `last_aditivo_date`

### AC2: Crawler de aditivos (ARQ cron)

- [ ] `backend/ingestion/aditivos_crawler.py` — função async `fetch_aditivos(numero_controle_pncp)` consulta endpoint PNCP e retorna lista tipada
- [ ] Respeitar rate limit PNCP: `max 5 concurrent`, 2s delay entre batches
- [ ] Retry exponencial (3 tentativas, HTTP 422/429 retryable); circuit breaker compartilhado (`pncp_client.py`)
- [ ] `backend/jobs/cron/aditivos_sync.py` — ARQ cron diário 06:00 BRT:
  - Processa 10.000 contratos por run (ordenados por `aditivos_last_checked_at ASC NULLS FIRST`)
  - Filtro: só `is_active=true` + `data_assinatura >= NOW() - INTERVAL '3 years'`
  - Upsert via RPC `upsert_aditivos_for_contract(numero_controle_pncp, aditivos_jsonb)`
- [ ] Fallback: se endpoint retornar 404, marca `aditivos_count=0` + `aditivos_last_checked_at=NOW()` (evita retry infinito)
- [ ] Prometheus: `smartlic_aditivos_crawler_requests_total{status}`, `smartlic_aditivos_coverage_pct`

### AC3: Backfill inicial

- [ ] Script `scripts/backfill_aditivos.py` processa priorização:
  - Tier 1: top 50k contratos por `valor_global` (últimos 2 anos)
  - Tier 2: restante dos últimos 2 anos
  - Tier 3: contratos 2-5 anos
- [ ] Executável em background via `railway run python scripts/backfill_aditivos.py --tier 1`
- [ ] Progress logging em `ingestion_runs` table (reusa infra existente)

### AC4: Dashboard admin de coverage

- [ ] Endpoint `GET /v1/admin/aditivos-coverage` (admin only): retorna `{total_contracts, checked, coverage_pct, last_run_at, queue_size}`
- [ ] Frontend `/admin/cache` adiciona card "Aditivos Coverage" (reutilizar componentes existentes)

### AC5: Testes

- [ ] `pytest backend/tests/ingestion/test_aditivos_crawler.py`:
  - Mock PNCP response happy path (3 aditivos retornados, agregados corretos)
  - 404 → marca checked + count=0 (não re-consulta em 7 dias)
  - HTTP 500 retry 3x → circuit breaker open
  - Rate limit 429 → respeita Retry-After
- [ ] `pytest backend/tests/jobs/test_aditivos_sync.py` cobre cron scheduling + batch processing
- [ ] Coverage thresholds respeitados (70% backend)

---

## Scope

**IN:**
- Migração SQL (+.down) em `supabase/migrations/`
- `backend/ingestion/aditivos_crawler.py` (novo)
- `backend/jobs/cron/aditivos_sync.py` (novo)
- `scripts/backfill_aditivos.py` (novo)
- View materializada `supplier_risk_summary_mv`
- Endpoint admin + card frontend
- Testes

**OUT:**
- Integração com CEIS/CNEP (bases de sanções externas) — fica para MON-REP-06b Q3
- UI pública exibindo aditivos — feito em MON-SEO-01
- Aditivos de contratos anteriores a 5 anos — fora de escopo

---

## Dependências

- PNCP endpoint `/contratos/{numeroControlePNCP}/termos-aditivos` validado funcional (checar 10 amostras via curl antes do dev)
- ARQ worker deployed (já em produção — `PROCESS_TYPE=worker`)
- Redis (circuit breaker compartilhado — já em produção)

---

## Riscos

- **Endpoint PNCP pode não expor aditivos de forma consistente:** validar com sample de 100 contratos; se coverage PNCP for <50%, priorizar Tier 1 por valor e aceitar coverage parcial
- **Backfill pesado:** 500k–1M chamadas à API PNCP. Mitigar com throttle 5 rps e backfill em 1-2 semanas background
- **Campos jurídicos diferentes por modalidade:** Lei 8.666 (legacy) vs 14.133 — schemas podem variar; tratar com `try/except` + log estruturado

---

## Dev Notes

_(a preencher pelo @dev durante implementação)_

---

## Arquivos Impactados

- `supabase/migrations/YYYYMMDDHHMMSS_add_aditivos_to_supplier_contracts.sql` (novo)
- `supabase/migrations/YYYYMMDDHHMMSS_add_aditivos_to_supplier_contracts.down.sql` (novo)
- `supabase/migrations/YYYYMMDDHHMMSS_create_supplier_risk_summary_mv.sql` (novo)
- `backend/ingestion/aditivos_crawler.py` (novo)
- `backend/jobs/cron/aditivos_sync.py` (novo)
- `scripts/backfill_aditivos.py` (novo)
- `backend/routes/admin_aditivos.py` (novo)
- `frontend/app/admin/cache/page.tsx` (estender)
- `backend/tests/ingestion/test_aditivos_crawler.py` (novo)

---

## Definition of Done

- [ ] Migração aplicada em produção (via deploy.yml auto-apply)
- [ ] Backfill Tier 1 completo (top 50k por valor) — validar via `SELECT count(*) WHERE aditivos_last_checked_at IS NOT NULL`
- [ ] Cron rodando há 7 dias sem failures em Sentry
- [ ] View `supplier_risk_summary_mv` populada + refresh diário funcionando
- [ ] Dashboard admin mostra coverage >= 30% dos contratos ativos últimos 2 anos
- [ ] `pytest backend/tests/ingestion/test_aditivos_crawler.py` passa
- [ ] Review de segurança: circuit breaker compartilhado evita flood do PNCP; rate limit respeitado
- [ ] Métricas Prometheus visíveis no Grafana

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — parte de EPIC-MON-SCHEMA, prereq para Due Diligence, Radar Risco, Monitor Órgão |
