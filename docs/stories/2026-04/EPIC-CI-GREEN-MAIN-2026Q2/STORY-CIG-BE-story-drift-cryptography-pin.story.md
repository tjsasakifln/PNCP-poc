# STORY-CIG-BE-story-drift-cryptography-pin — `requirements.txt` pin obsoleto — 2 testes static-scan assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
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

- [x] AC1: `pytest backend/tests/test_story303_crash_recovery.py -v` retorna exit code 0 localmente (2/2 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [x] AC3: Causa raiz descrita em "Root Cause Analysis" (assertion-drift). Referenciar CVE que motivou o update para `>=46.0.6`.
- [x] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [x] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Root Cause Analysis

**Classificação:** Assertion-drift (conforme triage row #27/30).

**Fato:** `backend/tests/test_story303_crash_recovery.py` contém dois testes static-scan em `backend/requirements.txt`:

1. `test_ac10_cryptography_pinned_exact` — assertava `"cryptography==46.0.5" in content` (exact pin literal).
2. `test_ac10_no_cryptography_greater_than` — assertava `">=" not in stripped` para a linha do pacote `cryptography`.

**Porém** o `requirements.txt` migrou de `cryptography==46.0.5` para `cryptography>=46.0.6,<47.0.0` devido às CVEs:

- **CVE-2026-26007** — corrigida em `cryptography 46.0.6`.
- **CVE-2026-34073** — corrigida em `cryptography 46.0.6`.

O pin exato original (STORY-303) foi estabelecido para garantir fork-safety com Gunicorn `--preload` (OpenSSL C bindings). O range `>=46.0.6,<47.0.0` preserva a fork-safety (cap `<47.0.0` — 47.x unreleased e não testado) e permite pegar fixes de patch dentro da série 46.0.x (DEBT-SYS-002, comentado em `requirements.txt`).

**Fix aplicado (test-only, sem alterar código de produção):**

- `test_ac10_cryptography_pinned_exact` — agora valida o invariante real: (a) upper bound `<47.0.0` presente (fork-safety) e (b) lower bound `>= 46.0.6` (CVE floor), parseando a versão com regex em vez de comparar string literal.
- `test_ac10_no_cryptography_greater_than` — renomeado em spirit: agora valida que o cap `<47.0.0` está presente, em vez de proibir `>=`. O nome do método foi preservado para compatibilidade de histórico (CI, relatórios).
- Docstrings atualizadas referenciando esta story e as CVEs para audit trail.
- `test_ac11_cryptography_has_fork_safety_comment` — **não alterado** (já passa; fork-safety comment continua em `requirements.txt`).

**Nenhuma regressão de produção.** Nenhuma alteração em `backend/requirements.txt` (out of scope — pin já está correto).

---

## File List

- **MODIFIED:** `backend/tests/test_story303_crash_recovery.py` — 2 test methods (`test_ac10_cryptography_pinned_exact`, `test_ac10_no_cryptography_greater_than`) refactored from literal-string static scan to semantic invariant check (upper cap + CVE floor). Docstrings atualizadas com referência à story e CVEs.

---

## Investigation Checklist (para @dev, fase Implement)

- [x] Rodar `pytest backend/tests/test_story303_crash_recovery.py -v` isolado.
- [x] `grep "cryptography" backend/requirements.txt` — confirmar pin atual (`>=46.0.6,<47.0.0`).
- [x] Atualizar static-scan para aceitar range em vez de exact pin.
- [x] Validar cobertura não regrediu.
- [x] Grep de skip markers vazio nos testes tocados (skip markers existentes em `TestCryptographyImport` são pré-existentes e fora do escopo).

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #27/30)

## Stories relacionadas no epic

- nenhuma (story isolada — static scan de requirements)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #27/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (8/10)** — Draft → Ready. Fix one-line trivial; preferir range match em static-scan (aceitar futuras bumps dentro de `<47.0.0`).
- **2026-04-18** — @dev: Implement. Refactored 2 static-scan tests em `backend/tests/test_story303_crash_recovery.py` de literal `"cryptography==46.0.5"` para semantic invariant check: (a) upper cap `<47.0.0` presente (fork-safety, DEBT-SYS-002), (b) lower bound parseado via regex e >= 46.0.6 (CVE-2026-26007 + CVE-2026-34073 floor). Nenhuma alteração em `backend/requirements.txt` ou código de produção. Suíte local: `27 passed` (2 previously failing now PASS). Status Ready → InReview. Aguarda `@qa *qa-gate` e run verde de `backend-tests.yml` para fechar AC2.
