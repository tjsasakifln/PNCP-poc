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

- [x] **AC1: Hero headline comunica DECISÃO, não velocidade** ✓ (commit e7bf18c)
  - Headline: "Saiba Onde Investir para Ganhar Mais Licitações" ✓
  - Zero menções a "3 minutos", "rápido", "velocidade" ✓
  - **Validação:** Grep confirmado — zero matches de eficiência em HeroSection.tsx

- [x] **AC2: Sub-headline posiciona IA como analista de oportunidades (não gerador de resumos)** ✓ (commit e7bf18c)
  - Sub-headline: "Inteligência que avalia oportunidades, prioriza o que importa" ✓
  - Zero menções a "resume", "resumo executivo", "sintetiza" ✓

- [x] **AC3: CTA principal usa verbo de resultado** ✓ (commit e7bf18c)
  - CTA: "Descobrir minhas oportunidades" ✓
  - Zero menções a "grátis", "teste", "experimente" — grep confirmado ✓

- [x] **AC4: Seção "custo de não usar" é tangível** ✓ (commit e7bf18c)
  - "Uma única licitação perdida por falta de visibilidade pode custar R$ 50.000, R$ 200.000 ou mais" ✓
  - "O custo de não usar SmartLic não é tempo — é dinheiro" ✓

- [x] **AC5: BeforeAfter compara cenários de RESULTADO (perder vs ganhar licitações), não de tempo** ✓ (commit e7bf18c)
  - Lado A: "Sem SmartLic" → "Perde contratos por falta de visibilidade" ✓
  - Lado B: "Com SmartLic" → "Visão completa do mercado em tempo real" ✓
  - Zero comparações de horas/minutos ✓

- [x] **AC6: DifferentialsGrid foca em valor, não features técnicas** ✓ (commit e7bf18c)
  - 4 diferenciais: PRIORIZAÇÃO INTELIGENTE, ANÁLISE AUTOMATIZADA, REDUÇÃO DE INCERTEZA, COBERTURA NACIONAL ✓
  - Zero métricas de eficiência (%, velocidade, precisão) ✓

- [x] **AC7: HowItWorks orientado ao resultado** ✓ (commit e7bf18c)
  - Step 1: "Diga o que você vende" ✓
  - Step 2: "Receba oportunidades priorizadas" ✓
  - Step 3: "Decida com confiança" ✓

- [x] **AC8: OpportunityCost quantifica dinheiro perdido, não horas perdidas** ✓ (commit e7bf18c)
  - "R$ 50.000, R$ 200.000 ou mais" como métrica principal ✓
  - "O custo de não usar SmartLic não é tempo — é dinheiro" ✓

### Eliminações Obrigatórias

- [x] **AC9: ZERO menções a métricas de eficiência** ✓ (commit e7bf18c)
  - "160x" e "95%" aparecem apenas como comentário numa regex utility (não user-visible) ✓
  - Stats badges usam valores de mercado: "R$ 2.3 bi", "12 setores", "27 estados" ✓
  - **Validação:** Grep confirmado — zero matches de eficiência em texto visível

- [x] **AC10: ZERO menções a PNCP ou fontes específicas** ✓ (commit e7bf18c)
  - Grep de "PNCP" em `landing/*.tsx` retorna ZERO matches ✓
  - Grep de "Portal Nacional" em `landing/*.tsx` retorna ZERO matches ✓

- [x] **AC11: ZERO testemunhos fictícios** ✓ (commit e7bf18c)
  - Grep de "João Silva", "Maria Santos", "Carlos Oliveira" retorna ZERO matches ✓
  - TestimonialsCarousel.tsx reescrito — nomes fictícios removidos ✓

### Novas Inclusões

- [x] **AC12: Banned phrases atualizadas em valueProps.ts** ✓ (commit e7bf18c)
  - `BANNED_PHRASES` contém 20+ termos incluindo eficiência e PNCP ✓
  - `validateCopy()` utility function para enforcement ✓

- [x] **AC13: Preferred phrases incluem linguagem de decisão** ✓ (commit e7bf18c)
  - `PREFERRED_PHRASES` contém: "Inteligência de decisão em licitações", "avaliação objetiva", "decisão informada", "vale a pena ou não" ✓

### Qualidade

- [ ] **AC14: Mobile responsive em viewport 375px** — pendente teste manual
  - Todos componentes de landing testados em 375x667 (iPhone SE)
  - Sem scroll horizontal, sem text overflow, CTAs visíveis
  - **Critério de validação:** Chrome DevTools mobile emulation 375px sem issues

- [ ] **AC15: Dark mode legível** — pendente teste manual
  - Todos textos com contraste mínimo 4.5:1 (WCAG AA)
  - Glass effects funcionam em dark mode
  - **Critério de validação:** Toggle dark mode, verificar legibilidade de todos componentes

- [x] **AC16: TypeScript clean** ✓
  - `npx tsc --noEmit --pretty` passa sem erros (validado no build) ✓

## Definition of Done

- [ ] Todos os 16 Acceptance Criteria passam — ⚠️ 14/16 done, 2 pendentes (AC14 mobile, AC15 dark mode)
- [ ] Landing page testada em Chrome, Safari, Firefox (latest)
- [ ] Mobile testado em dispositivo real (iOS e Android)
- [ ] Dark mode testado
- [ ] Performance: Lighthouse score >90 em Performance, Accessibility, Best Practices, SEO
- [ ] Copy reviewed por stakeholder (validação de narrativa)
- [x] Merged to main ✓ (commit e7bf18c)
- [ ] Deployed to production

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
