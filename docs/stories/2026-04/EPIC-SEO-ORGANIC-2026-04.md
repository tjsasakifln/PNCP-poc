# EPIC-SEO-ORGANIC-2026-04: Observatório de Licitações — Tráfego Orgânico Outlier

**Priority:** P1 — Growth
**Status:** Draft
**Owner:** @sm (River) + @dev + @devops
**Sprint:** Sequencial (stories independentes, execução em paralelo onde possível)
**Meta:** 0 → 2.500 cliques orgânicos/mês em 6 meses. 0 → 60 domínios referentes.

---

## Contexto Estratégico

Auditoria GSC (2026-04-11) revelou:
- **12 cliques/mês, 1.477 impressões, CTR 0,8%** — desempenho crítico
- **0 backlinks externos** (relatório Links: "Nenhum dado")
- **569 páginas programáticas detectadas mas recusadas** (thin content sinalizado)
- Concorrentes (BLL, ConLicitação, Instituto Licitar) têm DA 15-40 e **zero jornalismo de dados**

**Estratégia central (Consenso Conselho CMOs — 2026-04-11):**
Tornar o SmartLic o **Observatório Público das Licitações do Brasil** — transformar os 40K editais do datalake em jornalismo de dados que a imprensa, o SEBRAE e órgãos públicos são obrigados a citar. Backlinks seguem autoridade topical; autoridade topical segue dados proprietários.

---

## Stories do Epic

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| [STORY-430](STORY-430-thin-content-surgery-noindex-programmatic-pages.md) | **P0** | M | @dev + @devops | Draft | Cirurgia thin content — noindex 30% piores |
| [STORY-431](STORY-431-observatorio-relatorio-mensal-licitacoes.md) | P1 | L | @dev + @devops | Draft | Observatório — relatório mensal de dados |
| [STORY-432](STORY-432-calculadora-embed-linkbait.md) | P1 | M | @dev | Draft | Calculadora embeddável como link bait |
| [STORY-433](STORY-433-quick-wins-backlinks-sebrae-haro-listings.md) | P1 | S | @devops | Draft | Quick wins — SEBRAE, HARO, listings |
| [STORY-434](STORY-434-api-publica-readonly-datalake.md) | P2 | L | @dev + @devops | Draft | API pública read-only do datalake |
| [STORY-435](STORY-435-indice-transparencia-municipal.md) | P2 | XL | @dev + @devops | Draft | Índice de Transparência Municipal |
| [STORY-436](STORY-436-padrao-editorial-conteudo-publico.md) | **P1** | S | @dev | Draft | Padrão editorial — sem vestígios de AI no conteúdo público |

---

## Ordem de Execução Recomendada

### Sprint 1 (urgente — limpar sinal negativo)
- **STORY-430** (thin content surgery) — blocker implícito: site poluído prejudica todos os outros ranqueamentos

### Sprint 2 (construir ativos linkáveis)
- **STORY-436** (Padrão editorial) — deve ser concluída ANTES de publicar qualquer conteúdo
- **STORY-431** (Observatório) + **STORY-432** (Calculadora embed) — em paralelo, após STORY-436
- **STORY-433** (Quick wins backlinks) — pode começar imediatamente, independente

### Sprint 3 (ampliar autoridade)
- **STORY-434** (API pública) + **STORY-435** (Índice Municipal)

---

## KPIs do Epic

| KPI | Baseline (2026-04-11) | Meta 3 meses | Meta 6 meses | Meta 12 meses |
|-----|----------------------|-------------|--------------|---------------|
| Cliques orgânicos/mês | 12 | 350 | 2.500 | 15.000 |
| Domínios referentes (RDs únicos) | 0 | 15 | 60 | 200 |
| Backlinks DA 60+ | 0 | 3 | 15 | 50 |
| Páginas indexadas (% do total) | ~30% | 60% | 80% | 90% |
| Citações em imprensa/mês | 0 | 2 | 6 | 15 |
| Keywords top 10 | <5 | 40 | 200 | 800 |
| Signups orgânicos/mês | 0-2 | 15 | 80 | 400 |

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Epic criado — baseado em auditoria GSC + Consenso Conselho CMOs (53 especialistas, 8 clusters) |
