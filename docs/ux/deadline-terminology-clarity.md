# Deadline Terminology Clarity - Implementation Report

**Date:** 2026-02-10
**Author:** UX Design Expert + Frontend Developer
**Status:** ✅ Complete

## Problem Statement

The system was using ambiguous deadline terminology that confused users:

- **Ambiguous:** "prazo de abertura em 05/02/2026"
- **User interpretation:** "I have until 05/02 to submit my proposal" ❌
- **Actual meaning:** "Proposal submission STARTS on 05/02" ✅

This caused users to potentially miss real deadlines (e.g., 23/02/2026).

## Root Cause

1. **Backend LLM Prompt:** No explicit rules against ambiguous terms
2. **Frontend Cards:** Used generic labels like "Prazo:" and "Início:" without context
3. **No Validation:** No assertions to prevent ambiguous output from reaching users

## Solution Overview

### 1. Backend Changes (D:\pncp-poc\backend\llm.py)

#### Updated System Prompt

```python
system_prompt = f"""Você é um analista de licitações especializado em {sector_name}.

REGRAS CRÍTICAS DE TERMINOLOGIA:

1. NUNCA use estes termos ambíguos:
   - ❌ "prazo de abertura"
   - ❌ "abertura em [data]"
   - ❌ "prazo em [data]" (sem contexto claro)

2. SEMPRE use estes termos claros:
   - ✅ "recebe propostas a partir de [data_início]"
   - ✅ "prazo final para propostas em [data_fim]"
   - ✅ "você tem X dias para enviar proposta até [data_fim]"
   - ✅ "encerra em [data_fim]"

3. FORMATO DO RESUMO:
   - Seja direto e objetivo
   - Destaque as maiores oportunidades por valor
   - Para prazos urgentes (< 7 dias), use: "encerra em X dias (prazo final: [data])"
   - Mencione a distribuição geográfica
   - Use linguagem profissional, não técnica demais
   - Valores sempre em reais (R$) formatados
"""
```

#### Added Validation Assertions

```python
# CRITICAL: Validate that ambiguous deadline terminology is not present
forbidden_terms = [
    "prazo de abertura",
    "abertura em",
    "abertura:",
]
resumo_text = resumo.resumo_executivo.lower()
for term in forbidden_terms:
    if term in resumo_text:
        # Log the error for monitoring
        logging.warning(
            f"LLM generated ambiguous term '{term}' in summary: {resumo.resumo_executivo}"
        )
        # Fail fast to prevent user confusion
        raise ValueError(
            f"LLM output contains ambiguous deadline terminology: '{term}'. "
            "This violates UX clarity rules. Please regenerate summary."
        )
```

#### Updated Fallback Function

```python
# OLD (ambiguous):
alerta = f"Licitação com prazo em menos de 7 dias: {orgao}"

# NEW (clear):
alerta = f"⚠️ Licitação encerra em {dias_restantes} dia(s) - {orgao}"
```

### 2. Frontend Changes (D:\pncp-poc\frontend\app\components\LicitacaoCard.tsx)

#### New Visual Design

```tsx
{/* Clear Deadline Information */}
<div className="space-y-2 p-3 border border-strong rounded-lg bg-surface-1/30">
  {/* Data de início */}
  {licitacao.data_abertura && (
    <div className="flex items-start gap-2">
      <span className="text-lg">🟢</span>
      <div className="flex-1 min-w-0">
        <InfoTooltip
          content={
            <div>
              <p className="font-semibold mb-1">Data de início</p>
              <p className="text-xs">
                Esta é a data em que a licitação começa a receber propostas.
                Você pode enviar sua proposta a partir deste momento.
              </p>
            </div>
          }
        >
          <div>
            <p className="text-xs font-semibold text-green-700">
              Recebe propostas
            </p>
            <p className="text-sm">
              {format(parseISO(licitacao.data_abertura), "dd/MM/yyyy 'às' HH:mm")}
            </p>
          </div>
        </InfoTooltip>
      </div>
    </div>
  )}

  {/* Prazo final */}
  {licitacao.data_encerramento && (
    <div className="flex items-start gap-2">
      <span className="text-lg">🔴</span>
      <div className="flex-1 min-w-0">
        <InfoTooltip
          content={
            <div>
              <p className="font-semibold mb-1">Data limite</p>
              <p className="text-xs mb-2">
                Esta é a data e hora limite para envio de propostas.
                Após este momento, o sistema não aceita mais submissões.
              </p>
              <p className="text-xs text-yellow-600">
                ⚠️ Importante: Envie com antecedência para evitar problemas técnicos de última hora.
              </p>
            </div>
          }
        >
          <div>
            <p className="text-xs font-semibold text-red-700">
              Prazo final para propostas
            </p>
            <p className="text-sm">
              {format(parseISO(licitacao.data_encerramento), "dd/MM/yyyy 'às' HH:mm")}
            </p>
          </div>
        </InfoTooltip>
      </div>
    </div>
  )}

  {/* Tempo restante */}
  {licitacao.data_encerramento && (
    <div className="flex items-center gap-2 pt-1 border-t border-strong">
      <ClockIconSmall className="h-4 w-4 text-muted-foreground" />
      <span className="text-xs text-ink-secondary font-medium">
        {calculateTimeRemaining(licitacao.data_encerramento)}
      </span>
    </div>
  )}
</div>
```

#### Time Remaining Helper

```typescript
function calculateTimeRemaining(deadline: string): string {
  try {
    const deadlineDate = parseISO(deadline);
    const now = new Date();

    if (isPast(deadlineDate)) {
      return "⛔ Prazo encerrado";
    }

    const days = differenceInDays(deadlineDate, now);
    const hours = differenceInHours(deadlineDate, now) % 24;

    if (days === 0) {
      return `⏰ Você tem ${hours}h restantes`;
    }

    if (days === 1) {
      return `⏰ Você tem 1 dia e ${hours}h restantes`;
    }

    return `⏰ Você tem ${days} dias e ${hours}h restantes`;
  } catch {
    return "-";
  }
}
```

## Visual Comparison

### Before (Ambiguous)

```
┌─────────────────────────────────────┐
│ Status: Aberta                      │
│                                     │
│ Confecção de fardamentos            │
│ Prefeitura de Porto Alegre          │
│                                     │
│ 📍 RS - Porto Alegre                │
│ 📅 Prazo: 23/02/2026                │
│ 📅 Início: 05/02/2026               │
│                                     │
│ R$ 75.000                           │
└─────────────────────────────────────┘
```

**Problems:**
- "Prazo" is ambiguous - prazo for what?
- "Início" could mean anything
- No time information
- No urgency indicator

### After (Clear)

```
┌─────────────────────────────────────┐
│ Status: Aberta                      │
│                                     │
│ Confecção de fardamentos            │
│ Prefeitura de Porto Alegre          │
│                                     │
│ 📍 RS - Porto Alegre                │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🟢 Recebe propostas             │ │
│ │    05/02/2026 às 09:00          │ │
│ │                                 │ │
│ │ 🔴 Prazo final para propostas   │ │
│ │    23/02/2026 às 18:00          │ │
│ │                                 │ │
│ │ ─────────────────────────────   │ │
│ │ ⏰ Você tem 13 dias e 8h        │ │
│ │    restantes                    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ R$ 75.000                           │
└─────────────────────────────────────┘
```

**Improvements:**
- ✅ Clear labels with context
- ✅ Visual indicators (🟢/🔴)
- ✅ Time information included
- ✅ Countdown to deadline
- ✅ Tooltips for additional help

## Test Coverage

### Backend Tests (10 tests, all passing)

**File:** `D:\pncp-poc\backend\tests\test_llm_deadline_terminology.py`

- ✅ Forbidden terms trigger assertion
- ✅ "abertura em" triggers assertion
- ✅ Clear terminology passes validation
- ✅ Fallback uses clear terminology
- ✅ Urgent alerts use clear terminology
- ✅ System prompt includes forbidden terms list
- ✅ System prompt includes correct examples
- ✅ Assertion failures are logged
- ✅ Empty licitacoes have clear message
- ✅ Single licitacao clarity

### Frontend Tests (13 tests, all passing)

**File:** `D:\pncp-poc\frontend\__tests__\components\LicitacaoCard-deadline-clarity.test.tsx`

- ✅ Displays "Recebe propostas" instead of ambiguous terms
- ✅ Displays "Prazo final para propostas" instead of just "Prazo"
- ✅ Displays time remaining with clear language
- ✅ Uses colored icons 🟢/🔴
- ✅ Includes clock icon for time remaining
- ✅ Formats dates with complete time
- ✅ Handles expired deadlines correctly
- ✅ Handles missing data_abertura
- ✅ Handles missing data_encerramento
- ✅ Does NOT contain "prazo de abertura"
- ✅ Does NOT contain "abertura em [data]"
- ✅ Does NOT use "Início:" without context
- ✅ Tooltips contain clear explanations

## Forbidden Terms

These terms are NEVER allowed in user-facing text:

| Forbidden Term | Why It's Confusing | Use Instead |
|----------------|--------------------|-----------|
| "prazo de abertura" | Ambiguous - prazo means deadline, but abertura means opening | "recebe propostas a partir de [data]" |
| "abertura em [data]" | Users think this is the submission deadline | "prazo final para propostas em [data]" |
| "Prazo:" (without context) | Unclear which date this refers to | "Prazo final para propostas:" |
| "Início:" (without context) | Too generic, could mean anything | "Recebe propostas" |

## Quality Gates

### Backend

1. **LLM Output Validation:** Assertions in `llm.py` reject any summary with forbidden terms
2. **Logging:** All rejected summaries are logged for monitoring
3. **Fallback Safety:** Fallback function also follows clear terminology rules

### Frontend

1. **Visual Clarity:** 🟢/🔴 indicators make deadline stages obvious
2. **Time Context:** Always show time remaining, not just dates
3. **Tooltips:** Provide additional explanation on hover
4. **Test Coverage:** 13 tests ensure forbidden terms never appear

## Deployment Checklist

- [x] Backend prompt updated with forbidden terms
- [x] Backend assertions added
- [x] Backend logging configured
- [x] Backend fallback updated
- [x] Frontend cards redesigned
- [x] Frontend helper functions added
- [x] Frontend tooltips implemented
- [x] Backend tests created (10 tests)
- [x] Frontend tests created (13 tests)
- [x] All tests passing
- [ ] Manual testing in staging
- [ ] User acceptance testing
- [ ] Production deployment

## Monitoring

### Metrics to Track

1. **LLM Assertion Failures:** Monitor `logging.warning` calls for forbidden terms
2. **User Feedback:** Survey users about deadline clarity
3. **Submission Timing:** Track if users submit closer to actual deadlines (not confused by dates)

### Alert Thresholds

- **> 5% assertion failures:** Investigate prompt effectiveness
- **User complaints about dates:** Review terminology again

## Future Enhancements

1. **Glossary Page:** Create `/glossario` with definitions of all procurement terms
2. **Interactive Tutorial:** First-time users see guided tour of deadline meanings
3. **Calendar Integration:** Allow users to add deadlines to their calendar
4. **Smart Reminders:** Notify users X days before deadline based on proposal complexity

## Related Files

### Modified Files

- `backend/llm.py` - System prompt + assertions
- `frontend/app/components/LicitacaoCard.tsx` - Visual redesign
- `backend/tests/test_llm_deadline_terminology.py` - Backend tests (new)
- `frontend/__tests__/components/LicitacaoCard-deadline-clarity.test.tsx` - Frontend tests (new)

### Dependencies

- `date-fns` (already installed) - Date manipulation and formatting

## References

- **Issue:** User confusion about deadline terminology
- **Priority:** P0 (Critical UX issue)
- **Impact:** Prevents users from missing real deadlines
- **Effort:** 3 hours (UX + Dev + Testing)

---

**Sign-off:**

- [x] UX Design Expert - Terminology validated
- [x] Frontend Developer - Implementation complete
- [x] QA Engineer - All tests passing
- [ ] Product Owner - Approve for deployment
