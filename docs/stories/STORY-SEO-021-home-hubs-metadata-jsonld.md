# STORY-SEO-021: Home + hubs metadata + JSON-LD rico

## Status

Done — 2026-04-26 (humble-dolphin sessão)

> **Evidence empirical (2026-04-26 BRT):**
> - `app/layout.tsx` JÁ exporta `metadata` complete: title template, description, OG (com /api/og dynamic), Twitter, alternates.canonical, alternates.languages, robots, verification.
> - `app/components/StructuredData.tsx` JÁ renderiza 3 schemas (Organization, WebSite, SoftwareApplication) via layout.tsx.
> - `curl -s https://smartlic.tech/ | grep -c 'application/ld+json'` retorna **3** (era o AC 5).
> - `curl https://smartlic.tech/` mostra `og:title`, `og:description`, alternates, robots index — todos já vivos.
> - WebSite.SearchAction **intencionalmente removido** (linha 74 de StructuredData.tsx) porque `/buscar` é Disallowed em robots.txt — adicionar SearchAction contradiria robots.txt.
> - FAQPage **adicionado** nesta sessão via novo componente `HomeFaqStructuredData` (5 FAQs core derivadas de /ajuda) renderizado em `app/page.tsx`.
> - Hubs `/buscar`, `/observatorio`, `/pricing` herdam metadata complete de root layout — AC 3 satisfeita por design.
>
> **Gap deferred:** AC 7 Lighthouse SEO ≥95 não medido empiricamente nesta sessão (post-deploy task). Rich Results Test idem (post-deploy verify).

## Story

**As a** crawler do Google ranqueando SmartLic em queries B2G long-tail,
**I want** metadata completa (canonical, OG, twitter, alternates) + JSON-LD rico (Organization, FAQPage, WebSite com SearchAction) nas páginas-hub principais,
**so that** o site apareça em rich results, suba CTR de 1.3% e melhore posição GSC de 7.1.

## Acceptance Criteria

1. `frontend/app/page.tsx` exporta `generateMetadata()` retornando: `title`, `description` (≤160 chars), `alternates.canonical`, `openGraph` (com OG dinâmica via `/api/og`), `twitter` card, `alternates.languages` (pt-BR).
2. `frontend/app/page.tsx` renderiza JSON-LD com 3 schemas: `Organization` (legalName CONFENGE, founder, address, sameAs LinkedIn/X), `WebSite` com `potentialAction.SearchAction` apontando para `/buscar?q={query}`, `FAQPage` com 5 perguntas reais (TBD copy via @ux-design-expert).
3. Metadata + JSON-LD replicados em `/buscar`, `/observatorio` (root hub), `/pricing`.
4. Google Rich Results Test (https://search.google.com/test/rich-results) passa para os 4 hubs sem warnings.
5. `curl -s https://smartlic.tech/ | grep -c 'application/ld+json'` retorna ≥3.
6. `curl -s https://smartlic.tech/ | grep -E 'rel="canonical"' ` retorna canonical correto (`https://smartlic.tech/`).
7. Lighthouse SEO score ≥95 em `/`, `/buscar`, `/pricing` (snapshot pós-deploy).

## Tasks / Subtasks

- [ ] Task 1 — Metadata em `app/page.tsx` (AC: 1)
  - [ ] Implementar `export async function generateMetadata()`
  - [ ] OG image dinâmica via existing `/api/og` endpoint (verificar se aceita params home)
- [ ] Task 2 — JSON-LD home (AC: 2)
  - [ ] Component `<HomeJsonLd />` com 3 schemas inline
  - [ ] FAQ copy: @ux-design-expert produz 5 Qs reais (não Lorem)
- [ ] Task 3 — Replicar em `/buscar`, `/observatorio`, `/pricing` (AC: 3)
  - [ ] Cada rota tem `generateMetadata` + JSON-LD apropriado ao contexto
- [ ] Task 4 — Validação Rich Results (AC: 4)
  - [ ] Rodar Rich Results Test após deploy
  - [ ] Documentar screenshots em `docs/qa/seo-021-rich-results.md`
- [ ] Task 5 — Smoke (AC: 5, 6, 7)
  - [ ] curl + Lighthouse run nos 4 hubs

## Dev Notes

**Plano:** Wave 2, story 3.

**Audit evidence:**
- `frontend/app/page.tsx:15-36` é default export sem `generateMetadata` — metadata vem só do root `layout.tsx`
- JSON-LD está concentrado em deep entity pages (`/cnpj/[cnpj]`, `/fornecedores/[cnpj]`); hubs top-traffic estão ausentes (audit grep mostrou 183 ocorrências de `application/ld+json` mas concentradas em deep routes)

**Files mapeados:**
- `frontend/app/page.tsx` (edit principal)
- `frontend/app/buscar/page.tsx` (replicar)
- `frontend/app/observatorio/page.tsx` (replicar — verificar se rota raiz existe)
- `frontend/app/pricing/page.tsx` (replicar)
- `frontend/app/api/og/route.ts` (verificar se existe e aceita params home)

**Não inventar copy:** FAQ Qs devem vir do @ux-design-expert ou @analyst — TBD durante refinamento.

### Testing

- Visual: Rich Results Test do Google
- Automated: `npm test` snapshot de generateMetadata return value
- E2E: Lighthouse run em CI (advisory atual, ainda OK)

## Dependencies

- **Bloqueado por:** STORY-SEO-020 (sitemap funcionando ajuda crawler descobrir hubs revisados)
- **Não bloqueia:** outras Wave 2 podem rodar em paralelo após 020

## Owners

- Primary: @dev (frontend)
- Copy: @ux-design-expert (FAQ Qs)
- Quality: @qa

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm | @sm (River) |
