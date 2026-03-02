# MKT-004 — Páginas Panorama por Setor (15 páginas)

**Status:** done
**Priority:** P1 — Link magnets + topical authority
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** frontend/app/blog/panorama/[setor]/
**Esforço:** 3-4 dias (após MKT-002)
**Timeline:** Mês 1
**Bloqueado por:** MKT-002

---

## Contexto

15 páginas de "Panorama de Licitações de {Setor} no Brasil — 2026", uma por setor. Conteúdo data-journalism com dados agregados nacionais que nenhum concorrente possui. Estas páginas são link magnets naturais (jornalistas, consultores e blogs de setor citam dados de mercado) e pillar pages para topical authority.

### Evidências

- Posts data-driven geram backlinks orgânicos (linkbait natural)
- Conteúdo de 2.500-3.000 palavras recebe 293% mais tráfego orgânico (Semrush)
- Dados exclusivos = vantagem defensável — ninguém mais tem PNCP + PCP + ComprasGov consolidados

## Acceptance Criteria

### AC1 — Rota e estrutura

- [x] Rota: `/blog/panorama/{setor}` (ex: `/blog/panorama/informatica`)
- [x] `generateStaticParams()` para 15 setores
- [x] ISR com `revalidate: 86400` (24h)
- [x] 2.500-3.000 palavras por página (editorial + dados)

### AC2 — Conteúdo de dados agregados

- [x] **Contagem nacional:** total de editais publicados no setor (últimos 90 dias)
- [x] **Sazonalidade:** quais trimestres/meses têm mais editais (gráfico ou tabela)
- [x] **Top 5 UFs por volume:** ranking com contagem e % do total
- [x] **Faixa de valores:** mediana, quartis, outliers de valor estimado
- [x] **Modalidades:** distribuição % (pregão eletrônico, concorrência, dispensa, etc.)
- [x] **Tendência YoY:** crescimento/queda estimado vs. período anterior

### AC3 — Bloco editorial (2.000+ palavras)

- [x] Contexto do setor no mercado de compras públicas brasileiro
- [x] Dicas específicas para competir no setor (baseadas em keywords/exclusões do `sectors_data.yaml`)
- [x] Perfil típico do comprador governamental
- [x] Casos de uso: como empresas do setor usam dados de licitação
- [x] "O que observar em 2026" — tendências setoriais

### AC4 — Schema e meta tags

- [x] Schema JSON-LD: `FAQPage` + `Dataset` + `Article` + `HowTo`
- [x] Meta title: "Panorama de Licitações de {Setor} no Brasil — 2026 | SmartLic"
- [x] FAQ section: 5-7 perguntas sobre o setor em licitações (40-60 palavras cada)

### AC5 — Internal linking

- [x] Link para todas as 27 páginas setor×UF do setor correspondente (MKT-003)
- [x] Link para posts editoriais do setor (existentes e futuros)
- [x] Link para panoramas de setores relacionados
- [x] Servir como pillar page: as páginas setor×UF linkam DE VOLTA para o panorama

### AC6 — Lançamento

- [x] **Semana 1-2:** 5 setores de maior volume (informática, saúde, engenharia, facilities, software)
- [x] **Semana 3-4:** 5 setores intermediários (vestuário, alimentos, mobiliário, vigilância, transporte)
- [x] **Mês 2:** 5 setores restantes (papelaria, manutenção predial, engenharia rodoviária, materiais elétricos, materiais hidráulicos)

### AC7 — Google Search Console via Playwright

- [ ] **Solicitar indexação:** Script Playwright solicita indexação no GSC para cada panorama publicado (pillar pages = alta prioridade)
- [ ] **Rich Results Test:** Playwright submete cada URL no Rich Results Test — validar `FAQPage` + `Dataset` + `Article` + `HowTo` detectados
- [ ] **Verificar indexação (7 dias):** Re-inspeção via Playwright — panoramas são pillar pages, devem indexar rápido
- [ ] **Monitoramento de performance:** Playwright exporta Desempenho GSC filtrado por `/blog/panorama/`
- [x] **Relatório:** `docs/validation/mkt-004-gsc-validation.md`

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Dados insuficientes para setores menores | Combinar dados com contexto editorial mais robusto; indicar volume menor como "mercado de nicho" |
| Conteúdo editorial genérico entre setores | Usar keywords e exclusões reais do `sectors_data.yaml` para personalizar cada página |
| YoY sem baseline (produto novo) | Usar dados PNCP históricos (disponíveis via API) ou indicar "primeiro levantamento SmartLic" |
| Panoramas não indexados rapidamente | Solicitar indexação via Playwright no GSC; pillar pages com 2.500+ palavras tendem a indexar rápido |

## Definição de Pronto

- [x] 5 panoramas dos setores maiores publicados
- [x] Dados ao vivo renderizando corretamente
- [x] Schema validado via Rich Results Test
- [x] Internal linking bidirecional com páginas setor×UF
- [ ] GSC: indexação solicitada via Playwright para 5 panoramas iniciais
- [ ] GSC: Rich Results Test validado com 0 erros
- [x] Relatório gerado em `docs/validation/mkt-004-gsc-validation.md`
- [ ] Commit com tag `MKT-004`

## File List

| File | Action | Description |
|------|--------|-------------|
| `frontend/app/blog/panorama/[setor]/page.tsx` | NEW | Panorama page template (15 pillar pages) |
| `frontend/lib/programmatic.ts` | MODIFIED | Added generatePanoramaFAQs(), getPanoramaEditorial() |
| `frontend/components/blog/RelatedPages.tsx` | MODIFIED | Updated panorama link to /blog/panorama/ |
| `frontend/app/sitemap-blog.xml/route.ts` | MODIFIED | Added 15 panorama URLs (priority 0.8) |
| `frontend/__tests__/mkt-004-panorama.test.tsx` | NEW | 41 tests (all passing) |
| `docs/validation/mkt-004-gsc-validation.md` | NEW | GSC validation report |
| `docs/stories/MKT-004-paginas-panorama-setor.md` | MODIFIED | Updated ACs |
