# STORY-CIG-BE-test-overlap-regex-timeout — Regex Compile Timeout em test_no_excessive_overlap

**Priority:** P2 — diagnóstico/doc; não bloqueia produção
**Effort:** S (2-4h investigação + fix potencial)
**Squad:** @dev + @qa
**Status:** Draft
**Epic:** [EPIC-CI-GREEN-MAIN-2026Q2](EPIC.md)

---

## Contexto

Durante a sessão de consultor `flickering-llama` (2026-04-20), observamos que o CI `test` workflow (Tests Full Matrix + Integration + E2E) falha consistentemente em main com:

```
tests/test_integration_new_sectors.py::test_no_excessive_overlap
+++++++++++ Timeout +++++++++++ (30s limit via pyproject.toml)
```

Stack:
```python
File "backend/filter/keywords.py", line 1032, in match_keywords
    matched_exc = bool(re.search(pattern, objeto_norm))
File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/re/_compiler.py", line 750
```

Este failure é **preexistente em main** e **não-bloqueante** no gate required `Backend Tests (PR Gate)` (esse passa consistentemente verde). Aparece apenas no `test` full matrix que não é required.

## Hipóteses

1. **Regex compile catastrófico** — algum padrão em `sectors_data.yaml` tem backtracking exponencial. Candidatos: exclusions com alternation sem anchors ou lookarounds redundantes.
2. **Test enumera muitos pares** — `test_no_excessive_overlap` compara 15 setores × 2 (keywords + exclusions) → O(225) compile × matches. Se um pattern é O(n²) em compile, estoura 30s.
3. **Re pattern cache miss** — Python `re` cache é LRU ~512 patterns; teste compila mais que isso, invalidando cache.

## Escopo do trabalho

### Fase 1 — Reprodução e profile (2h)

- [ ] Rodar `pytest tests/test_integration_new_sectors.py::test_no_excessive_overlap -v --timeout=0 -s` localmente
- [ ] Se reproduz: profile com `cProfile` e `pstats` — identificar padrão mais caro
- [ ] Se não reproduz local mas sim no CI: adicionar `print(sector.id, keyword_count, time_spent)` e rodar em CI debug

### Fase 2 — Fix (2h)

Dependente do hotspot identificado. Caminhos prováveis:
- **Pre-compile patterns no load de `sectors_data.yaml`** — cachear em memória módulo-level, match_keywords apenas executa patterns compilados
- **Simplificar exclusions catastróficas** — substituir alternations ambíguas por regex específicos ou listas de substring
- **Quebrar test em N testes menores** — evita timeout cumulativo ao invés de solution

### Fase 3 — Regression guard

- [ ] Adicionar bench `test_regex_compile_time_budget` que mede compile total < 5s (catch regressão)

## Acceptance Criteria

- [ ] Root cause documentado em `docs/postmortems/test-overlap-regex-timeout.md` (ou ADR)
- [ ] `test_no_excessive_overlap` passa em CI full matrix por 5 runs consecutivos
- [ ] Se tuning de `sectors_data.yaml` necessário: doc atualizado com convenção "evitar alternation sem anchors"

## Non-goals

- Alterar filtering behavior em produção (só tuning de padrões).
- Migrar para `re2` (overhead maior que fix localizado).

## Dependências

Nenhuma. Standalone investigation story.

## Rollback

Se fix introduzir regressão de classificação: reverter `sectors_data.yaml` + tests. Mantém o gap mas preserva prod.

---

## Change Log

- **2026-04-20** — @sm: Draft criado (consultor session `flickering-llama`) para documentar `test_no_excessive_overlap` timeout preexistente observado durante CI runs de PR #431, #432, #433. Candidato follow-up pós primeiro pagante (P2).
