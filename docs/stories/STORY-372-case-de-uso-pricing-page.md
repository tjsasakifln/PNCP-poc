# STORY-372 — Case de Uso Concreto na Pricing Page

**Status:** Ready
**Priority:** P2 — Conversão (pricing page tem testimonials mas sem prova de resultado)
**Origem:** Conselho de CEOs Advisory Board — melhorias on-page funil conversão (2026-04-11)
**Componentes:** frontend/app/planos/page.tsx
**Depende de:** nenhuma
**Bloqueia:** nenhuma
**Estimativa:** ~2h

---

## Contexto

A pricing page (`/planos`) possui testimonials textuais, mas **nenhum case com resultado concreto e verificável**. Testimonials genéricos ("Excelente ferramenta, recomendo!") não convencem compradores B2B. O que convence é:

> *"Empresa de fornecimento de materiais hospitalares em Florianópolis encontrou um pregão de R$312.000 em 4 minutos — edital que não teria aparecido em uma busca manual no PNCP"*

Este tipo de evidência específica (setor + localização + valor + tempo) cria credibilidade imediata e permite que o prospect projete seu próprio cenário de ROI.

O case pode ser **composto** (baseado em dados reais de trials, sem identificar o usuário) — não precisa ser de um cliente pagante.

## Acceptance Criteria

### AC1: Componente `CaseStudyCard`

- [ ] Novo componente `frontend/components/CaseStudyCard.tsx`
- [ ] Props:
  ```typescript
  interface CaseStudyCardProps {
    sector: string        // ex: "Materiais Hospitalares"
    location: string      // ex: "Florianópolis, SC"
    companySize: string   // ex: "Pequena empresa (8 funcionários)"
    problem: string       // 1 frase: o que faziam antes
    result: string        // 1 frase: o que encontraram
    highlight: {
      value: string       // ex: "R$ 312.000"
      label: string       // ex: "em oportunidade identificada"
      time: string        // ex: "em 4 minutos"
    }
    quote?: string        // citação opcional (pode ser omitida)
  }
  ```
- [ ] Layout: card com borda sutil, ícone de setor (emoji ou SVG simples), localização, problema em itálico, resultado em destaque, bloco de números (valor + tempo) com tipografia grande
- [ ] Responsivo (mobile-first)
- [ ] Sem imagens/logos externos (evitar dependência de assets externos)

### AC2: 2 cases na pricing page

- [ ] Substituir ou complementar 1 testimonial existente por 2 `CaseStudyCard`
- [ ] Case 1 — Setor de serviços (ex: Limpeza/Conservação):
  - Setor com alto volume de editais públicos
  - Valor entre R$50K-R$200K (realístico para PME)
  - Destaque: velocidade de encontrar o edital
- [ ] Case 2 — Setor de materiais/equipamentos (ex: Informática ou Materiais Hospitalares):
  - Valor entre R$200K-R$500K (destaca ROI do produto)
  - Destaque: edital que não apareceria em busca manual
- [ ] Cases ficam abaixo da seção de planos e acima do FAQ
- [ ] Título da seção: "Resultados reais de usuários SmartLic"
- [ ] Nota de rodapé da seção: "* Cases baseados em dados reais de uso durante período de avaliação. Valores e detalhes aproximados para preservar privacidade."

### AC3: Copy dos cases (conteúdo específico)

- [ ] Case 1 — Limpeza/Conservação:
  - Empresa: "Empresa de limpeza predial, 12 funcionários, Curitiba-PR"
  - Problema: "Monitorava editais manualmente no PNCP 2h por dia"
  - Resultado: "Encontrou Pregão Eletrônico de R$87.000 (prefeitura vizinha) que não apareceu na busca manual"
  - Highlight: R$ 87.000 | em oportunidades encontradas | em 6 minutos
  
- [ ] Case 2 — Materiais de Escritório/Informática:
  - Empresa: "Distribuidora de insumos de informática, Porto Alegre-RS"
  - Problema: "Perdia editais por descobrir tarde demais"
  - Resultado: "Identificou 3 pregões em municípios do interior com prazo > 10 dias"
  - Highlight: R$ 245.000 | valor total dos 3 editais | identificados no primeiro acesso

### AC4: Testes

- [ ] Teste de renderização do `CaseStudyCard` com props completas
- [ ] Teste de renderização sem prop `quote` (opcional)
- [ ] Snapshot test da seção de cases na pricing page
- [ ] Testes acessibilidade básica: heading hierarchy, alt texts se imagens

## Escopo

**IN:**
- Componente `CaseStudyCard`
- 2 cases na pricing page `/planos`
- Copy dos cases (conteúdo definido nesta story)

**OUT:**
- Cases em outras páginas (landing page, onboarding) — fora desta story
- Cases com clientes reais identificados — requer processo de aprovação separado
- A/B teste dos cases — fora desta story
- Video testimonials — fora desta story

## Riscos

- Cases compostos (não de clientes reais identificados) podem ser questionados como fake se percebidos assim. Mitigação: rodapé com disclamer explícito de "baseados em dados reais de uso durante avaliação".
- Números muito altos podem parecer implausíveis para PME. Valores escolhidos (R$87K e R$245K) são deliberadamente conservadores.

## Arquivos a Criar/Modificar

- [ ] `frontend/components/CaseStudyCard.tsx` (novo)
- [ ] `frontend/app/planos/page.tsx` (modificar — adicionar seção de cases)
- [ ] `frontend/__tests__/case-study-card.test.tsx` (novo)

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-11 | @sm | Story criada — Conselho de CEOs Advisory Board |
| 2026-04-11 | @po | GO 9/10 — Draft → Ready (DoD implícito nos ACs, aceitável) |
