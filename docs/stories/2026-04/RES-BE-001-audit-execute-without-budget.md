# RES-BE-001: Auditoria Automatizada `.execute()` sem Budget Temporal — CI Gate

**Priority:** P0
**Effort:** M (2-3 dias)
**Squad:** @devops + @dev
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 1 (2026-04-29 → 2026-05-05) — bloqueador de RES-BE-002, RES-BE-004, RES-BE-005..008
**Dependências bloqueadoras:** Nenhuma (foundation)

---

## Contexto

O incidente P0 de 2026-04-27 (PR #529) foi causado por chamadas `.execute()` Supabase **síncronas, sem budget temporal**, em rotas HTTP críticas. Quando o pool de 10 conexões saturou sob a wave Googlebot, cada request ficou bloqueado indefinidamente no event loop até Railway matar a 120s — wedge total. O hotfix protegeu apenas 2 endpoints (`routes/empresa_publica.py:169`, `routes/contratos_publicos.py:450`) wrappando-os em `_run_with_budget` (definido em `backend/pipeline/budget.py:28-93`).

Auditoria manual (grep `\.execute()` em `backend/routes/`) identificou **56 callsites restantes** distribuídos em 30+ módulos:

| Módulo | Callsites |
|---|---|
| `routes/mfa.py` | 10 |
| `routes/referral.py` | 7 |
| `routes/sitemap_*.py` (vários) | 7 (total) |
| `routes/founding.py` | 4 |
| `routes/conta.py` | 4 |
| `routes/features.py` | 3 |
| `routes/user.py` | 2 |
| Outros 20+ módulos | 1 cada |

Sem um **gate CI determinístico**, novos PRs continuam introduzindo `.execute()` sem budget — regressão silenciosa garantida pela ausência de detecção. Esta story estabelece o piso: um script Python AST percorre `backend/routes/*.py`, detecta `.execute()` Supabase fora de `_run_with_budget` ou `asyncio.wait_for`, e falha o CI se a contagem aumentar acima do baseline congelado.

Sem este gate, RES-BE-002 (correção das top-5 rotas) corrige um snapshot, mas não mantém a invariante. Por isso esta story é P0 Sprint 1 e bloqueia toda a sequência subsequente do epic.

---

## Acceptance Criteria

### AC1: Script de auditoria AST

- [ ] Criar `backend/scripts/audit_execute_without_budget.py`
- [ ] Script percorre recursivamente `backend/routes/**/*.py` usando `ast.parse` + `ast.walk`
- [ ] Detecta nodes `ast.Attribute` cujo `attr == "execute"` sendo chamados (`ast.Call`)
- [ ] Marca um callsite como **PROTEGIDO** se está dentro de:
  - Função wrapper `_run_with_budget(...)` (qualquer profundidade)
  - `asyncio.wait_for(...)` (qualquer profundidade)
  - `with_negative_cache` decorator (provedor implícito de timeout — opcional, ver RES-BE-003)
- [ ] Marca um callsite como **DESPROTEGIDO** caso contrário
- [ ] Distingue `.execute()` Supabase (objeto retornado por chains tipo `.from_().select().execute()`) de outros `.execute()` (e.g. SQLAlchemy core, subprocess) via heurística de chain pattern (ver Dev Notes)
- [ ] Saída JSON estruturada em stdout:
  ```json
  {
    "total_callsites": 56,
    "protected": 2,
    "unprotected": 54,
    "unprotected_by_module": {
      "backend/routes/mfa.py": [{"line": 47, "snippet": "..."}, ...]
    }
  }
  ```

### AC2: Relatório markdown

- [ ] Script aceita flag `--output-md docs/audit/execute-without-budget-{date}.md`
- [ ] Relatório contém:
  - Header com data, total, protegidos, desprotegidos
  - Tabela ordenada por módulo (descending por count) com `path:line` clicável
  - Snippet de 3 linhas ao redor de cada callsite (contexto)
  - Seção "Baseline congelado" com hash SHA-256 do conteúdo do JSON ordenado
- [ ] Primeiro relatório baseline gerado e commitado em `docs/audit/execute-without-budget-2026-04-28.md`

### AC3: CI gate workflow

- [ ] Criar `.github/workflows/audit-execute-budget.yml`:
  ```yaml
  name: Audit .execute() without budget
  on:
    pull_request:
      paths:
        - 'backend/routes/**'
        - 'backend/scripts/audit_execute_without_budget.py'
  jobs:
    audit:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: { python-version: '3.12' }
        - run: python backend/scripts/audit_execute_without_budget.py --check-baseline backend/scripts/audit-baseline.json
  ```
- [ ] Job falha (exit 1) se `unprotected` aumentar acima do baseline JSON
- [ ] Job tem permissão para postar comentário em PR resumindo regressão (lista de novos callsites)
- [ ] Baseline `backend/scripts/audit-baseline.json` commitado com snapshot inicial (54 unprotected)

### AC4: Suporte para baseline decremental

- [ ] Script aceita flag `--update-baseline` para regerar `audit-baseline.json` (usado quando RES-BE-002..010 reduzem unprotected count)
- [ ] CI gate aceita decrease (unprotected < baseline), apenas falha em increase
- [ ] Documentação no `docs/audit/README.md` explica fluxo: PR que reduz unprotected deve atualizar baseline na mesma PR
- [ ] PR template (`.github/pull_request_template.md`) ganha checkbox "Atualizei `audit-baseline.json` se reduzi callsites desprotegidos"

### AC5: Detecção de regressões em PRs

- [ ] Test fixture em `backend/tests/scripts/test_audit_execute_without_budget.py`:
  - Caso 1: arquivo só com `.execute()` desprotegido → conta 1 unprotected
  - Caso 2: arquivo com `await _run_with_budget(supabase.from_().select().execute(), ...)` → conta 0 unprotected
  - Caso 3: arquivo com `asyncio.wait_for(supabase.from_().select().execute(), timeout=3)` → conta 0 unprotected
  - Caso 4: arquivo com `subprocess.run(...).execute()` (não-Supabase) → conta 0
  - Caso 5: arquivo com chain `.from_().update().eq().execute()` desprotegido → conta 1 unprotected
- [ ] Test garante que script retorna exit 1 quando `--check-baseline` detecta increase
- [ ] Test garante exit 0 quando count == baseline ou < baseline

### AC6: Telemetria & docs

- [ ] Resultado do audit em produção (count por módulo) é publicado como artefato em `gh-pages` ou similar para tendência histórica (opcional MVP — TODO @architect: decidir storage)
- [ ] `CLAUDE.md` ganha seção "## Resilience CI Gates" com referência ao novo workflow e link para `docs/audit/`
- [ ] Runbook `docs/runbooks/audit-execute-budget.md`: como rodar localmente, como atualizar baseline, como triagem de falso-positivo

### AC7: Testes

- [ ] **Unit tests:** `backend/tests/scripts/test_audit_execute_without_budget.py` — 8+ casos cobrindo true positive, true negative, e edge cases (chain longo, decorator, walrus operator, async generator)
- [ ] **Integration test:** rodar script contra fixture de `backend/routes/` real (snapshot atual) e validar count == baseline
- [ ] **CI dry run:** abrir PR de teste introduzindo `.execute()` desprotegido em arquivo dummy e confirmar gate falha
- [ ] Cobertura ≥85% nas linhas tocadas (`audit_execute_without_budget.py`)

---

## Scope

**IN:**
- Script Python AST `audit_execute_without_budget.py`
- Workflow CI `audit-execute-budget.yml`
- Baseline JSON congelado
- Relatório markdown inicial
- Testes unitários + integration
- Documentação CLAUDE.md + runbook

**OUT:**
- Correção dos 54 callsites desprotegidos (responsabilidade RES-BE-002 e seguintes)
- Audit de outros padrões I/O (e.g. Redis, httpx) — pode virar story futura RES-BE-014+
- Audit em `backend/services/`, `backend/jobs/` — escopo Sprint 2+ se priorizado

---

## Definition of Done

- [ ] Script implementado, testado, lint clean (ruff + mypy)
- [ ] Workflow CI funcional, validado em PR de teste
- [ ] Baseline `audit-baseline.json` commitado com 54 unprotected (ou número exato medido)
- [ ] Relatório `docs/audit/execute-without-budget-2026-04-28.md` commitado
- [ ] Cobertura testes ≥85% nas linhas tocadas
- [ ] CLAUDE.md atualizado (seção "Resilience CI Gates")
- [ ] Runbook `docs/runbooks/audit-execute-budget.md` criado
- [ ] CodeRabbit review clean (CRITICAL=0, HIGH=0)
- [ ] PR review por @architect (Aria) + @qa (Quinn) com verdict PASS
- [ ] Sem regressão em testes existentes (5131+ passing, 0 failures)

---

## Dev Notes

### Paths absolutos

- **Script:** `/mnt/d/pncp-poc/backend/scripts/audit_execute_without_budget.py` (novo)
- **Baseline:** `/mnt/d/pncp-poc/backend/scripts/audit-baseline.json` (novo)
- **Workflow:** `/mnt/d/pncp-poc/.github/workflows/audit-execute-budget.yml` (novo)
- **Tests:** `/mnt/d/pncp-poc/backend/tests/scripts/test_audit_execute_without_budget.py` (novo)
- **Runbook:** `/mnt/d/pncp-poc/docs/runbooks/audit-execute-budget.md` (novo)
- **Relatório baseline:** `/mnt/d/pncp-poc/docs/audit/execute-without-budget-2026-04-28.md` (novo)

### Padrão referência

- **Wrapper canônico:** `backend/pipeline/budget.py::_run_with_budget` (L28-93) — única função que conta como "protegido"
- **Hotfix precedente:** PR #529 commit `11b368cc` — exemplos `routes/empresa_publica.py:169` e `routes/contratos_publicos.py:450` são fixtures de "protegido"

### Heurística de detecção Supabase vs outros `.execute()`

Supabase Python SDK encadeia: `client.from_("table").select("*").eq("id", x).execute()`. Heurística:

1. Walk chain ascending de `Call` → `Attribute(attr="execute")`
2. Se em algum ponto da chain aparecer `from_`, `select`, `insert`, `update`, `delete`, `upsert`, `rpc` → considera Supabase
3. Caso contrário (e.g. `proc.execute()` de subprocess), ignora

Edge case: `supabase.table("x").select(...).execute()` — `table` não está na lista; adicionar.

TODO @architect: confirmar se vale escopo paralelo `backend/services/billing.py` e similares; assumir NÃO neste MVP — apenas `backend/routes/`.

### Frameworks de teste

- pytest 8.x + pytest-asyncio
- File location pattern: `backend/tests/scripts/test_<module>.py`
- Marks: `@pytest.mark.timeout(5)` (script é fast)
- Sem fixtures externas (Supabase mock não necessário; teste opera sobre AST)

### Convenções

- Type hints obrigatórios (mypy strict mode em `backend/scripts/`)
- Imports absolutos (Constitution Article VI)
- Logger com `logging.getLogger(__name__)`
- CLI args via `argparse` (não click — manter dependências CI mínimas)

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| Script tem falso-positivo (marca código protegido como desprotegido) e bloqueia PR válido | Atualizar heurística + adicionar fixture; `--update-baseline` temporário até fix |
| Gate CI fica lento (>2min) | Profile com `cProfile`; cache AST por módulo via mtime |
| Baseline drift acidental (alguém commita `--update-baseline` sem reduzir count) | Pre-commit hook valida baseline contra count atual; revert PR ofensivo |
| Workflow falha por mudança de path patterns (e.g. `backend/routes/` renomeado) | Atualizar workflow `paths:` + script glob; documentar no runbook |
| Falso negativo (script perde callsite por padrão exótico) | Adicionar fixture do padrão; regenerar baseline; abrir bug |

**Rollback completo:** revert do PR; CI gate desliga automaticamente. Não há mudança de runtime/produção, apenas CI/docs.

---

## Dependencies

**Entrada:** Nenhuma — story foundation. Padrão `_run_with_budget` já existe em `backend/pipeline/budget.py`.

**Saída (esta story bloqueia):**
- RES-BE-002 (top-5 routes) — usa script para validar correção
- RES-BE-004 (datalake observability) — sem dependência funcional, mas linha temporal
- RES-BE-005, 006, 007, 008 (god-module splits) — devem manter baseline

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | "Auditoria Automatizada `.execute()` sem Budget Temporal — CI Gate" — escopo unívoco. |
| 2 | Complete description | ✓ | Contexto liga incidente P0 → 56 callsites → necessidade de gate determinístico. |
| 3 | Testable acceptance criteria | ✓ | 7 ACs com checklist itens (AC1-AC7); fixtures explícitas em AC5; comandos CLI testáveis. |
| 4 | Well-defined scope | ✓ | IN/OUT taxativos; OUT delimita correção (RES-BE-002), Redis/httpx audit (futuro). |
| 5 | Dependencies mapped | ✓ | Foundation (sem entrada); saída lista RES-BE-002, 004, 005-008. |
| 6 | Complexity estimate | ✓ | M (2-3 dias) coerente com escopo (script + workflow + baseline + tests). |
| 7 | Business value | ✓ | "Previne regressão silenciosa" + bloqueio Sprint 1 explicado em contexto. |
| 8 | Risks documented | ✓ | 5 cenários de risco com ação de rollback; rollback completo (revert) trivial. |
| 9 | Criteria of Done | ✓ | 11 itens DoD bem definidos: lint, baseline, runbook, CodeRabbit, QA gate. |
| 10 | Alignment with PRD/Epic | ✓ | Métrica #4 do EPIC ("% rotas com `_run_with_budget`") depende deste gate. |

### Required Fixes

Nenhuma — story pronta para implementação.

### Observations

- AC6 storage de audit history marcado como "opcional MVP — TODO @architect" — não bloqueia (está fora do path crítico de CI gate).
- AC2 "Primeiro relatório baseline" referencia data `2026-04-28` (D+1) — coerente com Sprint 1 start 29/abr.
- @dev deve confirmar exato número de unprotected callsites (54 estimado pode oscilar conforme PR #529 já tenha merged em produção).

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada a partir do plano de auditoria pós-P0 | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Story pronta para Sprint 1, foundation epic. Status: Draft → Ready. | @po (Pax) |
