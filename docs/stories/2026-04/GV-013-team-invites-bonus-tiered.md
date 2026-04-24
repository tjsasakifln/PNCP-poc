# GV-013: Team Invites com Workspace + Bonus Tiered

**Priority:** P1
**Effort:** M (8 SP, 4-5 dias)
**Squad:** @dev + @data-engineer
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 2

---

## Contexto

Figma/Slack/Linear viralizaram via collaboration-driven loops — "convide sua equipe" é CTA nativo. Cada invite = signup pospotencial + product inherent value increases.

SmartLic hoje não tem workspace multi-user. Cada user opera silo. Esta story cria workspace compartilhado (pipeline + análises shared) + bonus tiered pro inviter.

Objetivo B2G: empresa B2G típica tem 2-5 stakeholders (CEO + diretor comercial + consultor jurídico + analista licitação). Viralidade intra-empresa = maior payoff que inter-empresa.

---

## Acceptance Criteria

### AC1: Tabelas workspace

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_workspaces.sql`:
  ```sql
  CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    owner_id UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
  );

  CREATE TABLE workspace_members (
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id),
    role TEXT DEFAULT 'member',  -- 'owner' | 'admin' | 'member' | 'viewer'
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    invited_by UUID REFERENCES auth.users(id),
    PRIMARY KEY (workspace_id, user_id)
  );

  CREATE TABLE workspace_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id),
    email TEXT NOT NULL,
    role TEXT DEFAULT 'member',
    token TEXT UNIQUE NOT NULL,
    invited_by UUID REFERENCES auth.users(id),
    status TEXT DEFAULT 'pending',  -- 'pending' | 'accepted' | 'revoked'
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    accepted_user_id UUID REFERENCES auth.users(id)
  );

  ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
  ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
  ALTER TABLE workspace_invites ENABLE ROW LEVEL SECURITY;
  ```
- [ ] RLS policies: member só acessa workspaces que pertence; owner pode invitar/remover

### AC2: Auto-create workspace on signup

- [ ] Trigger backend: quando user signup, criar workspace default "{Nome} Workspace" com user como owner
- [ ] Backfill job para users existentes (um-shot, seguro idempotente)

### AC3: UI team management

- [ ] `frontend/app/settings/team/page.tsx`:
  - Lista members atuais (nome, email, role, joined)
  - Botão "Convidar" abre modal:
    - Email (required)
    - Role select (member/admin/viewer)
    - Mensagem personal (optional)
  - Revoke invite / remove member actions (gated por role)

### AC4: Endpoint invite + email

- [ ] `backend/routes/team.py`:
  - POST `/v1/workspaces/{id}/invite` — cria token único + envia email
  - POST `/v1/workspaces/accept-invite` — aceita invite via token → cria user se new
- [ ] `backend/templates/emails/workspace_invite.html`:
  - "{inviter} te convidou para workspace {name} no SmartLic"
  - CTA "Aceitar convite" → `/signup?invite={token}` (pre-fill email)

### AC5: Bonus tiered (inviter reward)

- [ ] `backend/services/team_rewards.py`:
  - 1 invite aceito (novo signup) = +7d trial extend
  - 3 invites = +30d bônus adicional
  - 10 invites = cupom 50% primeiro mês anual (Stripe API create coupon)
- [ ] Reward aplicado on_signup (não on_invite, evita gaming)
- [ ] Dashboard "Meus convites": counter + progress bar para próxima tier

### AC6: Shared pipeline + análises

- [ ] Estender pipeline (`frontend/app/pipeline/page.tsx`):
  - Views: "Meus" / "Workspace" (toggle)
  - Items no workspace visíveis para todos members (respeitando role: viewer read-only)
  - Attribution: "adicionado por {nome}" em cada item

### AC7: Testes

- [ ] Unit RLS tests (workspace isolation)
- [ ] Integration invite flow end-to-end
- [ ] E2E Playwright: user A cria workspace → convida B → B recebe email → aceita → vê shared pipeline

---

## Scope

**IN:**
- Workspaces + members + invites
- Auto-create on signup
- UI team management
- Invite email
- Bonus tiered rewards
- Shared pipeline

**OUT:**
- Roles granulares (apenas 4: owner/admin/member/viewer)
- Workspace-level billing (v2 enterprise)
- Multi-workspace per user (v2)
- SSO/SAML (v3 enterprise)

---

## Dependências

- **Nenhuma** externa — story independente
- Blocker de GV-014 (Consultoria → Cliente usa workspace infra)

---

## Riscos

- **RLS gap expõe workspaces não-pertencidas:** teste rigoroso RLS com users diferentes
- **Gaming via self-invite:** detection (mesma origem IP, email similar) + CAPTCHA signup
- **Email deliverability:** SPF/DKIM já OK; monitor bounce
- **Migration retroativa:** workspace default para users existentes via job idempotente

---

## Arquivos Impactados

### Novos
- `frontend/app/settings/team/page.tsx`
- `backend/routes/team.py`
- `backend/services/team_rewards.py`
- `backend/templates/emails/workspace_invite.html`
- `supabase/migrations/YYYYMMDDHHMMSS_workspaces.sql` (+ down)
- `backend/scripts/backfill_workspaces.py`
- `backend/tests/test_workspaces_rls.py`

### Modificados
- `frontend/app/pipeline/page.tsx` (toggle Meus/Workspace)
- `backend/auth.py` (auto-create workspace on signup)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — Figma-style collaboration loop para virality intra-empresa B2G |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
