# CRIT-049: Verificação Pós-Deploy SIGSEGV + Resolução Sentry

**Epic:** Production Stability
**Sprint:** Sprint 5
**Priority:** P1 — HIGH
**Story Points:** 2 SP
**Estimate:** 1 hora (+ 24h monitoring)
**Owner:** @devops

---

## Problem

O fix CRIT-041 (commit `862d08b`) foi deployado em 2026-02-28 para resolver SIGSEGV persistente nos workers:
- Removido `uvicorn[standard]` (elimina uvloop/httptools)
- Removido grpcio + opentelemetry-exporter-otlp-proto-grpc do Dockerfile
- Faulthandler habilitado em cada worker via `post_worker_init` hook

**Porém os ACs de verificação (AC10/AC11) permanecem pendentes:**
- SMARTLIC-BACKEND-1N: `Worker (pid:504) was sent SIGSEGV!` — **259 events, ESCALATING**
- SMARTLIC-BACKEND-1B: `WORKER TIMEOUT (pid:6)` — 6 events, REGRESSED
- SMARTLIC-BACKEND-1A: `Worker (pid:6) was sent SIGABRT!` — 6 events, REGRESSED

**Questão:** Os 259 eventos são todos pré-deploy? Ou ainda há SIGSEGV ocorrendo?

---

## Acceptance Criteria

### Verificação

- [ ] **AC1:** Verificar no Sentry o timestamp do último evento SIGSEGV — se anterior ao deploy de CRIT-041, fix confirmado
- [ ] **AC2:** Verificar Railway deploy logs — confirmar que o container atual usa a imagem com CRIT-041
- [ ] **AC3:** Verificar via `railway logs` que `OK: all fork-unsafe packages removed` aparece no build log
- [ ] **AC4:** Monitorar Sentry por 24h — 0 novos eventos SIGSEGV/SIGABRT/WORKER_TIMEOUT

### Resolução Sentry

- [ ] **AC5:** Se AC4 passar: marcar SMARTLIC-BACKEND-1N como **Resolved** no Sentry (259 eventos, todos pré-fix)
- [ ] **AC6:** Se AC4 passar: marcar SMARTLIC-BACKEND-1B e 1A como **Resolved**
- [ ] **AC7:** Se AC4 NÃO passar: escalar para CRIT-050 com novo diagnóstico

### Documentação

- [ ] **AC8:** Atualizar CRIT-041 story com AC10/AC11 checados

---

## Notas

- Os logs Railway mostram startup clean: `CRIT-034: SIGABRT timeout handler installed` — handlers ativos
- Gunicorn com 2 workers, 120s timeout, max-requests=1000 + jitter
- Se SIGSEGV persistir pós-fix: próximo passo seria RUNNER=uvicorn (single-process, zero fork)
