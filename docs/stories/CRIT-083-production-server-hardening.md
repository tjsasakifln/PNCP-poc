# CRIT-083: Production Server Hardening — Processo Resiliente e Escalável

**Status:** Ready
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

- [ ] **AC1**: Migrar para **Gunicorn com UvicornWorker** (classe `uvicorn.workers.UvicornWorker` que NÃO faz fork do event loop):
  ```bash
  gunicorn main:app -k uvicorn.workers.UvicornWorker \
    --workers 2 --timeout 240 --keep-alive 75 \
    --max-requests 1000 --max-requests-jitter 50
  ```
  NOTA: `UvicornWorker` é thread-safe e NÃO usa `os.fork()` para o event loop — é safe com cryptography.
- [ ] **AC2**: Validar que **POST requests funcionam** com 2 workers (o SIGSEGV era por `--workers` do uvicorn CLI, NÃO do Gunicorn+UvicornWorker)
- [ ] **AC3**: Se AC2 falhar (SIGSEGV persiste), fallback para **uvicorn standalone + supervisord** com 2 instâncias em portas diferentes + nginx load balancer (via Railway service splitting)

### Proteção contra Memory Leak

- [ ] **AC4**: `--max-requests 1000` + `--max-requests-jitter 50` — recicla workers a cada ~1000 requests
- [ ] **AC5**: Adicionar métrica `smartlic_worker_memory_bytes` gauge (RSS por worker)
- [ ] **AC6**: Log de warning quando worker ultrapassa 512MB RSS

### Progress Tracker Cross-Worker

- [ ] **AC7**: Se rodando com >1 worker, o `asyncio.Queue` in-memory NÃO funciona entre workers. Migrar tracker para Redis Pub/Sub:
  - `POST /buscar` publica eventos em `search:progress:{search_id}`
  - `GET /buscar-progress/{id}` subscreve ao channel Redis
  - Fallback para in-memory Queue se Redis indisponível
- [ ] **AC8**: Teste de integração: POST em worker A, SSE em worker B — progresso chega corretamente

### Graceful Shutdown

- [ ] **AC9**: Gunicorn `--graceful-timeout 120` alinhado com Railway `drainingSeconds: 120`
- [ ] **AC10**: SSE connections recebem evento `shutdown` antes do worker morrer

### Validação

- [ ] **AC11**: Load test com `wrk -t2 -c10 -d30s POST /buscar` — zero 502s com 2 workers
- [ ] **AC12**: Kill -TERM em 1 worker durante busca ativa — busca completa no outro worker
- [ ] **AC13**: Testes existentes passam com `WEB_CONCURRENCY=2`

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
