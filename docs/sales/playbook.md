# Outreach Playbook — SmartLic B2G Wave 1

**STORY-B2G-001.** Runbook operacional para os próximos 6 semanas de outreach
(D+1 a D+45, meta: primeiro cliente pagante em D+45).

## Meta quantitativa

| Métrica | Meta semanal | Meta 6 semanas |
|---------|--------------|----------------|
| Contatos qualificados (email + LinkedIn) | 15 | 90 |
| Email/LinkedIn split | 10 / 5 | 60 / 30 |
| Response rate (a partir W3) | ≥ 20% | ≥ 18 responders |
| Trial-start rate (dos que responderam) | ≥ 30% | ≥ 5-7 trials |
| Trial-to-paid | ≥ 20% | ≥ 1-2 pagantes |

Origem dos números: base conservadora de outbound B2B qualificado com dado
proprietário. Se response rate < 10% em W3, pivotar template v1→v2.

## Capacidade disponível

- **Founder:** 12h/semana × 6 semanas = 72h total.
- **Timeboxing diário:** 2h/dia, janela 10h-12h BRT (horário comercial).
- **Não exceder 2h/dia** — fadiga em outreach é real e corrói response rate.
- Sexta 15h-17h reservada para revisão semanal + planejamento próxima semana
  (2h).

Se volume exceder capacidade pós-W3 (>30 leads ativos), contratar SDR
freelancer (R$ 3-5k/mês variável) — só após primeiro pagante como gate.

## Ritmo semanal (sugestão)

| Dia | Horário | Atividade |
|-----|---------|-----------|
| Seg | 09h-10h | Rodar `b2g_outreach_query.py` + validar 15 novos leads |
| Seg | 10h-12h | Gerar briefs (5) + enviar emails (3) |
| Ter | 10h-12h | Gerar briefs (5) + enviar emails (3) |
| Qua | 10h-12h | Follow-ups D+3 + enviar emails (2) |
| Qui | 10h-12h | LinkedIn InMails (5) + calls agendadas |
| Sex | 10h-12h | Calls + gerar 2 propostas |
| Sex | 15h-17h | Revisão CRM + weekly report + planning |

## Fluxo de um lead individual

```
1. Lead no CSV → gerar brief com b2g_lead_brief.py
2. Pesquisar nome do decisor (LinkedIn, 5 min)
3. Preencher placeholders do template v1
4. Revisar email (tamanho, gramática, personalização real)
5. Enviar + logar no CRM (status Contactado)
6. D+3 sem resposta → follow-up 1-liner
7. D+7 sem resposta → LinkedIn InMail (se fit alto) ou arquivar
8. Respondeu → call 20 min em 48h
9. Call OK → trigger trial (enviar link /signup)
10. D+7 do trial → check-in 15 min
11. D+12 do trial → proposta (usar /founding se primeiros 10)
12. Decisão: fechamento ou próximo micro-passo
```

## Checklist pré-envio de email

- [ ] Nome do decisor correto (não "prezado gerente")
- [ ] Razão social sem typos (conferir no CNPJ.ws ou BrasilAPI)
- [ ] X_contratos e Y_valor batem com o brief
- [ ] Setor_principal está certo (evitar erros grosseiros tipo classificar
  construtora como TI)
- [ ] N_editais > 0 (se 0, não enviar — o atrativo principal some)
- [ ] Footer LGPD presente
- [ ] Reply-to correto (Tiago Sasaki, não contato@ genérico)

## Quando abortar um lead

- CNPJ inativo na Receita Federal
- Empresa em recuperação judicial (risco de inadimplência)
- Response explicitamente negativa ("não temos interesse") — não insistir
- Opt-out (UNSUBSCRIBE) — adicionar ao `data/outreach/opt-outs.txt`
- 2 bounces de email (provavelmente domínio heurístico errado) —
  buscar email real via Hunter.io / Apollo.io Free

## Ferramentas complementares

| Necessidade | Ferramenta | Custo | Uso |
|-------------|-----------|-------|-----|
| Email real (quando heurístico falha) | Hunter.io Free | 25/mês grátis | Verificar domínio |
| Email real (fallback) | Apollo.io Free | 50/mês grátis | 50 leads/mês |
| Validação CNPJ | BrasilAPI | 0 | Já integrado no backend |
| Tracking de abertura | Mailtrack (Gmail) | Free tier | Ler signal de engajamento |
| CRM visual | Airtable Free | 0 | Até 1k rows |

Nenhuma dessas ferramentas é bloqueante — fluxo mínimo funciona só com Gmail +
CSV local.

## Case study pós-primeiro fechamento

Ao fechar o primeiro cliente pagante:

1. Criar `docs/sales/case-studies/{empresa-slug}-2026-{mes}.md` com template
   em `docs/sales/case-studies/_template.md`.
2. Solicitar permissão para quote com nome + logo (opcional — pode ser
   anônimo com métricas preservadas).
3. Reuso: landing `/casos` + CTA em outreach wave 2 + proposta formal.

## Bloqueadores conhecidos

1. **profiles sem CNPJ:** não dá para filtrar automaticamente leads que já são
   SmartLic users. Workaround manual: rodar `b2g_outreach_query.py` e
   cross-check com a view de admin antes do primeiro envio. Backlog futuro:
   adicionar `profiles.cnpj` + UNIQUE INDEX.
2. **Índice composto em `pncp_supplier_contracts`:** a query atual usa índice
   `idx_psc_fornecedor_data` (ni_fornecedor, data_assinatura DESC) que cobre
   o acesso por fornecedor, mas não por data apenas. Se o script demorar >30s
   para retornar, considerar adicionar índice `(data_assinatura DESC)` parcial
   em is_active = TRUE.
3. **Response rate baixo:** fallback é A/B com v2 (consultivo). Se ambos < 10%
   em W4, revisitar ICP (talvez foco em consultorias CNAE 70.2/74.9/82.9
   — ver STORY-BIZ-002).
