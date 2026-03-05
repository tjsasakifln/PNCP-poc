# CRIT-053: Pipeline Deve Reportar Status Real das Fontes

**Prioridade:** CRITICAL
**Componente:** Backend — search_pipeline.py, consolidation.py; Frontend — SearchResults, banners
**Origem:** Incidente 2026-03-05 — Pipeline reporta PNCP como "succeeded" quando retornou 0 por canary fail

## Problema

O search_complete event reporta:
```json
"sources_succeeded": ["PNCP", "PORTAL_COMPRAS"],
"sources_failed": [],
"is_partial": false
```

Quando na realidade PNCP foi descartado pelo canary e retornou zero resultados.
O frontend nao tem como saber que a fonte principal falhou. O usuario ve "nenhuma oportunidade encontrada" sem contexto.

### Cadeia de Mentiras

1. `pncp_client.buscar_todas_ufs_paralelo` retorna `[]` silenciosamente quando canary falha
2. `consolidation.py` trata `[]` como "sucesso com 0 resultados"
3. `search_pipeline.stage_persist` conta PNCP como `sources_succeeded`
4. Frontend nao mostra DegradationBanner (componente existe mas nunca recebe dados)
5. Usuario ve mensagem enganosa: "104 encontradas, nenhuma corresponde ao setor"

## Acceptance Criteria

### AC1: Fonte com canary fail = source_degraded (nao succeeded)
- [x] Novo status de fonte: `degraded` (alem de `success`, `error`, `timeout`)
- [x] Quando canary falha, PNCP entra como `status: "degraded"` em `data_sources`
- [x] `sources_succeeded` NAO inclui fontes degraded
- [x] Novo campo: `sources_degraded: ["PNCP"]` no search_complete event

### AC2: is_partial = true quando fonte primaria falha
- [x] Se PNCP (prioridade 1) esta degraded/failed, `is_partial = true`
- [x] `degradation_reason` preenchido: `"PNCP health canary timeout (cron status: degraded)"`

### AC3: Consolidation distingue "0 resultados" de "fonte indisponivel"
- [x] `SourceResult` ganha campo `skipped_reason: Optional[str]`
- [x] Quando PNCP retorna `[]` por canary fail, `skipped_reason = "health_canary_timeout"`
- [x] Consolidation NAO conta como "succeeded" fontes com `skipped_reason`

### AC4: Frontend mostra DegradationBanner
- [x] Quando `is_partial: true` e `sources_degraded` inclui PNCP:
  - Banner amarelo: "A fonte principal (PNCP) esta com lentidao. Resultados podem estar incompletos. Tente novamente em alguns minutos."
- [x] Quando `total_filtered == 0` e `is_partial == true`:
  - Banner vermelho: "Fontes indisponiveis. Os resultados exibidos podem nao refletir todas as oportunidades. Tente novamente mais tarde."
- [x] Banner inclui botao "Tentar Novamente" que forca `force_fresh: true`

### AC5: Mensagem de 0 resultados contextualizada
- [x] Quando 0 resultados E fontes degraded:
  - NAO mostrar "nenhuma corresponde ao setor X"
  - Mostrar: "A fonte principal de dados (PNCP) esta temporariamente indisponivel. Tente novamente em alguns minutos para resultados completos."
- [x] Quando 0 resultados E todas as fontes healthy:
  - Manter mensagem atual: "nenhuma corresponde ao setor X"

### AC6: UFs falhadas transparentes
- [x] `failed_ufs` incluido na resposta ao frontend
- [x] Se > 30% das UFs falharam, banner informativo: "Dados incompletos para X estados (AC, AL, AP...)"

### AC7: Metricas
- [x] `smartlic_source_degradation_total` (labels: source, reason)
- [x] `smartlic_partial_results_served_total`

### AC8: Testes
- [x] Test: canary fail → PNCP em sources_degraded, is_partial=true
- [x] Test: frontend renderiza DegradationBanner quando is_partial=true
- [x] Test: mensagem de 0 resultados muda quando fontes degraded
- [x] Test: todas fontes healthy + 0 resultados → mensagem normal

## Arquivos Afetados

### Backend
- `backend/consolidation.py` — SourceResult.skipped_reason field
- `backend/search_context.py` — sources_degraded field
- `backend/search_pipeline.py` — degradation detection logic, telemetry, BuscaResponse
- `backend/schemas.py` — sources_degraded field in BuscaResponse
- `backend/metrics.py` — SOURCE_DEGRADATION_TOTAL, PARTIAL_RESULTS_SERVED_TOTAL

### Frontend
- `frontend/app/types.ts` — sources_degraded in BuscaResult
- `frontend/app/buscar/components/DataQualityBanner.tsx` — sourcesDegraded prop, degradation message
- `frontend/app/buscar/components/SearchResults.tsx` — contextual zero results with degraded sources

### Tests
- `backend/tests/test_crit053_source_honesty.py` — 20 tests
- `frontend/__tests__/crit053-source-honesty.test.tsx` — 16 tests
