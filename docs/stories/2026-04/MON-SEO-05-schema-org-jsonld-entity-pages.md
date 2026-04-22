# MON-SEO-05: Schema.org JSON-LD Completo em Todas Páginas de Entidade

**Priority:** P2
**Effort:** S (2 dias)
**Squad:** @dev
**Status:** Draft
**Epic:** [EPIC-MON-SEO-2026-04](EPIC-MON-SEO-2026-04.md)
**Sprint:** Wave 3 (polimento final, depende MON-SEO-01/02/03)

---

## Contexto

Componente `SchemaMarkup.tsx` já existe (criado em MKT-002) mas não cobre todos os tipos necessários para rich results em:
- `/fornecedores/[cnpj]` → `Organization`, `ProfilePage`, `AggregateRating` (MON-SEO-01)
- `/categoria/[slug]` → `Dataset`, `FAQPage`, `BreadcrumbList` (MON-SEO-02)
- `/orgaos/[slug]` → `GovernmentOrganization`, `BreadcrumbList` (MON-SEO-03)

Esta story amarra todos em um componente robusto + CI validation.

---

## Acceptance Criteria

### AC1: Extensão `SchemaMarkup.tsx`

- [ ] `frontend/app/components/SchemaMarkup.tsx` aceita types adicionais:
  - `Organization`, `GovernmentOrganization`, `ProfilePage`
  - `Dataset`, `DataDownload`
  - `AggregateRating`, `Review` (futuro — sem reviews de usuário em v1)
  - `FAQPage` + `Question/Answer`
  - `BreadcrumbList`
- [ ] Props tipadas em TypeScript

### AC2: Integração em cada página

- [ ] `/fornecedores/[cnpj]`: Organization + ProfilePage + AggregateRating + BreadcrumbList
- [ ] `/categoria/[slug]`: Dataset + FAQPage (com 3-5 perguntas frequentes) + BreadcrumbList
- [ ] `/orgaos/[slug]`: GovernmentOrganization + BreadcrumbList

### AC3: CI validation

- [ ] Novo workflow `.github/workflows/schema-validation.yml`:
  - Roda em cada PR que toca páginas de entidade
  - Build + scrapea HTML + extrai JSON-LD
  - Valida contra schemas oficiais (https://validator.schema.org/ via API)
  - Falha PR se schema inválido ou campos obrigatórios ausentes

### AC4: Snapshot tests frontend

- [ ] `frontend/__tests__/schema-markup.test.tsx`:
  - Snapshot de cada page type com JSON-LD esperado
  - Valida que campos mínimos estão presentes

### AC5: Documentação

- [ ] `docs/seo/schema-org-guidelines.md` com:
  - Tipos cobertos
  - Como adicionar novo tipo
  - Checklist de rich results (Knowledge Panel, FAQ snippet, Dataset panel)

---

## Scope

**IN:**
- Extensão componente
- Integração nas 3 páginas
- CI validation workflow
- Snapshot tests
- Documentação

**OUT:**
- Rich Results para `Article`, `Recipe`, `Event` — não aplicável ao produto
- hreflang — v2

---

## Dependências

- MON-SEO-01, MON-SEO-02, MON-SEO-03 (páginas existem primeiro)

---

## Riscos

- **Schema validator.schema.org rate limit:** CI cache de respostas + skip em PRs sem mudanças em pages

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `frontend/app/components/SchemaMarkup.tsx` (estender)
- `frontend/app/fornecedores/[cnpj]/page.tsx` (usar componente)
- `frontend/app/categoria/[slug]/page.tsx` (usar componente)
- `frontend/app/orgaos/[slug]/page.tsx` (usar componente)
- `.github/workflows/schema-validation.yml` (novo)
- `frontend/__tests__/schema-markup.test.tsx` (estender)
- `docs/seo/schema-org-guidelines.md` (novo)

---

## Definition of Done

- [ ] Todas as 3 páginas de entidade têm JSON-LD completo
- [ ] Google Rich Results Test valida 10 samples (passa 100%)
- [ ] CI workflow ativo
- [ ] Documentação publicada

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — polimento schema.org para rich results |
