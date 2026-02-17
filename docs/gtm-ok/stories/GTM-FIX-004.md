# GTM-FIX-004: Fix PNCP Silent Truncation Notification

## Dimension Impact
- Moves D01 (Data Completeness) from 6/10 to 7/10
- Moves D04 (Error Handling) from 5/10 to 6/10

## Problem
When PNCP search hits the 500-page hard limit (max_pages=500 in pncp_client.py:694-703), data is silently truncated without user notification. User thinks they have complete results but may be missing 50%+ of opportunities. Detection logic exists (`is_truncated` flag) but is never propagated to frontend.

## Solution
1. Add `is_truncated: bool` field to `ParallelFetchResult` (pncp_client.py)
2. Propagate truncation flag through `SearchContext` to `BuscaResponse` schema (schemas.py)
3. Return `is_truncated` in `/buscar` API response
4. Display yellow warning banner in frontend when `is_truncated === true`
5. Banner text: "⚠️ Resultados truncados: Sua busca retornou mais de 250.000 registros. Refine os filtros (UFs, datas, valor) para ver todos os resultados."

## Acceptance Criteria
- [ ] AC1: `ParallelFetchResult` includes `is_truncated: bool` field
- [ ] AC2: `pncp_client.py:buscar_todas_ufs_paralelo()` sets `is_truncated=True` when any UF hits max_pages
- [ ] AC3: `BuscaResponse` schema includes `is_truncated` field
- [ ] AC4: `/buscar` endpoint returns `is_truncated` in response JSON
- [ ] AC5: Frontend `BuscaResponse` TypeScript type includes `is_truncated?: boolean`
- [ ] AC6: `buscar/page.tsx` displays TruncationWarningBanner when `is_truncated === true`
- [ ] AC7: Banner includes actionable guidance (refine filters, narrow date range)
- [ ] AC8: Backend test: test_truncation_flag_propagation()
- [ ] AC9: Frontend test: test_truncation_banner_display()
- [ ] AC10: Manual test: Search all 27 UFs + 365 days → verify banner appears

## Effort: S (4h)
## Priority: P0 (Data integrity issue)
## Dependencies: None

## Files to Modify
- `backend/pncp_client.py` (lines 694-703, add is_truncated to ParallelFetchResult)
- `backend/schemas.py` (add is_truncated to BuscaResponse)
- `backend/main.py` (propagate is_truncated from search_context to response)
- `frontend/types/busca.ts` (add is_truncated to BuscaResponse type)
- `frontend/app/buscar/page.tsx` (add TruncationWarningBanner component)
- `frontend/components/buscar/TruncationWarningBanner.tsx` (NEW)
- `backend/tests/test_pncp_client.py` (add test_truncation_flag)
- `frontend/__tests__/buscar/truncation-banner.test.tsx` (NEW)

## Testing Strategy
1. Unit test (backend): Mock fetch results with page_count >= max_pages → verify is_truncated=True
2. Unit test (frontend): Mock BuscaResponse with is_truncated=true → verify banner renders
3. Integration test: Execute search with very broad filters → verify flag propagates end-to-end
4. Manual test: Production test with all UFs + full year → confirm banner displays

## Banner Design Spec
```tsx
<div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
  <div className="flex items-start gap-3">
    <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
    <div>
      <h3 className="font-semibold text-yellow-900 dark:text-yellow-100">
        Resultados truncados
      </h3>
      <p className="text-sm text-yellow-800 dark:text-yellow-200 mt-1">
        Sua busca retornou mais de 250.000 registros do PNCP. Para garantir
        análise completa, refine os filtros (selecione menos UFs, reduza período,
        ou ajuste faixa de valores).
      </p>
    </div>
  </div>
</div>
```

## Future Enhancement (not in scope)
- Add "Refinar busca" button that opens filter panel
- Log truncation events to Mixpanel for UX analysis
- Consider increasing max_pages with pagination UI

## ⚠️ REVISÃO — Impacto PCP API (2026-02-16)

**Contexto:** Com a integração do Portal de Compras Públicas (GTM-FIX-011), truncation pode ocorrer em ambas as fontes independentemente.

**Alterações nesta story:**

1. **AC2 revisado:** `is_truncated` deve ser um objeto, não boolean simples:
   ```python
   # Antes:
   is_truncated: bool = False

   # Depois (backward-compatible):
   is_truncated: bool = False  # True if ANY source truncated
   truncation_details: Optional[dict] = None  # {"pncp": True, "pcp": False}
   ```
   O boolean `is_truncated` é mantido para backward compatibility. O `truncation_details` adiciona granularidade por fonte.

2. **AC6 revisado:** O banner de truncation deve indicar QUAL fonte truncou:
   - Apenas PNCP: "⚠️ Resultados do PNCP truncados..."
   - Apenas PCP: "⚠️ Resultados do Portal de Compras Públicas truncados..."
   - Ambos: "⚠️ Resultados truncados em ambas as fontes..."

3. **Novo AC11:** O `PCPClient` (criado em GTM-FIX-011) deve implementar sua própria detecção de truncation baseada em `quantidadeTotal` vs registros recebidos.

4. **Impacto no effort:** +1h (de S/4h para S/5h) — lógica de merge de truncation flags.

**Dependência:** Se implementada ANTES de GTM-FIX-011, manter implementação somente-PNCP. Quando GTM-FIX-011 entrar, o DataSourceAggregator mergeará os flags de truncation. Se implementada DEPOIS, já incluir dual-source desde o início.
