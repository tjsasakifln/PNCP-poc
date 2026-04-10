# EPIC-INCIDENT-2026-04-10: Resolução do Incidente Multi-Causa Sentry/Railway

**Priority:** P0 — Production Incident
**Status:** Draft
**Owner:** @aios-master (coordenação) + squads P0/P1/P2
**Sprint:** Emergencial (0-48h) + seguintes

---

## Contexto

Em 2026-04-10, análise consolidada de Sentry (`confenge`, 69 issues ativos em janela de 14 dias) + Railway logs (`bidiq-backend`, burst de 500 eventos ERROR em ~30 min na janela 15:32-16:02 UTC) identificou **11 causas-raiz distintas** afetando produção simultaneamente, sendo 4 P0 críticas ativamente em escalation.

**Relatório fonte:** [`docs/reports/sentry-railway-errors-2026-04-10.md`](../../reports/sentry-railway-errors-2026-04-10.md)

**Sumário das crises ativas:**

1. **Schema drift** — `search_sessions.objeto_resumo does not exist` (213 eventos, Escalating) → STORY-412 + STORY-414
2. **Crash loop ASGI** — `TypeError: func() missing 1 required positional argument: 'coroutine'` (44+44 eventos, Regressed) → STORY-413
3. **Trigger SQL quebrado** — `record "new" has no field "is_master"` (6 eventos) → STORY-415
4. **Cascade Supabase circuit breaker** — `sb_execute rejected` em múltiplos endpoints → STORY-416
5. **Timeouts BrasilAPI/perfil-b2g** — `httpx.ReadTimeout` em 42+ eventos, slow_request >110s aproximando limite Railway → STORY-417
6. **Trial email pipeline quebrado** — 23 eventos, pipeline não tem retry/DLQ → STORY-418
7. **Numeric overflow** — `precision 14 scale 2` em `search_sessions.valor_total` → STORY-419
8. **Stripe PIX inválido** — checkout quebrado há 2 dias → STORY-420
9. **Next.js InvariantError /login** — RSC vs text/plain → STORY-421
10. **Frontend SSE Connection closed** — 34 eventos, sem retry/cleanup → STORY-422
11. **Sentry hygiene** — issues já corrigidas ainda marcadas unresolved → STORY-423

---

## Stories do Epic

| Story | Priority | Effort | Squad | Status | Causa Raiz |
|-------|---------:|:------:|-------|:------:|------------|
| [STORY-412](STORY-412-fix-search-sessions-objeto-resumo-schema-drift.md) | **P0** | S | @data-engineer + @dev | Draft | Schema drift `objeto_resumo` |
| [STORY-413](STORY-413-fix-asgi-middleware-typeerror-coroutine-missing.md) | **P0** | M | @dev + @architect | Draft | TypeError crash loop |
| [STORY-414](STORY-414-harden-schema-contract-gate-ci-validation.md) | **P0** | M | @data-engineer + @devops | Draft | Schema contract gate passivo |
| [STORY-415](STORY-415-fix-trigger-prevent-privilege-escalation-is-master.md) | **P0** | S | @data-engineer | Draft | Trigger `is_master` quebrado |
| [STORY-416](STORY-416-stabilize-supabase-circuit-breaker-cascade.md) | P1 | L | @architect + @dev | Draft | Supabase CB cascade global |
| [STORY-417](STORY-417-fix-perfil-b2g-brasilapi-timeout-circuit-breaker.md) | P1 | M | @dev + @architect | Draft | BrasilAPI timeout sem CB |
| [STORY-418](STORY-418-trial-email-pipeline-resilience-retry-dlq.md) | P1 | M | @dev | Draft | Trial email sem retry/DLQ |
| [STORY-419](STORY-419-fix-search-sessions-valor-total-numeric-overflow.md) | P1 | S | @data-engineer + @dev | Draft | NUMERIC(14,2) overflow |
| [STORY-420](STORY-420-remove-invalid-stripe-pix-payment-method.md) | P2 | S | @dev | Draft | Stripe PIX inválido |
| [STORY-421](STORY-421-fix-nextjs-login-rsc-invariant-error.md) | P2 | M | @dev + @ux-design-expert | Draft | Next.js RSC InvariantError |
| [STORY-422](STORY-422-frontend-sse-connection-closed-retry-cleanup.md) | P2 | M | @dev | Draft | SSE abort sem retry |
| [STORY-423](STORY-423-sentry-hygiene-cleanup-stale-issues.md) | P2 | S | @devops | Draft | Sentry backlog poluído |

---

## Ordem de Execução Recomendada

### Sprint Emergencial (0-48h) — P0 em paralelo
- STORY-412 (@data-engineer + @dev) — schema drift + query fix
- STORY-413 (@dev + @architect) — crash loop middleware
- STORY-414 (@data-engineer + @devops) — contract gate hardening (segue 412)
- STORY-415 (@data-engineer) — trigger fix (independente)

**Gate de passagem para sprint seguinte:** Zero eventos Escalating/Regressed dos 4 issues P0 referenciados nas últimas 6h após deploy.

### Sprint Seguinte (48h-1w) — P1 em ordem de dependência
- STORY-416 (prioridade, habilita observability) → depois STORY-417 (reusa CB pattern) → STORY-418 (depende de 416 estabilizar) + STORY-419 (independente)

### Sprint Rotina (1w-2w) — P2 paralelo
- STORY-420, STORY-421, STORY-422, STORY-423

---

## Definition of Done (Epic)

- [ ] Todas as 12 stories em status `Done`
- [ ] Zero eventos **Escalating** ou **Regressed** no Sentry para os 11 issues referenciados
- [ ] Zero eventos dos error codes cobertos nas últimas 24h após último deploy
- [ ] Runbooks novos criados: `docs/runbook/supabase-circuit-breaker.md`, `docs/runbook/trial-email-pipeline.md`, `docs/runbook/sentry-triage.md`
- [ ] `migration-check.yml` workflow estendido com validação do schema contract (STORY-414 AC3)
- [ ] Postmortem em `docs/incidents/2026-04-10-multi-cause.md` documentando timeline, causa raiz e aprendizados

---

## Guardrails

- **Nenhuma story pode ser marcada Done** antes de verificação pós-deploy no Sentry (janela de 6h com zero eventos do error code alvo).
- **P0 stories devem ir direto para main** via hotfix branch, sem esperar sprint review.
- **Migrations devem ser validadas em staging** antes de prod (ver `.github/workflows/migration-check.yml`).
- **Todas as mudanças em `backend/supabase_client.py`** (STORY-416) exigem code review de @architect.

---

## Métricas de Sucesso

| Métrica | Baseline (2026-04-10) | Target |
|---------|----------------------:|-------:|
| Issues Sentry Escalating | 3 | 0 |
| Issues Sentry Regressed | 2 | 0 |
| Total eventos 14d | ~900 | <100 |
| Error rate backend (Sentry) | >1% | <0.1% |
| Slow requests >60s | 6+ | 0 |
| Schema contract violations | Ativo (Fatal) | 0 |

---

## Links

- **Relatório consolidado:** [`docs/reports/sentry-railway-errors-2026-04-10.md`](../../reports/sentry-railway-errors-2026-04-10.md)
- **Sentry dashboard:** https://confenge.sentry.io/issues/?query=is%3Aunresolved&statsPeriod=14d
- **Runbook incident response:** `docs/runbook/incident-response.md`
- **CLAUDE.md — Critical Implementation Notes:** seção sobre Supabase, PNCP, filtering pipeline

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Epic criado a partir de análise Sentry/Railway consolidada |
