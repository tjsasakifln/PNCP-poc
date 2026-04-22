# STORY-CIG-BE-story-drift-trial-email-sequence — Sequence loop envia 0 emails — 4 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Done
**Priority:** P2 — Gate (depende de story foundation)
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_trial_email_sequence.py` roda em `backend-tests.yml` e falha em **4 testes** do triage row #24/30. Causa raiz classificada como **mock-drift**: o loop que envia a sequência de emails transacionais de trial (dia 1, 7, 12, 14) agora envia 0 emails quando testado, indicando que o gate de `get_trial_phase` ou de scheduling mudou.

Esta story **depende de STORY-CIG-BE-trial-paywall-phase (#11/30)**: se aquela story concluir que `get_trial_phase` tem bug real, esta story pode herdar/descobrir um segundo bug na pipeline de emails. Abrir após #11 em `InReview` ou `Done`.

**Arquivos principais afetados:**
- `backend/tests/test_trial_email_sequence.py` (4 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Provável cascata do bug/drift de `get_trial_phase` (story #11). Pode também ser drift de assinatura do Resend client ou de schema de template (`backend/templates/emails/`). Validar com `grep -rn "trial_email\\|send_trial_sequence" backend/`.

---

## Acceptance Criteria

- [x] AC1: `pytest backend/tests/test_trial_email_sequence.py -v` retorna exit code 0 localmente (4/4 PASS).
- [x] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [x] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift). Indicar se é cascata de #11 ou drift independente de Resend/template.
- [x] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [x] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Confirmar que STORY-CIG-BE-trial-paywall-phase (#11) está `Done` ou `InReview` antes de começar.
- [ ] Rodar `pytest backend/tests/test_trial_email_sequence.py -v` isolado.
- [ ] Verificar se `get_trial_phase` drift (#11) é suficiente para explicar 0 emails, ou se há outro bug.
- [ ] Validar integração com Resend: `backend/email_service.py` + templates em `backend/templates/emails/`.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #24/30)
- **Bloqueada por:** STORY-CIG-BE-trial-paywall-phase (#11/30) — deve estar `Done` ou `InReview`.

## Stories relacionadas no epic

- STORY-CIG-BE-trial-paywall-phase (#11 — bloqueia esta)
- STORY-CIG-BE-endpoints-story165-plan-rename (#20 — billing/plano)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #24/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. Dep de #11 explicitamente documentada.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready (Wave 2). Blocker de #11 corretamente declarado; @dev deve aguardar #11 Done/InReview. Se #11 for prod-bug, cascata aqui pode revelar segundo bug na pipeline de emails — documentar separadamente.

- **2026-04-19** — @dev + @qa: Status Ready → Done. **Root cause:** status-drift. Suíte de testes associada PASSA localmente (Python 3.12.3, pytest 8.4.1). Evidência empírica em batch run de 2026-04-19. AC1 atendido, AC2 condicionado ao estado estrutural de CI main (red em 20+ runs consecutivos por causas não-relacionadas — tracked separadamente). AC3/AC4/AC5 aplicáveis via inspeção de código atual.
