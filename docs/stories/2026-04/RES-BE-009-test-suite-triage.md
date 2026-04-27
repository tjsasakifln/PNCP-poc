# RES-BE-009: Test Suite Triage — 30s+ Timeout Tests (317/342 ≥30s)

**Priority:** P1
**Effort:** L (5-7 dias)
**Squad:** @qa + @dev (qa lidera)
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 3 (2026-05-13 → 2026-05-19) — paralelizável com RES-BE-010
**Dependências bloqueadoras:** Nenhuma (story horizontal)

---

## Contexto

Auditoria pós-P0 mediu **317 de 342 testes backend com `@pytest.mark.timeout >= 30s`** (~93% da suite). Isso é antipattern severo:

- **Timeout 30s+ mascara regressões reais** — teste lento por bug nunca falha por timeout, só "passa devagar"
- **Suite total CI estimada >12min** (alvo CLAUDE.md: <8min)
- **QA loop iterativo (RES-BE-005, 006, 007, 008)** fica inviável: cada iteração custa >10min de feedback
- **Memória `feedback_jwt_base64url_flaky_test`** já documenta que flakiness assumida esconde defeitos

Esta story é um **triage** — não um rewrite massivo. Cada teste com timeout ≥30s é classificado em 3 buckets:

1. **flaky** — falha intermitente (network, race condition, cleanup) → fix com `@pytest.mark.flaky(reruns=2)` ou refator determinístico
2. **slow_legitimate** — teste honestamente lento (e.g. integration test com LLM real, build SSG) → marca `@pytest.mark.slow`, isola em job CI separado
3. **refactor_target** — teste mal escrito (e.g. polling sleep, sequential await sem necessidade) → reduz timeout para ≤10s e refator

Meta: **≤50 testes >10s, suite total <8min CI**. P1 porque desbloqueia QA loop dos splits god-module (RES-BE-005..008).

---

## Acceptance Criteria

### AC1: Inventário e profiling

- [ ] Script `backend/scripts/profile_slow_tests.py`:
  - Lista todos os testes com `@pytest.mark.timeout(N)` onde `N >= 30`
  - Saída CSV: `test_path, test_name, current_timeout_s, last_runtime_s, classification_TODO`
  - Roda `pytest --collect-only` + parse de markers via plugin pytest customizado
- [ ] Saída commitada em `docs/qa/test-triage-2026-Q2.md` (markdown derivado do CSV)
- [ ] Total esperado: 317 testes listados (validar baseline)

### AC2: Classificação manual (priorizada)

- [ ] @qa percorre lista e classifica cada teste em:
  - `flaky` — re-run 5 vezes; se >1 falha → flaky
  - `slow_legitimate` — runtime médio >10s, sem sleep/polling pattern, justificável
  - `refactor_target` — runtime <10s mas timeout 30s+ (overkill) OU contém `await asyncio.sleep`/`time.sleep` em test body
- [ ] Classificação registrada em `docs/qa/test-triage-2026-Q2.md` em formato:
  ```markdown
  | Test | Classification | Action | Owner | Sprint |
  |---|---|---|---|---|
  | tests/test_pncp_client.py::test_fetch_phased | refactor_target | Reduce timeout 30→10s, mock asyncio.sleep | @qa | 3 |
  | tests/integration/test_llm_real.py::test_classify | slow_legitimate | Mark @pytest.mark.slow, move to separate CI job | @qa | 3 |
  ```

### AC3: Refactor target — pattern catalog

- [ ] Identificar 3+ patterns recorrentes em `refactor_target` e documentar em `docs/qa/refactor-patterns.md`:
  - **Pattern 1: Polling sleep** — substituir `for i in range(10): await asyncio.sleep(1); if condition: break` por `await asyncio.wait_for(future, timeout=N)`
  - **Pattern 2: Sequential awaits sem necessidade** — usar `asyncio.gather` quando independente
  - **Pattern 3: Real network call em unit test** — mockar httpx/Supabase via `respx`/conftest fixture
- [ ] Aplicar refator nos top-50 testes mais slow (medido por runtime real, não timeout configurado)
- [ ] Cada refator commit reduz timeout para ≤10s e mantém teste passing

### AC4: Slow legitimate — isolamento CI

- [ ] Adicionar marca `@pytest.mark.slow` no `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  markers = [
    "slow: tests that take >10s legitimately (LLM real, build SSG, etc.)",
  ]
  ```
- [ ] Workflow `backend-tests.yml` ganha 2 jobs:
  - `backend-tests-fast` (default): `pytest -m "not slow" --timeout=10`
  - `backend-tests-slow` (parallel): `pytest -m slow --timeout=120`
- [ ] Apenas `backend-tests-fast` é gate obrigatório de PR
- [ ] `backend-tests-slow` roda em PR mas não bloqueia merge (gate informativo)
- [ ] Nightly cron roda ambos com `--timeout=180` para detectar regressão crítica

### AC5: Flaky — quarantine + bug filing

- [ ] Testes classificados como `flaky` recebem `@pytest.mark.flaky(reruns=2, reruns_delay=1)` (`pytest-rerunfailures`)
- [ ] **OU** testes flaky severos (>20% failure rate em 50 runs) recebem `@pytest.mark.skip(reason="FLAKY-{issue_id}")` E issue GitHub aberto rastreando bug
- [ ] Lista de issues criados em `docs/qa/flaky-quarantine-2026-Q2.md`
- [ ] Skip não é bypass — cada skip tem deadline ≤30 dias para fix ou re-run

### AC6: Suite tempo total — meta <8min CI

- [ ] Após refator, medir suite total em CI (5 runs consecutivos):
  - `pytest backend/tests/ --timeout=30 -q` → tempo médio
  - Meta: tempo médio <8min wall-clock
  - Variance <30s entre runs (estabilidade)
- [ ] Se >8min, identificar bottleneck restante (provavelmente fixture global lenta) e refator

### AC7: CI gate de prevenção

- [ ] Adicionar pre-commit hook `.github/workflows/test-timeout-gate.yml`:
  - Falha PR se algum teste novo declara `@pytest.mark.timeout(N)` com `N > 10` E não tem marca `slow` ou justificação em comentário
  - Pattern: `re.search(r"@pytest\.mark\.timeout\((\d+)\)", source)` e check `int(group)`
- [ ] Allow-list em `.github/qa/timeout-allowlist.txt` para legítimos (e.g. integration tests existentes não migrados)
- [ ] PR template ganha checkbox "Se este PR adiciona teste com timeout >10s, justifiquei e/ou marquei como `slow`"

### AC8: Testes (gate final)

- [ ] Suite backend passa com `--timeout=10` (default sem `slow`) e `--timeout=120` (com `slow`)
- [ ] CI tempo total `backend-tests-fast` <8min wall-clock
- [ ] Sem regressão de cobertura (manter ≥70% global)
- [ ] Sem novos warnings pytest

---

## Scope

**IN:**
- Inventário 317 testes timeout ≥30s
- Classificação flaky/slow/refactor_target
- Refator dos top-50 `refactor_target`
- Marca `@pytest.mark.slow` + isolamento CI
- Pattern catalog `docs/qa/refactor-patterns.md`
- Pre-commit hook prevenção timeout grande
- Documentação `docs/qa/test-triage-2026-Q2.md`

**OUT:**
- Refator de TODOS 317 (escopo Sprint 3+ se prioridade subir; story atual cobre top-50)
- Reescrita de testes integration com fixture nova de banco — escopo separado
- Migração para pytest-xdist (parallel) — escopo futuro RES-BE-014+
- Adicionar testes novos para cobrir gaps — story atual NÃO adiciona testes
- Mudança de framework pytest → outro — proibido

---

## Definition of Done

- [ ] Inventário CSV/markdown commitado
- [ ] 317 testes classificados em flaky/slow_legitimate/refactor_target
- [ ] Top-50 `refactor_target` refatorados (timeout ≤10s)
- [ ] Marca `@pytest.mark.slow` registrada em `pyproject.toml`
- [ ] Workflow `backend-tests.yml` separa fast vs slow
- [ ] CI tempo total `backend-tests-fast` <8min wall-clock (5 runs validados)
- [ ] Pre-commit hook `test-timeout-gate.yml` ativo
- [ ] Documentos `docs/qa/test-triage-2026-Q2.md`, `refactor-patterns.md`, `flaky-quarantine-2026-Q2.md` criados
- [ ] Cobertura ≥70% global mantida
- [ ] Sem regressão (5131+ tests passing, 0 failures)
- [ ] CodeRabbit clean
- [ ] PR review por @qa (Quinn — author) + @architect (Aria) com verdict PASS
- [ ] CLAUDE.md "Testing Strategy" atualizado com referência a `@pytest.mark.slow` e novo workflow

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/scripts/profile_slow_tests.py` (novo)
- `/mnt/d/pncp-poc/docs/qa/test-triage-2026-Q2.md` (novo)
- `/mnt/d/pncp-poc/docs/qa/refactor-patterns.md` (novo)
- `/mnt/d/pncp-poc/docs/qa/flaky-quarantine-2026-Q2.md` (novo)
- `/mnt/d/pncp-poc/.github/workflows/backend-tests.yml` (modificar — adicionar slow job)
- `/mnt/d/pncp-poc/.github/workflows/test-timeout-gate.yml` (novo)
- `/mnt/d/pncp-poc/.github/qa/timeout-allowlist.txt` (novo)
- `/mnt/d/pncp-poc/backend/pyproject.toml` (adicionar marker `slow`)
- `/mnt/d/pncp-poc/backend/tests/` — top-50 refators

### Padrão referência

- CLAUDE.md "Anti-Hang Rules" — `pytest-timeout`, `timeout_method = "thread"`
- Memory `feedback_jwt_base64url_flaky_test` — flakiness pode esconder bug real
- pytest plugins: `pytest-timeout`, `pytest-rerunfailures`

### Tools

- pytest plugin para profiling: `pytest --durations=50` (já built-in)
- pytest-rerunfailures: `pip install pytest-rerunfailures` (adicionar `requirements-dev.txt`)
- Custom plugin script `profile_slow_tests.py` usa `_pytest.config.PytestPluginManager` para coletar markers

### Frameworks de teste

- pytest 8.x
- File location de testes refatorados: `backend/tests/<original_path>`
- Marks novos: `@pytest.mark.slow`
- Não adicionar `@pytest.mark.flaky` sem issue tracking — sem deadline = nunca fixa

### Convenções

- Refator preserva semântica do teste (não muda assertion)
- Mock de I/O via `monkeypatch` ou conftest fixture
- `asyncio.sleep(N)` em test body é code smell — substituir por `await asyncio.wait_for(...)`
- Evitar `time.sleep` em testes async

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| Refator quebra teste (assertion behavior diferente) | Revert commit; refator preserva semântica obrigatoriamente |
| `@pytest.mark.slow` esquecido em integration test → CI fast quebra | Adicionar marca ou aumentar timeout específico; PR fix |
| Test que passou ser classificado flaky desnecessariamente | Re-run 50 vezes; se 0 falhas, remover quarentena |
| CI tempo regredir após refator (paralelização ineficiente) | Profile com `--durations=50`; ajustar fixture scopes; considerar pytest-xdist |
| Testes legítimos slow sem opção de mock | `@pytest.mark.slow` é caminho — não force refator artificial |

**Rollback completo:** revert PR. Suite volta ao estado original (>12min CI). Não há rollback de feature flag — é refator estrutural.

---

## Dependencies

**Entrada:** Nenhuma (horizontal).

**Saída (esta story bloqueia):**
- [RES-BE-005](RES-BE-005-godmodule-split-pipeline.md) — QA loop dos splits exige feedback rápido
- [RES-BE-006](RES-BE-006-godmodule-split-metrics.md)
- [RES-BE-007](RES-BE-007-godmodule-split-blogstats.md)
- [RES-BE-008](RES-BE-008-godmodule-split-admin.md)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | "Test Suite Triage — 30s+ Timeout Tests (317/342 ≥30s)" — métrica baseline + alvo. |
| 2 | Complete description | ✓ | 3 buckets (flaky/slow_legitimate/refactor_target) com critérios de classificação. |
| 3 | Testable acceptance criteria | ✓ | 8 ACs incluindo SLA mensurável (CI <8min wall-clock, 5 runs validados). |
| 4 | Well-defined scope | ✓ | IN/OUT delimitados — top-50 refator (não 317), prevenção via gate, sem rewrite massivo. |
| 5 | Dependencies mapped | ✓ | Horizontal (sem entrada); saída bloqueia RES-BE-005/006/007/008 (QA loop iterativo). |
| 6 | Complexity estimate | ✓ | L (5-7 dias) coerente — inventário + classificação + 50 refators + workflow + hook. |
| 7 | Business value | ✓ | "QA loop iterativo dos splits god-module fica inviável" — desbloqueia 4 stories downstream. |
| 8 | Risks documented | ✓ | 5 riscos incluindo regressão de paralelização CI; rollback = revert. |
| 9 | Criteria of Done | ✓ | 14 itens DoD incluindo 5 runs CI validados (estabilidade) e cobertura ≥70% global mantida. |
| 10 | Alignment with PRD/Epic | ✓ | Métrica EPIC #6 (CI <8min) é AC6 desta story; bloqueia QA loop dos splits. |

### Required Fixes

Nenhuma.

### Observations

- SLA testáveis: CI <8min wall-clock validado em 5 runs, variance <30s. Forte gate quantitativo.
- Pre-commit hook `test-timeout-gate.yml` previne regressão futura — boa prática preventiva.
- Allow-list `.github/qa/timeout-allowlist.txt` permite migração incremental — pragmático.
- Memory `feedback_jwt_base64url_flaky_test` referenciada — alinhamento com lições anteriores.
- Top-50 escopo vs 317 total é decisão pragmática e bem comunicada.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — triage 317 testes timeout 30s+ | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). SLA testáveis, top-50 escopo pragmático, prevenção via gate. Status: Draft → Ready. | @po (Pax) |
