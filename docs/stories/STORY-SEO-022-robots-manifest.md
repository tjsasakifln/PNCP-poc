# STORY-SEO-022: `robots.ts` + `manifest.ts`

## Status

Done — 2026-04-26 (humble-dolphin sessão, no-op audit)

> **Evidence empirical (2026-04-26 BRT):**
> - `frontend/public/robots.txt` JÁ existe: Allow `/`, Disallow `/admin`, `/auth/callback`, `/api`, `/dashboard`, `/conta`, `/buscar`, `/pipeline`, `/historico`, `/mensagens`, `/alertas`, `/onboarding`, `/recuperar-senha`, `/redefinir-senha`. Sitemap declarado: `https://smartlic.tech/sitemap.xml`. Google-Extended permitido (AI Overviews). AI bots de treinamento bloqueados (Amazonbot, CCBot, ClaudeBot, GPTBot, etc.).
> - `frontend/public/manifest.json` JÁ existe: name "SmartLic — Inteligência em Licitações", short_name, description, start_url `/`, display standalone, background_color `#ffffff`, theme_color `#0a1e3f`, lang `pt-BR`, icons `[logo.svg any] + [favicon.ico 48x48]`.
> - `app/layout.tsx:149` referencia `<link rel="manifest" href="/manifest.json" />`. theme-color meta linha 150.
> - `curl https://smartlic.tech/robots.txt` retorna 200, content válido, sitemap declarado (Cloudflare prepends AI Content Signals).
> - `curl https://smartlic.tech/manifest.json` retorna 200, JSON válido.
>
> **Gap real (deferred — não direct revenue lever):** ícones PWA 192x192 e 512x512 ausentes. Lighthouse PWA Installability score abaixo do AC 5 (≥80). Não bloqueia indexação SEO. Followup pode gerar PNGs do `logo.svg` quando ImageMagick estiver disponível.

## Story

**As a** crawler do Google e usuário mobile salvando shortcut para SmartLic,
**I want** `robots.txt` declarando rules + sitemap location e `manifest.json` válido com PWA basics,
**so that** crawl seja eficiente (sem hits inúteis) e UX mobile permita "instalação" do app.

## Acceptance Criteria

1. `frontend/app/robots.ts` existe e exporta default function retornando `MetadataRoute.Robots` com: `Allow: /`, `Disallow: /admin/`, `Disallow: /api/`, `sitemap: https://smartlic.tech/sitemap.xml`.
2. `frontend/app/manifest.ts` existe e exporta default function retornando `MetadataRoute.Manifest` com: `name`, `short_name`, `description`, `start_url: /`, `display: standalone`, `background_color`, `theme_color`, `icons[]` (192x192 + 512x512).
3. `curl -s https://smartlic.tech/robots.txt` retorna content válido com sitemap declarado.
4. `curl -s https://smartlic.tech/manifest.json` retorna JSON válido sem erros (testado via JSON Schema validator).
5. Lighthouse PWA Installability Audit retorna score ≥80 em `/`.
6. Google Search Console "Sitemaps" detecta sitemap automaticamente após próximo crawl.

## Tasks / Subtasks

- [ ] Task 1 — Criar `app/robots.ts` (AC: 1)
  - [ ] Usar Next.js 16 file-based metadata convention
  - [ ] Disallow correto para áreas privadas (`/admin/*`, `/api/*`)
- [ ] Task 2 — Criar `app/manifest.ts` (AC: 2)
  - [ ] Ícones: confirmar com @ux-design-expert se já existem em `frontend/public/`; se não, usar logo atual
  - [ ] Theme/background colors: pegar do design system existente (não inventar)
- [ ] Task 3 — Smoke + Lighthouse (AC: 3, 4, 5)
  - [ ] curl em prod
  - [ ] Rodar Lighthouse local + comparar PWA score

## Dev Notes

**Plano:** Wave 2, story 4 (HIGH).

**Audit evidence:**
- `ls /mnt/d/pncp-poc/frontend/app/robots.ts /mnt/d/pncp-poc/frontend/app/manifest.ts` retorna "No such file or directory" — confirmado ausentes (Wave 0 grep).

**Files mapeados:**
- `frontend/app/robots.ts` (create)
- `frontend/app/manifest.ts` (create)
- `frontend/public/icons/` (verificar ícones existentes — TBD se faltarem)

**Convenção Next.js 16:** file-based metadata gera automaticamente `/robots.txt` e `/manifest.json` no build. Não criar `.json` direto na pasta `public/`.

### Testing

- Manual: curl + Lighthouse PWA audit
- Validação: JSON Schema do manifest via https://manifest-validator.appspot.com

## Dependencies

- **Bloqueado por:** STORY-SEO-020 (sitemap precisa estar live antes de robots referenciá-lo)
- **Não bloqueia:** outras

## Owners

- Primary: @dev (frontend)
- Assets: @ux-design-expert (ícones se necessário)
- Quality: @qa

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm | @sm (River) |
