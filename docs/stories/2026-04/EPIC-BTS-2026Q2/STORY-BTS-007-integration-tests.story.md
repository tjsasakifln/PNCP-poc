# STORY-BTS-007 — Integration Tests → External Workflow (5 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P2 — Preserva zero-failure policy no gate sem depender de infra externa
**Effort:** S (2-3h)
**Agents:** @dev + @devops
**Status:** Ready

---

## Escopo

**IN:**
- Mover `backend/tests/integration/*` para workflow separado não-bloqueante
- Atualizar `.github/workflows/backend-tests.yml` para excluir `tests/integration/`
- Criar workflow `backend-tests-external.yml` (non-blocking, advisory)
- Adicionar unit tests equivalentes para preservar coverage ≥ 70%

**OUT:**
- Reescrever lógica dos integration tests (mantêm como estão, só mudam de gate)
- Provisionar infra (Redis, Supabase) no CI
- Alterar assinaturas de produção

---

## Contexto

5 testes em `backend/tests/integration/` rodam contra serviços reais (Redis, Supabase, possivelmente OpenAI). CI não provisiona essa infra, causando failures não-relacionadas à lógica de negócio.

**Decisão @po 2026-04-19:** direção **(a)** aprovada — mover para suite `external` não-bloqueante. Tests de integração contra serviços reais validam disponibilidade de infraestrutura, não lógica. O CI gate deve garantir zero falha em lógica; não deve falhar por indisponibilidade externa. Unit tests equivalentes preservam coverage.

---

## Valor

- **Mantém zero-failure policy no CI gate** sem depender de infra externa provisionada
- **Preserva testes integration executáveis** via workflow dedicado (opt-in, diagnóstico)
- **Reduz falsos positivos** que confundem triagem de bugs reais

---

## Riscos

- **Coverage pode cair** se unit tests equivalentes não forem adicionados. Mitigação: AC4 explícito + verificar threshold antes de merge.
- **Perda de sinal de quebra na integração** se external workflow for ignorado. Mitigação: agendar workflow external 1×/dia em schedule + alertar Sentry em falha.

---

## Arquivos (tests + workflows)

**Tests (mover, não editar):**
- `backend/tests/integration/test_full_pipeline_cascade.py` (3 failures → mover)
- `backend/tests/integration/test_queue_worker_fail_inline.py` (2 failures → mover)

**Workflows:**
- `.github/workflows/backend-tests.yml` (modificar — adicionar `--ignore=tests/integration/`)
- `.github/workflows/backend-tests-external.yml` (novo — runs integration + schedule diário)

**Novos unit tests equivalentes (preservar coverage):**
- `backend/tests/test_pipeline_cascade_unit.py` (novo — cobre cenários críticos de cascade com mocks)
- `backend/tests/test_queue_worker_inline_unit.py` (novo — cobre inline fallback com mocks)

---

## Acceptance Criteria

- [ ] AC1: Decisão documentada: **direção (a) aprovada pelo @po em 2026-04-19**. Mover `tests/integration/` para workflow `backend-tests-external.yml` não-bloqueante.
- [ ] AC2: `.github/workflows/backend-tests.yml` exclui `tests/integration/` do gate (adicionar `--ignore=tests/integration/` ao pytest command).
- [ ] AC3: `.github/workflows/backend-tests-external.yml` criado, executa `pytest tests/integration/` com Redis+Supabase service containers (ou mocks fortes), roda em PR + schedule diário; **não bloqueia merge** (`continue-on-error: true` ou job `if: github.event_name == 'schedule'`).
- [ ] AC4: Cobertura backend **não caiu** (threshold 70% mantido). Novos unit tests equivalentes adicionados conforme File List.
- [ ] AC5 (NEGATIVO): grep `@pytest.mark.skip|pytest.skip\\(|@pytest.mark.xfail` vazio nos arquivos tocados — Zero Quarentena policy.

---

## Definition of Done

- [ ] AC1-AC5 todos marcados `[x]`
- [ ] `backend-tests.yml` CI run mostra que `tests/integration/` não é mais executado no gate
- [ ] `backend-tests-external.yml` executa em PR + schedule diário; última run tem status visível
- [ ] Coverage report ≥ 70% mantido pós-mudança (evidência: link run ID no Change Log)

---

## Investigation Checklist (para @devops, fase Implement)

- [ ] Decidir entre service containers (Redis/Supabase mock via `postgres:15` + fakeredis) vs mocks fortes no workflow
- [ ] Validar que pytest marker `integration` já existe em `backend/tests/integration/conftest.py` (se sim, reusar; se não, adicionar)
- [ ] Confirmar `--ignore=tests/integration/` no gate + schedule cron em external workflow

---

## Dependências

- **Bloqueado por:** nenhum (pode rodar em paralelo)
- **Bloqueia:** nenhum

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready. @po precisa aprovar direção (a) vs (b) antes de implement.
- **2026-04-19** — @po (Pax): Validação NO-GO — 4/10. ACs bifurcados sem direção decidida (P3 ✗), DoD incompleto (P9 ✗). Status revertido para Draft. DECISÃO EMITIDA: Direção (a) aprovada.
- **2026-04-19** — @sm (River): Correções aplicadas. ACs atualizados para refletir somente path (a). Removido AC2b. Adicionadas seções Escopo, Valor, Riscos. Status Draft → Ready. Aguarda re-validação @po.
