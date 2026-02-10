---
task: Update ModalidadeFilter UI Component - Lei 14.133
responsavel: "@frontend-engineer"
responsavel_type: agent
atomic_layer: task
elicit: false
priority: P0
phase: 4
parallel_execution: true
Entrada: |
  - Lei 14.133/2021 official modalities with article references
  - Current ModalidadeFilter.tsx component
  - Updated backend ModalidadeContratacao enum (codes 1-3, 6-7, 9-11)
  - UI/UX requirements from Lei specs
Saida: |
  - Updated MODALIDADES constant with all 8 official modalities
  - Removed deprecated modalities (codes 4, 5)
  - Added Concurso (code 11)
  - Updated descriptions with Lei article references
  - Maintained popular/unpopular categorization
  - Component tests updated
Checklist:
  - "[ ] Read current ModalidadeFilter.tsx"
  - "[ ] Update MODALIDADES constant"
  - "[ ] Remove Tomada de Preços (code 4)"
  - "[ ] Remove Convite (code 5)"
  - "[ ] Add Concurso (code 11)"
  - "[ ] Update Credenciamento (code 8) status"
  - "[ ] Update all descriptions with Lei articles"
  - "[ ] Set popular flags correctly"
  - "[ ] Update component tests"
  - "[ ] Verify accessibility (ARIA, keyboard nav)"
  - "[ ] Test visual rendering"
---

# Update ModalidadeFilter UI - Lei 14.133/2021

## Objective

Update the frontend ModalidadeFilter component to display all 8 official modalities from Lei 14.133/2021, remove deprecated Lei 8.666/93 modalities, and update descriptions with legal references.

## Background

**Current State:**
- Component at `frontend/components/ModalidadeFilter.tsx`
- `MODALIDADES` constant with codes 1-10
- Includes deprecated codes 4, 5, 8
- Generic descriptions without legal references
- Popular modalities: Pregão Eletrônico, Pregão Presencial, Dispensa

**Target State:**
- 8 official Lei 14.133 modalities (codes: 1, 2, 3, 6, 7, 9, 10, 11)
- Deprecated codes 4, 5 removed
- Descriptions reference Lei articles
- Popular flags optimized for user experience
- Full accessibility maintained

## Implementation Steps

### 1. Read Current Component

```bash
Read frontend/components/ModalidadeFilter.tsx
```

### 2. Update MODALIDADES Constant

**File:** `frontend/components/ModalidadeFilter.tsx`

**Current (Lines 29-83):** Has codes 1-10 including deprecated

**New Implementation:**

```typescript
const MODALIDADES: Modalidade[] = [
  // POPULAR MODALITIES (Always visible - most commonly used)
  {
    codigo: 1,
    nome: "Pregao Eletronico",
    descricao: "Licitacao eletronica para bens e servicos comuns (Lei 14.133/21, Art. 6º XLIII)",
    popular: true,
  },
  {
    codigo: 2,
    nome: "Pregao Presencial",
    descricao: "Licitacao presencial para bens e servicos comuns, quando motivado (Lei 14.133/21, Art. 6º XLIII)",
    popular: true,
  },
  {
    codigo: 6,
    nome: "Dispensa de Licitacao",
    descricao: "Contratacao direta sem licitacao (Lei 14.133/21, Art. 75)",
    popular: true,
  },

  // OTHER MODALITIES (Collapsible section)
  {
    codigo: 3,
    nome: "Concorrencia",
    descricao: "Para bens/servicos especiais e obras de engenharia (Lei 14.133/21, Art. 6º XLII)",
  },
  {
    codigo: 7,
    nome: "Inexigibilidade",
    descricao: "Quando ha inviabilidade de competicao (Lei 14.133/21, Art. 74)",
  },
  {
    codigo: 9,
    nome: "Leilao",
    descricao: "Para alienacao de bens imoveis ou moveis (Lei 14.133/21, Art. 6º XLV)",
  },
  {
    codigo: 10,
    nome: "Dialogo Competitivo",
    descricao: "Para solucoes inovadoras complexas (Lei 14.133/21, Art. 6º XLVI)",
  },
  {
    codigo: 11,
    nome: "Concurso",
    descricao: "Escolha de trabalho tecnico, cientifico ou artistico (Lei 14.133/21, Art. 6º XLIV)",
  },
];

// REMOVED DEPRECATED MODALITIES (Lei 8.666/93 - Revogada):
// - codigo: 4, nome: "Tomada de Precos" → Use Concorrencia (3) or Pregao (1/2)
// - codigo: 5, nome: "Convite" → Use Pregao (1/2) or Dispensa (6)
// - codigo: 8, nome: "Credenciamento" → Not a modality per Lei 14.133

// Total: 8 official Lei 14.133/2021 modalities
// Popular: 3 (Pregoes + Dispensa - most frequently used)
// Others: 5 (Concorrencia, Inexigibilidade, Leilao, Dialogo, Concurso)
```

### 3. Add Legal Reference Helper

```typescript
/**
 * Get legal reference for a modalidade.
 * Useful for help tooltips or expanded information.
 */
const MODALIDADE_LEGAL_REFS = {
  1: {
    artigo: "Art. 6º, XLIII",
    lei: "Lei 14.133/2021",
    url: "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art6xliii",
  },
  2: {
    artigo: "Art. 6º, XLIII",
    lei: "Lei 14.133/2021",
    url: "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art6xliii",
  },
  3: {
    artigo: "Art. 6º, XLII",
    lei: "Lei 14.133/2021",
    url: "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art6xlii",
  },
  6: {
    artigo: "Art. 75",
    lei: "Lei 14.133/2021",
    decreto: "Decreto 12.807/2025 (valores atualizados)",
    url: "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art75",
  },
  7: {
    artigo: "Art. 74",
    lei: "Lei 14.133/2021",
    url: "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art74",
  },
  9: {
    artigo: "Art. 6º, XLV",
    lei: "Lei 14.133/2021",
    url: "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art6xlv",
  },
  10: {
    artigo: "Art. 6º, XLVI",
    lei: "Lei 14.133/2021",
    url: "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art6xlvi",
  },
  11: {
    artigo: "Art. 6º, XLIV",
    lei: "Lei 14.133/2021",
    url: "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art6xliv",
  },
};
```

### 4. Update Component Header Comment

```typescript
/**
 * ModalidadeFilter Component
 *
 * Multi-select filter for procurement modality types per Lei 14.133/2021.
 * Based on legal requirements from Lei 14.133/2021 and Decreto 12.807/2025.
 *
 * Features:
 * - Multi-select with checkboxes
 * - 3 popular modalities always visible: Pregao Eletronico, Pregao Presencial, Dispensa
 * - Collapsible section for other modalities (Concorrencia, Inexigibilidade, Leilao, etc.)
 * - "Todas" and "Limpar" buttons
 * - Counter showing selected count
 * - Full keyboard accessibility (WCAG 2.1 AA)
 * - ARIA compliant
 *
 * Legal Compliance:
 * - ✅ All 8 Lei 14.133/2021 modalities
 * - ✅ Removed Lei 8.666/93 deprecated modalities (Tomada de Precos, Convite)
 * - ✅ Article references in descriptions
 * - ✅ Updated per Decreto 12.807/2025
 */
```

### 5. Update Tests

**File:** `frontend/components/ModalidadeFilter.test.tsx` (create if not exists)

```typescript
import { render, screen, fireEvent } from "@testing-library/react";
import { ModalidadeFilter, MODALIDADES } from "./ModalidadeFilter";

describe("ModalidadeFilter - Lei 14.133 Compliance", () => {
  test("renders all 8 Lei 14.133 modalities", () => {
    const onChange = jest.fn();
    render(<ModalidadeFilter value={[]} onChange={onChange} />);

    // Should have exactly 8 modalities
    expect(MODALIDADES).toHaveLength(8);
  });

  test("contains only valid Lei 14.133 codes", () => {
    const validCodes = [1, 2, 3, 6, 7, 9, 10, 11];
    const codes = MODALIDADES.map((m) => m.codigo);

    expect(codes.sort()).toEqual(validCodes.sort());
  });

  test("does NOT contain deprecated codes", () => {
    const deprecatedCodes = [4, 5]; // Tomada de Precos, Convite
    const codes = MODALIDADES.map((m) => m.codigo);

    deprecatedCodes.forEach((deprecated) => {
      expect(codes).not.toContain(deprecated);
    });
  });

  test("has exactly 3 popular modalities", () => {
    const popular = MODALIDADES.filter((m) => m.popular);
    expect(popular).toHaveLength(3);

    // Should be Pregoes + Dispensa
    const popularCodes = popular.map((m) => m.codigo);
    expect(popularCodes).toContain(1); // Pregao Eletronico
    expect(popularCodes).toContain(2); // Pregao Presencial
    expect(popularCodes).toContain(6); // Dispensa
  });

  test("all modalities have Lei article references", () => {
    MODALIDADES.forEach((modalidade) => {
      expect(modalidade.descricao).toMatch(/Lei 14\.133/);
      expect(modalidade.descricao).toMatch(/Art\. /);
    });
  });

  test("includes Concurso (new modality)", () => {
    const concurso = MODALIDADES.find((m) => m.codigo === 11);
    expect(concurso).toBeDefined();
    expect(concurso?.nome).toBe("Concurso");
    expect(concurso?.descricao).toMatch(/Art\. 6º XLIV/);
  });

  test("Todas button selects all 8 modalities", () => {
    const onChange = jest.fn();
    render(<ModalidadeFilter value={[]} onChange={onChange} />);

    const todasButton = screen.getByText("Todas");
    fireEvent.click(todasButton);

    expect(onChange).toHaveBeenCalledWith([1, 2, 3, 6, 7, 9, 10, 11]);
  });

  test("Limpar button deselects all", () => {
    const onChange = jest.fn();
    render(<ModalidadeFilter value={[1, 2, 6]} onChange={onChange} />);

    const limparButton = screen.getByText("Limpar");
    fireEvent.click(limparButton);

    expect(onChange).toHaveBeenCalledWith([]);
  });

  test("accessibility: has proper ARIA labels", () => {
    const onChange = jest.fn();
    render(<ModalidadeFilter value={[]} onChange={onChange} />);

    const popularGroup = screen.getByLabelText("Modalidades populares");
    expect(popularGroup).toBeInTheDocument();
  });

  test("keyboard navigation works", () => {
    const onChange = jest.fn();
    render(<ModalidadeFilter value={[]} onChange={onChange} />);

    const firstCheckbox = screen.getAllByRole("checkbox")[0];
    firstCheckbox.focus();
    expect(document.activeElement).toBe(firstCheckbox);

    // Press Enter to toggle
    fireEvent.keyDown(firstCheckbox, { key: "Enter" });
    expect(onChange).toHaveBeenCalled();
  });
});
```

### 6. Visual Verification

Run the app and verify:

```bash
# Start frontend dev server
cd frontend
npm run dev

# Navigate to search page with modalidade filter
# Verify:
# - 3 popular modalities visible by default
# - "Mais opcoes" expands to show 5 more
# - All 8 modalities render correctly
# - Descriptions show Lei references
# - No codes 4, 5, 8 present
```

### 7. Accessibility Check

```bash
# Run accessibility tests
npm run test:a11y

# Manual checks:
# - Tab through all checkboxes
# - Use Enter/Space to toggle
# - Screen reader announces correctly
# - Focus indicators visible
# - Contrast ratios pass WCAG AA
```

## Validation Checklist

- [ ] Exactly 8 modalities in MODALIDADES constant
- [ ] Codes are: 1, 2, 3, 6, 7, 9, 10, 11
- [ ] No codes 4, 5, or 8
- [ ] All descriptions reference Lei 14.133/2021 articles
- [ ] Popular flags set for codes 1, 2, 6
- [ ] Concurso (code 11) included
- [ ] Component tests pass
- [ ] Visual rendering correct
- [ ] Accessibility maintained (WCAG 2.1 AA)
- [ ] No TypeScript errors
- [ ] No console warnings

## Files Modified

- `frontend/components/ModalidadeFilter.tsx` - Updated MODALIDADES constant
- `frontend/components/ModalidadeFilter.test.tsx` - Added Lei 14.133 tests

## Success Criteria

✅ All 8 Lei 14.133 modalities present
✅ Deprecated modalities removed (4, 5)
✅ Lei article references in all descriptions
✅ Popular categorization optimized
✅ Component tests pass (100% coverage)
✅ Accessibility maintained
✅ Visual rendering correct
✅ TypeScript compilation succeeds

## Legal References in UI

Each modalidade description now includes:
- Lei number (Lei 14.133/2021)
- Article reference (Art. 6º XLII-XLVI, Art. 74, Art. 75)
- Brief description of when it's used

This helps users:
- Understand which modality applies to their search
- Comply with legal requirements
- Find relevant legal documentation

---

**Priority:** P0 (Critical - User-facing component)
**Phase:** 4 (Frontend)
**Agent:** @frontend-engineer
**Parallel Execution:** Can run in parallel with backend adapter implementations
**Estimated Duration:** 2-3 hours
