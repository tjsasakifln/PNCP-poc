# RES-BE-008: God-Module Split — `routes/admin.py` (1132L)

**Priority:** P2
**Effort:** M (3-4 dias)
**Squad:** @architect + @dev (architect lidera)
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 6 (2026-06-17 → 2026-06-23) — backlog P2
**Dependências bloqueadoras:** [RES-BE-001](RES-BE-001-audit-execute-without-budget.md), [RES-BE-009](RES-BE-009-test-suite-triage.md)

---

## Contexto

`backend/routes/admin.py` tem **1132 linhas** servindo painel admin com 4 áreas funcionais misturadas:

1. **Users** — manage profiles, roles, ban/unban
2. **Billing** — Stripe sync ops, refunds, plan overrides
3. **Ops** — cache clear, search re-index, datalake refresh
4. **Debug** — view logs, metrics dump, feature flag toggle

RBAC (`require_admin`, `require_master`) é decorator local repetido; refator de auth tem que tocar arquivo gigante. Adicionar feature admin nova vira merge conflict garantido.

Esta story é P2 (não bloqueia incident response, é refator estrutural pós-Sprint 1) e effort M. Aplica padrões já validados em RES-BE-005, 006, 007.

---

## Acceptance Criteria

### AC1: Estrutura alvo

- [ ] Criar pacote `backend/routes/admin/`:
  ```
  backend/routes/admin/
  ├── __init__.py        # APIRouter consolidado + RBAC dependencies compartilhadas
  ├── users.py           # /admin/users/* (~250L)
  ├── billing.py         # /admin/billing/* (~300L)
  ├── ops.py             # /admin/ops/* (cache, datalake, search) (~300L)
  └── debug.py           # /admin/debug/* (logs, metrics, flags) (~250L)
  ```

### AC2: APIRouter + RBAC compartilhado

- [ ] `__init__.py`:
  ```python
  from fastapi import APIRouter, Depends
  from authorization import require_admin, require_master
  from .users import router as users_router
  from .billing import router as billing_router
  from .ops import router as ops_router
  from .debug import router as debug_router

  router = APIRouter(
      prefix="/v1/admin",
      tags=["admin"],
      dependencies=[Depends(require_admin)],  # RBAC global
  )
  router.include_router(users_router, prefix="/users")
  router.include_router(billing_router, prefix="/billing")
  router.include_router(ops_router, prefix="/ops")
  router.include_router(debug_router, prefix="/debug", dependencies=[Depends(require_master)])
  ```
- [ ] Endpoints `debug.*` exigem master (não só admin) — refletido em `dependencies=[Depends(require_master)]`
- [ ] Sub-módulos não repetem `Depends(require_admin)` em cada endpoint (vem do parent)

### AC3: Migração de endpoints

- [ ] Mapear cada `@router.*` original para sub-módulo:
  - `POST /admin/users/{id}/ban`, `PATCH /admin/users/{id}/role` → `users.py`
  - `POST /admin/billing/refund/{stripe_id}`, `GET /admin/billing/audit` → `billing.py`
  - `POST /admin/ops/cache/clear`, `POST /admin/ops/datalake/refresh`, `POST /admin/ops/search/reindex` → `ops.py`
  - `GET /admin/debug/logs`, `GET /admin/debug/metrics-dump`, `POST /admin/debug/flag/{name}` → `debug.py`
  - (Lista exata via grep)
- [ ] Path/method/response_model preservados; OpenAPI schema diff = zero

### AC4: Endpoint admin clear cache (RES-BE-003) acomodado

- [ ] Endpoint `POST /v1/admin/negative-cache/clear` (criado em RES-BE-003) move para `ops.py`
- [ ] Path final: `POST /v1/admin/ops/negative-cache/clear` (com prefix `/ops`)
- [ ] Atualizar runbook RES-BE-003 com path correto

### AC5: Smoke tests por área

- [ ] `backend/tests/routes/admin/test_users.py`:
  - Auth required (sem token → 401)
  - Admin token → 200
  - Operações: ban, unban, role change
- [ ] `backend/tests/routes/admin/test_billing.py`:
  - Refund flow (mock Stripe)
- [ ] `backend/tests/routes/admin/test_ops.py`:
  - Cache clear, datalake refresh
- [ ] `backend/tests/routes/admin/test_debug.py`:
  - Master required (admin não basta para debug)
  - Logs endpoint, metrics dump
- [ ] Cobertura ≥85%

### AC6: Validação OpenAPI

- [ ] Regenerar `frontend/app/api-types.generated.ts` e confirmar diff = zero
- [ ] CI gate `api-types-check.yml` passa
- [ ] Frontend `/admin` page (Next.js) continua funcionando

### AC7: Documentação

- [ ] `backend/routes/admin/README.md`:
  - Mapa de endpoints por área
  - Matriz RBAC (qual área exige admin vs master)
  - Como adicionar nova feature admin
- [ ] `.claude/rules/architecture-detail.md` atualizado: substituir referência única por listagem

### AC8: Testes (gate final)

- [ ] Suite total backend passa sem regressão
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] CI tempo total <8min mantido
- [ ] OpenAPI schema diff = zero
- [ ] Smoke staging: cada endpoint admin retorna 200 com auth correto

---

## Scope

**IN:**
- Split `routes/admin.py` em pacote 4 sub-módulos
- APIRouter compartilhado + RBAC consolidado
- Smoke tests por área
- Validação OpenAPI schema diff
- Documentação README + matriz RBAC

**OUT:**
- Adicionar novas features admin
- Refator de RBAC backend (escopo futuro: `services/authorization.py` consolidação)
- UI admin frontend mudança — pode estar em escopo paralelo
- Audit logging admin actions — escopo futuro
- Renaming de paths — proibido (quebra frontend admin)

---

## Definition of Done

- [ ] 4 sub-módulos criados (users, billing, ops, debug)
- [ ] Façade `__init__.py` com APIRouter + RBAC consolidado
- [ ] Cobertura testes ≥85%
- [ ] OpenAPI schema diff = zero
- [ ] Suite backend passa sem regressão
- [ ] Smoke tests staging passam
- [ ] Frontend `/admin` page continua funcionando
- [ ] CodeRabbit clean (CRITICAL=0, HIGH=0)
- [ ] PR review por @architect (Aria) e @qa (Quinn) com verdict PASS
- [ ] `routes/admin/README.md` criado com matriz RBAC
- [ ] CLAUDE.md atualizado se afetar invariante
- [ ] QA loop max 2 iterações
- [ ] Path do endpoint negative-cache/clear (RES-BE-003) atualizado em runbook

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/routes/admin.py` (deletar — vira pacote)
- `/mnt/d/pncp-poc/backend/routes/admin/__init__.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/admin/users.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/admin/billing.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/admin/ops.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/admin/debug.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/admin/README.md` (novo)
- `/mnt/d/pncp-poc/backend/tests/routes/admin/test_users.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/routes/admin/test_billing.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/routes/admin/test_ops.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/routes/admin/test_debug.py` (novo)

### Padrão referência

- RES-BE-007 (blog_stats split) — pattern já validado para routes
- `backend/authorization.py` — `require_admin`, `require_master` decorators existentes

### Process — ordem sugerida

1. Read `admin.py` integral; mapear endpoints + matriz RBAC
2. Branch: `refactor/RES-BE-008-admin-split`
3. Commit 1: criar pacote vazio
4. Commit 2..5: mover endpoints por área
5. Commit 6: deletar `admin.py`, finalizar `__init__.py`
6. Commit 7: regenerar OpenAPI types
7. Smoke staging + push

### Frameworks de teste

- pytest 8.x + httpx + pytest-asyncio
- File location: `backend/tests/routes/admin/test_*.py`
- Marks: `@pytest.mark.timeout(30)`
- Auth: `app.dependency_overrides[require_admin]`, `app.dependency_overrides[require_master]`
- Fixtures: mock Stripe client, mock Supabase

### Convenções

- APIRouter por sub-módulo sem prefix interno
- RBAC vem do `__init__.py` (parent dependency)
- response_model obrigatório
- Type hints obrigatórios

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| OpenAPI schema diff != zero | Identificar endpoint mudado; restaurar |
| Frontend `/admin` quebra | Verificar prefix do APIRouter; testar com browser DevTools |
| RBAC bypass acidental (endpoint sem auth) | Confirmar `dependencies=[Depends(require_admin)]` no parent; smoke test sem token deve retornar 401 em TODOS endpoints |
| Endpoint debug acessível por admin (deveria ser master) | Confirmar `dependencies=[Depends(require_master)]` no `include_router` de debug |
| QA loop excede 5 iterações | Escalar @aiox-master |

**Rollback completo:** revert PR. Endpoints voltam para arquivo único.

---

## Dependencies

**Entrada:**
- [RES-BE-001](RES-BE-001-audit-execute-without-budget.md) — gate CI
- [RES-BE-009](RES-BE-009-test-suite-triage.md) — suite saudável
- (Soft) [RES-BE-003](RES-BE-003-negative-cache-failure-paths.md) — endpoint clear cache vai para `ops.py`

**Saída:** Habilita futura story de audit logging admin actions (compliance LGPD pré-requisito).

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 9/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | God-module split admin (1132L) — escopo claro. |
| 2 | Complete description | ✓ | 4 áreas funcionais misturadas + RBAC fricção contextualizada. |
| 3 | Testable acceptance criteria | ✓ | 8 ACs incluindo OpenAPI diff zero, RBAC matrix testada por área. |
| 4 | Well-defined scope | ✓ | IN/OUT explicitos; renaming proibido (frontend admin). |
| 5 | Dependencies mapped | ✓ | Entrada RES-BE-001+009; soft RES-BE-003 (endpoint negative-cache/clear migra para ops.py). |
| 6 | Complexity estimate | ✓ | M (3-4 dias) — pattern já validado em RES-BE-007. |
| 7 | Business value | ✗ | P2 backlog: "Adicionar feature admin nova vira merge conflict garantido" — valor existe mas é estrutural, não urgente. Aceitável para Sprint 6. |
| 8 | Risks documented | ✓ | 5 riscos incluindo RBAC bypass acidental — bem flagged (smoke test sem token deve retornar 401). |
| 9 | Criteria of Done | ✓ | 13 itens DoD incluindo path do endpoint negative-cache/clear atualizado. |
| 10 | Alignment with PRD/Epic | ✓ | EPIC tabela: P2 Sprint 6, conforme planejado. |

### Required Fixes

Nenhuma.

### Observations

- RBAC consolidado via parent dependency é boa prática (DRY, menos chance de bypass).
- AC4 endpoint admin clear cache (de RES-BE-003) explicitamente acomodado — coordenação clara.
- P2 = aceito; pode ser deslocado se incident response priority subir.
- Critério #7 minorado mas nao impeditivo: valor estrutural, story bem escopada, sem urgência operacional.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — split god-module routes/admin.py | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (9/10). P2 backlog Sprint 6, RBAC consolidado via parent dep. Status: Draft → Ready. | @po (Pax) |
