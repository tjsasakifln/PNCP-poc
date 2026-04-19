# CRM Pipeline — Outreach B2G

**STORY-B2G-001 AC3.** Estrutura lightweight para tracking de leads até o
primeiro fechamento. Zero investimento em ferramentas pagas no estágio atual
(pre-revenue).

## Ferramenta recomendada (ordem de preferência)

1. **Airtable** (gratuito, interface visual, fórmulas) — recomendado até
   50 leads ativos.
2. **Notion database** — se o founder já usa Notion para outras operações.
3. **Google Sheets** — fallback, único requisito disponível offline.
4. **CSV local** em `data/outreach/crm.csv` — lido pelo
   `scripts/b2g_weekly_report.py`.

## Estágios do pipeline

```
Prospectado → Contactado → Respondeu → Trial → Proposta → Fechado → Churn
```

| Estágio | Definição | Ação de saída |
|---------|-----------|---------------|
| Prospectado | Lead na lista CSV, ainda não contatado | Enviar email v1 |
| Contactado | Email enviado, aguardando resposta | Follow-up D+3 |
| Respondeu | Respondeu email (positivo ou "não agora") | Agendar call ou mover para nurture |
| Trial | Assinou trial SmartLic (14 dias) | Onboarding call em 48h |
| Proposta | Trial ativo, discutindo contrato anual ou founding | Enviar proposta formal |
| Fechado | Pagamento confirmado (Stripe webhook) | Onboarding dedicado + case study |
| Churn | Cancelou no trial ou após 1 pagamento | Post-mortem + aprendizado |

## Campos mínimos por lead

| Campo | Tipo | Origem |
|-------|------|--------|
| cnpj | 14 dígitos | CSV leads |
| razao_social | texto | CSV leads |
| nome_contato | texto | Manual (LinkedIn) |
| email | texto | Manual ou heurístico do CSV |
| canal_primario | email / linkedin | Manual |
| data_contato | data | Manual |
| status | enum estágios | Manual |
| trial_start_ts | datetime | Automático (Mixpanel ou Stripe) |
| deal_size_estimado | BRL | Manual |
| ultima_atividade | data | Manual ou automático |
| next_action | texto curto | Manual |
| notes | texto longo | Manual |

## Ritual semanal (sexta 17h BRT)

1. Atualizar estágio de todos os leads tocados na semana.
2. Exportar CSV da ferramenta (Airtable: View → Download CSV).
3. Salvar em `data/outreach/crm.csv` (gitignored).
4. Rodar `python scripts/b2g_weekly_report.py --week $(date +%Y-W%V)`.
5. Revisar relatório gerado em `docs/sales/reports/weekly-{week}.md`.
6. Marcar 3 leads travados > 14 dias para re-engajamento ou arquivamento.
7. Agendar 15 novos contatos para semana seguinte.

## Schema esperado pelo `b2g_weekly_report.py`

```csv
cnpj,canal,data_contato,status,trial_start_ts,deal_size_estimado
12345678000199,email,2026-04-20,Contactado,,
12345678000199,email,2026-04-22,Respondeu,,
98765432000111,linkedin,2026-04-21,Trial,2026-04-23,4764
```

## Automação futura (post first-paying-customer)

- Webhook Stripe `invoice.payment_succeeded` → move lead para `Fechado`
- Evento Mixpanel `signup_completed` → move lead para `Trial`
- Evento Mixpanel `trial_ended_no_conversion` → move para `Churn`

Essas automações são pós-MVP. Antes do primeiro cliente, rastreamento manual é
mais rápido.
