# SEO Specialist — Overlay SmartLic

Overlay para agente principal do aiox-seo quando aplicado ao inbound orgânico B2G do SmartLic.

## Antes de propor SEO action

1. Ler `squads/aiox-seo/data/supplier-contracts-schema.md` — estrutura do dataset
2. Ler `squads/_shared/domain-glossary.md` — terminologia B2G
3. Verificar `frontend/app/observatorio/` e `frontend/app/contratos-*/` — existing pages
4. Rodar rápida validação: `curl https://smartlic.tech/sitemap.xml | head -50`

## Priorização B2G-specific

### Quick wins (faça primeiro)

1. **Gerar 1000 pages de top CNPJs por volume de contratos** — cada page /fornecedores/[cnpj]
2. **Gerar 500 pages de top órgãos** — cada page /orgaos/[cnpj]
3. **Sitemap XML estruturado** — delegar atualização diária (cron)
4. **JSON-LD em páginas existentes** — delegate via PR incremental

### Mid-term (mês 2-3)

1. **Hub pages por setor × UF** (15 × 27 = 405 pages, mas filtrar top ~100 com volume real)
2. **LLM-generated narrative summaries** por órgão/fornecedor (caching agressivo — não re-gerar)
3. **Internal linking graph** (cada contrato linka órgão + fornecedor + setor relacionado)

### Long-term (mês 4+)

1. **Topical authority** via blog posts analíticos (+ supplier_contracts data viz)
2. **Backlinks strategy** (parcerias com FGV, consultorias B2G)
3. **Programmatic featured snippets** (structure data otimizada para respostas diretas)

## Checklist técnico por page criada

- [ ] `generateMetadata()` com title + description únicos
- [ ] Canonical URL declarada (sem trailing slash inconsistente)
- [ ] OG image gerada (thumbnail com key data do contrato/órgão)
- [ ] JSON-LD apropriado (GovernmentService / Organization / Breadcrumb)
- [ ] Internal links para ≥3 páginas relacionadas
- [ ] Alt text em todas imagens/gráficos
- [ ] Breadcrumbs navegáveis
- [ ] Mobile-first (Tailwind breakpoints validados)
- [ ] LCP <2.5s (Lighthouse CI ou Vercel Speed Insights)
- [ ] Page não bloqueia indexação (`<meta name="robots">` ausente ou `index,follow`)

## Data constraints B2G

- **NUNCA** inventar fato sobre CNPJ/órgão — fact-check via supplier_contracts antes
- Se dado é incompleto: mostrar "dados oficiais parciais" em vez de esconder
- **LGPD-aware**: não agregar dados pessoais (CPF). CNPJ é público por lei.
- **Dataset staleness**: supplier_contracts é ingerido 3x/sem. Pages devem mostrar "atualizado em YYYY-MM-DD".

## Coexistência com páginas manuais existentes

`frontend/app/contratos-*/` tem ~30-50 posts manuais de blog. Páginas programmatic NÃO devem:
- Ter URL pattern que colide com manuais
- Duplicar conteúdo editorial
- Ofuscar páginas manuais no sitemap

Solução: usar prefix distinto (`/fornecedores/`, `/orgaos/`, `/observatorio/contratos/`) vs `/contratos/` (mantém manuais).

## Observabilidade

- **Search Console**: verificar semanalmente impressões + CTR por template
- **Vercel/Google Analytics**: pages/session + bounce rate por template
- **Sentry**: 404s em pages programmatic → ajustar fallback
- **Metric Prometheus** (se aplicável): `smartlic_seo_programmatic_pages_total`

## Handoff

- Delegar a `aiox-apex` se page precisa refactor de arquitetura (SSR, caching strategy)
- Delegar a `aiox-deep-research` se precisa validar claim quantitativa com dataset
- Escalate @devops se mudança toca `robots.txt`, `sitemap.xml` routing, ou CDN/Next config
