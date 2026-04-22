# STORY-BTS-010a — Billing, Partners & Feature Flags (14 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P1 — Billing integrity = revenue accuracy; feature flags guardam rollouts pagos
**Effort:** M (3-5h)
**Agents:** @dev + @qa
**Status:** Done (PR #404 merged `bce60289` — 2026-04-19; 8 real failures fixed — triage overscoped 14→8)

---

## Escopo

**IN:**
- Fix das suítes de billing ops, partner endpoints, feature flags matrix + admin, digest jobs

**OUT:**
- Refactor de `backend/services/billing.py` além do necessário para teste passar
- Mudanças em Stripe webhooks handlers (coberto por BTS-008)
- PNCP-specific tests (movidos para BTS-010b)

---

## Contexto

Split da STORY-BTS-010 original após validação @po (2026-04-19) — contagem "~25 tests" era imprecisa e escopo heterogêneo (6 domínios) em S-effort era implausível.

Esta sub-story agrupa **14 testes** em 1 domínio coerente: **revenue infra** (billing + partners + feature flags). Complemento em BTS-010b (PNCP/security/misc).

---

## Valor

- **Billing integrity** — tests de partners, dunning, Stripe events purge validam que pagamentos não vazam ou duplicam
- **Feature flag hygiene** — matriz e admin flags guardam rollouts como CONV-003 (cartão obrigatório), STORY-GROWTH-001 (paid acquisition)
- **Digest job reliability** — cron reporting para admins depende desse path

---

## Riscos

- **Mock-drift em stripe_events_purge** pode esconder bug real de retenção. Mitigação: RCA AC3 deve distinguir mock-drift de prod bug.
- **Feature flag matrix** dependente de env vars externas. Mitigação: confirmar que test fixtures não dependem de config produção.

---

## Arquivos (tests — 14 testes exatos)

- `backend/tests/test_partners.py` (5 failures)
- `backend/tests/test_dunning.py` (2 failures)
- `backend/tests/test_harden028_stripe_events_purge.py` (1 failure)
- `backend/tests/test_feature_flag_matrix.py` (4 failures)
- `backend/tests/test_feature_flags_admin.py` (2 failures)

**Total: 14 failures em 5 arquivos.** (`test_digest_job.py` movido para BTS-010b por afinidade com infra/jobs misc, conforme decisão @po na re-validação 2026-04-19.)

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_partners.py backend/tests/test_dunning.py backend/tests/test_harden028_stripe_events_purge.py backend/tests/test_feature_flag_matrix.py backend/tests/test_feature_flags_admin.py -v --timeout=30` retorna exit code 0 (14/14 PASS).
- [ ] AC2: `backend-tests.yml` run mostra 5 arquivos com **0 failed**. Link no Change Log.
- [ ] AC3: RCA distinguindo (a) mock-drift stripe, (b) feature flag default change, (c) partner route path drift.
- [ ] AC4: Cobertura backend não caiu (threshold 70%).
- [ ] AC5 (NEGATIVO): zero quarantine novas.

---

## Investigation Checklist

- [ ] `grep -rn "ENABLE_NEW_PRICING\\|FEATURE_FLAG_MATRIX" backend/tests/test_feature_flag*.py backend/tests/test_partners.py` — ver se env var mudou
- [ ] Para `test_feature_flag_matrix`: se é data-driven, verificar se produção adicionou flags sem atualizar matrix
- [ ] Para `test_harden028_stripe_events_purge`: confirmar se cron de purge ainda existe em `backend/jobs/cron/`

---

## Dependências

- **Bloqueado por:** BTS-001 (quota), BTS-003 (plan reconciliation)
- **Bloqueia:** nenhum

---

## Change Log

- **2026-04-19** — @sm (River): Story criada do split BTS-010 (Opção A do @po review). Status Ready.
- **2026-04-19** — @po (Pax): Re-validação **GO 9/10**. Ajuste aplicado: `test_digest_job.py` removido do escopo (movido para BTS-010b por afinidade com infra/jobs misc); contagens reconciliadas (14 testes em 5 arquivos). Pontos atendidos: P1 título, P2 contexto + split rationale, P3 ACs testáveis, P4 Escopo IN/OUT formal, P5 deps (BTS-001+003), P6 Effort M, P7 Valor (3 bullets), P8 Riscos com mitigação, P10 alinhado ao EPIC. P9 DoD coberto pelos ACs (sem seção dedicada, mas verificável). Story confirmada **Ready**.
