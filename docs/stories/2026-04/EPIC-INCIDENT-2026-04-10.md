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
| [STORY-412](STORY-412-fix-search-sessions-objeto-resumo-schema-drift.md) | **P0** | S | @data-engineer + @dev | Ready | Schema drift `objeto_resumo` |
| [STORY-413](STORY-413-fix-asgi-middleware-typeerror-coroutine-missing.md) | **P0** | M | @dev + @architect | Ready | TypeError crash loop |
| [STORY-414](STORY-414-harden-schema-contract-gate-ci-validation.md) | **P0** | M | @data-engineer + @devops | Ready | Schema contract gate passivo |
| [STORY-415](STORY-415-fix-trigger-prevent-privilege-escalation-is-master.md) | **P0** | S | @data-engineer | Ready | Trigger `is_master` quebrado |
| [STORY-416](STORY-416-stabilize-supabase-circuit-breaker-cascade.md) | P1 | L | @architect + @dev | Ready | Supabase CB cascade global |
| [STORY-417](STORY-417-fix-perfil-b2g-brasilapi-timeout-circuit-breaker.md) | P1 | M | @dev + @architect | Ready | BrasilAPI timeout sem CB |
| [STORY-418](STORY-418-trial-email-pipeline-resilience-retry-dlq.md) | P1 | M | @dev | Ready | Trial email sem retry/DLQ |
| [STORY-419](STORY-419-fix-search-sessions-valor-total-numeric-overflow.md) | P1 | S | @data-engineer + @dev | Ready | NUMERIC(14,2) overflow |
| [STORY-420](STORY-420-remove-invalid-stripe-pix-payment-method.md) | P2 | S | @dev | Ready | Stripe PIX inválido |
| [STORY-421](STORY-421-fix-nextjs-login-rsc-invariant-error.md) | P2 | M | @dev + @ux-design-expert | Ready | Next.js RSC InvariantError |
| [STORY-422](STORY-422-frontend-sse-connection-closed-retry-cleanup.md) | P2 | M | @dev | Ready | SSE abort sem retry |
| [STORY-423](STORY-423-sentry-hygiene-cleanup-stale-issues.md) | P2 | S | @devops | Ready | Sentry backlog poluído |
| [STORY-424](STORY-424-enable-pix-via-stripe-checkout-session-options.md) | P3 | L | @dev + @devops | Backlog | Follow-up PIX (Q2/2026) |

---

## Ordem de Execução Recomendada

### Sprint Emergencial (0-48h) — P0 em paralelo dev + **sequential merge (@pm 2026-04-10)**

**Desenvolvimento paralelo (4 squads, 4 branches `fix/`):**
- STORY-412 (@data-engineer + @dev) — schema drift + query fix (Opção C — remover campo)
- STORY-413 (@dev + @architect) — crash loop middleware
- STORY-414 (@data-engineer + @devops) — contract gate hardening (depende de 412)
- STORY-415 (@data-engineer) — trigger fix (Opção B — remover ref `is_master`)

**Ordem de merge imposta por @devops (sequencial com janela de observação):**

| Ordem | Story | Rationale | Janela pós-merge |
|:---:|---|---|:---:|
| **1º** | **STORY-413** | Bloqueia startup — serviço precisa estar UP antes de qualquer outro fix | 30min Sentry |
| **2º** | **STORY-415** | Desbloqueia Stripe reconciliation + admin UI (independente) | 30min Sentry |
| **3º** | **STORY-412** | Fixa trial analytics bleeding (213 eventos) | 30min Sentry |
| **4º** | **STORY-414** | Depende de 412 para validar gate funcionando | 2h Sentry + staging-first |

**Guardrails de merge:**
- Cada merge seguido de deploy Railway automático + observação Sentry
- Se qualquer merge causar regressão: **halt** (não continuar), rollback via `railway redeploy`
- @devops é único agente autorizado a merge/push P0 hotfix
- Commits via `fix/` branch + PR rápido direto para `main` (sem sprint review)

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

## Decisões Tomadas (@pm 2026-04-10)

Análise completa em conversação `docs/sessions/` (transcript @pm post-validação @po). 8 decisões elucidadas e aplicadas às stories:

| # | Decisão | Opção escolhida | Rationale |
|:---:|---|---|---|
| 1 | **STORY-420 Stripe PIX** | **B — Remover** + backlog P3 | B2B SaaS recorrente → cartão + boleto cobrem >95%. PIX pode ser re-introduzido em STORY-424 P3 |
| 2 | **STORY-415 `is_master`** | **B — Remover ref do trigger** | Investigação revelou que `is_master` é DERIVADO de `plan_type` em `authorization.py:81`, nunca foi coluna. Trigger foi bug desde o dia 1 |
| 3 | **STORY-412 `objeto_resumo`** | **C — Remover do payload** | Frontend não consome (0 matches grep). Fallback literal já existe em `analytics.py:344`. Remoção é mais limpa |
| 4 | **STORY-417 `orgao_stats`** | **A+C faseado** | Fase 1 Redis quick-win (0.5d) → Fase 2 Materialized View (1.5d) → Fase 3 índice backup. Textbook fit para dados slow-changing |
| 5 | **STORY-414 strict flag** | **Rollout faseado 14d** | P1 deploy → P2-P3 monitor staging 7-14d → P4 flip prod em janela quieta. Abort se false positive PGRST002 |
| 6 | **STORY-416 CB mode** | **Híbrido AND/OR** | `(5 consecutive) OR (rate > 0.7 AND window >= 10)`. Reduz flakiness sem perder burst detection. Thresholds via env var |
| 7 | **STORY-423 Slack** | **Criar canais Dia 0** | `#incident-response` + `#sentry-new-issues` pré-requisito de AC4. Fallback email. Webhook em env var |
| 8 | **P0 merge order** | **Parallel dev + sequential merge** | 413 → 415 → 412 → 414. Cada merge com janela de observação Sentry antes do próximo |

**Follow-up criado:**
- **STORY-424** (P3 backlog): "Enable PIX via Stripe checkout session options" — avaliar em Q2/2026. Trigger de re-priorização: >5 pedidos/mês de PIX via support

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
| 2026-04-10 | @po (Sarah) | Validação `*validate-story-draft` das 12 stories concluída. Todas GO (scores 8.5-10/10). Status Draft → Ready para todas. Pronto para `*dev develop-story`. |
| 2026-04-10 | @pm (Morgan) | 8 decisões elucidadas e aplicadas às stories (ver seção "Decisões Tomadas"). Investigações prévias resolveram condicionais em 412 (Opção C) e 415 (Opção B). Merge order P0 definido: 413 → 415 → 412 → 414. STORY-424 criada em backlog P3 como follow-up do PIX. |
