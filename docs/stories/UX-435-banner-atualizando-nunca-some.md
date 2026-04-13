# UX-435: Banner "Atualizando dados em tempo real" nunca desaparece

**Status:** Ready
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I4)
**Sprint:** Atual

## Contexto

Apos os 394 resultados carregarem com sucesso, o banner amarelo "Atualizando dados em tempo real..." permanece indefinidamente. O usuario fica inseguro se a busca terminou ou ainda esta processando.

## Acceptance Criteria

- [ ] AC1: Banner deve desaparecer quando busca finalizar (evento SSE `complete` ou `done`)
- [ ] AC2: Ou trocar texto para "Busca concluida — 394 oportunidades encontradas"
- [ ] AC3: Se existe revalidacao em background, mostrar "Buscando atualizacoes..." com timeout de 30s
- [ ] AC4: Testar com busca que completa normalmente e busca que usa cache stale

## Arquivos Provaveis

- `frontend/app/buscar/page.tsx` — state de loading/revalidating
- `frontend/app/buscar/components/CacheBanner.tsx` — banner de SWR
- `frontend/hooks/useSearch.ts` — flags de estado da busca

## Escopo

**IN:** `frontend/app/buscar/page.tsx` (lógica de estado do banner), `frontend/app/buscar/components/CacheBanner.tsx`, `frontend/hooks/useSearch.ts` (flag `isRevalidating`)  
**OUT:** Mudanças no fluxo SSE, alterações no backend, modificações no comportamento de cache SWR (apenas a exibição visual do banner)

## Complexidade

**XS** (< 4h) — identificar quando o evento SSE `complete` chega e garantir que o banner some ou mude de texto

## Riscos

- **Revalidação legítima:** Se o banner indica revalidação SWR em background (não apenas busca inicial), removê-lo prematuramente pode ocultar informação útil — AC3 cobre esse caso com timeout de 30s

## Critério de Done

- Após busca completar (SSE `complete` recebido), banner "Atualizando dados em tempo real" desaparece ou muda para "Busca concluída"
- Busca com cache stale: banner indica revalidação com timeout visível de 30s e some ao final
- Nenhum teste existente quebrado
