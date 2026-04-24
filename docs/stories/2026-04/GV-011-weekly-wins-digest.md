# GV-011: Weekly Wins Digest Público (Opt-In)

**Priority:** P2
**Effort:** S (5 SP, 2-3 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 4

---

## Contexto

Loom tem "Loom of the Week". Adaptação B2G: users que marcam pipeline como "Ganhei" podem opt-in para aparecer em digest público semanal `/wins/2026-04-W17`. Página indexável → SEO + social proof + content loop automático.

Integra com GV-012 (post-win modal) — momento pico de excitação do user é o momento certo de pedir opt-in.

---

## Acceptance Criteria

### AC1: Tabela + opt-in

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_public_wins.sql`:
  ```sql
  CREATE TABLE public_wins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    licitacao_id TEXT NOT NULL,
    valor_ganho_brl NUMERIC,
    sector TEXT,
    uf TEXT,
    org_publico TEXT,
    display_mode TEXT DEFAULT 'anonymous',  -- 'anonymous' | 'company_name' | 'full'
    week_slug TEXT NOT NULL,  -- '2026-04-W17'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    opted_out BOOLEAN DEFAULT FALSE
  );
  CREATE INDEX idx_public_wins_week ON public_wins(week_slug);
  ```

### AC2: Post-win opt-in (integra GV-012)

- [ ] `GV-012 PostWinModal` adiciona checkbox:
  - "Compartilhar vitória anonimizada no digest semanal (opt-in)"
  - Radio modes: Anonymous (setor+UF+valor bucket) | Company name (razão social) | Full (nome + detalhes)
  - Default: Anonymous pre-checked para maximizar participação
  - Consentimento LGPD expresso com timestamp

### AC3: Página weekly digest

- [ ] `frontend/app/wins/[weekSlug]/page.tsx`:
  - SSG + ISR 24h
  - Header: "Vitórias da semana {date_range}"
  - Stats agregados topo: total wins, valor total ganho (bucketized), setor com mais wins, UF com mais wins
  - Lista wins: cards com modo display conforme `display_mode`
  - CTA recorrente "Sua próxima vitória começa aqui" → `/signup`
  - Schema.org `ItemList`

### AC4: Cron build semanal

- [ ] `backend/jobs/cron/compile_wins_digest.py`:
  - Trigger Segunda 9h BRT
  - Para semana fechada (domingo anterior), agrega wins
  - Publish em static render (revalidate trigger Next.js)
  - Metrics `smartlic_wins_digest_published{week}`

### AC5: Opt-out retroativo

- [ ] `frontend/app/conta/privacidade/page.tsx`:
  - Lista minhas wins públicas
  - Toggle "Remover do digest" → update `opted_out=true`
  - Next revalidate remove da página
  - Respeita retroativo LGPD "direito ao esquecimento"

### AC6: LinkedIn share button

- [ ] Página weekly digest tem share button:
  - "Compartilhar na minha rede"
  - Pre-filled: "Confira as vitórias da semana no SmartLic — R$ X em licitações ganhas por empresas B2G"

### AC7: Tracking

- [ ] Mixpanel `public_wins_page_viewed`, `public_wins_share_clicked`, `public_wins_optin_granted`

### AC8: Testes

- [ ] Unit cron compile
- [ ] E2E Playwright: mark win → opt-in → wait revalidate → page renders

---

## Scope

**IN:**
- Opt-in flow (via GV-012)
- Weekly digest page
- Cron build
- Opt-out retroativo
- Share LinkedIn

**OUT:**
- Monthly/quarterly digests (weekly suficiente inicialmente)
- Newsletter email digest (focus on-page web)
- Gamification leaderboard (privacy B2G)

---

## Dependências

- **GV-012** (post-win modal) — opt-in flow
- `frontend/app/sitemap.ts`

---

## Riscos

- **Privacy leak — nome real sem opt-in explícito:** triple-check LGPD consentimento
- **Digest vazio (poucos wins):** fallback "Esta semana está começando" + stats agregados generais
- **Opt-out latency — página stale por 24h ISR:** botão "remover imediatamente" que força `revalidateTag`

---

## Arquivos Impactados

### Novos
- `frontend/app/wins/[weekSlug]/page.tsx`
- `backend/jobs/cron/compile_wins_digest.py`
- `supabase/migrations/YYYYMMDDHHMMSS_public_wins.sql` (+ down)
- `backend/tests/test_wins_digest.py`

### Modificados
- `frontend/app/pipeline/components/PostWinModal.tsx` (de GV-012 — adiciona opt-in)
- `frontend/app/conta/privacidade/page.tsx` (opt-out retroativo)
- `frontend/app/sitemap.ts` (incluir /wins/*)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — Loom-of-the-week adaptado B2G com LGPD compliance |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
