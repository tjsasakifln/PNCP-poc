# STORY-430: Thin Content Surgery — noindex nas Páginas Programáticas de Baixo Valor

**Priority:** P0 (blocker implícito do epic SEO — site poluído prejudica todos os ranqueamentos)
**Effort:** M (1-2 dias)
**Squad:** @dev + @devops
**Status:** Draft
**Epic:** [EPIC-SEO-ORGANIC-2026-04](EPIC-SEO-ORGANIC-2026-04.md)
**Sprint:** Sprint 1 — urgente

---

## Contexto

O Google Search Console detectou **569 páginas programáticas com status "Detectada, não indexada"** no domínio smartlic.tech (auditoria 2026-04-11). Esse status indica que o Googlebot rastreou as páginas e optou por não indexá-las — sinal de thin content ou conteúdo duplicado.

**Por que isso é urgente:** O Google aplica um **Domain Quality Score sitewide**. Ter centenas de páginas de baixa qualidade ativas deprime o score de TODO o site — inclusive artigos de blog bons e páginas de produto. Podar essas páginas é o pré-requisito para que qualquer outro conteúdo rankear melhor.

**Estrutura das páginas programáticas no SmartLic:**
- `/blog/licitacoes/[setor]/[uf]` — ~540 combinações (20 setores × 27 UFs)
- `/blog/programmatic/[setor]` — ~20 páginas
- `/blog/programmatic/[setor]/[uf]` — ~540 combinações
- `/alertas-publicos/[setor]/[uf]` — ~540 combinações
- `/contratos/[setor]` — 20 páginas
- `/contratos/[setor]/[uf]` — ~540 combinações

**Critério de thin content:** página sem dados reais (zero licitações ativas no datalake para aquela combinação setor+UF) OU conteúdo genérico sem diferencial em relação à versão nacional (setor sem UF).

**Regra de negócio para noindex:**
1. Páginas com **< 5 licitações ativas** no datalake para aquela combinação → `noindex, nofollow`
2. Páginas com conteúdo 100% gerado por template sem dado dinâmico → `noindex, nofollow`
3. Páginas que duplicam conteúdo da versão "pai" (ex: `/contratos/ti/sp` com os mesmos dados de `/contratos/ti`) → `rel=canonical` para a versão pai

**Impacto esperado:** Após noindex + canonical, crawl budget redistribuído para páginas com conteúdo real. Rankings das páginas restantes sobem 15-25% (baseado em estudos Search Engine Land 2023 sobre content pruning).

---

## Acceptance Criteria

### AC1: Inventário de páginas programáticas
- [ ] Executar query no datalake para contar licitações ativas por (setor, UF): `SELECT setor, uf, COUNT(*) FROM pncp_raw_bids WHERE is_active = true GROUP BY setor, uf`
- [ ] Identificar todas as combinações setor+UF com < 5 resultados ativos
- [ ] Documentar no PR o total de páginas que receberão noindex vs. páginas que ficam indexadas
- [ ] Resultado esperado: ~30% das combinações terão < 5 resultados (estimativa conservadora)

### AC2: Implementar lógica de noindex dinâmico nas páginas programáticas
- [ ] Em `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx`: adicionar lógica em `generateMetadata()` — se total de licitações ativas < 5 → retornar `robots: { index: false, follow: false }`
- [ ] Em `frontend/app/blog/programmatic/[setor]/[uf]/page.tsx`: mesma lógica
- [ ] Em `frontend/app/alertas-publicos/[setor]/[uf]/page.tsx`: mesma lógica
- [ ] Em `frontend/app/contratos/[setor]/[uf]/page.tsx`: mesma lógica
- [ ] O threshold (5) deve ser configurável via env var `MIN_ACTIVE_BIDS_FOR_INDEX` (default: 5)
- [ ] TypeScript compila sem erros (`npx tsc --noEmit`)

### AC3: Canonical tag para páginas com conteúdo duplicado da versão pai
- [ ] Em páginas `[setor]/[uf]` que têm conteúdo idêntico (≤10% diferença) da versão `[setor]` sem UF → adicionar `alternates: { canonical: '/blog/licitacoes/[setor]' }` no metadata
- [ ] Isso consolida link equity para a versão nacional em vez de diluir entre 27 UFs com dados insuficientes

### AC4: Remover páginas inexistentes do sitemap
- [ ] Modificar `frontend/app/sitemap.ts` para filtrar dinamicamente páginas programáticas — não incluir no sitemap combinações que teriam noindex
- [ ] Sitemap final deve conter apenas URLs que serão indexadas
- [ ] Verificar que `sitemap.ts` não excede o limite de 50.000 URLs (limite Google)
- [ ] Testar: `curl https://smartlic.tech/sitemap.xml | grep "licitacoes" | wc -l` deve reduzir vs. baseline

### AC5: Páginas que ficam indexadas recebem enriquecimento mínimo
- [ ] Páginas com ≥ 5 licitações ativas devem mostrar: (a) contagem total de licitações ativas, (b) valor médio dos contratos, (c) data da licitação mais recente — esses dados já existem no datalake
- [ ] Dados devem ser carregados server-side em `generateStaticParams` ou como RSC (não client-side fetch)
- [ ] Pelo menos 3 campos de dado real visível above-the-fold diferenciando da versão sem UF

### AC6: Validação pós-deploy via GSC
- [ ] Após deploy, inspecionar 3 URLs no GSC que deveriam ter noindex e confirmar header `X-Robots-Tag: noindex, nofollow` via DevTools → Network
- [ ] Inspecionar 3 URLs que deveriam estar indexadas e confirmar ausência de noindex
- [ ] Solicitar re-crawl do sitemap no GSC: `Sitemaps → Reenviar`

### AC7: Testes
- [ ] `npm test` passa sem regressões
- [ ] Teste unitário cobrindo a lógica de threshold: `generateMetadata` retorna `robots.index = false` quando count < MIN_ACTIVE_BIDS_FOR_INDEX
- [ ] Teste cobrindo o caso positivo: `robots.index = true` quando count ≥ threshold

---

## Scope

**IN:**
- `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx`
- `frontend/app/blog/programmatic/[setor]/[uf]/page.tsx`
- `frontend/app/alertas-publicos/[setor]/[uf]/page.tsx`
- `frontend/app/contratos/[setor]/[uf]/page.tsx`
- `frontend/app/sitemap.ts`
- Env var `MIN_ACTIVE_BIDS_FOR_INDEX`

**OUT:**
- Alteração de conteúdo dos artigos de blog manuais (73 artigos)
- Páginas de produto (`/planos`, `/features`, etc.)
- Alteração do schema do datalake
- Criação de novo conteúdo (escopo de outras stories)

---

## Dependências

- Datalake `pncp_raw_bids` operacional (confirmado: 40K+ rows ativas, ingestão 4x/dia)
- Acesso ao cliente Supabase no frontend via RSC (já existe em outras páginas do projeto)

---

## Riscos

- **Canonical incorreto:** Se a versão "pai" também tiver thin content, canonical para ela piora — verificar que a versão pai tem ≥ 10 licitações antes de usar como canonical target
- **Threshold muito alto:** MIN_ACTIVE_BIDS_FOR_INDEX = 5 pode ser conservador demais se o nicho tem volume baixo em algumas UFs. Ajustável via env.
- **Build time:** generateStaticParams para 1.000+ rotas pode aumentar build time. Mitigação: usar ISR (revalidate: 3600) em vez de static generation completa.

---

## Dev Notes

_(a preencher pelo @dev durante implementação)_

---

## Arquivos Impactados

- `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx`
- `frontend/app/blog/programmatic/[setor]/[uf]/page.tsx`
- `frontend/app/alertas-publicos/[setor]/[uf]/page.tsx`
- `frontend/app/contratos/[setor]/[uf]/page.tsx`
- `frontend/app/sitemap.ts`
- `frontend/__tests__/` (novos testes)

---

## Definition of Done

- [ ] Query confirma inventário: X páginas com noindex, Y páginas indexadas (documentado no PR)
- [ ] `npx tsc --noEmit` passa sem erros
- [ ] `npm test` passa sem regressões + novos testes AC7 passando
- [ ] 3 URLs com noindex confirmadas via DevTools/GSC Inspeção após deploy
- [ ] Sitemap resubmetido no GSC
- [ ] PR aprovado pelo @po (scope alinhado com critério de negócio)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — auditoria GSC revela 569 páginas thin content ativamente prejudicando domain quality score |
