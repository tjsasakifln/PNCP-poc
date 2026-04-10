# STORY-421: Fix Next.js InvariantError `/login` — Expected RSC response, got text/plain

**Priority:** P2 — Medium (baixa frequência, UX degradada)
**Effort:** M (1-2 days)
**Squad:** @dev + @ux-design-expert
**Status:** Draft
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issue:** https://confenge.sentry.io/issues/7397346898/ (6 eventos)
**Sprint:** Sprint rotina (1w-2w)

---

## Contexto

Frontend `/login` está gerando `InvariantError: Expected RSC response, got text/plain. This is a bug in Next.js.` em 6 eventos há 2 dias.

**Possíveis causas:**
1. Middleware (`frontend/middleware.ts`) retornando redirect com `Content-Type: text/plain` incorreto
2. Cache headers (CDN Cloudflare ou edge) servindo text/plain em vez de RSC payload
3. Erro em `frontend/app/login/page.tsx` (linhas 58-266) dentro do `<Suspense>` — fallback virando text/plain
4. Interação com OAuth callback (`/auth/callback`) que retorna redirect inválido

**Stack do erro:**
```
InvariantError: Expected RSC response, got text/plain. This is a bug in Next.js.
  at handleSlug(next.dist.shared.lib.router.utils:sorted-routes)
```

A referência a `handleSlug` + `sorted-routes` sugere que o erro acontece durante resolução de route dinâmica — possivelmente o middleware faz rewrite para uma rota dinâmica que retorna fallback inválido.

**Relacionado (mas já corrigido):** STORY-421 NÃO é o mesmo que o slug conflict `[setor] !== [cnpj]` — aquele já foi corrigido no commit `40bf4968`. Este é outro erro do mesmo pacote Next.js mas trigger diferente.

---

## Acceptance Criteria

### AC1: Reproduzir o bug
- [ ] Abrir Playwright e navegar para `/login` forçando:
  - [ ] Cache bypass (`Cache-Control: no-cache`)
  - [ ] Headers `Accept: text/x-component, */*`
  - [ ] Ambos desktop e mobile viewport
- [ ] Capturar Network tab e identificar response que retorna text/plain
- [ ] Documentar steps reproduzidos no Dev Notes

### AC2: Identificar causa raiz
- [ ] Auditar `frontend/middleware.ts` para redirects relacionados a `/login`
- [ ] Verificar se há `NextResponse.rewrite()` ou `NextResponse.redirect()` retornando text/plain
- [ ] Verificar CSP headers em `frontend/middleware.ts:82-91` — há restrição que está capando RSC?
- [ ] Checar Next.js issue tracker para bugs similares na versão em uso (`frontend/package.json`)
- [ ] Se for bug upstream Next.js, considerar upgrade ou workaround

### AC3: Aplicar fix
- [ ] Corrigir Content-Type header no middleware (ou middleware que seja o culpado)
- [ ] Se for redirect: usar `NextResponse.redirect(url, { status: 302 })` sem headers customizados
- [ ] Se for rewrite: garantir que target URL retorna HTML válido ou RSC payload
- [ ] Se for CSP: revisar `connect-src` para incluir necessary origins (`self`, etc)

### AC4: Error boundary defensivo
- [ ] Adicionar `error.tsx` em `frontend/app/login/error.tsx` (se não existir):
  ```tsx
  'use client';
  export default function LoginError({ error, reset }) {
    // Mostrar UI amigável + botão "tentar novamente"
    // Sentry.captureException(error)
  }
  ```
- [ ] Garante que usuários não veem tela branca mesmo se o bug voltar

### AC5: Regression E2E test
- [ ] Criar `frontend/e2e-tests/login-rsc.spec.ts`:
  - [ ] Navegar para `/login` cold (cache limpo)
  - [ ] Validar response Content-Type correto
  - [ ] Clicar em botão Google OAuth → validar redirect funciona
  - [ ] Logout + re-login → sem InvariantError
- [ ] Rodar em CI

### AC6: Verificação pós-deploy
- [ ] Monitorar Sentry issue 7397346898 por 48h — zero novos eventos
- [ ] Rodar E2E test em staging + produção via Playwright
- [ ] Marcar issue como **Resolved** no Sentry

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `frontend/middleware.ts` | Revisar redirects/rewrites que afetam /login |
| `frontend/app/login/page.tsx` | Linhas 58-266 — possivelmente refatorar Suspense boundary |
| `frontend/app/login/error.tsx` | **Novo** — error boundary defensivo |
| `frontend/e2e-tests/login-rsc.spec.ts` | **Novo** — regression test |
| `frontend/next.config.js` | (Possível) ajustar headers RSC |

---

## Implementation Notes

- **Investigação primeiro:** não adianta chutar fix sem reproduzir. Dedicar 2-3h para reproduzir antes de codificar qualquer mudança.
- **Next.js version:** verificar `frontend/package.json` — se estiver usando versão muito recente, pode ser bug conhecido. Procurar em https://github.com/vercel/next.js/issues com keyword "Expected RSC response".
- **Workaround temporário:** se bug é upstream sem fix disponível, adicionar `export const dynamic = 'force-dynamic'` em `/login/page.tsx` força rendering full (sem RSC optimization) — menos performático mas evita o bug.
- **CSP impact:** se o fix envolve mudar CSP, coordenar com @devops (STORY-223 histórica mostra que CSP mudanças afetam outras partes do app).
- **Related issue:** STORY-423 (Sentry hygiene) inclui marcar o slug conflict como resolved — não confundir as duas.

---

## Dev Notes (preencher durante implementação)

<!-- @dev: documentar steps para reproduzir + causa raiz encontrada -->

---

## Verification

1. **Local:** `npm run dev` + navegar `/login` sem erros no console
2. **E2E:** `npm run test:e2e -- login-rsc.spec.ts` passa
3. **Staging:** Playwright script navega 50x no `/login` sem gerar issue no Sentry
4. **Produção:** Sentry issue 7397346898 sem novos eventos por 48h

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
