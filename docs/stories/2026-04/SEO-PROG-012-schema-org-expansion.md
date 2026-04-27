# SEO-PROG-012: Schema.org expansion (FAQPage, Organization, BreadcrumbList em rotas indexáveis + Rich Results CI)

**Priority:** P2
**Effort:** M (3 dias)
**Squad:** @dev
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 5 (27/mai–02/jun)
**Sprint Window:** 2026-05-27 → 2026-06-02
**Bloqueado por:** SEO-PROG-001..005 (rotas ISR estáveis)

---

## Contexto

JSON-LD schema.org enriquece resultados Google com **rich results** (snippets expandidos, FAQ, breadcrumbs, knowledge panel). Estado atual SmartLic:

- `BreadcrumbList`: presente em rotas SEO (e.g., `/cnpj/[cnpj]/page.tsx:156-164`, `/orgaos/[slug]/...`).
- `Dataset` (CC-BY-4.0): presente em `/observatorio/[slug]` (memory `STORY-OBS-001`).
- `Organization`: presente em rotas CNPJ (declarando o fornecedor como org), mas **não no layout root** (layout root deveria declarar SmartLic como Organization).
- **`FAQPage`**: ausente. Páginas como `/itens/[catmat]` já têm `faq_items` no payload backend (`page.tsx:25-28`) — desperdício SEO.

**Gaps**:

1. Layout root (`frontend/app/layout.tsx`) sem `Organization` schema → Google não tem knowledge panel data para SmartLic.
2. Páginas com FAQs (CNPJ, órgão, item, observatório) sem FAQPage schema → perda de rich result oportunista.
3. **Sem CI gate** para validar JSON-LD válido. Schema quebrado é silent failure (página renderiza, Google rejeita rich result).

**Por que P2 (não P1):** rotas SSR→ISR (P0) + bundle reduction (P1) são prerequisitos de ranking. Schema expansion é **uplift incremental** após base sólida. Mas é decisão consciente (não defer indefinidamente).

---

## Acceptance Criteria

### AC1: Organization schema em layout root

**Given** `frontend/app/layout.tsx` é root layout
**When** @dev adiciona JSON-LD
**Then**:

- [ ] Adicionar Organization schema no `<head>` do layout root:

```tsx
const organizationSchema = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'SmartLic',
  alternateName: 'SmartLic — Inteligência em Licitações Públicas',
  url: 'https://smartlic.tech',
  logo: 'https://smartlic.tech/logo.svg',
  description:
    'Plataforma de inteligência em licitações públicas que automatiza descoberta, análise e qualificação de oportunidades B2G.',
  founder: {
    '@type': 'Organization',
    name: 'CONFENGE Avaliações e Inteligência Artificial LTDA',
  },
  sameAs: [
    // TODO: adicionar URLs de LinkedIn / GitHub / Twitter quando criados
  ],
  contactPoint: {
    '@type': 'ContactPoint',
    email: 'contato@smartlic.tech',
    contactType: 'customer support',
    areaServed: 'BR',
    availableLanguage: 'Portuguese',
  },
};

// Em layout.tsx:
<script
  type="application/ld+json"
  dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
/>
```

- [ ] Schema injetado em **todas** as páginas (root layout) — não apenas SEO routes
- [ ] **NÃO** duplicar com Organization schema em `/cnpj/[cnpj]/page.tsx:131` (que declara o fornecedor como Org). São entidades distintas (SmartLic vs. fornecedor); coexistem.

### AC2: FAQPage em `/itens/[catmat]`

**Given** `/itens/[catmat]` já tem `faq_items` no payload backend
**When** @dev adiciona FAQPage schema
**Then**:

- [ ] Render FAQPage schema dinâmico:

```tsx
const faqSchema =
  profile.faq_items && profile.faq_items.length > 0
    ? {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: profile.faq_items.map((faq) => ({
          '@type': 'Question',
          name: faq.question,
          acceptedAnswer: {
            '@type': 'Answer',
            text: faq.answer,
          },
        })),
      }
    : null;

// Render apenas se schema não-null:
{faqSchema && (
  <script
    type="application/ld+json"
    dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
  />
)}
```

- [ ] Validar via Rich Results Test API (AC7)

### AC3: FAQPage em `/cnpj/[cnpj]` e `/orgaos/[slug]`

**Given** essas rotas atualmente não têm FAQ rendered visível
**When** @dev adiciona
**Then**:

- [ ] Backend deve retornar `faq_items` no payload (TODO @architect: verificar; se não existe, criar follow-up backend story para adicionar 3-5 FAQs estáticas comuns por tipo de página)
- [ ] FAQs renderizam HTML visível na página (Google exige conteúdo visível, não só schema)
- [ ] Schema `FAQPage` espelha HTML (1:1)
- [ ] Component `<FAQSection items={...} />` reutilizável em `frontend/app/components/seo/FAQSection.tsx`
- [ ] Acessibilidade: `<details>`/`<summary>` ou disclosure pattern ARIA

### AC4: BreadcrumbList audit + standardize

**Given** BreadcrumbList já presente em rotas mas com inconsistências
**When** @dev audita
**Then**:

- [ ] Audit `grep -rn "BreadcrumbList" frontend/app/` — listar todas implementações
- [ ] Padronizar via util `frontend/lib/seo-schemas.ts`:

```ts
export interface BreadcrumbItem {
  name: string;
  url: string;
}

export function generateBreadcrumbSchema(items: BreadcrumbItem[]) {
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

- [ ] Refatorar implementações inline em rotas SEO para usar util

### AC5: Dataset schema em rotas com dados públicos

**Given** rotas `/cnpj`, `/orgaos`, `/itens` apresentam dados PNCP (public domain) — eligible para Dataset schema CC-BY
**When** @dev expande
**Then**:

- [ ] `/cnpj/[cnpj]/page.tsx:142-154` já tem Dataset schema — manter, ajustar `license` para `https://creativecommons.org/licenses/by/4.0/` (consistente com observatório)
- [ ] `/orgaos/[slug]/page.tsx`: adicionar Dataset schema similar
- [ ] `/itens/[catmat]/page.tsx`: adicionar Dataset schema

### AC6: Rich Results Test CI gate

**Given** schema quebrado é silent failure
**When** @devops adiciona CI step
**Then**:

- [ ] Adicionar step em `.github/workflows/lighthouse.yml` (ou novo workflow `schema-validation.yml`):

```yaml
- name: Validate JSON-LD via Rich Results Test
  run: |
    # Para cada sample route, fetch HTML, extrair JSON-LD, validar via:
    # - jsonld lib parse (npm: jsonld)
    # - schema.org type matching
    npm install -g jsonld schemarama
    for url in \
      "https://staging.smartlic.tech/cnpj/${LHCI_TOP_CNPJ}" \
      "https://staging.smartlic.tech/orgaos/${LHCI_TOP_ORGAO_SLUG}" \
      "https://staging.smartlic.tech/itens/${LHCI_TOP_CATMAT}" \
      "https://staging.smartlic.tech/observatorio/${LHCI_TOP_OBSERVATORIO_SLUG}"; do
      node scripts/validate-schema.js "$url" || exit 1
    done
```

- [ ] Criar `scripts/validate-schema.js`:
  - Fetch HTML, extract `<script type="application/ld+json">`, parse JSON
  - Validate required fields (Organization: name+url+logo; FAQPage: mainEntity 1+ Question; BreadcrumbList: itemListElement 1+; Dataset: name+description+license+creator)
  - Exit 1 se schema malformado ou required fields ausentes
- [ ] **Alternativa simpler:** usar Google Rich Results Test API se rate limits permitirem; senão, validação local syntax-only é suficiente

### AC7: Manual validation post-deploy

**Given** Google Rich Results Test (https://search.google.com/test/rich-results) é a fonte de verdade
**When** PR mergeada
**Then**:

- [ ] @qa valida manualmente top-3 rotas de cada tipo (3 CNPJs, 3 órgãos, 3 itens, 3 observatórios) via Rich Results Test
- [ ] Resultados documentados em PR comment ou Sentry breadcrumb manual
- [ ] Esperado: 0 errors, possivelmente warnings (alguns campos opcionais)

---

## Scope

**IN:**
- Organization schema em root layout
- FAQPage em `/itens`, `/cnpj`, `/orgaos`
- Component `<FAQSection />` reutilizável
- BreadcrumbList util (`lib/seo-schemas.ts`)
- Dataset schema expansion (cnpj, orgaos, itens)
- CI gate validação JSON-LD (syntax + required fields)
- Manual Rich Results Test post-deploy

**OUT:**
- VideoObject / Recipe / Product schemas (não aplicáveis B2G)
- Speakable / SpeechSynthesis (over-engineering)
- AggregateRating / Review schemas (sem reviews em B2G)
- HowTo schemas (defer; útil em blog content específico mas escopo separado)
- Google Knowledge Panel claim (out-of-scope; processo manual via Search Console)
- structured data testing tool integration (defer; CI syntax check é suficiente)

---

## Definition of Done

- [ ] Organization schema em layout root, válido
- [ ] FAQPage em 3 rotas (itens, cnpj, orgaos) com HTML correspondente
- [ ] `<FAQSection />` component acessível
- [ ] BreadcrumbList padronizado via util
- [ ] Dataset schema CC-BY-4.0 em 4 rotas (cnpj, orgaos, itens, observatorio)
- [ ] CI gate JSON-LD validation passa
- [ ] Manual Rich Results Test pass em top-3 rotas de cada tipo
- [ ] Lighthouse SEO category ≥ 0.95 (validado em SEO-PROG-010)
- [ ] Bundle delta < +3KB (FAQSection + utils)
- [ ] CodeRabbit clean
- [ ] PR aprovado @qa + @architect
- [ ] Change Log atualizado

---

## Dev Notes

### Paths absolutos

- **Layout root:** `/mnt/d/pncp-poc/frontend/app/layout.tsx`
- **Util novo:** `/mnt/d/pncp-poc/frontend/lib/seo-schemas.ts`
- **Component novo:** `/mnt/d/pncp-poc/frontend/app/components/seo/FAQSection.tsx`
- **Rotas a modificar:**
  - `/mnt/d/pncp-poc/frontend/app/cnpj/[cnpj]/page.tsx`
  - `/mnt/d/pncp-poc/frontend/app/orgaos/[slug]/page.tsx`
  - `/mnt/d/pncp-poc/frontend/app/itens/[catmat]/page.tsx`
  - `/mnt/d/pncp-poc/frontend/app/observatorio/[slug]/page.tsx`
- **CI script novo:** `/mnt/d/pncp-poc/scripts/validate-schema.js`
- **CI workflow:** `/mnt/d/pncp-poc/.github/workflows/lighthouse.yml` (extend) ou novo `schema-validation.yml`

### Reference

- [Google Search Central — Structured Data](https://developers.google.com/search/docs/appearance/structured-data)
- [Schema.org FAQPage](https://schema.org/FAQPage)
- [Schema.org Dataset](https://schema.org/Dataset) — license CC-BY-4.0 specifically required for Google Dataset Search

### Padrões existentes

- Inline JSON-LD via `<script type="application/ld+json">` em `cnpj/[cnpj]/page.tsx:175-187`. Manter pattern (não migrar para `next/script` — JSON-LD prefere `dangerouslySetInnerHTML`).
- BreadcrumbList example em `cnpj/[cnpj]/page.tsx:156-164`.

### Backend FAQs (TODO @architect)

- `/v1/itens/{catmat}/profile` já retorna `faq_items` (linha 25 de `itens/page.tsx`).
- `/v1/empresa/{cnpj}/perfil-b2g` e `/v1/orgao/{slug}/stats` provavelmente NÃO retornam — verificar e criar follow-up backend story leve.
- Alternativa: hardcode 3-5 FAQs estáticas no frontend baseadas no contexto (e.g., "Quantos contratos {razao_social} tem?") — menos rich, mas zero dependency backend.

### Testing standards

- **Component test:** `<FAQSection />` aria-expanded toggle, keyboard navigation.
- **Schema test:** parse + validate via `jsonld.expand()` library.
- **E2E:** verify `<script type="application/ld+json">` presente em cada rota target.

### CI script `validate-schema.js`

```js
// scripts/validate-schema.js
const https = require('https');
const url = process.argv[2];

https.get(url, (res) => {
  let html = '';
  res.on('data', (chunk) => (html += chunk));
  res.on('end', () => {
    const matches = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g);
    if (!matches || matches.length === 0) {
      console.error(`[${url}] No JSON-LD found`);
      process.exit(1);
    }
    for (const match of matches) {
      try {
        const json = JSON.parse(match.replace(/<script[^>]*>/, '').replace(/<\/script>/, ''));
        // basic shape check
        if (!json['@context'] || !json['@type']) {
          console.error(`[${url}] Missing @context/@type`);
          process.exit(1);
        }
        console.log(`[${url}] Valid: ${json['@type']}`);
      } catch (err) {
        console.error(`[${url}] Parse error: ${err.message}`);
        process.exit(1);
      }
    }
  });
});
```

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Detecção |
|---|---|---|
| Rich Results Test errors | >0 manual | QA |
| GSC structured data warnings | aparece em GSC console | GSC manual |
| CI schema validation false positives | >20% PRs fail sem motivo | Soft rollback |

### Ações

1. Soft: remover schema individual problemático (e.g., FAQPage em uma rota) sem reverter PR inteiro.
2. Hard: revert PR via @devops.

---

## Dependencies

### Entrada

- SEO-PROG-001..005 (rotas ISR estáveis, JSON-LD existing intacto)

### Saída

- Nenhuma direta (P2 não bloqueia outras stories)

### Paralelas

- SEO-PROG-013 (GSC ingest pode incluir métricas de rich results pós-validação)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 9/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: FAQPage + Organization + BreadcrumbList + Rich Results CI |
| 2 | Complete description | OK | Estado atual auditado (BreadcrumbList sim, Dataset sim, Organization parcial, FAQPage ausente) |
| 3 | Testable acceptance criteria | OK | AC1-AC7 testáveis; AC6 CI gate via script JSON-LD validation |
| 4 | Well-defined scope (IN/OUT) | OK | OUT lista 6 schemas não aplicáveis + Knowledge Panel (manual) |
| 5 | Dependencies mapped | OK | 001-005 ISR estáveis (não regredir JSON-LD existing) |
| 6 | Complexity estimate | OK | Effort M (3 dias) consistente: 4 schemas + util + component + CI script + manual validation |
| 7 | Business value | OK | Rich results = snippets expandidos + Google Knowledge Panel data |
| 8 | Risks documented | OK | 3 triggers; soft rollback granular (remover schema individual) |
| 9 | Criteria of Done | OK | 11 itens incluindo Lighthouse SEO ≥0.95 (validado em SEO-PROG-010) |
| 10 | Alignment with PRD/Epic | OK | License CC-BY-4.0 consistente entre rotas; util `lib/seo-schemas.ts` DRY |

### Observations

- AC1 Organization schema NÃO duplica com Organization em `cnpj/[cnpj]/page.tsx:131` (entidades distintas: SmartLic vs fornecedor) — distinção corretamente reconhecida.
- AC3 FAQPage requer backend retornar `faq_items` em CNPJ/orgaos (TODO @architect: criar follow-up backend ou hardcode 3-5 FAQs estáticas) — fallback claro.
- AC6 CI gate JSON-LD via script local (vs Google API) é decisão pragmática (rate limits + auth complexity); bypass de Rich Results Test API.
- Score 9 (não 10): AC3 backend dependency parcialmente resolvido (TODO + alternativa hardcode); aceitável para Ready.
- Padrão `<script type="application/ld+json">` via `dangerouslySetInnerHTML` mantido — correto para JSON-LD vs `next/script`.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — Organization root + FAQPage + Dataset expansion | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (9/10). FAQPage backend dependency com fallback hardcode. Status Draft→Ready. | @po (Pax) |
