# UX-432: Resultados de busca perdidos ao navegar entre paginas

**Status:** Draft
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I1)
**Sprint:** Proximo

## Contexto

Ao sair de /buscar (ex: clicar em Dashboard, Pipeline) e voltar, todos os resultados sao perdidos. O usuario precisa refazer a busca (~60s). Isso impede fluxos naturais como "ver resultado → abrir pipeline → voltar para resultado".

## Acceptance Criteria

- [ ] AC1: Resultados da busca atual devem persistir em sessionStorage ou zustand
- [ ] AC2: Ao voltar para /buscar, restaurar resultados se existirem (< 30min)
- [ ] AC3: Mostrar indicador visual "Resultados da busca anterior" com opcao de "Nova busca"
- [ ] AC4: Alternativa minima: confirmar com usuario antes de sair ("Voce tem resultados ativos")

## Arquivos Provaveis

- `frontend/app/buscar/page.tsx` — state management dos resultados
- `frontend/hooks/useSearch.ts` — search state
