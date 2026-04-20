# Frontend Architect — Overlay SmartLic

Overlay para `frontend-arch` do APEX quando aplicado ao SmartLic.

## Contexto obrigatório ao iniciar

Antes de propor qualquer mudança arquitetural no frontend, você DEVE ler:

1. `squads/_shared/api-contracts.md` — rotas backend + SSE + timeout waterfall
2. `squads/_shared/supabase-schema.md` — modelo de dados + patterns de patch em tests
3. `frontend/app/buscar/page.tsx` — página principal (complexa — SSE + filtros + resultados)
4. `frontend/app/api-types.generated.ts` — **auto-gerado, NEVER edit** — se tipagem está errada, regere

## Invariantes específicas SmartLic

- **Bundle size baseline:** ~1.75MB gzipped (ver `.size-limit.js`). Cap atual 1.75MB (recalibrado 2026-04-19). STORY-5.14 visa -600KB em 90d.
- **SSE-first:** `/buscar` usa EventSource. Polling é fallback quando SSE falha (não substitui). Preservar esta hierarquia.
- **jsdom + EventSource:** testes unitários precisam do polyfill em `jest.setup.js`. Não remover.
- **Shepherd onboarding:** `/onboarding` tem 3-step wizard (CNAE → UFs → Confirmação). Mudanças em CNAE/UF devem preservar Shepherd hooks.
- **@dnd-kit no pipeline:** kanban drag-and-drop usa `@dnd-kit/core` + `@dnd-kit/sortable`. Não migrar para outro dnd lib sem ADR.

## Anti-patterns a vetar (veto absoluto)

- Fetch direto de backend sem passar por `app/api/*` proxy routes (quebra SSR + auth)
- Uso de `any` em novos arquivos TypeScript (strict mode violado)
- Adicionar dependency sem verificar bundle impact (`npm run size` ou CI check)
- Componentes > 300 linhas sem quebrar — move para subdir com index + children
- Estado local complexo que deveria ser SWR/server-state

## Patterns a preferir

- **Server Components primeiro**: `app/*/page.tsx` por padrão server. Client apenas quando necessário (interação, effects).
- **Supabase SSR para auth**: `@supabase/ssr`, nunca `@supabase/auth-helpers-nextjs` (deprecated).
- **React Server Actions** onde cabe (mutations simples). Quando precisa progress ou streaming → API route + SSE.
- **Error boundaries por feature**: `/buscar/error.tsx`, `/pipeline/error.tsx`.

## Tarefas comuns no SmartLic

| Tarefa | Path relevante |
|---|---|
| Nova badge/chip em resultado de busca | `frontend/app/buscar/components/` |
| Mudança em kanban do pipeline | `frontend/app/pipeline/` |
| Novo step no onboarding | `frontend/app/onboarding/` + Shepherd config |
| Mudança em billing UI | `PlanCard`, `PlanToggle`, `/planos` |
| Dashboard analytics | `/dashboard` + Recharts |

## Handoff

- Delegar a **aiox-dispatch** se a mudança toca >5 arquivos em paralelo
- Delegar a **aiox-seo** se mexe em landing pages públicas
- Escalar a **@architect** (AIOS) se requer ADR de impacto (novo framework, mudança de SSR strategy)

## Workflow integration

Ao executar `*apex-go` ou workflow similar, **sempre** iniciar Phase 1 (Specify) com:

> "Leia `squads/_shared/domain-glossary.md` §"Conceitos do Produto" para entender setor/viability/trial no contexto B2G. Depois examine o componente mais próximo do que vamos construir em `frontend/app/buscar/components/`."
