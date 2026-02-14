# STORY-244: Copy Estratégica — Posicionamento Premium na Landing Page

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-244 |
| **Priority** | P1 |
| **Sprint** | Sprint 3 |
| **Estimate** | 10h |
| **Depends on** | Nenhuma (independente dos outros stories) |
| **Blocks** | Nenhuma |

## Problema
A landing page atual posiciona SmartLic como uma ferramenta de busca que "economiza tempo" (HeroSection: "Encontre Oportunidades Relevantes em 3 Minutos, Não em 8 Horas"). Isso é commodity — qualquer ferramenta de busca pode dizer isso.

O posicionamento correto é: **SmartLic é seu analista de licitações especializado** que encontra, avalia e recomenda as melhores oportunidades para SEU perfil de negócio.

## Solução
Reescrever toda a copy da landing page (6 componentes) para refletir posicionamento de inteligência estratégica, não de ferramenta de busca.

## Investigação Técnica

### Componentes da Landing Page

| Componente | Arquivo | Copy Atual (problema) | Copy Nova (direção) |
|-----------|---------|----------------------|---------------------|
| **HeroSection** | `frontend/app/components/landing/HeroSection.tsx:77-109` | "Encontre Oportunidades em 3 Minutos" / "Economize 10h/Semana" | "Seu Analista de Licitações com IA" / "Oportunidades Certas, No Momento Certo" |
| **BeforeAfter** | `frontend/app/components/landing/BeforeAfter.tsx` | Comparação antes/depois focada em tempo | Comparação focada em qualidade de decisão e taxa de acerto |
| **DifferentialsGrid** | `frontend/app/components/landing/DifferentialsGrid.tsx` | Features técnicas (multi-UF, Excel, etc.) | Diferenciais de valor (filtro inteligente, curadoria IA, zero ruído) |
| **HowItWorks** | `frontend/app/components/landing/HowItWorks.tsx` | "Selecione → Busque → Baixe" (mecânico) | "Diga o que vende → Receba curadoria → Decida com confiança" |
| **OpportunityCost** | `frontend/app/components/landing/OpportunityCost.tsx` | Custo de horas perdidas | Custo de oportunidades perdidas (licitações que passou batido) |
| **FinalCTA** | `frontend/app/components/landing/FinalCTA.tsx` | "Economize 10h/Semana Agora" | "Comece a Ganhar Licitações Hoje" |
| **DataSourcesSection** | `frontend/app/components/landing/DataSourcesSection.tsx` | Menciona fontes de dados (PNCP) | Menciona cobertura total + precisão ("100% das licitações federais") |

### Diretrizes de Copy

1. **Tom:** Profissional, confiante, orientado a resultado (não hype)
2. **Foco:** Resultado de negócio (ganhar licitações), não feature técnica (busca rápida)
3. **Prova social:** Números concretos ("R$ 2.3 bilhões em oportunidades mapeadas")
4. **Urgência real:** "Licitações encerram a cada hora. A que está aberta agora pode ser a sua."
5. **Linguagem:** "Curadoria" não "busca". "Oportunidades" não "resultados". "Inteligência" não "filtro".

## Acceptance Criteria

### Hero Section
- [ ] **AC1:** Headline principal comunica proposição de valor (inteligência/curadoria), não economia de tempo.
- [ ] **AC2:** Sub-headline menciona IA como diferencial ("IA analisa", "curadoria inteligente").
- [ ] **AC3:** CTA primary usa verbo de resultado ("Encontrar minhas oportunidades", "Começar agora").
- [ ] **AC4:** Badge ou trust signal com número de oportunidades mapeadas.

### Demais Seções
- [ ] **AC5:** BeforeAfter compara qualidade da decisão (antes: manual, incerto; depois: curado, preciso).
- [ ] **AC6:** DifferentialsGrid foca em 4 diferenciais de valor: (1) Filtro inteligente por setor, (2) Só oportunidades abertas, (3) Resumo executivo IA, (4) Zero ruído.
- [ ] **AC7:** HowItWorks usa 3 passos orientados ao usuário, não ao sistema.
- [ ] **AC8:** OpportunityCost quantifica oportunidades perdidas, não horas.
- [ ] **AC9:** FinalCTA usa verbo de resultado com urgência real.
- [ ] **AC10:** DataSourcesSection posiciona cobertura total ("Portal Nacional de Contratações Públicas — 100% das licitações federais").

### Qualidade
- [ ] **AC11:** Nenhuma seção usa os termos proibidos: "economize tempo", "busca rápida", "ferramenta de busca", "planilha automatizada".
- [ ] **AC12:** Todas as seções passam em revisão de tom (profissional, não hype).
- [ ] **AC13:** Mobile responsive — copy não quebra em viewport 375px.
- [ ] **AC14:** Dark mode — copy legível em ambos os temas.

### Regressão
- [ ] **AC15:** Testes de componente existentes atualizados para nova copy.
- [ ] **AC16:** TypeScript clean após mudanças.

## Definition of Done
- Todos os ACs checked
- `npm test` sem regressões
- TypeScript clean
- Screenshot review em mobile e desktop
