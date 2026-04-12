# SEO-440 — Fix: noindex canonical leakage + sitemap inclui páginas noindex

**Status:** Done  
**Type:** Hotfix  
**Prioridade:** Alta — 580 páginas não indexadas no GSC

## Problema

Diagnóstico via Playwright + curl em produção confirmou 3 bugs causando ~580 páginas não indexadas no Google Search Console:

### Bug 1 — Canonical noindex herda homepage (CRÍTICO)
Quando thin-content gate dispara (`total < MIN_ACTIVE_BIDS_FOR_INDEX`), os page.tsx retornam `robots: { index: false }` **sem** `alternates.canonical`. O Next.js hereda o canonical global do `layout.tsx` (`https://smartlic.tech`). Resultado: 300+ páginas dizem ao Google "meu canonical é a homepage", criando sinal de conteúdo duplicado na raiz.

Confirmado por curl:
```
blog/licitacoes/saude/ac → noindex + canonical: https://smartlic.tech ← ERRADO
alertas-publicos/saude/ac → noindex + canonical: https://smartlic.tech ← ERRADO
licitacoes/saude → noindex + canonical: https://smartlic.tech ← ERRADO
```

### Bug 2 — Sitemap inclui páginas noindex (CRÍTICO)
`sitemap.ts` gera alertasRoutes com `generateSectorUfParams()` (todas 405 combos) sem filtro. Fallback de `fetchLicitacoesIndexable()` também retorna todas 405 combos quando endpoint falha. Google descobre URLs pelo sitemap, crawla, vê noindex → "Excluded by noindex" no GSC.

Confirmado: `alertas-publicos/vestuario/*` (27 UFs) todas noindex mas no sitemap.

### Bug 3 — Fallback sitemap gera todas 405 combos
Em `sitemap.ts:41`, quando `/v1/sitemap/licitacoes-indexable` falha: `return generateLicitacoesParams()` gera todas as combinações incluindo thin content.

## Acceptance Criteria

- [x] AC1: Todos os branches `noindex` nos page.tsx programáticos incluem `alternates: { canonical: <url-da-própria-página> }`
- [x] AC2: `sitemap.ts` — alertasRoutes filtrado por `indexableCombos` (fetchLicitacoesIndexable) em vez de `generateSectorUfParams()`
- [x] AC3: `sitemap.ts` — fallback de `fetchLicitacoesIndexable()` retorna `[]` (não mais `generateLicitacoesParams()`)
- [ ] AC4: Verificação curl pós-deploy: páginas noindex mostram canonical self-referencial, não homepage
- [ ] AC5: Sitemap não contém URLs que retornam noindex (amostra de validação)
- [x] AC6: `npx tsc --noEmit` sem erros

## Arquivos Afetados

- `frontend/app/sitemap.ts` (linhas 41, 44, 283)
- `frontend/app/alertas-publicos/[setor]/[uf]/page.tsx`
- `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx` 
- `frontend/app/blog/programmatic/[setor]/[uf]/page.tsx`
- `frontend/app/licitacoes/[setor]/page.tsx`

## File List

- [x] `docs/stories/SEO-440-fix-noindex-canonical-sitemap.md` (esta story)
- [x] `frontend/app/sitemap.ts`
- [x] `frontend/app/alertas-publicos/[setor]/[uf]/page.tsx`
- [x] `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx`
- [x] `frontend/app/blog/programmatic/[setor]/[uf]/page.tsx`
- [x] `frontend/app/licitacoes/[setor]/page.tsx`
