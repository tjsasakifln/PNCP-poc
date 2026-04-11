# Postmortem — Incidente Multi-Causa 2026-04-10

**Severity:** P0 (production)
**Detection:** 2026-04-10, análise consolidada Sentry + Railway logs
**Status:** Mitigated (12 stories InReview 2026-04-11) · awaiting Sentry 48h
observation window
**Authors:** @dev, @pm, @po
**Origin:** [EPIC-INCIDENT-2026-04-10](../stories/2026-04/EPIC-INCIDENT-2026-04-10.md)
**Related report:** [docs/reports/sentry-railway-errors-2026-04-10.md](../reports/sentry-railway-errors-2026-04-10.md)

---

## Resumo executivo

Em 2026-04-10, análise consolidada do dashboard Sentry (69 issues unresolved
em 14 dias) + burst de ~500 eventos ERROR no Railway (janela 15:32–16:02 UTC)
revelou **11 causas-raiz distintas** afetando produção simultaneamente. Quatro
eram P0 ativamente em *Escalating*/*Regressed* e comprometiam funcionalidades
críticas: trial analytics, startup ASGI, Stripe reconciliation e schema drift.
Outros sete eram P1/P2 com impacto direto em revenue (checkout) ou experiência
(login, SSE, triagem Sentry poluída).

Em 48 horas o time entregou todas as 12 stories em modo `InReview`, cobrindo
desde correções tácticas (remoção de PIX do Stripe, filter `beforeSend` para
USER_CANCELLED) até ajustes estruturais (circuit breaker Supabase híbrido
AND/OR, DLQ para trial email, schema contract gate passivo → ativo faseado).

Nenhum usuário perdeu dados. Perdas estimadas concentradas em:
- ~23 emails de trial não entregues (~R$ 9.131 em MRR em risco)
- Checkout quebrado há 2 dias (impacto direto em trial→pro conversion)
- 34 eventos Sentry de SSE connection closed que eram ruído legítimo mas
  escondiam 1 a 2 timeouts reais por dia

---

## Timeline

**Todos os horários em UTC.**

| Momento | Evento |
|---|---|
| 2026-04-10 — início | @pm abre dashboard Sentry e inicia análise consolidada com Railway logs em paralelo |
| 2026-04-10 — manhã | Relatório `docs/reports/sentry-railway-errors-2026-04-10.md` consolidando 11 causas-raiz |
| 2026-04-10 — meio-dia | @sm cria 12 stories (412–423) a partir do relatório, uma por causa-raiz |
| 2026-04-10 — tarde | @po valida as 12 stories (10-point checklist), todas com verdict GO (8.5–10/10). Transição Draft → Ready |
| 2026-04-10 — tarde | @pm elicita 8 decisões estratégicas: remoção de PIX (Opção B), remoção de `is_master` ref no trigger (Opção B), remoção de `objeto_resumo` do payload (Opção C), rollout faseado para STORY-414 strict flag, Supabase CB em modo híbrido AND/OR, merge order P0 `413 → 415 → 412 → 414` |
| 2026-04-10 — tarde/noite | @dev executa YOLO sprint P0/P1: 8 stories (412–419) implementadas em paralelo. 62 novos testes, 3 migrations, 2 runbooks. StarletteIntegration removido do Sentry (root cause secundário do STORY-413) |
| 2026-04-10 — fim | 8 stories em `InReview` aguardando deploy + observação Sentry 6h |
| 2026-04-11 — início | @dev YOLO sprint P2: 4 stories (420–423) implementadas em paralelo — fix PIX, login error.tsx, SSE close_reason filter, sentry-triage runbook |
| 2026-04-11 | Postmortem criado (este documento). 12/12 stories em `InReview` |
| 2026-04-11+ | Aguarda merge/deploy + observação Sentry 48h para transição final → `Done` |

---

## Causas-raiz

### P0 (startup/data integrity)

| # | Story | Causa | Decisão | Mitigação |
|---|---|---|---|---|
| 1 | STORY-412 | `search_sessions.objeto_resumo` coluna removida mas ainda no payload da API (213 eventos Escalating) | Opção C: remover do payload (frontend não consome, fallback literal já existe em `analytics.py:344`) | Query atualizada; payload limpo |
| 2 | STORY-413 | `TypeError: func() missing 1 required positional argument: 'coroutine'` em ASGI middleware (44+44 eventos Regressed) — StarletteIntegration Sentry conflict | Remover StarletteIntegration do stack Sentry | StarletteIntegration desabilitado |
| 3 | STORY-414 | Schema contract gate CI existia mas era passivo (não falhava o build) — deixou schema drift passar | Rollout faseado 14d: P1 deploy monitor → P2-P3 staging 7-14d → P4 strict em janela quieta | Gate mantido passivo, rollout planejado |
| 4 | STORY-415 | Trigger SQL referenciava `new.is_master` mas `is_master` é derivado de `plan_type` em `authorization.py:81` — nunca foi coluna (bug desde dia 1) | Opção B: remover ref do trigger | Migration 415 corrige trigger |

### P1 (cascades)

| # | Story | Causa | Mitigação |
|---|---|---|---|
| 5 | STORY-416 | Cascade Supabase CB global — um endpoint disparava OPEN em todos os outros | CB híbrido AND/OR por categoria: `(5 consecutive) OR (rate > 0.7 AND window >= 10)`; categorias `read`/`write`/`rpc`; thresholds via env var |
| 6 | STORY-417 | BrasilAPI `httpx.ReadTimeout` sem CB próprio causando slow_request >110s no `/perfil-b2g` | Fase 1 Redis quick-win (0.5d); Fase 2 Materialized View (1.5d); Fase 3 índice backup |
| 7 | STORY-418 | Trial email pipeline sem retry/DLQ — ~23 emails perdidos no incidente | Nova tabela `trial_email_dlq` + reprocess com backoff `[30, 60, 120]`; abandono após 5 attempts |
| 8 | STORY-419 | `search_sessions.valor_total NUMERIC(14,2)` overflow em buscas com teto R$ 1e15+ | Widen para `NUMERIC(18,2)` + clamp defensivo no frontend (`VALOR_CEILING = 1e15`) |

### P2 (ruído e revenue)

| # | Story | Causa | Mitigação |
|---|---|---|---|
| 9 | STORY-420 | Stripe Brasil não aceita `"pix"` em `payment_method_types` para subscription mode — checkout quebrado há 2 dias, trial → pro bloqueado | Remoção de `"pix"`; try/except `InvalidRequestError → HTTP 400` / `StripeError → HTTP 503`. Follow-up: STORY-424 (Q2/2026) via `payment_method_options.pix` |
| 10 | STORY-421 | Next.js `InvariantError: Expected RSC response, got text/plain` em `/login` (6 eventos, Next.js upstream bug) | `frontend/app/login/error.tsx` novo client component com detecção de InvariantError + hard-reload (bypass RSC cache poisoning) |
| 11 | STORY-422 | SSE "Connection closed" (34 eventos) — mistura de USER_CANCELLED (ruído legítimo) com timeouts reais escondidos | Instrumentação de `close_reason` no abort + `Sentry.addBreadcrumb`/`setTag` + `beforeSend` filter drop USER_CANCELLED/NAVIGATION/bare AbortError |
| 12 | STORY-423 | Sentry backlog poluído (69 issues unresolved), sem rotina de triagem, sem alert rules ativos | `docs/runbook/sentry-triage.md` (runbook semanal 30min) + `docs/operations/alerting-runbook.md` seção 1.2b (3 alert rules novas) |

---

## Aprendizados

### 1. **Schema contract gates devem ser ativos desde o dia 1**

O gate existia como CI step mas era passivo (warn-only). Schema drift passou
despercebido por N dias até o crash em produção. Lição: warn-only gates não
existem — ou bloqueiam, ou são ruído. A mitigação (rollout faseado de 14d para
ativar o strict mode) foi o compromisso possível sem quebrar deploys legítimos,
mas a lição é universal: **gates precisam ter dente desde o primeiro deploy ou
nunca terão**.

### 2. **Cascade circuit breaker é pior que ausência de CB**

O Supabase CB foi projetado como singleton global. Um endpoint pouco usado
disparou OPEN e derrubou todo o resto por 60s. Lição: **CBs devem ser
particionados por categoria** (`read`/`write`/`rpc`) e ter critério híbrido
(consecutive OR rate-based) para evitar flakiness sem perder burst detection.
A Textbook `hystrix` sugere exatamente isso — tínhamos uma implementação
simplificada demais.

### 3. **Fire-and-forget email pipelines são mentira**

Trial email sequence usava `asyncio.create_task` sem tratar falhas. Quando
Resend throttled ou render falhou, emails sumiram sem log, sem retry, sem
DLQ. Lição: **toda operação com side-effect em terceiros precisa de DLQ** se
o negócio depende dela. ~R$ 9.131 em MRR em risco é uma confirmação cara.

### 4. **Stripe Brasil não é igual a Stripe US**

`payment_method_types: ["pix"]` funciona em payment mode mas não em
subscription mode no Brasil. Documentação confusa. Lição: **quando adicionar
método de pagamento em região não-US, validar o contract test no modo
`subscription` antes do merge**, não só no modo `payment`. Follow-up:
STORY-424 é a via documentada (payment_method_options.pix + `create_payment_method` API).

### 5. **Sentry dashboard limpa ≠ Sentry dashboard correto**

Operar com 69 issues unresolved esconde regressões reais. O runbook de triagem
semanal (`docs/runbook/sentry-triage.md`) é a resposta para **tornar a
limpeza recorrente e auditável** em vez de um mutirão ocasional.

### 6. **Erros "conhecidos" precisam ser explicitamente filtrados**

34 eventos de "Connection closed" no Sentry eram em sua maioria legítimos —
usuários cancelando buscas. Mas sem tag `close_reason`, não havia como
distinguir ruído de regressão real. Lição: **sempre taggar erros intencionais
com contexto**, nunca confiar que "AbortError é óbvio que é user cancel". O
`beforeSend` filter sem a tag seria uma armadilha — dropariam regressões reais.

### 7. **Incidentes multi-causa requerem paralelismo**

O instinto em incidente P0 é serializar ("resolver um de cada vez"). Com 11
causas-raiz, serializar significaria 11x N horas sequenciais. A estratégia
`parallel dev + sequential merge` da @pm foi correta: dev paralelo (4 squads,
4 branches `fix/`), merge sequencial com janela de observação Sentry entre
cada deploy. Lição: **em incidentes multi-causa, otimizar para deploy
independent units** (uma per CR) e não para rollback atomicity.

---

## Ações tomadas

### Code / infra (entregues — InReview)

- ✅ 12 stories (412–423) implementadas em YOLO sprint de ~30h (2026-04-10 → 2026-04-11)
- ✅ 3 migrations novas (415 trigger fix, 418 DLQ, 419 widen NUMERIC)
- ✅ 3 runbooks novos (`supabase-circuit-breaker.md`, `trial-email-pipeline.md`, `sentry-triage.md`)
- ✅ StarletteIntegration removido da inicialização Sentry (STORY-413 root cause secundária)
- ✅ Alert rules 14/15/16 documentadas em `docs/operations/alerting-runbook.md` (setup manual @devops pendente)
- ✅ Postmortem escrito (este documento)
- ✅ EPIC DoD atualizado: 12/12 stories `InReview`, 3 runbooks, postmortem entregues

### Ações pós-deploy (follow-up @devops)

- [ ] Merge ordenado `413 → 415 → 412 → 414 → 416 → 417 → 418 → 419 → 420 → 421 → 422 → 423`
- [ ] Deploy Railway após cada merge P0 com janela de observação 30min no Sentry
- [ ] Criar canais Slack `#incident-response` + `#sentry-new-issues`
- [ ] Setar `SENTRY_SLACK_WEBHOOK` no Railway (`railway variables set --service bidiq-backend SENTRY_SLACK_WEBHOOK=...`)
- [ ] Configurar alert rules 14/15/16 no Sentry UI (ver `docs/operations/alerting-runbook.md` seção 1.2b)
- [ ] Marcar issues já corrigidas como `Resolved` no Sentry (AC1/AC2 da STORY-423)
- [ ] Investigar 4 RemoteProtocolError issues (7396815149/134/122, 7387730654) — AC5 da STORY-423
- [ ] Janela de observação 48h após último deploy com métricas target:
  - 0 eventos Escalating/Regressed dos 11 issues referenciados
  - Volume Sentry 14d `<100` (baseline era ~900)
  - Slow requests >60s `== 0`
  - Volume de SSE connection closed `>80% menor` (STORY-422 AC7)
- [ ] Transição final `InReview → Done` de todas as 12 stories após validação

### Follow-ups de médio prazo

- [ ] **STORY-424** (P3 backlog): re-avaliar PIX via `payment_method_options.pix` em Q2/2026 ou quando receber >5 pedidos/mês de PIX via support
- [ ] Rollout faseado da STORY-414 strict flag: monitor 7-14d staging → flip prod em janela quieta
- [ ] Avaliar migração do Sentry filter de `beforeSend` para Inbound Filters no UI (mais performático, não executa em cada evento)
- [ ] Revisar outros pontos de `asyncio.create_task` sem DLQ (grep `create_task` em `backend/` + auditoria manual)

---

## Métricas

### Baseline (2026-04-10)

| Métrica | Valor |
|---|---|
| Issues Sentry unresolved (14d) | 69 |
| Issues Escalating | 3 |
| Issues Regressed | 2 |
| Total eventos 14d | ~900 |
| Error rate backend | >1% |
| Slow requests >60s | 6+ |
| Schema contract violations | Ativo (Fatal) |
| Trial emails perdidos | ~23 |
| Checkout quebrado | 2 dias |

### Target (após deploy + observação 48h)

| Métrica | Target |
|---|---|
| Issues Sentry Escalating | 0 |
| Issues Regressed | 0 |
| Total eventos 14d | <100 |
| Error rate backend | <0.1% |
| Slow requests >60s | 0 |
| Schema contract violations | 0 |
| Trial emails perdidos | 0 (DLQ reprocessa) |
| Checkout trial → pro | conversão normalizada |

---

## Referências

- [EPIC-INCIDENT-2026-04-10](../stories/2026-04/EPIC-INCIDENT-2026-04-10.md)
- [Relatório consolidado Sentry/Railway](../reports/sentry-railway-errors-2026-04-10.md)
- [Runbook Sentry triage](../runbook/sentry-triage.md) (novo)
- [Runbook Supabase circuit breaker](../runbook/supabase-circuit-breaker.md)
- [Runbook Trial email pipeline](../runbook/trial-email-pipeline.md)
- [Alerting runbook](../operations/alerting-runbook.md)
- Sentry dashboard: https://confenge.sentry.io/issues/?query=is%3Aunresolved&statsPeriod=14d
