# STORY-2.1: Pydantic → TypeScript Type Generation (TD-QA-064)

**Priority:** P1 (precede STORY-3.2 — pode reduzir 30-50% esforço de remover `any`)
**Effort:** S (4-8h)
**Squad:** @dev (executor) + @architect (quality gate)
**Status:** Draft
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

- [ ] `pydantic-to-typescript` ou `openapi-typescript-codegen` adicionado ao backend
- [ ] Script `scripts/generate-types.sh` regenera `frontend/lib/types/api-generated.ts`
- [ ] Run automático em CI (GitHub Actions) — fail se diff sem commit

### AC2: Cobertura mínima

- [ ] Schemas: `SearchRequest`, `SearchResponse`, `LicitacaoItem`, `ViabilityAssessment`, `ClassificationResult`, `PipelineItem`, `Plan`, `Subscription`, `User/Profile`
- [ ] Outros podem ser adicionados incrementalmente

### AC3: Frontend usa types gerados

- [ ] At least 5 frontend files migrated para usar types gerados (ex: `app/api/buscar/route.ts`, `hooks/useSearchOrchestration.ts`)
- [ ] Types gerados marked `// AUTO-GENERATED — DO NOT EDIT`

### AC4: Documentation

- [ ] CLAUDE.md atualizado com workflow: "after `schemas.py` change, run `scripts/generate-types.sh`"
- [ ] CI workflow documented

---

## Tasks / Subtasks

- [ ] Task 1: Tool selection + setup (AC1)
- [ ] Task 2: Generate baseline types (AC2)
- [ ] Task 3: Migrate 5 frontend files (AC3)
- [ ] Task 4: CI integration (AC1)
- [ ] Task 5: Docs (AC4)

## Dev Notes

- `backend/schemas.py` é monolítico (1500+ LOC, ver TD-SYS-024)
- Tools options: `pydantic-to-typescript` (CLI), `datamodel-code-generator`, `openapi-typescript` (via FastAPI OpenAPI export)
- FastAPI já expõe `/openapi.json` — pode ser source

## Testing

- **Unit**: smoke test que types gerados compilam
- **CI**: GitHub Action fail se diff non-committed

## Definition of Done

- [ ] Tool setup
- [ ] Types gerados covered + 5 frontend files migrated
- [ ] CI gate active
- [ ] Docs

## Risks

- **R1**: Tool incompat com Pydantic v2 → mitigation: test before commit
- **R2**: Generated types muito verbose → mitigation: use openapi codegen com config trimming

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
