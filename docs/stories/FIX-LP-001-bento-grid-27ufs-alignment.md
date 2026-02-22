# FIX-LP-001 — Corrigir alinhamento do card "27 UFs" na landing page

## Status: Ready

## Contexto

Na seção ValuePropSection da landing page, o card "27 UFs" (cobertura nacional) aparece deslocado visualmente em relação aos demais cards. O problema ocorre porque o BentoGrid usa 4 colunas no desktop e o card "27 UFs" ocupa apenas 3 colunas (`lg:col-span-3`), deixando 1 coluna vazia à direita. Isso gera uma assimetria visual que causa estranheza.

## Screenshot do problema

![Card 27 UFs deslocado](../../screenshots/fix-lp-001-before.png)

Layout atual no desktop (4 colunas):
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│              │              │              │              │
│  Foco (2x2)                │  Objetiva (2x1)             │
│              │              │              │              │
│              │              ├──────────────┴──────────────┤
│              │              │              │              │
│              │              │  Transparente (2x1)         │
├──────────────┴──────────────┼──────────────┤              │
│                             │              │              │
│  27 UFs (3x1)                              │  ← VAZIO    │
│                             │              │              │
└─────────────────────────────┴──────────────┘              │
```

O card "27 UFs" ocupa 3 de 4 colunas, criando 1 coluna vazia e desalinhamento visual.

## Arquivos envolvidos

| Arquivo | Propósito |
|---------|-----------|
| `frontend/app/components/ValuePropSection.tsx` | Define sizes dos cards (L23-28) |
| `frontend/app/components/ui/BentoGrid.tsx` | Grid layout e size mappings |
| `frontend/lib/copy/valueProps.ts` | Conteúdo dos cards (referência) |

## Critérios de Aceitação

- [ ] **AC1**: O card "27 UFs" ocupa a largura completa da grid (4 colunas) OU todos os 4 cards ficam visualmente equilibrados sem espaço vazio residual
- [ ] **AC2**: O layout permanece responsivo — mobile (1 col), tablet (2 cols), desktop (4 cols)
- [ ] **AC3**: Nenhum dos outros 3 cards (Foco, Objetiva, Transparente) é afetado negativamente
- [ ] **AC4**: Zero regressão nos testes existentes do frontend

## Opções de correção

### Opção 1 — Card "27 UFs" full-width (4 colunas) ⭐ Recomendada
Mudar `size: 'wide'` para um novo size `'full'` com `lg:col-span-4`, ou simplesmente usar `lg:col-span-4` diretamente.

**Prós:** Simples, elimina o espaço vazio, card de cobertura nacional merece destaque.
**Contras:** Card fica mais largo que os demais.

### Opção 2 — Grid de 3 colunas em vez de 4
Mudar o grid para 3 colunas. Foco=1col+2rows, Objetiva=1col, Transparente=1col, 27UFs=3col full.

**Prós:** Layout mais equilibrado.
**Contras:** Pode afetar o tamanho relativo dos cards Objetiva e Transparente.

### Opção 3 — Layout 2x2 simétrico
Todos os 4 cards com `size: 'medium'` (2x1), formando um grid 2x2 perfeito.

**Prós:** Máxima simetria.
**Contras:** Perde a hierarquia visual (Foco perde destaque como card principal).

## Estimativa

- **Complexidade:** Trivial (1-3 linhas de código)
- **Risco:** Baixo (alteração CSS apenas)
- **Testes:** Verificar visualmente + rodar `npm test` para regressões

## Labels

`fix`, `frontend`, `landing-page`, `UX`, `trivial`
