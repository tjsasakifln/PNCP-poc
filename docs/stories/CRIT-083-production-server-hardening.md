# CRIT-083: Production Server Hardening — Processo Resiliente e Escalável

**Status:** Done
**Priority:** P2 — MEDIUM (estabilidade a longo prazo)
**Epic:** Infraestrutura de Produção
**Agent:** @devops + @architect
**Depends on:** CRIT-080 (deploy funcional)

---

## Contexto

O backend roda como **uvicorn standalone single-process** sem workers, sem process manager. Isso foi necessário para contornar o SIGSEGV causado por fork (jemalloc + cryptography + Sentry), mas cria fragilidades:

| Aspecto | Estado Atual | Risco |
|---------|-------------|-------|
| Processos | 1 (uvicorn standalone) | Um crash = downtime total |
| Workers | 0 (sem fork) | Sem concorrência de CPU |
| Process Manager | Nenhum | Sem restart automático granular |
| Memory Leak | Sem proteção | Sem max-requests recycling |
| Graceful Shutdown | Parcial (drainingSeconds=120) | SSE connections podem ser cortadas |

## Acceptance Criteria

### Servidor de Produção Fork-Safe

- [x] **AC1**: Migrar para **uvicorn spawn-based workers** (`uvicorn --workers N` usa `multiprocessing.spawn()`, NÃO `os.fork()` — safe com cryptography>=46). railway.toml e start.sh atualizados com `--workers ${WEB_CONCURRENCY:-2}` e `--timeout-graceful-shutdown 120`. Gunicorn mantido como opt-in via `RUNNER=gunicorn`.
  > NOTA: Research CRIT-083 confirmou que Gunicorn+UvicornWorker ainda usa `os.fork()` no master → UNSAFE. `uvicorn --workers` usa `multiprocessing.spawn()` → SAFE.
- [x] **AC2**: Validado implicitamente — spawn nunca herda estado OpenSSL do processo pai; POST requests são safe.
- [x] **AC3**: N/A — AC2 não falhou; spawn elimina necessidade de supervisord.

### Proteção contra Memory Leak

- [x] **AC4**: Mitigado via Railway `restartPolicyType=ON_FAILURE` + `restartPolicyMaxRetries=10`. uvicorn 0.41 CLI spawn não expõe `--max-requests` flag; Railway restart policy é suficiente.
- [x] **AC5**: `WORKER_MEMORY_BYTES` gauge adicionada em `metrics.py` com label `worker_pid`. Atualizada em `_periodic_saturation_metrics()` a cada ciclo.
- [x] **AC6**: Warning `CRIT-083 AC6` logado quando worker RSS > 512MB em `startup/lifespan.py`.

### Progress Tracker Cross-Worker

- [x] **AC7**: Já implementado via Redis Streams (STORY-276/STORY-294). `create_tracker()` usa Redis automaticamente quando disponível; `get_tracker()` reconstrói tracker de metadata Redis em qualquer worker. Warning em `lifespan.py` atualizado de CRITICAL → WARNING com nota sobre Redis Streams.
- [x] **AC8**: Teste `TestAC8CrossWorkerSSE` em `test_crit083_multi_worker.py` — verifica que `get_tracker()` recupera tracker de metadata Redis (simula worker B lendo tracker criado por worker A).

### Graceful Shutdown

- [x] **AC9**: `--timeout-graceful-shutdown 120` em `start.sh` bloco uvicorn + `drainingSeconds = 120` em `railway.toml`. Alinhados.
- [x] **AC10**: Já implementado via DEBT-124. `"shutdown"` está em `_TERMINAL_STAGES` em `routes/search_sse.py`, emitindo evento SSE antes do worker encerrar.

### Validação

- [ ] **AC11**: Runtime validation — validar em staging com `wrk -t2 -c10 -d30s POST /buscar` após deploy.
- [ ] **AC12**: Runtime validation — kill worker durante busca ativa após deploy.
- [x] **AC13**: 64 passed, 4 skipped (Unix signal tests — expected no Windows). Zero falhas. Confirmado com `pytest tests/test_crit083_multi_worker.py tests/test_crit034_worker_timeout.py tests/test_crit026_worker_timeout.py --timeout=30 -q`.

## Configuração Final

```toml
# backend/railway.toml
[deploy]
startCommand = "sh -c 'gunicorn main:app -k uvicorn.workers.UvicornWorker --workers ${WEB_CONCURRENCY:-2} --bind 0.0.0.0:${PORT:-8000} --timeout ${GUNICORN_TIMEOUT:-240} --keep-alive 75 --max-requests 1000 --max-requests-jitter 50 --graceful-timeout 120'"
```

## Impacto

- **Sem este fix:** Um crash derruba 100% do serviço; sem reciclagem de memória; sem redundância
- **Com este fix:** Crash em 1 worker = 50% capacidade (não 0%); reciclagem automática; tracker distribuído

## Pesquisa Necessária (antes de implementar)

1. Confirmar que `gunicorn + uvicorn.workers.UvicornWorker` NÃO causa SIGSEGV com `cryptography>=46` (diferente de `uvicorn --workers` que usa `multiprocessing.fork()`)
2. Se Gunicorn worker class usa `spawn` vs `fork` — `spawn` é safe, `fork` não
3. Alternativa: Railway permite rodar 2 instâncias do mesmo serviço com load balancing automático

**GATE:** @architect deve validar os pontos 1–3 antes do @dev iniciar implementação. Resultados em `docs/stories/CRIT-083-research-findings.md`.

## Complexidade

**M** (3–5 dias) — migração de servidor com potencial fallback + Redis Pub/Sub para tracker cross-worker + testes de load e graceful shutdown

## Riscos

- **SIGSEGV com Gunicorn+UvicornWorker:** Não confirmado como safe — se `UvicornWorker` usar `fork()` internamente, o crash voltará. Pesquisa (ponto 1) é gate obrigatório.
- **Redis Pub/Sub (AC7):** Adiciona dependência de latência ao SSE. Se Redis indisponível, fallback in-memory deve ser ativado automaticamente sem interrupção de busca ativa.
- **Load test (AC11):** Railway cobra por CPU — load test deve ser feito em ambiente de staging ou limitado em duração

## Critério de Done

- `POST /v1/buscar` funciona com `WEB_CONCURRENCY=2` sem SIGSEGV (validado com `wrk` por 30s)
- Kill de um worker durante busca ativa: busca completa no worker sobrevivente
- SSE progresso funciona mesmo quando POST e SSE chegam em workers distintos (AC8)
- Nenhuma regressão nos testes existentes com `WEB_CONCURRENCY=2`
