# STORY-SEO-023: Programmatic entity content enrichment (substituir zero-data por valor real)

## Status

Approved

## Story

**As a** visitante chegando em `/cnpj/{X}`, `/orgaos/{Y}`, `/municipios/{Z}` ou `/fornecedores/{W}` via SEO long-tail,
**I want** página rica de conteúdo útil mesmo quando a entidade tem poucos contratos ativos no momento — não 404 nem `noindex`,
**so that** eu encontre valor real (informação pública contextual + histórico + orientação de domínio + relacionados) e o Google indexe a página com sinal positivo de qualidade.

> **Diretriz do produto (2026-04-26):** `noindex` é tão indesejável quanto 404. Toda URL programmatic deve ter conteúdo real, atualizado e de valor máximo ao visitante. Volume de licitações ativas no momento não pode ser gate de indexação — outras dimensões de valor sempre existem.

## Acceptance Criteria

1. Rotas afetadas: `frontend/app/cnpj/[cnpj]/page.tsx`, `orgaos/[slug]/page.tsx`, `municipios/[slug]/page.tsx`, `fornecedores/[cnpj]/page.tsx`.
2. Cada página retorna 200 com `<meta name="robots" content="index, follow" />` (sem condicional `noindex`); apenas slugs estruturalmente inválidos (formato CNPJ malformado, UF inexistente) seguem 404.
3. **Conteúdo mínimo garantido por página, mesmo quando contratos/bids ativos = 0:**
   - **Identificação pública da entidade** (nome oficial, razão social, CNAE primário, endereço, data de abertura, esfera/poder se órgão público) — fontes: Receita Federal CNPJ API + IBGE + Lei de Acesso (TBD lib via @architect)
   - **Resumo descritivo** ≥150 palavras gerado a partir de dados estruturados (sem LLM hallucination — usar templates parametrizados com dados verificados)
   - **Histórico ampliado**: estender janela para últimos 5 anos (não só 24m) — se ainda zero, mostrar "Nenhuma licitação registrada nos últimos 5 anos. Veja entidades similares com atividade recente: ..."
   - **Conteúdo educacional contextual**: bloco fixo de orientação prática (por tipo de entidade: "Como participar de licitações de {órgão}", "Como vender para {município}", "Histórico de contratação no setor de {CNAE}") — copy real produzida por @ux-design-expert / @analyst, não Lorem
   - **Entidades relacionadas**: lista de 5-10 similares (mesmo CNAE, mesma esfera, mesma UF) com dados ativos — fonte de internal linking + retenção
   - **Schema.org JSON-LD apropriado** (Organization, GovernmentOrganization, Place — dependendo do tipo)
4. Conteúdo é cacheado/ISR com `revalidate=86400` (24h) — refresh diário sem custo de geração on-demand.
5. Quando dados ativos existem (≥1 contrato/bid), conteúdo educacional permanece (não é substituído) — page expande com seção dinâmica de licitações/contratos atuais.
6. `generateMetadata` produz `title`, `description` e canonical sempre úteis (não placeholder); description ≥120 chars, baseada em dados estruturados.
7. Sweep grep não retorna `notFound()` em entity pages a menos que slug seja estruturalmente inválido (CNPJ regex falha, UF não em `BRAZILIAN_UFS`, slug com chars proibidos). Decisão documentada por arquivo.
8. Lighthouse SEO score ≥90 e Content score (palavras úteis) acima de threshold em 5 amostras: 2 entidades com dados ativos + 3 entidades sem dados ativos atuais.
9. GSC pós-deploy: zero "Excluded by 'noindex'" em entity URLs próprias; zero "Not found 404" em CNPJ/slug válido. Crawl stats refletem páginas indexáveis com conteúdo.
10. Quando fontes externas (Receita Federal, IBGE) falham/timeout: graceful degradation com cache stale ou conteúdo educacional puro — nunca 404, nunca noindex, nunca página vazia.

## Tasks / Subtasks

- [ ] Task 1 — Decisão de fontes externas (AC: 3, 10)
  - [ ] @architect ADR `docs/adr/NNN-entity-enrichment-data-sources.md`
  - [ ] Avaliar: Receita Federal CNPJ Pública API (rate limits, cache, custo), IBGE municipios API, BrasilAPI, alternativas
  - [ ] Cache strategy (Supabase table `entity_external_data` ou Redis com TTL longo)
- [ ] Task 2 — Backend enrichment service (AC: 3, 10)
  - [ ] @data-engineer + @dev: serviço backend que ingere e cacheia dados externos por entidade (ARQ job + table dedicada)
  - [ ] Endpoint `/v1/entity/{type}/{slug}/enrichment` retorna payload pronto para SSR
  - [ ] Fallback graceful em falha de upstream
- [ ] Task 3 — Conteúdo educacional reusável (AC: 3, 5)
  - [ ] @ux-design-expert + @analyst produzem 4 blocos educacionais (1 por tipo: cnpj/orgao/municipio/fornecedor)
  - [ ] Componente `<EducationalContext type={...} entity={...} />` parametrizado
  - [ ] Sem Lorem; sem fabricação de fatos
- [ ] Task 4 — Histórico ampliado (AC: 3)
  - [ ] Queries Supabase aceitam window param (default 5 anos)
  - [ ] @data-engineer revisa índices (memória `reference_smartlic_baseline_2026_04_24.md` lembra que purge 400d limita raw_bids — para histórico longo, usar `supplier_contracts` ou outra fonte)
- [ ] Task 5 — Entidades relacionadas (AC: 3)
  - [ ] RPC `get_similar_entities(type, slug, limit)`
  - [ ] Componente `<RelatedEntities />` reusável
- [ ] Task 6 — Refator das 4 entity pages (AC: 1, 2, 5, 6, 7)
  - [ ] Remover `notFound()` exceto para slugs estruturalmente inválidos
  - [ ] Remover lógica `MIN_ACTIVE_BIDS_FOR_INDEX` que produz `noindex`
  - [ ] Layout integrando: identificação + resumo + educacional + histórico + relacionados + (se houver) licitações ativas
  - [ ] generateMetadata sempre produtivo
- [ ] Task 7 — Validação CWV + Content (AC: 8)
  - [ ] Lighthouse runs em 5 URLs amostra
  - [ ] Manual content audit: ≥300 palavras úteis por página em qualquer cenário
- [ ] Task 8 — GSC monitoring (AC: 9)
  - [ ] Baseline antes do deploy
  - [ ] Re-medição em 14 e 28 dias

## Dev Notes

**Plano:** Wave 2, story 5 — **REWRITTEN 2026-04-26 após feedback do usuário**: filosofia mudou de "gate noindex se thin" para "garantir conteúdo real e valor sempre". Esta é a abordagem correta para SEO sustentável (Google E-E-A-T + Helpful Content System favorecem páginas reais com valor único, penalizam thin content E penalizam mascarar problema com noindex).

**Trade-offs explícitos:**
- Custo: integração com fontes externas (Receita Federal CNPJ Pública é gratuita mas tem rate limit; alternativas pagas TBD em ADR Task 1)
- Complexidade: ~+1 sprint vs simples noindex toggle
- Recompensa: páginas se tornam ativos SEO permanentes em vez de "buracos" indexados ou non-indexed
- Risco mitigado: se enriquecimento falha em runtime, fallback é conteúdo educacional + identificação básica — nunca 404 nem noindex

**Audit evidence (mantém):**
- `frontend/app/cnpj/[cnpj]/page.tsx:59-60`, `orgaos/[slug]/page.tsx:130-132` chamam `notFound()` quando profile vazio — incorreto
- `orgaos/[slug]:82` tem `MIN_ACTIVE_BIDS_FOR_INDEX` aplicando `noindex` — também incorreto sob nova diretriz; a lógica de threshold é descartada

**Referência externa:**
- Google Helpful Content System: páginas devem ser made-for-people, não made-for-search
- E-E-A-T: experiência, expertise, autoridade, trust — conteúdo educacional + dados verificados estruturados sinaliza ambas

**Files mapeados:**
- `frontend/app/cnpj/[cnpj]/page.tsx`, `orgaos/[slug]/page.tsx`, `municipios/[slug]/page.tsx`, `fornecedores/[cnpj]/page.tsx` (refator)
- `frontend/components/EducationalContext.tsx`, `RelatedEntities.tsx`, `EntityIdentification.tsx` (criar)
- `backend/services/entity_enrichment.py` (criar)
- `backend/jobs/cron/entity_enrichment_refresh.py` (criar — ARQ cron)
- Supabase migration: nova table `entity_external_data` (TBD com @data-engineer)
- `docs/adr/NNN-entity-enrichment-data-sources.md` (criar)

### Testing

- Unit: render entity page com fixture de profile vazio → conteúdo mínimo presente
- Integration: backend enrichment com upstream Receita mockado (sucesso + timeout + 404)
- E2E: Playwright crawl 10 URLs entity (mix com/sem dados) → todas 200 + meta robots index
- SEO: Lighthouse SEO + manual word count

## Dependencies

- **Bloqueado por:** STORY-SEO-020 (sitemap funcionando)
- **Bloqueia:** STORY-SEO-024 reusa enrichment pattern (mesma diretriz para novos templates)
- **Risco:** dependência externa (Receita Federal API uptime); mitigado por cache + fallback educacional

## Owners

- Primary: @architect (ADR + design enrichment), @dev (impl), @data-engineer (DB + cache)
- Content: @ux-design-expert + @analyst (conteúdo educacional real, não Lorem)
- Quality: @qa (content audit + CWV)

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm — gating noindex pattern | @sm (River) |
| 2026-04-26 | 0.2 | REWRITE: noindex igualmente indesejável; páginas devem ter conteúdo real e valor sempre (feedback usuário) | @sm (River) |
