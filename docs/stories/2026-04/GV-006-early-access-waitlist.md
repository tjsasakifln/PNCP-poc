# GV-006: Early Access Waitlist para Features Premium

**Priority:** P1
**Effort:** M (8 SP, 4-5 dias)
**Squad:** @dev + @pm + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 2

---

## Contexto

Manus viralizou com **waitlist scarcity + invite codes** — 500k+ signups orgânicos com invite codes vendidos em mercado secundário. O mecanismo gera FOMO + capture lead antes mesmo do produto existir.

SmartLic tem 3 features premium no horizonte que podem servir de anchor para waitlist:
1. **API B2B pública** (EPIC-MON-API-2026-04 Wave 4)
2. **Inteligência IA Setorial GPT-5** (uplift para GPT-5 quando release)
3. **Radar ML de Padrões** (detecção de prefeituras/órgãos com comportamento recorrente — futuro)

Waitlist serve dois propósitos:
- Capture leads mesmo pré-feature (engagement + atribuição)
- Valida demand real antes de investir em build completo

---

## Acceptance Criteria

### AC1: Landing page `/early-access`

- [ ] `frontend/app/early-access/page.tsx`:
  - Hero com 3 features premium (cards):
    - API B2B: "Integre SmartLic ao seu ERP — acesso direto aos dados"
    - Intel IA Setorial: "Análise setorial profunda com GPT-5"
    - Radar ML: "Detecte padrões em órgãos antes dos concorrentes"
  - User escolhe qual feature quer early access (multi-select ok)
  - Form: email + CNPJ + use case (3 lines)
  - Live counter: "X pessoas na fila | Y convites liberados esta semana" (WebSocket ou poll 60s)
  - Social proof: "Último aprovado: empresa do setor {X} há {Y}h"

### AC2: Tabela + endpoint waitlist

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_waitlist.sql`:
  ```sql
  CREATE TABLE waitlist_signups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    cnpj TEXT,
    use_case TEXT,
    features_interested TEXT[],  -- ['api_b2b', 'intel_ia', 'radar_ml']
    position INTEGER,
    invited BOOLEAN DEFAULT FALSE,
    invite_code TEXT UNIQUE,
    invite_code_used BOOLEAN DEFAULT FALSE,
    invited_at TIMESTAMPTZ,
    share_credits_earned INTEGER DEFAULT 0,
    referrer_email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(email, features_interested)
  );
  CREATE INDEX idx_waitlist_features ON waitlist_signups USING GIN (features_interested);
  ```
  Down migration obrigatório.
- [ ] Endpoints `backend/routes/waitlist.py`:
  - `POST /v1/waitlist/join` — valida + calcula posição + envia email confirmação
  - `GET /v1/waitlist/position?email=X` — retorna posição atual + features
  - `POST /v1/waitlist/redeem` — aceita invite code, converte waitlist em trial

### AC3: "Share to skip positions" mechanic

- [ ] Após signup waitlist, user recebe link `/waitlist/{email_hash}`:
  - Mostra "Você está na posição #1234"
  - Botão "Avance 10 posições — indique 1 colega" → gera link único `/early-access?ref={email_hash}`
  - Cada referral validated (email real + não-duplicado) = -10 posições
  - Max -100 posições via referrals (evita gaming)
- [ ] Social buttons pré-configured LinkedIn/WhatsApp/Twitter

### AC4: Admin aprovação batch

- [ ] `frontend/app/admin/waitlist/page.tsx` (admin only):
  - Tabela filterable por feature, CNPJ verificado, posição, data
  - Checkbox multi-select + "Aprovar N selecionados" button
  - Approve action:
    - Gera invite code único (random 12 chars)
    - Envia email "Você foi aprovado!" com código
    - Update `invited=true, invited_at=NOW()`
- [ ] CLI fallback `backend/scripts/approve_waitlist.py` para admin operations

### AC5: Invite code redemption

- [ ] `/early-access/redeem?code=X`:
  - Valida código (não usado, não expirado)
  - Se válido: inicia signup flow normal + atribui `feature_early_access = ['feature_id']` no profile
  - Se inválido: mensagem de erro + volta para waitlist
- [ ] Invite code expira 7 dias após generated

### AC6: Email transacional

- [ ] `backend/templates/emails/waitlist_confirmation.html`:
  - "Você está na posição #N"
  - Link para compartilhar e avançar
- [ ] `backend/templates/emails/waitlist_approved.html`:
  - "Você foi aprovado! Aqui está seu invite code: {code}"
  - CTA "Resgatar agora" → `/early-access/redeem?code=X`
  - Countdown 7 dias

### AC7: Live counter

- [ ] `frontend/components/WaitlistCounter.tsx`:
  - Poll `/v1/waitlist/stats` cada 60s
  - Retorna: `total_waiting`, `invites_released_this_week`, `last_approved_sector` + `last_approved_hours_ago`
  - Animação smooth count-up

### AC8: Testes

- [ ] Unit `backend/tests/test_waitlist.py`
- [ ] Integration `test_waitlist_rate_limit.py`
- [ ] E2E Playwright: join → receive position → share → validate position update → admin approve → redeem

---

## Scope

**IN:**
- Landing page + form
- Tabela + endpoints
- Share-to-skip mechanic
- Admin UI aprovação
- Email transacional
- Live counter

**OUT:**
- Pagamento para "pular fila" — v2 (controverso)
- Waitlist para features non-premium (core features acesso total sempre) — não aplicável
- Gamification leaderboard público — v2 (privacy B2G)

---

## Dependências

- **Nenhuma** — story independente
- Integração futura com EPIC-MON-API quando API B2B virar GA

---

## Riscos

- **Waitlist vazio (zero engagement):** mitigação — pré-validar com 5 customers entrevistados antes de build; considerar landing MVP sem backend se feedback fraco
- **Feature premium prometida nunca entrega:** expectativa management — email aprovação deixa claro "beta, features em desenvolvimento"; opção de opt-out 1-click
- **Abuse de referrals:** detection padrões (mesmo user várias contas) + CAPTCHA leve no `/early-access`

---

## Arquivos Impactados

### Novos
- `frontend/app/early-access/page.tsx`
- `frontend/app/early-access/redeem/page.tsx`
- `frontend/app/admin/waitlist/page.tsx`
- `frontend/components/WaitlistCounter.tsx`
- `backend/routes/waitlist.py`
- `backend/scripts/approve_waitlist.py`
- `backend/templates/emails/waitlist_confirmation.html`
- `backend/templates/emails/waitlist_approved.html`
- `supabase/migrations/YYYYMMDDHHMMSS_waitlist.sql` (+ down)
- `backend/tests/test_waitlist.py`

### Modificados
- `frontend/app/page.tsx` (adicionar link "Early Access" no footer)
- `frontend/app/sitemap.ts` (incluir `/early-access`)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — Manus-inspired waitlist mechanic adaptado B2G; anchor em 3 features EPIC-MON-API futuras |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
