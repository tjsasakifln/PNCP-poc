# DEBT-S0.1: Fix main.py/app_factory Dual-Path + CORS
**Epic:** EPIC-DEBT
**Sprint:** 0
**Priority:** P0
**Estimated Hours:** 4h
**Assignee:** TBD

## Objetivo

Investigar e resolver a ambiguidade entre `main.py` e `app_factory.py` como entry points da aplicacao. Producao roda `main:app` que tem CORS `allow_origins=["*"]` e middleware stack incompleta, enquanto `app_factory.py` tem CORS correto via `get_cors_origins()`. Resolver o dual-path elimina 4 debitos simultaneamente.

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| SYS-01 | CORS permite todas origens (`*`) + dual-path main.py/app_factory. Producao roda o stub `main:app`. | CRITICAL | 4h |
| SYS-06 | Route registration nao visivel em main.py. 38 modulos registrados via pattern nao visivel do entry point. | HIGH | 0h (bundled) |
| SYS-17 | Titulo do app "BidIQ Uniformes" em main.py. | LOW | 0h (bundled) |
| SYS-18 | Versao FastAPI 0.2.0 em main.py. Deveria ser v0.5. | LOW | 0h (bundled) |

## Acceptance Criteria

- [ ] AC1: Verificar via `railway logs --tail` qual entry point producao usa (`main:app` vs `app_factory:create_app`)
- [ ] AC2: Se `main:app`, migrar entry point para `app_factory:create_app` (ou inlinar app_factory em main.py)
- [ ] AC3: CORS em producao usa `get_cors_origins()` com allowlist explicita (nao `*`)
- [ ] AC4: Request com `Origin: https://evil.com` retorna SEM header `Access-Control-Allow-Origin`
- [ ] AC5: Request com `Origin: https://smartlic.tech` retorna header CORS correto
- [ ] AC6: Titulo da aplicacao e "SmartLic" (nao "BidIQ Uniformes")
- [ ] AC7: Versao da aplicacao e APP_VERSION do config.py (nao hardcoded 0.2.0)
- [ ] AC8: Todas as 38 rotas registradas e visiveis a partir do entry point

## Tasks

- [ ] T1: Verificar entry point atual em Railway via `railway logs` e Procfile/start.sh
- [ ] T2: Se `main:app`, atualizar Procfile/start.sh para usar `app_factory:create_app`
- [ ] T3: Remover ou marcar `main.py` como deprecated (redirect to app_factory)
- [ ] T4: Verificar que `get_cors_origins()` retorna allowlist correta para producao
- [ ] T5: Escrever teste `test_cors.py` com TestClient validando CORS behavior
- [ ] T6: Deploy para staging e verificar que todas rotas funcionam
- [ ] T7: Deploy para producao com rollback plan

## Testes Requeridos

- [ ] `test_cors.py`: Request com Origin malicioso nao recebe CORS headers
- [ ] `test_cors.py`: Request com Origin permitido recebe headers corretos
- [ ] `test_cors.py`: Preflight OPTIONS retorna metodos e headers permitidos
- [ ] Verificar que `/docs` mostra todas 49 rotas registradas
- [ ] E2E: Frontend funciona normalmente apos mudanca de entry point

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging
- [ ] Verificado em producao que CORS nao permite `*`

## Notas

- **RISCO ALTO:** Se frontend proxy depende de CORS `*` para algum caso edge, pode quebrar. Mitigacao: frontend proxy (`/api/*`) e same-origin e bypassa CORS.
- SYS-06, SYS-17, SYS-18 tem 0h porque sao resolvidos automaticamente ao usar app_factory como entry point.
- `app_factory.py` ja tem titulo correto, versao correta, e route registration completa.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secao "Sistema"
- Entry points: `backend/main.py`, `backend/app_factory.py`
- CORS config: `backend/config.py` (`get_cors_origins()`)
- Deploy config: `Procfile`, `backend/start.sh`
