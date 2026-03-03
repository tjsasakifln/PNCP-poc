# SHIP-004: Pricing End-to-End Validation

**Status:** 🔴 Pendente
**Prioridade:** P0
**Sprint:** SHIP (Go-to-Market)
**Criado:** 2026-03-03
**Depende de:** SHIP-001

## Contexto

Pricing foi atualizado em STORY-277/360 para:
- **SmartLic Pro:** R$397/mês | R$357/semestral (10% off) | R$297/anual (25% off)
- **Consultoria:** R$997/mês | R$897/semestral (10% off) | R$797/anual (20% off)

Precisa validar que a chain completa funciona: Stripe products → backend → frontend → checkout → webhook → acesso.

## Acceptance Criteria

### Stripe Dashboard

- [ ] AC1: Stripe Dashboard tem products/prices para SmartLic Pro (3 billing periods)
- [ ] AC2: Stripe Dashboard tem products/prices para Consultoria (3 billing periods)
- [ ] AC3: Price IDs no Stripe correspondem aos IDs em `plan_billing_periods` table

### Backend

- [ ] AC4: `GET /plans` retorna SmartLic Pro com 3 billing periods e valores corretos
- [ ] AC5: `GET /plans` retorna Consultoria com 3 billing periods e valores corretos
- [ ] AC6: `GET /subscription/status` para usuário trial retorna `plan_type: "free_trial"`

### Frontend

- [ ] AC7: `/planos` mostra toggle Mensal/Semestral/Anual com desconto visível
- [ ] AC8: Card SmartLic Pro mostra R$397 (mensal), R$357 (semestral), R$297 (anual)
- [ ] AC9: Card Consultoria mostra R$997 (mensal), R$897 (semestral), R$797 (anual)
- [ ] AC10: Botão "Assinar" redireciona para Stripe Checkout com valor correto

### Checkout Flow

- [ ] AC11: Stripe Checkout carrega com valor correto do plano selecionado
- [ ] AC12: Após pagamento (modo teste), redirect para `/planos/obrigado`
- [ ] AC13: Webhook `checkout.session.completed` atualiza `profiles.plan_type`
- [ ] AC14: Usuário consegue fazer buscas após pagamento (quota liberada)

### Trial

- [ ] AC15: Novo signup → `plan_type = "free_trial"`, `trial_ends_at` = now + 14 dias
- [ ] AC16: Trial badge no header mostra dias restantes
- [ ] AC17: Após 14 dias (simular), paywall bloqueia busca com mensagem de upgrade
