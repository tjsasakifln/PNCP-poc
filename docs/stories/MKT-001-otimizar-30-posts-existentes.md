# MKT-001 — Otimizar 30 Posts Existentes do Blog

**Status:** pending
**Priority:** P1 — Quick Win (ROI imediato sobre investimento já feito)
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** frontend/app/blog/[slug]/page.tsx, frontend/app/blog/page.tsx
**Esforço:** 2-3 dias
**Timeline:** Semana 1

---

## Contexto

O SmartLic já possui 30 posts publicados (15 B2G + 15 Consultorias), mas segundo análise do Conselho de CMOs, eles carecem de otimizações críticas para AI Overviews, conversão e SEO moderno. Estas otimizações têm ROI imediato — melhoram conteúdo já indexado sem criar nada novo.

### Evidências

- 44.2% das citações de LLMs vêm dos primeiros 30% do texto (Previsible AI Citation Study)
- FAQ Schema tem 67% de taxa de citação em AI Overviews (Zyppy Study)
- Conteúdo com 3-4 tipos de schema complementares é citado 2x mais (Schema App Research)
- Posts sem CTA forte são custo sem retorno de conversão

## Acceptance Criteria

### AC1 — FAQ Schema em todos os 30 posts

- [ ] Adicionar bloco FAQ (JSON-LD) com 5 perguntas relevantes por post
- [ ] Cada resposta deve ter entre 40-60 palavras (faixa ótima para extração por IA)
- [ ] Perguntas devem ser derivadas do conteúdo do post (não genéricas)
- [ ] Schema deve ser `FAQPage` combinado com `Article` + `BreadcrumbList`
- [ ] Validar via Google Rich Results Test

### AC2 — Front-loading de respostas

- [ ] Para cada um dos 30 posts, mover a resposta-chave (tese central) para os primeiros 200 palavras
- [ ] Manter lead paragraph como "answer block" claro e conciso (50-80 palavras)
- [ ] Não alterar o restante do conteúdo — apenas reorganizar a abertura

### AC3 — CTAs contextuais

- [ ] Inserir CTA inline no meio do post (após ~40% do conteúdo): "Teste grátis 30 dias — sem cartão de crédito"
- [ ] Inserir CTA final com botão estilizado: link direto para `/signup`
- [ ] CTA deve mencionar trial de 30 dias e "sem cartão"
- [ ] Tracking: `utm_source=blog&utm_medium=cta&utm_content=[slug]`

### AC4 — Schema markup completo

- [ ] Cada post deve ter no mínimo 3 tipos de schema: `Article` + `FAQPage` + `BreadcrumbList`
- [ ] Adicionar `Organization` schema no nível do blog
- [ ] Adicionar author credentialing: "Equipe SmartLic — Especialistas em Inteligência de Licitações Públicas"
- [ ] JSON-LD (não microdata) — formato preferido por todos os AI engines

### AC5 — Internal linking

- [ ] Cada post deve ter no mínimo 3 links internos para outros posts do blog
- [ ] Links devem ser cross-cluster (B2G → Consultoria e vice-versa) quando relevante
- [ ] Reservar 2 slots de link para futuras páginas programáticas (placeholder com `TODO`)

### AC6 — Meta tags e OG

- [ ] Verificar/atualizar meta description (150-160 chars) com keyword principal
- [ ] Verificar/atualizar OG image, OG title, OG description
- [ ] Adicionar canonical URL explícita

### AC7 — Validação via Playwright (Google Search Console + Rich Results)

- [ ] **Rich Results Test automatizado:** Script Playwright que navega para `https://search.google.com/test/rich-results`, submete cada URL dos 30 posts e verifica: 0 erros, schema `FAQPage` + `Article` + `BreadcrumbList` detectados
- [ ] **Google Search Console — Inspeção de URL:** Script Playwright que faz login no GSC (`search.google.com/search-console`), inspeciona cada um dos 30 posts via "Inspecionar URL", verifica status de indexação e solicita reindexação dos posts atualizados
- [ ] **Google Search Console — Verificar Sitemaps:** Via Playwright, confirmar que o sitemap do blog está submetido e sem erros no GSC (Sitemaps → Status)
- [ ] **Google Search Console — Core Web Vitals:** Via Playwright, navegar para relatório CWV e verificar que nenhum post do blog está em "Precisa de melhorias" ou "Ruim"
- [ ] **Relatório de validação:** Gerar arquivo `docs/validation/mkt-001-gsc-validation.md` com: URL, status indexação, schema detectado, CWV status, data da verificação

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Front-loading alterar negativamente o fluxo narrativo | Revisão editorial post-por-post; manter storytelling intacto após o lead |
| FAQ genéricas sem valor | Derivar FAQs do conteúdo real; cada FAQ deve responder uma busca real |
| CTA intrusivo prejudicar experiência de leitura | CTA inline discreto (banner leve, não popup); CTA final com design coerente |
| Schema inválido prejudicar indexação | Validar cada post no Google Rich Results Test antes de publicar |
| Reindexação demorar após alterações | Solicitar reindexação via GSC (Playwright) imediatamente após deploy |
| CWV degradar com schema/CTA extras | Verificar Core Web Vitals via GSC após deploy; rollback se degradar |

## Definição de Pronto

- [ ] 30 posts atualizados com FAQ schema + front-loading + CTAs
- [ ] Schema validado via Rich Results Test (0 erros)
- [ ] Zero regressões visuais no blog
- [ ] Validação GSC via Playwright: 30/30 posts indexados, schema detectado, CWV OK
- [ ] Relatório de validação gerado em `docs/validation/mkt-001-gsc-validation.md`
- [ ] Commit com tag `MKT-001`

## File List

- `frontend/app/blog/[slug]/page.tsx` — layout do post individual
- `frontend/app/blog/page.tsx` — listagem do blog
- `frontend/app/blog/data/` — dados dos posts (se existir)
