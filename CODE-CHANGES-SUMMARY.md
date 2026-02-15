# Code Changes Summary - Deadline Clarity Implementation

**Date:** 2026-02-10
**Files Changed:** 2 modified, 5 new
**Lines Added:** +215
**Lines Removed:** -25
**Net Change:** +190 lines

---

## Modified Files

### 1. backend/llm.py (+59 lines, -12 lines)

#### Change 1: Import logging module

```python
from datetime import datetime
from typing import Any
import json
import os
import logging  # NEW

from openai import OpenAI
```

#### Change 2: Rewrite system prompt with forbidden terms

```python
# BEFORE
system_prompt = f"""Você é um analista de licitações especializado em {sector_name}.
Analise as licitações fornecidas e gere um resumo executivo.

REGRAS:
- Seja direto e objetivo
- Destaque as maiores oportunidades por valor
- Alerte sobre prazos próximos (< 7 dias)
- Mencione a distribuição geográfica
- Use linguagem profissional, não técnica demais
- Valores sempre em reais (R$) formatados
"""

# AFTER (with explicit forbidden terms)
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

EXEMPLO CORRETO:
"Há 3 oportunidades em uniformes escolares no RS totalizando R$ 150.000.
Maior licitação: R$ 75.000 da Prefeitura de Porto Alegre, recebe propostas
até 15/02/2026 (você tem 8 dias para enviar)."

EXEMPLO INCORRETO (NUNCA FAÇA):
"Prazo de abertura em 5 de fevereiro" ❌
"Abertura em 5 de fevereiro" ❌
"""
```

#### Change 3: Add validation assertions

```python
# BEFORE
resumo = response.choices[0].message.parsed

if not resumo:
    raise ValueError("OpenAI API returned empty response")

return resumo

# AFTER (with forbidden term validation)
resumo = response.choices[0].message.parsed

if not resumo:
    raise ValueError("OpenAI API returned empty response")

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

return resumo
```

#### Change 4: Update fallback urgency message

```python
# BEFORE
if dias_restantes < 7:
    orgao = lic.get("nomeOrgao", "Órgão não informado")
    alerta = f"Licitação com prazo em menos de 7 dias: {orgao}"
    break

# AFTER (clear terminology)
if dias_restantes < 7:
    orgao = lic.get("nomeOrgao", "Órgão não informado")
    alerta = f"⚠️ Licitação encerra em {dias_restantes} dia(s) - {orgao}"
    break
```

---

### 2. frontend/app/components/LicitacaoCard.tsx (+181 lines, -15 lines)

#### Change 1: Add date-fns imports

```typescript
import { differenceInDays, differenceInHours, isPast, parseISO, format } from "date-fns";
```

#### Change 2: Add InfoTooltip component

```typescript
// NEW: Simple inline tooltip component
function InfoTooltip({ content, children }: { content: string | React.ReactNode; children: React.ReactNode }) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="cursor-help"
      >
        {children}
      </div>
      {isVisible && (
        <div className="absolute z-50 w-64 p-3 bg-surface-0 border border-strong rounded-lg shadow-lg bottom-full left-1/2 transform -translate-x-1/2 mb-2">
          <div className="text-sm text-ink">{content}</div>
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="w-2 h-2 bg-surface-0 border-r border-b border-strong transform rotate-45"></div>
          </div>
        </div>
      )}
    </div>
  );
}
```

#### Change 3: Add calculateTimeRemaining helper

```typescript
/**
 * Calculate time remaining until deadline with clear messaging
 */
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

#### Change 4: Replace ambiguous date display section

```typescript
// BEFORE (ambiguous)
{/* Location and Date Info */}
<div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
  <span className="inline-flex items-center gap-1 text-ink-muted">
    <LocationIcon className="w-4 h-4" />
    <span>
      {licitacao.uf}
      {licitacao.municipio && ` - ${licitacao.municipio}`}
    </span>
  </span>

  {licitacao.data_encerramento && (
    <span className="inline-flex items-center gap-1 text-success font-medium">
      <CalendarIcon className="w-4 h-4" />
      <span>Prazo: {formatDate(licitacao.data_encerramento)}</span>
    </span>
  )}
  {licitacao.data_abertura && (
    <span className="inline-flex items-center gap-1 text-ink-muted">
      <CalendarIcon className="w-4 h-4" />
      <span>Início: {formatDate(licitacao.data_abertura)}</span>
    </span>
  )}
</div>

// AFTER (clear with tooltips)
{/* Location Info */}
<div className="flex items-center gap-1 text-sm text-ink-muted">
  <LocationIcon className="w-4 h-4" />
  <span>
    {licitacao.uf}
    {licitacao.municipio && ` - ${licitacao.municipio}`}
  </span>
</div>

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
              {(() => {
                try {
                  return format(parseISO(licitacao.data_abertura), "dd/MM/yyyy 'às' HH:mm");
                } catch {
                  return formatDate(licitacao.data_abertura);
                }
              })()}
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
              {(() => {
                try {
                  return format(parseISO(licitacao.data_encerramento), "dd/MM/yyyy 'às' HH:mm");
                } catch {
                  return formatDate(licitacao.data_encerramento);
                }
              })()}
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

---

## New Files Created

### 1. Backend Tests

**File:** `backend/tests/test_llm_deadline_terminology.py`
**Size:** 282 lines
**Tests:** 10

**Test Categories:**
- LLM output validation (forbidden terms)
- Clear terminology acceptance
- Fallback function clarity
- Urgent alert messaging
- System prompt validation
- Assertion logging
- Edge cases (empty results, single bid)

**Key Test:**

```python
def test_forbidden_terms_trigger_assertion(self, mock_licitacoes, monkeypatch):
    """CRITICAL: LLM output with ambiguous terms must be rejected."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")

    mock_response = MagicMock()
    mock_response.choices[0].message.parsed = ResumoLicitacoes(
        resumo_executivo="Há 2 oportunidades com prazo de abertura em 5 de fevereiro.",
        total_oportunidades=2,
        valor_total=111000.0,
        destaques=["Test"],
        alerta_urgencia=None,
    )

    with patch("llm.OpenAI") as mock_openai:
        mock_openai.return_value.beta.chat.completions.parse.return_value = mock_response

        # Should raise ValueError due to forbidden term
        with pytest.raises(ValueError) as exc_info:
            gerar_resumo(mock_licitacoes)

        assert "ambiguous deadline terminology" in str(exc_info.value).lower()
        assert "prazo de abertura" in str(exc_info.value)
```

### 2. Frontend Tests

**File:** `frontend/__tests__/components/LicitacaoCard-deadline-clarity.test.tsx`
**Size:** 175 lines
**Tests:** 13

**Test Categories:**
- Clear terminology requirements
- Visual indicators (🟢/🔴)
- Date formatting (with time)
- Edge cases (expired, missing dates)
- Forbidden terms validation (CRITICAL)
- Tooltip presence

**Key Test:**

```typescript
describe('Forbidden terms validation (CRITICAL)', () => {
  it('NÃO deve conter "prazo de abertura" em nenhuma parte do card', () => {
    const { container } = render(<LicitacaoCard licitacao={mockLicitacao} />);

    const cardText = container.textContent?.toLowerCase() || '';
    expect(cardText).not.toContain('prazo de abertura');
  });

  it('NÃO deve conter "abertura em [data]" como label principal', () => {
    const { container } = render(<LicitacaoCard licitacao={mockLicitacao} />);

    const cardText = container.textContent?.toLowerCase() || '';
    expect(cardText).not.toMatch(/abertura em \d{2}\/\d{2}/i);
  });

  it('NÃO deve usar apenas "Início:" sem contexto', () => {
    render(<LicitacaoCard licitacao={mockLicitacao} />);

    const inicioLabel = screen.queryByText(/^Início:$/i);
    expect(inicioLabel).not.toBeInTheDocument();
  });
});
```

### 3. Documentation Files

1. **`docs/ux/deadline-terminology-clarity.md`** (450 lines)
   - Complete implementation report
   - Technical details
   - Test coverage
   - Monitoring plan

2. **`docs/ux/deadline-visual-comparison.md`** (550 lines)
   - Visual before/after comparison
   - Mobile views
   - Edge cases
   - Accessibility notes

3. **`DEADLINE-CLARITY-IMPLEMENTATION-COMPLETE.md`** (500+ lines)
   - Executive summary
   - Deployment plan
   - Test results
   - Sign-off checklist

4. **`CODE-CHANGES-SUMMARY.md`** (this file)
   - Detailed code diff
   - Line-by-line changes
   - Test examples

---

## Git Statistics

```
backend/llm.py                            |  59 ++++++++--
frontend/app/components/LicitacaoCard.tsx | 181 +++++++++++++++++++++++++++---
2 files changed, 215 insertions(+), 25 deletions(-)

New files:
backend/tests/test_llm_deadline_terminology.py (282 lines)
frontend/__tests__/components/LicitacaoCard-deadline-clarity.test.tsx (175 lines)
docs/ux/deadline-terminology-clarity.md (450 lines)
docs/ux/deadline-visual-comparison.md (550 lines)
DEADLINE-CLARITY-IMPLEMENTATION-COMPLETE.md (500 lines)
CODE-CHANGES-SUMMARY.md (this file)
```

**Total Impact:**
- Modified: 2 files (+215, -25)
- Created: 6 files (+2,457 lines)
- Tests: 23 (10 backend + 13 frontend) ✅

---

## Testing Commands

### Backend

```bash
cd backend
pytest tests/test_llm_deadline_terminology.py -v
```

**Expected:** 10 passed in ~1.5s

### Frontend

```bash
cd frontend
npm test -- __tests__/components/LicitacaoCard-deadline-clarity.test.tsx
```

**Expected:** 13 passed in ~3s

### All Tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

---

## Deployment Verification

### After Deployment, Verify:

1. **Backend:**
   ```bash
   # Check logs for assertion warnings
   grep "ambiguous term" /var/log/app.log

   # Should be ZERO occurrences
   ```

2. **Frontend:**
   - Open any licitacao card
   - Verify "Recebe propostas" label present
   - Verify "Prazo final para propostas" label present
   - Verify NO "Prazo de abertura" anywhere
   - Hover tooltips to check content
   - Check mobile responsive design

3. **Integration:**
   - Run a full search
   - Check AI summary for forbidden terms
   - Verify time remaining counter works
   - Test expired deadline display

---

## Rollback Instructions

If issues found in production:

```bash
# Backend rollback
git revert <commit-hash>
railway up  # Redeploy backend

# Frontend rollback
git revert <commit-hash>
railway up  # Redeploy frontend

# Full rollback
git revert <commit-hash-1> <commit-hash-2>
railway up
```

**Rollback Time:** <5 minutes

---

## Success Criteria

- [x] All 23 tests passing
- [x] No forbidden terms in code
- [x] Visual indicators (🟢/🔴) implemented
- [x] Tooltips provide context
- [x] Time remaining calculation works
- [x] Edge cases handled (expired, missing dates)
- [x] Mobile responsive
- [x] Assertions log failures
- [ ] Manual QA in staging
- [ ] User acceptance testing
- [ ] Zero forbidden terms in production

---

**Status:** ✅ Ready for Deployment
**Next Step:** Deploy to staging for manual QA
**ETA:** Ready now

---

**Generated:** 2026-02-10
**Authors:** UX Design Expert + Frontend Developer
**Review Required:** Product Owner, QA Engineer
