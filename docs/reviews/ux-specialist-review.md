# UX Specialist Review
**Reviewer:** @ux-design-expert
**Date:** 2026-03-20
**DRAFT Reviewed:** docs/prd/technical-debt-DRAFT.md (Brownfield Discovery Phase 4)
**Methodology:** Code-verified against actual frontend source (not spec-only)

---

## Debitos Validados

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Impacto UX | Design Review? | Notas |
|----|--------|---------------|---------------|-------|-----------|---------------|-------|
| FE-01 | Inline `var()` ao inves de Tailwind tokens | CRITICAL | **HIGH** | 32h | Visual: nenhum (funciona identicamente). DX: alto (inconsistencia de autoria) | Sim | Contagem real: ~1,754 ocorrencias em producao (nao 1,417). Porem isso nao e CRITICAL porque o comportamento visual e identico -- `bg-[var(--canvas)]` renderiza o mesmo que `bg-canvas`. O mapeamento Tailwind ja existe em tailwind.config.ts (DEBT-012). E debt de DX/consistencia, nao de UX. Rebaixo para HIGH. Estimo 32h (nao 40h) porque um codemod regex simples cobre 80% dos casos. |
| FE-02 | Component library UI ausente (6 primitivos) | HIGH | **HIGH** | 24h | Funcional: medio (inconsistencia visual entre paginas). DX: alto (duplicacao de codigo) | Sim | Validado. `components/ui/` tem apenas: button.tsx, Input.tsx, Label.tsx, Pagination.tsx, CurrencyInput.tsx, Button.examples.tsx. Faltam Card, Badge, Modal, Dialog, Select, Tabs, Tooltip como primitivos reutilizaveis. Cada pagina reinventa esses patterns inline. |
| FE-03 | Complexidade da pagina Buscar | HIGH | **HIGH** | 16h | Manutencao: alto. UX direto: nenhum (funciona bem para o usuario) | Nao | Validado: 39 componentes em `app/buscar/components/` + 9 hooks. Complexidade real mas e debt de engenharia, nao UX. Manter HIGH por custo de manutencao. |
| FE-04 | Padrao inconsistente de error pages | HIGH | **MEDIUM** | 3h | Funcional: baixo (todas reportam ao Sentry) | Nao | **Parcialmente falso.** Verifiquei TODOS 9 error.tsx: buscar, pipeline, historico, dashboard, conta, alertas, mensagens, admin, root -- TODOS importam Sentry e chamam `captureException`. A diferenca real e: root error.tsx usa analytics tracking + inline var() classes; per-route error.tsx (alertas, buscar, etc.) usam tokens Tailwind semanticos. A inconsistencia e cosmetica, nao funcional. Rebaixo para MEDIUM. |
| FE-05 | Cores hex raw em global-error.tsx e ThemeProvider | HIGH | **LOW** | 0.5h | Visual: nenhum | Nao | **Contexto ignorado pelo audit.** global-error.tsx DEVE usar inline styles com hex porque e o fallback quando o root layout falha -- nao tem acesso a Tailwind/CSS vars. O arquivo ja define suas proprias CSS vars com prefixo `--ge-*` e suporta dark mode via `prefers-color-scheme`. E um design CORRETO, nao um bug. Rebaixo para LOW (cosmetico: poderia alinhar hex values com design tokens como comentario). |
| FE-06 | Padrao de dual footer | HIGH | **MEDIUM** | 4h | UX: baixo-medio (confuso apenas se usuario scrolla buscar ate o final, o que e raro) | Sim | Validado. Buscar page tem footer dedicado com links uteis (Central de Ajuda, atalhos, etc.) + NavigationShell footer minimo. Documentado como intencional (SAB-013/DEBT-105). Na pratica, o footer da buscar e util e contextual. Rebaixo para MEDIUM -- unificacao seria nice-to-have. |
| FE-07 | useIsMobile initial false flash | HIGH | **HIGH** | 2h | UX: medio (layout shift perceptivel em mobile) | Nao | Validado. `useState(false)` em useIsMobile.ts. Toda renderizacao condicional baseada neste hook mostra desktop-first por 1 frame. Contribui para CLS. |
| FE-08 | Sem estrategia de image optimization | HIGH | **LOW** | 2h | Performance: minimo | Nao | **Severamente superestimado.** Verifiquei: o codebase tem apenas 4 imagens em `/public` (logo.svg, logo-descomplicita.png, hero-screenshot.png, hero-screenshot.webp). ZERO uso de `<img>` tags em JSX. HeroSection ja usa `next/image` com WebP. Nao ha imagens nao-otimizadas porque o app e predominantemente data/text UI. Rebaixo para LOW, 2h. |
| FE-09 | Localizacao inconsistente de componentes | MEDIUM | **MEDIUM** | 8h | DX: alto | Nao | Validado. `components/` (shared), `app/components/` (mixed), `app/buscar/components/` (page-specific). AuthProvider vive em `app/components/` mas e importado por 7 arquivos em `components/`. |
| FE-10 | Blog/SEO pages sem loading states | MEDIUM | **LOW** | 2h | UX: minimo (SSC pages sao rapidas) | Nao | Validado. Nenhum loading.tsx em `/blog` ou `/licitacoes`. Porem sao Server Components com static/ISR rendering -- loading states sao menos criticos. Rebaixo para LOW. |
| FE-11 | Animacoes duplicadas (CSS + Tailwind) | MEDIUM | **LOW** | 2h | DX: baixo | Nao | Validado. fadeInUp, shimmer, float definidos em globals.css E tailwind.config.ts. Funciona corretamente -- e redundancia, nao conflito. |
| FE-12 | Pages sem PageErrorBoundary | MEDIUM | **MEDIUM** | 3h | Resiliencia: medio | Nao | Validado. 9 error.tsx existem cobrindo todas rotas principais. A questao e se COMPONENTES internos capturam erros -- SearchErrorBoundary existe para buscar, mas outras paginas nao tem boundaries sub-page. |
| FE-13 | Falta aria-current no Sidebar | MEDIUM | **REMOVIDO** | -- | -- | -- | **FALSO POSITIVO.** Verifiquei `Sidebar.tsx` linha 86: `aria-current={active ? "page" : undefined}`. O Sidebar JA tem aria-current. Tanto Sidebar quanto BottomNav implementam corretamente. |
| FE-14 | Feature-gated pages ainda roteáveis | MEDIUM | **MEDIUM** | 2h | UX: medio (usuario chega em pagina funcional que pode nao estar pronta) | Nao | Parcialmente validado. `/alertas` e `/mensagens` estao na verdade FUNCIONAIS (nao sao stubs) -- tem UI completa com hooks SWR. O "feature gate" e apenas ocultar da navegacao. Se usuario acessa URL diretamente, funciona. Manter MEDIUM mas ajustar descricao. |
| FE-15 | Admin pages sem responsive | MEDIUM | **LOW** | 1h | UX: minimo (<5 usuarios internos) | Nao | Validado. Admin page principal ja tem `overflow-x-auto` em tabelas. SLO page tambem. O investimento de 8h nao justifica. Paliativo de 1h (`overflow-x-auto` onde faltar) e suficiente. |
| FE-16 | Sem Storybook | MEDIUM | **MEDIUM** | 16h | DX: alto (longo prazo) | Nao | Validado. Nao ha Storybook, component playground, ou documentacao visual. Com apenas 6 primitivos UI, o ROI atual e baixo. Cresce quando FE-02 (component library) for resolvido. |
| FE-17 | Pull-to-refresh desktop hack CSS | MEDIUM | **LOW** | 1h | DX: baixo | Nao | Validado. `globals.css` usa `@media (pointer: fine)` para desabilitar em desktop. E uma abordagem padrao, nao fragil. A alternativa (condicionar render) adicionaria re-render desnecessario. Rebaixo para LOW. |
| FE-18 | Shepherd.js Tailwind raw | MEDIUM | **MEDIUM** | 2h | Visual: medio (dark mode quebrado em onboarding tour) | Sim | Validado. `bg-white`, `text-gray-700`, `bg-gray-50`, `bg-blue-600`, `text-gray-600`, `bg-gray-300`, `ring-blue-500` -- 15+ usos de Tailwind defaults que NAO respeitam o design system. Dark mode usa `dark:` variants do Tailwind gray palette, nao os tokens de design (--surface-*, --ink-*). Tour visual sera inconsistente com o resto do app em temas customizados. |
| FE-19 | react-hook-form em devDependencies | MEDIUM | **MEDIUM** | 0.5h | Build: potencialmente critico | Nao | Validado. Linha 85 de package.json: `"react-hook-form": "^7.71.2"` esta em devDependencies. Usado em signup e onboarding (producao). Funciona hoje porque Next.js bundla tudo no build, mas e incorreto semanticamente e pode quebrar em edge cases (monorepos, pnpm strict). |
| FE-20 | SVGs sem aria-hidden | MEDIUM | **MEDIUM** | 3h | Acessibilidade: medio | Nao | Validado parcialmente. 396 usos de `aria-hidden` ja existem em 141 arquivos. A maioria dos SVGs decorativos ja esta coberta. Verificacao pontual: error.tsx files usam `aria-hidden="true"`. A lacuna e em SVGs inline menores espalhados. |
| FE-21 | Focus management apos modal close | MEDIUM | **MEDIUM** | 4h | Acessibilidade: medio | Nao | Validado. BottomNav tem focus trap. BuscarModals, InviteMemberModal, CancelSubscriptionModal, AlertFormModal -- sem evidencia de focus return ao trigger. |
| FE-22 | PlanToggle sem focus visible | MEDIUM | **REMOVIDO** | -- | -- | -- | **FALSO POSITIVO.** Verifiquei `PlanToggle.tsx` linha 67: `focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2`. Focus ring esta IMPLEMENTADO corretamente nos radio buttons. |
| FE-23 | 59 API route files (cold start) | MEDIUM | **LOW** | 0h | Performance: nao mensuravel | Nao | O impacto em cold start e teorico. Railway usa `output: "standalone"` que bundla tudo. Next.js App Router nao cria serverless functions individuais no modo standalone -- todas rotas rodam no mesmo processo Node.js. Rebaixo para LOW e estimo 0h (nao e um problema real). |
| FE-24 | Sem a11y tests no CI | LOW | **LOW** | 4h | Acessibilidade: longo prazo | Nao | Validado. `@axe-core/playwright` instalado (devDependencies) mas nao integrado nos E2E tests ou CI pipeline. |
| FE-25 | Tailwind content paths com pages/ | LOW | **LOW** | 0.5h | Build: nenhum (scan extra negligivel) | Nao | **FALSO POSITIVO.** Verifiquei tailwind.config.ts linha 7: `"./pages/**/*.{js,ts,jsx,tsx,mdx}"` -- porem `pages/` NAO existe. Entretanto, Tailwind simplesmente ignora paths inexistentes, zero impacto. Manter LOW mas poderia ser removido por higiene. |
| FE-26 | Imports circulares potenciais | LOW | **MEDIUM** | 4h | DX/Estabilidade: medio | Nao | Validado. 7 arquivos em `components/` importam de `app/components/AuthProvider`. Isso cria uma dependencia de shared -> page-specific que viola a arquitetura. Se AuthProvider fosse movido para `components/` ou `contexts/`, elimina o risco. Subo para MEDIUM. |
| FE-27 | NProgress vs built-in Next.js | LOW | **LOW** | 0h | -- | Nao | NProgress funciona bem e esta integrado. Next.js nao tem um equivalente built-in robusto para App Router client-side transitions. Nao e debt real. Estimo 0h. |
| FE-28 | Formatacao de datas inconsistente | LOW | **LOW** | 3h | DX: baixo | Nao | Validado. 25 arquivos usam padroes mistos. Funcional mas inconsistente. |
| FE-29 | Toast vs banner inconsistente | LOW | **LOW** | 4h | UX: baixo | Sim | Validado. Sonner para notificacoes transitorias, banners inline para erros persistentes. A estrategia ATUAL e razoavel -- falta documentacao da convencao, nao unificacao forcada. |
| FE-30 | Shepherd arrow hidden | LOW | **LOW** | 1h | UX: minimo | Nao | Validado. `.shepherd-arrow { @apply hidden; }` em globals.css. |
| FE-31 | Dashboard icon duplicado no BottomNav | LOW | **LOW** | 0.5h | UX: baixo (confusao visual sutil) | Nao | Validado. BottomNav linha 48: `icon: icons.search` para Dashboard. Deveria ser `icons.dashboard` (LayoutDashboard). |
| FE-32 | Framer Motion bundle | LOW | **LOW** | 0h | Performance: negligivel | Nao | Framer Motion ja e isolado em landing pages. Tree-shaking funciona. Nao e debt real. |

---

## Debitos Adicionados

| ID | Debito | Severidade | Area | Horas | Impacto UX | Design Review? |
|----|--------|-----------|------|-------|-----------|---------------|
| FE-33 | **Error pages usam tokens inconsistentes entre si.** Root `error.tsx` usa `bg-[var(--surface-0)]`, `text-[var(--ink)]` (inline vars). Per-route error.tsx (alertas, buscar, etc.) usam `bg-surface-0`, `text-ink` (Tailwind tokens). Ambos patterns coexistem -- deveria ser unificado para tokens Tailwind. | LOW | Design System | 2h | Visual: nenhum (renderiza igual) | Nao |
| FE-34 | **AuthProvider em localizacao incorreta.** `app/components/AuthProvider.tsx` e importado por 7+ componentes em `components/`. Deveria estar em `contexts/` ou `components/` (shared). Cria a dependencia circular documentada em FE-26. | MEDIUM | DX | 2h | Estabilidade: medio | Nao |
| FE-35 | **Dashboard no BottomNav usa label abreviado "Dash" sem aria-label.** BottomNav define `ariaLabel: "Dashboard"` -- isso esta correto. Entretanto, o label visual "Dash" pode confundir usuarios nao-tech. Considerar "Painel" (PT-BR nativo). | LOW | UX | 0.5h | UX: minimo | Nao |
| FE-36 | **Shepherd.js tour arrow hidden remove affordance visual.** Arrow conecta visualmente o tooltip ao elemento target. Sem arrow, usuario pode nao entender qual elemento esta sendo explicado, especialmente em tour steps que apontam para elementos pequenos. | LOW | UX | 1h | UX: baixo | Nao |

---

## Falsos Positivos Removidos

| ID | Motivo da Remocao |
|----|-------------------|
| FE-13 | **aria-current no Sidebar JA IMPLEMENTADO.** `Sidebar.tsx:86` tem `aria-current={active ? "page" : undefined}`. Tanto Sidebar quanto BottomNav estao corretos. O audit original nao verificou o codigo real. |
| FE-22 | **PlanToggle focus visible JA IMPLEMENTADO.** `PlanToggle.tsx:67` tem `focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2`. Focus ring funciona corretamente via teclado. |

---

## Respostas ao Architect

### 1. FE-01 -- Estrategia de migracao inline var()

**Recomendacao: codemod automatico (horizontal) + validacao por pagina.**

O mapeamento Tailwind ja existe em `tailwind.config.ts` (DEBT-012 criou todos os tokens). A migracao e puramente mecanica:

```bash
# Codemod regex (cobre ~80% dos casos):
# bg-[var(--canvas)] -> bg-canvas
# text-[var(--ink-secondary)] -> text-ink-secondary
# border-[var(--border)] -> border (DEFAULT mapping)
```

Abordagem recomendada:
1. Criar script de codemod (2h)
2. Rodar por diretorio, validar visualmente (20h)
3. Resolver edge cases manuais (10h)

NAO recomendo migrar por componente (bottom-up) porque a maioria dos usos e em paginas, nao componentes. A migracao horizontal por token (todos `bg-[var(--canvas)]` de uma vez) e mais segura e testavel.

### 2. FE-02 -- Primitivos prioritarios e abordagem

**Top 5 primitivos por urgencia:**
1. **Card** -- Usado em 15+ paginas (ResultCard, PipelineCard, AlertCard, DashboardStatCards, etc.)
2. **Modal/Dialog** -- 8+ implementacoes ad-hoc (BuscarModals, InviteMemberModal, CancelSubscriptionModal, AlertFormModal, DeepAnalysisModal, etc.)
3. **Badge** -- 10+ variantes (ViabilityBadge, CompatibilityBadge, ReliabilityBadge, LlmSourceBadge, ZeroMatchBadge, PlanBadge, StatusBadge, etc.)
4. **Select** -- CustomSelect existe em `app/components/` mas nao e primitivo UI. Multiplos selects customizados per-page.
5. **Tabs** -- Pipeline usa tabs mobile, conta/layout usa tabs de navegacao, admin usa tabs.

**Abordagem recomendada: Radix UI + CVA (Shadcn/UI pattern).**

O projeto ja usa CVA para Button. Adotar Radix UI headless daria acessibilidade built-in (focus management, keyboard nav, ARIA) sem opinionated styling. Shadcn/UI e o modelo de referencia perfeito -- gera componentes locais (nao dependencia), usa Tailwind + CVA, e o padrao mais adotado no ecossistema Next.js em 2026.

NAO recomendo construir do zero -- reinventar focus traps, keyboard navigation, e ARIA para modais/selects e custoso e propenso a bugs.

### 3. FE-06 -- Dual footer

**O footer da buscar page tem funcionalidades especificas que justificam sua existencia:** links para Central de Ajuda, atalhos de teclado, dicas de uso. O footer do NavigationShell e minimalista (copyright + links legais).

**Recomendacao: manter dual footer mas unificar visualmente.** Criar um `Footer` primitivo com variantes `minimal` (NavigationShell) e `rich` (buscar). Mesma base visual, conteudo configuravel. Estimo 4h.

### 4. FE-07 -- useIsMobile SSR-safe

**Recomendacao: CSS-first com `useMediaQuery` como fallback.**

Para layout (mostrar/esconder sidebar vs bottom nav), usar CSS `@media` puro -- zero layout shift. O hook `useIsMobile` deveria ser reservado apenas para logica JS que NAO tem equivalente CSS (ex: condicionar API calls, alterar tamanho de paginacao).

Correcao imediata (2h):
```typescript
export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`).matches;
  });
  // ... rest unchanged
}
```

Isso elimina o flash no primeiro client render (matchMedia e sincrono). SSR ainda retorna false, mas o primeiro paint no client ja sera correto.

### 5. FE-08 -- Image optimization

**Impacto real: MINIMO.** O codebase tem apenas 4 imagens em `/public`:
- `logo.svg` (SVG, ja otimo)
- `logo-descomplicita.png` (parceiro logo)
- `hero-screenshot.png` + `hero-screenshot.webp` (hero ja tem WebP)

ZERO tags `<img>` em JSX. O app e predominantemente data/text UI. `next/image` em HeroSection ja cobre o unico caso critico.

**Recomendacao:** Migrar `logo-descomplicita.png` para `next/image` (30min). Nao ha mais imagens para otimizar. A estimativa original de 8h e severamente inflada.

### 6. FE-15 -- Admin responsive

**Recomendacao: paliativo de 1h, P3.**

Admin pages ja tem `overflow-x-auto` na tabela principal. Aplicar em SLO e partners onde faltar (1h total). <5 usuarios internos, todos em desktop. O investimento de 8h em responsive completo nao justifica.

---

## Solucoes de Design Propostas

### FE-01: Inline var() Migration
**Problema:** ~1,754 ocorrencias de `bg-[var(--X)]` ao inves de `bg-X` em producao.
**Solucao:** Codemod regex automatico. Todos os tokens ja estao mapeados em tailwind.config.ts.
**Exemplo:**
```bash
# Transformacao automatica:
sed -i 's/bg-\[var(--canvas)\]/bg-canvas/g' **/*.tsx
sed -i 's/text-\[var(--ink)\]/text-ink/g' **/*.tsx
sed -i 's/text-\[var(--ink-secondary)\]/text-ink-secondary/g' **/*.tsx
# ... (script completo para todos tokens)
```
**Pre-requisito:** Validar que TODOS tokens usados em `var()` tem mapeamento em tailwind.config.ts. Tokens faltantes: `--gradient-*`, `--glass-*`, `--text-hero` (estes ficam como `var()` -- sem equivalente Tailwind).

### FE-02: Component Library Bootstrap
**Problema:** Apenas 6 primitivos UI. Modais, cards, badges reinventados per-page.
**Solucao:** Instalar `@radix-ui/react-dialog`, `@radix-ui/react-select`, `@radix-ui/react-tabs`. Criar wrappers CVA em `components/ui/`.
**Exemplo (Card):**
```tsx
// components/ui/Card.tsx
import { cva, type VariantProps } from "class-variance-authority";

const cardVariants = cva("rounded-card border transition-shadow", {
  variants: {
    variant: {
      default: "bg-surface-0 border-DEFAULT shadow-sm",
      elevated: "bg-surface-elevated border-DEFAULT shadow-md",
      interactive: "bg-surface-0 border-DEFAULT shadow-sm hover:shadow-md cursor-pointer",
    },
    padding: {
      none: "",
      sm: "p-4",
      md: "p-6",
      lg: "p-8",
    },
  },
  defaultVariants: { variant: "default", padding: "md" },
});

export interface CardProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof cardVariants> {}

export function Card({ className, variant, padding, ...props }: CardProps) {
  return <div className={cardVariants({ variant, padding, className })} {...props} />;
}
```

### FE-07: useIsMobile Layout Shift Fix
**Problema:** useState(false) causes desktop-first flash on mobile devices.
**Solucao:** Use synchronous matchMedia in initializer function.
**Exemplo:**
```typescript
const [isMobile, setIsMobile] = useState(() => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`).matches;
});
```

### FE-18: Shepherd.js Theme Alignment
**Problema:** 15+ uses of Tailwind defaults (bg-white, text-gray-700, bg-blue-600) instead of design tokens.
**Solucao:** Replace all with design system tokens.
**Exemplo:**
```css
/* BEFORE */
.shepherd-theme-custom {
  @apply bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200;
}
/* AFTER */
.shepherd-theme-custom {
  @apply bg-surface-elevated rounded-modal shadow-2xl border;
}
```

---

## Recomendacoes de Design System

### Primitivos a Padronizar (ordem de prioridade)

1. **Tokens ja existem -- adocao falta.** tailwind.config.ts tem 35+ color tokens, 4 border-radius tokens, 8 shadow tokens. Estao la, so nao sao usados (FE-01).

2. **Card** -- Componente mais duplicado. Padronizar com CVA variants (default, elevated, interactive).

3. **Modal/Dialog** -- Radix Dialog com wrapper. Unifica focus trap, ESC close, overlay, focus return.

4. **Badge** -- CVA com variants: status (success, warning, error), info (muted, accent), size (sm, md).

5. **Select** -- Radix Select com styling alinhado ao Input existente.

6. **Tabs** -- Radix Tabs para conta layout, pipeline mobile, admin.

### Convencoes a Documentar

- **Quando usar toast vs banner:** Toast para acoes do usuario (salvou, copiou, erro transitorio). Banner para estados do sistema (backend offline, cache stale, trial expirando).
- **Quando usar inline var() vs Tailwind token:** NUNCA usar inline var() se o token Tailwind existe. Reservar `[var(--X)]` apenas para tokens sem mapeamento (gradients, glass effects).
- **Localizacao de componentes:** `components/ui/` = primitivos atomicos. `components/` = compostos compartilhados. `app/X/components/` = especificos de pagina.

---

## Quick Wins UX (< 4h cada)

| # | Item | Horas | Impacto |
|---|------|-------|---------|
| 1 | FE-31: Trocar `icons.search` por `icons.dashboard` no BottomNav | 0.5h | Corrige icone errado visivel para todo usuario mobile |
| 2 | FE-19: Mover react-hook-form de devDependencies para dependencies | 0.5h | Corrige classificacao semantica incorreta de dependencia |
| 3 | FE-07: Fix useIsMobile initializer | 2h | Elimina layout shift em mobile |
| 4 | FE-25: Remover `pages/` de tailwind content paths | 0.5h | Higiene de config |
| 5 | FE-30: Re-habilitar shepherd arrow | 1h | Melhora affordance visual do tour |
| 6 | FE-15: Adicionar overflow-x-auto em admin tables faltantes | 1h | Tabelas nao cortam em telas menores |
| 7 | FE-35: Renomear "Dash" para "Painel" no BottomNav | 0.5h | Label PT-BR nativo |
| 8 | FE-33: Unificar error.tsx para usar Tailwind tokens | 2h | Consistencia DX |

---

## Resumo

| Metrica | Valor |
|---------|-------|
| **Total do DRAFT original** | 32 items |
| **Total validado** | 28 items |
| **Total adicionado** | 4 items (FE-33, FE-34, FE-35, FE-36) |
| **Total removido (falsos positivos)** | 2 items (FE-13, FE-22) |
| **Final** | 34 items |
| **Severidade ajustada** | 1 CRITICAL->HIGH, 3 HIGH->MEDIUM, 2 HIGH->LOW, 4 MEDIUM->LOW, 1 LOW->MEDIUM |
| **Esforco total original** | 180h |
| **Esforco total revisado** | ~140h |
| **Items requiring design review** | 4 (FE-01, FE-02, FE-06, FE-18) |

### Mudancas Mais Significativas

1. **FE-01 rebaixado de CRITICAL para HIGH** -- Funciona perfeitamente, e debt de DX, nao UX.
2. **FE-05 rebaixado de HIGH para LOW** -- global-error.tsx usa inline styles BY DESIGN (root layout failed).
3. **FE-08 rebaixado de HIGH para LOW** -- Apenas 4 imagens no codebase, hero ja otimizada.
4. **FE-13 e FE-22 removidos** -- Ambos ja implementados corretamente no codigo.
5. **FE-23 rebaixado para LOW, 0h** -- Standalone output nao cria serverless functions individuais.

### Nenhum CRITICAL restante no frontend.

O item mais impactante para UX real e **FE-07 (useIsMobile flash)** -- 2h de trabalho que elimina layout shift perceptivel em todos devices mobile.

O item mais impactante para DX e **FE-02 (component library)** -- 24h que destrava FE-01, FE-03, e melhora produtividade do time em toda feature futura.

---

*Revisado 2026-03-20 por @ux-design-expert durante Brownfield Discovery Phase 6.*
*Todos os items verificados contra codigo fonte real, nao apenas spec.*
