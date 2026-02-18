# Story UX-304: Fix Filtros Hiper-Agressivos (11k→0 Resultados)

**Epic:** EPIC-UX-PREMIUM-2026-02
**Story ID:** UX-304
**Priority:** 🔴 P0 CRITICAL
**Story Points:** 13 SP
**Created:** 2026-02-18
**Owner:** @dev + @architect
**Status:** 🔴 TODO

---

## Story Overview

**Problema:** Pipeline de filtros rejeita 100% dos resultados (11.106 → 0), mas usuário NÃO sabe POR QUÊ está vendo tela vazia.

**Evidência de Logs:**
```
aplicar_todos_filtros: iniciando com 11106 licitações
filter_rejection (11.106x)
→ 0 resultados finais
```

**Impacto:**
- Usuário vê tela vazia sem explicação
- Impossível debugar qual filtro eliminou tudo
- Frustração total ("sistema não funciona")

**Goal:** Telemetria de filtros com suggestions inteligentes quando zero resultados.

---

## Acceptance Criteria

### AC1: Filter Report em Cada Estágio
- [ ] **GIVEN** busca aplicada
- [ ] **WHEN** passa por pipeline de filtros
- [ ] **THEN** gera relatório detalhado:
  ```python
  FilterReport(
      stage="Status",
      input_count=11106,
      output_count=2340,
      rejected_count=8766,
      rejection_reasons={
          "fora_do_prazo": 5234,
          "status_incorreto": 3532
      }
  )
  ```

### AC2: Empty State Acionável (Não Genérico)
- [ ] **GIVEN** filtros resultam em 0 resultados
- [ ] **WHEN** mostra empty state
- [ ] **THEN** exibe breakdown visual:

**Exemplo UI:**
```
┌─────────────────────────────────────────────┐
│ 🔍 Nenhum Resultado Encontrado               │
│                                              │
│ Sua busca começou com 11.106 licitações:    │
│                                              │
│ ✓ Status "Abertas"                          │
│   11.106 → 2.340 (8.766 rejeitadas)         │
│   └─ 5.234 fora do prazo                    │
│   └─ 3.532 status incorreto                 │
│                                              │
│ ✓ Modalidade                                │
│   2.340 → 1.850 (490 rejeitadas)            │
│   └─ 490 outras modalidades                 │
│                                              │
│ ✗ Palavras-chave (BLOQUEOU TUDO)            │
│   1.850 → 0 (1.850 rejeitadas)              │
│   └─ 1.850 sem match com "uniforme"         │
│                                              │
│ 💡 Sugestão:                                 │
│ • Relaxar filtro de palavras-chave          │
│ • Tentar busca por termos específicos       │
│                                              │
│ [Buscar sem filtros de keyword]             │
│ [Ajustar filtros manualmente]               │
└─────────────────────────────────────────────┘
```

### AC3: Suggestions Inteligentes
- [ ] **GIVEN** filtro eliminou >80% dos resultados
- [ ] **WHEN** retorna zero final
- [ ] **THEN** sugere ação:

| Bottleneck | Sugestão |
|------------|----------|
| Status = "Abertas" rejeitou 100% | "Nenhuma licitação ABERTA. Tente incluir 'Em Julgamento'" |
| Keywords rejeitou >90% | "Poucos matches com '{termo}'. Considere adicionar termos relacionados" |
| Valor rejeitou >50% | "Faixa de valor muito restrita. Atual: R$50k-200k. Expandir?" |
| Modalidade rejeitou >70% | "Apenas Pregão Eletrônico selecionado. Incluir Concorrência?" |

### AC4: FilterReportBreakdown Component
- [ ] **GIVEN** filter report do backend
- [ ] **WHEN** renderiza empty state
- [ ] **THEN** mostra component visual:
  ```tsx
  <FilterReportBreakdown
    report={filterReport}
    onApplySuggestion={(suggestion) => {
      if (suggestion.action === 'relax_keyword_filter') {
        setKeywordFilters([]);
        retrySearch();
      }
    }}
  />
  ```

### AC5: Telemetria de Bottleneck
- [ ] **GIVEN** filtro bloqueia >80% dos resultados
- [ ] **THEN** envia evento Mixpanel:
  ```javascript
  mixpanel.track("filter_bottleneck", {
      stage: "keywords",
      input_count: 1850,
      output_count: 0,
      rejection_rate: 1.0,
      top_rejection_reason: "no_keyword_match",
      user_id: "...",
      search_params: {...}
  });
  ```

### AC6: Backend Filter Report Structure
- [ ] **GIVEN** função `aplicar_todos_filtros_com_telemetria()`
- [ ] **THEN** retorna:
  ```python
  {
      "results": [...],  # Pode ser vazio
      "filter_report": [
          {"stage": "status", "input": 11106, "output": 2340, ...},
          {"stage": "modalidade", "input": 2340, "output": 1850, ...},
          {"stage": "keywords", "input": 1850, "output": 0, ...}
      ],
      "suggestions": [
          {
              "type": "relax_filter",
              "stage": "keywords",
              "message": "Nenhum match com palavras-chave. Considere buscar por termos específicos.",
              "action": "use_termos_especificos_mode"
          }
      ]
  }
  ```

### AC7: Rejection Reasons por Filtro
- [ ] **Status Filter:** track `fora_do_prazo`, `status_incorreto`
- [ ] **Modalidade Filter:** track `outra_modalidade`
- [ ] **Keyword Filter:** track `no_match`, `partial_match_below_threshold`
- [ ] **Valor Filter:** track `abaixo_minimo`, `acima_maximo`, `sem_valor`
- [ ] **UF Filter:** track `outra_uf`

### AC8: Visual Funnel de Filtros
- [ ] **GIVEN** filter report
- [ ] **WHEN** mostra breakdown
- [ ] **THEN** renderiza funnel visual:

```
11.106 ━━━━━━━━━━━━━━━━━━━━━━━━ 100%
   ↓ Status
 2.340 ━━━━━━━━━━━━━━━━━━━━ 21%
   ↓ Modalidade
 1.850 ━━━━━━━━━━━━━━━━━ 17%
   ↓ Keywords
     0 ━ 0%  ← BLOQUEIO AQUI
```

### AC9: "Buscar Sem Filtros" Fallback
- [ ] **GIVEN** user clica "Buscar sem filtros de keyword"
- [ ] **WHEN** executa busca
- [ ] **THEN** mantém Status + Modalidade + Valor
- [ ] **AND** remove apenas filtro de keywords
- [ ] **AND** retorna resultados mais amplos

### AC10: Tests de Suggestions Logic
- [ ] **GIVEN** teste automatizado
- [ ] **WHEN** simula diferentes bottlenecks
- [ ] **THEN** verifica suggestion correta gerada

---

## Technical Implementation

### Backend: Filter Telemetry

```python
# backend/filter.py

from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class FilterReport:
    stage: str
    input_count: int
    output_count: int
    rejected_count: int
    rejection_reasons: Dict[str, int]

    @property
    def rejection_rate(self) -> float:
        if self.input_count == 0:
            return 0.0
        return self.rejected_count / self.input_count

def aplicar_todos_filtros_com_telemetria(
    licitacoes: List[dict],
    filtros: FiltrosRequest
) -> Dict[str, Any]:
    report: List[FilterReport] = []
    current = licitacoes

    # 1. Filtro de Status
    filtered, reasons = filtrar_por_status_telemetria(current, filtros.status)
    report.append(FilterReport(
        stage="status",
        input_count=len(current),
        output_count=len(filtered),
        rejected_count=len(current) - len(filtered),
        rejection_reasons=reasons
    ))
    current = filtered

    # 2. Filtro de Modalidade
    filtered, reasons = filtrar_por_modalidade_telemetria(current, filtros.modalidades)
    report.append(FilterReport(
        stage="modalidade",
        input_count=len(current),
        output_count=len(filtered),
        rejected_count=len(current) - len(filtered),
        rejection_reasons=reasons
    ))
    current = filtered

    # 3. Filtro de Keywords (mais agressivo)
    filtered, reasons = filtrar_por_keywords_telemetria(current, filtros.setor_id)
    report.append(FilterReport(
        stage="keywords",
        input_count=len(current),
        output_count=len(filtered),
        rejected_count=len(current) - len(filtered),
        rejection_reasons=reasons
    ))
    current = filtered

    # ... outros filtros

    # Gerar suggestions se vazio
    suggestions = gerar_sugestoes_se_vazio(report) if len(current) == 0 else []

    return {
        "results": current,
        "filter_report": [r.__dict__ for r in report],
        "suggestions": suggestions
    }

def filtrar_por_status_telemetria(
    licitacoes: List[dict],
    status: str
) -> Tuple[List[dict], Dict[str, int]]:
    filtered = []
    reasons: Dict[str, int] = defaultdict(int)

    for lic in licitacoes:
        if _status_match(lic, status):
            filtered.append(lic)
        else:
            # Classificar motivo de rejeição
            if _is_fora_do_prazo(lic):
                reasons["fora_do_prazo"] += 1
            else:
                reasons["status_incorreto"] += 1

    return filtered, dict(reasons)

def gerar_sugestoes_se_vazio(report: List[FilterReport]) -> List[dict]:
    if report[-1].output_count > 0:
        return []

    suggestions = []

    # Encontrar bottleneck (onde perdeu mais)
    bottleneck = max(report, key=lambda r: r.rejection_rate)

    if bottleneck.stage == "status" and "fora_do_prazo" in bottleneck.rejection_reasons:
        suggestions.append({
            "type": "include_status",
            "stage": "status",
            "message": "Nenhuma licitação ABERTA encontrada. Experimente incluir 'Em Julgamento'.",
            "action": "include_status_em_julgamento"
        })

    if bottleneck.stage == "keywords" and bottleneck.rejection_rate > 0.9:
        suggestions.append({
            "type": "relax_keywords",
            "stage": "keywords",
            "message": "Muitas oportunidades rejeitadas por palavras-chave. Considere buscar por termos específicos.",
            "action": "use_termos_especificos_mode"
        })

    if bottleneck.stage == "valor" and bottleneck.rejection_rate > 0.5:
        suggestions.append({
            "type": "expand_valor_range",
            "stage": "valor",
            "message": f"Faixa de valor muito restrita. Expandir para incluir mais oportunidades?",
            "action": "expand_valor_range"
        })

    return suggestions
```

### Frontend: Filter Report Breakdown

```tsx
// components/FilterReportBreakdown.tsx

interface FilterStage {
  stage: string;
  input_count: number;
  output_count: number;
  rejected_count: number;
  rejection_reasons: Record<string, number>;
}

interface FilterReportBreakdownProps {
  report: FilterStage[];
  suggestions: Array<{
    type: string;
    stage: string;
    message: string;
    action: string;
  }>;
  onApplySuggestion: (action: string) => void;
}

export const FilterReportBreakdown: React.FC<FilterReportBreakdownProps> = ({
  report,
  suggestions,
  onApplySuggestion
}) => {
  const stageNames = {
    status: "Status",
    modalidade: "Modalidade",
    keywords: "Palavras-chave",
    valor: "Valor Estimado",
    uf: "Estados"
  };

  const totalInicial = report[0]?.input_count || 0;

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold">Nenhum Resultado Encontrado</h3>
        <p className="text-gray-600 mt-2">
          Sua busca começou com {totalInicial.toLocaleString()} licitações:
        </p>
      </div>

      {/* Funnel Visual */}
      <div className="space-y-4">
        {report.map((stage, index) => {
          const percentage = totalInicial > 0 ? (stage.output_count / totalInicial) * 100 : 0;
          const isBottleneck = stage.output_count === 0 && stage.input_count > 0;

          return (
            <div key={stage.stage} className={isBottleneck ? "border-2 border-red-400 p-4 rounded-lg" : ""}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">
                  {isBottleneck ? "✗" : "✓"} {stageNames[stage.stage]}
                </span>
                <span className="text-sm text-gray-600">
                  {stage.input_count.toLocaleString()} → {stage.output_count.toLocaleString()}
                  <span className="text-red-600 ml-2">
                    ({stage.rejected_count.toLocaleString()} rejeitadas)
                  </span>
                </span>
              </div>

              {/* Progress bar */}
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full ${isBottleneck ? "bg-red-600" : "bg-blue-600"}`}
                  style={{ width: `${percentage}%` }}
                />
              </div>

              {/* Rejection reasons */}
              {Object.entries(stage.rejection_reasons).length > 0 && (
                <div className="mt-2 pl-4 text-sm text-gray-600">
                  {Object.entries(stage.rejection_reasons).map(([reason, count]) => (
                    <div key={reason} className="flex justify-between">
                      <span>└─ {formatRejectionReason(reason)}</span>
                      <span>{count.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}

              {isBottleneck && (
                <div className="mt-2 text-sm font-semibold text-red-700">
                  ⚠️ BLOQUEIO AQUI
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="bg-blue-50 p-4 rounded-lg">
          <h4 className="font-semibold flex items-center gap-2 mb-3">
            <LightBulbIcon className="w-5 h-5" />
            Sugestões:
          </h4>
          <div className="space-y-2">
            {suggestions.map((sug, index) => (
              <div key={index} className="flex items-start gap-3">
                <span className="text-blue-700">•</span>
                <div className="flex-1">
                  <p>{sug.message}</p>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="mt-2"
                    onClick={() => onApplySuggestion(sug.action)}
                  >
                    Aplicar sugestão
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

function formatRejectionReason(reason: string): string {
  const map = {
    fora_do_prazo: "fora do prazo",
    status_incorreto: "status incorreto",
    outra_modalidade: "outra modalidade",
    no_match: "sem match com palavras-chave",
    abaixo_minimo: "valor abaixo do mínimo",
    acima_maximo: "valor acima do máximo"
  };
  return map[reason] || reason;
}
```

### Frontend: Apply Suggestion Logic

```tsx
// app/buscar/page.tsx

const applySuggestion = (action: string) => {
  switch (action) {
    case "include_status_em_julgamento":
      setStatusFilter(["recebendo_proposta", "em_julgamento"]);
      retrySearch();
      break;

    case "use_termos_especificos_mode":
      setModoToMode("termos");  // Muda para busca por termos
      setKeywordFilters([]);
      break;

    case "expand_valor_range":
      setValorRange({ min: null, max: null });  // Remove limite
      retrySearch();
      break;

    case "relax_keyword_filter":
      setKeywordFilters([]);
      retrySearch();
      break;
  }
};
```

---

## File List

### Backend
- [ ] `backend/filter.py` — Telemetria + suggestions logic
- [ ] `backend/schemas.py` — FilterReport model
- [ ] `backend/tests/test_filter_telemetria.py` — 15 novos testes

### Frontend
- [ ] `frontend/components/FilterReportBreakdown.tsx` — NOVO componente
- [ ] `frontend/app/buscar/page.tsx` — Integrar breakdown + suggestions
- [ ] `frontend/__tests__/filter-report.test.tsx` — 8 novos testes

---

## Dependencies

### Related Stories
- UX-310 (Mensagens de erro acionáveis) — Overlap em suggestions

---

## Definition of Done

- [ ] Todos os ACs passam
- [ ] 15 testes backend passam
- [ ] 8 testes frontend passam
- [ ] QA manual: zero resultados mostra breakdown
- [ ] Suggestions aplicáveis retornam resultados

---

## Estimation Breakdown

- Backend telemetria: 5 SP
- Suggestions logic: 3 SP
- Frontend breakdown UI: 3 SP
- Testing: 2 SP

**Total:** 13 SP

---

**Status:** 🔴 TODO
**Next:** @architect review approach, @dev implement
