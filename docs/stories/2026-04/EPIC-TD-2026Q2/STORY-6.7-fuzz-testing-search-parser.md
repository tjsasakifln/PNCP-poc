# STORY-6.7: Fuzz Testing Search Filter Parser (G-013)

**Priority:** P3 | **Effort:** S (4-8h) | **Squad:** @qa + @dev | **Status:** Ready for Review
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** SmartLic, **I want** fuzz tests em `term_parser.py`, **so that** edge cases (input malformado) sejam pegos.

## Acceptance Criteria
- [x] AC1: `hypothesis>=6.92.0` adicionado em `backend/requirements-dev.txt`; marker `fuzz` registrado em `pyproject.toml`
- [x] AC2: `backend/tests/fuzz/__init__.py` + `backend/tests/fuzz/test_term_parser_fuzz.py` criados com 6 property-based tests cobrindo: arbitrary text, whitespace-only, comma-heavy inputs, smart quotes, unicode/extreme chars, long inputs (MAX_INPUT_LENGTH truncation branch)
- [x] AC3: 100+ random inputs por função (`@settings(max_examples=100)`) — 6 testes passam, 0 crashes encontrados
- [x] AC4: `.github/workflows/backend-tests.yml` atualizado com `--ignore=tests/fuzz` no run principal + step separado `Run fuzz tests (Hypothesis)` após os testes principais

## Tasks
- [x] Hypothesis setup (requirements-dev.txt + pyproject.toml marker)
- [x] Property tests (6 funções distintas)
- [x] CI integration (separate step in backend-tests.yml)

## Dev Notes

### Função pública do parser
`term_parser.py` expõe **uma** função pública: `parse_search_terms(raw_input: str) -> List[str]`.
Suporta comma-mode vs space-mode (sem AND/OR/parênteses como inicialmente descrito na story).
`MAX_INPUT_LENGTH = 256` — trunca entradas longas.

### Fuzz Bugs Encontrados: 0
Parser se comporta corretamente em todos os casos testados.

### Finding documentado (não-bug)
`\x7f` (DEL, categoria Unicode Cc) é retornado na lista de resultados porque NÃO é whitespace (`\s` do Python). Comportamento correto do parser — documentado no docstring do teste `test_empty_or_whitespace_returns_empty_list`.

### Import convention
```python
from term_parser import parse_search_terms, MAX_INPUT_LENGTH
```
(sem prefixo `backend.` — pytest roda dentro de `backend/`)

## File List
| File | Action |
|------|--------|
| `backend/requirements-dev.txt` | Modified — added `hypothesis>=6.92.0` |
| `backend/pyproject.toml` | Modified — added `fuzz` marker |
| `backend/tests/fuzz/__init__.py` | Created — empty package init |
| `backend/tests/fuzz/test_term_parser_fuzz.py` | Created — 6 property-based fuzz tests |
| `.github/workflows/backend-tests.yml` | Modified — --ignore=tests/fuzz + separate fuzz step |

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-16 | 1.1 | Implementation complete: 6 fuzz tests, all pass, 0 bugs found | @qa + @dev |
