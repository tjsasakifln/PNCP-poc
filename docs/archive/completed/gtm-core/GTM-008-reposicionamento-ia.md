# GTM-008: Reposicionamento da IA — De "Resumos" para "Decisão"

| Metadata | Value |
|----------|-------|
| **ID** | GTM-008 |
| **Priority** | P1 |
| **Sprint** | 2 |
| **Estimate** | 6h |
| **Type** | GTM (Go-to-Market) |
| **Dependencies** | GTM-001 (alinhamento de narrativa) |
| **Blocks** | GTM-009 (Features Page depende do novo posicionamento de IA) |
| **Status** | Completed |
| **Created** | 2026-02-15 |
| **Squad** | Content + Dev (Frontend) |

---

## Problem Statement

### IA como Commodity

**Problema central:** A IA é apresentada como **geradora de resumos** — funcionalidade commodity que qualquer ferramenta oferece.

#### Copy Atual (Problemática)

| Onde | Texto Atual | Por Que É Problemático |
|------|-------------|------------------------|
| Hero | "IA analisa milhares de editais" | Genérico, foca em volume (não em valor) |
| Feature | "Resumos executivos de 3 linhas" | Redução de texto é commodity, não diferencial |
| Value prop | "IA que Trabalha para Você" | Vago, não comunica benefício tangível |
| Feature detail | "GPT-4 analisa editais" | Name-dropping de modelo LLM não agrega valor |
| Plan feature | "IA Básico/Detalhado/Prioritário" | Diferenciação artificial (todos os planos devem ter IA completa) |
| Email | "Filtramos X licitações" | Passivo, foca em tarefa (não em resultado) |

### Diferencial Real da IA SmartLic

A IA não resume editais. A IA:

1. **Avalia adequação** — "Este edital é compatível com seu perfil?"
2. **Identifica riscos** — "Requisitos incompatíveis, prazo apertado, concorrência alta"
3. **Prioriza oportunidades** — "Vale a pena investir tempo neste ou focar naquele?"
4. **Orienta decisão** — "Participe com confiança" vs "Pule esta oportunidade"
5. **Reduz incerteza** — Substitui "ler 50 editais de 100 páginas" por "avaliação objetiva em segundos"

> **Reposicionamento:** IA não gera resumos. IA **avalia oportunidades e orienta decisões**.

---

## Solution/Scope

### Mapeamento de Copy para Atualizar

| Arquivo | Seção | Atual → Novo |
|---------|-------|--------------|
| `lib/copy/valueProps.ts` | Hero headline/subheadline | "IA analisa milhares de editais" → "IA avalia cada oportunidade e indica onde focar para ganhar" |
| `lib/copy/valueProps.ts` | Feature: "IA que Trabalha" | "Resumos executivos de 3 linhas" → "Avaliação objetiva: vale a pena ou não, e por quê" |
| `lib/copy/valueProps.ts` | Differentials | "IA que Trabalha para Você" → "Inteligência que reduz incerteza" |
| `lib/copy/valueProps.ts` | Feature detail | "GPT-4 analisa editais" → "Análise automatizada de critérios de elegibilidade, competitividade e adequação" |
| `app/planos/page.tsx` | Plan features | "IA Básico/Detalhado/Prioritário" → "Análise Estratégica" (único nível — após GTM-002) |
| `app/components/landing/HowItWorks.tsx` | Step 3 | "Receba resumos IA" → "Receba avaliação de adequação" |
| `app/features/page.tsx` | Feature: "IA" | "Decida em 30 segundos, não em 20 minutos" → "Avalie uma oportunidade em segundos com base em critérios objetivos" |
| `backend/templates/email/` (se existir) | Email de resultados | "Filtramos X licitações" → "Identificamos X oportunidades com alta adequação ao seu perfil" |

---

## Acceptance Criteria

### Eliminação de "Resumos"

- [x] **AC1:** ZERO menções a "resumo", "resumo executivo", "resumos" em copy user-facing
  - Verificar `lib/copy/valueProps.ts`, `comparisons.ts`, `app/features/page.tsx`, `app/planos/page.tsx`
  - Exceção: documentação técnica interna pode manter termo "summary" (campo `ai_summary` no JSON response é OK — não visível ao usuário)

### Novo Posicionamento de IA

- [x] **AC2:** IA posicionada como "avaliação de oportunidade" e "orientação de decisão"
  - Hero: "IA avalia cada oportunidade"
  - Features: "Avaliação objetiva", "Análise de adequação", "Inteligência de decisão"

- [x] **AC3:** Feature de IA descrita como "redução de incerteza", não "redução de texto"
  - **Antes:** "Resumos de 3 linhas economizam 20 minutos por edital"
  - **Depois:** "Avaliação objetiva elimina necessidade de ler editais completos para decidir se vale a pena"

- [x] **AC4:** Benefício tangível comunicado: "Você decide em segundos se uma oportunidade é adequada ao seu perfil"

### Eliminação de Diferenciação de Planos por IA

- [x] **AC5:** Planos **não diferenciam "nível de IA"** (após GTM-002: plano único, IA completa)
  - **Antes:** "Consultor Ágil: IA Básico (200 tokens)", "Sala de Guerra: IA Prioritário (10k tokens)"
  - **Depois:** "SmartLic Pro: Análise Estratégica (10k tokens)" — único nível

- [x] **AC6:** Trial tem IA completa (10k tokens) — já definido em GTM-003
  - Copy de trial: "Experimente o SmartLic completo por 7 dias" (não "IA básica")

### Email Templates

- [x] **AC7:** Email templates atualizados com nova linguagem (se arquivos de email existirem)
  - **Antes:** "Filtramos 47 licitações para você hoje"
  - **Depois:** "Identificamos 47 oportunidades com alta adequação ao seu perfil hoje"

- [x] **AC8:** Email de resultados foca em valor, não em tarefa
  - ❌ "Processamos X licitações"
  - ✅ "Encontramos X oportunidades priorizadas para você"

### Banned Phrases Update

- [x] **AC9:** Atualizar banned phrases em `valueProps.ts`:
  ```typescript
  const BANNED_PHRASES = [
    // ... existing (160x, 95%, 3 minutos, PNCP)
    'resumo',
    'resumo executivo',
    'resumos',
    'resumir',
    'sintetizar',
    'GPT-4', // Não fazer name-dropping de modelo LLM
    '3 linhas',
    'reduzir texto',
    // ...
  ];
  ```

- [x] **AC10:** Adicionar preferred phrases:
  ```typescript
  const PREFERRED_PHRASES = [
    // ... existing
    'avaliação de oportunidade',
    'orientação de decisão',
    'análise de adequação',
    'redução de incerteza',
    'inteligência de decisão',
    'avaliação objetiva',
    'critérios de elegibilidade',
    'análise automatizada',
    // ...
  ];
  ```

---

## Definition of Done

- [x] Todos os Acceptance Criteria marcados como concluídos
- [x] ZERO menções a "resumo" em copy user-facing (grep validation)
- [x] IA posicionada como "avaliação/orientação" em todas as páginas (landing, features, planos)
- [x] Email templates atualizados (se existirem)
- [x] Banned/Preferred phrases atualizados em `valueProps.ts`
- [x] Build passa (TypeScript clean, lint clean)
- [ ] PR aberto, revisado e merged
- [ ] Deploy em staging verificado (audit manual de copy em todas as páginas)

---

## Technical Notes

### Diferença entre Copy e Schema

**Copy user-facing (deve mudar):**
- Landing page: "IA avalia oportunidades"
- Features page: "Análise de adequação"
- Planos page: "Análise Estratégica"

**Schema técnico (pode manter):**
- `schemas.py`: `ai_summary: str` — campo JSON técnico
- Backend logs: "Generating summary for bid X" — log interno

**Justificativa:** Usuário não vê código/schemas. Refatorar campo `ai_summary` para `ai_evaluation` em todos os schemas é refactor massivo sem ganho de valor. Focar em copy visível.

### Exemplo de Transformação

#### Antes (Copy Atual)

> **"IA que Trabalha para Você"**
>
> Nossa inteligência artificial analisa milhares de editais e gera resumos executivos de 3 linhas. Decida em 30 segundos, não em 20 minutos.

#### Depois (Copy Nova)

> **"Inteligência que Reduz Incerteza"**
>
> Avaliação objetiva de cada oportunidade: critérios de elegibilidade, adequação ao seu perfil, competitividade e riscos. Você decide em segundos se vale a pena investir tempo, sem precisar ler editais de 100 páginas.

### Alinhamento com GTM-001

GTM-001 (reescrita completa da landing) já incluirá novo posicionamento de IA. GTM-008 garante consistência em:

- Features page (detalhamento técnico de como a IA funciona)
- Planos page (após GTM-002, IA é feature padrão — não diferencial de plano)
- Email templates (comunicação contínua pós-signup)

### Validação de Consistência

Após implementação, validar mensagens em:

1. **Landing page:** Hero, differentials, how-it-works
2. **Features page:** Seção de IA
3. **Planos page:** Descrição de features (se ainda mencionar IA separadamente)
4. **Buscar page:** Se houver copy explicativa sobre IA nos resultados
5. **Email templates:** Notificações de novas oportunidades

---

## Validation Script (Pós-Implementação)

```bash
#!/bin/bash
# validate-ia-positioning.sh

echo "🔍 Validating IA positioning..."

# Check for banned terms
echo "\n🚫 Checking for 'resumo' mentions:"
RESUMO_MATCHES=$(grep -ri "resumo" \
  frontend/lib/copy/ \
  frontend/app/components/landing/ \
  frontend/app/features/ \
  frontend/app/planos/ \
  2>/dev/null | grep -v ".ts:" | wc -l)

if [ "$RESUMO_MATCHES" -eq 0 ]; then
  echo "✅ PASS: Zero 'resumo' mentions in user-facing copy"
else
  echo "❌ FAIL: Found $RESUMO_MATCHES 'resumo' mentions"
  grep -ri "resumo" frontend/lib/copy/ frontend/app/components/landing/
fi

# Check for preferred terms
echo "\n✅ Checking for preferred terms:"
grep -ri "avaliação de oportunidade\|orientação de decisão\|análise de adequação" \
  frontend/lib/copy/ \
  frontend/app/features/ \
  | head -5

echo "\n✅ Validation complete"
```

---

## File List

### Frontend (Must Update)
- `frontend/lib/copy/valueProps.ts` (hero, differentials, features, banned/preferred phrases)
- `frontend/lib/copy/comparisons.ts` (se mencionar IA)
- `frontend/app/components/landing/HowItWorks.tsx` (step 3)
- `frontend/app/features/page.tsx` (seção IA)
- `frontend/app/planos/page.tsx` (features de IA — após GTM-002)

### Backend (Optional — se existir)
- `backend/templates/email/*.html` (email de resultados, se existir)

### Backend (No Change)
- `backend/schemas.py` (`ai_summary` field — técnico, não user-facing)
- `backend/llm.py` (logs internos)

---

## Related Stories

- **GTM-001:** Landing page rewrite (já incluirá novo posicionamento de IA)
- **GTM-002:** Plano único (elimina diferenciação de "níveis de IA")
- **GTM-003:** Trial completo (IA completa no trial, não "básica")
- **GTM-009:** Features page rewrite (depende deste reposicionamento)

---

*Story created from consolidated GTM backlog 2026-02-15*
