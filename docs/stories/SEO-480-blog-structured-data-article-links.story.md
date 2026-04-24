# SEO-480: /blog — adicionar structured data Blog + expor artigos no DOM

**Status:** Ready
**Origem:** Selenium Quality Audit — test_structured_data_present, test_blog_has_articles_listed (2026-04-22)
**Epic:** EPIC-SEO-2026-04
**Prioridade:** P1 — Alto (crawlability e rich results bloqueados)
**Complexidade:** M (Medium)
**Sprint:** SEO-sprint-atual
**Owner:** @dev
**Tipo:** Fix SEO + Crawlability

---

## Problema

O audit detectou 2 issues em `/blog`:

### Issue 1 — Structured data `Blog` ausente

`/blog` tem JSON-LD: `['Organization', 'WebSite', 'SoftwareApplication']`.
Falta o tipo `Blog` (ou `BlogPosting` list). Sem esse schema, Google não reconhece a página como hub de blog e não gera rich results de artigos (sitelinks, carrossel).

### Issue 2 — 0 artigos visíveis no DOM

Audit detectou 0 `article a`, `[class*='post'] a`, `[class*='article'] a` na página `/blog`.
Googlebot usa rendering JavaScript, mas crawlability de artigos individuais depende de links no HTML. Se os artigos são carregados via fetch client-side sem SSR, o Googlebot pode não os indexar via link discovery.

Métrica do audit:
```json
"blog_article_links_count": 0
```

---

## Critérios de Aceite

### Structured Data (AC1–AC2)

- [ ] **AC1:** `/blog` inclui JSON-LD com `@type: "Blog"` ou `@type: "CollectionPage"` contendo `BlogPosting` items
- [ ] **AC2:** Schema inclui `name`, `description`, e ao menos 3 `blogPost` entries recentes com `headline`, `url`, `datePublished`

### Artigos no DOM (AC3–AC4)

- [ ] **AC3:** `/blog` renderiza via SSR (ou SSG) lista de artigos com links `<a href="/blog/[slug]">` presentes no HTML initial (verificar com `curl https://smartlic.tech/blog | grep -c "href.*blog/"` — deve retornar > 5)
- [ ] **AC4:** Audit Selenium passa: `blog_article_links_count >= 5` em `test_blog_has_articles_listed`

### Regressão (AC5)

- [ ] **AC5:** `npm run build` sem erros, `npm test` 100% passing

---

## Investigação Prévia

Verificar se `/blog` usa `"use client"` no page.tsx — se sim, artigos são client-side only e Googlebot vê HTML vazio. Fix: mover fetch de artigos para Server Component ou usar `generateStaticParams`.

Arquivos prováveis:
- `frontend/app/blog/page.tsx` — adicionar structured data + confirmar SSR do listing
- `frontend/app/blog/layout.tsx` — se JSON-LD estiver no layout

---

## Riscos

- **R1 (Médio):** Se `/blog` usa `"use client"` — migrar para Server Component pode introduzir regressão se existir estado client-side na página. Investigar antes de implementar.
- **R2 (Baixo):** Adicionar `Blog` schema com artigos dinâmicos pode gerar schema inválido se campos obrigatórios (`headline`, `datePublished`) estiverem ausentes em algum post. Validar com schema.org validator.

## Dependências

- Nenhuma story bloqueante
- Epic: EPIC-SEO-2026-04

## Notas

- Não remover schemas existentes (`Organization`, `WebSite`, `SoftwareApplication`) — adicionar `Blog` ao array
- Validar schema em https://validator.schema.org após deploy (não committar URL)
- Prioridade alta: `/blog` é entrada orgânica para trial — artigos não crawleáveis = perda de tráfego SEO

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-22 | @sm | Story criada a partir do Selenium Quality Audit |
| 2026-04-22 | @po | Validação 10-point: **8/10 → GO** — adicionados Riscos, Dependências; R1 sinaliza investigação obrigatória antes do código |
