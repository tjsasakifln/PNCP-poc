# GTM-COPY-004: Elementos de Segurança na Decisão

**Épico:** GTM-COPY — Reposicionamento Estratégico de Comunicação
**Prioridade:** P1
**Tipo:** Enhancement
**Estimativa:** M (7-9 ACs)
**Depende de:** GTM-COPY-001

## Objetivo

Introduzir **elementos explícitos de segurança na decisão** ao longo do site, reforçando transparência dos critérios utilizados, indicação do nível de aderência de cada oportunidade e destaque de como o sistema reduz falsos positivos e negativos — transformando isso em **benefício tangível**.

## Contexto

O sistema já possui mecanismos robustos de filtragem (1000+ keywords, LLM arbiter, viability assessment), mas isso **não está comunicado** na landing. O visitante não sabe que:

1. Cada oportunidade tem um **score de aderência** ao perfil
2. O sistema usa **critérios objetivos** documentados (não heurísticas genéricas)
3. Existe redução ativa de **falsos positivos** (ruído) e **falsos negativos** (oportunidades perdidas)
4. A transparência dos critérios é um diferencial real

### Impacto Desejado

O visitante deve perceber que **continuar sem a ferramenta = operar no escuro**, enquanto usá-la = **decisões mais assertivas com maior previsibilidade de resultado**.

## Acceptance Criteria

### AC1 — Seção "Por que confiar nas recomendações"
- [x] Nova seção ou expansão de seção existente na landing
- [x] Título orientado a confiança: "Cada recomendação tem uma justificativa"
- [x] Explica em 3-4 pontos como o sistema avalia (sem revelar propriedade intelectual)
- [x] Arquivo: novo componente ou expansão de `DifferentialsGrid.tsx`

### AC2 — Critérios de Avaliação Visíveis
- [x] Lista explícita dos critérios que o sistema usa para avaliar oportunidades:
  - Compatibilidade setorial (keywords + IA)
  - Faixa de valor adequada ao porte
  - Prazo viável para preparação
  - Região de atuação
  - Modalidade favorável
- [x] Cada critério com ícone + descrição de 1 linha
- [x] Posicionamento: próximo à prova de funcionamento (GTM-COPY-003) ou como seção independente

### AC3 — Indicador de Aderência Explicado
- [x] Explicação visual de como o "nível de aderência" funciona
- [x] Escala: Alta / Média / Baixa com cores (verde/amarelo/cinza)
- [x] Cada nível tem descrição: "Alta = 3+ critérios atendem seu perfil"
- [x] Conecta com ViabilityBadge existente (se feature flag ativa) ou usa linguagem similar

### AC4 — Redução de Falsos Positivos (Comunicação)
- [x] Copy explícita sobre como o sistema **reduz ruído**
- [x] Números ou proporções: "Em média, X% dos editais são descartados por irrelevância"
- [x] Benefício tangível: "Você recebe 20 recomendações, não 2.000 resultados genéricos"
- [x] Pode ser integrado à seção de comparação ou à prova de funcionamento

### AC5 — Redução de Falsos Negativos (Comunicação)
- [x] Copy explícita sobre como o sistema **não perde oportunidades relevantes**
- [x] Explica: cobertura de 27 UFs, múltiplas fontes oficiais, IA para editais ambíguos
- [x] Benefício tangível: "Se existe algo compatível em qualquer lugar do Brasil, você sabe"
- [x] Pode ser integrado à seção de cobertura

### AC6 — "Operar no Escuro" Narrative
- [x] Em pelo menos 2 pontos da página, a narrativa reforça:
  - "Sem filtro estratégico, você decide com base em intuição"
  - "Com SmartLic, cada decisão é baseada em critérios objetivos documentados"
- [x] O contraste deve ser **emocional mas factual** — não fear-mongering
- [x] Integrado naturalmente nas seções BeforeAfter ou OpportunityCost

### AC7 — Trust Indicators Consolidados
- [x] Revisar e consolidar todos os indicadores de confiança da página:
  - Fontes oficiais verificadas
  - Critérios objetivos (não opinião)
  - Cancelamento em 1 clique
  - Sem dados fabricados
- [x] Posicionamento estratégico: próximo ao CTA principal e ao CTA final
- [x] Arquivo: `FinalCTA.tsx` e/ou `HeroSection.tsx`

### AC8 — Features Page — Seção de Confiança
- [x] Página `/features` recebe menção explícita à transparência de critérios
- [x] Pode ser um card adicional ou expansão dos existentes
- [x] Arquivo: `features/page.tsx` ou `FeaturesContent.tsx`

### AC9 — Zero Regressions
- [x] TypeScript compila
- [x] Testes frontend: zero novas falhas
- [x] Layout visual preservado nas seções não alteradas

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/components/landing/TrustCriteria.tsx` | **NOVO** — AC1, AC2, AC3, AC4, AC5 |
| `frontend/__tests__/landing/TrustCriteria.test.tsx` | **NOVO** — 9 testes |
| `frontend/app/components/landing/OpportunityCost.tsx` | AC6 — contraste critérios objetivos |
| `frontend/app/components/landing/BeforeAfter.tsx` | AC6 — "opera no escuro" + "critérios documentados" |
| `frontend/app/components/landing/FinalCTA.tsx` | AC7 — trust indicators near CTA |
| `frontend/app/components/landing/HeroSection.tsx` | AC7 — trust indicators below stats |
| `frontend/app/features/page.tsx` | AC8 — seção transparência de critérios |
| `frontend/app/page.tsx` | Import + placement do TrustCriteria |
| `frontend/lib/copy/valueProps.ts` | trustCriteria copy section |
| `frontend/__tests__/landing/BeforeAfter.test.tsx` | Updated assertions for new copy |
| `frontend/__tests__/landing/OpportunityCost.test.tsx` | Updated + new AC6 test |

## Notas de Implementação

- Os "critérios objetivos" referidos na copy são reais (keyword matching, value range, UF, modalidade, viability)
- Não revelar detalhes de implementação (LLM arbiter, GPT-4.1-nano) — linguagem acessível
- Percentuais de descarte podem ser estimados (ex: "70-90% dos editais são irrelevantes para qualquer setor específico")
- Manter copy library (`valueProps.ts`) como fonte centralizada

## Definition of Done

- [x] ACs 1-9 verificados
- [x] Narrativa de confiança coerente ao longo da página
- [x] Commit: `feat(frontend): GTM-COPY-004 — elementos de segurança na decisão`
