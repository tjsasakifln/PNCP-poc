# STORY-DISC-002: [SPIKE] Localizar componente fonte do JSON-LD `@type: "Dataset"`

## Status

**Withdrawn (NO-GO @po 2026-04-27)** — discovery resolvida em 1 grep durante validação; ver §"Verdict @po"

## Prioridade

P3 — Baixo (pré-requisito de STORY-SEO-029)

## Tipo

Spike / Discovery

## Origem

- Inspeção GSC root-cause 2026-04-27 (`docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §5.1 + D2)
- Pré-requisito de STORY-SEO-029

## Owner

@analyst

## Story

**As a** time tentando corrigir 4 warnings em schema Dataset,
**I want** localizar exatamente quais componentes/páginas emitem JSON-LD `@type: "Dataset"`,
**so that** STORY-SEO-029 possa editar o local correto sem hunt-and-peck.

## Problema

GSC reporta 7 datasets válidos + 1-4 com warnings (license, description, contentUrl, creator faltantes em diferentes páginas). Localização do schema é desconhecida — provavelmente `app/dados/page.tsx` ou `app/observatorio/*/page.tsx` mas precisa confirmação empírica.

## Critérios de Aceite

- [ ] **AC1:** Output: documento `docs/spikes/2026-04-dataset-schema-locations.md` listando:
  - Componente(s) que emite(m) JSON-LD `@type: "Dataset"` (paths e linhas)
  - Páginas que renderizam esses componentes (rotas afetadas)
  - Mapeamento: cada warning específico → página específica → componente fonte
- [ ] **AC2:** Grep extensivo: `grep -rn '"@type": "Dataset"' frontend/` + `grep -rn '"Dataset"' frontend/app/ frontend/components/`
- [ ] **AC3:** Para cada componente identificado, capturar shape atual do JSON-LD (qual campos presentes, quais faltam)
- [ ] **AC4:** Confirmar via curl produção (quando backend volta após STORY-INC-001):
  - `curl https://smartlic.tech/dados | grep -A30 'application/ld+json'`
  - `curl https://smartlic.tech/observatorio/* | grep -A30 'application/ld+json'`
- [ ] **AC5:** Recomendação para STORY-SEO-029: lista exata de arquivos a editar + diff sketch dos campos a adicionar

### Anti-requisitos

- NÃO implementar fix nesse spike — discovery only
- NÃO assumir uma localização sem grep + curl confirmation

## Tasks / Subtasks

- [ ] Task 1 — Grep frontend (AC: 2)
- [ ] Task 2 — Mapear páginas (AC: 1, 3)
- [ ] Task 3 — Confirmar produção (AC: 4)
  - [ ] **Parcialmente bloqueada por STORY-INC-001** se páginas dependem de fetch backend
- [ ] Task 4 — Recomendação (AC: 5)

## Referência de materiais

- Schema.org Dataset: https://schema.org/Dataset
- `frontend/app/dados/` (suspeitar)
- `frontend/app/observatorio/` (suspeitar)
- Brief: `docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §5.1

## Riscos

- **R1 (Baixo):** Spike curto, baixa complexidade. Se grep não encontra nada, escalar para @dev verificar se schema é gerado dinamicamente em runtime via lib

## Dependências

- **Parcialmente bloqueada por STORY-INC-001** — apenas Task 3
- **Bloqueia STORY-SEO-029**

## Verdict @po (2026-04-27)

**NO-GO — Withdrawn (overengineering, resolvido inline em 1 grep).**

Durante validação @po executei `grep -rn '"@type": "Dataset"' frontend/app frontend/components` que retornou:

```
frontend/app/licitacoes/[setor]/page.tsx:583:    "@type": "Dataset",
```

**Único emissor**. Spike de 80 linhas, 4 ACs, 4 Tasks não justifica 1 grep que rodou em <1s. IDS Article IV-A: CREATE rejeitado quando ADAPT existente (mover discovery inline em STORY-SEO-029) ou simples grep resolve.

**Ações:**

1. STORY-SEO-029 atualizada (Verdict @po) com Task 1 reformulada para incluir grep exhaustivo + path concreto (`frontend/app/licitacoes/[setor]/page.tsx:583`)
2. Esta story arquivada como Withdrawn

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-27 | @sm (River) | Spike criado a partir do brief GSC root-cause §5.1 + D2 |
| 2026-04-27 | @po (Sarah) | **Validação 6-section: NO-GO** — discovery resolvida em 1 grep durante validação (`frontend/app/licitacoes/[setor]/page.tsx:583`). Status: Draft → Withdrawn. Conteúdo subsumido em STORY-SEO-029. |
