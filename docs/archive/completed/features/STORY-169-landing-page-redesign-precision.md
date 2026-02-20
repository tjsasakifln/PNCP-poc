# STORY-169: Redesign Landing Page — Precision & Utility

**Epic:** User Experience
**Priority:** High
**Points:** 13
**Status:** In Progress
**Depends On:** STORY-168 (completed)

## User Story

**Como** visitante do SmartLic,
**Quero** uma experiência visual que transmita eficiência, confiabilidade e objetividade,
**Para que** eu perceba imediatamente que este é um sistema sério que vai direto ao que interessa.

## Contexto

A STORY-168 implementou a landing page com estrutura e copy corretos, mas usando padrões visuais genéricos que violam diretrizes de design (interface-design + frontend-design):

### Violações Identificadas

| Categoria | Problema | Impacto |
|-----------|----------|---------|
| **Tipografia** | Fonts padrão do sistema (Tailwind defaults) | Visual genérico "AI slop" |
| **Cores** | `blue-600` em tudo, não usa tokens do design system | Inconsistência, monotonia |
| **Layout** | Grids simétricos previsíveis (4 colunas iguais) | Template genérico |
| **Motion** | Nenhuma animação de entrada | Falta de polish |
| **Tokens** | Não usa `--ink`, `--canvas`, `--brand-navy` do globals.css | Desperdício do design system |

### Nova Direção Estética

**Personalidade:** "Precision & Utility" — ferramenta séria para profissionais sérios.

**Princípios:**
1. **Direto ao que interessa** — sem floreios, sem marketing speak
2. **Intuitivo** — hierarquia visual clara, navegação óbvia
3. **Rápido** — leitura escaneável, dados em destaque
4. **Confiável** — tom institucional, credibilidade primeiro

**Tom de Voz:**
- Factual, não efusivo
- Números concretos, não promessas vagas
- Confiante, não vendedor
- Institucional, não casual

## Acceptance Criteria

### AC1: Sistema de Tokens Aplicado

- [x] Todas as cores usando CSS variables do globals.css:
  - `text-[var(--ink)]` em vez de `text-gray-900`
  - `bg-[var(--brand-navy)]` em vez de `bg-blue-600`
  - `bg-[var(--surface-1)]` em vez de `bg-gray-50`
  - `border-[var(--border)]` em vez de `border-gray-200`
- [x] Cores semânticas aplicadas corretamente:
  - `--success` para indicadores positivos
  - `--error` para indicadores negativos (seção "Sem SmartLic")
  - `--warning` para alertas/urgência

### AC2: Tipografia Distintiva

- [x] Headline principal: peso maior (800), tracking tighter (-0.02em)
- [x] Subheadlines: peso médio (500), cor secundária (`--ink-secondary`)
- [x] Body text: usando `--ink` com line-height adequado
- [x] Números/stats: font-variant tabular-nums, peso bold
- [x] Hierarquia clara: 3 níveis distintos de heading

### AC3: Animações de Entrada

- [x] Hero: fade-in-up ao carregar (300ms)
- [x] Seções: staggered reveal ao entrar no viewport (IntersectionObserver)
- [x] Cards: entrada sequencial com delay (50ms entre cada)
- [x] CTAs: subtle scale on hover (1.02)
- [x] Respeita `prefers-reduced-motion`

### AC4: Layout Assimétrico (Quebra de Padrão)

- [x] **StatsSection**: Um número hero grande (6M+) + 3 menores ao lado
- [x] **DifferentialsGrid**: 2+2 assimétrico ou 1 destaque + 3 menores
- [x] **SectorsGrid**: Layout masonry ou grouped por categoria
- [x] **BeforeAfter**: Proporção 40/60 em vez de 50/50

### AC5: Copy Refinada — Tom Institucional Direto

**Hero:**
- Antes: "Encontre as que realmente importam para sua empresa."
- Depois: "Encontre as relevantes para seu setor."

**CTAs:**
- Antes: "Começar busca gratuita"
- Depois: "Acessar busca"

**Badge:**
- Antes: "Criado por servidores públicos | Dados PNCP + múltiplas fontes oficiais"
- Depois: "Fonte oficial: PNCP. Desenvolvido por servidores públicos."

**Custo de Oportunidade:**
- Antes: "Qual o custo de uma licitação não disputada por não ter sido encontrada?"
- Depois: "Licitações não encontradas são contratos perdidos."

**Diferenciais:**
- Remover textos longos
- Usar bullet points curtos
- Foco em dados, não promessas

### AC6: Backgrounds com Atmosfera

- [x] Hero: gradient sutil usando `--brand-blue-subtle`
- [x] Seções alternadas: `--surface-0` / `--surface-1`
- [x] CTA Final: `--brand-navy` sólido (não gradiente)
- [x] Bordas sutis: `--border` com 0.5px

### AC7: Estados de Interação

- [x] Hover em cards: `translateY(-2px)` + sombra sutil
- [x] Hover em botões: cor mais escura (`--brand-blue-hover`)
- [x] Focus visible: ring de 3px com `--ring`
- [x] Active: scale(0.98)

### AC8: Responsividade Refinada

- [x] Mobile: headlines 32px max, padding 16px
- [x] Tablet: transição suave de grids
- [x] Desktop: max-width 1200px, não 1280px (mais denso)

## Technical Implementation

### Arquivos a Modificar

```
frontend/app/components/landing/
├── HeroSection.tsx        # Tokens + animação + copy
├── OpportunityCost.tsx    # Tokens + copy refinada
├── BeforeAfter.tsx        # Layout assimétrico + cores semânticas
├── DifferentialsGrid.tsx  # Layout 2+2 + copy curta
├── HowItWorks.tsx         # Animações staggered
├── StatsSection.tsx       # Layout hero number + 3
├── DataSourcesSection.tsx # Simplificação visual
├── SectorsGrid.tsx        # Agrupamento por categoria
├── FinalCTA.tsx           # Brand-navy sólido + copy direta
└── LandingNavbar.tsx      # Tokens + estados
```

### Tailwind Customization (tailwind.config.ts)

```typescript
extend: {
  colors: {
    ink: 'var(--ink)',
    'ink-secondary': 'var(--ink-secondary)',
    'ink-muted': 'var(--ink-muted)',
    canvas: 'var(--canvas)',
    'brand-navy': 'var(--brand-navy)',
    'brand-blue': 'var(--brand-blue)',
    'surface-0': 'var(--surface-0)',
    'surface-1': 'var(--surface-1)',
    'surface-2': 'var(--surface-2)',
  },
  fontWeight: {
    'display': '800',
  },
  letterSpacing: {
    'tighter': '-0.02em',
  }
}
```

### Intersection Observer Hook

```typescript
// hooks/useInView.ts
export function useInView(options?: IntersectionObserverInit) {
  const ref = useRef<HTMLElement>(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => setIsInView(entry.isIntersecting),
      { threshold: 0.1, ...options }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return { ref, isInView };
}
```

## Copy Reference — Versão Final

### Hero

```
6+ milhões de licitações por ano.
Encontre as relevantes para seu setor.

500 mil publicações mensais. Filtros inteligentes. Resultado em minutos.

[Acessar busca]  [Como funciona]

Fonte oficial: PNCP. Desenvolvido por servidores públicos.
```

### Custo de Oportunidade

```
Licitações não encontradas são contratos perdidos.

• 500 mil oportunidades mensais
• Maioria ignorada por falta de ferramenta adequada
• Seu concorrente pode estar encontrando agora
```

### Comparativo

```
BUSCA MANUAL                    COM SMARTLIC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8h/dia em portais              15min/dia automatizado
Editais perdidos               Alertas em tempo real
27 fontes fragmentadas         Busca unificada
Sem histórico                  Rastreamento completo
```

### Diferenciais (Bullet Points)

```
TEMPO
• 500k oportunidades/mês processadas
• Resumos automáticos
• Resultado em minutos

PRECISÃO
• Filtros por setor, estado, valor
• Palavras-chave customizáveis
• Zero ruído

CONFIANÇA
• Fonte primária: PNCP
• Múltiplas fontes complementares
• Atualização diária

PRATICIDADE
• Relatório Excel em 1 clique
• Histórico completo
• Zero configuração
```

### Stats (Layout Hero)

```
         6M+
   licitações/ano
   ━━━━━━━━━━━━━━

500k/mês     12 setores     Servidores públicos
processadas  atendidos      criadores do sistema
```

### CTA Final

```
Pronto para encontrar licitações relevantes?

[Acessar busca — 3 consultas gratuitas]

Sem cartão. Sem compromisso.
```

## Definition of Done

- [x] Todos os componentes usando tokens do design system
- [x] Animações de entrada implementadas
- [x] Layout assimétrico em pelo menos 2 seções
- [x] Copy atualizada para tom institucional direto
- [x] Responsividade testada em 3 breakpoints
- [ ] Lighthouse Performance > 90
- [ ] Lighthouse Accessibility > 95
- [x] Testes unitários passando
- [ ] Code review aprovado
- [ ] Deploy em staging para validação

## Out of Scope

- Mudança de estrutura de seções (mantém STORY-168)
- Novas seções
- Alteração de rotas
- Testes E2E (já cobertos em STORY-168)

## Benchmark Analysis (2026-02-07)

Análise de 3 concorrentes para calibrar posicionamento:

### Effecti (effecti.com.br)
**Posicionamento:** Plataforma completa de automação

| Elemento | Observação |
|----------|------------|
| **Headline** | "Automatizar licitações com segurança e crescer com liberdade" |
| **Prova social** | 3.000+ empresas, R$ 82 bilhões arrematados em 2024 |
| **Stats** | +840k oportunidades, +456k propostas, +210k processos, +1,1B mensagens |
| **Cobertura** | 1.400 portais |
| **IA** | "Aimê" — assistente de IA para licitações |
| **CTAs** | "Teste grátis", "Acesse a demonstração" |
| **Extras** | Newsletter, Calculadora de ROI, Diagnóstico de Maturidade |

**Tom:** Marketing + benefícios emocionais ("crescer com liberdade")

### ConLicitação (conlicitacao.com.br)
**Posicionamento:** Plataforma de ferramentas modulares

| Elemento | Observação |
|----------|------------|
| **Headline** | "Tudo que você precisa para vender ao governo" |
| **Prova social** | 20.000+ empresas, logos (Bradesco, Philips, Sodexo, TAM, Accenture) |
| **3 Pilares** | Personalização, Agilidade, Segurança |
| **Ferramentas** | 9 módulos distintos (Banco de dados, Boletins, Gestão, etc.) |
| **Jornada** | 6 etapas visuais (Entendimento → Monitoramento) |
| **Depoimentos** | Carrossel com fotos reais e citações |
| **FAQ** | Perguntas frequentes expandíveis |
| **0800** | Número gratuito visível no header |

**Tom:** Funcional + abrangente ("tudo que você precisa")

### Descomplicita (descomplicita.com.br)
**Posicionamento:** Educação e capacitação (não concorrente direto)
- Foco em cursos e mentorias
- Autoridade via professores credenciados (advogados, ex-servidores)

---

## Insights do Benchmark → Aplicações SmartLic

### 1. DIFERENCIAÇÃO CLARA

| Concorrente | Foco | SmartLic |
|-------------|------|----------|
| Effecti | Automação completa + robô de lances | **Descoberta de oportunidades** |
| ConLicitação | Suite de 9+ ferramentas | **Uma ferramenta. Três passos.** |
| SmartLic | — | **Direto ao ponto. Sem ruído.** |

**Posicionamento único:** SmartLic não é plataforma completa. É **radar de oportunidades** — encontrar o que importa, rápido.

### 2. COPY REFINADA (Pós-Benchmark)

**Hero — Versão Final:**
```
Licitações relevantes. Sem ruído.

6 milhões de publicações/ano no Brasil.
Filtros inteligentes entregam o que importa para seu setor.

[Acessar busca]

Dados do PNCP. Desenvolvido por servidores públicos.
```

**Diferencial vs Concorrentes:**
- Effecti: "automatizar licitações com segurança e crescer com liberdade" (16 palavras)
- ConLicitação: "Tudo que você precisa para vender ao governo" (8 palavras)
- **SmartLic: "Licitações relevantes. Sem ruído."** (4 palavras)

### 3. O QUE NÃO COPIAR

| Prática | Porque Evitar |
|---------|---------------|
| Carrossel de logos | SmartLic não tem ainda (seria fake) |
| Depoimentos | Não há clientes suficientes (seria forçado) |
| +20 ferramentas | SmartLic é focado, não suite |
| 0800 | Não há estrutura de suporte telefônico |
| Calculadora de ROI | Over-engineering para POC |

### 4. O QUE ADOTAR

| Prática | Aplicação SmartLic |
|---------|-------------------|
| **Números grandes e específicos** | "6M+ licitações/ano" como hero stat |
| **Credencial diferenciadora** | "Desenvolvido por servidores públicos" em destaque |
| **Jornada simplificada** | Manter 3 passos (já temos), mas com visual mais impactante |
| **Comparativo Antes/Depois** | Já temos, refinar proporção visual |
| **CTAs diretos** | "Acessar busca" (não "Começar agora") |

### 5. SIGNATURE ELEMENT — SmartLic

Elemento visual único que nenhum concorrente tem:

**"O Filtro"** — Representação visual de:
```
500.000 publicações/mês  →  [FILTRO]  →  As que importam
         (ruído)                          (sinal)
```

Pode ser animado: partículas entrando, poucas saindo do outro lado. Reforça a mensagem "sem ruído".

---

## Copy Final (Versão Pós-Benchmark)

### Hero

```
Licitações relevantes. Sem ruído.

6 milhões de publicações por ano no Brasil.
Filtros inteligentes entregam o que importa para seu setor.

[Acessar busca]  [Como funciona]

Dados do PNCP. Desenvolvido por servidores públicos.
```

### Custo de Oportunidade

```
Licitações não encontradas são contratos perdidos.

• 500 mil oportunidades/mês no Brasil
• A maioria passa despercebida
• Seu concorrente pode estar encontrando agora
```

### Comparativo (Proporção 40/60)

```
┌─────────────────────┐  ┌──────────────────────────────┐
│   BUSCA MANUAL      │  │       COM SMARTLIC           │
│   ───────────────   │  │       ─────────────          │
│                     │  │                              │
│   8h/dia            │  │   15min/dia                  │
│   em portais        │  │   automatizado               │
│                     │  │                              │
│   Editais perdidos  │  │   Alertas em tempo real      │
│                     │  │                              │
│   27 fontes         │  │   Busca unificada            │
│   fragmentadas      │  │                              │
│                     │  │   Histórico completo         │
│   Sem histórico     │  │                              │
└─────────────────────┘  └──────────────────────────────┘
       (menor)                    (maior, destacado)
```

### Diferenciais (Layout 1+3)

```
┌─────────────────────────────────────────────────────────┐
│                      TEMPO                              │
│                      ─────                              │
│   500k oportunidades/mês processadas                    │
│   Resumos automáticos • Resultado em minutos            │
│                                                         │
│   (card maior, destaque)                                │
└─────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    PRECISÃO     │  │   CONFIANÇA     │  │  PRATICIDADE    │
│    ─────────    │  │   ──────────    │  │  ───────────    │
│  Filtros por    │  │  Fonte: PNCP    │  │  Excel 1-clique │
│  setor, estado  │  │  + complementos │  │  Zero config    │
│  valor          │  │  Atualização    │  │  Histórico      │
│  Zero ruído     │  │  diária         │  │  completo       │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Stats (Hero Number Layout)

```
         ┌─────────────────────────────┐
         │            6M+              │
         │      licitações/ano         │
         │      ─────────────          │
         │    (número hero, grande)    │
         └─────────────────────────────┘

┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│    500k/mês   │  │  12 setores   │  │  Servidores   │
│   processadas │  │   atendidos   │  │   públicos    │
└───────────────┘  └───────────────┘  └───────────────┘
```

### CTA Final

```
Encontre licitações relevantes.

[Acessar busca — 3 consultas gratuitas]

Sem cartão. Sem compromisso.
```

---

## References

- **interface-design**: https://github.com/Dammyjay93/interface-design
- **frontend-design**: https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design
- **Design System existente**: `frontend/app/globals.css`
- **Benchmark Effecti**: https://effecti.com.br
- **Benchmark ConLicitação**: https://conlicitacao.com.br

---

**Created by:** @pm (Morgan)
**Date:** 2026-02-07
**Updated:** 2026-02-07 (benchmark analysis added)
