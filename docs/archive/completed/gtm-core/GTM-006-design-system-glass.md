# GTM-006: Unificação do Design System — Glass Morphism Consistente

| Metadata | Value |
|----------|-------|
| **ID** | GTM-006 |
| **Priority** | P1 |
| **Sprint** | 2 |
| **Estimate** | 16h |
| **Type** | GTM (Go-to-Market) |
| **Dependencies** | GTM-001 (copy pronta para design) |
| **Blocks** | — |
| **Status** | In Progress |
| **Created** | 2026-02-15 |
| **Squad** | Frontend (UX Design Expert + Dev) |

---

## Problem Statement

### Inconsistências Identificadas na Auditoria

O design system atual apresenta divergências significativas entre a landing page e a área logada, criando uma experiência desconexa que prejudica a percepção de qualidade premium:

| Inconsistência | Landing | Área Logada |
|---------------|---------|-------------|
| **Glass effects** | `backdrop-blur-md` (GlassCard) | Sem glass (LicitacaoCard sólido) |
| **Header** | `text-2xl`, transparente→glass on scroll | `text-xl`, sempre glass |
| **Cards** | GlassCard com hover-lift | Solid cards sem efeito |
| **Seção backgrounds** | Variados (surface-0, surface-1, brand-blue-subtle) | Uniformes |
| **Animações** | Framer Motion pesado | Mínimas |

### Impacto no Negócio

- **Bounce Rate**: Usuários percebem "salto visual" ao navegar de landing para login para busca
- **Percepção Premium**: Design inconsistente contradiz o posicionamento de preço único de R$ 1.999/mês
- **Trust**: Falta de polish sugere produto incompleto ou em estágio beta

### Diretriz Estratégica

> **"Minimalista, moderno, elegante, estilo glass em todos os elementos. Acentos de pedras preciosas translúcidas."**

O design deve transmitir sofisticação, confiança e valor — alinhado com o reposicionamento estratégico de "inteligência de decisão" (não "ferramenta de busca rápida").

---

## Solution/Scope

### Arquivos Afetados

#### 1. Design Tokens e Configuração Base

| Arquivo | Mudança | Detalhes |
|---------|---------|----------|
| `frontend/app/globals.css` | **Adicionar palette de pedras preciosas translúcidas** | Definir CSS custom properties para gem-sapphire, gem-emerald, gem-amethyst, gem-ruby com opacidade 10-20% |
| `frontend/tailwind.config.ts` | **Adicionar tokens Tailwind** | Mapear pedras preciosas para classes utilitárias (`bg-gem-sapphire`, etc.) |

**Exemplo de implementação:**

```css
/* frontend/app/globals.css */
:root {
  /* Pedras preciosas translúcidas */
  --gem-sapphire: rgba(15, 82, 186, 0.15);      /* Azul safira */
  --gem-emerald: rgba(16, 185, 129, 0.12);      /* Verde esmeralda */
  --gem-amethyst: rgba(139, 92, 246, 0.15);     /* Roxo ametista */
  --gem-ruby: rgba(239, 68, 68, 0.15);          /* Vermelho rubi */
}

[data-theme="dark"] {
  --gem-sapphire: rgba(96, 165, 250, 0.2);
  --gem-emerald: rgba(52, 211, 153, 0.18);
  --gem-amethyst: rgba(167, 139, 250, 0.2);
  --gem-ruby: rgba(248, 113, 113, 0.2);
}
```

#### 2. Componentes Core

| Arquivo | Mudança | Detalhes |
|---------|---------|----------|
| `frontend/app/components/ui/GlassCard.tsx` | **Adicionar variant `result`** | Nova variante para cards de resultado de busca com glass effect + gems accent |
| `frontend/app/components/LicitacaoCard.tsx` | **Migrar para GlassCard** | Substituir implementação sólida atual por `<GlassCard variant="result">` |
| `frontend/app/components/AppHeader.tsx` | **Unificar com LandingNavbar** | Usar mesma base de código, adaptar apenas conteúdo (logo+nav vs logo+user menu) |

**Exemplo de GlassCard variant:**

```tsx
// frontend/app/components/ui/GlassCard.tsx
interface GlassCardProps {
  variant?: 'default' | 'result' | 'pricing' | 'feature';
  gemAccent?: 'sapphire' | 'emerald' | 'amethyst' | 'ruby';
  children: React.ReactNode;
}

export function GlassCard({ variant = 'default', gemAccent, children }: GlassCardProps) {
  const variantClasses = {
    default: 'backdrop-blur-md bg-white/10 dark:bg-black/20',
    result: 'backdrop-blur-lg bg-white/5 dark:bg-black/10 border border-white/20',
    pricing: 'backdrop-blur-xl bg-white/8 dark:bg-black/15',
    feature: 'backdrop-blur-md bg-gradient-to-br from-white/10 to-white/5'
  };

  const gemClasses = gemAccent ? `shadow-lg shadow-gem-${gemAccent}` : '';

  return (
    <div className={cn(
      "rounded-xl transition-all hover:scale-[1.02]",
      variantClasses[variant],
      gemClasses
    )}>
      {children}
    </div>
  );
}
```

#### 3. Headers e Navegação

| Arquivo | Mudança | Detalhes |
|---------|---------|----------|
| `frontend/app/buscar/page.tsx` header | **Alinhar com landing** | Usar mesma estrutura glass, transição transparente→glass on scroll, logo size consistente |
| `frontend/app/components/InstitutionalSidebar.tsx` | **Adicionar glass effects** | Atualmente sem backdrop-blur, migrar para glass consistente |

#### 4. Páginas e Layouts

| Arquivo | Mudança | Detalhes |
|---------|---------|----------|
| `frontend/app/planos/page.tsx` | **Glass cards para "níveis de compromisso"** | Substituir cards sólidos por `<GlassCard variant="pricing" gemAccent="amethyst">` (roxo premium) |
| `frontend/app/pipeline/page.tsx` | **Glass cards consistentes** | Aplicar glass em cards de oportunidades salvas |
| `frontend/app/layout.tsx` | **Viewport meta tag explícita** | Garantir `<meta name="viewport" content="width=device-width, initial-scale=1">` |

#### 5. Uso Estratégico de Pedras Preciosas

| Contexto | Gem | Aplicação |
|----------|-----|-----------|
| **Sucesso / Alta adequação** | Esmeralda (verde) | Cards de oportunidades prioritárias, badges de "recomendado" |
| **Premium / Plano** | Ametista (roxo) | Cards de pricing, features premium |
| **Ação / CTA** | Safira (azul) | Botões primários, links de conversão |
| **Urgência / Prazo** | Rubi (vermelho) | Badges de "prazo encerrando", alertas de trial |

---

## Acceptance Criteria

### Glass Effects Consistentes

- [x] **AC1:** Glass effect (`backdrop-blur`) aplicado consistentemente em: header, cards de resultado, cards de plano, modals, sidebar
- [x] **AC2:** Todos os cards interativos (resultados, planos, pipeline) usam variantes de GlassCard (não implementações custom)
- [x] **AC7:** Cards de resultado de busca usam `<GlassCard variant="result">` (não solid)
- [x] **AC8:** Sidebar institucional (login/signup) tem glass effects aplicados

### Design Tokens e Palette

- [x] **AC3:** Palette "pedras preciosas" definida em `globals.css` com CSS custom properties:
  - `--gem-sapphire`: azul translúcido (opacidade 15-20%)
  - `--gem-emerald`: verde translúcido (opacidade 12-18%)
  - `--gem-amethyst`: roxo translúcido (opacidade 15-20%)
  - `--gem-ruby`: vermelho translúcido (opacidade 15-20%)
- [x] **AC3.1:** Tokens mapeados em `tailwind.config.ts` como classes utilitárias (`bg-gem-sapphire`, `shadow-gem-emerald`, etc.)
- [x] **AC3.2:** Dark mode com opacidades ajustadas para legibilidade (cores mais claras, opacidade maior)

### Headers e Navegação

- [x] **AC4:** Header idêntico em landing e área logada (mesma base, conteúdo diferente)
- [x] **AC5:** Logo size consistente (`text-xl sm:text-2xl` em ambos)
- [x] **AC5.1:** Header landing: transparente → glass on scroll (behavior mantido)
- [x] **AC5.2:** Header área logada: glass consistente (alinhado com landing)

### Responsividade e Mobile

- [x] **AC6:** Viewport meta tag explícita em `layout.tsx`: `width=device-width, initial-scale=1`
- [x] **AC10:** Mobile: sem diferença de zoom/tamanho entre landing e área logada
- [x] **AC10.1:** Glass effects funcionam em viewports 375px, 768px, 1024px (teste em DevTools)

### Dark Mode

- [x] **AC9:** Dark mode consistente em todas as áreas (landing, login, busca, planos, pipeline)
- [x] **AC9.1:** Pedras preciosas legíveis em dark mode (opacidades ajustadas, cores mais claras)
- [x] **AC9.2:** Glass effects visíveis em dark mode (contraste suficiente)

### Qualidade Visual

- [x] **AC11:** Nenhum "salto" visual ao navegar de landing → login → busca (transição suave)
- [x] **AC12:** Hover effects consistentes (scale 1.02, transição 200ms) em todos os cards
- [x] **AC13:** Sombras aplicadas via pedras preciosas (`shadow-gem-*`) em contextos apropriados

### TypeScript e Build

- [x] **AC14:** TypeScript clean (`npx tsc --noEmit --pretty` passa sem erros)
- [x] **AC15:** Build de produção passa sem warnings relacionados ao design system
- [ ] **AC16:** Lighthouse Accessibility score ≥ 90 (contraste de cores adequado)

---

## Definition of Done

- [ ] Todos os Acceptance Criteria marcados como concluídos
- [ ] Glass effects aplicados consistentemente em 100% dos componentes user-facing
- [ ] Palette de pedras preciosas implementada e documentada
- [ ] Headers unificados entre landing e área logada
- [ ] Mobile responsivo testado em 375px, 768px, 1024px
- [ ] Dark mode funcional e legível em todas as páginas
- [ ] TypeScript clean, build passa, lint passa
- [ ] Lighthouse Accessibility ≥ 90
- [ ] PR aberto, revisado e merged
- [ ] Deploy em staging verificado (visual regression test manual)

---

## Technical Notes

### Framer Motion Performance

**Problema atual:** Landing usa Framer Motion pesado, área logada usa animações CSS mínimas.

**Solução:** Manter Framer Motion apenas em landing (impacto de UX justifica o peso). Área logada usa CSS transitions (performance > flair).

### GlassCard Variants

```tsx
// Hierarquia de intensidade de glass:
// default < result < pricing < feature

variant="default"  // backdrop-blur-md, uso geral
variant="result"   // backdrop-blur-lg, destaque médio
variant="pricing"  // backdrop-blur-xl, premium feel
variant="feature"  // backdrop-blur-md + gradient, destaque especial
```

### Exemplo de Uso de Gems

```tsx
// Card de oportunidade prioritária (alta adequação)
<GlassCard variant="result" gemAccent="emerald">
  <Badge className="bg-gem-emerald">Alta Prioridade</Badge>
  {/* conteúdo */}
</GlassCard>

// Card de plano anual (premium)
<GlassCard variant="pricing" gemAccent="amethyst">
  <h3>Anual - Domínio do Mercado</h3>
  {/* conteúdo */}
</GlassCard>

// Badge de prazo encerrando
<Badge className="bg-gem-ruby shadow-gem-ruby">
  Encerra em 2 dias
</Badge>
```

---

## File List

- `frontend/app/globals.css` (adicionar CSS custom properties)
- `frontend/tailwind.config.ts` (adicionar tokens de pedras preciosas)
- `frontend/app/components/ui/GlassCard.tsx` (adicionar variants)
- `frontend/app/components/LicitacaoCard.tsx` (migrar para GlassCard)
- `frontend/app/components/AppHeader.tsx` (unificar com LandingNavbar)
- `frontend/app/buscar/page.tsx` (header alignment)
- `frontend/app/components/InstitutionalSidebar.tsx` (glass effects)
- `frontend/app/planos/page.tsx` (glass cards)
- `frontend/app/pipeline/page.tsx` (glass cards)
- `frontend/app/layout.tsx` (viewport meta tag)

---

*Story created from consolidated GTM backlog 2026-02-15*
