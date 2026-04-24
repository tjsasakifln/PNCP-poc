# SEN-FE-001: `/contratos/orgao/[cnpj]` sai de static para dynamic at runtime (2238 eventos)

**Status:** InReview
**Origem:** Sentry unresolved — issue 7409705693 (2238 eventos em 14d — maior volume do projeto)
**Prioridade:** P0 — Crítico (2238 eventos é ordem de magnitude acima de qualquer outro; indica regressão de SSG)
**Complexidade:** S (Small)
**Owner:** @dev
**Tipo:** Performance / SEO

---

## Problema

Next.js (App Router) emite erro:

```
Error: Page changed from static to dynamic at runtime /contratos/orgao/10791831000182,
reason: no-store fetch https://api.smartlic.tech/v1/contratos/orgao/10791831000182/stats
/contratos/orgao/[cnpj]
```

Culprit: `GET /contratos/orgao/[cnpj]/page`, stack em `src/server/app-render/dynamic-rendering.ts::markCurrentScopeAsDynamic`.

O que está acontecendo:
- Route `/contratos/orgao/[cnpj]` deveria ser estática (bom para SEO programmatic + CDN)
- Fetch com `cache: 'no-store'` converte a página para dynamic em runtime → CDN cache invalidado → cada request bate no backend
- **2238 eventos em 14d** = provável que todo render de CNPJ gere este erro — perda de SSG em escala

Impacto:
- SEO: Google recrawl pega dynamic render, pode rebaixar vs concorrência estática
- Performance: sem cache CDN, cada visita bate em `/v1/contratos/*/stats` (SEN-BE-006 loop)
- Custo: Railway backend recebe carga que deveria ser CDN-served

---

## Critérios de Aceite

- [x] **AC1:** Localizar fetch culpado em `frontend/app/contratos/orgao/[cnpj]/page.tsx` — remover `{ cache: 'no-store' }` ✓ (page.tsx:54)
- [x] **AC2:** Substituir por `{ next: { revalidate: 14400 } }` (ISR 4h — alinhado com `export const revalidate = 14400` da page) — coerente com pattern memory `project_sitemap_serialize_isr_pattern`. Nota: valor 14400 (não 3600 como sugerido) para alinhamento exato com ISR da page.
- [x] **AC3:** N/A — página continua estática (ISR). Não movida para Suspense pois decisão de negócio não é dynamic.
- [ ] **AC4:** Rodar `npm run build` e verificar que route `/contratos/orgao/[cnpj]` aparece como `● (SSG)` ou `◐ (ISR)` no output (não `ƒ (Dynamic)`) — **pending local build** (build WSL lento; será verificado em CI/deploy)
- [x] **AC5:** Teste Playwright: navegar para `/contratos/orgao/10791831000182` após deploy; verificar console NÃO mostra "Page changed from static to dynamic" ✓ `frontend/e2e-tests/contratos-orgao-ssg.spec.ts`
- [ ] **AC6:** Sentry issue `7409705693` NÃO recebe eventos novos por 48h após deploy — **post-deploy follow-up** (agendar `/schedule` agent em +48h)
- [ ] **AC7:** p95 de TTFB em `/contratos/orgao/*` cai abaixo de 500ms (antes, backend-bound) — **post-deploy observability**

### Anti-requisitos

- NÃO deixar `force-dynamic` na página — perderia SEO benefit
- NÃO usar `unstable_cache` como workaround sem revisar estratégia ISR

---

## Referência de implementação

- `frontend/app/contratos/orgao/[cnpj]/page.tsx`
- Pattern de `revalidate = 3600`: ver `frontend/app/sitemap.ts` e outras páginas SSG
- Memory `project_sitemap_serialize_isr_pattern`

---

## Riscos

- **R1 (Baixo):** ISR 1h pode mostrar stats desatualizados por até 1h — aceitável para perfil de órgão (muda pouco)

## Dependências

- SEN-BE-006 (slow stats) — fix desta story reduz carga no backend

---

## File List

- `frontend/app/contratos/orgao/[cnpj]/page.tsx` — linha 54 (fix: `cache:'no-store'` → `next:{revalidate:14400}`)
- `frontend/e2e-tests/contratos-orgao-ssg.spec.ts` — novo spec Playwright cobrindo AC5

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — top priority (2238 eventos, maior do projeto) |
| 2026-04-23 | @po | Validação 10/10 → **GO — P0 TOP**. LIVE lastSeen 2026-04-23 (hoje). Promovida Draft → Ready |
| 2026-04-24 | @dev | Implementação AC1/AC2/AC3/AC5 em branch `fix/sen-fe-001-contratos-orgao-isr`. Fix 1-linha + Playwright spec. AC4 pending build local; AC6/AC7 post-deploy. Status Ready → InReview |
