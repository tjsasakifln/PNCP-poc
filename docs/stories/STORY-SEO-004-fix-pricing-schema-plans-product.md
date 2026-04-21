# Story SEO-004: Fix Pricing em SoftwareApplication + Product Schema em /planos

**Epic:** EPIC-SEO-2026-04
**Priority:** 🟠 P1
**Story Points:** 2 SP
**Owner:** @dev
**Status:** Ready
**Audit Ref:** Audit 3.2 + 3.3

---

## Problem

### Bug 1: Pricing Desatualizado em SoftwareApplication Schema

`frontend/app/components/StructuredData.tsx:83-89` declara:
```json
{
  "@type": "SoftwareApplication",
  "offers": {
    "@type": "AggregateOffer",
    "lowPrice": "1599.00",
    "highPrice": "1999.00",
    "priceCurrency": "BRL",
    "offerCount": 3
  }
}
```

Mas o pricing real (documentado em `CLAUDE.md` + `frontend/public/llms.txt`):
- **SmartLic Pro**: R$397/mês (mensal), R$357 (semestral -10%), R$297 (anual -25%)
- **Consultoria**: R$997/mês, R$897 (semestral -10%), R$797 (anual -20%)

**Preços ~4× maiores que o real.** Google SERP "Software" rich result pode exibir valor errado → usuário frustrado + CTR decai.

### Bug 2: /planos Sem Product Schema

`frontend/app/planos/page.tsx` não emite JSON-LD `Product` por plano. Perde elegibilidade para:
- Google Merchant listing rich result
- Pricing table SERP enhancement
- Comparação de produtos em SGE/AI Overviews

---

## Acceptance Criteria

- [ ] **AC1** — Atualizar `frontend/app/components/StructuredData.tsx:83-89`:
  ```
  lowPrice: '297.00',
  highPrice: '997.00',
  priceCurrency: 'BRL',
  offerCount: 6   // 2 planos × 3 periodicidades
  ```

- [ ] **AC2** — Adicionar campos obrigatórios para Rich Results eligibility em SoftwareApplication offers:
  - `priceValidUntil`: dinâmico (today + 1 ano, ISO 8601)
  - `availability`: `'https://schema.org/InStock'`

- [ ] **AC3** — Criar `frontend/app/planos/_components/ProductSchema.tsx` que emite 2 Products (Pro, Consultoria), cada um com 3 `Offer` (mensal/semestral/anual):
  ```json
  {
    "@type": "Product",
    "name": "SmartLic Pro",
    "description": "...",
    "brand": { "@type": "Brand", "name": "SmartLic" },
    "offers": [
      { "@type": "Offer", "price": "397.00", "priceCurrency": "BRL", "category": "monthly", ... },
      { "@type": "Offer", "price": "357.00", ... "category": "semestral" },
      { "@type": "Offer", "price": "297.00", ... "category": "annual" }
    ]
  }
  ```

- [ ] **AC4** — Preços declarados em schema DEVEM refletir a fonte da verdade (`plan_billing_periods` table). Se discrepância existir → falhar CI. Helper `getPlanPricing()` lê direto da fonte.

- [ ] **AC5** — Rich Results Test PASS para:
  - Homepage (SoftwareApplication atualizado)
  - `/planos` (Product + Offer)

- [ ] **AC6** — Teste unitário `frontend/__tests__/planos/ProductSchema.test.tsx` valida preços match com constantes de billing + schema é válido JSON.

---

## Scope IN

- Fix pricing no SoftwareApplication schema (StructuredData.tsx)
- ProductSchema.tsx para /planos
- Teste unitário

## Scope OUT

- Review/AggregateRating schema (Audit 3.5 — story separada, requer reviews autênticos)
- Alteração de preços reais (fonte: `plan_billing_periods`)
- Copy das descriptions em /planos

---

## Implementation Sketch

```tsx
// frontend/app/components/StructuredData.tsx (patch)
const softwareApplicationSchema = {
  // ...
  offers: {
    '@type': 'AggregateOffer',
    lowPrice: '297.00',
    highPrice: '997.00',
    priceCurrency: 'BRL',
    offerCount: 6,
    priceValidUntil: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    availability: 'https://schema.org/InStock',
  },
};
```

```tsx
// frontend/app/planos/_components/ProductSchema.tsx
import { PLANS_PRICING } from '@/lib/plans';  // source of truth

export function ProductSchema() {
  const schemas = [
    {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: 'SmartLic Pro',
      description: 'Inteligência de decisão em licitações para empresas B2G',
      brand: { '@type': 'Brand', name: 'SmartLic' },
      offers: PLANS_PRICING.pro.periods.map(p => ({
        '@type': 'Offer',
        price: p.price.toFixed(2),
        priceCurrency: 'BRL',
        availability: 'https://schema.org/InStock',
        priceValidUntil: nextYearIso(),
        url: `https://smartlic.tech/planos?periodicity=${p.key}`,
      })),
    },
    // ... Consultoria idem
  ];
  return (
    <>
      {schemas.map((s, i) => (
        <script key={i}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(s) }}
        />
      ))}
    </>
  );
}
```

---

## Files

- `frontend/app/components/StructuredData.tsx` (modify — linhas 83-89)
- `frontend/app/planos/_components/ProductSchema.tsx` (new)
- `frontend/app/planos/page.tsx` (import ProductSchema)
- `frontend/lib/plans.ts` (garantir source of truth; se não existir, criar)
- `frontend/__tests__/planos/ProductSchema.test.tsx` (new)

---

## Success Metrics

- Rich Results Test PASS em `/` + `/planos`
- Google SERP "Software" rich snippet mostra R$297 como lowPrice
- GSC "Enhancements → Merchant Listings" reporta 2 URLs válidas (após re-crawl)

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-21 | @sm (River) | Story criada a partir do audit SEO 2026-04-21 |
| 2026-04-21 | @po (Pax) | Validação 7.5/10 — GO. Obs: sem seção Risks; AC4 CI check de preço a detalhar em Dev Notes. Status Draft → Ready |
