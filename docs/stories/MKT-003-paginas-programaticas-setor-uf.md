# MKT-003 — Páginas Programáticas Setor × UF (405 páginas)

**Status:** pending
**Priority:** P1 — Diferencial estrutural de SEO
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** frontend/app/blog/licitacoes/[setor]/[uf]/
**Esforço:** 3-5 dias (após MKT-002)
**Timeline:** Semana 2-3
**Bloqueado por:** MKT-002

---

## Contexto

405 páginas (15 setores × 27 UFs) com dados ao vivo de licitações, alimentadas pela API do SmartLic. Esta é a camada de maior escala do SEO programático — cada página captura buscas de cauda longa como "licitações de informática em São Paulo" ou "editais de saúde no Paraná".

### Evidências

- SmartLic tem ativo único: dados consolidados de 3 fontes oficiais × 27 UFs × 15 setores
- Nenhum concorrente de conteúdo (Zenite, ConLicitação) tem dados ao vivo
- Zapier provou o modelo: template × variáveis = crescimento exponencial

## Acceptance Criteria

### AC1 — Rota dinâmica

- [ ] Rota: `/blog/licitacoes/{setor}/{uf}` (ex: `/blog/licitacoes/informatica/sp`)
- [ ] `generateStaticParams()` gera todas as 405 combinações
- [ ] ISR com `revalidate: 86400` (24h)
- [ ] 404 para combinações inválidas (setor/UF inexistente)

### AC2 — Conteúdo de cada página

- [ ] **H1:** "Licitações de {Setor} em {UF Nome Completo} — {Mês} {Ano}"
- [ ] **Dados ao vivo:** contagem de editais abertos, faixa de valores (min-max), modalidades predominantes (% pregão, % concorrência)
- [ ] **Top 5 oportunidades da semana:** objeto, valor estimado, órgão, data limite
- [ ] **Tendência 90 dias:** gráfico simples ou indicador textual (↑ +15%, ↓ -8%)
- [ ] **Bloco editorial fixo** (300+ palavras): contexto do setor na UF, dicas específicas, perfil de compradores
- [ ] **FAQ section:** 5 perguntas sobre licitações do setor na UF (40-60 palavras cada resposta)

### AC3 — Schema e meta tags

- [ ] Schema JSON-LD: `FAQPage` + `Dataset` + `BreadcrumbList`
- [ ] Meta title: "Licitações de {Setor} em {UF} — Editais Abertos {Ano} | SmartLic"
- [ ] Meta description: "Encontre {count} licitações de {setor} em {UF}. Dados ao vivo de PNCP, PCP e ComprasGov. Filtre por valor, modalidade e prazo. Teste grátis."
- [ ] Canonical URL, OG tags

### AC4 — CTA e conversão

- [ ] CTA inline: "Veja todas as {count} licitações de {setor} em {UF} — teste grátis 30 dias"
- [ ] CTA final com botão: link para `/signup?utm_source=blog&utm_medium=programmatic&utm_content={setor}-{uf}`
- [ ] Badge: "Dados atualizados em {data}" (credibilidade)

### AC5 — Lançamento faseado

- [ ] **Fase 1 (Semana 2):** 25 páginas — 5 setores maiores (informática, saúde, engenharia, facilities, software) × 5 UFs maiores (SP, RJ, MG, PR, RS)
- [ ] **Fase 2 (Semana 4):** Expandir para todos 15 setores × 5 UFs = 75 páginas
- [ ] **Fase 3 (Mês 2):** Expandir para 15 setores × 27 UFs = 405 páginas
- [ ] Monitorar indexação via Search Console após cada fase

### AC6 — Internal linking

- [ ] Cada página linka para: panorama do setor (MKT-005), 3 páginas de UFs vizinhas, post editorial do setor (se existir)
- [ ] Página de índice `/blog/licitacoes/` listando todos os setores e UFs com contagens

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Thin content (página com 0 licitações) | Exibir "Nenhuma licitação ativa neste período" + conteúdo editorial fixo + sugestão de UFs próximas |
| Indexação lenta (405 páginas novas) | Lançamento faseado (25 → 75 → 405), submissão via Search Console, internal linking |
| Dados desatualizados | ISR 24h + badge "atualizado em DD/MM" + fallback para cache se API falhar |
| Conteúdo editorial repetitivo entre UFs | Variar o bloco editorial por região (Norte/Nordeste/Sudeste/Sul/Centro-Oeste) |

## Definição de Pronto

- [ ] 25 páginas da Fase 1 publicadas e indexáveis
- [ ] Schema validado via Rich Results Test
- [ ] Sitemap inclui todas as páginas
- [ ] Dados ao vivo renderizando corretamente
- [ ] Testes: rendering, schema, dados, 404 para inválidos
- [ ] Commit com tag `MKT-003`

## KPIs

| Métrica | 30 dias | 90 dias | 180 dias |
|---------|---------|---------|----------|
| Páginas indexadas | 25 | 200 | 405 |
| Impressões Search Console/semana | 2.000 | 20.000 | 80.000 |
| Cliques orgânicos/semana | 50 | 1.000 | 5.000 |
