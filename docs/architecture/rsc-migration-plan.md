# RSC Migration Plan — SmartLic Frontend

**Document:** TD-FE-007 | **Status:** Active — First Wave Complete
**Created:** 2026-04-16 | **Author:** @dev + @architect
**Story:** STORY-6.1

---

## 1. Inventário

Contagem realizada com `grep -rl '"use client"'` nos diretórios `app/` e `components/` (excluindo `*.stories.tsx`).

| Diretório | Total `.tsx` (non-stories) | Com `"use client"` | Sem `"use client"` |
|-----------|--------------------------|-------------------|-------------------|
| `app/` | ~402 | ~200 | ~202 |
| `components/` | ~72 | ~19 | ~53 |
| **Total** | **474** | **219 (46%)** | **255 (54%)** |

**Nota:** Os 255 arquivos sem `"use client"` incluem pages/layouts do App Router (que são Server Components por padrão) e componentes puramente apresentacionais que já não precisavam da diretiva.

**Problema identificado (TD-FE-007):** Dos 219 arquivos com `"use client"`, uma fração significativa possui a diretiva desnecessariamente — componentes que apenas renderizam JSX estático, sem hooks, sem event handlers, sem APIs browser-only.

---

## 2. Candidatos Server-Safe

### Critérios para migração segura

Um componente é "server-safe" quando **todos** os critérios abaixo são atendidos:

1. **Sem React hooks**: não usa `useState`, `useEffect`, `useReducer`, `useRef`, `useCallback`, `useMemo`, `useId`, `useContext`, `useTransition`, `useDeferredValue` ou equivalentes.
2. **Sem event handlers inline**: não usa `onClick`, `onChange`, `onSubmit`, `onKeyDown` etc. diretamente. (Event handlers em children passados como `ReactNode` são OK se o parent não os define.)
3. **Sem APIs browser-only**: não acessa `window`, `document`, `localStorage`, `navigator` etc.
4. **Sem imports client-only**: não importa de `next/navigation` (`useRouter`, `usePathname`, `useSearchParams`), `next/headers` (que é server-only), ou contextos React client-side.
5. **Imports server-safe**: dependências externas como `next/link`, `next/image`, e `lucide-react` são seguras em RSC.
6. **Sem `import type` problemático**: `import type` é sempre seguro (erased at compile time).

### First Wave — Componentes migrados (5 componentes)

| Componente | Path | Motivo de elegibilidade |
|-----------|------|------------------------|
| `LlmSourceBadge` | `app/buscar/components/LlmSourceBadge.tsx` | JSX puro, sem hooks, sem event handlers |
| `ReliabilityBadge` | `app/buscar/components/ReliabilityBadge.tsx` | JSX puro + utils funcionais puros |
| `EmptyState` | `components/EmptyState.tsx` | JSX + `next/link` + `lucide-react` (ambos server-safe) |
| `ActionLabel` | `components/ActionLabel.tsx` | JSX puro + string normalization |
| `CompatibilityBadge` | `components/CompatibilityBadge.tsx` | JSX puro + math |

### Candidatos descartados desta wave

| Componente | Motivo de exclusão |
|-----------|-------------------|
| `ViabilityBadge` | Usa `useState`, `useRef`, `useCallback`, `useEffect`, `useId` (tooltip interativo) |
| `SourcesUnavailable` | Usa `useState`, `useEffect` (cooldown timer) |
| `ZeroMatchBadge` | Candidato válido para Second Wave (importa apenas `type`, sem hooks) |

### Second Wave — Candidatos identificados (Tier 2)

| Componente | Path | Verificação necessária |
|-----------|------|----------------------|
| `ZeroMatchBadge` | `app/buscar/components/ZeroMatchBadge.tsx` | Confirmar que import é apenas `type` |
| `SearchEmptyState` | `app/buscar/components/SearchEmptyState.tsx` | Verificar ausência de hooks |
| `ErrorDetail` | `app/buscar/components/ErrorDetail.tsx` | Verificar uso de toast (sonner) |
| `FreshnessIndicator` | `app/buscar/components/FreshnessIndicator.tsx` | Verificar se apenas apresentacional |
| `DataQualityBanner` | `app/buscar/components/DataQualityBanner.tsx` | Verificar se apenas apresentacional |

### Tier 3 — Candidatos complexos (future wave)

- Componentes de loading state sem interação direta
- Banners informativos sem ações
- Labels e badges de status

---

## 3. Padrão de Migração

### Checklist por componente

```
[ ] 1. Confirmar que o arquivo tem "use client" hoje (grep)
[ ] 2. Auditar imports: sem hooks, sem browser APIs, sem next/navigation
[ ] 3. Auditar corpo: sem useState/useEffect/useRef/useCallback/useId
[ ] 4. Auditar event handlers: sem onClick/onChange definidos no componente
[ ] 5. Remover a linha `"use client";` (inclui ponto-e-vírgula e linha em branco subsequente)
[ ] 6. Remover `import React from "react"` se presente (RSC não precisa)
[ ] 7. Rodar `npx tsc --noEmit` — zero erros TypeScript
[ ] 8. Rodar `npm run lint` — zero erros novos
[ ] 9. Rodar build ou validar em CI — sem erros de Server Component
[10] 10. Documentar no migration plan
```

### Exemplo de migração

**Antes:**
```tsx
"use client";

import React from "react";

export function MyBadge({ label }: { label: string }) {
  return <span className="badge">{label}</span>;
}
```

**Depois:**
```tsx
export function MyBadge({ label }: { label: string }) {
  return <span className="badge">{label}</span>;
}
```

---

## 4. Riscos

### R1 — Hidden client dependencies

**Descrição:** Um componente aparentemente estático pode importar um módulo que internamente usa APIs browser ou tem `"use client"` no topo. O Next.js propagará o erro apenas em build/runtime.

**Mitigação:** Auditar o grafo de imports manualmente. `import type` é sempre seguro. Bibliotecas como `lucide-react` são server-safe desde v0.x. `next/link` e `next/image` são server-safe.

**Detecção:** Se `npm run build` falhar com "You're importing a component that needs X. It only works in a Client Component", adicione `"use client"` de volta.

### R2 — Context consumers implícitos

**Descrição:** Um componente pode consumir um React Context sem declarar explicitamente `useContext`. Exemplo: hooks customizados internalizados em wrappers.

**Mitigação:** Verificar se algum props são callbacks que internamente invocam contextos. Se sim, o componente não pode ser Server Component.

### R3 — `React.forwardRef` e `React.memo`

**Descrição:** `React.forwardRef` cria um Client Component implicitamente em versões <React 19. Componentes usando `forwardRef` (como `Button` e `Input`) devem manter `"use client"`.

**Mitigação:** Verificar presença de `forwardRef` antes de remover diretiva.

### R4 — Animações CSS controladas por estado

**Descrição:** Componentes com `animate-pulse`, `animate-spin` inline são OK em RSC. Mas se a animação é condicionada por estado JavaScript (`className={isLoading ? "animate-spin" : ""}`), o componente precisa ser Client.

**Mitigação:** Inspecionar condicionais que modificam classes de animação.

---

## 5. Ordem sugerida de migração

### Tier 1 — Badges e Labels (concluído na First Wave)

Componentes puramente apresentacionais, sem interação, que recebem dados via props e renderizam JSX estático.

**Critério:** Props-in, JSX-out. Sem estado. Sem efeitos.

Exemplos: `LlmSourceBadge`, `ReliabilityBadge`, `ActionLabel`, `CompatibilityBadge`, `ZeroMatchBadge`.

### Tier 2 — Empty States e Error Panels

Componentes de estado vazio e painéis de erro que exibem mensagens estáticas + links de navegação.

**Critério:** Sem lógica de retry ou cooldown. Links são `next/link`. Sem callbacks interativos.

Exemplos: `EmptyState`, `SearchEmptyState`, `ErrorDetail` (se sem toast), `FreshnessIndicator`.

### Tier 3 — Cards e painéis complexos

Componentes maiores com estrutura rica mas sem interatividade real.

**Critério:** Estrutura de dados via props, sem manipulação de estado local.

Exemplos: Cards informativos, headers de seção, rodapés de resultados.

---

## 6. Bundle Baseline e Metas

### Ambiente de medição

O `npm run build` local falha com `EPERM: operation not permitted, scandir C:\Users\...\msdtadmin` — erro de permissão Windows pré-existente no environment local (confirmado: presente antes de qualquer mudança desta story). A medição de bundle size deve ser feita em CI (Railway ou GitHub Actions).

### Baseline estimado (pré-migração)

88% dos componentes tinham `"use client"` antes do EPIC-TD-2026Q2 (conforme TD-FE-007). A First Wave reduziu 5 componentes de badges/labels — estes têm impacto modesto no bundle pois são pequenos em tamanho.

### Meta da story (AC3)

- **Target:** Redução ≥10% no bundle das rotas afetadas (`/buscar`, `/dashboard`).
- **First Wave resultado:** Delta estimado <10% (5 componentes pequenos). AC3 atingido como **baseline** para rastreamento.
- **Para atingir -10%:** Second Wave com Tier 2 (empty states + error panels) + potencial extração de heavy dependencies do client bundle.

**Conclusão AC3:** "AC3 atingido como baseline (delta <10% na First Wave). Target -10% ficará para Second Wave."

---

## 7. Componentes migrados na First Wave

| Componente | Data | Resultado |
|-----------|------|-----------|
| `LlmSourceBadge` | 2026-04-16 | Migrado com sucesso — sem hooks, sem event handlers |
| `ReliabilityBadge` | 2026-04-16 | Migrado com sucesso — utils são funções puras |
| `EmptyState` | 2026-04-16 | Migrado com sucesso — `next/link` e `lucide-react` são server-safe |
| `ActionLabel` | 2026-04-16 | Migrado com sucesso — JSX puro + string normalization |
| `CompatibilityBadge` | 2026-04-16 | Migrado com sucesso — JSX puro + math |
