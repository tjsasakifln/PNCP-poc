# SEO-479: Fix meta title > 60 chars e description > 160 chars

**Status:** Ready
**Origem:** Selenium Quality Audit — test_seo_snapshot_audit (2026-04-22)
**Epic:** EPIC-SEO-2026-04
**Prioridade:** P2 — Médio (impacto direto em CTR no SERP)
**Complexidade:** S (Small)
**Sprint:** SEO-sprint-atual
**Owner:** @dev
**Tipo:** Fix SEO

---

## Problema

Audit Selenium detectou 4 páginas com `<title>` acima do limite de 60 chars (Google trunca no SERP) e 1 página com `<meta description>` acima de 160 chars:

| Página | Title atual | Chars | Limite |
|--------|-------------|-------|--------|
| `/fornecedores` | — | 64 | 60 |
| `/sobre` | — | 66 | 60 |
| `/planos` | — | 76 | 60 |
| `/features` | — | 67 | 60 |

| Página | Description | Chars | Limite |
|--------|-------------|-------|--------|
| `/sobre` | — | 178 | 160 |

Títulos truncados no Google perdem keyword de cauda e reduzem CTR orgânico.
Description truncada corta a CTA da frase, reduzindo click-through.

---

## Critérios de Aceite

### Títulos (AC1–AC4)

- [ ] **AC1:** `/fornecedores` — title ≤ 60 chars, mantendo keyword principal "fornecedores" e "licitações"
- [ ] **AC2:** `/sobre` — title ≤ 60 chars, mantendo "SmartLic" e contexto B2G
- [ ] **AC3:** `/planos` — title ≤ 60 chars, incluindo sinal de preço/trial se couber
- [ ] **AC4:** `/features` — title ≤ 60 chars, mantendo keyword de funcionalidade

### Description (AC5)

- [ ] **AC5:** `/sobre` — description entre 120–160 chars, terminando com frase completa (não truncada)

### Validação (AC6–AC7)

- [ ] **AC6:** Rodar `pytest tests/selenium/tests/test_public_seo.py::TestPublicPagesSEO::test_seo_snapshot_audit -v` — todos os 9 snapshots passam sem insight SEO de title/description
- [ ] **AC7:** Verificar via `curl -s https://smartlic.tech/<path> | grep -i "<title>"` que mudanças chegaram em produção

---

## Arquivos a modificar

- `frontend/app/fornecedores/page.tsx` — `metadata.title` / `metadata.description`
- `frontend/app/sobre/page.tsx` — `metadata.title` / `metadata.description`
- `frontend/app/planos/page.tsx` — `metadata.title`
- `frontend/app/features/page.tsx` — `metadata.title`

---

## Riscos

- **R1 (Baixo):** Novo título mais curto pode perder keyword de cauda secundária — mitigar priorizando keyword principal antes de cortar
- **R2 (Baixo):** Google pode ter indexado o título antigo; mudança leva 1–4 semanas para propagar no GSC — não é regressão, é comportamento normal

## Dependências

- Nenhuma story bloqueante
- Epic: EPIC-SEO-2026-04

## Notas

- Não alterar conteúdo visual da página, apenas metadados `export const metadata`
- Testar que mudança não quebra CI de `api-types-check.yml` (sem mudança de schema)
- Limites: title 50–60 chars, description 120–160 chars (range ideal para desktop e mobile SERP)

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-22 | @sm | Story criada a partir do Selenium Quality Audit |
| 2026-04-22 | @po | Validação 10-point: **8/10 → GO** — adicionados Riscos, Dependências e epic link |
