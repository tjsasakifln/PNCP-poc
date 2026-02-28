# MKT-005 — Páginas Programáticas por Cidade (Top 100)

**Status:** pending
**Priority:** P2 — Cauda longa geográfica
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** frontend/app/blog/licitacoes/cidade/[cidade]-[uf]/
**Esforço:** 3-4 dias (após MKT-002)
**Timeline:** Mês 2-3
**Bloqueado por:** MKT-002

---

## Contexto

Páginas por cidade capturam buscas hiper-locais como "licitações em Curitiba" ou "editais abertos em Belo Horizonte". O Brasil tem 5.570 municípios, mas as 100 maiores cidades concentram a maioria das buscas e do volume de licitações. Lançamento faseado: top 100 cidades.

### Evidências

- Buscas locais ("licitações em [cidade]") têm alta intenção comercial
- SEO local é menos competitivo que termos nacionais
- Zapier provou: cada combinação de variáveis captura cauda longa específica

## Acceptance Criteria

### AC1 — Rota e estrutura

- [ ] Rota: `/blog/licitacoes/cidade/{slug}` (ex: `/blog/licitacoes/cidade/curitiba-pr`)
- [ ] Slug: `{cidade-normalizada}-{uf}` (lowercase, sem acentos, hífen)
- [ ] Lista das top 100 cidades por população (fonte IBGE)
- [ ] ISR com `revalidate: 86400` (24h)

### AC2 — Conteúdo de cada página

- [ ] **H1:** "Licitações em {Cidade}/{UF} — Editais Abertos {Ano}"
- [ ] **Dados ao vivo:** contagem editais na cidade, órgãos compradores frequentes (top 5), valores médios
- [ ] **Setores mais ativos na cidade:** distribuição % por setor
- [ ] **Bloco editorial** (300+ palavras): perfil de compras públicas da cidade, dicas para fornecedores locais
- [ ] **FAQ:** 5 perguntas sobre licitações na cidade

### AC3 — Schema e meta tags

- [ ] Schema JSON-LD: `FAQPage` + `LocalBusiness` + `BreadcrumbList`
- [ ] Meta title: "Licitações em {Cidade}/{UF} — Editais Abertos {Ano} | SmartLic"
- [ ] Canonical URL, OG tags com cidade no título

### AC4 — Internal linking

- [ ] Link para página setor×UF da UF correspondente
- [ ] Link para cidades da mesma UF (vizinhas)
- [ ] Link para panorama do setor mais ativo na cidade

### AC5 — Lançamento faseado

- [ ] **Fase 1 (Mês 2):** 27 capitais estaduais
- [ ] **Fase 2 (Mês 3):** 73 cidades com +300k habitantes
- [ ] **Fase 3 (Mês 4+):** Expandir para top 200-500 conforme demanda

### AC6 — Google Search Console via Playwright

- [ ] **Solicitar indexação (capitais):** Script Playwright solicita indexação no GSC para as 27 URLs de capitais da Fase 1
- [ ] **Verificar indexação (14 dias depois):** Playwright re-inspeciona e gera relatório: indexada/pendente, schema detectado
- [ ] **Rich Results Test:** Playwright testa 5 URLs de capitais no Rich Results Test — validar `FAQPage` + `LocalBusiness` + `BreadcrumbList`
- [ ] **Monitoramento:** Playwright exporta Desempenho GSC filtrado por `/blog/licitacoes/cidade/`
- [ ] **Relatório:** `docs/validation/mkt-005-indexation-fase1.md`

### AC7 — Página de índice

- [ ] `/blog/licitacoes/cidades/` — mapa ou lista de todas as cidades com contagens
- [ ] Filtro por UF
- [ ] "Sua cidade não está aqui? Busque no SmartLic" → CTA trial

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Cidades com volume zero de licitações | Mostrar dados da UF como fallback + "Monitore licitações de {UF} que incluem {cidade}" |
| Thin content em cidades menores | Bloco editorial fixo por região + dados da UF complementam |
| 100+ páginas saturando indexação | Lançamento faseado (27 → 100) com solicitação de indexação via Playwright no GSC; monitoramento semanal |
| Nomes de cidade com homônimos | Slug inclui UF para desambiguação (ex: `vitoria-es`, `vitoria-da-conquista-ba`) |

## Definição de Pronto

- [ ] 27 capitais publicadas e indexáveis
- [ ] Dados renderizando corretamente (ou fallback gracioso)
- [ ] Schema validado
- [ ] GSC: 27 URLs de capitais com indexação solicitada via Playwright
- [ ] GSC: Rich Results Test validado para 5 URLs amostrais
- [ ] Relatório gerado em `docs/validation/mkt-005-indexation-fase1.md`
- [ ] Commit com tag `MKT-005`
