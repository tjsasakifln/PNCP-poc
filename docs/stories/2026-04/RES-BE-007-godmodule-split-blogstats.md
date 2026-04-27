# RES-BE-007: God-Module Split — `routes/blog_stats.py` (1179L)

**Priority:** P1
**Effort:** M (3-4 dias)
**Squad:** @architect + @dev (architect lidera)
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 4 (2026-05-27 → 2026-06-02) — paralelizável com RES-BE-005
**Dependências bloqueadoras:** [RES-BE-001](RES-BE-001-audit-execute-without-budget.md), [RES-BE-009](RES-BE-009-test-suite-triage.md)

---

## Contexto

`backend/routes/blog_stats.py` tem **1179 linhas** servindo endpoints SEO críticos (observatório, programmatic pages) e mistura **5 responsabilidades**:

1. **Aggregations** — queries complexas de stats (top fornecedores, top órgãos, time series)
2. **Public endpoints** — rotas indexáveis (Googlebot crawl)
3. **Internal endpoints** — admin/debug
4. **Exports** — Excel, CSV, JSON downloadable
5. **Cache management** — TTL custom por endpoint, warmup helpers

Esses endpoints são **alvo direto da próxima wave Googlebot** (são a fundação do SEO programmatic). Bug em um endpoint pode quebrar todos os 5; QA difícil; refator de aggregation força regression test em exports e cache.

Solução: split por feature area em pacote `routes/blog_stats/` com façade APIRouter compartilhado. Effort M (menor que RES-BE-005 porque LOC menor e nenhum fan-in massivo: routes têm consumidores únicos = main.py via `include_router`).

---

## Acceptance Criteria

### AC1: Estrutura alvo

- [ ] Criar pacote `backend/routes/blog_stats/`:
  ```
  backend/routes/blog_stats/
  ├── __init__.py        # APIRouter + include_routers de cada sub-módulo
  ├── aggregations.py    # queries SQL complexas, helpers (~300L)
  ├── public.py          # GET /blog-stats/* indexáveis Googlebot (~250L)
  ├── internal.py        # GET /blog-stats/admin/* (auth required) (~200L)
  ├── exports.py         # GET /blog-stats/export/* downloads (~250L)
  └── cache.py           # TTL config, warmup helpers (~150L)
  ```

### AC2: APIRouter compartilhado

- [ ] `__init__.py` consolida router:
  ```python
  from fastapi import APIRouter
  from .public import router as public_router
  from .internal import router as internal_router
  from .exports import router as exports_router

  router = APIRouter(prefix="/blog-stats", tags=["blog-stats"])
  router.include_router(public_router)
  router.include_router(internal_router, prefix="/admin")
  router.include_router(exports_router, prefix="/export")
  ```
- [ ] `aggregations.py` e `cache.py` são **utility modules** — exportam funções, não routers
- [ ] `backend/main.py` ou `backend/startup/routes.py` continua importando `from routes.blog_stats import router` — **zero mudança em main**

### AC3: Migração de endpoints

- [ ] Mapear cada `@router.get` original para sub-módulo:
  - `GET /blog-stats/top-fornecedores` → `public.py`
  - `GET /blog-stats/top-orgaos` → `public.py`
  - `GET /blog-stats/time-series` → `public.py`
  - `GET /blog-stats/admin/refresh-cache` → `internal.py`
  - `GET /blog-stats/admin/audit` → `internal.py`
  - `GET /blog-stats/export/excel` → `exports.py`
  - `GET /blog-stats/export/csv` → `exports.py`
  - (Lista exata via `grep "@router.\(get\|post\)" backend/routes/blog_stats.py`)
- [ ] Path/method/response_model preservados (zero-impact externo, contrato OpenAPI estável)
- [ ] Aplicar `@with_negative_cache(ttl=300)` (RES-BE-003) em endpoints `public.*` se ainda não foi aplicado

### AC4: Smoke tests por endpoint

- [ ] Criar `backend/tests/routes/blog_stats/test_public.py`:
  - 1 test por endpoint público: GET retorna 200, response model válido, response time <500ms (com mock)
- [ ] `backend/tests/routes/blog_stats/test_internal.py`:
  - Auth required: sem token → 401; com admin token → 200
- [ ] `backend/tests/routes/blog_stats/test_exports.py`:
  - Excel/CSV gerado com payload realista; content-type correto
- [ ] Cobertura ≥85% nas linhas tocadas

### AC5: Validação de schema OpenAPI

- [ ] Após split, regenerar `frontend/app/api-types.generated.ts` (CLAUDE.md procedure):
  ```bash
  cd backend && uvicorn main:app --port 8000  # term 1
  npm --prefix frontend run generate:api-types  # term 2
  ```
- [ ] **Diff:** `git diff frontend/app/api-types.generated.ts` deve ser **zero** (sem mudança de schema)
- [ ] CI gate `api-types-check.yml` deve passar

### AC6: Validação SEO — não regredir crawl

- [ ] Smoke test pós-deploy staging:
  - `curl https://staging.smartlic.tech/api/blog-stats/top-fornecedores?uf=SP` → 200, JSON válido
  - `curl https://staging.smartlic.tech/api/blog-stats/top-orgaos` → 200
  - Mesmo payload que produção (diff < 1%)
- [ ] Documentar no PR: lista de endpoints SEO críticos validados

### AC7: Documentação

- [ ] `backend/routes/blog_stats/README.md`:
  - Mapa de endpoints (path → handler → submodule)
  - Como adicionar novo endpoint
  - TTL de cache por endpoint
  - Lista de endpoints SEO indexáveis (alvo Googlebot)
- [ ] `.claude/rules/architecture-detail.md` atualizado: substituir referência única por listagem do pacote

### AC8: Testes (gate final)

- [ ] Suite total backend passa sem regressão
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] CI tempo total <8min mantido
- [ ] OpenAPI schema diff = zero
- [ ] Smoke test staging confirma sem regressão SEO

---

## Scope

**IN:**
- Split `routes/blog_stats.py` em pacote 5 sub-módulos
- APIRouter compartilhado preservando paths
- Smoke tests por endpoint
- Validação OpenAPI schema diff = zero
- Documentação README + architecture-detail
- (Aplicar `@with_negative_cache` se ainda não aplicado nos endpoints público — coordenar com RES-BE-003)

**OUT:**
- Otimizar queries (escopo separado — `db-analyze-hotpaths`)
- Adicionar novos endpoints
- Renaming de paths — proibido (quebra Googlebot crawl)
- Mudar response_model — proibido (quebra frontend)
- Migrar para GraphQL — fora de escopo

---

## Definition of Done

- [ ] 5 sub-módulos criados (aggregations, public, internal, exports, cache)
- [ ] Façade `__init__.py` com APIRouter consolidado
- [ ] Cobertura testes ≥85%
- [ ] OpenAPI schema diff = zero (api-types-check.yml verde)
- [ ] Suite backend passa sem regressão
- [ ] Smoke tests staging passam (curl em todos endpoints públicos)
- [ ] CodeRabbit clean (CRITICAL=0, HIGH=0)
- [ ] PR review por @architect (Aria) e @qa (Quinn) com verdict PASS
- [ ] `routes/blog_stats/README.md` criado
- [ ] CLAUDE.md atualizado se afetar invariante (provavelmente não — arquitetura interna)
- [ ] QA loop max 2 iterações

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/routes/blog_stats.py` (deletar — vira pacote)
- `/mnt/d/pncp-poc/backend/routes/blog_stats/__init__.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/blog_stats/aggregations.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/blog_stats/public.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/blog_stats/internal.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/blog_stats/exports.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/blog_stats/cache.py` (novo)
- `/mnt/d/pncp-poc/backend/routes/blog_stats/README.md` (novo)
- `/mnt/d/pncp-poc/backend/tests/routes/blog_stats/test_public.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/routes/blog_stats/test_internal.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/routes/blog_stats/test_exports.py` (novo)

### Padrão referência

- RES-BE-005 e RES-BE-006 — façade pattern
- `backend/cache/` package estrutura
- FastAPI `APIRouter` composition: https://fastapi.tiangolo.com/tutorial/bigger-applications/

### Process — ordem sugerida

1. Read `blog_stats.py` integral; mapear cada endpoint para sub-módulo
2. Branch: `refactor/RES-BE-007-blog-stats-split`
3. Commit 1: criar pacote vazio com `__init__.py` placeholder
4. Commit 2: mover endpoints `public.*`
5. Commit 3: mover endpoints `internal.*`
6. Commit 4: mover endpoints `exports.*`
7. Commit 5: extrair `aggregations.py`, `cache.py`
8. Commit 6: deletar `blog_stats.py` arquivo, finalizar `__init__.py` façade
9. Commit 7: regenerar OpenAPI types frontend
10. Run pytest, smoke staging, push

### Frameworks de teste

- pytest 8.x + httpx + pytest-asyncio
- File location: `backend/tests/routes/blog_stats/test_*.py`
- Marks: `@pytest.mark.timeout(30)`
- Auth: `app.dependency_overrides[require_auth]` para internal endpoints
- Fixtures: mockar `pncp_raw_bids` query results para isolar de DB

### Convenções

- APIRouter por sub-módulo: `router = APIRouter()` em cada arquivo, sem prefix interno (prefix vai no `__init__.py`)
- response_model obrigatório em todos endpoints (CLAUDE.md "Pydantic → TypeScript Type Sync")
- Imports absolutos
- Type hints obrigatórios

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| OpenAPI schema diff != zero | Identificar endpoint mudado; restaurar response_model ou path; regenerar |
| Endpoint SEO retorna 404 pós-deploy | Verificar `include_router(prefix=...)` está correto; checar `main.py` import |
| Googlebot crawl regrede em GSC | Smoke test imediato; rollback PR; investigar caching |
| QA loop excede 5 iterações | Escalar @aiox-master; possível split em 2 PRs (public+internal vs exports+aggregations) |
| Aggregations queries lentas pós-split (sem cache lazy) | Confirmar `cache.py` exporta helpers usados; revisar TTL |

**Rollback completo:** revert PR. Endpoints voltam para arquivo único.

---

## Dependencies

**Entrada:**
- [RES-BE-001](RES-BE-001-audit-execute-without-budget.md) — gate CI
- [RES-BE-009](RES-BE-009-test-suite-triage.md) — suite saudável
- (Soft) [RES-BE-003](RES-BE-003-negative-cache-failure-paths.md) — coordenar `@with_negative_cache` se ainda não aplicado

**Saída:** Habilita SEO-PROG-006 (sitemap particionado) — split torna queries facilmente reusáveis no novo pipeline de sitemap.

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | God-module split com LOC (1179L) + módulo alvo claro. |
| 2 | Complete description | ✓ | 5 responsabilidades misturadas + alvo Googlebot SEO contextualizado. |
| 3 | Testable acceptance criteria | ✓ | 8 ACs incluindo OpenAPI schema diff = zero (forte gate quantitativo) e smoke staging com curl. |
| 4 | Well-defined scope | ✓ | IN/OUT delimitados; renaming proibido (Googlebot crawl stability). |
| 5 | Dependencies mapped | ✓ | Entrada RES-BE-001+009; soft dep RES-BE-003 (negative cache); saída habilita SEO-PROG-006. |
| 6 | Complexity estimate | ✓ | M (3-4 dias) coerente — menor que RES-BE-005/006 (sem fan-in massivo). |
| 7 | Business value | ✓ | "Endpoints alvo direto da próxima wave Googlebot" — risco SEO traduzido. |
| 8 | Risks documented | ✓ | 5 riscos incluindo Googlebot crawl regression em GSC; rollback PR direto. |
| 9 | Criteria of Done | ✓ | 11 itens DoD incluindo OpenAPI diff zero + smoke staging por endpoint. |
| 10 | Alignment with PRD/Epic | ✓ | Habilita SEO-PROG-006 (sitemap particionado) — saída explícita. |

### Required Fixes

Nenhuma.

### Observations

- AC5 OpenAPI schema diff = zero é gate forte — protege contrato frontend.
- AC6 smoke staging com curl em endpoints reais é boa prática — captura regressões silenciosas pre-deploy.
- Coordenação soft com RES-BE-003 (`@with_negative_cache`) flagged — sem bloqueio sequencial estrito.
- Effort M apropriado — paralelizável com RES-BE-005 em Sprint 4.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — split god-module routes/blog_stats.py | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). OpenAPI diff zero + smoke staging gates fortes. Status: Draft → Ready. | @po (Pax) |
