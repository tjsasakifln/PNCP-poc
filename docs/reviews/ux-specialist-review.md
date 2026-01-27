# UX/Frontend Specialist Review
**BidIQ Uniformes POC v0.2**

**Revisor:** @ux-design-expert
**Data:** January 26, 2026
**DRAFT:** `docs/prd/technical-debt-DRAFT.md`

---

## Débitos Validados

| ID | Débito | Severidade | Horas | Prioridade | Validado? | Notas |
|----|--------|-----------|-------|-----------|-----------|-------|
| FE-001 | Frontend structure not created | CRÍTICO | 4-6 | P0 | ✅ SIM | Bloqueador crítico, deve ser prioridade 1 |
| FE-002 | Core components not implemented | CRÍTICO | 8-10 | P0 | ✅ SIM | UFSelector, DatePicker, ResultsTable, SummaryCard são essenciais |
| FE-003 | API routes not implemented | CRÍTICO | 2-3 | P0 | ✅ SIM | /api/buscar e /api/download são mínimos necessários |
| FE-004 | Error handling UI missing | ALTO | 3-4 | P1 | ✅ SIM | Crítico para UX - usuários precisam feedback em falhas |
| FE-005 | Loading states not implemented | ALTO | 2-3 | P1 | ✅ SIM | Skeleton loaders + spinner são importantes |
| FE-006 | Form validation feedback missing | ALTO | 2-3 | P1 | ✅ SIM | Validação silenciosa é confusa, precisa feedback visual |
| FE-007 | Mobile responsiveness untested | ALTO | 4-5 | P1 | ✅ SIM | Tailwind está ali, mas precisa testar em dispositivos reais |
| FE-008 | WCAG accessibility not implemented | ALTO | 4-5 | P1 | ⚠️ AJUSTADO | Importante, mas pode ser Phase 2. MVP pode ser WCAG A instead of AA |
| FE-009 | Help/documentation UI missing | MÉDIO | 2-3 | P2 | ✅ SIM | Inline tooltips simples é suficiente |
| FE-010 | Download management limited | MÉDIO | 4-5 | P2 | ✅ SIM | Single download é OK para MVP |
| FE-011 | Advanced filters not available | MÉDIO | 6-8 | P2 | ✅ SIM | MVP: apenas UF + data. Value range slider pode ser Phase 2 |
| FE-012 | Pagination missing for large results | MÉDIO | 4-6 | P2 | ✅ SIM | Use virtual scrolling ou lazy load se resultsexcederem 100 items |

**Total Débitos Validados:** 12/12 ✅

---

## Débitos Adicionados

| ID | Novo Débito | Severidade | Horas | Prioridade |
|----|-------------|-----------|-------|-----------|
| FE-013 | Color contrast not validated | MÉDIO | 1-2 | P2 |
| FE-014 | Font optimization missing | BAIXO | 1 | P3 |
| FE-015 | Image optimization strategy missing | BAIXO | 2 | P3 |

**Subtotal Novos:** 3 débitos, 4-5 horas

---

## Respostas ao Architect

### Pergunta: Componentes propostos cobrem o caso de uso?

**Resposta:** ✅ SIM, com adição de 1 novo componente:

**Propostos e APROVADOS:**
1. UFSelector ✅ - Multi-select 27 estados é perfeito
2. DateRangePicker ✅ - Smart default (last 7 days) é bom
3. ResultsTable ✅ - Tabela é a melhor visualização para dados de procurement
4. SummaryCard ✅ - GPT summary é diferencial importante

**Recomendação ADICIONAL:**
5. **ErrorAlert Component** (ainda não listado): para mostrar erros de forma destacada

---

### Pergunta: UX Flow (search → filter → results → download) é suficiente?

**Resposta:** ✅ SIM, para MVP é suficiente. Fluxo é simples e limpo.

**Sugestão:** Adicionar "Clear Filters" button e "New Search" button para melhor UX.

---

### Pergunta: Mobile-first ou desktop-first?

**Resposta:** **Desktop-first para MVP**, mobile-friendly depois.

**Justificativa:**
- Procurement contracts consultam em desktop geralmente
- Tailwind responsive classes já estão no lugar
- Mobile testing é Phase 3
- Não é bloqueador para MVP

---

### Pergunta: Nível de WCAG (A, AA, AAA)?

**Resposta:** **WCAG A para MVP, AA para Phase 2**.

**Justificativa:**
- WCAG A: ~4-5 horas (Phase 1)
- WCAG AA: +4-5 horas (Phase 2)
- MVP pode ter color contrast simples + keyboard nav
- AA é melhor mas pode esperar

---

### Pergunta: Quando incluir advanced filters (value range, keywords)?

**Resposta:** **Phase 2 (post-MVP)**

**MVP:** UF + Data range apenas (suficiente para validar produto)
**Phase 2:** Value range slider + keyword search UI

---

### Pergunta: Tailwind puro ou componentes customizados?

**Resposta:** **Tailwind puro para MVP**.

**Justificativa:**
- Mais rápido
- Menos dependências
- Pode refatorar para Headless UI depois
- Tailwind utilities são sufficients

---

### Pergunta: Melhor UX para comunicar estado?

**Resposta:**
- **Buscando:** Spinner + "Buscando X resultados..." no ResultsTable area
- **Erro:** ErrorAlert component com retry button
- **Nenhum resultado:** Mensagem limpa "Nenhuma oportunidade encontrada para XYZ"

---

### Pergunta: Download management - single vs multiple?

**Resposta:** **Single download é OK para MVP**.

- Current design: Excel cached 10min, download by ID
- Multiple simultaneous: Can add later if needed
- History: Phase 2 (nice-to-have)

---

## Recomendações de Design

### 1. Component Implementation Order

**Priority 1 (Week 1):**
1. UFSelector - Simple multi-button grid
2. DateRangePicker - HTML5 date inputs
3. ResultsTable - Basic table with styling
4. ErrorAlert - Visible error messages

**Priority 2 (Week 1-2):**
5. SummaryCard - Display GPT summary
6. LoadingSkeletons - Placeholder rows during fetch

---

### 2. UX Flow Diagram

```
┌─────────────────────────────────────────┐
│ User lands on page                      │
│ - UF selector (27 states buttons)       │
│ - Date range picker (smart default)     │
│ - Search button                         │
└─────────────┬───────────────────────────┘
              ↓
       [User clicks Search]
              ↓
      ┌──────────────────────┐
      │ Loading state        │
      │ - Skeleton loaders   │
      │ - Spinner + message  │
      └──────────┬───────────┘
                 ↓
      ┌──────────────────────┐
      │ Results received     │
      ├──────────────────────┤
      │ - Summary Card       │ ← GPT summary
      │ - Results Table      │ ← All bids
      │ - Download Button    │ ← Excel export
      └──────────────────────┘

ERROR PATH:
      ↓
   Backend/Network Error
      ↓
 ┌──────────────────────┐
 │ Error Alert          │
 │ - Error message      │
 │ - Retry button       │
 └──────────────────────┘
```

---

### 3. Component Props & Interfaces

**UFSelector:**
```typescript
interface UFSelectorProps {
  selected: Set<string>;
  onChange: (ufs: Set<string>) => void;
}
// Renders 27 state buttons in 3x9 grid
// Visual: green when selected, gray when not
```

**DateRangePicker:**
```typescript
interface DateRangePickerProps {
  dateRange: { start: string; end: string };
  onChange: (range: { start: string; end: string }) => void;
}
// 2 HTML5 date inputs side by side
// Default: today - 7 days
```

**ResultsTable:**
```typescript
interface ResultsTableProps {
  results: Licitacao[];
  loading: boolean;
  onDownload: () => void;
}
// Displays up to 1000 results (add virtualization if needed)
// Columns: Código, Objeto, Órgão, UF, Valor, Status, Link
// Download button after results load
```

**ErrorAlert:**
```typescript
interface ErrorAlertProps {
  message: string;
  onRetry: () => void;
}
// Red border, clear error message, retry button
```

---

### 4. Styling Guidelines

**Color Palette:**
- Primary Green: #2E7D32 (buttons, selected states)
- Neutral Gray: #F3F4F6 (backgrounds)
- Error Red: #DC2626 (error alerts)
- Success Green: #10B981 (success states)
- Border: #E5E7EB (light gray)

**Typography:**
- Headings: Bold, 18px-24px
- Body: Regular, 14px-16px
- Mono (for codes): 12px (e.g., bid codes)

**Spacing:**
- Padding: 6px, 12px, 24px (Tailwind standard)
- Gaps: 16px, 24px
- Margins: 12px, 24px, 32px

---

### 5. Accessibility Recommendations (Phase 1)

**Minimum (Phase 1):**
- [ ] Semantic HTML (headings, labels, buttons)
- [ ] Color not only visual indicator
- [ ] Focus indicators visible
- [ ] Button text clear ("Buscar", not "GO")
- [ ] Error messages linked to inputs

**Should Have (Phase 2):**
- [ ] ARIA labels on form inputs
- [ ] Keyboard navigation fully functional
- [ ] Screen reader tested
- [ ] Color contrast 4.5:1 for text

---

### 6. Performance Targets

**Frontend Bundle Size:**
- JavaScript: <100KB gzipped
- CSS (Tailwind): <50KB gzipped
- Fonts: <20KB (if any)
- **Total:** <200KB

**Core Web Vitals:**
- FCP (First Contentful Paint): <1.5s
- LCP (Largest Contentful Paint): <2.5s
- CLS (Cumulative Layout Shift): <0.1

**Optimization Strategy:**
- Code splitting (Next.js automatic)
- CSS purging (Tailwind + PurgeCSS)
- Image lazy loading (next/image)
- No blocking CSS/JS

---

### 7. Mobile Responsiveness Checklist (Phase 2)

- [ ] Mobile viewport 320px min width
- [ ] Touch targets 44px minimum
- [ ] Stacked layout on mobile (grid-cols-1)
- [ ] Readable font sizes (no < 14px)
- [ ] Horizontal scroll avoided
- [ ] Test on: iPhone 12, iPad, Android

---

## Impacto das Correções Propostas

### MVP Scope (Phase 1)

**Do:**
- Implement FE-001, FE-002, FE-003, FE-004, FE-005, FE-006 (27 horas)
- Tailwind styling only
- Basic error handling
- Desktop-first responsive

**Não faça:**
- Advanced filters (FE-011)
- Download history (FE-010)
- Pagination (FE-012)
- Full WCAG AA (FE-008)
- Font/image optimization (FE-014, FE-015)

**Resultado:** Funcional, usável, não perfeito

### Phase 2 (After MVP)

**Fazer:**
- FE-007: Mobile responsiveness (5h)
- FE-008: WCAG AA (5h)
- FE-009: Help/docs (3h)
- FE-011: Advanced filters (8h)
- FE-012: Pagination (6h)
- FE-013, FE-014, FE-015: Optimization (4-5h)

**Resultado:** Production-grade frontend

---

## Timeline Recomendado (UX View)

**Week 1: MVP (Core Components)**
```
Mon-Tue: FE-001 Create Next.js structure
Wed:     FE-002 Implement core 4 components
Thu:     FE-003 API routes + error handling
Fri:     FE-005 Loading states + finish styling
```

**Week 2: Testing & Polish**
```
Mon-Tue: FE-004, FE-006 Error/validation UI
Wed-Thu: Testing on desktop + mobile preview
Fri:     Bug fixes
```

**Week 3: Phase 2 (If timeline allows)**
```
Mon-Tue: Mobile responsiveness
Wed-Fri: Advanced features or more testing
```

---

## Questões Abertas para Architect

1. **Database:** Quando Supabase/PostgreSQL será integrado? Impacta Frontend?
   - Impact: User accounts, saved searches (Phase 2?)

2. **Authentication:** Será necessário antes de MVP?
   - Impact: Login UI, session management

3. **Analytics:** Quando implementar tracking?
   - Impact: Google Analytics, Sentry setup

4. **Notifications:** Real-time alerts sobre novos bids?
   - Impact: WebSocket integration (Phase 3?)

---

## Parecer Final

**Status: ✅ APROVADO PARA FASE 2**

**Débitos Frontend são claros, sequência é sensata.**

**MVP com 27-35 horas de trabalho frontend é realista (2 semanas com 1 dev full-time).**

**Não há bloqueadores técnicos - é trabalho direto sem surpresas esperadas.**

**Próximo passo:** Validação do @qa + consolidação final do @architect.

---

**Revisor:** @ux-design-expert
**Data:** January 26, 2026
**Assinado:** ✅ Revisão completa
