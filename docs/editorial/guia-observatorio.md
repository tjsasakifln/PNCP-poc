# Guia do Observatório — Escrita de Insights Mensais

Instruções para o fundador (Tiago Sasaki) escrever os textos interpretativos de cada relatório mensal do Observatório.

---

## Estrutura Obrigatória de Cada Insight

**Dado → Contexto → Implicação**

1. **Dado:** número exato, período, escopo geográfico
2. **Contexto:** o que está por trás desse número (sazonalidade, política pública, evento, lei)
3. **Implicação:** o que isso significa para quem compra do governo

---

## Exemplo: Correto

> São Paulo publicou 3.421 editais em março — 22% acima de fevereiro. O crescimento concentrou-se em obras de infraestrutura (41% do total), alinhado ao calendário do programa estadual de recuperação urbana. Fornecedores de engenharia e construção têm janela de 8 semanas para montagem de portfólio.

**Por que funciona:** número + comparação + causa + ação.

---

## Exemplo: Errado

> É importante ressaltar que o estado de São Paulo apresentou um aumento significativo no volume de licitações no contexto atual, o que evidencia o dinamismo do setor público brasileiro.

**Por que não funciona:** zero dado, zero período, zero implicação, três termos proibidos.

---

## Checklist de Cada Insight (máx. 50 palavras)

- [ ] Tem número específico?
- [ ] Tem comparação (vs. mês anterior, vs. mesma UF, vs. média nacional)?
- [ ] Tem interpretação do dado (por que aconteceu)?
- [ ] Tem menos de 50 palavras?
- [ ] Passou no lint de termos proibidos?

---

## Headlines do Relatório

O headline principal deve conter **o fato mais impactante do período**, com número.

Correto: "Brasil registrou 47.231 editais em março — maior volume em 18 meses"
Errado: "Mercado de licitações mostra crescimento expressivo em março de 2026"

---

## Seções Padrão do Relatório Mensal

### 1. Headline (1 frase, dado + impacto)
### 2. Panorama Nacional (3–4 parágrafos, 1 por dimensão principal)
### 3. Setores em Alta (lista dos 3 setores com maior crescimento %, dado + causa)
### 4. Estados em Destaque (top 3 por volume, com variação mensal)
### 5. Modalidades (distribuição %, com foco no pregão eletrônico)
### 6. Para Fornecedores (2–3 ações concretas baseadas nos dados do mês)
### 7. Metodologia (parágrafo de 3 linhas, linguagem acessível)

---

## Datas e Períodos

- Sempre "março de 2026" — nunca "03/2026"
- "1º trimestre de 2026" — nunca "Q1/2026"
- "nos últimos 30 dias" — nunca "recentemente"
- "de janeiro a março de 2026" — nunca "no período analisado"

---

## Fontes e Atribuição

Cada dado precisa de fonte:
- `Fonte: SmartLic Observatório — dados PNCP` (para dados do datalake)
- Período: `Editais publicados de 1 a 31 de março de 2026`
- Metodologia referenciada no rodapé: `/observatorio/metodologia`

---

## Aprovação Antes de Publicar

1. Rodar `node scripts/lint-text.js` — deve passar sem erros
2. Ler o relatório inteiro em voz alta
3. Conferir checklist em `docs/editorial/checklist-publicacao.md`
4. Assinar o campo "Aprovado?" no checklist
5. Só depois: publicar e ativar o relatório na página do Observatório
