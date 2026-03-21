# DEBT-BL.2: Accessibility + UX Polish
**Epic:** EPIC-DEBT
**Sprint:** Backlog
**Priority:** P3
**Estimated Hours:** 14.5h
**Assignee:** TBD

## Objetivo

Resolver debitos de acessibilidade e polish de UX que melhoram a experiencia do usuario mas nao sao bloqueantes. Inclui melhorias no CI de acessibilidade, correcoes de labels, e ajustes visuais no onboarding tour.

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| FE-24 | a11y no CI. `@axe-core/playwright` integrado mas gate cobre apenas critical. Expandir para serious violations. | LOW | 4h |
| FE-31 | Dashboard icon errado no BottomNav. Usa `icons.search` ao inves de `icons.dashboard`. | LOW | 0.5h |
| FE-35 | BottomNav label "Dash" confuso. Considerar "Painel" (PT-BR nativo). | LOW | 0.5h |
| FE-36 | Shepherd.js tour arrow hidden remove affordance visual. Sem arrow, usuario nao associa tooltip ao elemento. | LOW | 1h |

## Acceptance Criteria

- [ ] AC1: axe-core CI gate expandido para bloquear `serious` violations alem de `critical`
- [ ] AC2: Lista de violations `serious` existentes documentada como baseline (se houver)
- [ ] AC3: BottomNav Dashboard usa `icons.dashboard` (nao `icons.search`)
- [ ] AC4: BottomNav label "Dash" renomeado para "Painel"
- [ ] AC5: `ariaLabel` "Dashboard" mantido (ingleses tecnico aceito em aria)
- [ ] AC6: Shepherd.js tour exibe arrow apontando para o elemento target
- [ ] AC7: Arrow usa styling consistente com design tokens

## Tasks

### a11y CI Expansion (4h)
- [ ] T1: Auditar violations `serious` atuais com `npx playwright test accessibility-audit.spec.ts`
- [ ] T2: Documentar baseline de violations serious existentes
- [ ] T3: Corrigir violations serious corrigiveis rapidamente
- [ ] T4: Atualizar gate em `accessibility-audit.spec.ts` para incluir `serious`
- [ ] T5: Adicionar violations nao-corrigiveis ao allowlist com justificativa

### BottomNav Fixes (1h)
- [ ] T6: Trocar `icons.search` por `icons.dashboard` no BottomNav item Dashboard
- [ ] T7: Renomear label "Dash" para "Painel"
- [ ] T8: Manter `ariaLabel: "Dashboard"` inalterado

### Shepherd Arrow (1h)
- [ ] T9: Remover CSS que oculta arrow do Shepherd.js tour
- [ ] T10: Estilizar arrow com design tokens (nao Tailwind raw)
- [ ] T11: Testar visualmente em desktop e mobile

## Testes Requeridos

- [ ] axe-core audit passa com gate expandido (0 critical + 0 serious, exceto allowlist)
- [ ] BottomNav renderiza icone correto para Dashboard
- [ ] BottomNav mostra "Painel" como label
- [ ] Shepherd tour mostra arrow conectando tooltip ao elemento
- [ ] Frontend test count >= 5583
- [ ] E2E: onboarding tour funciona end-to-end

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **FE-24:** axe-core ja esta integrado (DEBT-109). O trabalho e expandir o gate, nao implementar do zero.
- **FE-31 e FE-35 sao quick fixes** de 5-10 minutos cada. Podem ser feitos junto em 1 PR.
- **FE-36:** Shepherd arrow foi intencionalmente ocultado -- verificar se havia motivo (overlap visual?) antes de restaurar.
- Estes items nao tem dependencias externas e podem ser feitos a qualquer momento.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secao "Frontend"
- a11y audit: `frontend/e2e-tests/accessibility-audit.spec.ts`
- BottomNav: `frontend/components/BottomNav.tsx`
- Shepherd config: `frontend/app/buscar/components/` (tour configuration)
