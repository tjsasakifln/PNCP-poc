# STORY-CIG-BE-precision-recall-regex-hotspot — `filter.keywords.match_keywords` hang em benchmark cross-sector (>30s) — 1 teste flakiness/perf

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P2 — Gate (perf hotspot, exige investigação)
**Effort:** M (3-8h, pode escalar L se refactor de regex necessário)
**Agents:** @dev, @qa, @devops, @architect (review de performance)

---

## Contexto

Suíte `backend/tests/test_precision_recall_benchmark.py` roda em `backend-tests.yml` e falha em **1 teste** do triage row #17/30 — porém por **timeout >30s**, não por assertion. Causa raiz classificada como **flakiness** com suspeita de **prod-bug de performance**: `filter.keywords.match_keywords` hang em benchmark cross-sector (todos os 20 setores). Suspeita inicial do triage: regex com backtracking catastrófico (O(n²) ou pior).

Perf hotspot em filtro de produção tem impacto direto em SLA de busca (pipeline budget 100s — CLAUDE.md STORY-4.4).

**Arquivos principais afetados:**
- `backend/tests/test_precision_recall_benchmark.py` (1 teste)
- (potencialmente) `backend/filter/keywords.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Regex com `*` ou `+` dentro de grupo alternado causando backtracking exponencial em inputs longos. Alternativas: (a) simplificar regex, (b) pré-compilar patterns, (c) usar `regex` package em vez de `re` (com backtracking controlado), (d) dividir em múltiplas passadas lineares.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_precision_recall_benchmark.py -v --timeout=60` retorna exit code 0 localmente (1/1 PASS em <30s).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (flakiness/perf). Se fix alterou produção: incluir benchmark antes/depois (ex: 10× speedup mínimo esperado).
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido. Precision ≥85%, recall ≥70% (SLA CLAUDE.md) mantidos.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_precision_recall_benchmark.py -v --timeout=60 --tb=long`.
- [ ] Capturar profile: `python -m cProfile -o prof.out -m pytest backend/tests/test_precision_recall_benchmark.py` + `snakeviz prof.out` ou `pstats`.
- [ ] Identificar o regex problemático em `backend/filter/keywords.py` (ou wherever `match_keywords` vive).
- [ ] Pair com @architect para decidir entre (a-d) acima.
- [ ] Validar que precision/recall SLA continuam após otimização.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #17/30)

## Stories relacionadas no epic

- STORY-CIG-BE-story-drift-sectors-split (#21 — benchmark cross-sector)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #17/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. **Nota para @po:** @architect é obrigatório no review por ser perf hotspot de produção.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. **@architect review obrigatório** antes de @dev iniciar Implement — perf hotspot em `filter.keywords.match_keywords` + SLA 85%/70% precision/recall não podem regredir. Incluir benchmark antes/depois em AC3.
