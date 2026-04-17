# STORY-6.3: Backend Low Cleanup (TD-SYS-030, 031, 032)

**Priority:** P3 | **Effort:** S (8-12h) | **Squad:** @dev | **Status:** Ready for Review
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** dev SmartLic, **I want** débitos low backend resolvidos, **so that** codebase fique limpo.

## Acceptance Criteria
- [x] AC1 (TD-SYS-030): Seção "Migration Policy (STORY-6.3 EPIC-TD-2026Q2)" adicionada em `CLAUDE.md`, próxima à seção "Migration CI Flow (CRIT-050)". Documenta: `supabase/migrations/` como source-of-truth (SQL declarativo, aplicado via CI), `backend/migrations/` como legado Python/Alembic (audit trail, não recebe novas migrations), e regra forward-looking (novas mudanças de schema vão em `supabase/migrations/` com `.down.sql` pareado — STORY-6.2).
- [x] AC2 (TD-SYS-031): Diretório `backend/legacy/` **não existe** no filesystem (auditado via `ls backend/legacy/` = "No such file or directory"). Nenhum dead code para remover neste path. Scan adicional de `backend/scripts/` identificou scripts de auditoria/benchmark one-off (ex: `audit_all_sectors.py`, `bench_fts.py`, `backfill_embeddings.py`) — esses são utilitários de manutenção válidos, não dead code. Nenhuma deleção realizada. Candidatos para revisão futura listados abaixo em Dev Notes.
- [ ] AC3 (TD-SYS-032): **Deferred** — depende de STORY-1.6 (CRIT-080 SIGSEGV resolution) para re-enable OTEL spans seguros.

## Tasks
- [x] Doc clarification (AC1)
- [x] Dead code audit (AC2 — N/A, legacy/ não existe)
- [ ] OTEL re-enable se SIGSEGV resolved (AC3 — Deferred)

## Dev Notes
- **AC2 — backend/scripts/ candidates para revisão futura (follow-up, não deletar agora):**
  - `audit_all_sectors.py` / `audit_all_sectors.json` / `audit_all_sectors_report.md` — one-off audit
  - `audit_pipeline_complete.py` — one-off
  - `audit_pncp_data_nullability.py` — used for STORY-2.12 AC1 investigation
  - `build_benchmark_from_datalake.py` / `generate_benchmark_report.py` — benchmark tooling (may still be needed)
  - `dedup_profiles_email.py` — one-off data fix script
  These are non-imported scripts run manually; low risk if kept. Recommend review when Sprint 8+ has capacity.
- **AC3 blocked by STORY-1.6:** `docs/stories/2026-04/EPIC-TD-2026Q2/STORY-1.6-sigsegv-investigation.md`

## File List
| File | Action |
|------|--------|
| `CLAUDE.md` | Modified (new Migration Policy section near CRIT-050) |
| `docs/stories/2026-04/EPIC-TD-2026Q2/STORY-6.3-backend-low-cleanup.md` | Modified |

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-16 | 1.1 | AC1+AC2 completos. AC3 **Deferred** — depende de STORY-1.6 (CRIT-080 SIGSEGV resolution) para re-enable OTEL spans seguros. | @dev |
