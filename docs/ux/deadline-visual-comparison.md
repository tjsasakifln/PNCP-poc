# Deadline Terminology - Visual Comparison

## Before: Ambiguous and Confusing ❌

### LicitacaoCard (Old Design)

```
┌────────────────────────────────────────────────────────┐
│ [Verde] Aberta  │ Pregão Eletrônico  │  [🕒 5 dias]  │
├────────────────────────────────────────────────────────┤
│                                                        │
│ Confecção de fardamentos escolares para rede          │
│ municipal de ensino                                    │
│                                                        │
│ Prefeitura de Porto Alegre                            │
│                                                        │
│ 📍 RS - Porto Alegre                                   │
│ 📅 Prazo: 23/02/2026    📅 Início: 05/02/2026        │
│                                                        │
│ R$ 75.000                                              │
│                                                        │
│ 🏷️ uniforme  fardamento  escolar                      │
├────────────────────────────────────────────────────────┤
│ [Ver Edital] 🔗                           ❤️  📤      │
└────────────────────────────────────────────────────────┘
```

### Problems

1. **"Prazo:" is ambiguous**
   - User thinks: "Prazo means deadline, so 23/02 is when I need to submit"
   - Reality: It's actually the final deadline, but not labeled clearly

2. **"Início:" is vague**
   - User thinks: "Início of what? The procurement process?"
   - Reality: It's when proposal submission STARTS

3. **No time information**
   - Dates show day but not time (could be 00:00 or 23:59)

4. **No urgency indicator**
   - User doesn't know how much time they have left

5. **No educational tooltips**
   - First-time users have no help understanding terms

### AI Summary (Old - Ambiguous)

```
📊 Resumo Executivo

"Há 3 oportunidades de uniformes escolares no RS com prazo de
abertura em 5 de fevereiro, totalizando R$ 186.000."
```

**User interpretation:**
> "I have until February 5th to submit my proposal" ❌

**Actual meaning:**
> "Proposal submission OPENS on February 5th" ✅

---

## After: Clear and Unambiguous ✅

### LicitacaoCard (New Design)

```
┌────────────────────────────────────────────────────────┐
│ [Verde] Aberta  │ Pregão Eletrônico  │  [🕒 5 dias]  │
├────────────────────────────────────────────────────────┤
│                                                        │
│ Confecção de fardamentos escolares para rede          │
│ municipal de ensino                                    │
│                                                        │
│ Prefeitura de Porto Alegre                            │
│                                                        │
│ 📍 RS - Porto Alegre                                   │
│                                                        │
│ ┌──────────────────────────────────────────────────┐  │
│ │ 🟢 Recebe propostas                       [ⓘ]   │  │
│ │    05/02/2026 às 09:00                           │  │
│ │                                                  │  │
│ │ 🔴 Prazo final para propostas             [ⓘ]   │  │
│ │    23/02/2026 às 18:00                           │  │
│ │                                                  │  │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │  │
│ │ 🕒 Você tem 13 dias e 8h restantes              │  │
│ └──────────────────────────────────────────────────┘  │
│                                                        │
│ R$ 75.000                                              │
│                                                        │
│ 🏷️ uniforme  fardamento  escolar                      │
├────────────────────────────────────────────────────────┤
│ [Ver Edital] 🔗                           ❤️  📤      │
└────────────────────────────────────────────────────────┘
```

### Improvements

1. **✅ "Recebe propostas" - Crystal clear**
   - User understands: "This is when I CAN START submitting"
   - No ambiguity about whether it's a deadline or opening date

2. **✅ "Prazo final para propostas" - Explicit context**
   - User understands: "This is my FINAL DEADLINE to submit"
   - Can't be confused with start date

3. **✅ Time included (HH:mm)**
   - User knows: "I have until 18:00, not just the day"
   - Critical for same-day submissions

4. **✅ Visual indicators (🟢/🔴)**
   - Green = Start/Opening
   - Red = Deadline/Closing
   - Color-coded for quick scanning

5. **✅ Time remaining counter**
   - User knows: "I have exactly 13 days and 8 hours left"
   - Creates urgency without confusion

6. **✅ Tooltips [ⓘ] on hover**
   ```
   [Hover over 🟢 Recebe propostas]

   ┌────────────────────────────────────┐
   │ Data de início                     │
   │                                    │
   │ Esta é a data em que a licitação   │
   │ começa a receber propostas. Você   │
   │ pode enviar sua proposta a partir  │
   │ deste momento.                     │
   └────────────────────────────────────┘
   ```

   ```
   [Hover over 🔴 Prazo final]

   ┌────────────────────────────────────┐
   │ Data limite                        │
   │                                    │
   │ Esta é a data e hora limite para   │
   │ envio de propostas. Após este      │
   │ momento, o sistema não aceita mais │
   │ submissões.                        │
   │                                    │
   │ ⚠️ Importante: Envie com           │
   │ antecedência para evitar problemas │
   │ técnicos de última hora.           │
   └────────────────────────────────────┘
   ```

### AI Summary (New - Clear)

```
📊 Resumo Executivo

"Há 3 oportunidades de uniformes escolares no RS totalizando
R$ 186.000. Maior licitação: R$ 75.000 da Prefeitura de Porto
Alegre, recebe propostas até 23/02/2026 (você tem 13 dias para
enviar)."
```

**User interpretation:**
> "I can submit proposals until February 23rd. I have 13 days to prepare." ✅

**Actual meaning:**
> Same as interpretation ✅

---

## Edge Cases

### 1. Urgent Deadline (< 24h)

```
┌──────────────────────────────────────────────────┐
│ 🟢 Recebe propostas                              │
│    05/02/2026 às 09:00                           │
│                                                  │
│ 🔴 Prazo final para propostas                    │
│    10/02/2026 às 18:00                           │
│                                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│ ⏰ Você tem 6h restantes                         │
│    [Background: Yellow with pulse animation]     │
└──────────────────────────────────────────────────┘
```

### 2. Expired Deadline

```
┌──────────────────────────────────────────────────┐
│ 🟢 Recebe propostas                              │
│    05/02/2026 às 09:00                           │
│                                                  │
│ 🔴 Prazo final para propostas                    │
│    08/02/2026 às 18:00                           │
│                                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│ ⛔ Prazo encerrado                                │
│    [Gray background]                             │
└──────────────────────────────────────────────────┘
```

### 3. No Start Date (Data Missing)

```
┌──────────────────────────────────────────────────┐
│ 🔴 Prazo final para propostas                    │
│    23/02/2026 às 18:00                           │
│                                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│ ⏰ Você tem 13 dias e 8h restantes              │
└──────────────────────────────────────────────────┘
```

### 4. Very Urgent (< 3h) - Critical Alert

```
┌──────────────────────────────────────────────────┐
│ 🟢 Recebe propostas                              │
│    05/02/2026 às 09:00                           │
│                                                  │
│ 🔴 Prazo final para propostas                    │
│    10/02/2026 às 15:00                           │
│                                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│ 🚨 URGENTE! Você tem 2h restantes               │
│    [Red background with pulse animation]         │
└──────────────────────────────────────────────────┘
```

---

## Mobile View Adaptation

### Before (Stacked, Ambiguous)

```
┌───────────────────────┐
│ [Verde] Aberta        │
├───────────────────────┤
│ Confecção de...       │
│ Prefeitura de POA     │
│                       │
│ 📍 RS                 │
│ 📅 Prazo: 23/02       │
│ 📅 Início: 05/02      │
│                       │
│ R$ 75.000             │
│                       │
│ [Ver Edital]          │
└───────────────────────┘
```

### After (Stacked, Clear)

```
┌───────────────────────┐
│ [Verde] Aberta        │
├───────────────────────┤
│ Confecção de...       │
│ Prefeitura de POA     │
│                       │
│ 📍 RS                 │
│                       │
│ ┌─────────────────┐   │
│ │ 🟢 Recebe       │   │
│ │    05/02 09:00  │   │
│ │                 │   │
│ │ 🔴 Prazo final  │   │
│ │    23/02 18:00  │   │
│ │                 │   │
│ │ ─────────────   │   │
│ │ ⏰ 13d 8h       │   │
│ └─────────────────┘   │
│                       │
│ R$ 75.000             │
│                       │
│ [Ver Edital]          │
└───────────────────────┘
```

---

## Terminology Dictionary

### ✅ Approved Terms

| Term | Meaning | Use Case |
|------|---------|----------|
| **Recebe propostas** | When proposal submission opens | Start date label |
| **Prazo final para propostas** | Final deadline for submissions | End date label |
| **Você tem X dias restantes** | Time remaining counter | Urgency indicator |
| **Encerra em X dias** | Days until closure | Urgency alert |
| **Prazo encerrado** | Deadline has passed | Expired state |

### ❌ Forbidden Terms

| Term | Why Forbidden | Risk |
|------|--------------|------|
| **Prazo de abertura** | "Prazo" (deadline) + "abertura" (opening) is contradictory | Users think it's submission deadline |
| **Abertura em [data]** | Unclear what is "opening" | Users confuse with deadline |
| **Prazo:** (alone) | Context-free, could mean anything | Ambiguous reference |
| **Início:** (alone) | Too generic | Users don't know what starts |

---

## User Testing Results (Hypothetical)

### Before Implementation

**Task:** "When do you need to submit your proposal for this bid?"

| User | Answer | Correct? |
|------|--------|----------|
| User A | "By February 5th" | ❌ (Confused start with deadline) |
| User B | "Um... I'm not sure. 23rd?" | ⚠️ (Uncertain) |
| User C | "Is it the 5th or 23rd?" | ❌ (Complete confusion) |
| User D | "February 23rd" | ✅ (Lucky guess) |
| User E | "The início date?" | ❌ (Misunderstood term) |

**Success Rate:** 20% (1/5)

### After Implementation

**Task:** "When do you need to submit your proposal for this bid?"

| User | Answer | Correct? |
|------|--------|----------|
| User A | "February 23rd at 6pm" | ✅ |
| User B | "23/02 by 18:00" | ✅ |
| User C | "I have 13 days until 23rd" | ✅ |
| User D | "Final deadline is 23/02" | ✅ |
| User E | "23rd February, 6pm" | ✅ |

**Success Rate:** 100% (5/5) ✅

---

## Accessibility Improvements

### Color Blindness

- ✅ Icons (🟢/🔴) include text labels
- ✅ Not relying solely on color for meaning
- ✅ Borders and structure provide context

### Screen Readers

```html
<div aria-label="Informações de prazo">
  <div aria-label="Data de início de recebimento de propostas">
    Recebe propostas: 05/02/2026 às 09:00
  </div>
  <div aria-label="Data limite final para envio de propostas">
    Prazo final para propostas: 23/02/2026 às 18:00
  </div>
  <div aria-label="Tempo restante até o prazo">
    Você tem 13 dias e 8 horas restantes
  </div>
</div>
```

### Keyboard Navigation

- ✅ Tooltips accessible via keyboard focus
- ✅ Tab order follows visual hierarchy
- ✅ Enter/Space activates tooltips

---

## Implementation Checklist

- [x] Backend prompt updated
- [x] Backend assertions added
- [x] Frontend visual redesign
- [x] Tooltip component created
- [x] Time remaining calculator
- [x] Edge case handling
- [x] Mobile responsive design
- [x] Accessibility attributes
- [x] Color contrast validation
- [x] Backend tests (10)
- [x] Frontend tests (13)
- [ ] Manual QA in staging
- [ ] User acceptance testing
- [ ] Production deployment
- [ ] Monitor assertion failures
- [ ] A/B test for user comprehension

---

**Next Steps:**

1. Deploy to staging environment
2. Conduct user testing with 10 users
3. Measure comprehension rate (target: >90%)
4. Monitor LLM assertion logs
5. Deploy to production if successful
6. Create glossary page for additional education
