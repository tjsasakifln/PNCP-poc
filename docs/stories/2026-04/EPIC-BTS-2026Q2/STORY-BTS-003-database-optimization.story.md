# STORY-BTS-003 — Database Optimization & Plan Reconciliation (15 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P1
**Effort:** S (2-3h)
**Agents:** @dev + @qa + @data-engineer
**Status:** Done (PR #399 merged `c75f3a81` — 2026-04-19)

---

## Contexto

15 testes cobrindo DB optimization (indexes, query patterns) + plan reconciliation (Stripe ↔ Supabase profiles sync). Suspeita: schema drift em `plan_billing_periods` após STORY-277/360 GTM-002 rename + queries tocando colunas movidas.

---

## Arquivos (tests)

- `backend/tests/test_debt017_database_optimization.py` (11 failures)
- `backend/tests/test_debt010_plan_reconciliation.py` (4 failures)

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_debt017_database_optimization.py backend/tests/test_debt010_plan_reconciliation.py -v --timeout=30` retorna exit code 0 (15/15 PASS).
- [ ] AC2: `backend-tests.yml` CI verde para esses 2 arquivos. Link no Change Log.
- [ ] AC3: Causa raiz categorizada por sub-grupo (DB index drift, query path drift, Stripe sync drift).
- [ ] AC4: Cobertura não caiu.
- [ ] AC5 (NEGATIVO): zero quarantine new.

---

## Investigation Checklist

- [ ] `grep -rn "plan_billing_periods\\|monthly_quota\\|subscription_grace" backend/` — mapear uso atual
- [ ] Confirmar se migrations faltam em `supabase/migrations/`
- [ ] Para reconciliation: verificar se handler Stripe webhook aponta para path correto

---

## Dependências

- **Bloqueado por:** BTS-001 (plan capabilities)
- **Bloqueia:** BTS-010 (billing)

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready.
- **2026-04-19** — @po (Pax): Validação GO — 7/10. Gaps: P4 escopo, P7 valor não enunciado, P8 riscos. Story confirmada Ready. Recomendação: adicionar valor ao campo Priority.
