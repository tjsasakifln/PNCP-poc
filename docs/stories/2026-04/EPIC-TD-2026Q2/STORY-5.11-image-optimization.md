# STORY-5.11: Image Optimization Next.js Image (TD-FE-014)

**Priority:** P2 | **Effort:** S (4-8h → actual ~30min) | **Squad:** @dev + @ux-design-expert | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** todas imagens via `<Image>` Next.js (auto WebP, lazy load),
**so that** LCP melhore.

## Acceptance Criteria
- [x] AC1: Audit `<img>` tags — encontrados 2 (produção) + 2 (test mocks):
  - **Migrado:** `components/auth/MfaSetupWizard.tsx:161` — QR code `<img>` → `<Image>` com `unoptimized` (data URL), `priority`, width/height 192
  - **Preservado (intencional):** `app/estatisticas/embed/page.tsx:52` — template HTML dentro de string, exposto a usuários para embed em sites externos. `<Image>` do Next não funcionaria fora do contexto Next.
  - **Test mocks:** 2 arquivos em `__tests__/` usam `<img>` dentro de `jest.mock('next/image', ...)` — são mocks legítimos, não assets
- [x] AC2: Logos/icons com width/height definidos — QR code (192x192). Hero + outros assets já usam `<Image>` (ver `components/landing/HeroSection.tsx`)
- [x] AC3: Lighthouse LCP <2.5s — workflow de medição definido em STORY-5.16 (Lighthouse CI). Budgets ≤ 2.5s codificados em `lighthouserc.json`

## Tasks
- [x] Audit + substituições (1 migração realizada)
- [x] Validate Lighthouse (delegado a STORY-5.16 — mesmo sprint)

## Implementation Summary

**File `frontend/components/auth/MfaSetupWizard.tsx`:**

```diff
+ import Image from "next/image";
  ...
- <img src={qrCode} alt="QR Code para configuração TOTP" className="w-48 h-48" />
+ <Image
+   src={qrCode}
+   alt="QR Code para configuração TOTP"
+   width={192}
+   height={192}
+   className="w-48 h-48"
+   unoptimized
+   priority
+ />
```

- `unoptimized`: QR code é data URL; Next image optimizer não processa base64 nem adiciona valor.
- `priority`: QR é LCP na página de setup MFA (usuário precisa escanear imediatamente).
- `width`/`height`: 192 (Tailwind `w-48` = 12rem = 192px).

**Not migrated (intentional):**

```tsx
// frontend/app/estatisticas/embed/page.tsx:52
const badgeHtml = `<a href="https://smartlic.tech/estatisticas"><img src="${backendUrl}/v1/stats/public?format=badge" alt="..." /></a>`;
```

Esse HTML é copiado pelos usuários para embedar no site deles (terceiros).
`<Image>` depende do runtime Next; no site de terceiro, só `<img>` funciona.

## File List

**Modified:**
- `frontend/components/auth/MfaSetupWizard.tsx` — QR code migrado para `next/image`

## Tests

- `__tests__/auth/mfa-flow.test.tsx`: 18/18 passing após migração (zero regressão)
- Typecheck (`npx tsc --noEmit`): zero novos erros

## Definition of Done
- [x] Produção sem `<img>` para assets gerenciados pelo Next (apenas 1 HTML embebido para terceiros, intencional)
- [x] Hero + landing já usam `<Image>` (pré-existente)
- [x] Typecheck + tests verdes
- [ ] LCP verificação end-to-end — delegado a STORY-5.16

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Implementation: 1 migração (QR code MFA) + audit confirma demais `<img>` são fora de escopo (embed externo + test mocks) | @dev |
