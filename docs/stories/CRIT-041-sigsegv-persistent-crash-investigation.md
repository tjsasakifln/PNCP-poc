# CRIT-041: Investigar SIGSEGV Residual nos Workers

**Epic:** Production Stability
**Sprint:** Sprint 4
**Priority:** P2 — MEDIUM (preventivo)
**Story Points:** 5 SP
**Estimate:** 2-3 horas
**Owner:** @dev + @devops

---

## Problem

Após o fix CRIT-SIGSEGV (commit `b959cac`):
- Removido `uvicorn[standard]` → `uvicorn` (sem uvloop/httptools)
- Removido grpcio via `pip uninstall -y grpcio grpcio-status` no Dockerfile
- Habilitado `faulthandler.enable()` no topo de main.py
- Desabilitado `--preload` por padrão em start.sh

O Sentry registrou 55 eventos SIGSEGV (SMARTLIC-BACKEND-1N) nas últimas 48h, porém **todos ocorreram ANTES do deploy mais recente** (último SIGSEGV: ~19h atrás, deploy atual estável desde 14:22 UTC sem crashes). O fix parece ter funcionado, mas o issue Sentry permanece "Escalating" por conta do volume histórico.

**Status:** Monitoramento preventivo — confirmar que o fix é definitivo e resolver o issue no Sentry.

---

## Hipóteses de Investigação

### H1: Dockerfile cache bust desatualizado
O `LABEL build.timestamp="2026-02-20T12:00:00"` no Dockerfile pode não ter forçado rebuild. Railway pode estar usando imagem antiga (pré-fix) se o cache layer não foi invalidado.

**Ação:** Verificar se a imagem em produção realmente NÃO contém grpcio:
```bash
railway run pip list | grep -i grpc
railway run python -c "import uvloop; print('UVLOOP PRESENT')" 2>&1
```

### H2: cryptography C extension + --preload
start.sh documenta: "cryptography>=46.0.5 + --preload causes SIGSEGV". Embora `--preload` esteja desabilitado por padrão, verificar se `GUNICORN_PRELOAD=true` está setado em Railway.

### H3: Outro C extension fork-unsafe
Verificar todos os C extensions instalados no container:
```bash
railway run python -c "
import pkgutil, importlib
for m in pkgutil.iter_modules():
    try:
        mod = importlib.import_module(m.name)
        if hasattr(mod, '__file__') and mod.__file__ and ('.so' in mod.__file__ or '.pyd' in mod.__file__):
            print(f'{m.name}: {mod.__file__}')
    except: pass
"
```

### H4: Memory pressure (OOM → SIGSEGV)
Workers com `WEB_CONCURRENCY=2` em container com 8GB. Se um worker usa muita memória (large search results), o OOM killer pode enviar SIGSEGV ao invés do esperado SIGKILL.

---

## Acceptance Criteria

### Diagnóstico

- [x] **AC1:** `railway run pip list | grep -iE "grpc|uvloop|httptools"` → **grpcio 1.73.0, grpcio-status 1.71.0, httptools 0.7.1 PRESENT** (uvloop absent). Root cause: `opentelemetry-exporter-otlp` umbrella package re-installs `otlp-proto-grpc` → grpcio after `pip uninstall`.
- [x] **AC2:** `railway run python -c` only tests bare Python (not workers). Added `faulthandler.enable()` to `gunicorn_conf.py:post_worker_init()` to guarantee it's active in every worker regardless of import order.
- [x] **AC3:** `railway variables` → GUNICORN_PRELOAD absent (defaults to `false` in start.sh). WEB_CONCURRENCY=2. **PASS**.
- [x] **AC4:** No SIGSEGV events since latest deploy (55 historical events, all pre-fix). Faulthandler now guaranteed in workers via `post_worker_init` hook — any future crash will show full Python+C traceback.
- [x] **AC5:** No active crashes to capture. Previous 55 events occurred BEFORE grpcio removal attempt. With extended uninstall (AC6) + faulthandler in workers (AC2), any future crash will produce actionable stack traces.

### Fix (baseado no diagnóstico)

- [x] **AC6:** Dockerfile updated: `build.timestamp="2026-02-28T18:00:00"`, `CACHEBUST=20260228v1`. Extended `pip uninstall` to also remove `opentelemetry-exporter-otlp-proto-grpc`, `opentelemetry-exporter-otlp`, `httptools`. Added verification echo.
- [x] **AC7:** Identified C extensions: grpcio (fork-unsafe gRPC), httptools (fork-unsafe HTTP parser), otlp-proto-grpc (pulls grpcio). All removed in Dockerfile post-install. Documented in requirements.txt comments.
- [x] **AC8:** WEB_CONCURRENCY=2 on 8GB container — no OOM evidence in recent logs. No change needed. If OOM recurs, `RUNNER=uvicorn` (AC9) eliminates fork overhead entirely.
- [x] **AC9:** Added `RUNNER=uvicorn` option to start.sh — uses `uvicorn main:app` standalone (single-process, no fork). Default remains `RUNNER=gunicorn` for backward compat. Set `RUNNER=uvicorn` in Railway to eliminate ALL fork-unsafe issues.

### Validação

- [ ] **AC10:** Após fix, monitorar Sentry por 24h — 0 eventos SIGSEGV _(requires deploy + 24h monitoring)_
- [ ] **AC11:** Verificar que `smartlic_sse_connection_errors_total` não aumentou (sem regressão) _(requires deploy + monitoring)_

---

## Contexto Técnico

**Por que SIGSEGV em ASGI workers:**
- Gunicorn usa prefork model: processo pai faz fork() → processos filhos herdam memória
- C extensions (grpcio, uvloop, cryptography) usam thread-local state que é invalidado no fork
- Resultado: child process acessa memória corrompida → SIGSEGV

**Referências:**
- [gunicorn fork SIGSEGV issue #2761](https://github.com/benoitc/gunicorn/issues/2761)
- [grpc SIGSEGV issue #23796](https://github.com/grpc/grpc/issues/23796)
- [Python faulthandler docs](https://docs.python.org/3.12/library/faulthandler.html)
- [uvicorn deployment without gunicorn](https://www.uvicorn.org/deployment/)

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/Dockerfile` | Cache bust 20260228v1, extended pip uninstall (5 packages), verification echo |
| `backend/start.sh` | Added `RUNNER=uvicorn` standalone mode (no-fork), default still gunicorn |
| `backend/requirements.txt` | Updated comments documenting umbrella package risk |
| `backend/gunicorn_conf.py` | Added `faulthandler.enable()` in `post_worker_init` hook |
| `docs/stories/CRIT-041-*` | AC checkboxes updated with diagnostic findings |
