# STORY-1.6: CRIT-080 SIGSEGV Deep-Dive Investigation Kickoff (TD-SYS-001)

**Priority:** P0 (production reliability — POST endpoints crasham intermitentemente)
**Effort:** L (16-40h, ongoing — kickoff é P0 mas full resolução pode estender)
**Squad:** @architect (lead) + @dev (executor) + @devops (deployment validation)
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 0 (kickoff) → potencial sprint 1-2 spillover

---

## Story

**As a** usuário SmartLic,
**I want** que requests POST (`/buscar`, `/checkout`, `/feedback`) não crashem com SIGSEGV intermitente,
**so that** funcionalidades core sejam confiáveis e taxa de erro Sentry caia abaixo de 0.1% requests.

---

## Contexto

CRIT-080 (documentado em CLAUDE.md): combinação `jemalloc LD_PRELOAD` + `Sentry StarletteIntegration` + `cryptography>=46` causa SIGSEGV em POST requests durante TLS handshake. GET requests funcionam. Mitigations atuais (StarletteIntegration desabilitado, uvloop off, OTEL HTTP-only) reduzem mas não eliminam o problema completamente.

Esta story é o **kickoff** da investigação sistemática — não promete fix completo (pode levar consultoria especializada). Entregable é diagnóstico claro + plano de remediação.

---

## Acceptance Criteria

### AC1: Reprodução em ambiente isolado

- [ ] Setup local Docker que reproduz SIGSEGV (mesmo Dockerfile da prod)
- [ ] Documentar exact steps para reproduzir
- [ ] Capturar core dump + stack trace

### AC2: Bissection das deps

- [ ] Testar matrix de versões cryptography (45, 46, 47) × Sentry (versão atual, sem StarletteIntegration, sem Sentry) × jemalloc (on, off)
- [ ] Documentar qual combinação specific dispara
- [ ] Identificar minimal reproducer

### AC3: Plano de remediação

- [ ] Documento `docs/architecture/CRIT-080-investigation.md` com:
  - Root cause analysis
  - 3 opções de remediação (com trade-offs)
  - Recomendação técnica
  - Estimativa de esforço para implementar fix

### AC4: Métricas baseline

- [ ] Sentry dashboard: taxa de SIGSEGV em POST endpoints (último 7 dias)
- [ ] Documentar como métrica para comparar pós-fix

---

## Tasks / Subtasks

- [ ] Task 1: Setup reprodução local (AC1)
  - [ ] Docker compose com mesmo build da prod
  - [ ] Stress test POST endpoints com `wrk` ou `k6`
  - [ ] Configurar core dump capture
- [ ] Task 2: Bissection (AC2)
  - [ ] Build matrix de Dockerfiles
  - [ ] Run tests por combinação (16-24 builds esperados)
  - [ ] Tabular resultados
- [ ] Task 3: Investigation deep-dive
  - [ ] Search GitHub issues: `cryptography` + `jemalloc` + `gunicorn`
  - [ ] Search GitHub issues: `sentry-sdk` + `StarletteIntegration` + `segfault`
  - [ ] Consultar EXA web search por casos similares 2026
- [ ] Task 4: Documento de plano (AC3)
  - [ ] Criar `docs/architecture/CRIT-080-investigation.md`
  - [ ] 3 opções típicas:
    - A) Replace jemalloc por glibc malloc (perf trade-off)
    - B) Re-enable StarletteIntegration com versão Sentry específica
    - C) Replace cryptography com versão 45.x (security trade-off)
- [ ] Task 5: Baseline métricas (AC4)
  - [ ] Query Sentry API para POST error rate
  - [ ] Snapshot screenshot do dashboard

---

## Dev Notes

### Relevant Source Files

- `backend/Dockerfile` — onde jemalloc LD_PRELOAD é configurado
- `backend/requirements.txt` — versão cryptography
- `backend/main.py` — Sentry init (StarletteIntegration disabled)
- `backend/start.sh` — Gunicorn launcher
- `CLAUDE.md` linha 213+ — context histórico do CRIT-080

### Key Tools

- `gdb` para análise de core dump
- `py-spy` para Python stack inspection
- `valgrind` para memory analysis
- Sentry MCP / API para fetch metrics

### Known Workarounds (atual)

```python
# main.py
sentry_sdk.init(
    integrations=[
        # StarletteIntegration(),  # DISABLED — CRIT-080
        FastApiIntegration(),
    ],
    ...
)
```

```dockerfile
# Dockerfile
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2
```

### Constraints

- **NÃO** desabilitar Sentry inteiro (perda de observability)
- **NÃO** rollback cryptography sem security audit (CVEs recentes)
- Testar mudanças primeiro em staging com canary

---

## Testing

- **Stress test**: `k6` com 100 RPS POST `/buscar` por 10min
- **Sentry monitoring**: rate de SIGSEGV antes/depois
- **Canary deploy**: 5% traffic primeiro, observa 24h

---

## Definition of Done (kickoff scope)

- [ ] Reprodução local funciona
- [ ] Bissection completa (matrix tabulada)
- [ ] Plano de remediação documentado
- [ ] Baseline métricas capturadas
- [ ] Decisão de qual opção implementar (sponsor approval)
- [ ] Story de implementação criada (STORY-X.Y para Sprint 1-2)

---

## Risks

- **R1**: Investigation pode revelar bug em dependência upstream sem fix disponível → mitigation: contribute upstream ou consultoria especializada
- **R2**: Reprodução local não consegue replicate prod (Railway-specific) → mitigation: usar staging Railway environment
- **R3**: Esforço pode exceder 40h significantly → mitigation: timeboxar; se >40h, escalate sponsor

---

## Change Log

| Date       | Version | Description                                  | Author |
|------------|---------|----------------------------------------------|--------|
| 2026-04-14 | 1.0     | Initial draft from EPIC-TD-2026Q2 Phase 10  | @sm    |
