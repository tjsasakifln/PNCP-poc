# GV-009: "Licitação do Dia" — Daily Personalized Matching

**Priority:** P1
**Effort:** M (8 SP, 4 dias)
**Squad:** @dev + @data-engineer
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 2

---

## Contexto

Duolingo viralizou via streak (habit formation). Adaptação B2G: cada dia user recebe **1 licitação ultra-compatível** no email + push → abre → vê → age. Streak de dias consecutivos cria hábito + retenção + FOMO.

**Diferença vs STORY-321 (Done, Email Sequence Trial 14d):**
- 321 = sequência trial fixa (8 emails em datas específicas D0/3/7/14/21/25/29/32, copy estático)
- GV-009 = ongoing daily (trial + paid) com edital escolhido por matching algo (score ≥80 + setor + UF do user)
- Copy dinâmica por edital específico

---

## Acceptance Criteria

### AC1: Matching algorithm

- [ ] `backend/services/daily_edital_matcher.py`:
  - Para cada user ativo (trial + paid):
    - Query `search_datalake` com filtros do profile (UFs, setores, valor range)
    - Rank por viability score (desc) + recency (últimas 48h upweight)
    - Retorna top 1 edital
    - Fallback: se nenhum edital score ≥80 achado, retorna top edital score ≥60 com aviso "opção secundária"
  - Dedup: não enviar mesmo edital 2x pro mesmo user em 30 dias

### AC2: ARQ cron job

- [ ] `backend/jobs/cron/daily_edital.py`:
  - Trigger 9h BRT (12h UTC) — "@arq.cron(hour=12, minute=0)"
  - Itera users com `alert_preferences.daily_edital_enabled=true`
  - Calls matcher + sends email + push
  - Metrics: `smartlic_daily_edital_sent_total{status}` (sent/skipped/error)

### AC3: Email template

- [ ] `backend/templates/emails/licitacao_do_dia.html`:
  - Header: "🎯 Sua licitação do dia — {data}"
  - Hero card: título edital, órgão, valor, UF, modalidade, prazo
  - Viability score + breakdown 4 fatores (visual)
  - 2 CTAs: "Ver análise completa" (→ /buscar?preselect={id}) + "Adicionar ao pipeline"
  - Streak badge: "🔥 {N}º dia consecutivo"
  - Footer: ajustes de preferência + unsubscribe
- [ ] Fallback texto para clients que não renderizam HTML

### AC4: Push notification (web)

- [ ] `frontend/lib/push.ts` estende com `sendDailyEdital(user, edital)`:
  - Web Push API via service worker (se user opted-in)
  - Payload: título + valor + UF + link direto
  - Click abre `/buscar?preselect={id}` com contexto pre-loaded

### AC5: Streak tracking

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_user_streaks.sql`:
  ```sql
  CREATE TABLE user_streaks (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_open_at TIMESTAMPTZ,
    streak_type TEXT DEFAULT 'daily_edital',
    updated_at TIMESTAMPTZ DEFAULT NOW()
  );
  ALTER TABLE user_streaks ENABLE ROW LEVEL SECURITY;
  ```
  Down obrigatório.
- [ ] Email open (via Resend webhook) → incrementa streak
- [ ] Gap >24h resets streak (gentle break)
- [ ] Streak visível em `/dashboard` (componente `StreakBadge`)

### AC6: Preferências user

- [ ] `frontend/app/alerts/page.tsx` (existente) adiciona toggle:
  - "Receber Licitação do Dia (daily)" — default ON para novos trials, OFF opt-in para existentes
  - Horário preferido (select: 8h / 9h / 10h / 14h / 18h)
  - Pause 7 dias (vacation mode)

### AC7: Break streak win-back

- [ ] Se streak quebra (day +3 sem abrir email):
  - Trigger `backend/jobs/cron/streak_break_reactivation.py`
  - Email especial: "Sua série de {N} dias parou — retome hoje" com CTA
  - Rate limit 1 win-back por quebra

### AC8: Testes

- [ ] Unit matcher (edge: zero licitações, all score <60)
- [ ] Integration cron job end-to-end
- [ ] E2E Playwright: streak increments on email open (mock webhook)
- [ ] Load test: matcher <2s per user (alvo 10k users processados em <20min)

---

## Scope

**IN:**
- Matcher algorithm
- Cron daily
- Email + push
- Streak tracking
- User preferences
- Break win-back

**OUT:**
- Multi-licitação/dia (1 focal suficiente) — v2
- SMS delivery (email + push cobre) — v2
- Streak leaderboard público (privacy B2G) — rejeitado
- Push iOS native (web push suficiente por ora) — v2

---

## Dependências

- **STORY-321** (Done) — não sobrepõe, mas user lê preferências semelhantes
- ARQ job queue existente
- `alert_preferences` tabela existente

---

## Riscos

- **Email fatigue:** 1/dia é limite confortável. Rate limit rígido. Unsubscribe 1-click.
- **Matcher latency em peak:** 10k users × 2s = 20min window — OK para cron, mas monitor p95
- **Streak perdida por bug (não por user):** audit log + retry graceful; se servidor falha, não punir user (streak preservada)

---

## Arquivos Impactados

### Novos
- `backend/services/daily_edital_matcher.py`
- `backend/jobs/cron/daily_edital.py`
- `backend/jobs/cron/streak_break_reactivation.py`
- `backend/templates/emails/licitacao_do_dia.html`
- `backend/templates/emails/streak_break_reactivation.html`
- `frontend/components/StreakBadge.tsx`
- `frontend/lib/push.ts`
- `supabase/migrations/YYYYMMDDHHMMSS_user_streaks.sql` (+ down)
- `backend/tests/test_daily_edital_matcher.py`

### Modificados
- `frontend/app/alerts/page.tsx` (adiciona toggle daily)
- `frontend/app/dashboard/page.tsx` (mostra StreakBadge)
- `backend/webhooks/resend.py` (captura email_opened → streak update)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — Duolingo streak adaptado B2G; complementa STORY-321 sem sobrepor |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
