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
- [ ] Novo status de fonte: `degraded` (alem de `success`, `error`, `timeout`)
- [ ] Quando canary falha, PNCP entra como `status: "degraded"` em `data_sources`
- [ ] `sources_succeeded` NAO inclui fontes degraded
- [ ] Novo campo: `sources_degraded: ["PNCP"]` no search_complete event

### AC2: is_partial = true quando fonte primaria falha
- [ ] Se PNCP (prioridade 1) esta degraded/failed, `is_partial = true`
- [ ] `degradation_reason` preenchido: `"PNCP health canary timeout (cron status: degraded)"`

### AC3: Consolidation distingue "0 resultados" de "fonte indisponivel"
- [ ] `SourceResult` ganha campo `skipped_reason: Optional[str]`
- [ ] Quando PNCP retorna `[]` por canary fail, `skipped_reason = "health_canary_timeout"`
- [ ] Consolidation NAO conta como "succeeded" fontes com `skipped_reason`

### AC4: Frontend mostra DegradationBanner
- [ ] Quando `is_partial: true` e `sources_degraded` inclui PNCP:
  - Banner amarelo: "A fonte principal (PNCP) esta com lentidao. Resultados podem estar incompletos. Tente novamente em alguns minutos."
- [ ] Quando `total_filtered == 0` e `is_partial == true`:
  - Banner vermelho: "Fontes indisponiveis. Os resultados exibidos podem nao refletir todas as oportunidades. Tente novamente mais tarde."
- [ ] Banner inclui botao "Tentar Novamente" que forca `force_fresh: true`

### AC5: Mensagem de 0 resultados contextualizada
- [ ] Quando 0 resultados E fontes degraded:
  - NAO mostrar "nenhuma corresponde ao setor X"
  - Mostrar: "A fonte principal de dados (PNCP) esta temporariamente indisponivel. Tente novamente em alguns minutos para resultados completos."
- [ ] Quando 0 resultados E todas as fontes healthy:
  - Manter mensagem atual: "nenhuma corresponde ao setor X"

### AC6: UFs falhadas transparentes
- [ ] `failed_ufs` incluido na resposta ao frontend
- [ ] Se > 30% das UFs falharam, banner informativo: "Dados incompletos para X estados (AC, AL, AP...)"

### AC7: Metricas
- [ ] `smartlic_source_degradation_total` (labels: source, reason)
- [ ] `smartlic_partial_results_served_total`

### AC8: Testes
- [ ] Test: canary fail → PNCP em sources_degraded, is_partial=true
- [ ] Test: frontend renderiza DegradationBanner quando is_partial=true
- [ ] Test: mensagem de 0 resultados muda quando fontes degraded
- [ ] Test: todas fontes healthy + 0 resultados → mensagem normal

## Arquivos Afetados

### Backend
- `backend/pncp_client.py` — retornar metadata de canary fail (nao [] silencioso)
- `backend/consolidation.py` — SourceResult.skipped_reason, nao contar como succeeded
- `backend/search_pipeline.py` — stage_persist popula sources_degraded, is_partial
- `backend/schemas.py` — novos campos na resposta

### Frontend
- `frontend/app/buscar/components/DegradationBanner.tsx` — ativar com dados reais
- `frontend/app/buscar/components/SearchResults.tsx` — mensagem contextualizada
- `frontend/app/buscar/page.tsx` — passar degradation state para componentes
- `frontend/app/buscar/hooks/useSearch.ts` — parsear sources_degraded da resposta
