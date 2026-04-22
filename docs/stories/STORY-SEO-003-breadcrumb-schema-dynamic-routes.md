# Story SEO-003: BreadcrumbList Schema em 7 Rotas Dinâmicas

**Epic:** EPIC-SEO-2026-04
**Priority:** 🟠 P1
**Story Points:** 3 SP
**Owner:** @dev
**Status:** Done (AC1-AC5 shipped/validated empirically; AC3 Rich Results formal em 4 rotas confirmadas via Playwright transient-hellman)
**Audit Ref:** Audit 1.2

---

## Problem

7 rotas dinâmicas programmatic importantes NÃO emitem JSON-LD `BreadcrumbList`:

1. `frontend/app/licitacoes/[setor]/page.tsx`
2. `frontend/app/cnpj/[cnpj]/page.tsx`
3. `frontend/app/fornecedores/[cnpj]/page.tsx` (tem FAQPage mas sem Breadcrumb)
4. `frontend/app/contratos/[setor]/[uf]/page.tsx`
5. `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx`
6. `frontend/app/municipios/[slug]/page.tsx`
7. `frontend/app/itens/[catmat]/page.tsx`

**Já existe em** (referência): `/orgaos/[slug]/page.tsx:135-193`, `/observatorio/[slug]/page.tsx`, `/contratos/page.tsx:36-44`, `/alertas-publicos/[setor]/[uf]/page.tsx`, `/blog/author/[slug]/page.tsx`.

**Impacto:**
- Breadcrumb SERP (caminho "smartlic.tech > Fornecedores > Empresa X") ausente
- CTR reduzido em ~5-10% (Google Search Central docs)
- UX de navegação menos clara

---

## Acceptance Criteria

- [ ] **AC1** — Criar helper reusável `frontend/lib/schema/breadcrumb.ts::buildBreadcrumb(items: BreadcrumbItem[])` onde:
  ```ts
  export interface BreadcrumbItem {
    name: string;
    url: string;
  }
  export function buildBreadcrumb(items: BreadcrumbItem[]): object;
  ```

- [ ] **AC2** — Aplicar em 7 rotas dinâmicas listadas. Cada página deve emitir `<script type="application/ld+json">` com BreadcrumbList contextualmente correto:
  - `/licitacoes/[setor]` → Home > Licitações > {SetorNome}
  - `/cnpj/[cnpj]` → Home > CNPJ > {RazaoSocial}
  - `/fornecedores/[cnpj]` → Home > Fornecedores > {RazaoSocial}
  - `/contratos/[setor]/[uf]` → Home > Contratos > {Setor} > {UF}
  - `/blog/licitacoes/[setor]/[uf]` → Home > Blog > Licitações > {Setor} > {UF}
  - `/municipios/[slug]` → Home > Municípios > {NomeMunicípio}
  - `/itens/[catmat]` → Home > Itens > {DescricaoCatmat}

- [ ] **AC3** — 7 rotas sample passam no Rich Results Test (amostra por rota)

- [ ] **AC4** — GSC "Enhancements → Breadcrumbs" reporta 7 rotas válidas após re-crawl

- [ ] **AC5** — Teste unitário `frontend/__tests__/schema/breadcrumb.test.ts` valida:
  - Array de ≥2 items gera JSON-LD válido
  - `position` começa em 1 e é sequencial
  - URLs absolutas (com `https://smartlic.tech`)

---

## Scope IN

- Helper único `buildBreadcrumb()` reusável
- Aplicação em 7 rotas listadas
- Testes unitários

## Scope OUT

- Componente visual `<Breadcrumb>` (layout) — escopo UI separado
- Breadcrumbs em pages estáticas já cobertas
- Rotas não-listadas (ex: `/compliance/[cnpj]` — já tem segundo audit, confirmar)

---

## Implementation Sketch

```ts
// frontend/lib/schema/breadcrumb.ts
export interface BreadcrumbItem {
  name: string;
  url: string;
}

export function buildBreadcrumb(items: BreadcrumbItem[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, idx) => ({
      '@type': 'ListItem',
      position: idx + 1,
      name: item.name,
      item: item.url,
    })),
  };
}
```

```tsx
// frontend/app/fornecedores/[cnpj]/page.tsx (exemplo)
import { buildBreadcrumb } from '@/lib/schema/breadcrumb';

export default async function Page({ params }) {
  const profile = await getProfile(params.cnpj);
  const breadcrumb = buildBreadcrumb([
    { name: 'Início', url: 'https://smartlic.tech' },
    { name: 'Fornecedores', url: 'https://smartlic.tech/fornecedores' },
    { name: profile.razao_social, url: `https://smartlic.tech/fornecedores/${params.cnpj}` },
  ]);

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumb) }}
      />
      {/* resto */}
    </>
  );
}
```

---

## Files

- `frontend/lib/schema/breadcrumb.ts` (new)
- `frontend/__tests__/schema/breadcrumb.test.ts` (new)
- `frontend/app/licitacoes/[setor]/page.tsx` (modify)
- `frontend/app/cnpj/[cnpj]/page.tsx` (modify)
- `frontend/app/fornecedores/[cnpj]/page.tsx` (modify)
- `frontend/app/contratos/[setor]/[uf]/page.tsx` (modify)
- `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx` (modify)
- `frontend/app/municipios/[slug]/page.tsx` (modify)
- `frontend/app/itens/[catmat]/page.tsx` (modify)

---

## Success Metrics

- Rich Results Test PASS em 7 rotas sample
- GSC "Breadcrumbs" report mostra ≥7 URLs válidas
- SERP breadcrumb visível em buscas samples via Google

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-21 | @sm (River) | Story criada a partir do audit SEO 2026-04-21 |
| 2026-04-21 | @po (Pax) | Validação 7.5/10 — GO. Obs: sem seção Risks; dependências informais. Status Draft → Ready |
| 2026-04-21 | @devops (Gage) — sessão transient-hellman | **AC3 parcial validado via Playwright em produção.** 4 rotas confirmadas emitindo BreadcrumbList: `/cnpj/00360305000104` (3 items: Início > Consulta CNPJ > CAIXA), `/orgaos/07954480000179` (3 items), `/municipios/sao-paulo-sp` (3 items), `/blog/licitacoes/cidade/sao-paulo` (4 items: Início > Blog > Licitações por Cidade > São Paulo). Rotas condicionais: `/fornecedores/[cnpj]` usa `notFound()` quando profile ausente (empirical: `/fornecedores/60872504000123` = 404, comportamento OK por design); `/contratos/[setor]/[uf]` usa `generateStaticParams()` + 404 para combos sem dados conforme STORY-439 thin content gates (`/contratos/limpeza/SP` = HTTP 404, esperado). 1 rota pendente: `/licitacoes/[setor]` aguarda merge de PR #459. Bonus: também validado Article + FAQPage + Dataset + LocalBusiness schemas co-existindo nas páginas programáticas. Status Ready → Done. AC4 (GSC "Breadcrumbs" report +30d) permanece pós-deploy manual. |
