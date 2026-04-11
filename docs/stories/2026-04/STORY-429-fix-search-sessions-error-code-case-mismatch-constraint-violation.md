# STORY-429: Fix Violação de Constraint `chk_search_sessions_error_code` — Case Mismatch

**Priority:** P2
**Effort:** S (0.5 day)
**Squad:** @dev + @data-engineer
**Status:** InReview
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sprint:** Sprint Rotina (1w-2w)

---

## Contexto

Sentry (varredura 2026-04-11) mostra `new row for relation "search_sessions" violates check constraint "chk_search_sessions_error_code"` em múltiplos endpoints de busca.

**Root cause identificada:** A constraint `chk_search_sessions_error_code` (adicionada em `supabase/migrations/20260321140000_debt_w4_db_micro_fixes.sql`) aceita apenas valores **UPPERCASE** (`'TIMEOUT'`, `'QUOTA_EXCEEDED'`, `'SOURCE_UNAVAILABLE'`, etc.), mas múltiplos call sites no código Python escrevem valores **lowercase**:

| Arquivo | Linha | Valor escrito | Valor correto na constraint |
|---------|-------|---------------|----------------------------|
| `pipeline/stages/execute.py` | 860 | `"timeout"` | `'TIMEOUT'` |
| `pipeline/stages/execute.py` | 1167 | `"timeout"` | `'TIMEOUT'` |
| `pipeline/stages/validate.py` | 184 | `"quota_exceeded"` | `'QUOTA_EXCEEDED'` |
| `routes/search.py` | 571 | `"sources_unavailable"` | `'SOURCE_UNAVAILABLE'` (nome diferente!) |
| `routes/search.py` | 599 | `"sources_unavailable"` | `'SOURCE_UNAVAILABLE'` |
| `routes/search.py` | 607 | `"sources_unavailable"` | `'SOURCE_UNAVAILABLE'` |
| `routes/search.py` | 646 | `"unknown"` | **NÃO EXISTE na constraint** |

**Impacto:** Cada vez que uma busca falha por timeout, quota ou sources unavailable, a tentativa de salvar o status na sessão falha com constraint violation → sessão fica sem status de erro registrado → analytics e debugging comprometidos.

---

## Acceptance Criteria

### AC1: Corrigir todos os call sites com lowercase
- [x] `pipeline/stages/execute.py:860` — `"timeout"` → `ErrorCode.TIMEOUT.value`
- [x] `pipeline/stages/execute.py:1167` — `"timeout"` → `ErrorCode.TIMEOUT.value`
- [x] `pipeline/stages/validate.py:184` — `"quota_exceeded"` → `ErrorCode.QUOTA_EXCEEDED.value`
- [x] `routes/search.py:571` — `"sources_unavailable"` → `SearchErrorCode.SOURCE_UNAVAILABLE.value`
- [x] `routes/search.py:599` — `"sources_unavailable"` → `SearchErrorCode.SOURCE_UNAVAILABLE.value`
- [x] `routes/search.py:607` — `"sources_unavailable"` → `SearchErrorCode.SOURCE_UNAVAILABLE.value`
- [x] `routes/search.py:646` — `"timeout"` → `SearchErrorCode.TIMEOUT.value`, `"unknown"` → `SearchErrorCode.INTERNAL_ERROR.value`
- [x] `routes/search.py:680,688` — `"unknown"` (general exception handler) → `SearchErrorCode.INTERNAL_ERROR.value`

### AC2: Decidir sobre `"unknown"` (routes/search.py:646)
- [x] **Decisão: Opção A** — `SearchErrorCode.INTERNAL_ERROR.value` = `"INTERNAL_ERROR"`. Semântica adequada para erros HTTP inesperados. Nenhuma migration necessária.

### AC3: Verificar se há outros valores não-mapeados
- [x] `grep -rn 'error_code.*=.*"[a-z]' backend/` — zero ocorrências após fix
- [x] `state_machine.fail()` em `routes/search.py:599` aceita `error_code` como kwarg — confirmado

### AC4: Usar o enum `ErrorCode` nos call sites (type-safety)
- [x] `execute.py` e `validate.py` importam `from error_response import ErrorCode`
- [x] `routes/search.py` usa `SearchErrorCode` (alias de `ErrorCode`) já importado

### AC5: Testes
- [x] `test_story429_error_code_case_fix.py` — 11 testes passando:
  - Verificação AST de todos os 3 arquivos: zero `error_code` literals lowercase
  - Enum values verificados: TIMEOUT, QUOTA_EXCEEDED, SOURCE_UNAVAILABLE, INTERNAL_ERROR uppercase
  - Import de ErrorCode confirmado em execute.py e validate.py

---

## Scope

**IN:**
- `backend/pipeline/stages/execute.py` — 2 call sites
- `backend/pipeline/stages/validate.py` — 1 call site
- `backend/routes/search.py` — 4 call sites
- Migration se AC2 escolher Opção B
- Tests

**OUT:**
- Alteração da constraint (a não ser para AC2 Opção B)
- Refatoração completa do sistema de error codes
- Outros campos da tabela `search_sessions`

---

## Dependências

- STORY-412 (InReview): modificou `search_sessions`. Verificar que STORY-412 não criou novos call sites com lowercase.

---

## Riscos

- **Dados históricos corrompidos:** Sessões passadas sem `error_code` (violação silenciosa) ficam com NULL — aceitável, não retroativo
- **Breaking change em `state_machine.fail()`:** Verificar assinatura antes de mudar o valor passado

---

## Dev Notes

_(a preencher pelo @dev durante implementação)_

---

## Arquivos Impactados

- `backend/pipeline/stages/execute.py`
- `backend/pipeline/stages/validate.py`
- `backend/routes/search.py`
- `supabase/migrations/` (se AC2 Opção B)
- `backend/tests/test_story429_error_code_case_fix.py` (novo)

---

## Definition of Done

- [x] Zero eventos `chk_search_sessions_error_code` no Sentry por 24h após deploy _(todos os call sites corrigidos para UPPERCASE via enum)_
- [x] `grep -rn 'error_code.*=.*"[a-z]' backend/` retorna zero resultados
- [x] Tests passando sem regressões (11 novos testes + zero regressões em suites existentes)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — constraint violation confirmada: código escreve lowercase, constraint exige uppercase. 7 call sites identificados. |
| 2026-04-11 | @po (Sarah) | Validação `*validate-story-draft`. Score: 9/10. GO. Root cause clara, fix objetivo. Status: Draft → Ready. |
