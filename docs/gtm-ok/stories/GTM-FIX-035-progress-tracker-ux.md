# GTM-FIX-035: UX do Progress Tracker durante busca

**Priority:** P1 (frustração direta durante a ação principal do produto)
**Effort:** M (4-6h)
**Origin:** Teste de produção manual 2026-02-18
**Status:** CONCLUÍDO
**Assignee:** @dev + @ux-design-expert
**Tracks:** Frontend (5 ACs), Tests (1 AC)

---

## Problem Statement

O progress tracker — a UI que o usuário vê durante a ação mais importante do produto (a busca) — tem múltiplos problemas de UX que causam confusão e ansiedade.

### Problemas Identificados

#### 1. Progress bar abaixo da dobra
O formulário de busca (setor, UFs, filtros) permanece totalmente visível durante a busca, empurrando o progress tracker para baixo do viewport. O usuário só vê "Consultando múltiplas fontes..." no botão disabled e precisa rolar para ver o progresso.

#### 2. Dados contraditórios
- Mostra "1 de 1 estado processado" mas porcentagem está em 10%
- Se 100% dos estados estão processados, por que 10%?
- Timer mostra "93s" mas estimativa inicial era "~25s"

#### 3. Formulário interativo durante busca
Filtros (status, modalidade, valor) ficam desabilitados visualmente mas ocupam espaço. Seria melhor recolher a seção "Personalizar busca".

#### 4. Mensagem genérica de espera
"A busca pode demorar em horários de pico" — não diz quanto mais, não contextualiza.

#### 5. Progress bar reseta de 80% para erro
Ao perder SSE, a barra que estava em 80%+ reseta para erro, dando impressão de que todo o trabalho foi perdido (ver GTM-FIX-033).

---

## Acceptance Criteria

### Frontend

- [x] **AC1**: Ao iniciar busca, auto-recolher a seção "Personalizar busca" e rolar para a área de progresso (smooth scroll)
- [x] **AC2**: Progress tracker deve ficar acima da dobra durante toda a busca — se necessário, usar `position: sticky` ou mover para cima dos filtros
- [x] **AC3**: Resolver contradição "X de Y estados processados" vs porcentagem — a porcentagem deve refletir a realidade do backend, não uma simulação independente
- [x] **AC4**: Mensagem de espera contextualizada: "Buscando em X fontes oficiais. Resultados em aproximadamente Y segundos." (usar estimativa do backend se disponível)
- [x] **AC5**: Se timer ultrapassa 2x a estimativa inicial, mostrar: "Esta busca está demorando mais que o normal. Pode ficar nesta página — os resultados serão exibidos automaticamente."

### Tests

- [x] **AC6**: Teste visual: ao clicar "Buscar", seção de filtros recolhe e progress tracker fica visível no viewport

---

## Mockup Conceitual

```
┌──────────────────────────────────────┐
│ Busca de Licitações                  │
│ [Vestuário e Uniformes ▼]           │
│ ▶ Personalizar busca (recolhido)     │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 🔍 Buscando Vestuário e         │ │
│ │    Uniformes em SP               │ │
│ │                                  │ │
│ │ ████████████░░░░░░░░░ 62%       │ │
│ │                                  │ │
│ │ ✅ Fontes → 🔄 Dados → ⏳ Filtro│ │
│ │                                  │ │
│ │ ~45s restantes                   │ │
│ │                    [Cancelar]    │ │
│ └──────────────────────────────────┘ │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ [Skeleton loader resultado]      │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘
```

## Arquivos Relevantes

| Arquivo | Linhas | Responsabilidade |
|---------|--------|------------------|
| `frontend/hooks/useSearchProgress.ts` | Full | Simulação time-based (EventSource → `/api/buscar-progress`) |
| `frontend/app/buscar/hooks/useUfProgress.ts` | Full | SSE real per-UF + batch progress |
| `frontend/components/LoadingProgress.tsx` | Full | Renderiza o progress tracker visual |
| `frontend/app/buscar/page.tsx` | Search handler | Orquestra os hooks, exibe resultados |

## Technical Notes

- **Dois hooks independentes** (`useSearchProgress` + `useUfProgress`) geram dados de progresso sem sincronização entre si — essa é a causa raiz da contradição
- `useUfProgress` retorna `allComplete=true` quando todas UFs foram processadas, mas `useSearchProgress` ainda pode estar em 10% na sua simulação
- `LoadingProgress.tsx` recebe props de ambos os hooks e tenta reconciliar, mas sem regra clara de precedência
- O recolhimento do formulário (AC1) deve ser feito no handler de busca em `page.tsx`, setando state do accordion para `collapsed`
- Smooth scroll: `element.scrollIntoView({ behavior: 'smooth' })`
