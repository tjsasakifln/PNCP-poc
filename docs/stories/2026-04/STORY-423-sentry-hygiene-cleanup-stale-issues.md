# STORY-423: Sentry Hygiene — Cleanup de Issues Stale + Triagem

**Priority:** P2 — Medium (backlog poluído dificulta triagem futura)
**Effort:** S (0.5-1 day)
**Squad:** @devops
**Status:** InReview
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sprint:** Sprint rotina (1w-2w)

---

## Contexto

A análise de 2026-04-10 identificou 69 issues ativos no Sentry `confenge` em janela de 14 dias. Parte desses já foram **corrigidos no código** mas permanecem marcados como `unresolved` no Sentry, poluindo a visualização e dificultando triagem futura. Além disso, há ~19 issues de baixo volume (1 evento) que precisam triagem manual — linkar com story existente ou fechar como flakes conhecidas.

**Issues já resolvidas no código (só precisam ser marcadas como Resolved no Sentry):**
- **7401546943** — `Error: You cannot use different slug names for the same dynamic path ('setor' !== 'cnpj')` — corrigido no commit `40bf4968`

**Issues de baixo volume para triagem:**
- Single-event errors em páginas 2 e 3 do Sentry (ver `docs/reports/sentry-railway-errors-2026-04-10.md`)
- Inclui: DimensionItem Pydantic validation, BadRequestError OpenAI, pipeline RLS 42501, check constraint `chk_search_sessions_error_code`, JSON could not be generated 400, etc.

**Issues operacionais identificadas mas sem story dedicada:**
- **RemoteProtocolError: Server disconnected** (5 eventos, 2-6 dias) — provavelmente retry automático de httpx, precisa investigar se é falso positivo
- Health incident `unhealthy` (1 evento) — one-off que pode ser lógico ignorar

---

## Acceptance Criteria

### AC1: Marcar issues já corrigidas como Resolved
- [ ] Acessar https://confenge.sentry.io e marcar como Resolved:
  - [ ] Issue 7401546943 (slug conflict) — commit `40bf4968` fechou
- [ ] Documentar no runbook que "slug conflict" foi resolvido — se recorrer, abrir nova investigação

### AC2: Triagem dos 19 issues de página 3 (Sentry backend, 14d)
- [ ] Para cada issue de single-event:
  - [ ] Ler mensagem e stacktrace
  - [ ] Decisão:
    - **(a) Duplicate** — linkar com outra issue principal, marcar como duplicate
    - **(b) Cover by story** — adicionar issue ID no campo "Linked Issues" da story relevante (ex: DimensionItem pode ir para STORY-414 se for schema drift)
    - **(c) Won't fix (known flake)** — marcar como Ignored com justificativa
    - **(d) Needs new story** — criar mini-story P3 se não couber em story existente
- [ ] Produzir relatório consolidado em `docs/runbook/sentry-triage.md` listando cada decisão

### AC3: Runbook de triagem semanal
- [ ] Criar `docs/runbook/sentry-triage.md` com:
  - Processo step-by-step de triagem semanal (toda sexta, 30 min)
  - Tabela de decisão (quando marcar Resolved vs Ignored vs New Story)
  - Template de comentário no Sentry quando linking com story
  - Meta: máximo 20 issues unresolved em janela de 30 dias
- [ ] Adicionar ao calendário de cerimônias do squad

### AC4: Sentry Alert Rules — elevar sinal

**Pré-requisito (@pm 2026-04-10 — Dia 0):**
- [ ] **Criar canal Slack `#incident-response`** antes de qualquer outra ação de AC4
- [ ] **Criar canal Slack `#sentry-new-issues`**
- [ ] Webhook URL em env var `SENTRY_SLACK_WEBHOOK` — **NUNCA commitar no repo**
- [ ] **Fallback email** se Slack indisponível: `tiago.sasaki@gmail.com`
- [ ] Se workspace Slack não existir, avaliar alternativa: Discord (grátis) ou trial Slack

**Alert rules no Sentry:**
- [ ] Criar alert rule: **"Fatal or Escalating"**
  - [ ] Condição: `level:fatal OR status:escalating`
  - [ ] Notificação: imediata (não agregada)
  - [ ] Canal: Slack #incident-response + email tiago.sasaki@gmail.com
- [ ] Criar alert rule: **"Any issue with >100 events in 1h"**
  - [ ] Early warning de burst
- [ ] Criar alert rule: **"New issue in production"**
  - [ ] Agregado a cada 15 min para não spammar
  - [ ] Canal: Slack #sentry-new-issues
- [ ] Documentar em `docs/operations/alerting-runbook.md`

### AC5: Investigar RemoteProtocolError
- [ ] Analisar Sentry issues com "RemoteProtocolError: Server disconnected" (7396815149, 7396815134, 7396815122, 7387730654)
- [ ] Stacktrace deve indicar qual endpoint/client (Stripe? PNCP? BrasilAPI?)
- [ ] Decisão:
  - Se é retry automático de httpx que eventualmente sucede → marcar como Ignored
  - Se é erro propagado ao usuário → criar STORY-424 dedicada
- [ ] Documentar decisão

### AC6: Verificação
- [ ] Após execução da triagem, contar issues ativas: `curl https://confenge.sentry.io/api/.../issues?query=is:unresolved` deve retornar **<30** (era 69)
- [ ] Screenshot do dashboard Sentry antes/depois em `docs/runbook/sentry-triage.md`
- [ ] Compartilhar com squad no próximo standup

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `docs/runbook/sentry-triage.md` | **Novo runbook** |
| `docs/operations/alerting-runbook.md` | Documentar novas alert rules |
| Sentry dashboard (externo) | Marcar issues Resolved/Ignored, criar alert rules |

---

## Implementation Notes

- **Esta story é principalmente operacional — pouco código.** Maior parte é clicking no Sentry dashboard.
- **@devops exclusive:** @devops é o owner de MCP management e alerts — essa story é naturalmente dele.
- **Não commitar credentials:** alert rules podem ter webhooks Slack — NÃO commitar URLs de webhook no repo.
- **Priorizar AC4 (alerts):** ter alerts ativos antes do próximo incidente é mais valioso que limpar backlog histórico. Se bandwidth apertar, fazer AC4 primeiro.
- **Integration com Slack:** verificar se workspace Slack tem canal `#incident-response`. Se não, criar primeiro.
- **Meta de longo prazo:** atingir <20 issues unresolved em janela de 30 dias e manter assim.

---

## Dev Notes (preencher durante implementação)

<!-- @devops: listar quantas issues foram triadas em cada categoria (Resolved/Duplicate/Ignored/New Story) -->

---

## Verification

1. **Sentry dashboard:** abrir filter `is:unresolved statsPeriod:14d` → contagem <30
2. **Alert teste:** simular evento fatal em staging → alert dispara em <2 min no canal Slack
3. **Runbook:** rodar triagem seguindo runbook → processo completo em <30 min
4. **Slug issue:** issue 7401546943 aparece como Resolved com commit linkado

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
| 2026-04-10 | @po (Sarah) | `*validate-story-draft` → verdict GO (8.5/10). Status Draft → Ready. |
| 2026-04-10 | @pm (Morgan) | Decisão AC4: criar canais Slack `#incident-response` + `#sentry-new-issues` **como pré-requisito Dia 0** antes de configurar alert rules. Fallback: email para `tiago.sasaki@gmail.com` se Slack indisponível. Webhook em env var, nunca no repo. |
| 2026-04-11 | @dev (YOLO P2 sprint) | Parte automatizável entregue: `docs/runbook/sentry-triage.md` novo — runbook semanal 30min com processo 4 passos, tabela de decisão (Resolved/Ignored/Linked/New/Escalate), templates de comentário, critérios de escalação P0, playbooks específicos (issue resolvido mas unresolved / ruidoso / single-event), snapshots tracking. `docs/operations/alerting-runbook.md` estendido com seção 1.2b (3 alert rules novas: Fatal/Escalating imediato, Burst >100/h, New issue prod agregado 15min) + checklist pré-deploy + setup manual Sentry UI. AC1/AC2/AC5/AC6 (ações no Sentry UI externo) e criação de canais Slack permanecem como follow-up operacional @devops documentado no runbook. Status Ready → InReview aguardando execução @devops.<br>**File List:** `docs/runbook/sentry-triage.md`, `docs/operations/alerting-runbook.md` |
