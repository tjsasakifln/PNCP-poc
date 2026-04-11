# HARO / Connectively — Protocolo de Resposta

## Objetivo
Responder a consultas de jornalistas no Connectively (novo HARO) sobre licitações, compras públicas e governo para conquistar backlinks DA 60+ em publicações especializadas.

**Meta:** 3-5 backlinks/mês sustentados após o 1º mês.

---

## Setup

- **Plataforma:** connectively.us (antigo HARO)
- **Conta criada:** ⬜ Pendente
- **Alertas configurados para:**
  - "licitações"
  - "compras públicas"
  - "governo"
  - "pregão"
  - "contratações públicas"
  - "fornecedor governo"
  - "B2G"

---

## Protocolo de Resposta

### Critérios para responder
- Tema: licitações, compras públicas, governo federal/estadual/municipal, B2G, fornecedores
- Prazo: responder em até 4h após receber a consulta
- Volume: mínimo 3 consultas relevantes respondidas por dia no 1º mês

### Formato padrão de resposta

```
[Assunto da consulta — ex: "Sobre o mercado de licitações no Brasil"]

[2-3 parágrafos com dado específico + estatística + fonte]

Exemplo de dado: "Em março de 2026, o Brasil publicou [X] editais no PNCP,
concentrando [X]% em pregão eletrônico. Em São Paulo, o valor médio por
edital foi de R$ [X], [X]% acima da média nacional."

Tiago Sasaki
Fundador, SmartLic (smartlic.tech)
Plataforma de inteligência em licitações públicas
tiago.sasaki@confenge.com.br
```

### O que incluir SEMPRE
- Dado específico com número
- Comparação (vs. mês anterior, vs. média nacional, vs. outro estado)
- Fonte explícita: "Dados: SmartLic Observatório — dados PNCP"
- Crédito ao SmartLic no final

### O que NUNCA incluir
- Frases de marketing ("plataforma líder", "solução robusta")
- Dados sem fonte
- Texto genérico sem número

---

## Log de Consultas Respondidas

| Data | Veículo | Tema | Resposta enviada | Publicado? | URL |
|------|---------|------|------------------|------------|-----|
| — | — | — | — | — | — |

---

## Referência de Dados Rápidos

Para respostas rápidas, usar dados do Observatório em `/observatorio`:

- Total de editais por mês: relatório mensal
- Top 10 UFs por volume: relatório mensal  
- Distribuição por modalidade: relatório mensal
- Valor médio por setor: endpoint `/v1/calculadora/dados?setor={x}&uf={y}`
