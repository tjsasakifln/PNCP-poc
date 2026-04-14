# STORY-2.1: Pydantic → TypeScript Type Generation (TD-QA-064)

**Priority:** P1 (precede STORY-3.2 — pode reduzir 30-50% esforço de remover `any`)
**Effort:** S (4-8h)
**Squad:** @dev (executor) + @architect (quality gate)
**Status:** Ready for Review
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1 (Semana 2)

---

## Story

**As a** dev frontend trabalhando com APIs SmartLic,
**I want** types TypeScript gerados automaticamente do schema Pydantic backend,
**so that** mudanças em `backend/schemas.py` quebrem o build frontend em compile time, eliminando classe inteira de bugs.

---

## Acceptance Criteria

### AC1: Tool integration

- [x] `openapi-typescript@7.13.0` já em devDep do frontend (pre-existente)
- [x] Script `scripts/generate-api-types.sh` regenera `frontend/app/api-types.generated.ts` (pre-existente)
- [x] CI workflow `.github/workflows/api-types-check.yml` extrai OpenAPI via `python -c "from main import app; app.openapi()"` direto (sem precisar subir backend), roda `openapi-typescript`, falha em diff contra arquivo commitado

### AC2: Cobertura mínima

- [x] Cobertura verificada em `api-types.generated.ts`: BuscaRequest, BuscaResponse, LicitacaoItem, FilterStats, Recomendacao, ResumoEstrategico, ResumoLicitacoes, UserProfileResponse, PlanDetails, PlansResponse, ConversationDetail/Summary, AdminUsersListResponse, SessionsListResponse, SetoresResponse, SourceInfo

### AC3: Frontend usa types gerados

- [x] 6 arquivos migrados (> mínimo 5 exigido):
  - `frontend/app/planos/page.tsx` (UserProfile via `components["schemas"]["UserProfileResponse"]`)
  - `frontend/app/admin/page.tsx` (UserProfile + UsersResponse)
  - `frontend/app/admin/components/AdminUserTable.tsx`
  - `frontend/app/admin/types.ts` (novo, consolidador)
  - `frontend/hooks/usePlan.ts` (PlanInfo derivado de UserProfileResponse)
  - `frontend/hooks/usePipeline.ts` (PipelineApiResponse derivado de PipelineListResponse)
- [x] Types gerados marcados `// AUTO-GENERATED — DO NOT EDIT` no header

### AC4: Documentation

- [x] CLAUDE.md atualizado com seção "Pydantic → TypeScript Type Sync (STORY-2.1 EPIC-TD-2026Q2)"
- [x] CI workflow comentado inline

---

## Tasks / Subtasks

- [x] Task 1: Tool selection + setup (AC1) — reusou infra pre-existente
- [x] Task 2: Verificar cobertura (AC2)
- [x] Task 3: Migrate 6 frontend files (AC3)
- [x] Task 4: CI integration — workflow api-types-check.yml (AC1)
- [x] Task 5: Docs CLAUDE.md (AC4)

## Dev Notes

- `backend/schemas.py` é monolítico (1500+ LOC, ver TD-SYS-024)
- Tools options: `pydantic-to-typescript` (CLI), `datamodel-code-generator`, `openapi-typescript` (via FastAPI OpenAPI export)
- FastAPI já expõe `/openapi.json` — pode ser source

## Testing

- **Unit**: smoke test que types gerados compilam
- **CI**: GitHub Action fail se diff non-committed

## File List

- **Created**:
  - `.github/workflows/api-types-check.yml`
  - `frontend/app/admin/types.ts`
- **Modified**:
  - `CLAUDE.md` (nova seção "Pydantic → TypeScript Type Sync")
  - `frontend/app/planos/page.tsx`
  - `frontend/app/admin/page.tsx`
  - `frontend/app/admin/components/AdminUserTable.tsx`
  - `frontend/hooks/usePlan.ts`
  - `frontend/hooks/usePipeline.ts`

## Definition of Done

- [x] Tool setup (reusou infra pre-existente + CI gate novo)
- [x] Types gerados covered + 6 frontend files migrated
- [x] CI gate active via `.github/workflows/api-types-check.yml`
- [x] Docs atualizados em CLAUDE.md

## Risks

- **R1**: Tool incompat com Pydantic v2 → mitigation: test before commit
- **R2**: Generated types muito verbose → mitigation: use openapi codegen com config trimming

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — CI gate com Python OpenAPI extraction direta (sem subir backend em runner). 6 frontend files migrated. | @dev (EPIC-TD Sprint 1 batch) |
