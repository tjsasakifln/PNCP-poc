# Session 2026-04-27 — GSC root-cause + 9 stories validadas

**Branch:** `session/2026-04-26-keen-sutton-trial-audit` (⚠️ herdada — nome mente sobre conteúdo. Considerar fork/rename antes de push.)
**Sessão anterior:** `2026-04-26-keen-sutton-mission-handoff.md` + `2026-04-26-humble-dolphin.md`
**Agente:** Claude (modo /sm + /po)

## Objetivo

Inspecionar dashboard GSC via Playwright; consolidar root-causes em brief para SM; criar e validar stories para sanar definitivamente cada problema.

## Entregue

### 1. Brief root-cause (23KB, 360 linhas)

`docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md`

- Inspeção GSC via Playwright (Performance, Indexação, Sitemaps, CWV, Datasets)
- 6 clusters de páginas não indexadas mapeados (4.718 URLs)
- DOM artifact corrigido (`` Material Icons PUA inflando bucket counts)
- Sentry pull validando P0 incident
- Stories prévias mapeadas (SEN-BE-005/007/008, STORY-SEO-001/018/022/023)

### 2. Descoberta P0 (lateral à inspeção)

**Backend `api.smartlic.tech` saturado/inalcançável** validado via:
- Curl burst 10/10 timeouts em 2 rounds 30s apart (inclusive `/buscar` user-facing)
- Sentry: 800 events/24h, top issue "Health degraded pncp" 713 evt **desde 22-abr 22:34** (5 dias sem resolução)
- Sitemap endpoints rodando até 28 minutos (1680.8s p99)
- DB ConnectionTerminated + canceling statement timeouts

### 3. 9 stories criadas + validadas (1 ciclo SM→PO completo)

| ID | Status final | Razão |
|----|-------------|-------|
| `STORY-INC-001-backend-db-pool-exhaustion-2026-04-27.md` | **Withdrawn** | Duplicado 100% por SEN-BE-001 (P0) + SEN-BE-005 (P1) + SEN-BE-007 (P1) + SEN-BE-008 (P0). IDS Article IV-A: REUSE > CREATE |
| `STORY-SEO-025-cnpj-sitemap-gate-alignment.md` | **Withdrawn** | Conflita SEO-023 Approved (produto pivotou "noindex tão indesejável quanto 404") |
| `STORY-SEO-026-robots-alertas-prefix-match-fix.md` | **Ready** | Fix robots.txt RFC 9309 §2.2.2 prefix-match `/alertas` → `/alertas-publicos` (280 URLs) |
| `STORY-SEO-027-contratos-orgao-root-404.md` | **Ready** | Refatorada discovery-first per spec @po; 44 URLs P3 |
| `STORY-SEO-028-blog-licitacoes-orphan-categorias.md` | **Ready** | 55 URLs `/blog/licitacoes/{cat}/{uf}` 404 (categorias renomeadas/removidas) |
| `STORY-SEO-029-dataset-schema-warnings.md` | **Ready** | 4 warnings schema Dataset (license/description/contentUrl/creator); discovery resolvida inline em `app/licitacoes/[setor]/page.tsx:583` |
| `STORY-DISC-001-fornecedores-15d-slug-origin.md` | **Ready** | Spike origem slugs `/fornecedores/{15d}` (286 URLs); pattern dígito 2 anexado consistente |
| `STORY-DISC-002-dataset-schema-locate.md` | **Withdrawn** | Resolvida em 1 grep durante validação @po — overengineering |
| `STORY-PROC-001-stale-p0-execution-gap.md` | **Ready (P0 governance)** | Investigar por que SEN-BE-001/008 (P0) ficaram Ready 14+ dias enquanto backend degradava |

### 4. Materiais brutos GSC (paths absolutos)

```
/mnt/d/pncp-poc/gsc-404-urls.txt              # 1000 URLs (de 2113)
/mnt/d/pncp-poc/gsc-noindex-urls.txt          # 1000 URLs (de 1880)
/mnt/d/pncp-poc/gsc-5xx-urls.txt              # 162 URLs (full)
/mnt/d/pncp-poc/gsc-robots-urls.txt           # 464 URLs (full)
/mnt/d/pncp-poc/gsc-perf-queries-28d.txt      # 395 queries
/mnt/d/pncp-poc/gsc-perf-pages-28d.txt        # 1395 page rows
```

**Caveat:** todos contêm sufixo PUA `` em cada URL. Strip via:
```python
re.sub(r'[-]+$', '', url)
```

## ⚠️ Achado MAIOR (lever organizacional, não engenharia)

A inspeção GSC foi o valor; **as 5 stories Ready criadas hoje são gaps marginais.** O lever real é:

**Pull SEN-BE-001 (P0) + SEN-BE-008 (P0) AGORA + executar STORY-PROC-001.**

Backend está saturado há 5 dias com 2 stories P0 Status:Ready prontas que ninguém puxou. SEO root-cause é vítima downstream — todas rotas `/cnpj`, `/fornecedores`, `/orgaos`, `/contratos/orgao` estão virando 404 hoje porque `AbortSignal.timeout(10000)` no client cancela fetch antes de backend responder.

## Pendente (dono + prazo)

| Ação | Owner | Prazo | Dependência |
|------|-------|-------|-------------|
| **Pull SEN-BE-001 + SEN-BE-008 (P0 incident response)** | @pm + @data-engineer + @dev | imediato | Anexar brief root-cause como evidência |
| **Executar STORY-PROC-001** (retrospective <30min) | @pm + @po | 7 dias | — |
| Pull STORY-SEO-026 (robots prefix-match) | @dev | quando capacidade | nenhum bloqueio |
| Pull STORY-DISC-001 (slug spike Tasks 1,3,4,5) | @analyst | quando capacidade | nenhum bloqueio |
| Pull STORY-SEO-027 + 028 + 029 (mensuração GSC) | @dev / @analyst | após backend recover | bloqueada por SEN-BE-001/008 |
| Branch hygiene: rename ou fork antes de push | @devops | antes de push | — |
| Commit + push das 9 stories + brief + 6 arquivos brutos | @devops | quando branch hygiene resolvida | — |

## Riscos vivos

- **R1 (Crítico):** Backend P0 outage continua — `/buscar` user-facing afetado. Cada hora sem fix = revenue loss + churn risk
- **R2 (Alto):** Padrão "P0 Ready 14d sem pull" pode repetir se PROC-001 não executada — próximo incidente terá mesma surpresa
- **R3 (Médio):** Branch name `keen-sutton-trial-audit` mente sobre conteúdo (GSC root-cause). PR readers vão discount provenance
- **R4 (Baixo):** SEO-027 SLA 7d para @sm refinar implícito — virou explícito após @po flag; agora explícito mas sem accountability automática

## Memory updates (já gravados)

- `project_backend_outage_2026_04_27.md` — registrado P0 outage + Sentry evidence (713 evt "Health degraded pncp" desde 22-abr)
- `MEMORY.md` linha 48 atualizada apontando para o memory + brief

## KPI da sessão

| Métrica | Valor |
|---------|-------|
| Tempo total inspeção + brief + 8 stories + validação @po | ~3h |
| Stories criadas | 9 (8 SM + 1 PO) |
| Stories Ready (puxáveis) | 6 |
| Stories Withdrawn | 3 |
| Discoveries inline (resolvidas em 1 grep) | 1 (DISC-002) |
| URLs GSC brutas coletadas | ~3.621 (acumulado de 6 arquivos) |
| Sentry events analisados | 800 evt 24h + top 15 issues |
| Decisões IDS Article IV-A invocadas | 3 (NO-GO INC-001, NO-GO SEO-025, NO-GO DISC-002) |

## Próxima ação prioritária de receita

**Não é story SEO. É puxar SEN-BE-001 + SEN-BE-008 (P0 backend Ready 14+ dias).**

Backend saturado bloqueia:
- `/buscar` (feature core) → user churn
- Trial signups (paywall hits backend)
- Mixpanel events (paywall_hit, trial_started silenced)
- SEO descoberta (frontend pages → 404 cascata)

Brief root-cause `docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §"P0 INCIDENTE VIVO" tem evidência pronta para anexar à conversa de priorização com fundador/PM.

## Próximo agente recomendado

**@pm** (priorização + autorização pull SEN-BE-001/008) **OU** **@devops** (branch hygiene + commit das 9 stories + push) — dependendo do que destrava primeiro.

Não recomendado: começar implementação de SEO-026/028/029 antes do incident — métricas pós-fix não fazem sentido com backend down.
