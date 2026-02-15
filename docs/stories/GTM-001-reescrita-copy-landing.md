# GTM-001: Reescrita Completa da Copy — Landing Page

## Metadata
| Field | Value |
|-------|-------|
| **ID** | GTM-001 |
| **Priority** | P0 (GTM-blocker) |
| **Sprint** | Sprint 1 |
| **Estimate** | 12h |
| **Depends on** | GTM-007 (PNCP sanitization) |
| **Blocks** | GTM-005, GTM-006, GTM-008 |
| **Absorbs** | STORY-173 (Brand Positioning), STORY-244 (Strategic Copy) |

## Filosofia

> **"Não vendemos busca. Vendemos inteligência de decisão."**

> **"Não vendemos velocidade. Vendemos vantagem competitiva."**

A landing page atual comunica "ferramenta que economiza tempo" — commodity. Headlines como "Encontre em 3 Minutos", "160x Mais Rápido", "95% de Precisão" colocam SmartLic na mesma prateleira de qualquer buscador automatizado. O mercado de licitação compra vantagem competitiva, não velocidade.

**Princípios Guia:**
1. IA não gera resumos. IA avalia oportunidades e orienta decisões.
2. PNCP nunca é mencionado. Consultamos "dezenas de fontes oficiais em tempo real".
3. Não existem "planos de assinatura". Existem "níveis de compromisso em se destacar no mercado".
4. O custo de não usar o SmartLic é tangível: perder contratos por falta de visibilidade.

## Problema

A landing page comunica "ferramenta que economiza tempo" — commodity. Headlines como "Encontre em 3 Minutos", "160x Mais Rápido", "95% de Precisão" colocam SmartLic na mesma prateleira de qualquer buscador automatizado. O mercado de licitação compra vantagem competitiva, não velocidade.

### Evidência Atual

| Seção | Copy Atual | Problema |
|-------|-----------|----------|
| Hero | "Encontre em 3 Minutos" | Foca em velocidade, não decisão |
| BeforeAfter | "8h manual vs 3min automático" | Compara tempo, não resultado financeiro |
| DifferentialsGrid | "95% precisão, 160x mais rápido" | Features técnicas, não valor |
| OpportunityCost | "Você perde 8 horas por semana" | Custo de horas, não de oportunidades perdidas |
| DataSourcesSection | "PNCP + 27 portais estaduais" | Expõe fonte gratuita |
| Testimonials | João Silva, Maria Santos, Carlos Oliveira | Fictícios, zero credibilidade |

## Solução: Reescrita Completa com Foco em Resultado

### Arquivos Afetados

| Componente | Arquivo | Status Atual → Desejado |
|-----------|---------|------------------------|
| **HeroSection** | `frontend/app/components/landing/HeroSection.tsx` | "Encontre em 3 Minutos" → Inteligência de decisão |
| **BeforeAfter** | `frontend/app/components/landing/BeforeAfter.tsx` | Comparação tempo → Comparação resultado financeiro |
| **DifferentialsGrid** | `frontend/app/components/landing/DifferentialsGrid.tsx` | Features técnicas → Diferenciais de valor |
| **HowItWorks** | `frontend/app/components/landing/HowItWorks.tsx` | Mecânico → Orientado ao resultado |
| **OpportunityCost** | `frontend/app/components/landing/OpportunityCost.tsx` | Custo de horas → Custo de oportunidades perdidas |
| **FinalCTA** | `frontend/app/components/landing/FinalCTA.tsx` | "Economize tempo" → "Comece a ganhar" |
| **StatsSection** | `frontend/app/components/landing/StatsSection.tsx` | Métricas genéricas → Impacto em resultado |
| **DataSourcesSection** | `frontend/app/components/landing/DataSourcesSection.tsx` | Cita PNCP → "fontes oficiais" genérico |
| **valueProps.ts** | `frontend/lib/copy/valueProps.ts` | Reescrita completa (~437 linhas) |
| **comparisons.ts** | `frontend/lib/copy/comparisons.ts` | Reescrita completa (~217 linhas) |

### Nova Narrativa — Copy Guide

#### Hero Section
- **Headline atual:** "Encontre Licitações em 3 Minutos"
- **Headline nova:** "Saiba Onde Investir para Ganhar Mais Licitações"
- **Sub-headline atual:** "IA analisa milhares de editais e retorna apenas oportunidades relevantes"
- **Sub-headline nova:** "Inteligência que avalia oportunidades, prioriza o que importa e orienta suas decisões"
- **CTA atual:** "Comece grátis"
- **CTA nova:** "Descobrir Minhas Oportunidades"

#### BeforeAfter Section
- **Atual:** Cenário manual (8h/semana) vs automático (3min)
- **Nova:** Cenário sem SmartLic vs com SmartLic

**Sem SmartLic:**
- Perde oportunidades por não saber que existem
- Entra em licitações ruins (baixa chance de ganhar)
- Concorrente já se posicionou enquanto você ainda procura
- Custo: oportunidades perdidas = R$ em contratos não ganhos

**Com SmartLic:**
- Vê todas as oportunidades do seu mercado em tempo real
- Sabe quais merecem atenção (análise de adequação)
- Se posiciona antes da concorrência
- Resultado: mais licitações ganhas

#### DifferentialsGrid
**Focos novos:**
1. **Priorização Inteligente** — "Saiba onde focar. O sistema avalia cada oportunidade e indica o que merece sua atenção."
2. **Análise Automatizada** — "Não precisa ler editais para decidir. A IA avalia requisitos, prazos e competitividade."
3. **Redução de Incerteza** — "Entre preparado. Decisões baseadas em critérios objetivos, não em intuição."
4. **Cobertura Nacional** — "Nunca perca uma oportunidade por não saber que ela existe. Consulta em todas as fontes, todos os dias."

#### HowItWorks
**Atual (mecânico):**
1. Selecione setor
2. Configure filtros
3. Receba resultados

**Novo (orientado ao resultado):**
1. Diga o que vende
2. Receba oportunidades priorizadas
3. Decida com confiança

#### OpportunityCost
**Atual:** "Você perde 8 horas por semana procurando manualmente"
**Novo:** "Enquanto você procura, seu concorrente já está se posicionando. Cada dia sem visibilidade completa é uma oportunidade que pode ir para outro."

**Mensagem âncora:** "Uma única licitação perdida por falta de visibilidade pode custar R$ 50.000, R$ 200.000 ou mais. O custo de não usar SmartLic não é tempo — é dinheiro."

## Acceptance Criteria

### Copy Estratégica

- [ ] **AC1: Hero headline comunica DECISÃO, não velocidade**
  - Headline: "Saiba onde investir para ganhar mais licitações" (ou similar focado em decisão)
  - Zero menções a "3 minutos", "rápido", "velocidade"
  - **Critério de validação:** Grep de "minuto", "rápido", "veloci" no HeroSection.tsx retorna zero

- [ ] **AC2: Sub-headline posiciona IA como analista de oportunidades (não gerador de resumos)**
  - IA descrita como: "avalia oportunidades", "prioriza", "orienta decisões"
  - Zero menções a "resume", "resumo executivo", "sintetiza"
  - **Critério de validação:** Sub-headline contém palavras-chave de decisão, não de síntese

- [ ] **AC3: CTA principal usa verbo de resultado**
  - CTA: "Descobrir minhas oportunidades" ou "Ver oportunidades prioritárias"
  - Zero menções a "grátis", "teste", "experimente"
  - **Critério de validação:** CTA button text não contém "grátis" ou "teste"

- [ ] **AC4: Seção "custo de não usar" é tangível**
  - OpportunityCost.tsx mostra: "Seu concorrente já pode estar se posicionando enquanto você ainda está procurando"
  - Quantifica: "Uma licitação perdida = R$ X em receita perdida"
  - **Critério de validação:** Componente menciona "concorrente" ou "competição" e quantifica dinheiro (não horas)

- [ ] **AC5: BeforeAfter compara cenários de RESULTADO (perder vs ganhar licitações), não de tempo**
  - Lado A: "Sem SmartLic → perde oportunidades, entra em licitações ruins"
  - Lado B: "Com SmartLic → vê tudo, prioriza melhor, ganha mais"
  - Zero comparações de horas/minutos
  - **Critério de validação:** BeforeAfter.tsx não contém unidades de tempo (h, min, segundos)

- [ ] **AC6: DifferentialsGrid foca em valor, não features técnicas**
  - 4 diferenciais: Priorização Inteligente, Análise Automatizada, Redução de Incerteza, Cobertura Nacional
  - Cada card responde "o que isso muda no seu resultado?"
  - Zero métricas de eficiência (%, velocidade, precisão)
  - **Critério de validação:** DifferentialsGrid.tsx não contém números de % ou menções a velocidade

- [ ] **AC7: HowItWorks orientado ao resultado**
  - Step 1: "Diga o que vende"
  - Step 2: "Receba curadoria inteligente"
  - Step 3: "Decida com confiança"
  - **Critério de validação:** HowItWorks.tsx usa verbos de decisão (não de tarefa mecânica)

- [ ] **AC8: OpportunityCost quantifica dinheiro perdido, não horas perdidas**
  - Mensagem central: "Cada licitação perdida por falta de visibilidade = R$ X"
  - Exemplo tangível: "Uma licitação de R$ 200k que foi para o concorrente porque você não sabia que existia"
  - **Critério de validação:** OpportunityCost.tsx menciona R$ (não horas) como métrica principal

### Eliminações Obrigatórias

- [ ] **AC9: ZERO menções a métricas de eficiência**
  - Banned phrases: "160x", "95%", "3 minutos", "8 horas", "economize tempo", "busca rápida", "em segundos"
  - **Critério de validação:** Grep de "160", "95%", "3 min", "rápid", "segund", "economiz" em landing/*.tsx retorna zero matches

- [ ] **AC10: ZERO menções a PNCP ou fontes específicas**
  - Banned phrases: "PNCP", "Portal Nacional de Contratações Públicas", "Compras.gov", nomes de portais
  - Use: "dezenas de fontes oficiais", "fontes governamentais", "dados oficiais em tempo real"
  - **Critério de validação:** Grep de "PNCP", "Portal Nacional" em landing/*.tsx retorna zero matches

- [ ] **AC11: ZERO testemunhos fictícios**
  - Remover: João Silva, Maria Santos, Carlos Oliveira, Ana Costa, qualquer pessoa fictícia
  - TestimonialsCarousel.tsx: ou removido completamente ou substituído por AnalysisExamplesCarousel (GTM-005)
  - **Critério de validação:** Grep de "João Silva", "Maria Santos", "Carlos" em landing/*.tsx retorna zero

### Novas Inclusões

- [ ] **AC12: Banned phrases atualizadas em valueProps.ts**
  - Adicionar a `BANNED_PHRASES`: todos termos de eficiência listados em AC9 e AC10
  - Adicionar comentário explicativo: "// GTM-001: Foco em resultado, não em velocidade"
  - **Critério de validação:** `valueProps.ts` contém array `BANNED_PHRASES` com pelo menos 15 termos

- [ ] **AC13: Preferred phrases incluem linguagem de decisão**
  - Adicionar a `PREFERRED_PHRASES`: "inteligência de decisão", "oportunidades priorizadas", "vantagem competitiva", "orientação estratégica", "redução de incerteza", "decisão com confiança"
  - **Critério de validação:** `valueProps.ts` contém array `PREFERRED_PHRASES` com termos de decisão

### Qualidade

- [ ] **AC14: Mobile responsive em viewport 375px**
  - Todos componentes de landing testados em 375x667 (iPhone SE)
  - Sem scroll horizontal, sem text overflow, CTAs visíveis
  - **Critério de validação:** Chrome DevTools mobile emulation 375px sem issues

- [ ] **AC15: Dark mode legível**
  - Todos textos com contraste mínimo 4.5:1 (WCAG AA)
  - Glass effects funcionam em dark mode
  - **Critério de validação:** Toggle dark mode, verificar legibilidade de todos componentes

- [ ] **AC16: TypeScript clean**
  - Zero erros de tipo em `npx tsc --noEmit`
  - Imports organizados, zero `any` types
  - **Critério de validação:** `npx tsc --noEmit --pretty` passa sem erros

## Definition of Done

- [ ] Todos os 16 Acceptance Criteria passam
- [ ] Landing page testada em Chrome, Safari, Firefox (latest)
- [ ] Mobile testado em dispositivo real (iOS e Android)
- [ ] Dark mode testado
- [ ] Performance: Lighthouse score >90 em Performance, Accessibility, Best Practices, SEO
- [ ] Copy reviewed por stakeholder (validação de narrativa)
- [ ] Merged to main e deployed to production

## File List

### Modified
- `frontend/app/components/landing/HeroSection.tsx`
- `frontend/app/components/landing/BeforeAfter.tsx`
- `frontend/app/components/landing/DifferentialsGrid.tsx`
- `frontend/app/components/landing/HowItWorks.tsx`
- `frontend/app/components/landing/OpportunityCost.tsx`
- `frontend/app/components/landing/FinalCTA.tsx`
- `frontend/app/components/landing/StatsSection.tsx`
- `frontend/app/components/landing/DataSourcesSection.tsx`
- `frontend/lib/copy/valueProps.ts` (~437 linhas)
- `frontend/lib/copy/comparisons.ts` (~217 linhas)

### Possibly Removed
- `frontend/app/components/landing/TestimonialsCarousel.tsx` (se não substituído por GTM-005)

## Notes

- Esta story absorve STORY-173 (Brand Positioning) e STORY-244 (Strategic Copy), que tinham escopo menor
- Depende de GTM-007 completar primeiro (sanitização PNCP) para evitar retrabalho
- Bloqueia GTM-005 (Carrossel de Exemplos), GTM-006 (Design System), GTM-008 (Reposicionamento IA) pois todas dependem da narrativa base estar estabelecida
- **Estimativa de 12h:** 4h copy/strategy + 6h implementation + 2h testing/polish
