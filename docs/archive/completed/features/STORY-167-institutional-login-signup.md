# STORY-167: Redesign Institucional das Páginas de Login e Signup

**Epic:** User Experience
**Priority:** High
**Points:** 13
**Status:** Ready for Development

## User Story

**Como** visitante do SmartLic,
**Quero** ver as vantagens e credibilidade do sistema ao acessar as páginas de login e cadastro,
**Para que** eu entenda o valor da plataforma antes mesmo de criar minha conta.

## Contexto

As páginas de login e signup atuais são funcionais, porém "peladas" - apenas um card de formulário
centralizado em um fundo vazio. O usuário não recebe nenhuma informação institucional sobre
as vantagens do sistema, fontes de dados ou credibilidade da plataforma.

### Problema Atual
- Login: Card simples com "Entre para acessar suas buscas"
- Signup: Card simples com "Comece com 3 buscas gratuitas"
- Nenhuma comunicação de valor antes do usuário entrar
- Experiência genérica, não diferenciada

### Solução Proposta
Transformar as páginas de entrada em uma **experiência institucional envolvente** usando o
padrão **Split Screen (50/50)**, comunicando valor, credibilidade e profissionalismo.

## Design Aprovado: Split Screen Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌────────────────────────────┐  ┌────────────────────────────────┐ │
│  │                            │  │                                │ │
│  │   PAINEL INSTITUCIONAL     │  │   FORMULÁRIO                   │ │
│  │   (50% da largura)         │  │   (50% da largura)             │ │
│  │                            │  │                                │ │
│  │   • Headline impactante    │  │   [Card de Login/Signup        │ │
│  │   • 4-5 benefícios         │  │    existente - preservado]     │ │
│  │   • Estatísticas           │  │                                │ │
│  │   • Badge PNCP oficial     │  │                                │ │
│  │   • Selo LGPD              │  │                                │ │
│  │                            │  │                                │ │
│  │   Background: gradient     │  │   Background: canvas           │ │
│  │   navy → blue              │  │                                │ │
│  │                            │  │                                │ │
│  └────────────────────────────┘  └────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Responsividade (Mobile < 768px)
- Layout em coluna única (stacked)
- Painel institucional compacto acima do formulário
- Benefícios em formato resumido (3 itens principais)

## Acceptance Criteria

### AC1: Componente InstitutionalSidebar

- [ ] Criar componente reutilizável `InstitutionalSidebar.tsx`
- [ ] Props para customizar headline e contexto (login vs signup)
- [ ] Background gradient: `from-[var(--brand-navy)] to-[var(--brand-blue)]`
- [ ] Texto em branco com boa legibilidade
- [ ] Responsivo: coluna em desktop, compacto em mobile

### AC2: Conteúdo do Painel - Página de Login

- [ ] **Headline:** "Descubra oportunidades de licitação antes da concorrência"
- [ ] **Subheadline:** "Acesse seu painel e encontre as melhores oportunidades para sua empresa"
- [ ] **Benefícios (5 itens com ícones):**
  1. Monitoramento em tempo real do PNCP
  2. Filtros por estado, valor e setor
  3. Resumo executivo gerado por IA
  4. Exportação de relatórios em Excel
  5. Histórico completo de buscas
- [ ] **Estatísticas:**
  - "27 estados monitorados"
  - "9 setores pré-configurados"
  - "Atualização diária"
- [ ] **Badge de credibilidade:** "Dados oficiais do PNCP - Portal Nacional de Contratações Públicas"

### AC3: Conteúdo do Painel - Página de Signup

- [ ] **Headline:** "Sua empresa a um passo das melhores oportunidades públicas"
- [ ] **Subheadline:** "Crie sua conta e comece a encontrar licitações compatíveis com seu negócio"
- [ ] **Benefícios (5 itens com ícones):**
  1. Comece grátis com 3 buscas completas
  2. Sem necessidade de cartão de crédito
  3. Configuração em menos de 2 minutos
  4. Suporte dedicado via WhatsApp
  5. Dados protegidos e conformidade LGPD
- [ ] **Estatísticas:**
  - "Empresas de 27 estados já usam"
  - "Milhares de licitações encontradas"
  - "100% fonte oficial"
- [ ] **Selos de confiança:**
  - "PNCP - Fonte oficial do Governo Federal"
  - "LGPD Compliant"

### AC4: Layout Split Screen - Desktop

- [ ] Container `min-h-screen` com `flex`
- [ ] Painel esquerdo: `w-1/2` com padding generoso
- [ ] Painel direito: `w-1/2` com card centralizado
- [ ] Formulários existentes preservados sem alterações funcionais
- [ ] Transição suave entre páginas (consistência visual)

### AC5: Layout Responsivo - Mobile/Tablet

- [ ] Breakpoint: `md:` (768px)
- [ ] Mobile: layout em coluna (`flex-col`)
- [ ] Painel institucional compacto no topo (max 40% da altura)
- [ ] Formulário abaixo com scroll se necessário
- [ ] Reduzir benefícios para 3 itens principais em mobile
- [ ] Esconder estatísticas em telas muito pequenas (`sm:hidden`)

### AC6: Ícones e Visual

- [ ] Ícones SVG inline para cada benefício (não dependências externas)
- [ ] Ícones sugeridos:
  - Monitoramento: relógio/refresh
  - Filtros: funil
  - IA: cérebro/chip
  - Excel: tabela/download
  - Histórico: arquivo/clock
  - Grátis: presente/gift
  - Segurança: escudo/lock
  - Suporte: headset/chat
- [ ] Estilo: stroke icons, cor branca, 24x24px

### AC7: Badge PNCP Oficial

- [ ] Destaque visual diferenciado (borda, background sutil)
- [ ] Ícone de verificado/check
- [ ] Texto: "Dados extraídos diretamente da API oficial do PNCP"
- [ ] Link para pncp.gov.br (abre em nova aba, rel="noopener")

### AC8: Animações Sutis (Opcional - Nice to Have)

- [ ] Fade-in dos elementos ao carregar
- [ ] Hover sutil nos benefícios
- [ ] Sem animações que afetem performance ou acessibilidade

### AC9: Testes

- [ ] Teste unitário do componente InstitutionalSidebar
- [ ] Teste de renderização condicional (login vs signup)
- [ ] Teste de responsividade (mock de viewport)
- [ ] Teste E2E: fluxo login com painel visível
- [ ] Teste E2E: fluxo signup com painel visível
- [ ] Verificar que formulários existentes continuam funcionando

### AC10: Acessibilidade

- [ ] Contraste adequado (texto branco sobre gradient escuro)
- [ ] Links externos com `aria-label` descritivo
- [ ] Ordem de leitura lógica (painel → formulário)
- [ ] Não interferir na navegação por teclado do formulário

## Technical Details

### Estrutura de Arquivos

```
frontend/app/
├── components/
│   └── InstitutionalSidebar.tsx    # Novo componente
├── login/
│   └── page.tsx                     # Modificado (adicionar sidebar)
└── signup/
    └── page.tsx                     # Modificado (adicionar sidebar)
```

### Props do Componente

```typescript
interface InstitutionalSidebarProps {
  variant: 'login' | 'signup';
  className?: string;
}
```

### Conteúdo Estruturado

```typescript
const SIDEBAR_CONTENT = {
  login: {
    headline: "Descubra oportunidades de licitação antes da concorrência",
    subheadline: "Acesse seu painel e encontre as melhores oportunidades para sua empresa",
    benefits: [
      { icon: "clock", text: "Monitoramento em tempo real do PNCP" },
      { icon: "filter", text: "Filtros por estado, valor e setor" },
      { icon: "brain", text: "Resumo executivo gerado por IA" },
      { icon: "download", text: "Exportação de relatórios em Excel" },
      { icon: "history", text: "Histórico completo de buscas" },
    ],
    stats: [
      { value: "27", label: "estados monitorados" },
      { value: "9", label: "setores pré-configurados" },
      { value: "24h", label: "atualização diária" },
    ],
  },
  signup: {
    headline: "Sua empresa a um passo das melhores oportunidades públicas",
    subheadline: "Crie sua conta e comece a encontrar licitações compatíveis com seu negócio",
    benefits: [
      { icon: "gift", text: "Comece grátis com 3 buscas completas" },
      { icon: "card-off", text: "Sem necessidade de cartão de crédito" },
      { icon: "zap", text: "Configuração em menos de 2 minutos" },
      { icon: "headset", text: "Suporte dedicado via WhatsApp" },
      { icon: "shield", text: "Dados protegidos e conformidade LGPD" },
    ],
    stats: [
      { value: "27", label: "estados cobertos" },
      { value: "1000+", label: "licitações/dia" },
      { value: "100%", label: "fonte oficial" },
    ],
  },
};
```

### CSS/Tailwind Classes Principais

```css
/* Gradient background */
.institutional-bg {
  @apply bg-gradient-to-br from-[var(--brand-navy)] to-[var(--brand-blue)];
}

/* Badge PNCP */
.pncp-badge {
  @apply flex items-center gap-2 px-4 py-3
         bg-white/10 backdrop-blur-sm rounded-lg
         border border-white/20;
}

/* Stat card */
.stat-card {
  @apply text-center px-4 py-3 bg-white/5 rounded-lg;
}
```

## Wireframe Visual

### Desktop (1440px)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────┐ ┌──────────────────────────────────┐ │
│ │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ │                                  │ │
│ │  ░  HEADLINE IMPACTANTE      ░  │ │    ┌────────────────────────┐    │ │
│ │  ░  Subheadline menor        ░  │ │    │                        │    │ │
│ │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ │    │     SmartLic         │    │ │
│ │                                 │ │    │                        │    │ │
│ │  ✓ Benefício 1                  │ │    │  [Google OAuth]        │    │ │
│ │  ✓ Benefício 2                  │ │    │  ────── OU ──────      │    │ │
│ │  ✓ Benefício 3                  │ │    │  [Email + Senha]       │    │ │
│ │  ✓ Benefício 4                  │ │    │  [Magic Link]          │    │ │
│ │  ✓ Benefício 5                  │ │    │                        │    │ │
│ │                                 │ │    │  [     Entrar    ]     │    │ │
│ │  ┌─────┐ ┌─────┐ ┌─────┐        │ │    │                        │    │ │
│ │  │ 27  │ │  9  │ │ 24h │        │ │    │  Não tem conta?        │    │ │
│ │  │est. │ │set. │ │atua.│        │ │    │  Criar conta →         │    │ │
│ │  └─────┘ └─────┘ └─────┘        │ │    └────────────────────────┘    │ │
│ │                                 │ │                                  │ │
│ │  ┌─────────────────────────┐    │ │                                  │ │
│ │  │ ✓ Dados oficiais PNCP   │    │ │                                  │ │
│ │  └─────────────────────────┘    │ │                                  │ │
│ └─────────────────────────────────┘ └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

### Mobile (375px)

```
┌─────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░  HEADLINE           ░ │
│ ░  Subheadline        ░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░ │
│                         │
│ ✓ Benefício 1           │
│ ✓ Benefício 2           │
│ ✓ Benefício 3           │
│                         │
│ [✓ Dados oficiais PNCP] │
├─────────────────────────┤
│                         │
│  ┌───────────────────┐  │
│  │   SmartLic      │  │
│  │                   │  │
│  │ [Google OAuth]    │  │
│  │ ───── OU ─────    │  │
│  │ [Email]           │  │
│  │ [Senha]           │  │
│  │                   │  │
│  │ [   Entrar   ]    │  │
│  │                   │  │
│  │ Criar conta →     │  │
│  └───────────────────┘  │
│                         │
└─────────────────────────┘
```

## Out of Scope

- Vídeo ou animações complexas no painel
- Carrossel de depoimentos/testimonials
- Integração com analytics de scroll/engagement
- A/B testing de variações de copy
- Tradução para outros idiomas
- Alterações funcionais nos formulários de login/signup

## Dependencies

- Nenhuma nova dependência de pacotes
- Usa apenas Tailwind CSS existente
- Ícones SVG inline (sem bibliotecas)

## Definition of Done

- [x] Componente InstitutionalSidebar criado e testado
- [x] Página de login atualizada com split screen
- [x] Página de signup atualizada com split screen
- [x] **Rebrand completo:** Todas referências "Smart PNCP" → "SmartLic" (verificado e corrigido)
- [x] Responsividade testada (desktop, tablet, mobile)
- [x] Formulários existentes funcionando sem regressão
- [x] Testes unitários passando (26/26 passing)
- [x] Testes E2E criados (30 scenarios)
- [x] TypeScript type check passed
- [x] Production build successful
- [ ] Code review aprovado (awaiting PR review)
- [ ] Deploy em staging para validação visual (pending push)

## File List

_Arquivos modificados/criados:_

- [x] `frontend/app/components/InstitutionalSidebar.tsx` (novo - 235 linhas)
- [x] `frontend/app/login/page.tsx` (modificado - split-screen integration)
- [x] `frontend/app/signup/page.tsx` (modificado - split-screen integration)
- [x] `frontend/__tests__/components/InstitutionalSidebar.test.tsx` (novo - 26 tests)
- [x] `frontend/e2e-tests/institutional-pages.spec.ts` (novo - 30 scenarios)
- [x] `docs/stories/STORY-167-design-spec.md` (novo - design guidelines)
- [x] `docs/stories/STORY-167-architecture-spec.md` (novo - architecture decisions)

## Mockup Reference

Padrão visual inspirado em:
- Stripe Login (split screen com branding)
- Linear Login (gradient + benefícios)
- Vercel Login (minimalista + profissional)

---

**Created by:** @pm (Morgan)
**Design approved by:** Product Owner
**Date:** 2026-02-07
