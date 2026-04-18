# STORY-CIG-BE-story-drift-cryptography-pin — `requirements.txt` pin obsoleto — 2 testes static-scan assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P2 — Gate
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_story303_crash_recovery.py` roda em `backend-tests.yml` e falha em **2 testes** do triage row #27/30. Causa raiz classificada como **assertion-drift**: os testes fazem static-scan em `backend/requirements.txt` e esperam `cryptography==46.0.5` (pin exato). Porém o projeto migrou para `cryptography>=46.0.6,<47.0.0` por CVE (conforme triage doc).

A assertion está obsoleta; não é bug. Fix é single-line update no teste.

**Arquivos principais afetados:**
- `backend/tests/test_story303_crash_recovery.py` (2 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Assertion-drift trivial. Fix: atualizar regex/string esperada no static-scan para refletir pin atual (range `>=46.0.6,<47.0.0`).

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_story303_crash_recovery.py -v` retorna exit code 0 localmente (2/2 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (assertion-drift). Referenciar CVE que motivou o update para `>=46.0.6`.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_story303_crash_recovery.py -v` isolado.
- [ ] `grep "cryptography" backend/requirements.txt` — confirmar pin atual.
- [ ] Atualizar static-scan para aceitar range em vez de exact pin.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #27/30)

## Stories relacionadas no epic

- nenhuma (story isolada — static scan de requirements)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #27/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
