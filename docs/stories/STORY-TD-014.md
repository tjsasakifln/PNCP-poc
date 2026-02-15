# STORY-TD-014: Dynamic Imports + Consolidacao de Planos + Icones

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 3: Qualidade e Cobertura

## Prioridade
P2

## Estimativa
16h

## Descricao

Esta story otimiza o bundle size do frontend, consolida definicoes de planos divergentes, e inicia a migracao de icones para lucide-react.

1. **Dynamic imports para dependencias pesadas (FE-07, MEDIUM, 6h)** -- Zero uso de `next/dynamic` ou `React.lazy` apesar de dependencias pesadas:
   - recharts (~200KB) -- Dashboard
   - @dnd-kit (3 pacotes) -- Pipeline
   - framer-motion (~40KB) -- Landing
   - shepherd.js -- Search onboarding

   Prioridade de migracao: recharts > @dnd-kit > shepherd.js > framer-motion. Cada componente pesado deve ser carregado com `next/dynamic` e skeleton/loading state apropriado.

2. **Consolidacao PLAN_HIERARCHY/PLAN_FEATURES (FE-17, MEDIUM, 4h)** -- `planos/page.tsx` linhas 34-46, 55+ definem `PLAN_HIERARCHY` e `PLAN_FEATURES` como duplicata de `lib/plans.ts`. Mudancas de plano requerem editar dois arquivos, arriscando drift de precos/features. Consolidar para source unica em `lib/plans.ts`.

3. **Migracao de icones para lucide-react (FE-05, MEDIUM, 6h)** -- 162 ocorrencias de SVG inline em 30+ arquivos, mas lucide-react esta instalado e usado em apenas 5 arquivos. Migrar SVGs inline para lucide-react onde equivalentes existem. Manter SVGs customizados que nao tem equivalente.

## Itens de Debito Relacionados
- FE-07 (MEDIUM): Sem dynamic imports para dependencias pesadas
- FE-17 (MEDIUM): PLAN_HIERARCHY e PLAN_FEATURES hardcoded em planos/page.tsx
- FE-05 (MEDIUM): Inline SVGs duplicados em 30+ arquivos (162 ocorrencias SVG/viewBox)

## Criterios de Aceite

### Dynamic Imports
- [ ] recharts carregado via `next/dynamic` com `ssr: false` e loading skeleton
- [ ] @dnd-kit carregado via `next/dynamic` na pagina de pipeline
- [ ] shepherd.js carregado via `next/dynamic` no onboarding
- [ ] framer-motion carregado via dynamic import onde possivel
- [ ] Nenhum loading spinner generico -- cada dynamic import tem skeleton especifico
- [ ] Initial JS bundle < 200KB (medir com `next build` analyzer)

### Consolidacao de Planos
- [ ] `PLAN_HIERARCHY` removido de `planos/page.tsx` -- importado de `lib/plans.ts`
- [ ] `PLAN_FEATURES` removido de `planos/page.tsx` -- importado de `lib/plans.ts`
- [ ] Precos identicos entre todas as paginas que exibem precos
- [ ] `grep -r "PLAN_HIERARCHY" frontend/` mostra definicao APENAS em `lib/plans.ts`
- [ ] `grep -r "PLAN_FEATURES" frontend/` mostra definicao APENAS em `lib/plans.ts`

### Icones
- [ ] Pelo menos 50% das ocorrencias SVG inline migradas para lucide-react
- [ ] Sizing consistente (lucide default + Tailwind classes)
- [ ] Icones que nao tem equivalente em lucide permanecem como SVG inline (documentados)
- [ ] Nenhum icone com `aria-label="Icone"` generico (corrigir: `aria-hidden="true"` se decorativo, ou label descritiva)

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| REG-T13 | Dynamic imports carregam com skeleton/loading | E2E | P2 |
| PERF-T02 | Bundle size apos dynamic imports: Initial JS < 200KB | Build metric | P2 |
| PERF-T03 | LCP pagina de busca (first visit, cold cache) < 2.5s | Lighthouse | P2 |
| -- | Pagina de planos mostra precos corretos (consolidados) | E2E | P2 |

## Dependencias
- **Blocks:** Nenhuma
- **Blocked by:** Nenhuma (independente)

## Riscos
- **CR-07:** Dynamic imports podem causar loading spinners excessivos. Usar skeletons adequados e testar em 3G throttled.
- Migracao de icones pode causar diferencas sutis de sizing. Revisar visualmente.
- Consolidacao de planos requer verificacao de que `lib/plans.ts` e a source of truth real.

## Rollback Plan
- Dynamic imports: reverter individualmente se componente especifico tiver problema.
- Consolidacao de planos: reverter se precos mostrarem incorretamente.
- Icones: reverter por arquivo se necessario.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + E2E)
- [ ] CI/CD green
- [ ] Bundle size medido e documentado (antes/depois)
- [ ] Lighthouse LCP medido
- [ ] Deploy em staging verificado
- [ ] Verificacao visual de icones em 3+ paginas
