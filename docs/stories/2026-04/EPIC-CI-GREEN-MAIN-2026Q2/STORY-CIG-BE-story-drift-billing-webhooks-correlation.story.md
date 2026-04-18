# STORY-CIG-BE-story-drift-billing-webhooks-correlation — Webhook/auth 403s + quota delegation não invocado — 4 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate (auth/webhook = superfície crítica)
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Duas suítes `test_crit004_correlation.py` e `test_organizations.py` rodam em `backend-tests.yml` e falham em **4 testes** do triage row #29/30. Causa raiz classificada como **mock-drift**:

1. **Webhook/auth 403s**: Stripe webhook handlers recebem 403 (autorização falha). Possível drift em `webhooks/stripe.py` signature verification mock.
2. **Quota delegation não invocado**: CRIT-004 (correlação de IDs) esperava delegação para `check_and_increment_quota_atomic` mas o mock não captura a call.

**Arquivos principais afetados:**
- `backend/tests/test_crit004_correlation.py`
- `backend/tests/test_organizations.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Refactor recente em `webhooks/handlers/` (relacionado a STORY #28) ou em `authorization.py` mudou superfície. Validar com `grep -rn "verify_webhook_signature\\|check_and_increment_quota_atomic" backend/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_crit004_correlation.py backend/tests/test_organizations.py -v` retorna exit code 0 localmente (4/4 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift). Distinguir os 2 sub-drifts (webhook auth vs quota delegation).
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados. CLAUDE.md invariante: tests mockando `/buscar` devem mockar `check_and_increment_quota_atomic`.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 2 suítes isoladas.
- [ ] `grep -rn "verify_webhook_signature\\|check_and_increment_quota_atomic" backend/`.
- [ ] Validar que Stripe webhook signature verification continua ativa em produção.
- [ ] Coordenar com STORY-CIG-BE-pgrst205-http503-contract (#18) se `test_organizations.py` overlap — evitar duplicação de fix.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #29/30)

## Stories relacionadas no epic

- STORY-CIG-BE-pgrst205-http503-contract (#18 — também toca `test_organizations.py`)
- STORY-CIG-BE-asyncio-run-production-scan (#28 — `webhooks/handlers/__init__.py` impactado)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #29/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
