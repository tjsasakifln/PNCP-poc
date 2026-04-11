# Runbook — Sentry Triage Semanal

**Owner:** @devops (backup: @dev on-call)
**Cadence:** Toda sexta-feira, 15h BRT, 30 min
**Last updated:** 2026-04-10 (STORY-423)
**Origin:** EPIC-INCIDENT-2026-04-10 — dashboard Sentry acumulou 69 issues
unresolved em 14 dias, vários já corrigidos no código mas não marcados,
poluindo a triagem e escondendo regressões reais.

## Por que existe este runbook

O Sentry não fecha automaticamente issues quando o código é corrigido.
Sem uma rotina explícita de triagem, o dashboard vira um cemitério:
- Erros já resolvidos continuam aparecendo como "unresolved", confundindo
  quem está de plantão.
- Regressões novas ficam invisíveis no meio do backlog antigo.
- Single-event issues acumulam sem análise, virando ruído estrutural.
- Alert rules (STORY-423 AC4) ficam fatigadas e são ignoradas.

**Meta:** manter `unresolved_count < 20` em janela de 30 dias,
`escalating_count == 0` fora de incidentes ativos.

## Pré-requisitos

- Acesso ao org `confenge` no Sentry com role `Member` ou superior
- Canais Slack `#incident-response` + `#sentry-new-issues` criados
  (ver `docs/operations/alerting-runbook.md` seção STORY-423)
- Link direto do dashboard: https://confenge.sentry.io/issues/?query=is%3Aunresolved&statsPeriod=14d

## Processo (30 min)

### Passo 1 — Snapshot (3 min)

Abrir o dashboard com query `is:unresolved age:-14d` e anotar:
- `unresolved_count` (total)
- `escalating_count` (issues em `Escalating`)
- `new_issue_count` (criadas na última semana)
- `top_event_count` (evento mais ruidoso)

Registrar snapshot no fim deste runbook (seção "Snapshots") ou em uma
issue do Linear/GitHub dedicada ao ciclo.

### Passo 2 — Classificar cada issue (20 min)

Para cada issue, escolher **uma** das decisões:

| Decisão | Quando usar | Ação no Sentry UI |
|---|---|---|
| **Resolved** | O código foi corrigido (localizar commit / PR) | `Resolve` + comentário com hash/PR |
| **Ignored** | Known flake, erro de terceiros, comportamento esperado | `Ignore` → `Until this issue affects more users` + comentário justificando |
| **Linked to story** | Coberto por story existente (em Ready/InProgress/InReview) | Adicionar link para a story no comentário + `Ignore until next release` |
| **New mini-story** | Regressão nova não coberta por story existente | Criar story P2/P3 em `docs/stories/{ano-mes}/`, linkar no comentário |
| **Escalate P0** | >5 eventos/dia em produção, severity `fatal`, afeta revenue | Chamar `#incident-response` + seguir `docs/runbook/incident-response.md` |

### Passo 3 — Template de comentário Sentry

Use sempre o mesmo formato para facilitar busca futura:

```
[Triage YYYY-MM-DD] @devops
Decision: resolved | ignored | linked | new-story | escalated
Ref: <commit-hash> | <story-id> | <PR-link>
Notes: <1-2 linhas explicando>
```

### Passo 4 — Atualizar métricas (5 min)

Registrar na tabela "Snapshots" abaixo:
- Quantos issues transitaram `unresolved → resolved`
- Quantos `ignored`
- Quantos viraram `new-story`
- Quantos escalados

Compartilhar no standup da segunda seguinte o delta semana-a-semana.

## Critérios de escalação P0

Escalar imediatamente (sem esperar a sexta) se:

- Issue em estado `Escalating` por >2h
- >50 eventos em 1h de um mesmo issue em produção
- `fatal` severity afetando checkout, auth ou search
- Qualquer erro com stack trace em `webhooks/stripe.py`, `auth.py`, `quota.py`

Em todos os casos, abrir incident em `#incident-response` com o link do
issue e seguir `docs/runbook/incident-response.md`.

## Anti-padrões (não fazer)

- **Ignorar sem comentário** — perde o contexto para o próximo de plantão.
- **Resolver sem verificar o código** — se o fix não está no main, o issue
  volta no próximo deploy.
- **Marcar batch de issues sem ler** — invalida a triagem; melhor deixar
  para a semana seguinte do que fazer mal.
- **Criar story para cada single-event** — só vale a pena se o erro tem
  impacto visível ou é reprodutível.

## Playbooks específicos

### "Issue X já corrigido mas ainda unresolved"

1. `git log --all --oneline | grep <issue-keyword>` para achar o commit do fix.
2. Confirmar que o commit está em `main` e foi deployado (`railway status`).
3. Marcar Resolved com o template acima.
4. Se reaparecer: é regressão — criar story P0/P1 e reverter o triage.

### "Issue ruidoso com >100 eventos/dia"

1. Checar se é um alert rule desligado (STORY-423 AC4) — se sim, reativar.
2. Ver se o issue tem `tag:close_reason USER_CANCELLED` ou similar —
   provavelmente é ruído que o `beforeSend` filter deveria pegar. Abrir
   story para estender o filter em `frontend/sentry.client.config.ts`.
3. Caso contrário, escalar P0.

### "Single-event issue sem contexto"

1. Se tem stack trace útil → criar story de investigação.
2. Se é `Error: <undefined>` ou similar sem contexto → `Ignore until
   affects more users` com comentário "insufficient context".

## Relação com outras rotinas

- **Alert rules** (STORY-423 AC4): ver `docs/operations/alerting-runbook.md`
  para setup de Slack webhooks.
- **Incident response**: ver `docs/runbook/incident-response.md` para
  escalações fora da cadência semanal.
- **Close_reason filter** (STORY-422): `frontend/sentry.client.config.ts`
  — mantém ruído de cancelamento de busca fora do dashboard.
- **Trial email DLQ** (STORY-418): issues com `STORY-418: trial_email_dlq`
  são auto-reprocessadas; não criar story até verificar `trial_email_dlq`
  tabela antes.

## Snapshots

Registrar cada ciclo de triagem aqui (manter últimos 8 ciclos):

| Data | unresolved | escalating | resolved no ciclo | ignored | new stories | escalados |
|---|---|---|---|---|---|---|
| 2026-04-10 (baseline) | 69 | 3 | — | — | — | — |

## Change log

| Data | Autor | Mudança |
|---|---|---|
| 2026-04-10 | @dev (STORY-423) | Runbook criado a partir do EPIC-INCIDENT-2026-04-10 |
