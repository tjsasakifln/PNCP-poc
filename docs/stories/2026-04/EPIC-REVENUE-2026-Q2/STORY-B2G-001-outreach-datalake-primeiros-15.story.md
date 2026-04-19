# STORY-B2G-001: Outreach B2G via DataLake — Primeiros 90 Contatos Qualificados

**Priority:** P0 — Caminho mais previsível para primeiro pagante em runway curto
**Effort:** S (tooling 2 dias) + Ongoing (12h/semana × 6 semanas)
**Squad:** @analyst (qualificação) + @dev (tooling inicial) + Founder (execução de contatos)
**Status:** Ready
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Sprint:** Wave Receita D+1 a D+45

---

## Contexto

SmartLic possui vantagem competitiva única: **dados proprietários** no DataLake Supabase (~2M contratos em `supplier_contracts` + ~50k licitações ativas em `pncp_raw_bids`). Competidores (BLL, ConLicitação, Instituto Licitar) não têm esse volume indexado nem a capacidade de usar como inteligência de aquisição.

Em runway <3 meses com zero pagantes, outreach outbound tem os maiores ROI e menor time-to-revenue:

- SEO: 3-6 meses para tração
- Paid ads: 1-7 dias para signal, mas CAC incerto
- **Outbound qualificado: 2-6 semanas** (contato → trial → pagante)

Esta story **não é primariamente técnica** — é operacional. A parte técnica (tooling, query, templates) tem ~2 dias. O resto é execução disciplinada em ritual diário pelo founder por 6 semanas.

**Impacto esperado:** 3-5 pagantes em D+45 (6-8% trial-to-paid em outbound qualificado é conservador).

---

## Acceptance Criteria

### AC1: Script de geração de lista qualificada
- [ ] `scripts/b2g_outreach_query.py` executa query Supabase e gera CSV timestamped `data/outreach/leads-2026-W{XX}.csv`
- [ ] Query selecionar top 50 CNPJs (fornecedores) que:
  - Participaram de ≥3 contratos nos últimos 90 dias em `supplier_contracts`
  - **Não** possuem conta no SmartLic (`profiles` join)
  - Volume contratual somado ≥ R$ 100k (filtro de qualificação)
  - CNAE dentro dos 15 setores ativos do SmartLic (`backend/sectors_data.yaml`)
- [ ] CSV com colunas: `cnpj`, `razao_social`, `participacoes_90d`, `volume_total_90d`, `top_3_setores`, `email_provavel`, `cidade_uf`
- [ ] `email_provavel` derivado do domínio da razão social via heurística (dominio + `contato@`, `comercial@`, `diretoria@`) — marcar como `PROVAVEL` no CSV
- [ ] Tempo de execução <30s com índice existente em `supplier_contracts(data_assinatura, cnpj_fornecedor)`

### AC2: Template de abordagem multi-canal
- [ ] `docs/sales/templates/outreach-email-v1.md` com placeholders: `{nome}`, `{razao_social}`, `{X_contratos}`, `{Y_valor}`, `{Z_dias_desde_ultimo}`, `{setor_principal}`, `{cidade_uf}`
- [ ] `docs/sales/templates/outreach-linkedin-v1.md` versão mais curta (limite 300 chars para InMail)
- [ ] Template segue modelo POV (Perspective of Value): "Identificamos que [empresa] teve X contratos em [setor] nos últimos 90 dias, totalizando R$ Y. Mapeamos [N] editais abertos agora que combinam com o histórico — quer ver?"
- [ ] Variantes A/B: template-v1 (direto) + template-v2 (consultivo/educacional)

### AC3: CRM lightweight para tracking
- [ ] `docs/sales/crm-pipeline.md` documenta estrutura: Airtable ou Notion com estágios `Prospectado → Contactado → Respondeu → Trial Iniciado → Proposta Enviada → Fechado → Churn`
- [ ] Campos por lead: CNPJ, nome, canal (email/LinkedIn), data_contato, resposta_sim/nao, trial_start_ts, deal_size_estimado, next_action
- [ ] Ritual semanal: toda sexta 17h, update de estágio + métricas agregadas

### AC4: Script de pré-processamento de lead (personalization at scale)
- [ ] `scripts/b2g_lead_brief.py` recebe CNPJ e gera `data/outreach/briefs/{cnpj}.md` com:
  - Resumo do fornecedor (razão social, CNAE principal, porte)
  - Top 5 contratos recentes com valores
  - Top 3 setores SmartLic com fit score
  - **3-5 editais abertos** relevantes (query ao `pncp_raw_bids` filtrado por setor + UF do CNPJ)
  - Sugestão de abordagem (hook específico baseado no histórico)
- [ ] Brief é colado como personalização quando founder envia email — reduz tempo de personalização de 15min para 3min por contato

### AC5: Meta operacional clara
- [ ] Cadência: **15 contatos qualificados/semana** × 6 semanas = **90 contatos**
- [ ] Distribuição por canal: 10 email + 5 LinkedIn
- [ ] Response rate alvo: ≥20% após 2 iterações do template (adaptar se <10% em W2)
- [ ] Trial-start rate alvo: ≥30% dos que respondem
- [ ] Trial-to-paid alvo: ≥20% (vs ~3% baseline — outbound qualificado converte mais)

### AC6: Case study post-primeiro-fechamento
- [ ] Ao fechar primeiro cliente B2G: documentar em `docs/sales/case-studies/{empresa}-2026-{mes}.md`
- [ ] Estrutura: problema, solução, resultado quantificado, quote do cliente (com permissão)
- [ ] Reuso: case study vira CTA em outreach wave 2 + landing `/casos`

### AC7: Relatório semanal automatizado
- [ ] `scripts/b2g_weekly_report.py` roda toda sexta e gera `docs/sales/reports/weekly-{YYYY-WXX}.md` com:
  - Contatos enviados esta semana (por canal)
  - Response rate semanal
  - Trials iniciados esta semana
  - Pipeline total por estágio
  - Bloqueadores identificados
- [ ] Report é fonte de decisão para ajuste de template/canal/segmento

### AC8: Compliance LGPD
- [ ] Emails incluem footer: "Você recebeu este email porque identificamos fit comercial. Para não receber mais, responda UNSUBSCRIBE." + link opt-out
- [ ] Lista de opt-outs persistida em `data/outreach/opt-outs.txt` (gitignored)
- [ ] Script AC1 filtra opt-outs automaticamente em runs futuros

---

## Arquivos

**Scripts (novos):**
- `scripts/b2g_outreach_query.py`
- `scripts/b2g_lead_brief.py`
- `scripts/b2g_weekly_report.py`

**Documentação (nova):**
- `docs/sales/templates/outreach-email-v1.md`
- `docs/sales/templates/outreach-email-v2.md`
- `docs/sales/templates/outreach-linkedin-v1.md`
- `docs/sales/crm-pipeline.md`
- `docs/sales/playbook.md` (runbook operacional)
- `docs/sales/case-studies/.gitkeep`
- `docs/sales/reports/.gitkeep`

**Data (gitignored, mas estrutura):**
- `data/outreach/.gitkeep`
- `data/outreach/briefs/.gitkeep`
- `data/outreach/opt-outs.txt` (vazio inicialmente)

**CI:**
- Nenhuma mudança — scripts standalone, não entram em pytest gate

---

## Métricas de Sucesso

- **Leading (medir semanalmente):**
  - Contatos enviados: meta 15/semana
  - Response rate: meta ≥20% na W3
  - Trials iniciados: meta 3-5/semana a partir de W3
- **Lagging (medir mensalmente):**
  - Trial-to-paid rate: meta ≥20% em W6
  - Revenue direto atribuído a B2G-001: meta ≥R$ 1.200 MRR em D+60

**Ritual:** 2h/dia (10h-12h BRT, janela comercial empresas) × 5 dias/semana = 10h + 2h review semanal = 12h/semana.

**Capacidade solo founder:** ≤12h/semana sustentável por 6 semanas. Se exceder, avaliar freelancer SDR pós-primeiro pagante (R$ 3-5k/mês variável).

---

## Riscos e Mitigações

**Risco 1:** Email corporativo inferido (contato@) bounce alto
- **Mitigação:** Usar hunter.io ou ferramenta grátis Apollo.io Free (50 contatos/mês) para email real quando possível

**Risco 2:** Response rate <10% em W3
- **Mitigação:** Iterar template — pivotar para abordagem educacional (artigo setorial gratuito como CTA) em vez de demo direta

**Risco 3:** Founder fadiga de outreach
- **Mitigação:** Time-boxing estrito (máx 2h/dia) + ritual documentado em `docs/sales/playbook.md`

**Risco 4:** Objeção "concorrente já temos" alta
- **Mitigação:** Copy destaca dado único (histórico de contratos de 2M, análise IA 15 setores) — não compete com radar genérico

---

## Definition of Done

- [ ] AC1-AC8 todos marcados `[x]`
- [ ] 3 scripts rodando localmente sem erros
- [ ] Primeiro CSV de leads gerado (≥40 leads qualificados)
- [ ] 15 contatos enviados na W1 (primeira semana pós-merge)
- [ ] Weekly report W1 gerado
- [ ] PR mergeado para `main` com scripts + docs
- [ ] Ritual semanal (sexta 17h) documentado no calendário do founder

---

## Dev Notes

**Query SQL exata (validar antes de script):**
```sql
WITH qualified AS (
  SELECT
    cnpj_fornecedor,
    razao_social_fornecedor,
    COUNT(*) AS participacoes_90d,
    SUM(valor_total) AS volume_90d,
    ARRAY_AGG(DISTINCT setor ORDER BY setor) AS setores,
    MAX(data_assinatura) AS ultimo_contrato
  FROM supplier_contracts
  WHERE data_assinatura > NOW() - INTERVAL '90 days'
    AND valor_total > 0
  GROUP BY cnpj_fornecedor, razao_social_fornecedor
  HAVING COUNT(*) >= 3 AND SUM(valor_total) >= 100000
)
SELECT q.*
FROM qualified q
LEFT JOIN profiles p ON p.cnpj = q.cnpj_fornecedor
WHERE p.id IS NULL
ORDER BY q.volume_90d DESC
LIMIT 50;
```

**Template de abordagem (v1 draft — validar antes de enviar):**
```
Assunto: {razao_social} — {N} editais abertos em {setor_principal}

{nome},

Notei que {razao_social} participou de {X_contratos} contratos em {setor_principal} nos últimos 90 dias ({Y_valor} somados). Você já identificou os {N} editais abertos agora com fit direto para vocês?

Mapeamos no SmartLic (ferramenta que criamos para analisar editais PNCP com IA). Posso enviar a lista dos {N} editais com análise de viabilidade individual — leva 5 min de leitura.

Quer receber?

Tiago Sasaki
Fundador, SmartLic
smartlic.tech
```

---

## File List

_(populado pelo @dev durante execução)_

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-19 | @sm (River) | Story criada Ready. Subsídios do plano Board v1.0. |
