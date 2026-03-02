# STORY-360: Inconsistência de desconto entre planos e copy

**Prioridade:** P2
**Tipo:** fix (copy + dados)
**Sprint:** Sprint 3
**Estimativa:** S
**Origem:** Conselho CTO Advisory Board — Auditoria de Promessas (2026-03-01)
**Dependências:** Nenhuma
**Bloqueado por:** —
**Bloqueia:** —
**Paralelo com:** STORY-353, STORY-358, STORY-359

---

## Contexto

Existem inconsistências de preço entre diferentes fontes:
- `planos/page.tsx:25` → annual discount: 25% → R$297/mês
- `CLAUDE.md` → documenta R$317/mês anual
- FAQ → "25% de economia" para anual
- Consultoria plan → 20% anual (diferente do Pro)
Isso confunde o usuário e o suporte.

## Promessa Afetada

> Confiança na transparência de preços
> "Investimento fixo mensal, sem surpresas"

## Causa Raiz

Preços hardcoded em múltiplos locais sem fonte única de verdade. Frontend e documentação divergem. Stripe é o master, mas frontend não busca preços do backend.

## Critérios de Aceite

- [x] AC1: Definir fonte única de verdade para preços: `backend/routes/billing.py` GET /v1/plans → `plan_billing_periods` table → Stripe (master)
- [x] AC2: Frontend busca preços do backend (`GET /plans`) em vez de hardcoded, com fallback para valores estáticos
- [x] AC3: Verificar que Stripe price IDs correspondem aos valores exibidos no frontend
- [x] AC4: Atualizar CLAUDE.md com preços corretos após verificação no Stripe
- [x] AC5: FAQ de preços deve referenciar valores do mesmo objeto `PRICING` (não números duplicados)
- [x] AC6: Garantir que desconto do Pro (25% anual) e Consultoria (20% anual) estejam claramente diferenciados na UI
- [x] AC7: Testes: verificar que `PRICING` e `CONSULTORIA_PRICING` são consistentes com backend

## Arquivos Afetados

- `frontend/app/planos/page.tsx` — dynamic pricing fetch, FAQ references constants, PlanToggle discounts prop
- `frontend/app/api/plans/route.ts` — NEW: API proxy for GET /plans
- `frontend/components/subscriptions/PlanToggle.tsx` — accepts `discounts` prop, default 25% annual
- `backend/routes/billing.py` — GET /v1/plans returns `billing_periods` from DB, strips Stripe IDs
- `CLAUDE.md` — fixed R$317→R$297 annual price, added Consultoria pricing
- `frontend/__tests__/story-360-pricing-consistency.test.tsx` — NEW: 14 tests (AC2/3/5/6/7)
- `backend/tests/test_story360_pricing_consistency.py` — NEW: 12 tests (AC1/3/7)
- `frontend/__tests__/pages/PlanosPage.test.tsx` — updated 25% references
- `frontend/__tests__/components/subscriptions/PlanToggle.test.tsx` — updated 25% + discounts prop tests

## Validação

| Métrica | Threshold | Onde medir |
|---------|-----------|------------|
| Preço frontend = Stripe | 100% match | Integration test |
