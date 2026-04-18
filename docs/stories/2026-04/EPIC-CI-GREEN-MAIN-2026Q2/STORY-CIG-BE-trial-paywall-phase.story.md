# STORY-CIG-BE-trial-paywall-phase — `get_trial_phase` sempre retorna `full_access` (lógica revertida) — 15 testes prod-bug candidato

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate Blocker (possível regressão de revenue)
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops, @po (se confirmado bug real de paywall)

---

## Contexto

Suítes de paywall/trial rodam em `backend-tests.yml` e falham em **15 testes** do triage row #11/30. Classificação pelo triage é **assertion-drift**, mas a função afetada (`get_trial_phase`) é um dos pontos mais sensíveis do produto (STORY-264/277/319/320 — trial de 14 dias, paywall pós-trial). O triage anota: *"`get_trial_phase` sempre retorna `full_access` — lógica revertida"*.

Duas hipóteses precisam ser distinguidas em Implement:

1. **Assertion-drift benigna:** logic atual é correta; testes asseguram fases antigas (`trial_active` / `trial_expired` / `paywall`) que foram consolidadas em um único retorno `full_access` para plano SmartLic Pro.
2. **Prod-bug real:** paywall está desativado em produção por acidente — usuários com trial expirado estão recebendo `full_access` indevidamente. Neste caso, story vira bugfix P0 e exige pair com @po.

Decisão entre (1) e (2) só é possível após leitura do módulo real + diff histórico de `get_trial_phase`.

**Esta story desbloqueia stories downstream:**
- STORY-CIG-BE-story-drift-trial-email-sequence (#24/30, depende desta)

**Arquivos principais afetados:**
- `backend/tests/test_story320_paywall.py`
- `backend/tests/test_trial_block.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Provável **bug real** dado que o triage chamou "lógica revertida" explicitamente — mas validar com `git log backend/quota.py backend/services/billing.py -p` antes de rotular como regressão.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_story320_paywall.py backend/tests/test_trial_block.py -v` retorna exit code 0 localmente (15+/15+ PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" distinguindo (1) assertion-drift benigna vs (2) prod-bug real. Se (2), referenciar issue aberta + decisão @po.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido. Se (2), adicionar teste de regressão explícito cobrindo o bugfix.
- [ ] AC5 (NEGATIVO): `grep -nE "@pytest\\.mark\\.skip|pytest\\.skip\\(|@pytest\\.mark\\.xfail|\\.only\\("` vazio nos arquivos tocados. Nota: `test_trial_block.py::test_post_pipeline_blocked` é **move-to-integration-external** no triage (real Supabase UUID) — tratar esse row 1 isoladamente (marca `@pytest.mark.external` só nele) NÃO conta como quarentena porque está documentado como exceção do triage com justificativa técnica.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 2 suítes isoladas e capturar mensagens de erro.
- [ ] `git log --follow -p backend/quota.py backend/services/billing.py` — identificar commit que alterou `get_trial_phase`.
- [ ] Classificar: (1) assertion-drift benigna OU (2) prod-bug real. Se ambíguo, escalar para @po.
- [ ] Se (2) prod-bug: abrir issue P0, marcar story `Status: Blocked` até decisão @po sobre rollback vs fix-forward.
- [ ] Validar que feature flag `SUBSCRIPTION_GRACE_DAYS=3` continua respeitada (CLAUDE.md).
- [ ] Confirmar que quota enforcement (`check_and_increment_quota_atomic`) continua sendo invocada (CLAUDE.md anota obrigatoriedade em tests mockando `/buscar`).
- [ ] Validar cobertura não regrediu.
- [ ] Aplicar `@pytest.mark.external` em `test_post_pipeline_blocked` se decisão for manter teste real (documentar em workflow `integration-external.yml`).

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #11/30)
- **Bloqueia:** STORY-CIG-BE-story-drift-trial-email-sequence (#24/30)

## Stories relacionadas no epic

- STORY-CIG-BE-story-drift-trial-email-sequence (#24 — dep)
- STORY-CIG-BE-endpoints-story165-plan-rename (#20 — mesma área billing/plano)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #11/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. **Atenção @po:** triagem anotou "lógica revertida" — validar prod-bug vs assertion-drift é obrigatório antes de GO.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO com ressalva (7/10)** — Draft → Ready (**Wave 1 foundation**). Ambiguidade (1) assertion-drift vs (2) prod-bug real é estruturalmente aceitável em Draft — Investigation Checklist tem escalation path documentado. **Se @dev confirmar (2) prod-bug em Implement**, Status volta a `Blocked` e @po escala para **P0 bugfix** (regressão de revenue/paywall tem impacto direto em MRR). Bloqueia #24.
