# STORY-168: Redesign Landing Page - Institucional + Conversão

**Epic:** User Experience
**Priority:** High
**Points:** 21
**Status:** In Progress

## User Story

**Como** visitante do SmartLic que ainda não é cliente,
**Quero** entender o valor, credibilidade e diferenciais do sistema ao acessar a página inicial,
**Para que** eu tome a decisão informada de assinar o serviço ou criar conta gratuita.

## Contexto

A página inicial atual (`frontend/app/page.tsx`) é funcional para usuários logados (busca de licitações), mas NÃO comunica valor para visitantes não autenticados. Queremos transformá-la em uma **landing page institucional moderna** que:

1. **Preserve o aspecto institucional** (branding, credibilidade, conformidade PNCP)
2. **Comunique valor de forma otimizada** (economia de tempo, vantagem competitiva, dados confiáveis, praticidade)
3. **Use linguagem técnico-profissional** (dados, métricas, eficiência - público B2B Gov)
4. **Inclua prova social leve** (comparativo antes/depois, estatísticas de impacto)
5. **Seja elegante e moderna** (design system consistente, microinterações, responsividade)

### Problema Atual

- Página inicial mostra interface de busca diretamente (assume usuário logado)
- Nenhuma comunicação de valor antes do login
- Não diferencia visitante novo vs usuário retornando
- Não há CTA claro para assinatura ou trial gratuito

### Solução Proposta

Criar uma **landing page institucional navegável** com seções modulares que transmitem confiança, praticidade e vantagem competitiva. O design deve ser profissional e moderno, evitando linguagem motivacional excessiva.

## Design Aprovado: Estrutura de Seções

```
┌─────────────────────────────────────────────────────────────────┐
│ NAVBAR (sticky)                                [Login] [Cadastro]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ HERO SECTION                                                    │
│ ══════════════════════════════════════════════════════════════  │
│                                                                 │
│   "6+ milhões de licitações por ano no Brasil.                 │
│    Encontre as que realmente importam para sua empresa."       │
│                                                                 │
│   Subheadline: "500 mil oportunidades/mês. Filtros inteligentes│
│                 eliminam o ruído e destacam editais relevantes."│
│                                                                 │
│   [Começar busca gratuita]  [Ver como funciona ↓]              │
│                                                                 │
│   Badge: "Criado por servidores públicos | Dados PNCP +        │
│           múltiplas fontes oficiais"                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION: Custo de Oportunidade                                 │
│ ══════════════════════════════════════════════════════════════  │
│                                                                 │
│   "Qual o custo de uma licitação não disputada por não ter     │
│    sido encontrada?"                                            │
│                                                                 │
│   • 500 mil oportunidades/mês                                   │
│   • Maioria passa despercebida por fornecedores                 │
│   • Cada edital perdido = concorrente que venceu no seu lugar   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION: Comparativo Antes/Depois                              │
│ ══════════════════════════════════════════════════════════════  │
│                                                                 │
│   ┌────────────────────┐  ┌─────────────────────┐              │
│   │ SEM SmartLic       │  │ COM SmartLic        │              │
│   │                    │  │                     │              │
│   │ ❌ 8h/dia buscando  │  │ ✓ 15min/dia focado  │              │
│   │ ❌ Editais perdidos │  │ ✓ Alertas automáticos│              │
│   │ ❌ Busca manual 27  │  │ ✓ Busca unificada   │              │
│   │    portais          │  │   múltiplas fontes  │              │
│   └────────────────────┘  └─────────────────────┘              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION: Diferenciais (4 colunas)                              │
│ ══════════════════════════════════════════════════════════════  │
│                                                                 │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│   │ Economia │ │ Vantagem │ │  Dados   │ │Praticidad│         │
│   │  Tempo   │ │Competitiva│ │Confiáveis│ │    e     │         │
│   │          │ │          │ │          │ │          │         │
│   │ Filtros  │ │ Alertas  │ │ PNCP +   │ │ Relatório│         │
│   │IA +      │ │ em tempo │ │ múltiplas│ │ Excel    │         │
│   │ resumos  │ │ real     │ │ fontes   │ │ 1-click  │         │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION: Como Funciona (3 passos)                              │
│ ══════════════════════════════════════════════════════════════  │
│                                                                 │
│   1 → Configure      2 → Receba         3 → Participe          │
│       filtros            alertas             e vença           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION: Estatísticas de Impacto                               │
│ ══════════════════════════════════════════════════════════════  │
│                                                                 │
│   ┌─────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐        │
│   │ 6M+     │ │ 500k     │ │ 12 setores │ │ Criado   │        │
│   │licit/ano│ │ oport/mês│ │ +expansão  │ │por servid│        │
│   │         │ │          │ │            │ │públicos  │        │
│   └─────────┘ └──────────┘ └────────────┘ └──────────┘        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION: Fontes de Dados (credibilidade)                       │
│ ══════════════════════════════════════════════════════════════  │
│                                                                 │
│   Principal: PNCP (Portal Nacional de Contratações Públicas)   │
│   + Complementares: BLL, Portal Compras Públicas, BNC, etc.    │
│                                                                 │
│   [Logos ou badges das fontes]                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION: Setores Atendidos (12 cards)                          │
│ ══════════════════════════════════════════════════════════════  │
│                                                                 │
│   Uniformes | Facilities | Software | [+9 setores]             │
│   Badge: "Em constante expansão"                               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SECTION: CTA Final                                             │
│ ══════════════════════════════════════════════════════════════  │
│                                                                 │
│   "Pronto para economizar tempo e encontrar mais oportunidades?"│
│                                                                 │
│   [Começar agora - 3 buscas gratuitas]                         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ FOOTER (institucional)                                          │
│   Links: Sobre | Planos | Suporte | LGPD                       │
└─────────────────────────────────────────────────────────────────┘
```

## Acceptance Criteria

### AC1: Hero Section - Comunicação de Valor

- [x] **Headline principal:** "6+ milhões de licitações por ano no Brasil. Encontre as que realmente importam para sua empresa."
- [x] **Subheadline:** "500 mil oportunidades mensais. Filtros inteligentes eliminam o ruído e destacam editais relevantes para o seu setor."
- [x] **CTAs principais:**
  - [x] Primário: "Começar busca gratuita" (leva para signup)
  - [x] Secundário: "Ver como funciona" (scroll suave para seção "Como Funciona")
- [x] **Badge de credibilidade:** "Criado por servidores públicos | Dados PNCP + múltiplas fontes oficiais"
- [x] Background: gradient sutil, não chamativo

### AC2: Seção Custo de Oportunidade

- [x] **Headline provocativa:** "Qual o custo de uma licitação não disputada por não ter sido encontrada?"
- [x] **3 pontos-chave em destaque:**
  - 500 mil oportunidades mensais publicadas no Brasil
  - A maioria passa despercebida por fornecedores qualificados
  - Cada edital perdido = concorrente que venceu no seu lugar
- [x] **Visual:** Caixa destacada (background levemente diferenciado) com ícone de alerta/aviso
- [x] **Tom:** Consultivo e baseado em fatos, não alarmista

### AC3: Seção Comparativo Antes/Depois

- [x] Layout **2 colunas** (desktop) / empilhado (mobile)
- [x] Coluna esquerda: "Sem SmartLic"
  - ❌ 8 horas/dia buscando manualmente em 27 portais diferentes
  - ❌ Editais importantes perdidos por sobrecarga de informação
  - ❌ Busca fragmentada, sem histórico unificado
- [x] Coluna direita: "Com SmartLic"
  - ✅ 15 minutos/dia com buscas automáticas e filtros inteligentes
  - ✅ Alertas em tempo real para oportunidades relevantes
  - ✅ Busca unificada em múltiplas fontes com histórico completo
- [x] Visual: cartões com contraste (background claro vs escuro) e ícones

### AC4: Seção Diferenciais (4 pilares)

- [x] **4 cartões em grid responsivo** (2x2 em tablet, 1 coluna em mobile):
  1. **Economia de Tempo**
     - Ícone: relógio
     - Texto: "Filtros inteligentes + resumos IA eliminam ruído"
  2. **Vantagem Competitiva**
     - Ícone: alvo/target
     - Texto: "Alertas em tempo real para agir antes da concorrência"
  3. **Dados Confiáveis**
     - Ícone: shield/check
     - Texto: "Múltiplas fontes oficiais, atualização diária"
  4. **Praticidade**
     - Ícone: download
     - Texto: "Relatórios Excel prontos + histórico completo"
- [x] Cada cartão: hover sutil, sem animações excessivas

### AC5: Seção Como Funciona (3 passos)

- [x] **3 cartões numerados** (1, 2, 3):
  1. Configure filtros (estado, setor, valor, palavras-chave)
  2. Receba alertas automáticos e relatórios
  3. Participe das licitações com vantagem competitiva
- [x] Ilustração minimalista ou ícone para cada passo
- [x] Setas de progressão (→) entre os passos (desktop)

### AC6: Seção Estatísticas de Impacto

- [x] **4 métricas em grid:**
  - **6M+ licitações/ano** - Volume total no Brasil
  - **500k oportunidades/mês** - Fluxo mensal
  - **12 setores + em expansão** - Abrangência crescente
  - **Criado por servidores públicos** - Expertise insider
- [x] Números grandes, labels menores
- [x] Background: subtle background color diferenciado
- [x] Destacar "Criado por servidores públicos" como diferencial de credibilidade

### AC7: Seção Fontes de Dados (Credibilidade)

- [x] **Texto principal:** "Desenvolvido por quem conhece a máquina pública por dentro"
- [x] **Destaque:** "Criado por servidores públicos com experiência em licitações"
- [x] **Fonte primária destacada:** PNCP (Portal Nacional de Contratações Públicas)
- [x] **Fontes complementares:** BLL, Portal Compras Públicas, BNC, Licitar Digital, etc. (logos ou badges)
- [x] Link para PNCP (pncp.gov.br) abrindo em nova aba

### AC8: Seção Setores Atendidos

- [x] **12 setores** em grid 4x3 (desktop) / 2 colunas (mobile):
  - Uniformes e Vestuário
  - Facilities Management
  - Software e TI
  - Alimentação
  - Equipamentos
  - Transporte
  - Medicamentos
  - Limpeza
  - Segurança
  - Materiais de Escritório
  - Construção Civil
  - Serviços Gerais
- [x] **Badge:** "Em constante expansão - novos setores adicionados regularmente"
- [x] Cada setor: ícone + nome
- [x] Hover: leve destaque (sem navegação - apenas visual)

### AC9: CTA Final

- [x] **Headline:** "Pronto para economizar tempo e encontrar mais oportunidades?"
- [x] **Botão primário:** "Começar agora - 3 buscas gratuitas" (leva para signup)
- [x] **Texto secundário:** "Sem necessidade de cartão de crédito"
- [x] Background: destaque visual (ex: gradient ou cor de brand)

### AC10: Navbar e Footer

- [x] **Navbar:**
  - Logo SmartLic (esquerda)
  - Links: Planos, Como Funciona (scroll interno), Suporte
  - Botões: Login (outline), Cadastro (primário)
  - Sticky no scroll (desktop)
- [x] **Footer:**
  - Links: Sobre, Planos e Preços, Suporte, Política de Privacidade, Termos de Uso
  - Selo LGPD Compliant
  - Destaque sutil: "Desenvolvido por servidores públicos"
  - Copyright SmartLic 2026

### AC11: Responsividade

- [x] Breakpoints: mobile (<640px), tablet (640-1024px), desktop (>1024px)
- [x] Hero: headline reduzida em mobile (font-size menor)
- [x] Grid de diferenciais: 1 coluna (mobile), 2 colunas (tablet), 4 colunas (desktop)
- [x] Grid de setores: 2 colunas (mobile), 4 colunas (desktop)
- [x] CTA buttons: full-width em mobile, tamanho fixo em desktop

### AC12: Performance e Acessibilidade

- [ ] **Performance:**
  - Lazy load de imagens/ícones
  - Target Lighthouse score: >90 (Performance, Accessibility, Best Practices, SEO)
- [ ] **Acessibilidade:**
  - Contraste adequado (WCAG AA)
  - Links com `aria-label` descritivos
  - Navegação por teclado funcional
  - Semântica HTML correta (`<section>`, `<header>`, `<nav>`, `<footer>`)

### AC13: Testes

- [x] Teste unitário: componentes de seções (Hero, Comparativo, Diferenciais, etc.)
- [x] Teste E2E: fluxo navegação na landing page
- [x] Teste E2E: scroll suave para "Como Funciona"
- [x] Teste E2E: navegação para Login e Signup
- [x] Teste de responsividade (viewport mobile, tablet, desktop)

## Technical Details

### Estrutura de Arquivos

```
frontend/app/
├── (landing)/
│   ├── page.tsx                    # Landing page principal
│   ├── components/
│   │   ├── HeroSection.tsx
│   │   ├── OpportunityCost.tsx     # Nova seção - custo de oportunidade
│   │   ├── BeforeAfter.tsx
│   │   ├── DifferentialsGrid.tsx
│   │   ├── HowItWorks.tsx
│   │   ├── StatsSection.tsx
│   │   ├── DataSourcesSection.tsx
│   │   ├── SectorsGrid.tsx
│   │   ├── FinalCTA.tsx
│   │   └── LandingNavbar.tsx
│   └── layout.tsx                  # Layout específico landing
├── (dashboard)/
│   └── page.tsx                    # Interface de busca (usuário logado)
```

### Props e Tipos

```typescript
interface SectionProps {
  className?: string;
}

interface DifferentialCard {
  icon: React.ReactNode;
  title: string;
  description: string;
}

interface StatCard {
  value: string;
  label: string;
}

interface SectorCard {
  icon: React.ReactNode;
  name: string;
}
```

### Copy Guidelines (Técnico-Profissional)

**Tom de voz:**
- Objetivo, baseado em dados e métricas reais
- Evitar superlativos exagerados ("revolucionário", "incrível")
- Focar em eficiência, custo de oportunidade, expertise
- Usar números concretos (6M+ licitações/ano, 500k/mês, 12 setores)
- Destacar autoridade: criado por servidores públicos

**Gatilhos profissionais a enfatizar:**
1. **Custo de oportunidade:** Licitações perdidas = concorrentes vencendo
2. **Expertise insider:** Criado por quem conhece a máquina pública por dentro
3. **Volume e escala:** 6+ milhões/ano, 500k oportunidades/mês
4. **Eficiência:** Filtrar 500k oportunidades mensais em minutos

**Evitar:**
- ❌ "A melhor ferramenta do mercado!"
- ❌ "Revolucione sua empresa!"
- ❌ "Não perca essa oportunidade incrível!"

**Preferir:**
- ✅ "6+ milhões de licitações/ano. Encontre as que importam."
- ✅ "500 mil oportunidades mensais. Filtros inteligentes eliminam o ruído."
- ✅ "Criado por servidores públicos. Conhecemos a máquina por dentro."
- ✅ "Qual o custo de uma licitação não disputada por não ter sido encontrada?"

## Out of Scope

- Vídeo explicativo (pode ser adicionado futuramente)
- Carrossel de depoimentos (não há depoimentos ainda)
- A/B testing de variações de copy
- Chat ao vivo / suporte inline
- Calculadora de ROI
- Integração com analytics de scroll/heatmap (pode ser adicionado depois)

## Dependencies

- Nenhuma nova dependência de pacotes
- Usa apenas Tailwind CSS existente
- Ícones SVG inline (sem bibliotecas externas)

## Definition of Done

- [ ] Todos os componentes de seções criados e testados
- [ ] Landing page (`(landing)/page.tsx`) implementada
- [ ] Responsividade testada (mobile, tablet, desktop)
- [ ] Navegação para Login e Signup funcionando
- [ ] Scroll suave para "Como Funciona" funcionando
- [ ] Testes unitários passando (cobertura >60%)
- [ ] Testes E2E criados e passando
- [ ] TypeScript type check passou
- [ ] Production build bem-sucedido
- [ ] Lighthouse score >90 (Performance, Accessibility, Best Practices, SEO)
- [ ] Code review aprovado
- [ ] Deploy em staging para validação visual
- [ ] Validação com stakeholder/PO

## File List

_Arquivos a serem criados/modificados:_

- [x] `frontend/app/(landing)/page.tsx` (novo)
- [x] `frontend/app/(landing)/layout.tsx` (novo)
- [x] `frontend/app/(landing)/components/HeroSection.tsx` (novo)
- [x] `frontend/app/(landing)/components/OpportunityCost.tsx` (novo)
- [x] `frontend/app/(landing)/components/BeforeAfter.tsx` (novo)
- [x] `frontend/app/(landing)/components/DifferentialsGrid.tsx` (novo)
- [x] `frontend/app/(landing)/components/HowItWorks.tsx` (novo)
- [x] `frontend/app/(landing)/components/StatsSection.tsx` (novo)
- [x] `frontend/app/(landing)/components/DataSourcesSection.tsx` (novo)
- [x] `frontend/app/(landing)/components/SectorsGrid.tsx` (novo)
- [x] `frontend/app/(landing)/components/FinalCTA.tsx` (novo)
- [x] `frontend/app/(landing)/components/LandingNavbar.tsx` (novo)
- [x] `frontend/__tests__/landing/HeroSection.test.tsx` (novo)
- [x] `frontend/__tests__/landing/OpportunityCost.test.tsx` (novo)
- [x] `frontend/__tests__/landing/BeforeAfter.test.tsx` (novo)
- [x] `frontend/__tests__/landing/DifferentialsGrid.test.tsx` (novo)
- [x] `frontend/__tests__/landing/StatsSection.test.tsx` (novo)
- [x] `frontend/e2e-tests/landing-page.spec.ts` (novo)

## Mockup Reference

Padrão visual inspirado em:
- **Stripe** (landing page profissional B2B)
- **Linear** (design system limpo, gradientes sutis)
- **Notion** (seções modulares, navegação fluida)
- **Vercel** (minimalismo, foco em conteúdo)

## Copy Sugerido (Draft - Atualizado)

### Hero Section

**Headline:** "6+ milhões de licitações por ano no Brasil. Encontre as que realmente importam para sua empresa."

**Subheadline:** "500 mil oportunidades mensais. Filtros inteligentes eliminam o ruído e destacam editais relevantes para o seu setor."

**Badge:** "Criado por servidores públicos | Dados PNCP + múltiplas fontes oficiais"

### Custo de Oportunidade

**Headline:** "Qual o custo de uma licitação não disputada por não ter sido encontrada?"

**3 Pontos-chave:**
- 500 mil oportunidades publicadas mensalmente no Brasil
- A maioria passa despercebida por fornecedores qualificados
- Cada edital perdido = concorrente que venceu no seu lugar

### Diferenciais

1. **Economia de Tempo**
   - Filtros inteligentes processam 500k oportunidades mensais. Resumos IA destacam editais relevantes em minutos, não dias.

2. **Vantagem Competitiva**
   - Alertas em tempo real para agir antes da concorrência. Histórico completo para análise estratégica de padrões.

3. **Dados Confiáveis**
   - Múltiplas fontes oficiais (PNCP + complementares). Criado por quem conhece a máquina pública por dentro.

4. **Praticidade**
   - Relatórios Excel prontos para download. Zero configuração técnica. 12 setores atendidos e em expansão.

### Comparativo

**Sem SmartLic:**
- 8 horas/dia buscando manualmente em dezenas de portais diferentes
- Editais importantes perdidos por sobrecarga de informação (500k/mês é humanamente impossível de processar)
- Busca fragmentada, sem histórico unificado ou análise de padrões

**Com SmartLic:**
- 15 minutos/dia com buscas automáticas e filtros inteligentes (criados por quem entende licitações)
- Alertas em tempo real para oportunidades relevantes ao seu setor
- Busca unificada em múltiplas fontes com histórico completo e rastreamento

### Estatísticas de Impacto

**4 métricas:**
1. **6M+ licitações/ano** - Volume total publicado no Brasil
2. **500k oportunidades/mês** - Fluxo mensal processado automaticamente
3. **12 setores + em expansão** - Abrangência crescente (uniformes, facilities, software, alimentação, equipamentos, transporte, medicamentos, limpeza, segurança, escritório, construção, serviços gerais)
4. **Criado por servidores públicos** - Expertise insider: conhecemos a máquina por dentro

### Fontes de Dados (Credibilidade)

**Headline:** "Desenvolvido por quem conhece a máquina pública por dentro"

**Texto principal:** Sistema criado por servidores públicos com anos de experiência em processos licitatórios. Sabemos quais dados importam e onde encontrá-los.

**Fontes oficiais integradas:**
- PNCP (Portal Nacional de Contratações Públicas) - fonte primária
- BLL (Bolsa de Licitações e Leilões)
- Portal Compras Públicas
- BNC (Banco Nacional de Compras)
- Licitar Digital
- E outras fontes estaduais/municipais em constante expansão

---

**Created by:** @pm (Morgan)
**Design approved by:** Product Owner
**Date:** 2026-02-07
