# Story DEBT-109: QA Automation — axe-core, OpenAPI Snapshot & Conftest Cleanup

## Metadata
- **Story ID:** DEBT-109
- **Epic:** EPIC-DEBT
- **Batch:** C (Optimization)
- **Sprint:** 4-6 (Semanas 7-10)
- **Estimativa:** 16h
- **Prioridade:** P2
- **Agent:** @qa + @devops

## Descricao

Como engenheiro de qualidade, quero habilitar auditorias automaticas de acessibilidade (axe-core) nos E2E tests, enforcar snapshots do schema OpenAPI em CI, e limpar o conftest de integracao para usar async cleanup adequado, para que a qualidade seja verificada automaticamente a cada deploy e os testes de integracao sejam confiaveis.

## Debt Items Cobertos

| ID | Debito | Severidade | Horas |
|----|--------|:---:|:---:|
| QA-NEW-02 | `@axe-core/playwright` instalado mas ZERO specs usam — zero automated a11y assertions em E2E | HIGH | 8h |
| QA-NEW-03 | No enforced OpenAPI schema snapshot test — `openapi_schema.diff.json` com drift ativo | MEDIUM | 4h |
| QA-NEW-01 | Integration conftest.py lacks `_cleanup_pending_async_tasks` e `_isolate_arq_module` — usa warning suppression | MEDIUM | 4h |

## Acceptance Criteria

- [x] AC1: 5 E2E specs core incluem `@axe-core/playwright` audit (login, buscar, dashboard, pipeline, planos)
- [x] AC2: axe-core audits passam com 0 critical violations
- [x] AC3: axe-core violations serious/moderate documentadas como known issues (se houver)
- [x] AC4: OpenAPI schema snapshot salvo em repo (`tests/snapshots/openapi_schema.json`)
- [x] AC5: CI falha se OpenAPI schema diverge do snapshot (drift detection)
- [x] AC6: Script para atualizar snapshot: `pytest --update-snapshots` ou similar
- [x] AC7: Integration conftest.py usa `_cleanup_pending_async_tasks` fixture (autouse)
- [x] AC8: Integration conftest.py usa `_isolate_arq_module` fixture (autouse)
- [x] AC9: Warning suppression removida do conftest — warnings sao resolvidos, nao suprimidos
- [x] AC10: `python scripts/run_tests_safe.py` — 0 failures, 0 warnings de async tasks

## Testes Requeridos

- **QA-NEW-02 (axe-core):**
  - `npm run test:e2e` — 5 specs com audits passam
  - Verificar que axe-core nao causa flakiness (timeouts, etc)
  - Documentar violations known (se houver) com issue references

- **QA-NEW-03 (OpenAPI Snapshot):**
  - Alterar um endpoint — CI deve falhar com "schema drift detected"
  - Rodar `pytest --update-snapshots` — CI passa novamente
  - Snapshot file versionado em git

- **QA-NEW-01 (Conftest):**
  - `pytest tests/integration/ --timeout=30` — 0 hangs
  - Verificar que async tasks sao limpas apos cada test (no lingering tasks)
  - `pytest tests/integration/ -W error::RuntimeWarning` — 0 warnings

## Notas Tecnicas

- **QA-NEW-02 (axe-core E2E):**
  - `@axe-core/playwright` ja esta instalado (`package.json`)
  - Adicionar em cada spec:
    ```typescript
    import AxeBuilder from '@axe-core/playwright';
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations.filter(v => v.impact === 'critical')).toHaveLength(0);
    ```
  - 5 core specs: login, buscar, dashboard, pipeline, planos
  - Cuidado com timing — rodar axe apos page fully loaded

- **QA-NEW-03 (OpenAPI Snapshot):**
  - Endpoint: `GET /openapi.json` do FastAPI
  - Usar `pytest-snapshot` ou custom fixture
  - Ignorar campos dinamicos (server URL, timestamps)
  - CI step: `pytest -k test_openapi_schema`

- **QA-NEW-01 (Conftest):**
  - Copiar patterns de `backend/tests/conftest.py` (que ja tem os fixtures corretos)
  - Arquivo: `backend/tests/integration/conftest.py`
  - Fixture `_cleanup_pending_async_tasks`: cancela `asyncio.all_tasks()` apos cada test
  - Fixture `_isolate_arq_module`: limpa `sys.modules["arq"]` com proper cleanup

## Dependencias

- **Depende de:** Nenhuma (pode ser parallelizado com DEBT-106/107/108)
- **Bloqueia:** Nenhuma (mas QA-NEW-02 habilita deteccao continua de regressoes a11y)

## Definition of Done

- [x] 5 E2E specs com axe-core audit
- [x] 0 critical a11y violations
- [x] OpenAPI snapshot enforced em CI
- [x] Integration conftest com async cleanup adequado
- [x] Warning suppression removida
- [x] Testes passando
- [ ] Code review aprovado
- [x] CI pipeline atualizado
