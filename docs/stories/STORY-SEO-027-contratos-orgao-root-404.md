# STORY-SEO-027: Investigar e mitigar 44 hits 404 em `/contratos/orgao` (URL raiz órfã)

## Status

**Ready (re-aprovada @sm 2026-04-27)** — refatorada discovery-first per spec @po 2026-04-27

## Prioridade

P3 — Baixo (44 URLs em volume total ~7.8k indexadas; pattern claro mas origem externa não controlamos diretamente)

## Origem

- Inspeção GSC root-cause 2026-04-27 (`docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §3.1 + S4)
- Verdict @po 2026-04-27 em versão original (Draft) — premissa "remover do sitemap" inválida porque sitemap nunca emitiu

## Tipo

SEO / Discovery + Bug

## Owner

@analyst (Tasks 1-2 discovery) + @dev (Task 3 mitigação)

## Story

**As a** time de growth orgânico,
**I want** identificar a origem real dos 44 hits 404 em `/contratos/orgao` (sem CNPJ) e implementar mitigação proporcional ao volume,
**so that** Google atualize seu índice e o sinal de qualidade do site não seja afetado por URLs órfãs persistentes.

## Problema

GSC cluster "Não encontrado (404)" reporta 44 URLs com path exato `/contratos/orgao` (raiz, sem `[cnpj]`). Validação durante review @po 2026-04-27 estabeleceu:

| Premissa testada | Resultado |
|------------------|-----------|
| Sitemap emite `/contratos/orgao` (raiz)? | **NÃO** — `frontend/app/sitemap.ts:767` emite apenas `${baseUrl}/contratos/orgao/${cnpj}` (sempre com CNPJ) |
| Existe `app/contratos/orgao/page.tsx`? | **NÃO** — só `app/contratos/orgao/[cnpj]/page.tsx` |
| Frontend tem link literal `/contratos/orgao` sem template var? | **NÃO** — `grep -rn "/contratos/orgao[\"' )]" frontend/app frontend/components` retorna 0 matches |

**Conclusão:** origem é externa ao código atual. Hipóteses ranqueadas:

1. **Backlink externo antigo** (mais provável) — site de terceiro linkou versão pré-fix; URLs persistem em backlink graph
2. **Link interno em template removido** — algum componente legacy emitia link sem CNPJ; commit removeu mas Google ainda crawla
3. **Referência stale Google** — Google manteve URL no índice de período onde rota existia (improvável dado que páginas raiz órfãs geralmente são purgadas em <30d)

## Critérios de Aceite

- [ ] **AC1:** Discovery completo — output em comentário inline OU `docs/spikes/2026-04-contratos-orgao-44-hits-origin.md`:
  - Lista das 44 URLs únicas extraídas de `gsc-404-urls.txt` (filtro path exato `/contratos/orgao` sem subpath)
  - Logs Sentry filter `path = /contratos/orgao` (sem subpath) últimos 30d → top 10 referers capturados
  - GSC > Performance > URL filter exato → queries que geraram impressões nessa URL (se houver)
  - Git log `frontend/` últimos 90 dias buscando `contratos/orgao` em deletions — verificar se algum template emitia
  - Conclusão: origem identificada (Hipótese 1/2/3 ou outra) OU "indeterminada" aceitável
- [ ] **AC2:** Decisão técnica registrada baseada no AC1:
  - **Se Hipótese 1 (backlink externo) confirmada:** retornar **410 Gone** explícito em `app/contratos/orgao/page.tsx` (criar arquivo novo) — sinaliza Google purge mais rápido que 404
  - **Se Hipótese 2 (template legacy) confirmada:** garantir que template removido não é redeployable; documentar em `docs/adr/` para evitar regressão
  - **Se Hipótese 3 ou indeterminada:** mesma ação que Hipótese 1 (410 Gone) — defensivo
- [ ] **AC3:** Implementação da mitigação escolhida:
  - Se 410: novo arquivo `frontend/app/contratos/orgao/page.tsx` com `notFound()` + header HTTP 410. Next.js 16 não tem 410 nativo via `notFound()` (retorna 404); usar `redirect` para 410 custom OU middleware. Confirmar approach pré-implementação.
  - Validação local: `curl -sS -I http://localhost:3000/contratos/orgao` retorna 410 (ou 404 se 410 não viável tecnicamente)
- [ ] **AC4:** Pós-deploy: ≤5 hits em `/contratos/orgao` (raiz) no GSC em 30 dias
- [ ] **AC5:** Sitemap continua não emitindo essa URL (regressão check via `grep "contratos/orgao[\"']" frontend/app/sitemap.ts | grep -v cnpj`) — esperado 0 matches sempre
- [ ] **AC6:** Anti-regressão: teste em `frontend/__tests__/sitemap.test.ts` (criar se não existir) confirma sitemap não tem entry com path exato `/contratos/orgao`

### Anti-requisitos

- **NÃO** criar landing page com conteúdo só para "evitar 404" — soft 404 penalty pior que 404 honesto
- **NÃO** redirect 301 para `/contratos` ou outra URL — conteúdos diferentes; Google penaliza
- **NÃO** investir >2h em discovery se Hipótese 1 confirmada nas primeiras amostras Sentry — escopo P3, voltar e implementar 410

## Tasks / Subtasks

- [ ] Task 1 — Discovery via Sentry (AC: 1)
  - [ ] @analyst: query Sentry API `path = /contratos/orgao` (regex `^/contratos/orgao$` se possível) últimos 30d
  - [ ] Capturar `referer` header dos eventos
  - [ ] Top 10 referers + classificação (interno/externo/desconhecido)
- [ ] Task 2 — Discovery via GSC + git log (AC: 1)
  - [ ] @analyst: GSC > Performance via Playwright; filter URL exato → query report
  - [ ] `git log -p --all -- 'frontend/app/**/*.tsx' | grep -B5 -A5 "/contratos/orgao[\"' )]" | head -100` — buscar emissões removidas
  - [ ] Output consolidado em `docs/spikes/2026-04-contratos-orgao-44-hits-origin.md` ou comentário desta story
- [ ] Task 3 — Decisão + implementação (AC: 2, 3)
  - [ ] @dev avalia viabilidade técnica de 410 Gone em Next.js 16 (vs middleware vs alternativa)
  - [ ] Implementação curta
- [ ] Task 4 — Anti-regressão (AC: 6)
  - [ ] @qa adiciona teste sitemap
- [ ] Task 5 — Mensuração pós-deploy (AC: 4)
  - [ ] Re-medir GSC em 30d via Playwright (mesmo protocolo do brief raiz)

## Referência de implementação

- `frontend/app/sitemap.ts:767` (emissor que não inclui raiz)
- `frontend/app/contratos/orgao/[cnpj]/page.tsx` (rota com CNPJ existente)
- `gsc-404-urls.txt` (lista bruta — filter `python3 -c "import json,re; [print(u) for u in json.load(open('gsc-404-urls.txt')) if re.match(r'https://smartlic.tech/contratos/orgao(\$|[\\ue000-\\uf8ff])', u)]"`)
- Brief: `docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §3.1
- Memory: `reference_sentry_credentials.md` (org=confenge, proj=smartlic-backend)

## Decisão: NÃO merge com STORY-SEO-018

Considerada e rejeitada após análise:

| Aspecto | STORY-SEO-018 | STORY-SEO-027 |
|---------|---------------|---------------|
| Categoria | Rotas dinâmicas com slug **semântico** quebrado (`/orgaos/ministerio-saude`, `/observatorio/raio-x-sp`) | URL **raiz órfã** sem `[param]` (`/contratos/orgao`) |
| Causa raiz | Rota existe em código mas slug format quebrado / data source faltante | Rota raiz **não existe em código**; URL é externa |
| Solução | Implementar / noindex / redirect baseado em valor SEO | 410 Gone (defensivo) ou identificar template removido |
| Volume | 7+ rotas distintas, 8 SP, escopo grande | 1 rota, 44 URLs, P3 |
| Owner | @dev + @data-engineer | @analyst (discovery) + @dev (impl curta) |

Cluster diferente. Manter separação preserva escopo SEO-018 sem inflar.

## Riscos

- **R1 (Médio):** Discovery pode não identificar origem (Sentry retention <30d, GSC não filtra path exato facilmente). Mitigar: aceitar "indeterminada" como conclusão válida → seguir 410 defensivo
- **R2 (Baixo):** 410 em Next.js 16 pode requerer middleware custom — fallback aceitável é 404 padrão (status quo) com nota técnica explicando que Next.js 16 não suporta 410 nativo
- **R3 (Baixo):** Backlinks externos podem persistir mesmo após 410 — Google pode levar 60-90d para purgar; AC4 30d pode ser otimista. Aceitar parcialmente atendido se trend descendente

## Dependências

- **Bloqueada parcialmente por SEN-BE-008** apenas para Task 5 (mensuração GSC) — Tasks 1-4 podem rodar imediatamente
- **Não merge com STORY-SEO-018** (justificativa em §"Decisão: NÃO merge")
- **Não conflita com STORY-SEO-024** (programmatic surface expansion — escopo é criar templates novos, não fixar URL órfã específica)

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-27 | @sm (River) | Story criada a partir do brief GSC root-cause §3.1 + S4 |
| 2026-04-27 | @po (Sarah) | **Validação 6-section: NEEDS REVISION**. Sitemap não emite URL raiz — escopo real é discovery do referer externo. Status: Draft → Draft (revision requested). |
| 2026-04-27 | @sm (River) | **Refatorada discovery-first per spec @po:** AC1 reescrito como discovery, decisão técnica explicit em AC2 (Hipóteses 1/2/3), Task 1-2 separadas (Sentry / GSC+git log), prioridade P2→P3 (volume baixo + origem externa), decisão NÃO merge com SEO-018 documentada. Status: Draft (revision requested) → Ready. |
