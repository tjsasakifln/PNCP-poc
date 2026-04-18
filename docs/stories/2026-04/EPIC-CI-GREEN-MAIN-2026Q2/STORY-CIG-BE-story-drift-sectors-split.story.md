# STORY-CIG-BE-story-drift-sectors-split — Sector IDs legados vs novos splits (`software_desenvolvimento`, `insumos_hospitalares`) — 15 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Seis suítes que validam classificação setorial rodam em `backend-tests.yml` e falham em **15 testes** do triage row #21/30. Causa raiz classificada como **assertion-drift**: os IDs de setor legados (`software`, `saude`, `facilities`, `transporte`) foram divididos em novos IDs granulares (`software_desenvolvimento`, `insumos_hospitalares`, etc.) em `backend/sectors_data.yaml`, mas os testes ainda esperam os IDs antigos.

Esta story se relaciona com a sincronização frontend (STORY-CIG-FE-19 `sector-sync.story.md`) — ver `scripts/sync-setores-fallback.js` (CLAUDE.md dev recipes).

**Arquivos principais afetados:**
- `backend/tests/test_sector_red_flags.py`
- `backend/tests/test_precision_recall_datalake.py`
- `backend/tests/test_story267_synonym_terms.py`
- `backend/tests/test_co_occurrence.py`
- `backend/tests/test_story283_phantom_cleanup.py`
- `backend/tests/test_search_pipeline_filter_enrich.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Assertion-drift: testes comparam sector IDs contra set hardcoded. Fix: atualizar expected IDs OU derivar dinamicamente de `sectors_data.yaml` (preferível — padrão usado em FE-19).

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_sector_red_flags.py backend/tests/test_precision_recall_datalake.py backend/tests/test_story267_synonym_terms.py backend/tests/test_co_occurrence.py backend/tests/test_story283_phantom_cleanup.py backend/tests/test_search_pipeline_filter_enrich.py -v` retorna exit code 0 localmente (15/15 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 6 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (assertion-drift). Tabela mapeando IDs legados → novos splits.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido. Benchmark precision ≥85% / recall ≥70% (SLA documentado em CLAUDE.md).
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 6 suítes isoladas.
- [ ] Validar contagem atual em `backend/sectors_data.yaml` (via `grep -c "^- id:" backend/sectors_data.yaml`).
- [ ] Preferir derivar IDs de `sectors_data.yaml` dinamicamente em vez de hardcode (mesmo padrão de FE-19).
- [ ] Validar que benchmark SLA não regrediu (precision ≥85%, recall ≥70% — CLAUDE.md).
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #21/30)

## Stories relacionadas no epic

- STORY-CIG-FE-19 `sector-sync` (frontend counterpart — já Done)
- STORY-CIG-BE-precision-recall-regex-hotspot (#17 — benchmark relacionado)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #21/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (8/10)** — Draft → Ready. SLA benchmark 85%/70% explícito em AC4; preferir derivar sector IDs de `sectors_data.yaml` dinamicamente (padrão FE-19) vs hardcode — evita dupla-manutenção.
