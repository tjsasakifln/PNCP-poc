# STORY-424: Enable PIX via Stripe Checkout Session Options

**Priority:** P3 — Backlog (Q2/2026 evaluation)
**Effort:** L (3-5 days)
**Squad:** @dev + @devops + @pm
**Status:** Backlog
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md) (follow-up de STORY-420)
**Created by:** @pm (Morgan) 2026-04-10

---

## Contexto

Esta story é **follow-up planejado de STORY-420**, onde foi decidido remover PIX do `payment_method_types` para parar sangria imediata de checkout quebrado. A decisão foi baseada em:

1. SmartLic é B2B SaaS recorrente (R$397/mês) → cartão corporativo domina
2. PIX subscription no Stripe Brasil ainda é área cinza
3. Fix de horas (remover) vs sprint completo (habilitar corretamente)

Esta story é a **segunda metade** dessa decisão — avaliar se PIX deve ser re-introduzido **corretamente** via `payment_method_options.pix` em uma janela futura com planejamento adequado.

---

## Trigger de Priorização

**Não iniciar esta story até que UMA das condições abaixo seja verdadeira:**

- [ ] Support recebe **>5 pedidos/mês** "posso pagar via PIX?" por 2 meses consecutivos
- [ ] Stripe Brasil anuncia oficialmente suporte a PIX em subscription checkout
- [ ] Q2/2026 review agenda revisão de payment methods
- [ ] Competidor direto oferece PIX e causa churn mensurável

**Responsável pelo trigger:** @pm (Morgan) — revisão trimestral

---

## Acceptance Criteria (alto nível)

### AC1: Validação de viabilidade Stripe
- [ ] Confirmar via Stripe Docs que `payment_method_options.pix` é suportado em checkout session para conta Brasil
- [ ] Se não suportado: escalar para Stripe support ou avaliar integração direta com PSP alternativo (Pagar.me, Mercado Pago)
- [ ] Documentar achados em `docs/research/stripe-pix-viability.md`

### AC2: Habilitar PIX no Stripe Dashboard
- [ ] @devops habilita PIX na conta Stripe (dashboard > Payments > Settings)
- [ ] Verificar compliance checks + KYC se necessário
- [ ] Ativar em test mode primeiro, validar fluxo completo

### AC3: Integração backend
- [ ] Em `backend/routes/billing.py::create_checkout_session`, adicionar:
  ```python
  "payment_method_types": ["card", "boleto", "pix"],
  "payment_method_options": {
      "pix": {
          "expires_after_seconds": 3600,  # 1 hour
      }
  }
  ```
- [ ] Testar com cartão de teste Stripe + conta PIX de teste
- [ ] Validar webhook handling para `checkout.session.completed` via PIX

### AC4: Frontend UI
- [ ] Em `frontend/app/planos/page.tsx`, readicionar badge visual "PIX disponível"
- [ ] Atualizar copy de marketing se relevante
- [ ] Screenshot comparativo antes/depois em PR

### AC5: Observability
- [ ] Métrica Prometheus `smartlic_checkout_by_payment_method_total{method="pix"|"card"|"boleto"}`
- [ ] Dashboard Grafana com conversion rate por método
- [ ] Alert Sentry se PIX error rate > 5%

### AC6: Testes
- [ ] Unit tests em `backend/tests/test_billing.py` cobrindo PIX option
- [ ] E2E Playwright test no checkout flow com seleção PIX
- [ ] Load test: 100 checkouts simultâneos via PIX

### AC7: Rollout faseado
- [ ] Fase 1: 10% dos usuários via feature flag `PIX_CHECKOUT_ENABLED`
- [ ] Fase 2: 50% após 7d sem issues
- [ ] Fase 3: 100% após 14d estável
- [ ] Rollback: feature flag off

---

## Arquivos Impactados (estimativa)

| Arquivo | Mudança |
|---------|---------|
| `backend/routes/billing.py` | Readicionar PIX via `payment_method_options` |
| `backend/tests/test_billing.py` | Tests PIX flow |
| `frontend/app/planos/page.tsx` | Readicionar badge PIX |
| `frontend/app/pricing/page.tsx` | Readicionar menção marketing |
| `docs/research/stripe-pix-viability.md` | **Novo** — achados de viabilidade |
| Stripe Dashboard (externo) | Habilitar PIX na conta |

---

## Implementation Notes

- **Não iniciar sem trigger.** Esta story existe para documentar intent — não é work-in-progress
- **Dependência externa crítica:** Stripe Brasil precisa suportar PIX em checkout session. Se não suportar, story deve pivotar para avaliação de PSP alternativo (fora do escopo atual)
- **Revenue impact estimado:** se >5 pedidos/mês = ~R$2k MRR potencial (5 usuários × R$397). Se <R$2k, não justifica sprint L
- **Alternativa:** se PIX for crítico mas Stripe não suportar, avaliar manter Stripe para cartão + PSP alternativo para PIX (dual-rail)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @pm (Morgan) | Story criada como follow-up P3 de STORY-420. Trigger de priorização documentado. Status: Backlog. |
