# STORY-CI-2 — SyntaxError f-string backslash em backend/llm.py (Python 3.11)

**Epic:** EPIC-CI-RECOVERY-2026Q2  
**Sprint:** 2026-Q2-S3  
**Status:** Ready  
**Priority:** P0 — Blocker  
**Effort:** XS (<30min)  
**Agents:** @dev  

---

## Contexto

`backend/llm.py` contém dois blocos (linhas ~160-169) com f-strings que incluem escape unicode (`\u00e7` = ç, `\u00f5` = õ) **dentro** da expressão ternária do f-string:

```python
# Bloco 1 (linha 161-164):
resumo.alerta_urgencia = (
    f"\u26a0\ufe0f {_n} "
    f"{'licita\u00e7\u00e3o encerra' if _n == 1 else 'licita\u00e7\u00f5es encerram'} nas próximas 24 horas."
)

# Bloco 2 (linha 167-169):
resumo.alerta_urgencia = (
    f"\u26a0\ufe0f {_n} "
    f"{'licita\u00e7\u00e3o encerra' if _n == 1 else 'licita\u00e7\u00f5es encerram'} em até 7 dias."
)
```

**Python 3.11** proíbe backslash dentro de `{...}` em f-strings (`SyntaxError: f-string expression part cannot include a backslash`). O PEP 701 só relaxou essa restrição no Python 3.12.

O CI matrix roda com Python 3.11 → falha na importação do módulo → job inteiro cai.

---

## Acceptance Criteria

- [x] AC1: `python -c "import ast; ast.parse(open('backend/llm.py', encoding='utf-8').read())"` → `AST OK` ✓
- [x] AC2: Comportamento em runtime preservado (strings UTF-8 literais — mesma saída para `_n=1` e `_n>1`)
- [ ] AC3: `pytest -k test_llm` passa sem regressão (a verificar no CI)
- [ ] AC4: Zero novas falhas de teste além da baseline de 292 pre-existing (a verificar no CI)

---

## Implementação

**Arquivo:** `backend/llm.py` — dois blocos (localizar por `alerta_urgencia`)

**Fix:** Extrair ternário para variável local com strings literais UTF-8 (não escape):

```python
# BLOCO 1 — "nas próximas 24 horas"
# ANTES:
resumo.alerta_urgencia = (
    f"\u26a0\ufe0f {_n} "
    f"{'licita\u00e7\u00e3o encerra' if _n == 1 else 'licita\u00e7\u00f5es encerram'} nas próximas 24 horas."
)

# DEPOIS:
_verbo_urgencia = "licitação encerra" if _n == 1 else "licitações encerram"
resumo.alerta_urgencia = f"⚠️ {_n} {_verbo_urgencia} nas próximas 24 horas."

# BLOCO 2 — "em até 7 dias"
# ANTES:
resumo.alerta_urgencia = (
    f"\u26a0\ufe0f {_n} "
    f"{'licita\u00e7\u00e3o encerra' if _n == 1 else 'licita\u00e7\u00f5es encerram'} em até 7 dias."
)

# DEPOIS:
_verbo_7d = "licitação encerra" if _n == 1 else "licitações encerram"
resumo.alerta_urgencia = f"⚠️ {_n} {_verbo_7d} em até 7 dias."
```

O emoji `⚠️` é UTF-8 literal — compatível com Python 3.11 dentro e fora de f-strings.

---

## Verificação Local

```bash
# Syntax check rápido (não precisa de Python 3.11 instalado)
cd backend
python -c "import ast; ast.parse(open('llm.py').read()); print('OK')"

# Testes de regressão
pytest tests/test_llm.py -v --timeout=30
pytest tests/ -k "llm" --timeout=30
```

---

## File List

- `backend/llm.py` — dois blocos `alerta_urgencia` (linhas ~160-169)
