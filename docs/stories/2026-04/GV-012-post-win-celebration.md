# GV-012: Post-Win Celebration Flow + Shareable Card

**Priority:** P1
**Effort:** S (5 SP, 2-3 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 2

---

## Contexto

Momento pico de excitação de um user B2G = **ganhou uma licitação**. Hoje o pipeline aceita status "Ganhei" sem celebração nem CTA social. Perde-se oportunidade máxima de viral advocacy.

Solução: modal celebratório + shareable card (LinkedIn/WhatsApp) gerado como PNG canvas → user posta vitória + watermark SmartLic.

Integra com GV-011 (opt-in para weekly digest) e GV-018 (referral tiered — badge team_builder se aplicável).

---

## Acceptance Criteria

### AC1: Modal celebração

- [ ] `frontend/app/pipeline/components/PostWinModal.tsx`:
  - Disparado quando user marca pipeline item com status `ganho`
  - Uma vez por win (não re-abrir)
  - Confetti animation (canvas-confetti lib) no mount
  - Mensagem: "🎉 Parabéns! Você ganhou — R$ {valor_estimado} na licitação {titulo}"
  - 3 CTAs:
    - "Compartilhar no LinkedIn" (gera card PNG + share)
    - "Indicar colega" (redirect /indique — integra GV-018)
    - "Fechar"
  - Checkbox opt-in: "Aparecer no digest público semanal (anônimo ou com razão social)" — integra GV-011

### AC2: Shareable card gerator

- [ ] `frontend/app/pipeline/components/WinShareCard.tsx`:
  - Canvas render (HTML2Canvas ou custom Canvas API)
  - Layout card:
    - Background gradient branded
    - "GANHEI!" em destaque
    - Valor bucketized: "R$ 100k-500k" ou opcional exato (se user opt-in)
    - Setor + UF
    - Logo SmartLic + watermark (herda GV-002)
    - QR code opcional pointing to `/signup?ref={user_hash}` (integra GV-018)
  - Download PNG (1200x630 LinkedIn-ready)
  - Tamanhos alternativos: Instagram story (1080x1920), Twitter (1200x675)

### AC3: Share buttons canais

- [ ] LinkedIn: open `https://linkedin.com/sharing/share-offsite/?url=...` com image anexa (via URL tmp hostada)
- [ ] WhatsApp: `wa.me/?text=...` com link para OG preview page
- [ ] Email: mailto: pré-preenchido
- [ ] Copy link: URL da OG page (`/analise/[hash]?win=true`)

### AC4: Tracking

- [ ] Mixpanel:
  - `win_marked` (quando status vira 'ganho')
  - `win_celebration_shown`
  - `win_shared` com `channel` (linkedin/whatsapp/email/copy)
  - `win_digest_optin_granted` (integra GV-011)
- [ ] Backend logs win em tabela `user_wins` para analytics

### AC5: OG preview page (se share URL)

- [ ] URL `/analise/[hash]?win=true` renderiza modo especial:
  - Título: "Acabei de ganhar uma licitação com SmartLic!"
  - Card visual + watermark
  - CTA destacado "Análise grátis 14 dias"
  - OG image reutiliza card gerado

### AC6: Testes

- [ ] Unit `frontend/__tests__/components/PostWinModal.test.tsx`
- [ ] Snapshot `WinShareCard` 3 size variants
- [ ] E2E Playwright: mark win → modal opens → download card → share (mock)

---

## Scope

**IN:**
- Modal celebração
- Card PNG generator
- Share multi-channel
- Tracking
- OG preview com ?win=true

**OUT:**
- Video export do confetti (overkill) — v2
- GIF animated card — v2
- Multi-language card (pt-BR only) — v2

---

## Dependências

- **GV-002** (watermark) — card herda
- **GV-011** (weekly digest) — opt-in checkbox integra
- **GV-018** (referral) — QR code link

---

## Riscos

- **Canvas rendering issues mobile:** fallback SVG ou server-side render via @vercel/og
- **Valor exato leak sem opt-in:** default bucket; opt-in explícito para exato
- **Share buttons falhando em some networks:** graceful degradation (copy link sempre funciona)

---

## Arquivos Impactados

### Novos
- `frontend/app/pipeline/components/PostWinModal.tsx`
- `frontend/app/pipeline/components/WinShareCard.tsx`
- `frontend/__tests__/components/PostWinModal.test.tsx`
- `supabase/migrations/YYYYMMDDHHMMSS_user_wins.sql` (+ down)

### Modificados
- `frontend/app/pipeline/page.tsx` (trigger modal on status change)
- `frontend/app/analise/[hash]/page.tsx` (suporte query `?win=true`)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — peak-moment advocacy capture; integra GV-011 + GV-018 |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
