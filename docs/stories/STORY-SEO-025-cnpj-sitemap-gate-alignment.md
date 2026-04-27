# STORY-SEO-025: Alinhar critério `/v1/sitemap/cnpjs` com gate noindex de `/cnpj/[cnpj]`

## Status

**Withdrawn (NO-GO @po 2026-04-27)** — conflita direção produto SEO-023 (Approved); ver §"Verdict @po" abaixo

## Prioridade

P1 — Alto (781 noindex evitáveis, ~17% do total não-indexado)

## Origem

- Inspeção GSC root-cause 2026-04-27 (`docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §3.2)
- Pattern já estabelecido em `STORY-SEO-471` (Done) para `/contratos/[setor]/[uf]`

## Tipo

SEO / Data Pipeline / Backend

## Owner

@data-engineer + @dev

## Story

**As a** time de growth orgânico,
**I want** que o sitemap publique apenas CNPJs com chance real de serem indexados (alinhado ao gate `total_contratos_24m > 0`),
**so that** Google não desperdice crawl budget descobrindo 781 URLs garantidas a virar noindex.

## Problema

O endpoint backend `/v1/sitemap/cnpjs` filtra CNPJs com `≥1 bid` no datalake. Mas a página `frontend/app/cnpj/[cnpj]/page.tsx` (linha 112) aplica:

```ts
robots: { index: total_contratos_24m > 0, follow: true }
```

Mismatch: lista pode incluir CNPJ com bids mas sem contratos → página renderiza com `noindex`. Resultado: 781 URLs no cluster "Excluída pela tag noindex" do GSC (cluster real após strip de PUA artifact, ver §3.2 do brief).

Padrão paralelo: a STORY-SEO-471 já resolveu isso para `/contratos/[setor]/[uf]` mudando o endpoint sitemap para retornar união `(bids ≥ N OR contracts ≥ M)`. Replicar.

## Critérios de Aceite

- [ ] **AC1:** Endpoint `/v1/sitemap/cnpjs` retorna apenas CNPJs com `total_contratos_24m > 0` (ou parametrizar para alinhar 100% com gate de page)
- [ ] **AC2:** Implementação via RPC PostgreSQL nova ou ajuste do query atual em `pncp_supplier_contracts` (não em `pncp_raw_bids`); paralelo ao padrão SEO-471
- [ ] **AC3:** Decisão arquitetural documentada: alinhar 100% (mais conservador, perde ~bids) OU união (mantém visibilidade para CNPJs com bids ativos mesmo sem histórico). ADR ou comentário inline justificando
- [ ] **AC4:** Frontend `app/sitemap.ts` consome endpoint atualizado sem mudança (compatibilidade preserved)
- [ ] **AC5:** Validação empírica pós-deploy: ≤50 URLs `/cnpj/{cnpj14}` no cluster "noindex" do GSC em 14 dias (vs 781 atuais)
- [ ] **AC6:** Total `<url>` em `/sitemap/4.xml` ou shard que cobre `/cnpj/*` reflete redução (registrar valor antes/depois)
- [ ] **AC7:** Testes backend cobrindo o novo critério (`backend/tests/test_sitemap_cnpjs.py`)

### Anti-requisitos

- NÃO remover noindex da página `/cnpj/[cnpj]` para "casar" — gate existe por razão (thin content)
- NÃO usar `pncp_raw_bids` como filtro novo — `pncp_supplier_contracts` é a fonte alinhada ao gate

## Tasks / Subtasks

- [ ] Task 1 — Decisão arquitetural (AC: 3)
  - [ ] @architect compara opções: alinhamento 100% vs união
  - [ ] Estimar impacto: hoje sitemap publica X CNPJs, com filtro novo publica Y
  - [ ] Documentar em comentário inline ou ADR
- [ ] Task 2 — Backend RPC/query (AC: 1, 2)
  - [ ] @data-engineer cria/ajusta query em `backend/routes/sitemap_cnpjs.py` (ou equivalente)
  - [ ] Reusar padrão de SEO-471
- [ ] Task 3 — Testes (AC: 7)
  - [ ] @qa adiciona/atualiza testes em `backend/tests/test_sitemap_cnpjs.py`
- [ ] Task 4 — Deploy + medição (AC: 5, 6)
  - [ ] Deploy via @devops
  - [ ] Submeter sitemap atualizado no GSC
  - [ ] Re-medir em 14d via Playwright (mesmo protocolo do brief)

## Referência de implementação

- `backend/routes/sitemap_cnpjs.py` (verificar nome real do módulo)
- `frontend/app/sitemap.ts` linhas 104-116 (cache `_cnpjCache`)
- `frontend/app/cnpj/[cnpj]/page.tsx` linha 112 (gate `index: total_contratos_24m > 0`)
- Story de referência: `docs/stories/SEO-471-sitemap-licitacoes-indexable-v2-contratos.md`

## Riscos

- **R1 (Baixo):** Sitemap pode ficar significativamente menor — mas Google indexar 100% de N URLs é melhor que crawlar 5N e indexar N
- **R2 (Baixo):** Endpoint pode ficar mais lento com novo JOIN — coordenar com STORY-INC-001 (statement_timeout)

## Dependências

- **Bloqueada por:** STORY-INC-001 (precisa backend respondendo para validar AC1, AC5)
- **Padrão:** STORY-SEO-471 (Done) — replicar arquitetura
- **Coordena com:** STORY-SEO-001 (sitemap-4 vazio InProgress) — endpoint `/cnpj/*` provavelmente vai pra shard 4

## Verdict @po (2026-04-27)

**NO-GO — Withdrawn (conflito direção produto).**

`STORY-SEO-023` Status: **Approved** (memory `project_smartlic_onpage_pivot_2026_04_26`, "noindex tão indesejável quanto 404") estabelece direção oposta:

- SEO-023 AC2: "Cada página retorna 200 com `<meta name="robots" content="index, follow" />` (sem condicional `noindex`)" — **remover gate noindex de `/cnpj/[cnpj]`**
- SEO-023 AC3: conteúdo rico mesmo com 0 contratos (Receita Federal CNPJ API + IBGE + histórico 5 anos + educacional + relacionados)

Meu SEO-025 propõe alinhar sitemap **ao gate atual** (manter noindex condicional). Vai contra SEO-023 que **remove o gate**. Implementar SEO-025 antes de SEO-023 = trabalho que será revertido.

**Ações recomendadas:**

1. **Pull SEO-023** (Approved → Ready → InProgress) — esse é o caminho correto
2. **Após SEO-023 ship**, re-medir cluster noindex `/cnpj/{14d}` no GSC. Esperado: 781 → próximo de 0 (sem precisar mudar sitemap, porque pages deixaram de marcar noindex)
3. **Se ainda houver noindex residual após SEO-023**, criar nova story com escopo redefinido (nesse momento)

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-27 | @sm (River) | Story criada a partir do brief GSC root-cause §3.2 + S2 |
| 2026-04-27 | @po (Sarah) | **Validação 6-section: NO-GO** — conflito de direção com STORY-SEO-023 (Approved). Status: Draft → Withdrawn. Recomendação: priorizar SEO-023 puxar primeiro. |
