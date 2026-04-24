# Story SEO-018: Rotas Entity Broken — Implementar OR Noindex+Remove

**Epic:** EPIC-SEO-RECOVERY-2026-Q2
**Priority:** 🟡 P2
**Story Points:** 8 SP
**Owner:** @dev + @data-engineer
**Status:** Ready
**Depends on:** SEO-013

---

## Problem

Diagnóstico 2026-04-24 identificou **5+ rotas dinâmicas em código que retornam 404 direto em prod** — não aparecem no sitemap mas potencialmente descobertas via internal links, URL guessing de crawlers, ou referências externas:

| Path testado | Status | Rota em código |
|--------------|--------|----------------|
| `/observatorio/raio-x-sp` | 404 | `frontend/app/observatorio/[slug]/page.tsx` |
| `/observatorio/raio-x-saude` | 404 | idem |
| `/municipios/sp-sao-paulo` | 404 | `frontend/app/municipios/[slug]/page.tsx` |
| `/municipios/rj-rio-de-janeiro` | 404 | idem |
| `/orgaos/ministerio-saude` | 404 | `frontend/app/orgaos/[slug]/page.tsx` |
| `/itens/150101` | 404 | `frontend/app/itens/[catmat]/page.tsx` |
| `/alertas-publicos/saude` | 404 | `frontend/app/alertas-publicos/[setor]/page.tsx` |

Rotas **funcionando** (test):
- `/indice-municipal/sao-paulo-sp` → 200
- `/cnpj/00000000000191` → 200
- `/compliance/00000000000191` → 200
- `/alertas-publicos/saude/sp` → 200 (2-level route OK)

### Contexto: sitemap/4.xml já deveria cobrir isso

`frontend/app/sitemap.ts:708-777` (case 4) tem código para gerar rotas:
- `/cnpj/{cnpj}` (cnpjList)
- `/orgaos/{cnpj}` (orgaoList)
- `/fornecedores/{cnpj}` (fornecedoresCnpjList)
- `/municipios/{slug}` (municipiosList)
- `/itens/{catmat}` (itensList)
- `/contratos/orgao/{cnpj}` (contratosOrgaoList)

**Mas** endpoints backend retornam listas vazias ou timeout → sitemap/4.xml=0 (resolvido via SEO-013+014).

**Gap residual:** mesmo com endpoints funcionando, algumas rotas não aparecem:
- `/observatorio/raio-x-{slug}` — NUNCA foi adicionada ao sitemap. Rota existe como `frontend/app/observatorio/[slug]/page.tsx` mas sitemap id:0 tem apenas `/observatorio/raio-x-marco-2026` hardcoded (STORY-SEO-017 vai resolver esse específico).
- `/orgaos/{slug}` vs `/orgaos/{cnpj}` — sitemap gera `/orgaos/{cnpj}` mas rota pode aceitar slugs semânticos (`ministerio-saude`) que não são emitidos.
- `/municipios/{slug}` formato pode divergir: sitemap emite slugs via endpoint backend, mas test com `sp-sao-paulo` retorna 404 enquanto `/indice-municipal/sao-paulo-sp` funciona — inconsistência de formato slug entre rotas.

### Decisão estratégica

**Para cada rota, 3 caminhos:**

1. **IMPLEMENTAR** — se há dados reais e valor SEO (volume de busca, keyword relevância)
2. **NOINDEX+REMOVE** — se rota foi criada sem data source pronto, mais seguro remover da descoberta pública
3. **REDIRECT** — se rota duplica outra funcional (ex: `/orgaos/ministerio-saude` → `/orgaos/{cnpj-do-ministerio-saude}`)

---

## Acceptance Criteria

- [ ] **AC1** — Auditoria completa das rotas dinâmicas em `frontend/app/`:
  ```bash
  find frontend/app -type d -name "\[*\]" | while read dir; do
    path=$(echo "$dir" | sed 's|frontend/app||')
    echo "$path"
  done
  ```
  Documentar em seção "Auditoria" desta story: cada rota, se retorna 200/404 com sample slug, se está no sitemap, decisão (implementar/noindex/redirect).
- [ ] **AC2** — Para cada rota decidida como IMPLEMENTAR:
  - Confirmar data source backend responde (endpoint existe + retorna dados)
  - Page.tsx renderiza com fallback graceful (não 404) quando dados ausentes
  - Adicionar à sitemap se gerável em massa (>10 URLs válidas)
- [ ] **AC3** — Para cada rota decidida como NOINDEX+REMOVE:
  - `page.tsx` retorna `robots: { index: false, follow: false }`
  - Entry removida do sitemap (se lá está)
  - Internal links para essa rota removidos OR rel="nofollow"
- [ ] **AC4** — Para cada rota REDIRECT:
  - `next.config.js` ou middleware adiciona permanent redirect (301)
  - Source path adicionado a noindex (defense in depth)
- [ ] **AC5** — HTTP sweep após deploy:
  ```bash
  # Lista rotas críticas com slugs reais (não guess):
  for path in /observatorio/raio-x-sp /municipios/sp-sao-paulo /orgaos/03504182000126 /itens/{first-real-catmat} /alertas-publicos/saude; do
    code=$(curl -sL -o /dev/null -w "%{http_code}" https://smartlic.tech${path})
    echo "$code  $path"
  done
  ```
  Esperado: todas 200 OR intencionalmente 301/410, nenhuma 404 não-documentada.
- [ ] **AC6** — Sitemap total URLs cresce em ≥3000 (URLs de `/observatorio/raio-x-{uf}` × 27 UFs = 27, `/municipios/{slug}` × capital+grandes = 200, `/itens/{catmat}` top 1000 = 1000, rotas entity diversas somadas ≥3000).
- [ ] **AC7** — GSC "Not found (404)" drop em 28d após deploy.

---

## Scope IN

- Auditoria de todas rotas dinâmicas em `frontend/app/`
- Implementação OR noindex OR redirect para cada rota broken
- Atualização do sitemap para emitir novas rotas implementadas
- HTTP sweep validação

## Scope OUT

- Criação de rotas NOVAS (só recuperar existentes)
- Content quality/optimization das páginas (fase separada)
- A/B testing de slug format

---

## Implementation Notes

### Passo 1: auditoria

```bash
# Descoberta de rotas dinâmicas em código
cd /mnt/d/pncp-poc/frontend
find app -type d -name "\[*\]" -not -path "*/api/*" | sort

# Para cada, buscar uso em sitemap.ts
grep -n "\[rota\]\|url:.*\${baseUrl}/rota" app/sitemap.ts
```

Preencher tabela:

| Route | Sample 200 | Sample 404 | In sitemap? | Data source | Decision |
|-------|-----------|-----------|-------------|-------------|----------|
| `/observatorio/[slug]` | `marco-2026` | `raio-x-sp` | Hardcoded 1 entry | Backend? | IMPLEMENT (27 UFs) |
| `/municipios/[slug]` | `sao-paulo-sp` (via indice-municipal)? | `sp-sao-paulo` | Via endpoint | `/v1/sitemap/municipios` | Normalize slug format |
| ... | ... | ... | ... | ... | ... |

### Passo 2: implementar rotas selecionadas

Exemplo para `/observatorio/raio-x-{uf}`:

```typescript
// frontend/app/observatorio/[slug]/page.tsx (refactor)
export async function generateStaticParams() {
  const UFS = ['ac', 'al', /* ... 27 UFs */];
  return UFS.map(uf => ({ slug: `raio-x-${uf}` }));
}

export default async function Page({ params }: Props) {
  const { slug } = await params;
  const uf = slug.replace('raio-x-', '').toUpperCase();
  if (!/^[A-Z]{2}$/.test(uf)) return notFound(); // only real UF slugs
  const data = await fetchObservatorioData(uf);
  if (!data || data.total === 0) {
    return <EmptyStateObservatorio uf={uf} />;
  }
  return <ObservatorioUfPage data={data} />;
}
```

Adicionar ao sitemap (case 0 ou case 4):
```typescript
const UFS = [...];
const observatorioUfRoutes = UFS.map(uf => ({
  url: `${baseUrl}/observatorio/raio-x-${uf.toLowerCase()}`,
  lastModified: today,
  changeFrequency: 'monthly' as const,
  priority: 0.7,
}));
```

### Passo 3: noindex rotas sem futuro

```typescript
// frontend/app/orgaos/[slug]/page.tsx (se decidir remover slug semântico)
export const dynamic = 'force-static';
export async function generateMetadata() {
  return { robots: { index: false, follow: false } };
}
```

### Passo 4: redirect (se aplicável)

```typescript
// next.config.js
async redirects() {
  return [
    {
      source: '/orgaos/:slug((?!\\d+$).+)',  // slugs não-numéricos
      destination: '/orgaos', // redirect para hub
      permanent: true,
    },
  ];
}
```

---

## Risco

Maior story do epic (8 SP). Possível decompor em sub-stories se auditoria revelar >5 rotas para implementar. @po pode sugerir split em validação.

---

## Dependencies

- **Pre:** SEO-013 (backend responsivo para data sources), SEO-014 (RPCs funcionando)
- **Unlocks:** Meta de 10k+ páginas indexáveis

---

## Change Log

| Date | Agent | Action |
|------|-------|--------|
| 2026-04-24 | @sm (River) | Story criada. Maior do epic — pode ser split após AC1 auditoria revelar escopo real. |
| 2026-04-24 | @po (Pax) | *validate-story-draft 9/10 → GO condicional. Status Draft → Ready. **Caveat:** após AC1 auditoria, se >5 rotas IMPLEMENTAR, @dev deve retornar para @sm re-split em sub-stories (SEO-018a/b/c). 8 SP é teto — não estourar. |
