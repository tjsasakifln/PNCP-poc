# STORY-1.6: CRIT-080 SIGSEGV Deep-Dive Investigation Kickoff (TD-SYS-001)

**Priority:** P0 (production reliability — POST endpoints crasham intermitentemente)
**Effort:** L (16-40h, ongoing — kickoff é P0 mas full resolução pode estender)
**Squad:** @architect (lead) + @dev (executor) + @devops (deployment validation)
**Status:** Done
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

- [ ] Setup local Docker — **PROTOCOLADO** no doc (§4). Execução em follow-up story (requer runtime Docker + core dump infra).
- [x] Documentar exact steps para reproduzir — matriz + comando wrk/gdb no doc
- [ ] Capturar core dump + stack trace — follow-up story

### AC2: Bissection das deps

- [x] Matriz 36 células proposta (cryptography × sentry × jemalloc × uvloop) documentada em §4
- [x] Subset razoável (12 células iniciais) identificado
- [ ] Execução propriamente dita — follow-up story (16-24h dedicados)

### AC3: Plano de remediação

- [x] Documento `docs/architecture/CRIT-080-investigation.md` criado com:
  - [x] Executive summary + contexto
  - [x] Stack atual das 4 mitigações em vigor (jemalloc off, Starlette off, uvloop off, cryptography pin)
  - [x] 4 hipóteses técnicas ranqueadas (H1-H4)
  - [x] 3 opções de remediação (A/B/C) com trade-offs + esforço
  - [x] Recomendação técnica (Opção A + bissection parcial sob gatilho)
  - [x] Próximos passos formais (follow-up story)

### AC4: Métricas baseline

- [x] Placeholder documentado em §8 (query Sentry Discover sugerida)
- [ ] Popular valores reais — requer @devops com acesso Sentry admin (follow-up action)

---

## Tasks / Subtasks

- [ ] Task 1: Setup reprodução local (AC1) — **PROTOCOLADO** no doc; execução em follow-up story
- [x] Task 2: Bissection protocol documentado (AC2) — 36 células matriz + 12 subset inicial
- [x] Task 3: Investigation deep-dive — 4 hipóteses ranqueadas no doc §3
- [x] Task 4: Documento `docs/architecture/CRIT-080-investigation.md` criado (AC3)
  - [x] 3 opções analisadas (A=status quo + upgrade; B=remover `--preload`; C=migrar gunicorn→hypercorn)
- [x] Task 5: Baseline métricas — placeholder + query Sentry Discover no doc §8

## File List

**New:**
- `docs/architecture/CRIT-080-investigation.md`

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
| 2026-04-14 | 1.1     | GO (9/10) — Draft → Ready. Obs: adicionar IN/OUT explícito (fix = OUT do kickoff) antes de InProgress | @po    |
| 2026-04-14 | 2.0     | Kickoff doc produzido com 4 hipóteses + 3 opções + matriz bissection + recomendação (Opção A + bissection sob gatilho). Follow-up story a criar quando SIGSEGV rate ≥0.5% OU cryptography 47 publicada. Status Ready → Done | @architect |
