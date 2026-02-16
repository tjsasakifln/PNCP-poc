# STORY-TD-005: Dialog Primitive e Acessibilidade

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 1: Seguranca e Correcoes

## Prioridade
P1

## Estimativa
4h

## Descricao

Esta story cria uma infraestrutura de dialogo acessivel reutilizavel e corrige as violacoes WCAG em modais existentes.

**Problema:** Os dialogs modais da pagina `/buscar` (save search dialog linhas 238-274, keyboard help linhas 277-350) sao `<div>` com `fixed inset-0 z-50` sem focus trap, sem `role="dialog"`, e sem `aria-modal="true"`. Usuarios de teclado podem Tab para tras do modal, violando WCAG 2.4.3 (Focus Order) e 4.1.2 (Name/Role/Value). O `UpgradeModal.tsx` ja implementa o pattern corretamente e serve como referencia.

**Solucao:** Extrair um componente `<Dialog>` reutilizavel baseado no pattern do `UpgradeModal.tsx` (que ja tem aria-modal, role, Escape capture-phase). Adicionar focus trap (~30 linhas). Refatorar os 3 modais para usar o novo componente.

**Bonus automatico:** A correcao do focus trap resolve automaticamente UX-02 (Escape conflict no keyboard shortcuts modal), pois o evento Escape sera capturado pelo modal antes de disparar `limparSelecao()`.

## Itens de Debito Relacionados
- A11Y-01 (HIGH): Modal dialogs sem focus trap -- WCAG 2.4.3 Focus Order violation
- A11Y-02 (HIGH): Modals nao usam `role="dialog"` ou `aria-modal="true"` -- WCAG 4.1.2
- UX-02 (MEDIUM): Keyboard shortcuts modal sem focus trap; conflito de Escape

## Criterios de Aceite

### Dialog Component
- [x] Componente `<Dialog>` criado (ex: `frontend/app/components/Dialog.tsx`)
- [x] Props: `isOpen`, `onClose`, `title`, `children`, `className` (minimo)
- [x] Inclui `role="dialog"` no elemento raiz
- [x] Inclui `aria-modal="true"`
- [x] Inclui `aria-labelledby` apontando para titulo
- [x] Focus trap implementado: Tab/Shift+Tab cicla DENTRO do modal
- [x] Escape fecha o modal (capture-phase event listener, como UpgradeModal linha 45)
- [x] Focus retorna ao elemento que abriu o modal ao fechar
- [x] Background overlay bloqueia interacao (click outside fecha ou nao, configuravel)

### Refatoracao de Modais
- [x] Save search dialog (`/buscar` linhas ~238-274) usa `<Dialog>`
- [x] Keyboard help modal (`/buscar` linhas ~277-350) usa `<Dialog>`
- [x] `UpgradeModal.tsx` opcionalmente migrado para usar `<Dialog>` (ou mantido como referencia)
- [x] Funcionalidade existente preservada em todos os modais

### Acessibilidade
- [x] Tab nao escapa do modal em nenhuma direcao
- [x] Shift+Tab nao escapa do modal
- [x] Screen reader anuncia "dialog" ao abrir
- [x] Escape fecha APENAS o modal (nao dispara `limparSelecao()`)

## Testes Requeridos

| ID | Teste | Tipo | Prioridade | Status |
|----|-------|------|-----------|--------|
| REG-T10 | Modais mantem focus trap (Tab nao escapa) | E2E accessibility | P1 | Done |
| REG-T11 | Escape fecha modal, UF selection permanece | E2E interaction | P1 | Done |

## Dependencias
- **Blocks:** STORY-TD-019 (backlog item UX-NEW-03 -- admin confirm dialog -- usara o `<Dialog>` criado aqui)
- **Blocked by:** Nenhuma

## Riscos
- Risco baixo. Pattern ja existe em `UpgradeModal.tsx`, trata-se de extrai-lo e reutilizar.
- Atencao: focus trap pode conflitar com inputs dentro do modal (ex: campo de nome da busca salva). Testar interacao.

## Rollback Plan
- Se focus trap causar problemas, desabilitar trap mantendo role/aria-modal (melhoria parcial).
- Reverter para `<div>` original como ultimo recurso.

## Definition of Done
- [x] Codigo implementado e revisado
- [x] Testes passando (unitario + E2E acessibilidade)
- [x] CI/CD green
- [x] Documentacao do componente `<Dialog>` (props, uso)
- [ ] Deploy em staging verificado
- [ ] Verificacao manual com Tab/Shift+Tab/Escape em todos os modais

## Arquivos Modificados
- `frontend/app/components/Dialog.tsx` — NEW: Reusable accessible dialog component
- `frontend/app/components/UpgradeModal.tsx` — Migrated to use `<Dialog>`
- `frontend/app/buscar/page.tsx` — Save search + keyboard help modals refactored
- `frontend/__tests__/Dialog.test.tsx` — NEW: 19 unit tests for Dialog component
- `frontend/__tests__/UpgradeModal.test.tsx` — Updated for new Dialog-based structure
- `frontend/e2e-tests/dialog-accessibility.spec.ts` — NEW: REG-T10 + REG-T11 E2E tests
