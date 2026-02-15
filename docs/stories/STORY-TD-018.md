# STORY-TD-018: Consolidacao Plan Data + Search Button Sticky

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 2: Consolidacao e Refatoracao

## Prioridade
P2

## Estimativa
8h

## Descricao

Esta story resolve dois problemas de UX de media prioridade que afetam a experiencia do usuario.

1. **Search button sticky em desktop (UX-01, MEDIUM, 4h)** -- O botao de busca fica abaixo do fold em desktop quando o accordion de filtros esta aberto. Sticky mobile (`sticky bottom-4 sm:bottom-auto`) existe mas e desabilitado em desktop. O CTA primario da pagina de busca nao deveria ser invisivel. Implementar sticky behavior em desktop tambem, com estilo adequado.

2. **Setores hardcoded em dois lugares (FE-06, MEDIUM, 4h)** -- A lista de setores esta hardcoded em `useSearchFilters.ts` (SETORES_FALLBACK) e `signup/page.tsx` (SECTORS), podendo divergir. Setores de signup podem nao corresponder aos disponíveis na busca. Consolidar para uma unica source of truth:
   - Opção 1: importar de `lib/sectors.ts` compartilhado
   - Opção 2: usar script `scripts/sync-setores-fallback.js` (ja existe, STORY-170 AC15) para manter sincronia

## Itens de Debito Relacionados
- UX-01 (MEDIUM): Search button abaixo do fold em desktop com accordion aberto
- FE-06 (MEDIUM): Lista de setores hardcoded em dois lugares

## Criterios de Aceite

### Search Button Sticky
- [ ] Botao de busca visivel em todas as resolucoes desktop (1024px+)
- [ ] Botao sticky nao obstrui conteudo importante
- [ ] Botao sticky tem sombra ou borda para indicar elevacao
- [ ] Botao volta ao fluxo normal quando em viewport (nao sticky se ja visivel)
- [ ] Comportamento sticky mobile preservado
- [ ] Comportamento funciona com accordion aberto e fechado

### Setores Consolidados
- [ ] `SETORES_FALLBACK` em `useSearchFilters.ts` importa de source unica
- [ ] `SECTORS` em `signup/page.tsx` importa da mesma source
- [ ] Source unica: `lib/sectors.ts` ou equivalente
- [ ] `grep -r "SETORES_FALLBACK" frontend/` mostra definicao em 1 lugar apenas
- [ ] Script `sync-setores-fallback.js` atualizado para nova localizacao (se mudou)
- [ ] Setores identicos entre signup e busca

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| -- | Search button visivel em desktop (1440px) com accordion aberto | E2E visual | P2 |
| -- | Search button visivel em mobile (375px) | E2E visual | P2 |
| -- | Setores de signup == setores de busca | Unitario | P2 |

## Dependencias
- **Blocks:** Nenhuma
- **Blocked by:** Nenhuma (independente)

## Riscos
- Sticky button pode causar layout shift ou obstruir conteudo em resoluções intermediarias. Testar em 768px, 1024px, 1440px, 1920px.
- Consolidacao de setores requer verificar se ambas as listas sao semanticamente identicas (IDs, nomes, descricoes).

## Rollback Plan
- Sticky: reverter CSS se causar problemas de layout.
- Setores: reverter para hardcoded se consolidacao causar divergencia.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + E2E)
- [ ] CI/CD green
- [ ] Verificacao visual em 4+ resolucoes
- [ ] Deploy em staging verificado
