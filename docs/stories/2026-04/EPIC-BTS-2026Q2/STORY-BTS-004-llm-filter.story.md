# STORY-BTS-004 — LLM Zero-Match & Filter Pipeline (16 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P1
**Effort:** S (2-3h)
**Agents:** @dev + @qa
**Status:** Done (PR #400 merged `8190f24f` — 2026-04-19)

---

## Contexto

16 testes cobrindo LLM zero-match classifier + filter pipeline (filtrar prazo aberto, arbiter parallel, async zero-match, setor pipeline). Esses testes validam a camada de classificação GPT-4.1-nano. Refactors recentes (GTM-FIX-028 LLM batch, STORY-354 pending review) provavelmente movem símbolos.

---

## Arquivos (tests)

- `backend/tests/test_llm_zero_match.py` (6 failures)
- `backend/tests/test_filtrar_prazo_aberto.py` (6 failures)
- `backend/tests/test_crit059_async_zero_match.py` (2 failures)
- `backend/tests/test_crit_flt_002_arbiter_parallel.py` (1 failure)
- `backend/tests/test_crit_019_setor_pipeline.py` (1 failure)

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_llm_zero_match.py backend/tests/test_filtrar_prazo_aberto.py backend/tests/test_crit059_async_zero_match.py backend/tests/test_crit_flt_002_arbiter_parallel.py backend/tests/test_crit_019_setor_pipeline.py -v --timeout=30` retorna exit code 0 (16/16 PASS).
- [ ] AC2: CI `backend-tests.yml` 0 failed nesses 5 arquivos.
- [ ] AC3: RCA distinguindo (a) mock-drift de `llm_arbiter._get_client`, (b) feature flag default change (ex: LLM_FALLBACK_PENDING_ENABLED), (c) zero-match prompt template change.
- [ ] AC4: Cobertura não caiu.
- [ ] AC5: zero quarantine.

---

## Investigation Checklist

- [ ] `grep -rn "_get_client\\|classify_zero_match\\|llm_arbiter" backend/tests/test_llm*.py backend/tests/test_crit*arbiter*.py`
- [ ] Cross-check produção em `backend/llm_arbiter.py` atual
- [ ] Se prompt mudou: atualizar assertion sobre resposta esperada

---

## Dependências

- **Bloqueado por:** BTS-001 (quota/plan capabilities influence filter)
- **Bloqueia:** nenhum (filter é upstream de outras áreas)

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready.
- **2026-04-19** — @po (Pax): Validação GO — 7/10. Gaps: P4 escopo, P7 valor, P8 riscos. Story confirmada Ready.
