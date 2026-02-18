# GTM-RESILIENCE-D04 — Viability Assessment Separado de Relevância

| Campo | Valor |
|-------|-------|
| **Track** | D — Classificação de Precisao |
| **Prioridade** | P1 |
| **Sprint** | 4 |
| **Estimativa** | 6-8 horas (backend 4h + frontend 2h + testes 2h) |
| **Gaps Endereçados** | CL-03 |
| **Dependências** | GTM-RESILIENCE-D02 (confidence_score no pipeline) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

O pipeline atual classifica licitações em uma unica dimensão: "relevante" ou "nao relevante" para o setor. Mas "relevante" nao significa "viável para o usuario". Uma licitação de uniformes em Roraima (RR) e perfeitamente relevante para o setor de vestuário, mas pode ser completamente inviável para uma empresa baseada em Sao Paulo sem logística para a região Norte.

**O usuario percebe licitações relevantes-mas-inviáveis como falsos positivos**, degradando a confiança no produto.

### Dimensões de viabilidade ausentes:

| Dimensão | Exemplo de Inviabilidade | Status Atual |
|----------|--------------------------|--------------|
| **Modalidade** | Dispensa de valor <R$50k vs Pregão Eletrônico | Nao avaliado |
| **Status/Timeline** | Encerrada ontem vs abertura em 30 dias | Parcialmente (filtro de status) |
| **Valor** | R$500 (muito pequeno) vs R$5M (adequado) | Parcialmente (filtro de range) |
| **Geografia** | UF distante sem presença do usuario | Nao avaliado |
| **Competição** | Pregão nacional com 50+ fornecedores | Nao avaliado |

### Diferença conceitual:

```
RELEVÂNCIA: "Este contrato e sobre uniformes?"     → SIM (classificação correta)
VIABILIDADE: "Minha empresa consegue competir?"    → TALVEZ (depende de capacidade/região)
```

Sao dimensões ortogonais. Um contrato pode ser altamente relevante e completamente inviável (e vice-versa, em cenários mais raros).

## Problema

A ausência de viability assessment faz com que o usuario veja licitações que, apesar de corretamente classificadas como do setor, nao sao oportunidades reais para sua empresa. Isso cria "noise" nos resultados — o usuario precisa manualmente avaliar viabilidade para cada item, o que e trabalhoso e degrada a percepção de valor do produto.

## Solução

Implementar um scoring de viabilidade independente da relevância, calculado com base em fatores determinísticos (modalidade, valor, status, timeline) e fatores configuráveis por usuario (UFs de atuação, capacidade de valor). Exibir como indicador separado no frontend.

### Modelo de scoring:

```
viability_score = (
    modalidade_score * 0.30 +     # Pregão eletrônico = melhor
    timeline_score * 0.25 +        # Mais dias até fechamento = melhor
    value_fit_score * 0.25 +       # Valor no range do usuário = melhor
    geography_score * 0.20          # UF próxima ao usuário = melhor
)
```

Resultado: 0-100, mapeado para faixas: Alta (>70), Media (40-70), Baixa (<40).

---

## Acceptance Criteria

### AC1 — Modelo de Viabilidade
- [ ] Nova classe `ViabilityAssessment` em `viability.py` (novo modulo)
- [ ] Campos: `viability_score` (int 0-100), `viability_level` (Literal["alta", "media", "baixa"]), `factors` (dict com breakdown por fator)
- [ ] Score composto por 4 fatores com pesos configuráveis
- [ ] Mapeamento de faixas: alta >70, media 40-70, baixa <40

### AC2 — Fator: Modalidade (peso 0.30)
- [ ] Pregão Eletrônico (mod 6): score 100 (mais acessível, menor barreira)
- [ ] Pregão Presencial (mod 7): score 80
- [ ] Concorrência Eletrônica (mod 4): score 70
- [ ] Concorrência Presencial (mod 5): score 60
- [ ] Dispensa (mod 8): score 40 (valor geralmente baixo, menos competitivo)
- [ ] Credenciamento (mod 12): score 50 (nao competitivo, por adesão)
- [ ] Outros: score 50 (default)
- [ ] Scores de modalidade configuráveis em `viability_config` section de `sectors_data.yaml` ou config standalone

### AC3 — Fator: Timeline (peso 0.25)
- [ ] Se `data_abertura` > 14 dias no futuro: score 100 (tempo de sobra)
- [ ] Se `data_abertura` entre 7-14 dias: score 80
- [ ] Se `data_abertura` entre 3-7 dias: score 60
- [ ] Se `data_abertura` entre 1-3 dias: score 30 (urgente)
- [ ] Se `data_abertura` ja passou (encerrada): score 10
- [ ] Se `data_abertura` nao disponível: score 50 (neutro)
- [ ] Calculo usa `datetime.now(timezone.utc)` (timezone-aware, lição do GTM-FIX-031)

### AC4 — Fator: Value Fit (peso 0.25)
- [ ] Score baseado na proximidade do valor estimado com o range ideal do setor
- [ ] Setor "vestuario" range ideal: R$50k - R$2M
- [ ] Valor dentro do range: score 100
- [ ] Valor entre 50-100% do min ou 100-200% do max: score 60
- [ ] Valor abaixo de 50% do min ou acima de 200% do max: score 20
- [ ] Valor nao informado (R$0): score 40 (nao penalizar excessivamente — PCP v2 nao tem valor)
- [ ] Ranges configuráveis por setor em `sectors_data.yaml` (campo `viability_value_range`)

### AC5 — Fator: Geografia (peso 0.20)
- [ ] Score baseado na proximidade entre UF da licitação e UFs de atuação do usuario
- [ ] Se UF da licitação esta nas UFs selecionadas na busca: score 100 (usuario ja demonstrou interesse)
- [ ] Se UF adjacente (região geográfica): score 60
- [ ] Se UF distante (outra região): score 30
- [ ] Se UF nao identificada: score 50 (neutro)
- [ ] Mapa de adjacência por macroregião (5 regiões + DF): `REGION_MAP` hardcoded no modulo
- [ ] Para v1: usar UFs da busca como proxy de "UFs de atuação" (sem perfil de usuario ainda)

### AC6 — Independência da Relevância
- [ ] Viability score e calculado SOMENTE para bids que passaram o filtro de relevância (aceitas)
- [ ] Viability score NAO altera a decisão de relevância (nao rejeita bids relevantes com viabilidade baixa)
- [ ] Viability score e informativo (para ranking e UI), nao eliminatório
- [ ] Os dois scores sao retornados como campos separados: `confidence_score` (relevância) e `viability_score` (viabilidade)

### AC7 — Integração no Pipeline
- [ ] Viability assessment executa DEPOIS de todos os filtros de relevância, ANTES do re-ranking
- [ ] Posição: Stage 4.5 (entre filtragem e enrichment/sort)
- [ ] Execução: síncrona, sem chamadas externas (puro cálculo), <1ms por bid
- [ ] Nao altera o tempo de busca perceptivelmente

### AC8 — Frontend: Indicadores Visuais
- [ ] Novo componente `ViabilityBadge` que mostra: "Alta" (verde), "Media" (amarelo), "Baixa" (cinza)
- [ ] Badge exibido ao lado do badge de relevância existente ("Palavra-chave" / "Validado por IA")
- [ ] Tooltip no badge mostra breakdown dos fatores: "Modalidade: Pregão (ótimo) | Prazo: 12 dias (bom) | Valor: R$180k (ideal) | UF: SP (sua região)"
- [ ] Layout responsivo: badges empilham em mobile (<768px)
- [ ] Cores consistentes com design system existente (Tailwind)

### AC9 — Ordenação Composta
- [ ] Quando viability assessment ativo, sorting usa formula composta:
  `combined_score = confidence_score * 0.6 + viability_score * 0.4`
- [ ] Resultados ordenados por `combined_score` DESC
- [ ] Usuario pode clicar header "Relevância" ou "Viabilidade" para ordenar por dimensão única (futuro — nao implementar sort UI nesta story)

### AC10 — Feature Flag e Config
- [ ] `VIABILITY_ASSESSMENT_ENABLED` env var (default `false` — opt-in para Sprint 4)
- [ ] Quando `false`, pipeline nao calcula viability, campo ausente no response
- [ ] Pesos dos fatores configuráveis via env vars: `VIABILITY_WEIGHT_MODALITY=0.30`, etc.
- [ ] Flag adicionada ao `_FEATURE_FLAG_REGISTRY`

### AC11 — Testes
- [ ] Teste unitário: Pregão Eletrônico score modalidade = 100
- [ ] Teste unitário: Dispensa score modalidade = 40
- [ ] Teste unitário: data_abertura em 20 dias = timeline score 100
- [ ] Teste unitário: data_abertura ontem = timeline score 10
- [ ] Teste unitário: valor R$100k para vestuario (dentro do range) = value_fit score 100
- [ ] Teste unitário: valor R$10k para vestuario (abaixo do range) = value_fit score <=60
- [ ] Teste unitário: UF da busca = UF da licitação = geography score 100
- [ ] Teste unitário: UF distante = geography score 30
- [ ] Teste unitário: viability nao altera decisão de relevância
- [ ] Teste unitário: combined_score ordena corretamente
- [ ] Teste frontend: ViabilityBadge renderiza "Alta" em verde
- [ ] Teste frontend: tooltip mostra breakdown dos fatores

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/viability.py` | **NOVO** — modelo ViabilityAssessment, cálculo dos 4 fatores, REGION_MAP |
| `backend/search_pipeline.py` | Integração do viability assessment no Stage 4.5 |
| `backend/sectors_data.yaml` | Novo campo `viability_value_range` por setor |
| `backend/schemas.py` | Campos `viability_score`, `viability_level`, `viability_factors` no response |
| `backend/config.py` | `VIABILITY_ASSESSMENT_ENABLED`, pesos dos fatores |
| `frontend/app/buscar/components/ViabilityBadge.tsx` | **NOVO** — componente visual |
| `frontend/app/buscar/page.tsx` | Integração do ViabilityBadge nos cards de resultado |
| `backend/tests/test_viability.py` | **NOVO** — testes unitários (10+) |
| `frontend/__tests__/viability-badge.test.tsx` | **NOVO** — testes do componente |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Pesos dos fatores nao refletem preferência real | Alta | Medio | Pesos configuráveis via env var + user feedback (D-05) |
| Geography score impreciso sem perfil do usuario | Media | Baixo | v1 usa UFs da busca como proxy; perfil completo em sprint futuro |
| Complexidade visual (2 badges) confunde usuario | Media | Medio | Tooltip explicativo + user testing |
| Value fit penaliza licitações PCP (valor=0) | Media | Baixo | Score 40 (neutro-baixo) para valor nao informado |

---

## Definition of Done

- [ ] Todos os 11 ACs verificados e passando
- [ ] Nenhuma regressão nos testes existentes
- [ ] Coverage do novo modulo >= 80%
- [ ] Performance: viability calc <1ms por bid no p95
- [ ] Feature flag permite ativar/desativar sem deploy
- [ ] Frontend renderiza corretamente em desktop e mobile
- [ ] Code review aprovado por @architect e @ux-design-expert
