# Funnel Diagnostic — Mission sparkling-patterson (H0→H1)

**Data:** 2026-04-24
**Fonte:** `/tmp/funnel_diagnostic.py` contra Supabase prod via SUPABASE_SERVICE_ROLE_KEY (read-only, REST API)

---

## Números brutos

### Aquisição
| Janela | Signups (non-admin) | Founding leads SEO |
|--------|--------------------|--------------------|
| 30d | 2 | 0 |
| 7d | **0** | 0 |
| Lifetime | 3 (total non-admin) | 0 |

### Engajamento
| Janela | Search sessions | Unique users |
|--------|----------------|--------------|
| 30d | 127 | 3 |
| 7d | **1** | ? |
| Lifetime | 170 | — |

- Média 30d: ~42 searches/user (engagement **alto** entre os 3)
- Colapso 7d (127 → 1) = última cohort expirou trial ou abandonou

### Conversão / Retention
| Métrica | Valor |
|---------|-------|
| Stripe `checkout.session.completed` 30d | 1 |
| Stripe `invoice.payment_succeeded` 30d | 1 |
| Stripe `customer.subscription.deleted` 30d | 1 |
| Current `plan_type` paid (non-admin) | **0** |
| Current `plan_type` free_trial | 3 |
| Trial status | 100% expired / 0% active / 0% converted-retained |

**Interpretação:** 1 usuário passou pelo fluxo Stripe completo em 30d (pagou + cancelou). `profiles.plan_type` reflete estado final (webhook sync OK). 3/3 trials expiraram sem conversão persistente.

### Trial emails (já existem em produção)
| Métrica | Valor |
|---------|-------|
| Templates enviados (lifetime) | 14 |
| 30d | 9 |
| 7d | 4 |
| **Opens all-time** | **0** |
| **Clicks all-time** | **0** |

Templates presentes: `paywall_alert`, `value`, `last_day`, `expired`, `engagement`, `midpoint` (6 variantes)

**Colunas:** `id, user_id, email_type, sent_at, email_number, opened_at, clicked_at, resend_email_id`
**Ausente:** `delivery_status`, `bounced_at`, `complained_at`

---

## Leitura estratégica

### Maior dropoff real (re-priorização)

| Hipótese original | Observado | Revisado |
|-------------------|-----------|----------|
| H1: signup → first search | 3/3 buscaram | não é gargalo |
| H2: first search → engagement | 42 searches/user médio | **engagement alto** — produto funciona |
| H3: trial → paid conversion | 1/3 pagou (33%) | **insuficiente dado** (N=3) |
| H4: paid → retained | 0/1 retido | churn pós-paid (N=1) |
| **H5: aquisição** | 0 signups 7d, 0 founding_leads | **MAIOR GARGALO** |
| H6: trial email delivery/open | 0 opens em 14 emails | **tracking broken — ambíguo** |

### Verdade desconfortável

1. **Aquisição morta** — 0 signups 7d, 0 lifetime founding_leads. Sem inbound. Sem funil de topo = otimizar retention de 3 users é otimizar zero.
2. **Trial emails deployed mas zerotracking** — 9 emails enviados 30d, 0 opens/clicks. Ou (a) emails caem spam/bounce, (b) users não abrem, (c) Resend webhook não populou tracking. Memory `reference_trial_email_log_delivery_status_null.md` confirma Resend webhook nunca foi configurado no dashboard. **Métrica 0% opens é inconclusiva.**
3. **Opção A original (ship trial email lifecycle)** — sistema já existe. O gap real é **observabilidade de entrega + instrumentação Mixpanel**.
4. **Opção B (SEO)** — 0 founding_leads + sitemap-4.xml = 0 URLs (memory). Canal inbound dormente.

---

## Dropoff máximo identificado

**Nível sistêmico:** aquisição (0 signups 7d)
**Nível unit:** 1 emails enviados com 0% open rate — tracking broken

## Contra-medida candidata

1. **Opção B ganha peso vs A** — destravar canal de aquisição SEO (PR #505 + sitemap fix) é upstream de tudo. Sem signups novos, A otimiza zero.
2. **Opção A refocada** — instrumentar delivery primeiro (Resend webhook config + `trial_email_log.delivery_status` + Mixpanel events), NÃO shippar novos templates. Templates já existem.

---

## Arquivos de verdade

- `backend/routes/trial_emails.py` — route exists (confirmado via ls)
- Templates: provavelmente `backend/templates/emails/trial_*.html` (a verificar)
- Tabela `trial_email_log` — schema acima
- Stripe webhook handlers: `backend/webhooks/stripe.py` (confirmado funcionando via plan_type sync)
