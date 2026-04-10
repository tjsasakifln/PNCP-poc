# STORY-413: Fix ASGI Middleware TypeError `func() missing 'coroutine'` (Crash Loop)

**Priority:** P0 — Production Incident (Regressed)
**Effort:** M (1-2 days)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issues:**
- https://confenge.sentry.io/issues/7400217484/ (44 eventos, Escalating)
- https://confenge.sentry.io/issues/7282829485/ (44 eventos, Regressed — `Application startup failed`)
- https://confenge.sentry.io/issues/7282829484/ (44 eventos, Regressed — Traceback sibling)
**Sprint:** Emergencial (0-48h)

---

## Contexto

`TypeError: func() missing 1 required positional argument: 'coroutine'` está sendo lançado **unhandled** em `fastapi.middleware.asyncexitstack.AsyncExitStackMiddleware` e causando `Application startup failed. Exiting.` no uvicorn. Total: 132 eventos em 3 issues correlatas, há 15h, todas **Regressed/Escalating**.

**Causa raiz suspeita (mapeada pelo Explore agent):**

- `backend/task_registry.py:82` tem o padrão:
  ```python
  if entry.is_coroutine:
      entry.task = asyncio.create_task(entry.start_fn())
  else:
      entry.task = await entry.start_fn()
  ```
- Se uma função registrada no `TaskRegistry` tiver assinatura incorreta ou for wrapping errado de Sentry/OTel (ex: decorator que recebe `coroutine` como parâmetro esperado), a chamada falha com exatamente esse erro.
- O chamador provável é `backend/startup/lifespan.py:165` → `backend/startup/lifespan.py:231` (TaskRegistry.start_all)
- `backend/startup/sentry.py:126-131` registra `FastApiIntegration` + `StarletteIntegration` — nota: `StarletteIntegration` já está documentado como **disabled por SIGSEGV**; verificar se outro integration entrou recentemente

**Impacto atual:** crash loop no startup quando uma task específica é registrada, deixando o serviço indisponível temporariamente. Como é Regressed, houve regressão recente — investigar commits das últimas 24-48h no backend.

---

## Acceptance Criteria

### AC1: Reproduzir localmente
- [ ] Configurar ambiente apontando para staging Supabase + Redis
- [ ] Rodar `uvicorn backend.main:app --reload` e capturar stacktrace completo do `TypeError`
- [ ] Documentar no Dev Notes qual task/middleware dispara o erro

### AC2: Identificar a task/middleware com assinatura errada
- [ ] Inspecionar todas as `start_fn` registradas no `TaskRegistry` (em `backend/task_registry.py` + chamadas `.register(...)`)
- [ ] Verificar `backend/startup/lifespan.py` para ordem de startup de tasks
- [ ] Verificar `backend/startup/sentry.py:126-131` para integrations Sentry ativos
- [ ] Rodar `git log -p --since="3 days ago" backend/task_registry.py backend/startup/ backend/main.py` e identificar qualquer mudança suspeita em decoradores/wrappers

### AC3: Corrigir root cause
- [ ] Se for wrapper Sentry incorreto: corrigir registration ou downgrade temporário do `sentry-sdk` até fix upstream
- [ ] Se for task com assinatura errada: ajustar a função para `async def foo() -> None` conforme contract
- [ ] Se for regressão de código: reverter o commit ofensor ou re-implementar sem quebrar
- [ ] Revisar contract do `TaskRegistry` e adicionar validação de assinatura no `.register()` (fail-fast no import time, não no startup)

### AC4: Regression test
- [ ] Novo arquivo `backend/tests/test_task_registry.py` com testes cobrindo:
  - [ ] Registro de coroutine válida → ok
  - [ ] Registro de função síncrona válida → ok
  - [ ] Registro de função com assinatura errada → raise na hora do `.register()`, não no startup
  - [ ] `start_all()` com mix de coroutines e sync → executa corretamente

### AC5: Observability
- [ ] Adicionar log estruturado em `TaskRegistry.start_all()` listando cada task antes de iniciar (facilita debug futuro)
- [ ] Capturar exception + nome da task offending antes de propagar para uvicorn
- [ ] Alert dedicado no Sentry para `Application startup failed` com severity Fatal

### AC6: Verificação pós-deploy
- [ ] Monitorar Sentry issues 7400217484, 7282829485, 7282829484 por 24h — zero novos eventos
- [ ] `railway logs --filter "Application startup failed"` = vazio
- [ ] Smoke test: `curl $PROD_URL/health` retorna 200 após cada deploy subsequente

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/task_registry.py` | Linha 82 — validar assinatura no register, melhorar error handling |
| `backend/startup/lifespan.py` | Linhas 165, 231 — log estruturado de tasks iniciando |
| `backend/startup/sentry.py` | Linhas 126-131 — revisar integrations, possível rollback |
| `backend/tests/test_task_registry.py` | **Novo** — regression tests |
| `backend/main.py` | Revisar ordem de middlewares se necessário |

---

## Implementation Notes

- **Prioridade de diagnóstico:** primeiro descobrir QUAL task está falhando. Adicionar logging antes de reproducer para facilitar.
- **Hipótese #1 — Sentry integration:** Se `sentry-sdk` atualizou recentemente, pode ter mudado assinatura de `_create_span_call` (visto no stacktrace). Downgrade para versão anterior até validar.
- **Hipótese #2 — Task decorator regressão:** Alguém pode ter adicionado `@some_decorator` em uma task sem manter `async` correctly.
- **Hipótese #3 — Middleware order:** `AsyncExitStackMiddleware` é o middleware principal do FastAPI — se outro middleware foi adicionado antes e quebra o stack, isso causa o erro no startup.
- **Rollback plan:** se correção demorar, reverter último deploy via `railway redeploy` para versão estável conhecida, enquanto investiga.

---

## Dev Notes (preencher durante implementação)

<!-- @dev: documentar aqui qual task dispara o erro e o commit ofensor -->

---

## Verification

1. **Local:** `uvicorn backend.main:app --reload` sobe sem TypeError
2. **Staging:** deploy + `curl /health` retorna 200 em 30s após start
3. **Produção:** 3 restarts consecutivos do serviço sem crash
4. **Sentry:** 24h sem novos eventos nos 3 issues listados

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
| 2026-04-10 | @po (Sarah) | `*validate-story-draft` → verdict GO (9/10). Status Draft → Ready. |
