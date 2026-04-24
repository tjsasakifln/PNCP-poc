# GV-014: Consultoria → Cliente Read-Only Dashboard

**Priority:** P1
**Effort:** L (13 SP, 6-8 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready (conditional — commercial gate)
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 3
**Pré-requisito comercial:** validar se plano Consultoria R$997/mês tem ≥3 users pagantes ativos (consultar `plan_billing_periods` + Stripe). Se zero → deprioritizar.

---

## Contexto

Consultorias/assessorias são 30% do target SmartLic. Pain point: entregar relatórios manualmente ao cliente final é trabalho repetitivo.

Solução viral: consultor compartilha dashboard read-only com seu cliente. Cliente vê oportunidades filtradas + análises preparadas pela consultoria + watermark SmartLic + CTA "Tenha sua própria análise". Cada cliente vê o produto em contexto real = high-intent signup potential.

Esta é a **alavanca viral mais forte** do epic para segmento consultoria (5 clientes por consultor × 10 consultorias = 50 exposições diretas por mês).

---

## Acceptance Criteria

### AC1: Gate comercial

- [ ] Feature flag `CONSULTORIA_CLIENT_SHARE_ENABLED` default OFF
- [ ] Skill `@analyst` valida: há ≥3 consultorias pagantes? Se não, story sai para v2.
- [ ] Se validado: feature ativa só para users com `plan_type IN ('consultoria_monthly', 'consultoria_semiannual', 'consultoria_annual')`

### AC2: Tabela client shares

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_consultoria_client_shares.sql`:
  ```sql
  CREATE TABLE consultoria_client_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultor_id UUID REFERENCES auth.users(id),
    client_email TEXT NOT NULL,
    client_name TEXT,
    client_cnpj TEXT,
    access_token TEXT UNIQUE NOT NULL,
    filters JSONB,  -- setores, UFs, valor_range específicos deste cliente
    read_only BOOLEAN DEFAULT TRUE,
    history_days_limit INTEGER DEFAULT 30,
    status TEXT DEFAULT 'active',  -- 'active' | 'paused' | 'revoked'
    last_accessed_at TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  ALTER TABLE consultoria_client_shares ENABLE ROW LEVEL SECURITY;
  ```

### AC3: UI consultor — gerenciar clientes

- [ ] `frontend/app/consultoria/clientes/page.tsx`:
  - Lista clientes (cards): nome, email, CNPJ, status, última visita, # acessos
  - Botão "Adicionar cliente" → form (nome, email, CNPJ, setores, UFs, valor range)
  - Actions: compartilhar link, pausar acesso, revogar
  - Branding config: logo consultoria, cor primária (co-brand permitido)

### AC4: Dashboard read-only cliente

- [ ] `frontend/app/consultoria/cliente/[token]/page.tsx`:
  - Sem auth user — access via token unique
  - Header: logo consultoria + pequeno "powered by SmartLic" (obrigatório, não removível)
  - Oportunidades filtradas pelos settings do consultor
  - Viability scores visíveis
  - Read-only: não pode adicionar ao pipeline, não pode exportar
  - CTA destacado bottom: "Tenha sua própria conta SmartLic — análises ilimitadas" → `/signup?source=consultoria_share&partner={consultor_id}`
  - Tracking: `access_count` + `last_accessed_at` incrementa em cada view

### AC5: Magic link auth para cliente

- [ ] Client recebe email com `/consultoria/cliente/[token]` (token em URL)
- [ ] Sessão temporária 30 dias (cookie httpOnly), refresh automático em acesso
- [ ] Revoke imediato via consultor dashboard → token invalidated

### AC6: Email template

- [ ] `backend/templates/emails/consultoria_client_invite.html`:
  - "Sua consultoria {nome_consultoria} preparou um dashboard de oportunidades para você"
  - CTA "Acessar dashboard" → magic link
  - Branding co-brand (logo consultoria + SmartLic small)

### AC7: Analytics para consultor

- [ ] `frontend/app/consultoria/analytics/page.tsx`:
  - Por cliente: # acessos, últimas visitas, licitações mais vistas
  - Summary: total clients, total access events semanais

### AC8: LGPD compliance

- [ ] Termos de uso específicos cliente (consent expresso ao aceitar magic link)
- [ ] Consultor responsável por consentimento do cliente (disclaimer no dashboard consultor)
- [ ] Data retention: acessos guardados 90 dias

### AC9: Testes

- [ ] Unit RLS (consultor A não vê clients de B)
- [ ] Integration magic link flow
- [ ] E2E Playwright: consultor add client → cliente recebe email → abre link → vê dashboard → clica "tenha própria conta" → signup attribution correto

---

## Scope

**IN:**
- Gate comercial pre-check
- Tabela + RLS
- UI consultor gerenciar
- Dashboard read-only cliente
- Magic link auth
- Analytics consultor
- LGPD terms

**OUT:**
- White-label total (domain próprio) — v3 enterprise
- Cliente poder comentar/interagir (só read-only) — v2
- Cliente ter próprio pipeline dentro do share (v2)
- Billing split consultor/cliente — v3

---

## Dependências

- **Validação comercial** — ≥3 consultorias pagantes
- **GV-013** (workspace infra) — reusar conceito de membership
- **GV-002** (watermark) — dashboard cliente usa

---

## Riscos

- **Segurança magic link:** tokens longos (32+ chars), httpOnly, expire 30d; revoke instant
- **Consultor vê dados cruzados de clientes:** RLS rigoroso — consultor_id isolation
- **Cliente final vendo dados de outros clientes da mesma consultoria:** filter strict por token
- **LGPD — consentimento do cliente não-user:** consultor atesta no contrato que tem consentimento; SmartLic não pode ser responsabilizado em B2B2C

---

## Arquivos Impactados

### Novos
- `frontend/app/consultoria/clientes/page.tsx`
- `frontend/app/consultoria/cliente/[token]/page.tsx`
- `frontend/app/consultoria/analytics/page.tsx`
- `backend/routes/consultoria_shares.py`
- `backend/templates/emails/consultoria_client_invite.html`
- `frontend/components/SharedDashboardBranding.tsx`
- `supabase/migrations/YYYYMMDDHHMMSS_consultoria_client_shares.sql` (+ down)
- `backend/tests/test_consultoria_shares.py`

### Modificados
- `frontend/app/planos/page.tsx` (destacar feature na descrição do plano Consultoria)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — viral loop segmento consultoria; gate comercial 3+ pagantes antes de build |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO conditional**. Antes Sprint 3 start: @analyst valida ≥3 consultorias pagantes; se falhar → deprioritizar para v2. Status Draft → Ready (conditional). |
