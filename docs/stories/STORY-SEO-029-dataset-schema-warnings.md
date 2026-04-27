# STORY-SEO-029: Corrigir 4 warnings em schema Dataset (GSC > Melhorias > Conjuntos de dados)

## Status

**Ready (GO @po 2026-04-27 com nota)** — promovida Draft → Ready; bloqueio DISC-002 desnecessário (resolvido em 1 grep)

## Prioridade

P3 — Baixo (warnings, não erros; impacto SEO indireto via rich results)

## Origem

- Inspeção GSC root-cause 2026-04-27 (`docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §5.1 + S6)

## Tipo

SEO / Structured Data

## Owner

@dev

## Story

**As a** time SmartLic com schema Dataset publicado para alimentar Google Dataset Search e rich results,
**I want** que os 4 campos faltantes (license, description, contentUrl, creator) sejam preenchidos no JSON-LD,
**so that** páginas com Dataset schema sejam elegíveis para destaque em Google Dataset Search.

## Problema

GSC > Melhorias > Conjuntos de dados reporta 4 warnings:

| Warning | Páginas afetadas |
|---------|-----------------|
| Campo `description` ausente | 1 |
| Campo `license` ausente | **4** (maior) |
| Campo `contentUrl` ausente (em `distribution`) | 1 |
| Campo `creator` ausente | 1 |

Localização do schema **a confirmar via STORY-DISC-002** (spike discovery). Provavelmente em `app/dados/page.tsx` ou `app/observatorio/*/page.tsx`.

## Critérios de Aceite

- [ ] **AC1:** Lista exata de páginas afetadas + componente fonte do JSON-LD identificada (output de STORY-DISC-002)
- [ ] **AC2:** Campo `description` adicionado: descrição substantiva (≥50 caracteres) explicando o conjunto de dados (origem PNCP, periodicidade, escopo)
- [ ] **AC3:** Campo `license` adicionado: URL canônica da licença usada (ex: `https://creativecommons.org/licenses/by-sa/4.0/`) — confirmar com legal/PO qual licença se aplica aos dados PNCP que o SmartLic agrega
- [ ] **AC4:** Campo `contentUrl` adicionado dentro de `distribution`: URL onde o dataset pode ser baixado (ex: endpoint export CSV/JSON)
- [ ] **AC5:** Campo `creator` adicionado: `{ "@type": "Organization", "name": "SmartLic / CONFENGE Avaliacoes e Inteligencia Artificial LTDA", "url": "https://smartlic.tech" }`
- [ ] **AC6:** Validação via Google Rich Results Test (https://search.google.com/test/rich-results) — 0 warnings após fix
- [ ] **AC7:** Pós-deploy: GSC > Melhorias > Conjuntos de dados mostra 0 warnings em 30 dias
- [ ] **AC8:** Snapshot de teste em `frontend/__tests__/dataset-schema.test.ts` validando os 4 campos presentes

### Anti-requisitos

- NÃO inventar metadata (campos vazios ou placeholder Lorem) — Google penaliza
- NÃO usar licença permissiva (MIT, etc.) sem confirmar com legal/PO — dados PNCP têm restrições governamentais

## Tasks / Subtasks

- [ ] Task 1 — Discovery (AC: 1)
  - [ ] **Bloqueada por STORY-DISC-002** — esperar output
- [ ] Task 2 — Conteúdo (AC: 2, 3, 4, 5)
  - [ ] @analyst ou @po confirma licença a usar
  - [ ] @dev preenche os 4 campos no componente JSON-LD identificado
- [ ] Task 3 — Testes (AC: 8)
  - [ ] @qa adiciona snapshot de teste
- [ ] Task 4 — Validação (AC: 6, 7)
  - [ ] Rich Results Test antes do deploy
  - [ ] Re-medir GSC em 30d

## Referência de implementação

- (a confirmar via STORY-DISC-002)
- Schema.org Dataset: https://schema.org/Dataset
- Google guidelines: https://developers.google.com/search/docs/appearance/structured-data/dataset

## Riscos

- **R1 (Baixo):** Campo `license` errado pode ter implicação legal — escalar PO se incerteza
- **R2 (Baixo):** `contentUrl` requer endpoint exposto — coordenar com backend se ainda não existe

## Dependências

- **Bloqueada por:** STORY-DISC-002 (discovery do componente fonte)
- **Não bloqueada por STORY-INC-001** — apenas adição de metadata estática

## Verdict @po (2026-04-27)

**GO — Ready (6/6 sections PASS), com discovery resolvido inline.**

| Section | Status | Notas |
|---------|--------|-------|
| 1. Goal & Context Clarity | PASS | 4 warnings GSC concretos; valor (Google Dataset Search elegibilidade) explícito |
| 2. Technical Implementation Guidance | PASS | Schema.org + Google guidelines linkados |
| 3. Reference Effectiveness | PASS | Brief §5.1 |
| 4. Self-Containment | PASS | Conteúdo do JSON-LD especificado por campo |
| 5. Testing Guidance | PASS | AC6 (Rich Results Test) + AC7 (GSC pós-deploy) + AC8 (snapshot test) |
| 6. CodeRabbit Integration | N/A | Não configurado |

**Discovery consolidada:** validação @po executou `grep -rn '"@type": "Dataset"' frontend/app frontend/components` retornou **`frontend/app/licitacoes/[setor]/page.tsx:583`** como único emissor de schema Dataset. STORY-DISC-002 (bloqueador original) **não é mais necessária como spike separada** — discovery resolvida em 1 linha.

**Mudança recomendada:**
- Remover Task 1 ("Bloqueada por STORY-DISC-002") e substituir por: Task 1 — Validar exhaustivamente outros emissores via grep; mapear quais `[setor]` específicos disparam cada warning (license/description/contentUrl/creator). Atualizar AC1 com path concreto: `frontend/app/licitacoes/[setor]/page.tsx` linha 583+.

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-27 | @sm (River) | Story criada a partir do brief GSC root-cause §5.1 + S6 |
| 2026-04-27 | @po (Sarah) | **Validação 6-section: 6/6 PASS → GO**. Status: Draft → Ready. Discovery DISC-002 resolvida inline (grep apontou `frontend/app/licitacoes/[setor]/page.tsx:583`). Remover bloqueio DISC-002. |
