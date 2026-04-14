# STORY-1.5: Kanban Keyboard Navigation WCAG 2.1 AA (TD-FE-006)

**Priority:** P0 (compliance B2G obrigatório — LBI 13.146/2015 + Lei 14.738/2023)
**Effort:** M (8-16h)
**Squad:** @ux-design-expert (lead) + @dev (executor) + @qa (quality gate)
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 0

---

## Story

**As a** usuário com deficiência motora ou que usa apenas teclado,
**I want** poder mover cards entre colunas do Kanban via teclado (arrow keys + Enter/Space),
**so that** SmartLic seja WCAG 2.1 AA compliant e elegível para vendas B2G enterprise (compliance brasileiro obrigatório).

---

## Contexto

Phase 3 (frontend-spec) e Phase 6 (UX review) confirmaram: o `/pipeline` usa `@dnd-kit/core` + `@dnd-kit/sortable` para drag-and-drop, mas **sem keyboard navigation configurada**. `useSortable` permite `coordinateGetter` customizado para arrow keys, mas atualmente usa default mouse-only.

Lei 14.738/2023 (acessibilidade digital) torna WCAG 2.1 AA **obrigatório para serviços B2G**. Bloqueia vendas enterprise hoje. ROI: 1-2 dias trabalho destrava deals R$ 50K+.

---

## Acceptance Criteria

### AC1: Keyboard activation

- [ ] Card no Kanban é focusável via Tab
- [ ] Pressionar Enter ou Space "pega" o card (visual feedback)
- [ ] Esc cancela operação

### AC2: Arrow key movement

- [ ] Arrow Up/Down move card dentro da mesma coluna (reordena)
- [ ] Arrow Left/Right move card para coluna adjacente
- [ ] Movimentos respeitam constraints (não permite mover além de boundaries)

### AC3: Screen reader announcements

- [ ] `aria-live="assertive"` region anuncia "Card X movido para coluna Y, posição Z"
- [ ] Estado inicial e final de cada movimento anunciado

### AC4: Visual focus indicator

- [ ] Card focado tem outline visível (`focus-visible:ring-2 focus-visible:ring-blue-500`)
- [ ] Card "pego" para movimento tem indicador distinto (ex: dashed border + aria-grabbed)

### AC5: Existing mouse drag continua funcionando

- [ ] Regression test: mouse drag-drop não quebra
- [ ] Touch drag (mobile) continua funcionando

### AC6: Test automation

- [ ] Playwright E2E: keyboard-only flow (focus card → move → assert position)
- [ ] axe-core scan: 0 violations no `/pipeline`

---

## Tasks / Subtasks

- [ ] Task 1: Configurar `useSortable` com `coordinateGetter` (AC1, AC2)
  - [ ] `frontend/app/pipeline/components/PipelineKanban.tsx` (ou similar)
  - [ ] Implementar `keyboardCoordinateGetter` da `@dnd-kit/core/utilities`
- [ ] Task 2: Adicionar ARIA + announcer (AC3)
  - [ ] `<div role="status" aria-live="assertive" />`
  - [ ] Update via `useAnnouncer` hook custom
- [ ] Task 3: Visual focus indicators (AC4)
  - [ ] Tailwind classes em `<KanbanCard>`
  - [ ] State variant "is-keyboard-grabbed"
- [ ] Task 4: Regression tests (AC5)
  - [ ] Update existing Playwright drag-drop test
- [ ] Task 5: Novos E2E (AC6)
  - [ ] `frontend/e2e-tests/pipeline-keyboard.spec.ts`
- [ ] Task 6: axe-core integration
  - [ ] `@axe-core/playwright` install
  - [ ] Assertion no E2E
- [ ] Task 7: Documentation
  - [ ] Atualizar `docs/frontend/frontend-spec.md` removendo TD-FE-006
  - [ ] Help center ou tooltip in-app explicando keyboard shortcuts

---

## Dev Notes

### Relevant Source Files

- `frontend/app/pipeline/page.tsx` — main route
- `frontend/app/pipeline/components/PipelineKanban.tsx` — DndContext setup
- `frontend/app/pipeline/components/KanbanCard.tsx` — sortable item
- `frontend/app/pipeline/components/KanbanColumn.tsx` — droppable column

### Key API References

- `@dnd-kit/core` — `KeyboardSensor` + `sortableKeyboardCoordinates`
- Pattern: https://docs.dndkit.com/api-documentation/sensors/keyboard
- Example: https://github.com/clauderic/dnd-kit/blob/master/stories/2%20-%20Presets/Sortable/MultipleContainers.tsx

### Snippet (esperado)

```tsx
import { KeyboardSensor, useSensor, useSensors } from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';

const sensors = useSensors(
  useSensor(PointerSensor),
  useSensor(KeyboardSensor, {
    coordinateGetter: sortableKeyboardCoordinates,
  })
);
```

### Constraints

- Não quebrar mobile touch drag
- Performance: announcer não pode flood (debounce)

---

## Testing

- **Unit (RTL)**: `KanbanCard` keyboard event handlers
- **E2E (Playwright)**: full keyboard flow + axe-core scan
- **Manual**: tester com NVDA (Windows) + VoiceOver (Mac) — agendar 1h sessão tester

---

## Definition of Done

- [ ] Keyboard nav funcional (AC1-2)
- [ ] Screen reader announcements OK (AC3)
- [ ] Visual focus claro (AC4)
- [ ] Regression tests passam (AC5)
- [ ] axe-core 0 violations (AC6)
- [ ] Manual screen reader test approved
- [ ] PR aprovado por @qa

---

## Risks

- **R1**: `@dnd-kit` keyboard sensor pode conflitar com keyboard shortcuts globais — mitigation: scope ao kanban container
- **R2**: Tester acessibilidade não disponível — fallback: usar Lighthouse + axe + manual VoiceOver

---

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
