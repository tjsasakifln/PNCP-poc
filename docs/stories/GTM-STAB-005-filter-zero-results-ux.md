# GTM-STAB-005 — Fix "0 Oportunidades" com Check Verde + UX de Resultados Vazios

**Status:** Code Complete — all ACs implemented (needs deploy + prod validation)
**Priority:** P1 — High (UX medíocre → percepção de produto quebrado)
**Severity:** Frontend + Backend — filtro rejeita tudo, UX não comunica adequadamente
**Created:** 2026-02-24
**Sprint:** GTM Stabilization
**Relates to:** GTM-STAB-004 (partial results), UX-341 (empty states educativos), STORY-267 (term search parity)

---

## Problema

### 1. Check verde com 0 resultados = confusão

O screenshot mostra ES e SP com **✓ verde** e "0 oportunidades". Para o usuário, verde = sucesso. Mas 0 oportunidades = fracasso. Essa contradição visual gera frustração:

- "O sistema buscou e não encontrou nada?" → Desconfiança
- "Os dados estão corretos?" → Perda de credibilidade
- "Por que eu esperei 100s para isso?" → Abandono

### 2. Filtro muito agressivo para termos livres

O pipeline de filtro (filter.py, 3500+ linhas) foi otimizado para buscas por **setor** (15 setores com keywords calibradas). Quando o usuário faz busca por **termos livres** (custom_terms), o mesmo filtro se aplica e frequentemente rejeita TUDO:

- Keyword density mínima rejeita bids que mencionam o termo de forma diferente
- Sector exclusions podem excluir termos legítimos
- Min-match floor pode ser alto demais para termos genéricos
- Proximity/co-occurrence rules rejeitam falsos positivos que são verdadeiros positivos

### 3. Nenhuma orientação quando 0 resultados

Não há empty state educativo. O usuário vê "0 oportunidades" e não sabe:
- Se é porque não existem licitações no período
- Se é porque o filtro está muito restritivo
- O que fazer para melhorar os resultados

---

## Acceptance Criteria

### AC1: Semântica visual de UF status
- [x] UfProgressGrid.tsx — 4 estados visuais distintos ✅ (lines 25-52): successWithResults (green), successZero (amber), failed (red), retrying (blue)
- [x] "0 oportunidades" com check verde NÃO existe mais ✅ (amber/yellow for N=0)
- [x] Quando N=0, card amarelo/cinza (não verde) ✅

### AC2: Empty state educativo
- [x] ZeroResultsSuggestions.tsx — actionable buttons (ampliar período, adicionar estados, mudar setor) ✅
- [x] Quando total de resultados = 0 após processamento completo — ✅ `ZeroResultsSuggestions` enhanced with `totalFromSources` + `filterStats` props, wired in `SearchResults.tsx`
- [x] Botões de sugestão funcionais (onAdjustPeriod, onAddNeighborStates, onChangeSector) ✅
- [x] Se modo setor com 0: sugerir ampliar período e estados ✅
- [x] Se modo termos com 0: sugerir setor mais próximo ✅

### AC3: Filter stats transparente
- [x] FilterStats model in schemas.py (lines 754-768) with full rejection breakdown ✅
- [x] filter_stats: Optional[FilterStats] in BuscaResponse (line 955) ✅
- [x] Quando resultados = 0, exibir motivo do filtro — ✅ `FilterStatsBreakdown.tsx` renders color-coded horizontal bars per filter stage
- [x] Frontend exibe: "47 licitações encontradas nas fontes oficiais, mas nenhuma corresponde aos seus critérios" — ✅ wired in `ZeroResultsSuggestions` + `SearchResults.tsx`
- [x] Isso dá confiança: o sistema BUSCOU, os dados EXISTEM, mas não são relevantes ✅

### AC4: Auto-relaxation para termos livres
- [x] 4-level auto-relaxation implemented ✅ (search_pipeline.py:1661-1817):
  - Level 0: Normal filtering with min_match_floor
  - Level 1: Relaxed min-match (floor=0, 1+ match) → `filter_relaxed=True`
  - Level 2: Keyword-free for term searches
  - Level 3: Top-10 by value, no keyword filter
- [x] Cada retry automático ✅
- [x] `filter_relaxed: Optional[bool]` + `relaxation_level: Optional[int]` in BuscaResponse ✅ (schemas.py:1076-1118)
- [x] Frontend banner "Resultados com filtro ampliado" — ✅ `FilterRelaxedBanner.tsx` with dismissible blue banner + contextual relaxation messages

### AC5: "Indisponível" com contexto
- [x] Quando UF=failed, mostrar motivo — ✅ `UfFailureDetail.tsx` with per-reason icons + messages:
  - "PNCP não respondeu para MG (tempo esgotado)" → timeout
  - "Taxa limite atingida para RJ" → rate_limit
  - "Fonte indisponível para ES" → offline
  - "Erro ao consultar UF" → error
- [x] Sugerir: retry button per UF (when `onRetry` callback provided) ✅

### AC6: Testes
- [x] Frontend: test empty state com 0 resultados → sugestões visíveis — ✅ `stab-005-zero-results.test.tsx` (23 tests)
- [x] Frontend: test UF status amarelo para success+0 ✅
- [x] Backend: test auto-relaxation retorna resultados quando normal retorna 0 — ✅ test_stab005_auto_relaxation.py (8 tests, all pass)
- [x] Backend: test filter_stats incluso no response quando filtrado=0 — ✅ test_stab005_auto_relaxation.py class TestFilterStatsInResponse
- [x] E2E: busca com termos específicos — ✅ Playwright 2026-02-25: "calibração de equipamentos metrológicos" → 10 results via auto-relaxation from 132 analyzed. Sector search → "132 licitações encontradas nas fontes oficiais, mas nenhuma corresponde ao setor" + "Verificar setor" button

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `frontend/app/buscar/components/UfProgressGrid.tsx` | AC1: 4 estados visuais |
| `frontend/app/buscar/components/SearchResults.tsx` | AC2: empty state educativo |
| `frontend/app/buscar/page.tsx` | AC2+AC4: sugestões + auto-retry |
| `backend/search_pipeline.py` | AC4: auto-relaxation logic |
| `backend/filter.py` | AC3: filter_stats no return + AC4: relaxation retries |
| `backend/schemas.py` | AC3: filter_summary field + relaxation_level |
| `backend/routes/search.py` | AC3: include filter_stats when 0 results |

---

## Decisões Técnicas

- **Amarelo para 0 results** — Padrão UX: verde=sucesso, vermelho=erro, amarelo=atenção. "Sem oportunidades" é atenção, não sucesso.
- **Filter stats** — Transparência gera confiança. "O sistema buscou mas não encontrou" é muito melhor que "0 oportunidades" sem contexto.
- **Auto-relaxation** — Google Search faz isso: "Did you mean..." + resultados ampliados. Nunca retorne vazio se há dados.
- **3 níveis de relaxation** — Gradual, do mais preciso ao mais amplo. Cada nível é logged para analytics.

## Estimativa
- **Esforço:** 6-8h
- **Risco:** Baixo-Médio (UX changes + filter relaxation)
- **Squad:** @ux-design-expert (AC1+AC2+AC5) + @dev (AC3+AC4) + @qa (AC6)
