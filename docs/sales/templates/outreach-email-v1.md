# Outreach Email v1 — POV direto (SmartLic × B2G qualificado)

**Modelo:** Perspective of Value (POV). Direto ao ponto, referencia histórico
proprietário, promete próximo micro-passo leve (lista de editais).

**Quando usar:** primeiro contato frio com CNPJ identificado no DataLake como
ativo em licitações nos últimos 90 dias, com fit claro em 1-2 setores
SmartLic.

**Placeholders a preencher manualmente com dados do brief `b2g_lead_brief.py`:**

- `{nome}` — nome do tomador de decisão (pesquisar em LinkedIn; se não achar,
  usar "prezados" — mas personalização 1:1 dobra response rate)
- `{razao_social}` — razão social da empresa
- `{X_contratos}` — participações 90d (do CSV)
- `{Y_valor}` — volume 90d formatado em BRL
- `{Z_dias_desde_ultimo}` — dias desde o último contrato (do brief)
- `{setor_principal}` — setor SmartLic inferido do objeto
- `{N_editais}` — número de editais abertos no brief para esta UF/setor
- `{cidade_uf}` — cidade/UF

---

## Assunto

```
{razao_social} — {N_editais} editais abertos em {setor_principal} hoje
```

## Corpo

```
{nome},

Notei que a {razao_social} assinou {X_contratos} contratos nos últimos 90 dias
em {setor_principal}, somando {Y_valor}. O último foi há cerca de
{Z_dias_desde_ultimo} dias.

Mapeamos no SmartLic (ferramenta que desenvolvi para analisar PNCP + ComprasGov
com IA) {N_editais} editais abertos agora em {cidade_uf}/região com fit direto
para o perfil de vocês — com análise de viabilidade individual (modalidade,
prazo, valor, geografia).

Posso enviar a lista dos {N_editais} editais com a análise em PDF? Leva 5 min
de leitura e me dá 5 min do seu tempo para saber se faz sentido continuar.

Tiago Sasaki
Fundador, SmartLic
https://smartlic.tech

---
Você recebeu este email porque identificamos fit comercial com o perfil da
{razao_social} no PNCP. Para não receber mais, responda UNSUBSCRIBE.
```

---

## Notas operacionais

- **Não** anexar a lista no primeiro email. O objetivo é resposta "sim", não
  consumir o atrativo antes da conversa.
- Se responderem "sim", enviar brief `.md` renderizado do `b2g_lead_brief.py`
  com o PDF gerado via `proposta-b2g` ou manualmente.
- Follow-up D+3 se silêncio: 1 linha única, "Fica aberto — avisa se fizer
  sentido depois".

---

## A/B contra v2 (consultivo)

Rodar v1 e v2 em cohorts paralelas de 15 contatos cada. Meta W3: response rate
≥ 15% (qualquer variante). Se v1 < 10% e v2 ≥ 15%, pivotar outreach para v2.
