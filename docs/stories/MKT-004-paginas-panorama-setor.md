# MKT-004 — Páginas Panorama por Setor (15 páginas)

**Status:** pending
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

- [ ] Rota: `/blog/panorama/{setor}` (ex: `/blog/panorama/informatica`)
- [ ] `generateStaticParams()` para 15 setores
- [ ] ISR com `revalidate: 86400` (24h)
- [ ] 2.500-3.000 palavras por página (editorial + dados)

### AC2 — Conteúdo de dados agregados

- [ ] **Contagem nacional:** total de editais publicados no setor (últimos 90 dias)
- [ ] **Sazonalidade:** quais trimestres/meses têm mais editais (gráfico ou tabela)
- [ ] **Top 5 UFs por volume:** ranking com contagem e % do total
- [ ] **Faixa de valores:** mediana, quartis, outliers de valor estimado
- [ ] **Modalidades:** distribuição % (pregão eletrônico, concorrência, dispensa, etc.)
- [ ] **Tendência YoY:** crescimento/queda estimado vs. período anterior

### AC3 — Bloco editorial (2.000+ palavras)

- [ ] Contexto do setor no mercado de compras públicas brasileiro
- [ ] Dicas específicas para competir no setor (baseadas em keywords/exclusões do `sectors_data.yaml`)
- [ ] Perfil típico do comprador governamental
- [ ] Casos de uso: como empresas do setor usam dados de licitação
- [ ] "O que observar em 2026" — tendências setoriais

### AC4 — Schema e meta tags

- [ ] Schema JSON-LD: `FAQPage` + `Dataset` + `Article` + `HowTo`
- [ ] Meta title: "Panorama de Licitações de {Setor} no Brasil — 2026 | SmartLic"
- [ ] FAQ section: 5-7 perguntas sobre o setor em licitações (40-60 palavras cada)

### AC5 — Internal linking

- [ ] Link para todas as 27 páginas setor×UF do setor correspondente (MKT-003)
- [ ] Link para posts editoriais do setor (existentes e futuros)
- [ ] Link para panoramas de setores relacionados
- [ ] Servir como pillar page: as páginas setor×UF linkam DE VOLTA para o panorama

### AC6 — Lançamento

- [ ] **Semana 1-2:** 5 setores de maior volume (informática, saúde, engenharia, facilities, software)
- [ ] **Semana 3-4:** 5 setores intermediários (vestuário, alimentos, mobiliário, vigilância, transporte)
- [ ] **Mês 2:** 5 setores restantes (papelaria, manutenção predial, engenharia rodoviária, materiais elétricos, materiais hidráulicos)

### AC7 — Google Search Console via Playwright

- [ ] **Solicitar indexação:** Script Playwright solicita indexação no GSC para cada panorama publicado (pillar pages = alta prioridade)
- [ ] **Rich Results Test:** Playwright submete cada URL no Rich Results Test — validar `FAQPage` + `Dataset` + `Article` + `HowTo` detectados
- [ ] **Verificar indexação (7 dias):** Re-inspeção via Playwright — panoramas são pillar pages, devem indexar rápido
- [ ] **Monitoramento de performance:** Playwright exporta Desempenho GSC filtrado por `/blog/panorama/`
- [ ] **Relatório:** `docs/validation/mkt-004-gsc-validation.md`

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Dados insuficientes para setores menores | Combinar dados com contexto editorial mais robusto; indicar volume menor como "mercado de nicho" |
| Conteúdo editorial genérico entre setores | Usar keywords e exclusões reais do `sectors_data.yaml` para personalizar cada página |
| YoY sem baseline (produto novo) | Usar dados PNCP históricos (disponíveis via API) ou indicar "primeiro levantamento SmartLic" |
| Panoramas não indexados rapidamente | Solicitar indexação via Playwright no GSC; pillar pages com 2.500+ palavras tendem a indexar rápido |

## Definição de Pronto

- [ ] 5 panoramas dos setores maiores publicados
- [ ] Dados ao vivo renderizando corretamente
- [ ] Schema validado via Rich Results Test
- [ ] Internal linking bidirecional com páginas setor×UF
- [ ] GSC: indexação solicitada via Playwright para 5 panoramas iniciais
- [ ] GSC: Rich Results Test validado com 0 erros
- [ ] Relatório gerado em `docs/validation/mkt-004-gsc-validation.md`
- [ ] Commit com tag `MKT-004`
