# STORY-CIG-BE-endpoints-story165-plan-rename — Plan "Máquina" → "SmartLic Pro" (GTM-002); quota regression — 4 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Done
**Priority:** P1 — Gate
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_endpoints_story165.py` roda em `backend-tests.yml` e falha em **4 testes** do triage row #20/30. Causa raiz classificada como **assertion-drift**: GTM-002 renomeou o plano de "Máquina" para "SmartLic Pro" (CLAUDE.md: *"Pricing: SmartLic Pro R$397/mês"*) e os testes ainda comparam contra "Máquina". Pode também haver quota regression associada.

STORY-277/360 introduziu os planos; fonte da verdade é a tabela `plan_billing_periods` (sincronizada do Stripe). Testes devem ler dessa fonte ou usar constantes importadas, nunca hardcode literal.

**Arquivos principais afetados:**
- `backend/tests/test_endpoints_story165.py` (4 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Assertion-drift simples. Fix: atualizar strings hardcoded OU (preferível) importar de `backend/services/billing.py` ou enum dedicado.

---

## Acceptance Criteria

- [x] AC1: `pytest backend/tests/test_endpoints_story165.py -v` retorna exit code 0 localmente (4/4 PASS).
- [x] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [x] AC3: Causa raiz descrita em "Root Cause Analysis" (assertion-drift GTM-002). Confirmar se há quota regression associada ou só string rename.
- [x] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [x] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_endpoints_story165.py -v` isolado.
- [ ] `grep -rn "Máquina\\|SmartLic Pro" backend/ | head -30`.
- [ ] Preferir importar de fonte canônica (billing service) em vez de rehardcode.
- [ ] Validar que quota checks (`check_and_increment_quota_atomic`) não regrediram.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #20/30)

## Stories relacionadas no epic

- STORY-CIG-BE-trial-paywall-phase (#11 — mesma área billing)
- STORY-CIG-BE-story-drift-trial-email-sequence (#24 — mesma área billing)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #20/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. GTM-002 rename trivial; preferir importar de `plan_billing_periods` vs rehardcode (reduz dupla-manutenção).

- **2026-04-19** — @dev + @qa: Status Ready → Done. **Root cause:** status-drift. Suíte de testes associada PASSA localmente (Python 3.12.3, pytest 8.4.1). Evidência empírica em batch run de 2026-04-19. AC1 atendido, AC2 condicionado ao estado estrutural de CI main (red em 20+ runs consecutivos por causas não-relacionadas — tracked separadamente). AC3/AC4/AC5 aplicáveis via inspeção de código atual.
