# /proposta-b2g — Gerador de Proposta Comercial B2G

## Purpose

Gera um PDF de proposta comercial personalizada para um lead B2G de QUALQUER setor. A proposta apresenta o SERVICO de consultoria em licitacoes — o que sera entregue apos a contratacao. NAO busca editais, NAO analisa oportunidades, NAO apresenta metricas de mercado.

**Output:** `docs/propostas/proposta-{CNPJ}-{slug}-{YYYY-MM-DD}.pdf`

---

## REGRAS CRITICAS (ler antes de executar)

1. **NAO buscar editais** — a proposta nao consulta PNCP nem qualquer API de editais
2. **NAO apresentar metricas de mercado** — zero volumes, zero valores agregados, zero "R$ X bilhoes"
3. **NAO listar oportunidades abertas** — a proposta VENDE o servico, nao FAZ o monitoramento
4. **NAO citar numero de fontes** — nunca "3 fontes", "PNCP + PCP + ComprasGov". Usar "monitoramento continuo das publicacoes oficiais"
5. **NAO citar nomes de APIs ou portais** nas secoes voltadas ao cliente
6. **NAO usar termos de construcao/engenharia** em textos genericos
7. **NAO referenciar cargo publico especifico ou UF do consultor** — autoridade e generica
8. **Delegar coleta de dados ao script** — `python scripts/build-proposta-data.py {CNPJ}`
9. **Delegar geracao PDF ao script** — `python scripts/generate-proposta-pdf.py --input {json} --output {pdf}`

---

## Execucao (2 passos)

### Passo 1: Gerar JSON de dados (perfil empresa + setor)

```bash
CNPJ_LIMPO=$(echo "{CNPJ}" | tr -d './-')
python scripts/build-proposta-data.py ${CNPJ_LIMPO} --pacote semanal
```

O script coleta APENAS:
- Perfil da empresa (BrasilAPI)
- Deteccao de setor via CNAE
- UFs de abrangencia (vizinhas da sede)
- Salva em `docs/propostas/data-{CNPJ}-{YYYY-MM-DD}.json`

### Passo 2: Gerar PDF

```bash
python scripts/generate-proposta-pdf.py \
  --input docs/propostas/data-{CNPJ}-{YYYY-MM-DD}.json \
  --output docs/propostas/proposta-{CNPJ}-{slug}-{YYYY-MM-DD}.pdf \
  --pacote semanal
```

Pronto. Nao ha mais passos.

---

## Pacotes

| Pacote | Preco | Freq | UFs | Suporte |
|--------|-------|------|-----|---------|
| Mensal | R$997/mes | 1x/mes | UF sede | Comercial |
| **Semanal (Rec.)** | R$1.500/mes | 4x sem + 1x mes | sede + limitrofes | Estendido |
| Diario | R$2.997/mes | diario + sem + mes | sede + 4 UFs | Dedicado |

Desconto anual: pague 10, leve 12.

---

## Estrutura do PDF (8 secoes)

1. **Capa** — data, validade 15 dias, CNPJ, nome
2. **Carta ao Decisor** — setor-agnostica, foco no servico
3. **Diagnostico da Empresa** — dados cadastrais, pontos fortes (sem historico de contratos)
4. **O Que Nosso Trabalho Entrega** — processo de analise (6 etapas), entregaveis, diferenciais do servico
5. **Por Que Monitoramento Continuo** — COM vs SEM, logica do retorno (generico)
6. **Pacotes de Monitoramento** — 3 tiers com UFs dinamicas
7. **Quem Analisa Seus Editais** — autoridade generica, tecnologia, diferenciais
8. **Condicoes Comerciais + Proximos Passos** — preco, oferta, CTA

---

## Suppressions (NUNCA incluir)

- Editais individuais com datas, objetos, orgaos ou links
- Historico de contratos ou faturamento governamental
- Metricas de mercado (volume, valor total, distribuicao)
- Numero de fontes de dados ("3 fontes", nomes de APIs)
- Cargo publico especifico (ex: "engenheiro da SIE/SC")
- Hardcoding de UFs (ex: "SC+PR+RS")
- Termos de construcao civil em textos genericos
- Qualquer dado que sugira busca de editais reais

## Quality Gate (automatico)

O script `build-proposta-data.py` valida:
- Razao social encontrada
- CNAE detectado para setor especifico
- Situacao cadastral ATIVA
- Dados minimos presentes

---

## Params

$ARGUMENTS
