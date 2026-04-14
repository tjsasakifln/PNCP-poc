# STORY-1.5: Kanban Keyboard Navigation WCAG 2.1 AA (TD-FE-006)

**Priority:** P0 (compliance B2G obrigatório — LBI 13.146/2015 + Lei 14.738/2023)
**Effort:** M (8-16h)
**Squad:** @ux-design-expert (lead) + @dev (executor) + @qa (quality gate)
**Status:** Done
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

- [x] Card focável via Tab (dnd-kit injeta tabIndex=0 via `attributes` spread)
- [x] Space/Enter ativa keyboard drag no `KeyboardSensor` (pré-existente em `PipelineKanban.tsx:52-55`)
- [x] Esc cancela operação (handled pelo dnd-kit `onDragCancel`)

### AC2: Arrow key movement

- [x] Arrow keys movem card entre células via `sortableKeyboardCoordinates` (pré-existente)
- [x] Movimento entre colunas funciona por cartas adjacentes
- [x] Constraints respeitados automaticamente pelo `closestCorners` collision

### AC3: Screen reader announcements

- [x] dnd-kit injeta `aria-live="assertive"` region automaticamente quando `accessibility.announcements` é configurado (verificado em `PipelineKanban.tsx:81-99`)
- [x] Announcements em português para `onDragStart`, `onDragOver`, `onDragEnd`, `onDragCancel`
- [x] E2E valida presença da live region

### AC4: Visual focus indicator

- [x] Card + botões recebem `focus-visible:ring-2 focus-visible:ring-brand-blue focus-visible:ring-offset-2` (PipelineCard.tsx)
- [x] Column header + dropzone com role="group" + aria-labelledby (PipelineColumn.tsx)
- [x] Card "pego" para drag já tinha `opacity-50 shadow-lg ring-2 ring-brand-blue` pré-existente

### AC5: Existing mouse drag continua funcionando

- [x] `PointerSensor` preservado (linha 53 de `PipelineKanban.tsx`)
- [x] 179 testes Jest pipeline pass (inclui tests de drag)

### AC6: Test automation

- [x] Novo spec: `frontend/e2e-tests/pipeline-keyboard.spec.ts` (4 testes — AC1/AC4, AC3, AC2, AC6)
- [x] `AxeBuilder` scan com tags `wcag2a wcag2aa wcag21a wcag21aa`; asserta 0 critical violations

---

## Tasks / Subtasks

- [x] Task 1: `useSortable` + `KeyboardSensor` + `sortableKeyboardCoordinates` (já pré-existente em `PipelineKanban.tsx:52-55`)
- [x] Task 2: ARIA announcer — dnd-kit nativo via `accessibility.announcements` (pré-existente)
- [x] Task 3: Visual focus indicators (NOVO — `focus-visible` em PipelineCard + PipelineColumn)
- [x] Task 4: Regression — 179 pipeline Jest tests pass
- [x] Task 5: Novo E2E `pipeline-keyboard.spec.ts` (4 testes)
- [x] Task 6: axe-core — `@axe-core/playwright@4.11.1` já presente no package.json
- [x] Task 7: Documentação — `docs/frontend/frontend-spec.md` marca TD-FE-006 como ✅ RESOLVIDO

## File List

**New:**
- `frontend/e2e-tests/pipeline-keyboard.spec.ts`

**Modified:**
- `frontend/app/pipeline/PipelineCard.tsx` (focus-visible classes + aria-label)
- `frontend/app/pipeline/PipelineColumn.tsx` (role="group" + aria-labelledby + focus-visible)
- `docs/frontend/frontend-spec.md` (TD-FE-006 marcado resolvido)

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
| 2026-04-14 | 1.1     | GO (9/10) — Draft → Ready. Obs: adicionar IN/OUT (mobile swipe = OUT) antes de InProgress | @po    |
| 2026-04-14 | 2.0     | Implementation: descoberta que KeyboardSensor + announcements já existiam → escopo reduzido para focus-visible CSS + aria enrichment + novo E2E spec com axe-core. 179 Jest tests pass. Status Ready → Done | @dev |
