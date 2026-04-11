# Guia de Estilo Editorial — SmartLic

Documento de referência para todo conteúdo público do SmartLic: páginas programáticas, Observatório, blog, tooltips, descrições de gráficos, emails e textos de UI.

**Versão:** 1.0 | **Aprovado por:** Fundador | **Data:** Abril 2026

---

## 1. Princípio Fundamental

Todo texto público do SmartLic segue a estrutura: **dado → contexto → implicação.**

Correto: "São Paulo publicou 3.421 editais em março — 22% acima de fevereiro. O crescimento concentrou-se em obras de infraestrutura (41% do total), alinhado ao calendário do programa estadual de recuperação urbana."

Errado: "É importante ressaltar que o estado de São Paulo apresentou um aumento significativo no volume de licitações no contexto atual."

---

## 2. Termos Proibidos

Estes termos revelam geração automática de texto e destroem credibilidade editorial:

| Termo proibido | Substituição obrigatória |
|----------------|--------------------------|
| `é importante notar` | Omitir ou afirmar diretamente |
| `é importante ressaltar` | Omitir ou afirmar diretamente |
| `é importante destacar` | Omitir ou afirmar diretamente |
| `vale ressaltar` | Omitir ou afirmar diretamente |
| `fica evidente que` | Citar o dado que evidencia |
| `no contexto atual` | Especificar: "em março de 2026" |
| `de forma significativa` | Dar o número: "alta de 34%" |
| `de maneira abrangente` | Eliminar ou reescrever com especificidade |
| `robusto` (sentido abstrato) | "com 40 mil+ registros" |
| `ao longo do tempo` | Especificar o período: "nos últimos 12 meses" |
| `é fundamental` | Omitir ou reescrever como afirmação |
| `em suma` / `em resumo` | Ir direto à conclusão |
| `cabe mencionar` | Mencionar diretamente |
| `tendo em vista` | "Como", "Porque", "Dado que" |
| `no que diz respeito a` | "Sobre", "Em" |
| `apresentou um aumento` | "[Sujeito] cresceu X%" |
| `verificou-se que` | "[Dado] mostra que" |
| `de forma expressiva` | Dar o número |
| `notável crescimento` | "crescimento de X%" |
| `evidencia-se` | Omitir ou citar o dado |
| `conforme mencionado` | Omitir ou repetir o fato brevemente |

---

## 3. Padrão Obrigatório

### Estrutura da frase
- **Sujeito + verbo + dado concreto.** Nunca frase sem dado verificável.
- Máximo 25 palavras por frase (regra jornalística).
- Máximo 4 frases por parágrafo.

### Números
- Valores monetários: `R$ 1.234.567,89` (ponto de milhar, vírgula decimal)
- Percentuais: `34%` (sem espaço)
- Contagens: `2.847 editais` (ponto de milhar)
- Scores: `72,4 pontos` (1 decimal)
- Datas por extenso: "março de 2026" (nunca "03/2026" ou "2026-03" em texto corrido)

### Municípios
- Usar nome oficial IBGE: "São Paulo" (não "SP Capital"), "Belo Horizonte" (não "BH")
- Acentuação: Acordo Ortográfico 2009 vigente

### Palavras com acentuação frequentemente esquecida
`município`, `licitação`, `públicas`, `índice`, `análise`, `período`, `seção`, `número`, `título`, `órgão`, `modalidade`, `habilitação`, `contratação`, `edição`

---

## 4. Voz e Tom

**Voz:** Especialista prático. Análise sem jargão.
**Tom:** Direto, factual, sem marketing.

Correto: "Pregão eletrônico concentrou 73% dos editais — mesma proporção de fevereiro."
Errado: "O pregão eletrônico demonstra ser a modalidade mais robusta e abrangente do ecossistema de compras públicas."

---

## 5. Textos Gerados por Código

Textos construídos por templates (Observatório, Índice Municipal, gráficos):

- **Nunca texto livre de LLM em conteúdo público.** Concatenação de variáveis sobre base aprovada pelo fundador.
- Template base escrito e aprovado por humano antes de qualquer publicação.
- Variáveis dinâmicas: apenas dados (números, nomes, datas) — nunca texto livre.

Exemplo válido de template:
```
"{Município} ({UF}) obteve {score} pontos no Índice de Transparência SmartLic — {período}.
O município ocupa a {ranking}ª posição entre os {total} avaliados, no {percentil}º percentil nacional."
```

---

## 6. Fontes e Atribuição

Todo dado publicado precisa de fonte explícita:
- `Fonte: SmartLic Observatório — dados PNCP`
- `Dados: PNCP, processados pelo SmartLic`
- Período sempre especificado: "março de 2026" ou "1º trimestre de 2026"

---

## 7. Revisão Humana Obrigatória

**Nenhuma página pública vai ao ar sem o fundador ter lido do início ao fim e aprovado.**

Isso se aplica a:
- Cada relatório do Observatório
- Cada página do Índice Municipal antes do primeiro pitch para imprensa
- Qualquer conteúdo novo em `/observatorio`, `/indice-municipal`, blog editorial

O checklist de publicação está em `docs/editorial/checklist-publicacao.md`.
