# GV-010: Badges + LinkedIn-Shareable Certificate

**Priority:** P2
**Effort:** M (8 SP, 4 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 3

---

## Contexto

LinkedIn tem cultura forte B2G (executivos postam "ganhei contrato X", "certificado Y"). SmartLic pode emitir badges/certificates com link shareable no LinkedIn → cada compartilhamento vira ad + social proof para peers.

Gamification mapeada em STORY-247 (TODO) mas nunca implementada. Esta story estende para CTA viral externo (não só engagement interno).

---

## Acceptance Criteria

### AC1: Sistema de badges

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_user_badges.sql`:
  ```sql
  CREATE TABLE user_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    badge_code TEXT NOT NULL,
    awarded_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(user_id, badge_code)
  );
  ```
- [ ] Badges implementados:
  - `explorer` — 10 análises completas
  - `strategist` — 50 análises + 3 itens no pipeline
  - `winner` — marca 1 licitação como "ganho"
  - `consistent` — streak 30 dias (GV-009)
  - `team_builder` — 5 referrals aceitos (integra GV-018)

### AC2: Trigger awarder

- [ ] `backend/services/badge_awarder.py`:
  - Event-driven: cada ação chave dispara check
  - Criteria avaliados via SQL queries simples
  - Email trigger unlock: "Parabéns! Você ganhou badge {name}"

### AC3: Dashboard user — progresso

- [ ] `frontend/app/dashboard/components/BadgeGallery.tsx`:
  - Grid todas badges disponíveis (earned + locked com progress)
  - Progress bar: "40/50 análises para badge Strategist"
  - Click abre modal com detalhes

### AC4: Certificate público shareable

- [ ] `frontend/app/certificados/[userId]/[badgeCode]/page.tsx`:
  - SSG + ISR
  - Layout certificate (border ornamental + brand)
  - "Certificamos que [nome_fantasia ou pseudonimizado] conquistou [Badge Name]"
  - Data + signature SmartLic
  - Pseudonimização default (apenas razão_social_mascara); opt-in nome real via settings
- [ ] OG image dinâmica `/certificados/[userId]/[badgeCode]/opengraph-image.tsx`:
  - Template badge + user name + data

### AC5: LinkedIn share integration

- [ ] Button "Compartilhar no LinkedIn" pré-configured:
  - URL: `https://www.linkedin.com/sharing/share-offsite/?url=https://smartlic.tech/certificados/{userId}/{badgeCode}`
  - Copy pre-filled incentiva text: "Alcancei o badge {name} no SmartLic — análise de licitações com IA"
- [ ] Fallback buttons: WhatsApp, Twitter, copy-link

### AC6: Tracking + attribution

- [ ] Mixpanel:
  - `badge_awarded` (por código)
  - `certificate_viewed_public` (quem visita `/certificados/*`)
  - `certificate_shared` (por canal)
- [ ] Signup via link certificate → attribution `source=certificate_linkedin`

### AC7: Testes

- [ ] Unit badge_awarder criteria
- [ ] Snapshot certificate page
- [ ] E2E Playwright: earn badge → visit certificate → share LinkedIn (mock) → OG image renders

---

## Scope

**IN:**
- Sistema badges + awarder
- Dashboard progresso
- Certificate público + OG
- Share LinkedIn

**OUT:**
- Badges customizáveis por user (v2)
- NFT-style uniqueness (overengineered)
- Gamification leaderboard público (privacy B2G)

---

## Dependências

- **GV-002** (pseudonimização) — certificate herda
- **GV-018** (se live) — badge `team_builder` integra

---

## Riscos

- **Certificate sem opt-in expõe nome:** default pseudonimizado + opt-in explícito LGPD
- **Gaming via contas múltiplas:** rate limit criação conta + CNPJ uniqueness; badges tied a atividade orgânica

---

## Arquivos Impactados

### Novos
- `frontend/app/certificados/[userId]/[badgeCode]/page.tsx`
- `frontend/app/certificados/[userId]/[badgeCode]/opengraph-image.tsx`
- `frontend/app/dashboard/components/BadgeGallery.tsx`
- `backend/services/badge_awarder.py`
- `backend/templates/emails/badge_unlock.html`
- `supabase/migrations/YYYYMMDDHHMMSS_user_badges.sql` (+ down)
- `backend/tests/test_badge_awarder.py`

### Modificados
- `frontend/app/dashboard/page.tsx` (integra BadgeGallery)
- `frontend/app/conta/privacidade/page.tsx` (toggle mostrar nome real em certificates)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — cobre gap STORY-247 com foco viral externo LinkedIn B2G |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
