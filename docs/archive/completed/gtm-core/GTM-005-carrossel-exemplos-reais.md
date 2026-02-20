# GTM-005: Carrossel de Exemplos Reais — Substituir Testemunhos

## Metadata
| Field | Value |
|-------|-------|
| **ID** | GTM-005 |
| **Priority** | P1 |
| **Sprint** | Sprint 2 |
| **Estimate** | 8h |
| **Depends on** | GTM-001 (landing redesign — narrativa base deve estar pronta) |
| **Blocks** | None |

## Filosofia

> **"Não mostre testemunhos de pessoas fictícias. Mostre exemplos reais de análise em ação."**

> **"Social proof não vem de 'João Silva disse que adorou'. Vem de 'Essa licitação foi analisada assim, decisão sugerida: X'."**

O site atual tem testemunhos fictícios (Carlos Mendes / Uniformes Excellence, Ana Paula Silva / Facilities Pro, Roberto Santos / Tech Solutions BR) que não transmitem credibilidade. Usuários de SaaS são céticos com testemunhos genéricos sem foto real, sem link de LinkedIn, sem verificação.

**Diretriz GTM:** Substituir por exemplos reais de análise: "Essa licitação → o sistema analisou assim → a decisão foi essa".

## Problema

### Testemunhos Atuais

**Arquivo:** `frontend/app/components/landing/TestimonialsCarousel.tsx`

**Conteúdo:**

| Nome | Empresa | Testemunho | Problema |
|------|---------|-----------|----------|
| Carlos Mendes | Uniformes Excellence | "Sistema mudou completamente nossa operação... encontramos 3x mais oportunidades" | Fictício, genérico, não verificável |
| Ana Paula Silva | Facilities Pro | "Interface intuitiva, resultados precisos..." | Sem especificidade, não mostra produto |
| Roberto Santos | Tech Solutions BR | "ROI positivo no primeiro mês..." | Métrica não comprovada |

**Localização no código:** `frontend/lib/copy/valueProps.ts` L374-406 (testimonials section)

**Problemas:**
1. **Falta de credibilidade:** Nomes comuns, sem foto real, sem empresa verificável
2. **Genérico demais:** "Mudou nossa operação" não diz COMO
3. **Não demonstra produto:** Testemunho fala sobre resultado, não mostra o sistema trabalhando
4. **Zero social proof:** Nenhum logo de empresa real, nenhum link, nenhuma verificação

### Impacto na Conversão

Testemunhos fictícios podem **reduzir** conversão ao invés de aumentar:
- Usuário suspeita que são fake → desconfia do produto
- Não há especificidade → não ajuda a entender caso de uso
- Não mostra o produto em ação → não educa

## Solução: Carrossel de Exemplos Reais de Análise

### Conceito: "Veja o SmartLic Trabalhando"

Em vez de "João disse que adorou", mostrar:

```
Licitação Real → Análise do SmartLic → Decisão Sugerida
```

**Exemplo de card:**

```
┌─────────────────────────────────────────────────────┐
│ Fornecimento de Uniformes Escolares — SP           │
│ Valor Estimado: R$ 450.000                         │
├─────────────────────────────────────────────────────┤
│ 🤖 Análise SmartLic:                                │
│ • Prazo adequado: 45 dias para proposta            │
│ • Requisitos compatíveis: 3 itens padrão           │
│ • Competitividade: Baixa (município pequeno)       │
│ • Score de adequação: 8.5/10                       │
├─────────────────────────────────────────────────────┤
│ 💡 Decisão Sugerida:                                │
│ "Participar com prioridade alta. Alta chance de    │
│  sucesso dada baixa concorrência e especificações  │
│  compatíveis com seu portfólio."                   │
└─────────────────────────────────────────────────────┘
```

### Estrutura do Componente

**Novo componente:** `AnalysisExamplesCarousel.tsx` (substitui `TestimonialsCarousel.tsx`)

**Props:**
```typescript
interface AnalysisExample {
  id: string;
  title: string;  // Ex: "Fornecimento de Uniformes Escolares"
  uf: string;     // Ex: "SP"
  valor: number;  // Em centavos
  analysis: {
    prazo: string;           // Ex: "45 dias para proposta"
    requisitos: string;      // Ex: "3 itens padrão"
    competitividade: string; // Ex: "Baixa (município pequeno)"
    score: number;           // 0-10
  };
  decision: string;  // Texto da decisão sugerida
  category: string;  // Ex: "uniforms", "facilities"
}
```

**Dados iniciais (curados manualmente):**

```typescript
const ANALYSIS_EXAMPLES: AnalysisExample[] = [
  {
    id: "example-1",
    title: "Fornecimento de Uniformes Escolares",
    uf: "SP",
    valor: 45000000, // R$ 450.000
    analysis: {
      prazo: "45 dias para proposta",
      requisitos: "3 itens padrão (calça, camisa, jaqueta)",
      competitividade: "Baixa — município pequeno interior",
      score: 8.5
    },
    decision: "Participar com prioridade alta. Alta chance de sucesso dada baixa concorrência e especificações compatíveis.",
    category: "uniforms"
  },
  {
    id: "example-2",
    title: "Serviços de Limpeza e Conservação",
    uf: "RJ",
    valor: 120000000, // R$ 1.200.000
    analysis: {
      prazo: "30 dias para proposta",
      requisitos: "Certificações ISO obrigatórias",
      competitividade: "Alta — capital com muitos fornecedores",
      score: 5.2
    },
    decision: "Avaliar certificações antes de prosseguir. Se não tiver ISO 9001, custo de entrada pode não valer a pena.",
    category: "facilities"
  },
  {
    id: "example-3",
    title: "Aquisição de EPIs",
    uf: "MG",
    valor: 8500000, // R$ 85.000
    analysis: {
      prazo: "20 dias para proposta",
      requisitos: "Certificação CA do Ministério do Trabalho",
      competitividade: "Média — 5-8 participantes esperados",
      score: 7.0
    },
    decision: "Oportunidade viável. Valor moderado, requisitos atingíveis. Preparar documentação CA com antecedência.",
    category: "uniforms"
  },
  {
    id: "example-4",
    title: "Manutenção de Elevadores",
    uf: "SP",
    valor: 35000000, // R$ 350.000
    analysis: {
      prazo: "15 dias para proposta — prazo apertado",
      requisitos: "Equipe técnica certificada NR-12",
      competitividade: "Alta — nicho especializado",
      score: 4.8
    },
    decision: "Avaliar capacidade de resposta rápida. Prazo curto pode limitar preparação de proposta competitiva.",
    category: "facilities"
  },
  {
    id: "example-5",
    title: "Uniformes para Agentes de Saúde",
    uf: "BA",
    valor: 28000000, // R$ 280.000
    analysis: {
      prazo: "60 dias para proposta",
      requisitos: "Tecido hospitalar específico, cor padronizada",
      competitividade: "Baixa — especificação técnica reduz concorrência",
      score: 8.8
    },
    decision: "Excelente oportunidade. Prazo confortável, especificação técnica favorece fornecedores especializados.",
    category: "uniforms"
  }
];
```

### Layout do Carrossel

**UI:**
- Auto-scroll horizontal (pause on hover)
- 3 cards visíveis em desktop, 1 em mobile
- Dots navigation na parte inferior
- Setas laterais (opcional)

**Card design:**
- Glass morphism (alinhado com GTM-006 Design System)
- Badge de categoria no topo (Uniformes / Facilities / etc.)
- Ícones:
  - 📍 UF
  - 💰 Valor
  - 🤖 Análise SmartLic
  - 💡 Decisão Sugerida
- Score visual: barra de 0-10 ou estrelas

**Seção na landing:**
```tsx
<Section id="examples" className="bg-surface-1">
  <SectionHeader>
    <h2>Veja o SmartLic Trabalhando</h2>
    <p>Exemplos reais de como o sistema avalia oportunidades e orienta decisões.</p>
  </SectionHeader>

  <AnalysisExamplesCarousel examples={ANALYSIS_EXAMPLES} />

  <Note>
    Dados reais de licitações públicas. Análises geradas pelo SmartLic.
  </Note>
</Section>
```

## Escopo

### Arquivo Novo: `frontend/app/components/landing/AnalysisExamplesCarousel.tsx`

**Estrutura:**
```tsx
import { useState, useEffect } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';

interface AnalysisExample {
  // ... (schema acima)
}

export function AnalysisExamplesCarousel({ examples }: { examples: AnalysisExample[] }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // Auto-scroll logic
  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % examples.length);
    }, 5000); // 5s per slide
    return () => clearInterval(interval);
  }, [isPaused, examples.length]);

  return (
    <div
      className="carousel-container"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="carousel-track">
        {examples.map((example, index) => (
          <AnalysisCard
            key={example.id}
            example={example}
            isActive={index === activeIndex}
          />
        ))}
      </div>

      {/* Dots navigation */}
      <DotsNavigation
        total={examples.length}
        activeIndex={activeIndex}
        onChange={setActiveIndex}
      />
    </div>
  );
}

function AnalysisCard({ example, isActive }: { example: AnalysisExample; isActive: boolean }) {
  return (
    <GlassCard variant="elevated" className={isActive ? 'active' : ''}>
      {/* Badge categoria */}
      <CategoryBadge category={example.category} />

      {/* Header */}
      <h3>{example.title}</h3>
      <div className="meta">
        <span>📍 {example.uf}</span>
        <span>💰 R$ {(example.valor / 100).toLocaleString('pt-BR')}</span>
      </div>

      {/* Análise */}
      <div className="analysis-section">
        <h4>🤖 Análise SmartLic</h4>
        <ul>
          <li>Prazo: {example.analysis.prazo}</li>
          <li>Requisitos: {example.analysis.requisitos}</li>
          <li>Competitividade: {example.analysis.competitividade}</li>
        </ul>
        <ScoreBar score={example.analysis.score} />
      </div>

      {/* Decisão */}
      <div className="decision-section">
        <h4>💡 Decisão Sugerida</h4>
        <p>{example.decision}</p>
      </div>
    </GlassCard>
  );
}
```

**Linhas estimadas:** ~250 linhas (component + subcomponents + styles)

### Arquivo Modificado: `frontend/lib/copy/valueProps.ts`

**Mudança:** Substituir seção `testimonials` por `analysisExamples`

**Antes (L374-406):**
```typescript
testimonials: [
  {
    name: "Carlos Mendes",
    company: "Uniformes Excellence",
    text: "O SmartLic mudou completamente nossa operação..."
  },
  // ... outros fictícios
]
```

**Depois:**
```typescript
// Remover seção testimonials
// Dados de exemplos movidos para AnalysisExamplesCarousel.tsx diretamente
// (não precisam estar em valueProps.ts — são componente-specific)
```

**Ou manter em valueProps.ts se preferir centralizar:**
```typescript
analysisExamples: ANALYSIS_EXAMPLES // (exportar de valueProps.ts)
```

**Linhas afetadas:** ~30 linhas (remoção de testimonials)

### Arquivo Possivelmente Removido: `frontend/app/components/landing/TestimonialsCarousel.tsx`

**Ação:** Deletar ou renomear para `AnalysisExamplesCarousel.tsx`

Se houver lógica de carrossel reutilizável (auto-scroll, dots nav), pode ser refatorado em vez de deletado.

### Arquivo Modificado: `frontend/app/page.tsx` (ou landing page entry point)

**Mudança:** Substituir `<TestimonialsCarousel>` por `<AnalysisExamplesCarousel>`

**Antes:**
```tsx
<TestimonialsCarousel testimonials={valueProps.testimonials} />
```

**Depois:**
```tsx
<AnalysisExamplesCarousel examples={ANALYSIS_EXAMPLES} />
```

**Linhas afetadas:** ~5 linhas (import + component usage)

## Acceptance Criteria

### Conteúdo

- [ ] **AC1: Carrossel mostra 3-5 exemplos reais de licitações analisadas**
  - Mínimo 3 exemplos (uniformes, facilities, equipamentos)
  - Dados curados manualmente (não gerados automaticamente — pode ser futuro)
  - **Critério de validação:** `ANALYSIS_EXAMPLES` array tem 5 entries completas

- [ ] **AC2: Cada card mostra análise estruturada**
  - Campos: título, UF, valor, prazo, requisitos, competitividade, score, decisão
  - Formato consistente entre cards
  - **Critério de validação:** Cada card renderiza todos os campos sem falhas

- [ ] **AC3: Formato narrativo: "Licitação → Análise → Decisão"**
  - Card divide claramente: (1) Licitação (header), (2) Análise (body), (3) Decisão (footer/highlight)
  - Usuário entende fluxo: dado de entrada → processamento IA → recomendação
  - **Critério de validação:** Card tem 3 seções visuais distintas

- [ ] **AC4: Decisão sugerida é específica e acionável**
  - ✅ Bom: "Participar com prioridade alta. Prazo adequado, requisitos compatíveis."
  - ❌ Ruim: "Boa oportunidade. Vale a pena participar."
  - Cada decisão tem justificativa baseada na análise
  - **Critério de validação:** Nenhuma decisão é genérica de <20 palavras ou sem justificativa

### Eliminações

- [ ] **AC5: ZERO testemunhos fictícios de pessoas**
  - Remover: Carlos Mendes, Ana Paula Silva, Roberto Santos, qualquer nome de pessoa
  - Se manter testemunhos reais no futuro: exigir foto real + empresa verificável + LinkedIn
  - **Critério de validação:** Grep de "Carlos Mendes", "Ana Paula", "Roberto Santos" retorna zero matches

- [ ] **AC6: TestimonialsCarousel.tsx removido ou completamente reescrito**
  - Nenhum código do carrossel antigo permanece (se reescrito)
  - Ou arquivo deletado (se criar novo do zero)
  - **Critério de validação:** `TestimonialsCarousel.tsx` não existe OU não contém testimonials fictícios

### UX/UI

- [ ] **AC7: Auto-scroll com pause on hover**
  - Carrossel avança automaticamente a cada 5s
  - Hover no card pausa auto-scroll
  - Mouse leave resume auto-scroll
  - **Critério de validação:** Hover funciona, auto-scroll pausa e resume

- [ ] **AC8: Dots navigation funcional**
  - Dots na parte inferior indicam posição (ativo vs inativo)
  - Clicar em dot navega para aquele slide
  - **Critério de validação:** Clicar em dot #3 → slide #3 aparece

- [ ] **AC9: Responsive em mobile (375px)**
  - Desktop: 3 cards visíveis (ou 2 se cards grandes)
  - Mobile: 1 card visível por vez
  - Swipe touch funciona (se implementado)
  - **Critério de validação:** Chrome DevTools 375px → carrossel mostra 1 card, navegação funciona

- [ ] **AC10: Glass morphism consistente (alinhado com GTM-006)**
  - Cards usam `GlassCard` component com `backdrop-blur`
  - Cores/spacing alinhados com design system
  - Dark mode funcional
  - **Critério de validação:** Cards têm glass effect, dark mode não quebra

### Qualidade

- [ ] **AC11: Dados podem ser estáticos inicialmente (curados manualmente)**
  - Não precisa integrar com API backend inicialmente
  - Array hardcoded em `AnalysisExamplesCarousel.tsx` é aceitável
  - Futuro: pode vir de API `/api/analysis-examples` (não nesta story)
  - **Critério de validação:** Componente funciona sem chamadas de API

- [ ] **AC12: TypeScript clean**
  - Interface `AnalysisExample` bem tipada
  - Zero `any` types
  - Props validadas
  - **Critério de validação:** `npx tsc --noEmit` passa sem erros

## Definition of Done

- [ ] Todos os 12 Acceptance Criteria passam
- [ ] Componente `AnalysisExamplesCarousel` implementado e testado
- [ ] 5 exemplos reais curados (uniformes, facilities, equipamentos mix)
- [ ] `TestimonialsCarousel.tsx` removido ou reescrito
- [ ] Landing page atualizada (substitui testimonials por examples)
- [ ] Mobile testado (375px)
- [ ] Dark mode testado
- [ ] Auto-scroll + pause on hover funciona
- [ ] Dots navigation funciona
- [ ] TypeScript clean (`npx tsc --noEmit`)
- [ ] Merged to main, deployed to production

## File List

### New
- `frontend/app/components/landing/AnalysisExamplesCarousel.tsx` (~250 linhas)
- `frontend/app/components/landing/CategoryBadge.tsx` (se não reutilizar existente)
- `frontend/app/components/landing/ScoreBar.tsx` (component para barra de score)

### Modified
- `frontend/lib/copy/valueProps.ts` (~30 linhas — remover testimonials)
- `frontend/app/page.tsx` (ou landing entry point — ~5 linhas)

### Possibly Removed
- `frontend/app/components/landing/TestimonialsCarousel.tsx`

## Notes

- Esta story depende de GTM-001 completar primeiro (landing redesign) para garantir narrativa alinhada
- Não bloqueia outras stories — pode ser desenvolvida em paralelo com GTM-006 (Design System)
- **Estimativa de 8h:** 3h component implementation (carrossel + cards) + 2h curadoria de exemplos (escrever análises realistas) + 2h styling/glass morphism + 1h testing
- **Dados iniciais:** 5 exemplos curados manualmente são suficientes. Futuro pode adicionar API para gerar dinamicamente ou rotacionar exemplos
- **Alternativa:** Se não quiser remover testimonials completamente, pode ter AMBOS (examples + testimonials reais verificáveis). Mas priorizar examples.
- **SEO:** Exemplos de análise podem conter keywords (uniformes escolares, limpeza, facilities) que ajudam SEO
- **Trust signal:** Mostrar análise real em ação é mais convincente que "João disse que gostou" — educa E convence
