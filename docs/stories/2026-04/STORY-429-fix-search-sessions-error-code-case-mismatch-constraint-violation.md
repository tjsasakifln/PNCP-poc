# STORY-429: Fix Violação de Constraint `chk_search_sessions_error_code` — Case Mismatch

**Priority:** P2
**Effort:** S (0.5 day)
**Squad:** @dev + @data-engineer
**Status:** Ready
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
- [ ] `pipeline/stages/execute.py:860` — trocar `"timeout"` por `ErrorCode.TIMEOUT.value` (= `"TIMEOUT"`)
- [ ] `pipeline/stages/execute.py:1167` — idem
- [ ] `pipeline/stages/validate.py:184` — trocar `"quota_exceeded"` por `ErrorCode.QUOTA_EXCEEDED.value`
- [ ] `routes/search.py:571` — trocar `"sources_unavailable"` por `ErrorCode.SOURCE_UNAVAILABLE.value`
- [ ] `routes/search.py:599` — idem (via `state_machine.fail()` — verificar se aceita ErrorCode)
- [ ] `routes/search.py:607` — idem
- [ ] `routes/search.py:646` — `"unknown"` → trocar por `ErrorCode.INTERNAL_ERROR.value` ou criar novo valor na constraint

### AC2: Decidir sobre `"unknown"` (routes/search.py:646)
- **Opção A:** Mapear para `ErrorCode.INTERNAL_ERROR` (já existe na constraint) — perda de semântica minor
- **Opção B:** Adicionar `'UNKNOWN'` à constraint via nova migration — preserva semântica mas requer migration
- [ ] Decisão registrada em Dev Notes

### AC3: Verificar se há outros valores não-mapeados
- [ ] `grep -rn 'error_code.*=.*"[a-z]' backend/` — confirmar zero ocorrências após fix
- [ ] Verificar se `state_machine.fail()` em `routes/search.py:599` passa o `error_code` corretamente para `update_search_session_status`

### AC4: Usar o enum `ErrorCode` nos call sites (type-safety)
- [ ] Trocar strings literais por `ErrorCode.XXX.value` nos call sites corrigidos
- [ ] Isso garante que futuros códigos inválidos sejam detectados em tempo de compilação

### AC5: Testes
- [ ] Test unitário confirmando que os 7 call sites escrevem valores uppercase válidos
- [ ] Test de integração: simular timeout → confirmar que `search_sessions.error_code` = `'TIMEOUT'`
- [ ] Test de integração: simular quota exceeded → confirmar `'QUOTA_EXCEEDED'`

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

- [ ] Zero eventos `chk_search_sessions_error_code` no Sentry por 24h após deploy
- [ ] `grep -rn 'error_code.*=.*"[a-z]' backend/` retorna zero resultados
- [ ] Tests passando sem regressões

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — constraint violation confirmada: código escreve lowercase, constraint exige uppercase. 7 call sites identificados. |
| 2026-04-11 | @po (Sarah) | Validação `*validate-story-draft`. Score: 9/10. GO. Root cause clara, fix objetivo. Status: Draft → Ready. |
