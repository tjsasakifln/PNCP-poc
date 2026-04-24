# GV-002: "Powered by SmartLic" Watermark + Pseudonimização em `/analise/[hash]`

**Priority:** P0 — blocker para GV-003, GV-004, GV-010, GV-011, GV-012, GV-014
**Effort:** S (5 SP, 2-3 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 1

---

## Contexto

Página pública `/analise/[hash]` (SEO-PLAYBOOK P6) já existe via endpoint `/api/share` e serve análises compartilhadas sem auth. Hoje expõe dados do usuário sem:
- Pseudonimização (CNPJ buscante + valores exatos aparecem)
- Branding persistente (sem CTA "Use SmartLic")
- OG image otimizada (preview pobre no LinkedIn/WhatsApp)

**Padrão Loom:** "todo output compartilhado é anúncio do produto." Sem watermark, share não converte.
**Lesson Lovable April/2026:** exposição pública sem pseudonimização gerou incidente de segurança. B2G com estratégia competitiva sensível exige mask default.

Esta story é **pré-requisito** para 6 outras stories do epic (GV-003/004/010/011/012/014) que dependem do artefato shareable.

---

## Acceptance Criteria

### AC1: Componente `PoweredByWatermark`

- [ ] `frontend/components/PoweredByWatermark.tsx`:
  - Badge flutuante canto inferior direito (sticky, não-bloqueante)
  - Copy default: "Análise feita com SmartLic — 14 dias grátis"
  - Botão CTA "Analisar minha empresa" → `/signup?source=shared_analysis&ref={share_hash}`
  - Close-button opt-out para user premium Pro+ (feature flag `watermark_removable_pro`)
  - Hover = expand com logo + benefit bullets (3 items max)
  - Mobile: colapsa em ícone, expande on-tap
- [ ] A/B test variant copy (registrado em GV-001 config):
  - `control`: "Análise feita com SmartLic — 14 dias grátis"
  - `urgency`: "Você também pode descobrir oportunidades — Teste grátis 14 dias"
  - `social`: "+2.000 empresas usam SmartLic para licitações — Comece grátis"

### AC2: Pseudonimização backend

- [ ] Estender `backend/routes/share.py` com layer `pseudonymize_analysis_payload(payload, requester_plan)`:
  - CNPJ buscante: mascarar formato `XX.XXX.XXX/0001-XX` (preserva sufixo 4 dígitos)
  - Valor estimado exato: converter para buckets:
    - `<R$ 100k`
    - `R$ 100k - R$ 500k`
    - `R$ 500k - R$ 2M`
    - `R$ 2M - R$ 10M`
    - `>R$ 10M`
  - Nome fantasia empresa buscante: removido (só `razao_social_mascara` visível)
  - Preservar: dados do edital (já são públicos do PNCP), setor, UF, modalidade
- [ ] Pro+ user com opt-out: payload sem mask (requer `remove_pseudonymization=true` no share creation + consentimento expresso registrado)
- [ ] Unit test `backend/tests/test_share_pseudonymize.py`:
  - CNPJ mask correto
  - Bucket mapping valores limítrofes
  - Opt-out preserva dados

### AC3: OG image dinâmica

- [ ] `frontend/app/analise/[hash]/opengraph-image.tsx` (Next.js 16 `@vercel/og`):
  - Template: logo SmartLic + título edital pseudonimizado + viability score + badge setor
  - Dimensões: 1200x630 (LinkedIn/WhatsApp/Twitter optimized)
  - Background gradient branded
  - Revalidate 24h (ISR)
- [ ] `frontend/app/analise/[hash]/twitter-image.tsx` (reutiliza opengraph-image)
- [ ] Meta tags em `page.tsx`:
  - `og:title`, `og:description`, `og:image`, `og:url`
  - `twitter:card = summary_large_image`

### AC4: CTA tracking

- [ ] Todo click no watermark emite `share_referral_click` Mixpanel com:
  - `share_hash`
  - `variant` (A/B variant atribuído)
  - `source_page` (shared_analysis)
  - `ua_summary` (mobile/desktop)
- [ ] Signup via link `source=shared_analysis` atribui `attribution_source = viral_share` no profile
- [ ] Dashboard admin `/admin/growth` (criado em GV-001) mostra:
  - Total watermark impressions
  - CTR por variant
  - Signup conversion rate por variant

### AC5: Settings — opt-out pseudonimização

- [ ] `frontend/app/conta/privacidade/page.tsx` (novo):
  - Toggle "Compartilhar análises sem pseudonimizar CNPJ/valores" (default OFF)
  - Só disponível para plano Pro+ (gated com upsell CTA)
  - Consentimento expresso LGPD com timestamp
  - Aplicado apenas em shares criados PÓS toggle ON (não retroativo)

### AC6: Testes

- [ ] Unit `frontend/__tests__/components/PoweredByWatermark.test.tsx`
- [ ] Unit `backend/tests/test_share_pseudonymize.py`
- [ ] E2E Playwright: user A compartilha análise → user B (não-logado) abre `/analise/[hash]` → vê watermark + dados pseudonimizados → clica CTA → signup + attribution correto
- [ ] Visual regression (Percy/Chromatic): watermark desktop + mobile

---

## Scope

**IN:**
- Componente watermark
- Pseudonimização backend
- OG images
- CTA tracking + attribution
- Settings opt-out

**OUT:**
- Tradução i18n do watermark (v2, BR-only por ora)
- Remoção total de watermark (enterprise plan custom — v2)
- Animação avançada do watermark (se A/B control ganhar, adicionar depois)
- A/B do CTA landing page destino (escopo separado)

---

## Dependências

- **GV-001** (A/B framework) — precisa estar Ready para AC1 variants
- `backend/routes/share.py` e `frontend/app/analise/[hash]/page.tsx` existentes (SEO-PLAYBOOK P6)

---

## Riscos

- **Pseudonimização insuficiente expõe CNPJ:** pen test antes deploy. Auditoria manual de 50 share links existentes (migration backfill não obrigatória — só novos shares).
- **OG image geração lenta timeout:** usar `@vercel/og` edge runtime; fallback estático se `generateImage` falhar.
- **Backlash sobre mask automático:** comunicar em changelog + email a usuários existentes; opt-out Pro disponível.

---

## Arquivos Impactados

### Novos
- `frontend/components/PoweredByWatermark.tsx`
- `frontend/app/analise/[hash]/opengraph-image.tsx`
- `frontend/app/analise/[hash]/twitter-image.tsx`
- `frontend/app/conta/privacidade/page.tsx`
- `backend/tests/test_share_pseudonymize.py`
- `frontend/__tests__/components/PoweredByWatermark.test.tsx`
- `frontend/e2e-tests/share-watermark.spec.ts`

### Modificados
- `frontend/app/analise/[hash]/page.tsx` (integra watermark + og tags)
- `backend/routes/share.py` (adiciona pseudonymize layer)
- `frontend/config/experiments.ts` (registra `gv_002_watermark_copy`)

---

## Testing Strategy

1. **Unit** AC6
2. **Visual** Percy comparando 3 variants + mobile/desktop
3. **E2E Playwright** fluxo completo share → open incognito → signup
4. **Manual audit** 50 share links via `/admin/shares` post-deploy
5. **Lighthouse-CI** ≥90 SEO score pós-deploy em `/analise/[hash]` público

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — blocker Wave 1 do epic; inspiração Loom watermark pattern |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
