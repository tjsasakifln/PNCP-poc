# /pricing-b2g — Inteligência de Preços B2G

## Purpose

Analisa TODOS os contratos homologados no PNCP para um objeto/setor específico e calcula a distribuição estatística de preços reais praticados. Responde com precisão cirúrgica à pergunta mais importante do cliente: "quanto eu deveria ofertar?"

**Output primário:** `docs/pricing/pricing-{objeto_slug}-{YYYY-MM-DD}.md` (relatório de preços)
**Output secundário:** `docs/pricing/pricing-{objeto_slug}-{YYYY-MM-DD}.xlsx` (dados brutos + análise)

---

## Usage

```
/pricing-b2g "serviço de limpeza hospitalar"
/pricing-b2g "pavimentação asfáltica" --uf SP,MG,PR
/pricing-b2g "medicamentos" --setor medicamentos
/pricing-b2g "manutenção predial" --meses 24 --modalidade 5
/pricing-b2g --edital 80869886000143/2026/10           # preço para edital específico
/pricing-b2g "uniformes" --cnpj 12345678000190         # contextualizado para um cliente
```

## What It Does

### Phase 1: Coleta de Contratos Homologados (@data-engineer)

**Objetivo:** Buscar o MAIOR volume possível de contratos SIMILARES já homologados (preço real pago, não estimado).

**1a. PNCP — Contratos por keywords**

```bash
# Buscar contratações com valorTotalHomologado (preço real pago pelo governo)
# Período: últimos 12-24 meses (--meses)
# Todas as UFs (ou filtro por --uf)
curl -s "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao\
  ?dataInicial={N_meses_atras_YYYYMMDD}\
  &dataFinal={hoje_YYYYMMDD}\
  &codigoModalidadeContratacao={modalidade}\
  &pagina=1&tamanhoPagina=50"
```

- Paginar extensivamente (max 20 páginas por modalidade) — queremos VOLUME
- Filtrar por keywords do objeto no campo `objetoCompra`
- Para cada resultado, verificar se `valorTotalHomologado` está preenchido (contrato efetivado)
- Se `valorTotalHomologado` é null, usar `valorTotalEstimado` como fallback (marcado como "estimado")
- Filtrar por UF se `--uf` informado
- Modalidades: 4 (Concorrência), 5 (Pregão Eletrônico), 6 (Pregão Presencial), 8 (Inexigibilidade)

**1b. Enriquecimento — Itens do contrato (quando disponível)**

```bash
# Para contratos relevantes, buscar itens individuais
curl -s "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj_orgao}/compras/{ano}/{seq}/itens"
```

- Extrair preços unitários quando disponíveis
- Permite análise de preço por item (não apenas por contrato total)
- Priorizar: top 20 contratos mais recentes e mais similares

**1c. Se `--edital` fornecido — contexto específico**

- Buscar dados do edital via PNCP API
- Baixar PDF do edital e extrair: valor estimado, quantitativos, especificações
- Buscar contratos anteriores do MESMO ÓRGÃO para objetos similares
- Buscar contratos do MESMO OBJETO em outros órgãos

### Phase 2: Limpeza e Normalização (@data-engineer)

**2a. Filtragem de outliers**
- Remover contratos com valor R$0 ou null
- Remover contratos com valor >10x a mediana (provável erro de registro)
- Remover contratos com valor <0.1x a mediana (provável registro parcial)
- Flag contratos de inexigibilidade (preço pode ser inflado por falta de competição)

**2b. Normalização**
- Ajustar por inflação (IPCA) se período >12 meses — trazer todos a valores de hoje
- Quando possível, normalizar por unidade (preço/m², preço/un, preço/mês)
- Separar por modalidade (pregão tende a ter preço menor que concorrência)
- Separar por porte do órgão (federal/estadual/municipal)

**2c. Classificação de similaridade**
Para cada contrato encontrado, calcular similaridade com o objeto alvo:

| Critério | Peso | Score |
|----------|------|-------|
| Keywords match no objeto | 40% | % de keywords presentes |
| Mesma modalidade | 20% | 100% se igual, 50% se diferente |
| Mesma UF | 15% | 100% se igual, 70% se região, 50% se diferente |
| Período recente | 15% | 100% se <6m, 70% se 6-12m, 50% se 12-24m |
| Mesmo órgão | 10% | 100% se igual, 0% se diferente |

Ordenar contratos por similaridade score e usar os top N para estatísticas.

### Phase 3: Análise Estatística (@analyst)

**3a. Distribuição de preços**

| Métrica | Cálculo | O que significa |
|---------|---------|-----------------|
| **N (amostra)** | COUNT de contratos válidos | Confiabilidade da análise |
| **Mediana** | P50 dos valores homologados | Preço "típico" — melhor que média (menos sensível a outliers) |
| **P25 (1º quartil)** | 25% dos contratos abaixo deste valor | Preço agressivo — competitivo mas viável |
| **P75 (3º quartil)** | 75% dos contratos abaixo deste valor | Preço conservador — margem confortável |
| **P10** | 10% abaixo | Piso do mercado — abaixo disso é inexequível |
| **P90** | 90% abaixo | Teto do mercado — acima disso perde |
| **Média** | Média aritmética | Referência, mas distorcida por outliers |
| **Desvio padrão** | Dispersão | Mercado fragmentado (alto) vs consolidado (baixo) |
| **Coeficiente de variação** | DP / Média × 100 | <30% = mercado previsível, >50% = mercado volátil |

**3b. Desconto médio sobre valor estimado**

```
Desconto_medio = (Valor_estimado - Valor_homologado) / Valor_estimado × 100
```

| Faixa de desconto | Interpretação |
|-------------------|---------------|
| 0-10% | Baixa competição — poucos licitantes |
| 10-25% | Competição moderada — mercado saudável |
| 25-40% | Alta competição — preço é fator decisivo |
| >40% | Competição predatória — risco de inexequibilidade |

Calcular por modalidade (pregão geralmente tem desconto maior que concorrência).

**3c. Análise temporal**
- Preços estão subindo, caindo ou estáveis nos últimos 12 meses?
- Sazonalidade? (ex: material escolar mais caro em janeiro)
- Impacto de inflação vs dinâmica competitiva

**3d. Análise geográfica**
- Preço médio por UF (custos regionais variam muito)
- UFs com preços mais baixos vs mais altos
- Impacto da distância (frete, logística)

**3e. Análise por porte do órgão**
- Federal vs Estadual vs Municipal — quem paga mais?
- Órgãos específicos que consistentemente pagam acima/abaixo da mediana

### Phase 4: Recomendação de Preço (@analyst)

**4a. Se `--edital` fornecido (edital específico):**

```markdown
## Recomendação de Preço — Edital {número}

**Valor estimado do edital:** R${valor} (ou "sigiloso")
**Análise baseada em:** {N} contratos similares (últimos {M} meses)

### Faixa de Preço Recomendada

| Estratégia | Valor Sugerido | Desconto sobre estimado | Probabilidade de ganhar |
|------------|:---:|:---:|:---:|
| **Agressivo** | R${P25} | {X}% | Alta (mas margem apertada) |
| **Competitivo** | R${mediana} | {X}% | Média-Alta |
| **Conservador** | R${P75} | {X}% | Média-Baixa (margem confortável) |

**Preço sugerido:** R${valor} (estratégia {X})

**Fundamentação:**
- Mediana do mercado para objetos similares: R${mediana}
- Desconto médio praticado neste órgão: {X}%
- Último contrato deste órgão para objeto similar: R${valor} em {data}
- Contratos mais recentes (3 meses): tendência de {subida/queda/estabilidade}

**Risco de inexequibilidade:** Se ofertar abaixo de R${P10}, há risco de ser questionado.
A Lei 14.133 define proposta inexequível como <75% do valor estimado (ou <50% da média das propostas).
```

**4b. Se consulta genérica (sem edital):**

Fornecer tabela de referência por UF/modalidade com percentis e recomendação geral.

**4c. Se `--cnpj` fornecido (contextualizado para cliente):**

Adicionar:
- Histórico de preços deste CNPJ (em que faixa ele normalmente oferta)
- Posição competitiva: ele geralmente oferta no P25? P50? P75?
- Recomendação ajustada ao perfil (se normalmente ganha no P30, sugerir P25-P35)

### Phase 5: Geração dos Outputs (@dev)

#### Relatório Markdown

```markdown
# Inteligência de Preços — {objeto}
**Data:** {data} | **Período:** {meses} meses | **Amostra:** {N} contratos

## Resumo Executivo
- Mediana do mercado: **R${valor}**
- Faixa recomendada: **R${P25} — R${P75}**
- Desconto médio sobre estimado: **{X}%**
- Tendência: **{subindo/caindo/estável}**

## Distribuição de Preços
[tabela com P10, P25, Mediana, P75, P90, Média, DP, CV]

## Preços por UF
[tabela: UF | N contratos | Mediana | P25 | P75]

## Preços por Modalidade
[tabela: Modalidade | N | Mediana | Desconto médio]

## Preços por Período
[tabela: Trimestre | N | Mediana | Tendência]

## Top 10 Contratos Mais Similares
[tabela: Órgão | UF | Objeto | Valor Homologado | Data | Similaridade]

## Recomendação
[seção 4a/4b/4c dependendo do uso]

---
Tiago Sasaki - Consultor de Licitações
(48)9 8834-4559
```

#### Planilha Excel — 4 abas

| Aba | Conteúdo |
|-----|----------|
| **Resumo** | Estatísticas + gráfico de distribuição + recomendação |
| **Dados Brutos** | Todos os contratos coletados (órgão, UF, valor, data, objeto, similaridade score) |
| **Análise por UF** | Pivot por UF com percentis |
| **Análise Temporal** | Pivot por trimestre com tendência |

## Regras de Confiabilidade

| N (amostra) | Confiabilidade | Ação |
|:-----------:|:--------------:|------|
| >50 | ALTA | Recomendação firme |
| 20-50 | MÉDIA | Recomendação com ressalva |
| 10-20 | BAIXA | "Amostra limitada — usar como referência, não como regra" |
| <10 | INSUFICIENTE | "Dados insuficientes para análise estatística confiável. Considerar pesquisa de mercado adicional." |

## Downstream

```
/radar-b2g                               → identifica edital quente
/pricing-b2g --edital {id}               → quanto ofertar neste edital
/war-room-b2g {edital}                   → prepara participação com preço definido
/proposta-b2g {CNPJ}                     → inclui ROI baseado em preços reais
```

## APIs Reference

| API | Endpoint | Uso |
|-----|----------|-----|
| PNCP Consulta | `/api/consulta/v1/contratacoes/publicacao` | Contratos homologados |
| PNCP Itens | `/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens` | Preços unitários |
| PNCP Arquivos | `/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos` | PDF do edital (se --edital) |
| PNCP Download | `/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{n}` | Download PDF |

## Params

$ARGUMENTS
